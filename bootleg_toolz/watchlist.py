"""
Watchlist module for bm.

Provides Excel/CSV-driven multi-series management — load a watchlist from an
Excel (.xlsx) or CSV file, fetch data via Dataset.pull_* methods, persist
results to HDF5 + Excel/CSV.
"""

from __future__ import annotations

import gc
import os
import re
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from bootleg_datafeed.auxiliary import (
    close_open_stores,
    drop_duplicate_columns,
    hdf_key_safe,
    strip_timezone_from_df,
)
from bootleg_datafeed.dataset import Dataset
from bootleg_datafeed.models import StandardSeries

# Canonical metadata index — merged from reference implementation + bm/models fields
METADATA_INDEX = [
    # Core identity
    'id',
    'title',
    'source',
    'original_source',
    # Series properties
    'frequency',
    'frequency_short',
    'series_type',
    'data_type',
    # Units
    'units',
    'units_short',
    # Date range
    'start_date',
    'end_date',
    # Statistics
    'length',
    'min_value',
    'max_value',
    # Exchange (tv, nasdaq)
    'exchange',
    # Descriptions & timestamps
    'description',
    'last_updated',
]

# Sources that accept optional delimited params in the watchlist id column
MULTI_PARAM_SOURCES = {
    'tv': ['symbol', 'exchange'],
    'bea': ['dataset', 'table_code'],
    'abs': ['series_id', 'catalog_num'],
    'glassnode': ['metric', 'asset', 'interval'],
    'cryptocompare': ['fsym', 'tsym'],
}


def _parse_id(source: str, id_str: str) -> tuple[str, dict]:
    """
    Parse a watchlist id string. If source accepts extra params AND a delimiter
    (comma or semicolon) is present, split and assign parts to source-specific
    params. Otherwise return id_str as primary_id with no extra kwargs
    (source applies its own defaults).

    Examples:
      source='yfinance',  id_str='AAPL'                      -> ('AAPL', {})
      source='tv',        id_str='BTCUSD, INDEX'            -> ('BTCUSD', {'exchange': 'INDEX'})
      source='tv',        id_str='BTCUSD'                   -> ('BTCUSD', {})   # no delimiter -> TV defaults
      source='bea',        id_str='T10101'                    -> ('T10101', {})   # no delimiter -> dataset defaults to 'NIPA'
      source='bea',        id_str='NIPA, T10101'             -> ('NIPA', {'table_code': 'T10101'})
      source='glassnode',  id_str='/market/price_usd_close' -> ('/market/price_usd_close', {})  # no delimiter
      source='glassnode',  id_str='/market/price_usd_close, BTC, 24h'
                                                               -> ('/market/price_usd_close', {'asset': 'BTC', 'interval': '24h'})
    """
    if source not in MULTI_PARAM_SOURCES:
        return (id_str.strip(), {})

    if not re.search(r'[,;]', id_str):
        return (id_str.strip(), {})

    parts = [p.strip() for p in re.split(r'[,;]', id_str)]
    param_names = MULTI_PARAM_SOURCES[source]

    primary_id = parts[0] if parts else ''
    extra_kwargs = {
        param_names[i]: parts[i]
        for i in range(1, len(parts))
        if i < len(param_names)
    }

    return (primary_id, extra_kwargs)


def _pull_series(
    source: str,
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs,
) -> StandardSeries:
    """Pull a single series via Dataset.pull(), handling multi-param ids."""
    ds = Dataset()
    primary_id, extra = _parse_id(source, series_id)
    kwargs.update(extra)
    return ds.pull(source, primary_id, start_date=start_date, end_date=end_date, **kwargs)


def _pick_excel_file_dialog() -> Optional[str]:
    """Pick an Excel file to open using common Linux native dialog tools.

    Tries `zenity` first, then `kdialog`. Returns None if canceled/unavailable.
    """
    # GNOME/GTK environments
    if shutil.which('zenity'):
        cmd = [
            'zenity',
            '--file-selection',
            '--title=Open watchlist (.xlsx)',
            '--file-filter=Excel files | *.xlsx',
            '--file-filter=All files | *',
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    # KDE/Qt environments
    if shutil.which('kdialog'):
        cmd = ['kdialog', '--getopenfilename', str(Path.cwd()), '*.xlsx|Excel files (*.xlsx)']
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    return None


def _save_excel_file_dialog() -> Optional[str]:
    """Pick a save-as path for an Excel file using common Linux native dialog tools.

    Tries `zenity` first, then `kdialog`. Returns None if canceled/unavailable.
    """
    # GNOME/GTK environments
    if shutil.which('zenity'):
        cmd = [
            'zenity',
            '--file-selection',
            '--save',
            '--confirm-overwrite',
            '--title=Save watchlist (.xlsx)',
            '--file-filter=Excel files | *.xlsx',
            '--file-filter=All files | *',
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    # KDE/Qt environments
    if shutil.which('kdialog'):
        cmd = ['kdialog', '--getsavefilename', str(Path.cwd()), '*.xlsx|Excel files (*.xlsx)']
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    return None


class Watchlist:
    """
    A watchlist for managing multi-source time series data.

    Attributes:
        name: Watchlist name (default 'base_watchlist')
        watchlists_path: Base directory for watchlist files
        storepath: Path to HDF5 store (.h5s file)
        watchlist: DataFrame with columns ['id', 'source', 'title']
        metadata: DataFrame with METADATA_INDEX rows as index, series ids as columns
        datasets: dict of pandas Series keyed by series id
        full_metadata: dict of raw metadata dicts per series id

    Example:
        wl = Watchlist()
        errors = wl.get_watchlist_data('2020-01-01', '2024-12-31')
        wl.save_watchlist('my_watchlist.xlsx')
    """

    def __init__(
        self,
        name: str = "base_watchlist",
        watchlists_path: Optional[str] = None,
    ):
        self.name = name
        self.watchlists_path = watchlists_path
        self.storepath: Optional[str] = None

        # Core data structures
        self.watchlist = pd.DataFrame(columns=['id', 'source', 'title'])
        self.metadata = pd.DataFrame(index=METADATA_INDEX)
        self.datasets: dict[str, pd.Series] = {}
        self.full_metadata: dict[str, dict] = {}

    # -------------------------------------------------------------------------
    # Series management
    # -------------------------------------------------------------------------

    def append_series(self, series: StandardSeries) -> None:
        """
        Add a StandardSeries to the watchlist.

        If series id already exists in watchlist, metadata, or datasets, it is
        replaced rather than appended as a duplicate.
        """
        sid = series.metadata.id

        # Replace/add in watchlist DataFrame
        mask = self.watchlist['id'] == sid
        new_row = pd.DataFrame({
            'id': [sid],
            'source': [series.metadata.source],
            'title': [series.metadata.title or sid],
        })
        if mask.any():
            self.watchlist.loc[mask] = new_row.values
        else:
            self.watchlist = pd.concat([self.watchlist, new_row], ignore_index=True)

        # Replace in datasets dict
        self.datasets[sid] = series.to_pandas()

        # Replace in full_metadata dict
        self.full_metadata[sid] = series.metadata.model_dump()

    def drop_series(self, series_id: str) -> None:
        """Remove a series from all storage."""
        # From watchlist DataFrame
        self.watchlist = self.watchlist[self.watchlist['id'] != series_id]

        # From metadata DataFrame
        if series_id in self.metadata.columns:
            self.metadata = self.metadata.drop(columns=[series_id])

        # From datasets dict
        if series_id in self.datasets:
            del self.datasets[series_id]

        # From full_metadata dict
        if series_id in self.full_metadata:
            del self.full_metadata[series_id]

    def deduplicate(self) -> None:
        """
        Remove duplicate series ids from watchlist, metadata, and datasets.

        - watchlist DataFrame: keep first occurrence by id column
        - metadata DataFrame: drop duplicate columns (keep first)
        - datasets dict: drop keys not present in watchlist id column
        """
        # Deduplicate watchlist DataFrame by id column
        self.watchlist = self.watchlist.drop_duplicates(subset=['id'], keep='first')

        # Deduplicate metadata columns
        dup_cols = self.metadata.columns[self.metadata.columns.duplicated()].tolist()
        if dup_cols:
            self.metadata = self.metadata.drop(columns=dup_cols)

        # Drop datasets keys not in watchlist
        valid_ids = set(self.watchlist['id'])
        keys_to_drop = [k for k in self.datasets if k not in valid_ids]
        for k in keys_to_drop:
            del self.datasets[k]

        # Sync metadata columns with datasets keys
        self.metadata = self.metadata.drop(
            columns=[c for c in self.metadata.columns if c not in self.datasets]
        )

    # -------------------------------------------------------------------------
    # Data fetching
    # -------------------------------------------------------------------------

    def get_watchlist_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        extend_abs: bool = False,
    ) -> dict[str, Exception]:
        """
        Fetch all series from the watchlist via Dataset.pull().

        Args:
            start_date: Start date for fetching (YYYY-MM-DD)
            end_date: End date for fetching (YYYY-MM-DD)
            extend_abs: If True, pass extend=True to pull_abs for each ABS
                        series, splicing cross-frequency siblings for a longer
                        history.

        Returns:
            dict of {series_id: exception} for any series that failed.
            Empty dict means all series fetched successfully.
        """
        errors = {}
        for _, row in self.watchlist.iterrows():
            try:
                kwargs = {}
                if extend_abs and row['source'] == 'abs':
                    kwargs['extend'] = True
                series = _pull_series(
                    row['source'], row['id'],
                    start_date=start_date, end_date=end_date,
                    **kwargs,
                )
                self.append_series(series)
            except Exception as e:
                errors[row['id']] = e
                continue

        self.deduplicate()
        self.update_metadata()
        return errors

    def update_metadata(self) -> None:
        """
        Rebuild the metadata DataFrame from all datasets.

        Calls to_pandas() on each series's metadata and transposes so columns
        are series ids and rows are METADATA_INDEX field names.
        """
        if not self.datasets:
            self.metadata = pd.DataFrame(index=METADATA_INDEX)
            return

        meta_rows = {}
        for sid, series in self.datasets.items():
            if sid in self.full_metadata:
                meta = self.full_metadata[sid]
            else:
                meta = {}

            # Build a dict matching METADATA_INDEX
            row = {}
            for field in METADATA_INDEX:
                row[field] = meta.get(field, None)

            # Fill computed fields if not already present
            if row.get('length') is None and len(series) > 0:
                row['length'] = len(series)
            if row.get('min_value') is None and len(series) > 0:
                try:
                    row['min_value'] = float(series.min())
                except (ValueError, TypeError):
                    row['min_value'] = None
            if row.get('max_value') is None and len(series) > 0:
                try:
                    row['max_value'] = float(series.max())
                except (ValueError, TypeError):
                    row['max_value'] = None
            if row.get('start_date') is None and len(series) > 0:
                idx = series.index
                row['start_date'] = idx[0] if len(idx) > 0 else None
            if row.get('end_date') is None and len(series) > 0:
                idx = series.index
                row['end_date'] = idx[-1] if len(idx) > 0 else None

            meta_rows[sid] = row

        self.metadata = pd.DataFrame(meta_rows, index=METADATA_INDEX)

    # -------------------------------------------------------------------------
    # HDF5 persistence
    # -------------------------------------------------------------------------

    def save_datasets(self) -> None:
        """
        Persist datasets to the HDF5 store (.h5s file).

        On key collision (two different ids sanitizing to the same HDF5 key),
        the second occurrence is dropped and a warning is printed.
        """
        if not self.datasets:
            return

        close_open_stores(self.storepath)
        key_mapping = {}
        watchstore = pd.HDFStore(self.storepath, mode='w')

        try:
            for key, series in self.datasets.items():
                sanitized = hdf_key_safe(key)
                if sanitized in key_mapping:
                    warnings.warn(
                        f"HDF5 key collision for '{key}' — second occurrence dropped",
                        UserWarning,
                    )
                    continue
                key_mapping[sanitized] = key
                watchstore[sanitized] = series if series is not None else pd.Series(dtype='object')

            if key_mapping:
                watchstore['_key_mapping'] = pd.Series(key_mapping, name='original_keys')
        finally:
            watchstore.close()

    def load_datasets(self) -> None:
        """Load series data from the HDF5 store into datasets."""
        if not self.storepath or not os.path.exists(self.storepath):
            return

        close_open_stores(self.storepath)
        with pd.HDFStore(self.storepath, mode='r') as watchstore:
            key_mapping = {}
            if '_key_mapping' in watchstore.keys():
                key_mapping = watchstore['_key_mapping'].to_dict()

            for sanitized_key in watchstore.keys():
                if sanitized_key.startswith('/_key_mapping'):
                    continue
                clean_key = key_mapping.get(sanitized_key.lstrip('/'), sanitized_key.lstrip('/'))
                series = watchstore[sanitized_key]
                if not isinstance(series.index, pd.DatetimeIndex):
                    try:
                        series.index = pd.to_datetime(series.index, errors='coerce')
                    except Exception:
                        pass
                self.datasets[clean_key] = series

        # Sync full_metadata from datasets
        self.full_metadata = {
            sid: self.metadata[sid].to_dict() if sid in self.metadata.columns else {}
            for sid in self.datasets
        }

    # -------------------------------------------------------------------------
    # Excel persistence
    # -------------------------------------------------------------------------

    def save_watchlist(self, path: Optional[str] = None, force_dialog: bool = False) -> None:
        """
        Save watchlist to .xlsx (3 sheets) and optionally .h5s.

        Args:
            path: File path for .xlsx save. storepath derived from this.
                  If None, uses self.storepath. If no storepath set,
                  opens a native save-file dialog (zenity/kdialog).
            force_dialog: If True, always open the save-file dialog.
        """
        if path is None and self.storepath is None or force_dialog:
            path = _save_excel_file_dialog()
            if path is None:
                return

        save_path = path or self.storepath
        if not save_path:
            return

        xlsx_path = str(Path(save_path).with_suffix('.xlsx'))
        self.storepath = str(Path(save_path).with_suffix('.h5s'))

        # Ensure directory exists
        Path(xlsx_path).parent.mkdir(parents=True, exist_ok=True)

        # Strip timezone from metadata before writing
        meta_clean = strip_timezone_from_df(self.metadata)

        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            # Sheet 1: watchlist
            wl = self.watchlist.copy()
            wl.index.name = 'index'
            wl.to_excel(writer, sheet_name='watchlist')

            # Sheet 2: all_metadata
            meta_clean.to_excel(writer, sheet_name='all_metadata')

            # Sheet 3: full_metadata (optional)
            if self.full_metadata:
                fm_df = pd.DataFrame(self.full_metadata).T
                fm_clean = strip_timezone_from_df(fm_df)
                fm_clean.index.name = 'id'
                fm_clean.to_excel(writer, sheet_name='full_metadata')

        # Save datasets to HDF5
        if self.datasets:
            self.save_datasets()

    def load_watchlist(self, filepath: Optional[str] = None) -> None:
        """
        Load watchlist from .xlsx file and accompanying .h5s.

        Args:
            filepath: Path to .xlsx file. If None, opens a native file dialog
                      (zenity/kdialog) when available.
        """
        if filepath is None:
            filepath = _pick_excel_file_dialog()
            if not filepath:
                raise ValueError(
                    "No filepath provided and no file selected. "
                    "Pass filepath explicitly or install zenity/kdialog for dialog support."
                )

        xlsx_path = Path(filepath)
        if xlsx_path.suffix.lower() != '.xlsx':
            raise ValueError(f"Expected .xlsx file, got: {xlsx_path}")
        if not xlsx_path.exists():
            raise FileNotFoundError(f"Watchlist file not found: {xlsx_path}")

        self.storepath = str(xlsx_path.with_suffix('.h5s'))
        self.name = xlsx_path.stem

        # Load metadata sheet
        self.metadata = pd.read_excel(filepath, index_col=0, sheet_name='all_metadata')
        self.metadata = self.metadata.reindex(METADATA_INDEX)

        # Load watchlist sheet
        self.watchlist = pd.read_excel(filepath, index_col=0, sheet_name='watchlist')

        # Load full_metadata sheet if present
        try:
            fm_df = pd.read_excel(filepath, index_col=0, sheet_name='full_metadata', dtype=str)
            self.full_metadata = fm_df.to_dict(orient='index')
        except Exception:
            self.full_metadata = {}

        # Deduplicate on load
        self.deduplicate()

        # Load datasets from HDF5 if present
        if os.path.exists(self.storepath):
            self.load_datasets()

        self.update_metadata()

    # -------------------------------------------------------------------------
    # CSV persistence (alternative to Excel)
    # -------------------------------------------------------------------------

    def save_watchlist_csv(self, path: Optional[str] = None) -> None:
        """
        Save watchlist to CSV format.

        CSV format: 'id,source,title' columns for the watchlist index.
        Series data is NOT stored in CSV (use save_watchlist + HDF5 for that).

        Args:
            path: File path for .csv save. If None, uses self.storepath.
        """
        if path is None and self.storepath is None:
            raise ValueError("Must provide path or set storepath first")

        save_path = Path(path or self.storepath).with_suffix('.csv')
        save_path.parent.mkdir(parents=True, exist_ok=True)

        wl = self.watchlist.copy()
        wl.index.name = 'index'
        wl.to_csv(save_path, index=True)

    def load_watchlist_csv(self, filepath: str) -> None:
        """
        Load watchlist from CSV format.

        CSV format: 'id,source,title' columns. Only loads the watchlist index;
        datasets must be loaded separately via load_datasets() or by passing
        a storepath that points to an existing .h5s file.

        Args:
            filepath: Path to .csv file
        """
        csv_path = Path(filepath)
        self.storepath = str(csv_path.with_suffix('.h5s'))
        self.name = csv_path.stem

        self.watchlist = pd.read_csv(filepath, index_col=0)
        # Normalize column names
        if 'id' not in self.watchlist.columns:
            self.watchlist.columns = ['id', 'source', 'title']

        # Initialize empty metadata/datasets; caller must call load_datasets()
        # or get_watchlist_data() to populate series data
        self.metadata = pd.DataFrame(index=METADATA_INDEX)
        self.full_metadata = {}

        self.deduplicate()

    # -------------------------------------------------------------------------
    # Plotting
    # -------------------------------------------------------------------------

    def plot_watchlist(
        self,
        left: Optional[list[str]] = [],
        right: Optional[list[str]] = None,
        additional_series: Optional[dict[str, dict[str, pd.Series]]] = None,
        plot_title: Optional[str] = None,
        primary_yaxis_title: Optional[str] = None,
        secondary_yaxis_title: Optional[str] = None,
        height: int = 600,
        width: int = 1000,
        template: str = "plotly_white",
        show_grid: bool = True,
        show_legend: bool = True,
        **kwargs,
    ):
        """Plot watchlist series using plotly.

        Wraps bm.charting.plot_watchlist for dual-axis support.

        Args:
            left: List of series ids for left (primary) axis. If None, plots all.
            right: List of series ids for right (secondary) axis.
            additional_series: dict - Extra series to plot on the named axes.
                Format: {'left': {label1: series1, label2: series2}, 'right': {label3: series3}}.
                Top-level keys are axis names ('left'/'right', both optional).
                Inner-dict keys become legend labels. Inner values must be pandas Series.
            plot_title: Chart title (default: watchlist name)
            primary_yaxis_title: Left y-axis label
            secondary_yaxis_title: Right y-axis label
            height: Plot height in pixels (default 600)
            width: Plot width in pixels (default 1000)
            template: Plotly template (default 'plotly_white')
            show_grid: Show grid lines (default True)
            show_legend: Show legend (default True)
            **kwargs: Passed to bm.charting functions

        Returns:
            plotly.graph_objects.Figure
        """
        from bootleg_toolz import charting

        # Determine which series to plot
        all_ids = list(self.datasets.keys())

        if left is None:
            # Plot all on left if not specified
            left_ids = all_ids
        else:
            left_ids = [sid for sid in left if sid in self.datasets]

        if right is None:
            right_ids = []
        else:
            right_ids = [sid for sid in right if sid in self.datasets]

        # Build (metadata, series) tuples
        def _make_items(sids):
            items = []
            for sid in sids:
                if sid not in self.datasets:
                    continue
                series = self.datasets[sid]
                # StandardSeries -> pandas Series
                if hasattr(series, 'to_pandas'):
                    series = series.to_pandas()
                # Get metadata dict
                meta = self.full_metadata.get(sid, {})
                items.append((meta, series))
            return items

        left_items = _make_items(left_ids)
        right_items = _make_items(right_ids)

        # Append caller-provided series to the named axis.
        # additional_series format: {'left': {label1: s1, ...}, 'right': {label2: s2, ...}}
        for axis_name, series_dict in (additional_series or {}).items():
            if axis_name not in ('left', 'right'):
                continue
            target = left_items if axis_name == 'left' else right_items
            for label, series in (series_dict or {}).items():
                if series is None:
                    continue

                s = series.to_pandas() if hasattr(series, 'to_pandas') else series
                if not isinstance(s, pd.Series):
                    continue

                s = s.copy()
                s.name = str(label)
                target.append(({'title': str(label), 'id': str(label)}, s))

        if plot_title is None:
            plot_title = self.name

        return charting.plot_watchlist(
            left=left_items,
            right=right_items if right_items else None,
            plot_title=plot_title,
            primary_yaxis_title=primary_yaxis_title,
            secondary_yaxis_title=secondary_yaxis_title,
            height=height,
            width=width,
            template=template,
            show_grid=show_grid,
            show_legend=show_legend,
            **kwargs,
        )

    def save_chart(
        self,
        path: str,
        left: Optional[list[str]] = None,
        right: Optional[list[str]] = None,
        scale: int = 3,
        **kwargs,
    ) -> Path:
        """Plot and save watchlist as a high-resolution PNG.

        Args:
            path: Output file path (.png)
            left: List of series ids for left axis. If None, plots all.
            right: List of series ids for right axis.
            scale: Resolution scale factor (default 3 = ~300 DPI effective)
            **kwargs: Passed to plot_watchlist()

        Returns:
            Path to saved PNG file
        """
        from bootleg_toolz import charting

        fig = self.plot_watchlist(left=left, right=right, **kwargs)
        return charting.save_png(fig, path, scale=scale)
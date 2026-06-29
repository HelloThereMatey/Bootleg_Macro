"""
Internal model classes for bm GUI.

PandasModel   — Qt table model wrapping a pandas DataFrame
WatchlistSelectionModel — Qt table model for the user's selected series list
SearchWorker  — QRunnable worker for background search
"""

from __future__ import annotations

import time

import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets

from bootleg_macro.watchlist_gui.gui._logging import log


class PandasModel(QtCore.QAbstractTableModel):
    """
    Qt table model wrapping a pandas DataFrame.

    Supports read-only display with optional column stretching and
    emits dataChanged on updates so views refresh automatically.
    """

    def __init__(self, data: pd.DataFrame | None = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else pd.DataFrame()

    # --- Qt Model Abstraction ---

    def rowCount(self, parent=...):
        return self._data.shape[0]

    def columnCount(self, parent=...):
        if self._data.empty:
            return 0
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            val = self._data.iloc[index.row(), index.column()]
            return str(val) if val is not None else ""
        return None

    def headerData(
        self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole
    ):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

    def flags(self, index):
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        )

    # --- Data Access ---

    def update_data(self, new_data: pd.DataFrame) -> None:
        n = len(new_data) if new_data is not None else 0
        log.info("PandasModel updated — %d rows, %d cols",
                 n, new_data.shape[1] if new_data is not None and not new_data.empty else 0)
        self.beginResetModel()
        self._data = new_data.copy() if new_data is not None else pd.DataFrame()
        self.endResetModel()
        if not self._data.empty:
            top = self.index(0, 0)
            bottom = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(top, bottom)

    def get_row(self, row_idx: int) -> dict:
        """Return row as a dict."""
        if 0 <= row_idx < len(self._data):
            return self._data.iloc[row_idx].to_dict()
        return {}

    def get_dataframe(self) -> pd.DataFrame:
        return self._data.copy()


class WatchlistSelectionModel(QtCore.QAbstractTableModel):
    """
    Qt table model managing the user's selected watchlist series.

    Columns: id, source, title
    """

    COLUMNS = ["id", "source", "title"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = pd.DataFrame(columns=self.COLUMNS)

    # --- Qt Model Abstraction ---

    def rowCount(self, parent=...):
        return len(self._data)

    def columnCount(self, parent=...):
        return len(self.COLUMNS)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            col = self.COLUMNS[index.column()]
            return str(self._data.iloc[index.row()][col])
        return None

    def headerData(
        self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole
    ):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.COLUMNS[section]
        return None

    def flags(self, index):
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        )

    # --- Selection Mutations ---

    def add_series(self, series_row: dict) -> None:
        """
        Add a series from a row dict (must contain 'id', 'source', 'title').
        Duplicates (same id+source) are ignored.
        """
        sid = str(series_row.get("id", ""))
        src = str(series_row.get("source", ""))
        title = str(series_row.get("title", sid))

        # Deduplicate
        if sid and src:
            mask = (self._data["id"] == sid) & (self._data["source"] == src)
            if mask.any():
                return

        row_idx = len(self._data)
        self.beginInsertRows(QtCore.QModelIndex(), row_idx, row_idx)
        new_row = pd.DataFrame([[sid, src, title]], columns=self.COLUMNS)
        self._data = pd.concat([self._data, new_row], ignore_index=True)
        self.endInsertRows()

    def remove_rows(self, row_indices: list[int]) -> None:
        """Remove rows by their integer indices."""
        if not row_indices:
            return
        rows_to_remove = sorted(set(row_indices), reverse=True)
        for r in rows_to_remove:
            if 0 <= r < len(self._data):
                self.beginRemoveRows(QtCore.QModelIndex(), r, r)
                self._data = self._data.drop(r).reset_index(drop=True)
                self.endRemoveRows()

    def clear(self) -> None:
        if self._data.empty:
            return
        self.beginResetModel()
        self._data = pd.DataFrame(columns=self.COLUMNS)
        self.endResetModel()

    def update_data(self, new_data: pd.DataFrame) -> None:
        self.beginResetModel()
        self._data = new_data.copy() if new_data is not None else pd.DataFrame(columns=self.COLUMNS)
        self.endResetModel()

    # --- Convenience ---

    def to_dataframe(self) -> pd.DataFrame:
        return self._data.copy()

    def get_row(self, row_idx: int) -> dict:
        if 0 <= row_idx < len(self._data):
            return self._data.iloc[row_idx].to_dict()
        return {}


class SearchWorker(QtCore.QRunnable):
    """
    Runnable worker that runs a WatchlistSearch call in a background thread.

    Signals are emitted on completion / error and are automatically queued
    to the receiver's thread via Qt.QueuedConnection.
    """

    class Signals(QtCore.QObject):
        finished = QtCore.pyqtSignal(pd.DataFrame)
        error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        search_client,
        source: str,
        query: str,
    ):
        super().__init__()
        self.search_client = search_client
        self.source = source  # "all" or a specific source name
        self.query = query
        self.signals = self.Signals()

    def run(self):
        t0 = time.perf_counter()
        log.info("SearchWorker starting — source=%s query=%r", self.source, self.query)
        try:
            if self.source == "all":
                df = self.search_client.search_all(self.query)
            else:
                df = self.search_client.search(self.source, self.query)
            elapsed = time.perf_counter() - t0
            n = len(df)
            log.info("SearchWorker done — %d result(s) in %.2fs", n, elapsed)
            self.signals.finished.emit(df)
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            log.error("SearchWorker failed after %.2fs: %s", elapsed, exc)
            self.signals.error.emit(str(exc))

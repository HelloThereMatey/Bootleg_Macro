"""
WatchlistBuilderWindow — main GUI window for bm watchlist building.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from bootleg_datafeed import Dataset, SOURCES
from bootleg_datafeed._user_path import get_user_path
from bootleg_toolz import Watchlist
from bootleg_datafeed import WatchlistSearch
from bootleg_gui.gui._models import PandasModel, SearchWorker, WatchlistSelectionModel
from bootleg_gui.gui._logging import log
from bootleg_gui.gui.widgets import ResultsTable, SearchBar, WatchlistPanel


class WatchlistBuilderWindow(QtWidgets.QMainWindow):
    """
    Main GUI window for watchlist creation and search.

    Features:
        - Search across all bm data sources via WatchlistSearch
        - Double-click search results to add series to the watchlist
        - View, remove, and clear watchlist selections
        - Save watchlist as Excel (.xlsx + .h5s sidecar) or CSV
        - Load existing watchlists from Excel or CSV

    Public API:
        get_watchlist() -> Watchlist
        set_watchlist(wl: Watchlist) -> None
        load_watchlist(filepath: str) -> None
    """

    def __init__(
        self,
        watchlist: Watchlist | None = None,
        watchlists_path: str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ):
        super().__init__(parent)
        log.info("Initialising WatchlistBuilderWindow")
        self._watchlist: Watchlist | None = None
        self._watchlists_path = watchlists_path or self._default_watchlists_path()
        self._search_client = WatchlistSearch()
        self._results_model = PandasModel()
        self._selection_model = WatchlistSelectionModel()

        self._setup_ui()
        self._connect_signals()
        self._populate_source_dropdown()
        log.info("WatchlistBuilderWindow ready — path=%s", self._watchlists_path)

    def _ensure_watchlist(self) -> Watchlist:
        """Get or create the current watchlist."""
        if self._watchlist is None:
            self._watchlist = Watchlist(name="untitled")
            log.info("Created new default watchlist (name='untitled')")
        return self._watchlist

    def get_watchlist(self) -> Watchlist | None:
        """Return the current watchlist (None if not yet created)."""
        return self._watchlist

    def set_watchlist(self, watchlist: Watchlist) -> None:
        """Load an existing Watchlist for display/editing."""
        log.info("Loading watchlist — %d series, name=%s",
                 len(watchlist.watchlist), watchlist.name)
        self._watchlist = watchlist
        df = watchlist.watchlist.copy() if not watchlist.watchlist.empty else watchlist.watchlist
        self._selection_model.update_data(df)

    def load_watchlist(self, filepath: str) -> None:
        """Load watchlist from .xlsx or .csv file."""
        if not filepath or not os.path.isfile(filepath):
            log.warning("load_watchlist called with missing file: %s", filepath)
            return
        log.info("Loading watchlist from: %s", filepath)
        wl = Watchlist()
        if filepath.endswith(".csv"):
            wl.load_watchlist_csv(filepath)
        else:
            wl.load_watchlist(filepath)
        self.set_watchlist(wl)

    # --- Setup ---

    def _setup_ui(self):
        self.setWindowTitle("Watchlist Builder — bm")
        self.resize(1200, 720)

        # Central widget
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setSpacing(6)
        outer.setContentsMargins(8, 8, 8, 8)

        # Menu bar
        self._setup_menu_bar()

        # Search area
        self.search_bar = SearchBar(SOURCES, parent=self)
        self.search_bar.setMinimumWidth(600)
        outer.addWidget(self.search_bar)

        # Results table
        self.results_table = ResultsTable(parent=self)
        self.results_table.setModel(self._results_model)
        outer.addWidget(self.results_table, stretch=2)

        # Watchlist panel
        self.watchlist_panel = WatchlistPanel(parent=self)
        self.watchlist_panel.set_selection_model(self._selection_model)
        outer.addWidget(self.watchlist_panel, stretch=1)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)

    def _setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        new_action = file_menu.addAction("New Watchlist", self._on_new_watchlist)
        new_action.setShortcut(QtGui.QKeySequence.StandardKey.New)

        open_action = file_menu.addAction(
            "Open Watchlist…", self._on_open_watchlist
        )
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)

        save_action = file_menu.addAction(
            "Save Watchlist…", self._on_save_watchlist
        )
        save_action.setShortcut(QtGui.QKeySequence.StandardKey.Save)

        file_menu.addSeparator()

        quit_action = file_menu.addAction(
            "Quit", self.close
        )
        quit_action.setShortcut(QtGui.QKeySequence.StandardKey.Quit)

        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About bm", self._on_about)

    def _connect_signals(self):
        # Search
        self.search_bar.search_triggered.connect(self._on_search_triggered)
        self.results_table.series_double_clicked.connect(
            self._on_series_double_clicked
        )
        # Watchlist panel
        self.watchlist_panel.remove_requested.connect(
            self._on_remove_requested
        )
        self.watchlist_panel.clear_requested.connect(
            self._on_clear_requested
        )
        self.watchlist_panel.save_requested.connect(
            self._on_save_requested
        )
        self.watchlist_panel.load_requested.connect(
            self._on_load_requested
        )

    def _populate_source_dropdown(self):
        # Sources are already populated in SearchBar via SourceSelector
        pass

    # --- Search ---

    def _on_search_triggered(self, query: str, source: str):
        log.info("Search triggered — source=%s query=%r", source, query)
        self.search_bar.set_searching(True)
        self.status_bar.showMessage(f"Searching {source} for '{query}'…")

        worker = SearchWorker(self._search_client, source, query)
        worker.signals.finished.connect(self._on_search_finished)
        worker.signals.error.connect(self._on_search_error)
        QtCore.QThreadPool.globalInstance().start(worker)

    def _on_search_finished(self, df):
        self._results_model.update_data(df)
        self.search_bar.set_searching(False)
        n = len(df)
        log.info("Search finished — %d result%s", n, "s" if n != 1 else "")
        self.status_bar.showMessage(
            f"Found {n} result{'s' if n != 1 else ''}"
        )

    def _on_search_error(self, err_msg: str):
        self.search_bar.set_searching(False)
        log.error("Search error: %s", err_msg)
        self.status_bar.showMessage(f"Search error: {err_msg}")
        QtWidgets.QMessageBox.warning(
            self, "Search Error", err_msg
        )

    # --- Series Selection ---

    def _on_series_double_clicked(self, row_dict: dict):
        sid = str(row_dict.get("id", ""))
        src = str(row_dict.get("source", ""))
        title = str(row_dict.get("title", sid))

        # Auto-create a watchlist if none is loaded yet
        wl = self._ensure_watchlist()

        log.info("Adding %s (%s) → watchlist '%s'", sid, src, wl.name)

        # Build a minimal StandardSeries and append to the watchlist
        from bootleg_datafeed.models import SeriesMetadata, StandardSeries

        meta = SeriesMetadata(id=sid, title=title, source=src)
        ss = StandardSeries(data={}, metadata=meta)
        wl.append_series(ss)

        # Also add to the selection display table
        self._selection_model.add_series({
            "id": sid,
            "source": src,
            "title": title,
        })

        self.status_bar.showMessage(f"Added: {sid} ({src})")

    def _on_remove_requested(self, row_indices: list[int]):
        if self._selection_model is None:
            return
        rows_to_remove = sorted(set(row_indices), reverse=True)
        removed_ids = []
        for r in rows_to_remove:
            if 0 <= r < len(self._selection_model.to_dataframe()):
                df = self._selection_model.to_dataframe()
                row = df.iloc[r]
                sid = str(row["id"])
                if self._watchlist is not None:
                    self._watchlist.drop_series(sid)
                removed_ids.append(sid)
        self._selection_model.remove_rows(row_indices)
        log.info("Removed series: %s", removed_ids or row_indices)
        self.status_bar.showMessage("Removed selected series")

    def _on_clear_requested(self):
        log.info("Clearing watchlist")
        self._selection_model.clear()
        # Rebuild watchlist from selection model
        wl_name = self._watchlist.name if self._watchlist else "untitled"
        wl = Watchlist(name=wl_name)
        for _, row in self._selection_model.to_dataframe().iterrows():
            from bootleg_datafeed.models import SeriesMetadata, StandardSeries
            meta = SeriesMetadata(
                id=str(row["id"]),
                title=str(row["title"]),
                source=str(row["source"]),
            )
            wl.append_series(StandardSeries(data={}, metadata=meta))
        self._watchlist = wl
        self.status_bar.showMessage("Cleared all selections")

    # --- File dialogs (overridable for custom behavior) ---

    def _choose_file_to_open(self) -> str | None:
        """Show an open-file dialog and return the chosen path, or None if cancelled."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Watchlist",
            self._watchlists_path,
            "Excel Files (*.xlsx);;CSV Files (*.csv)",
        )
        return path if path else None

    def _choose_file_to_save(self) -> str | None:
        """Show a save-file dialog and return the chosen path, or None if cancelled."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Watchlist",
            self._watchlists_path,
            "Excel Files (*.xlsx);;CSV Files (*.csv)",
        )
        return path if path else None

    # --- File Operations ---

    def _on_new_watchlist(self):
        log.info("New watchlist created")
        self._watchlist = Watchlist(name="untitled")
        self._selection_model.clear()
        self.status_bar.showMessage("New watchlist started")

    def _on_open_watchlist(self):
        path = self._choose_file_to_open()
        if path:
            log.info("Opening watchlist: %s", path)
            self.load_watchlist(path)
            self.status_bar.showMessage(f"Loaded: {path}")

    def _on_save_watchlist(self):
        path = self._choose_file_to_save()
        if path:
            log.info("Saving watchlist via menu: %s", path)
            self._do_save(path)

    def _on_save_requested(self, _):
        # Panel button emits empty string — open dialog here
        path = self._choose_file_to_save()
        if path:
            log.info("Saving watchlist via panel: %s", path)
            self._do_save(path)

    def _on_load_requested(self, _):
        # Panel button emits empty string — open dialog here
        path = self._choose_file_to_open()
        if path:
            log.info("Loading watchlist via panel: %s", path)
            self.load_watchlist(path)
            self.status_bar.showMessage(f"Loaded: {path}")

    def _do_save(self, path: str):
        log.info("Saving watchlist to: %s", path)
        # Sync selection model to watchlist before saving
        from bootleg_datafeed.models import SeriesMetadata, StandardSeries

        # Derive watchlist name from filename
        stem = Path(path).stem

        wl = Watchlist(name=stem)
        for _, row in self._selection_model.to_dataframe().iterrows():
            meta = SeriesMetadata(
                id=str(row["id"]),
                title=str(row["title"]),
                source=str(row["source"]),
            )
            wl.append_series(StandardSeries(data={}, metadata=meta))

        try:
            if path.endswith(".csv"):
                wl.save_watchlist_csv(path)
            else:
                wl.save_watchlist(path)
            log.info("Watchlist saved OK — %d series", len(wl.watchlist))
            self.status_bar.showMessage(f"Saved: {path}")
        except Exception as exc:
            log.error("Save failed: %s", exc)
            QtWidgets.QMessageBox.warning(
                self, "Save Error", str(exc)
            )

    # --- Help ---

    def _on_about(self):
        log.info("About dialog shown")
        QtWidgets.QMessageBox.about(
            self,
            "About bm Watchlist Builder",
            "<h3>bm — Bootleg Macro Data Library</h3>"
            "<p>PyQt6 GUI for building watchlists from financial "
            "and economic data sources.</p>"
            "<p>Search, select, save — all in one place.</p>",
        )

    # --- Helpers ---

    @staticmethod
    def _default_watchlists_path() -> str:
        path = Path(get_user_path()) / "Watchlists"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    # --- Launcher ---

    @classmethod
    def run(cls) -> "WatchlistBuilderWindow":
        """Launch the GUI and return the window instance after it closes.

        Use this to launch from a script or notebook:

            window = WatchlistBuilderWindow.run()
        """
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        window = cls()
        window.show()
        app.exec()
        return window


def launch() -> WatchlistBuilderWindow:
    """Launch the WatchlistBuilderWindow GUI.

    Shortcut so the GUI can be opened with a single function call from
    any Python environment (scripts, notebooks, REPL):

        from bootleg_gui.gui import launch
        window = launch()
    """
    return WatchlistBuilderWindow.run()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = WatchlistBuilderWindow()
    window.show()
    sys.exit(app.exec())
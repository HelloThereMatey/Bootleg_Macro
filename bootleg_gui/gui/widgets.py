"""
Reusable widget components for the bm GUI.
"""

from __future__ import annotations

import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets

from bootleg_gui.gui._models import PandasModel, WatchlistSelectionModel
from bootleg_gui.gui._logging import log


class SourceSelector(QtWidgets.QComboBox):
    """Dropdown for selecting a single source or 'all'."""

    ALL_LABEL = "All Sources"

    def __init__(self, sources: list[str], parent=None):
        super().__init__(parent)
        self.addItem(self.ALL_LABEL)
        self.addItems(sorted(sources))
        self.setCurrentIndex(0)

    def current_source(self) -> str:
        text = self.currentText()
        return "all" if text == self.ALL_LABEL else text


class SearchBar(QtWidgets.QWidget):
    """
    Top search controls: query input, source selector, and search button.

    Signals:
        search_triggered(str, str): — (query, source_or_"all")
    """

    search_triggered = QtCore.pyqtSignal(str, str)

    def __init__(self, sources: list[str], parent=None):
        super().__init__(parent)
        self._sources = sources
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.query_input = QtWidgets.QLineEdit(parent=self)
        self.query_input.setPlaceholderText("Search… (comma for multi-term, * for wildcard)")
        self.query_input.setMinimumWidth(300)

        self.source_selector = SourceSelector(self._sources, parent=self)
        self.source_selector.setMinimumWidth(130)

        self.search_button = QtWidgets.QPushButton("Search", parent=self)
        self.search_button.setMinimumWidth(90)

        layout.addWidget(self.query_input, stretch=1)
        layout.addWidget(self.source_selector)
        layout.addWidget(self.search_button)

    def _connect_signals(self):
        self.search_button.clicked.connect(self._on_search_clicked)
        self.query_input.returnPressed.connect(self._on_search_clicked)

    def _on_search_clicked(self):
        query = self.query_input.text().strip()
        if not query:
            return
        source = self.source_selector.current_source()
        log.info("Search button clicked — source=%s query=%r", source, query)
        self.search_triggered.emit(query, source)

    def set_searching(self, is_searching: bool) -> None:
        """Disable controls while a search is in progress."""
        self.query_input.setEnabled(not is_searching)
        self.source_selector.setEnabled(not is_searching)
        self.search_button.setEnabled(not is_searching)
        if is_searching:
            self.search_button.setText("Searching…")
        else:
            self.search_button.setText("Search")

    def get_query(self) -> str:
        return self.query_input.text().strip()

    def get_selected_source(self) -> str:
        return self.source_selector.current_source()


class ResultsTable(QtWidgets.QTableView):
    """
    Table view displaying search results.

    Double-clicking a row emits `series_double_clicked` with the full row dict.

    Signals:
        series_double_clicked(dict): — row dict with id/title/source keys
    """

    series_double_clicked = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QTableView.SelectionMode.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        self.setWordWrap(False)
        self._model: PandasModel | None = None

    def setModel(self, model):
        """Override so we track the model reference for double-click lookup."""
        super().setModel(model)
        self._model = model

    def setModel(self, model):
        """Override so we track the model reference for double-click lookup."""
        super().setModel(model)
        self._model = model

    def set_results(self, df: pd.DataFrame) -> None:
        """Populate the table with search results DataFrame."""
        if self._model is None:
            self._model = PandasModel(df)
            self.setModel(self._model)
        else:
            self._model.update_data(df)

    def clear(self) -> None:
        if self._model:
            self._model.update_data(pd.DataFrame())

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        """Emit series_double_clicked with the full row dict."""
        super().mouseDoubleClickEvent(event)
        index = self.indexAt(event.pos())
        if index.isValid() and self._model is not None:
            row_dict = self._model.get_row(index.row())
            if row_dict:
                log.info("Result double-clicked — row %d: id=%s source=%s",
                         index.row(), row_dict.get("id"), row_dict.get("source"))
                self.series_double_clicked.emit(row_dict)


class WatchlistPanel(QtWidgets.QWidget):
    """
    Bottom panel showing the user's selected series and action buttons.

    Signals:
        remove_requested(list[int]): — row indices to remove
        clear_requested():           — clear all selections
        save_requested(str):         — file path to save
        load_requested(str):         — file path to open
    """

    remove_requested = QtCore.pyqtSignal(list)
    clear_requested = QtCore.pyqtSignal()
    save_requested = QtCore.pyqtSignal(str)
    load_requested = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selection_model: WatchlistSelectionModel | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Table view for selected series
        self.table_view = QtWidgets.QTableView(parent=self)
        self.table_view.setSelectionBehavior(
            QtWidgets.QTableView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QtWidgets.QTableView.SelectionMode.ExtendedSelection
        )
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )

        # Button row
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(6)

        self.remove_btn = QtWidgets.QPushButton("Remove Selected", parent=self)
        self.clear_btn = QtWidgets.QPushButton("Clear All", parent=self)
        self.load_btn = QtWidgets.QPushButton("Load Watchlist", parent=self)
        self.save_btn = QtWidgets.QPushButton("Save Watchlist", parent=self)

        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)

        layout.addWidget(self.table_view, stretch=1)
        layout.addLayout(btn_layout)

        # Signals
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)

    def set_selection_model(self, model: WatchlistSelectionModel) -> None:
        self._selection_model = model
        self.table_view.setModel(model)

    def get_selection_model(self) -> WatchlistSelectionModel | None:
        return self._selection_model

    def _on_remove_clicked(self):
        if self._selection_model is None:
            return
        rows = [i.row() for i in self.table_view.selectionModel().selectedRows()]
        if rows:
            log.info("Remove button clicked — %d row(s)", len(rows))
            self.remove_requested.emit(rows)

    def _on_clear_clicked(self):
        log.info("Clear All button clicked")
        self.clear_requested.emit()

    def _on_load_clicked(self):
        log.info("Load Watchlist button clicked")
        # Emit with empty string — caller should open dialog
        self.load_requested.emit("")

    def _on_save_clicked(self):
        log.info("Save Watchlist button clicked")
        # Emit with empty string — caller should open dialog
        self.save_requested.emit("")

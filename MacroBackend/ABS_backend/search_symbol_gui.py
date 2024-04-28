import pandas as pd
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

import os
import sys
wd = os.path.dirname(__file__); parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(grampa)

from MacroBackend import Utilities

abs_index_path = grampa+fdel+"User_Data"+fdel+"ABS"+fdel+"ABS_Series_MasterIndex.csv"

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self._data.columns[section])
        if orientation == QtCore.Qt.Orientation.Vertical and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return str(self._data.index[section])
        return None


##### My main window class ####################
class Ui_MainWindow(object):
    def __init__(self, MainWindow: QtWidgets.QMainWindow):
        self.setupUi(MainWindow)
        self.setupWidgets()
        self.connectSignals()

    def setupUi(self, MainWindow: QtWidgets.QMainWindow):
        # Set the application icon
        icon = QtGui.QIcon(wd+fdel+"app_icon.png")  # Update the path to where your icon is stored
        print("Icon path: ", wd+fdel+"app_icon.png", icon.__str__())
        MainWindow.setWindowIcon(icon)
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Search for the symbols of various time series from a number of sources")
        MainWindow.resize(1617, 586)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 731, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuAbout = QtWidgets.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        self.menubar.addAction(self.menuAbout.menuAction())

    def setupWidgets(self):
        font = QtGui.QFont()
        font.setFamily("Sans Serif")
        font.setPointSize(14)

        self.source_dropdown = QtWidgets.QComboBox(self.centralwidget)
        self.source_dropdown.setGeometry(QtCore.QRect(1220, 10, 211, 31))
        self.source_dropdown.setFont(font)
        self.source_dropdown.setObjectName("source_dropdown")

        self.searchstr_entry = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.searchstr_entry.setGeometry(QtCore.QRect(10, 10, 691, 31))
        self.searchstr_entry.setFont(font)
        self.searchstr_entry.setObjectName("searchstr_entry")
        self.searchstr = ""

        self.run_search = QtWidgets.QPushButton("Search Symbol", parent=self.centralwidget)
        self.run_search.setGeometry(QtCore.QRect(1450, 10, 161, 31))
        font = QtGui.QFont(); font.setPointSize(12)
        self.run_search.setFont(font)
        self.run_search.setObjectName("run_search_symbol")

        self.results = QtWidgets.QTableView(self.centralwidget)
        self.results.setGeometry(QtCore.QRect(10, 50, 1601, 481))
        self.results.setObjectName("results")

        self.resizeModeButton = QtWidgets.QRadioButton("Adjust column widths",parent=self.centralwidget)
        self.resizeModeButton.setGeometry(QtCore.QRect(960, 10, 200, 31))
        font = QtGui.QFont(); font.setPointSize(12); self.resizeModeButton.setFont(font)
        self.resizeModeButton.setObjectName("interactive_resize")
        self.resizeModeButton.setChecked(False)
        self.resizeModeButton.hide()  # Initially hide the button

    def add_sources(self, sources: dict):
        self.added_sources = sources
        self.source_dropdown.addItems(self.added_sources)

    def connectSignals(self):
        self.searchstr_entry.textChanged.connect(self.update_searchstr)
        self.source_dropdown.currentIndexChanged.connect(self.dropdown_changed)
        self.run_search.clicked.connect(self.run_search_df)
    
    def update_searchstr(self):
        self.searchstr = self.searchstr_entry.toPlainText()

    def dropdown_changed(self):
        self.selected_source = self.source_dropdown.currentText()
        print(f"Selected source: {self.selected_source}")
        if isinstance(self.selected_source, str):
            self.source_table_path = sources[self.selected_source]
        else:
            self.source_table_path = None
    
    def run_search_df(self):
        if self.source_table_path:
            print("Loading index of ABS time-series to dataframe from: ", self.source_table_path)
            df = pd.read_csv(self.source_table_path, index_col=0)
            results = Utilities.Search_DF(df, self.searchstr)
            if len(results) == 0:
                print("No results found, check search terms.")
                results = pd.DataFrame(["No results found, check search terms.",\
                    "The search uses regex to match words exactly so spelling mistakes etc. are not tolerated."], columns = ["Result"], index=[0, 1])
            # Set the model to the QTableView
            self.model = PandasModel(results)
            self.results.setModel(self.model)
            self.updateToggleButtonVisibility()

            # Configure the horizontal header to initially stretch columns, then allow resizing
            self.tableheader = self.results.horizontalHeader()
            self.tableheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

            self.resizeModeButton.toggled.connect(self.toggle_resize_mode)

        else:
            print("No source table selected")

    def updateToggleButtonVisibility(self):
        if self.results.model() and self.results.model().rowCount() > 0:
            self.resizeModeButton.show()
        else:
            self.resizeModeButton.hide()
        
    def toggle_resize_mode(self, checked):
        if checked:
            self.tableheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        else:
            self.tableheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

if __name__ == "__main__":

    sources = {'fred': "", 
               'yfinance': "", 
               'tv': "", 
               'coingecko': "", 
               'quandl': "", 
               'glassnode': "", 
               'abs': abs_index_path}
    
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    ui.add_sources(sources.keys())
    MainWindow.show()
    sys.exit(app.exec())




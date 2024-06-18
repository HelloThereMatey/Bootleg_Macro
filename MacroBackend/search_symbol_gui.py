import pandas as pd
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

import os
import sys
wd = os.path.dirname(__file__); parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(parent)

from MacroBackend import Utilities, PriceImporter, js_funcs, Glassnode

keys = Utilities.api_keys().keys
abs_index_path = parent+fdel+"User_Data"+fdel+"ABS"+fdel+"ABS_Series_MasterIndex.csv"
cG_allshitsPath = wd+fdel+"AllCG.csv"
metricsListPath = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"

######## Custom classess ##################

class MyTableView(QtWidgets.QTableView):
    returnPressed = QtCore.pyqtSignal()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.returnPressed.emit()

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
        self.search_results = None
        self.tableheader = None
        self.results_count = 0
        self.selected_row = None
        self.return_dict = {}

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
        self.source_dropdown.setGeometry(QtCore.QRect(1220, 12, 211, 31))
        self.source_dropdown.setFont(font)
        self.source_dropdown.setObjectName("source_dropdown")

        self.searchstr_entry = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.searchstr_entry.setGeometry(QtCore.QRect(10, 10, 691, 31))
        self.searchstr_entry.setFont(font)
        self.searchstr_entry.setObjectName("searchstr_entry")
        self.searchstr = ""

        self.run_search = QtWidgets.QPushButton("Search Source", parent=self.centralwidget)
        self.run_search.setGeometry(QtCore.QRect(1450, 8, 161, 40))
        font = QtGui.QFont(); font.setPointSize(14)
        self.run_search.setFont(font)
        self.run_search.setObjectName("run_search_symbol")

        self.results = QtWidgets.QTableView(self.centralwidget)
        self.results.setGeometry(QtCore.QRect(10, 50, 1601, 481))
        self.results.setObjectName("results")

        self.numres = QtWidgets.QLabel("Number of results", parent=self.centralwidget)
        self.numres.setGeometry(QtCore.QRect(730, 10, 100, 30))

        self.clear_button = QtWidgets.QPushButton("Clear results", parent=self.centralwidget)
        self.clear_button.setGeometry(QtCore.QRect(960, 8, 100, 40))
        font = QtGui.QFont(); font.setPointSize(12)

    def add_sources(self, sources: dict):
        self.sources = sources
        self.source_dropdown.addItems(self.sources.keys())

    def connectSignals(self):
        self.searchstr_entry.textChanged.connect(self.update_searchstr)
        self.source_dropdown.currentIndexChanged.connect(self.dropdown_changed)
        self.run_search.clicked.connect(self.run_search_df)
        self.clear_button.clicked.connect(self.clear_results)
        self.results.doubleClicked.connect(self.select_row)
    
    def update_searchstr(self):
        self.searchstr = self.searchstr_entry.toPlainText()
    
    def dropdown_changed(self):
        self.selected_source = self.source_dropdown.currentText()
        value = self.sources[self.selected_source]
        print(f"Selected source: {self.selected_source}")

        # Check if the source_value is a callable (i.e., a function)
        if callable(value):
            # It's a function, call the function
            print("The source value is a function...")
            self.source_table_path = None
            self.source_function = value
        elif isinstance(value, str):
            # It's a string, treat it as a file path
            print("The source is a file path...")
            self.source_table_path = value
            self.source_function = None
        else:
            # If it's neither, set to None or handle appropriately
            print("For the selected source, ", self.selected_source, ", no method of searching has been set yet....")
            self.source_table_path = None
            self.source_function = None
        return

    def run_search_df(self):
        split = self.searchstr.strip().split(",")
        terms = [x.strip() for x in split]
        i = 0

        for term in terms:
            if self.search_results is not None:
                results = Utilities.Search_DF(self.search_results, term)
            else:
                if self.source_table_path is not None:
                    print("Loading index of ABS time-series to dataframe from: ", self.source_table_path)
                    df = pd.read_csv(self.source_table_path, index_col=0)
                    results = Utilities.Search_DF(df, term)
                    if len(results) == 0:
                        print("No results found, check search terms.")
                        results = pd.DataFrame(["No results found, check search terms.",\
                            "The search uses regex to match words exactly so spelling mistakes etc. are not tolerated."], columns = ["Result"], index=[0, 1])
            
                elif self.source_function is not None:
                    if self.selected_source == 'fred':
                        results = self.source_function(term, keys['fred'], save_output=False)
                    elif self.selected_source == 'tv':    
                        resdict = self.source_function(searchstr = term)
                        results = pd.DataFrame(resdict).T
                    elif self.selected_source == 'yfinance':
                        resdict = self.source_function(searchstr = term)
                        results = resdict['tickers_df']
                    else:
                        print("No source table selected")
                        return    
                
                else:
                    print("No source table selected")
                    return
            if results.empty:   # If no results are found, display a message
                print("No results found, check search terms.")
                results = pd.DataFrame(["No results found, check search terms.",\
                "The search uses regex to match words exactly so spelling mistakes etc. are not tolerated."], columns = ["Result"], index=[0, 1])

            self.search_results = results

        self.model = PandasModel(self.search_results)  # Set the model to the QTableView
        self.results_count = len(self.search_results)
        self.results.setModel(self.model)
        self.numres.setText(str(self.results_count))
        if self.tableheader is None:
            self.tableheader = self.results.horizontalHeader()
    
        self.tableheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        return
    
    def clear_results(self):
        self.search_results = None
        self.results.setModel(None)
        self.tableheader = None
        return
    
    def select_row(self, index):
        self.selected_row = self.search_results.iloc[index.row()]
        print("Row selected: ", self.selected_row)
        self.add_row_to_return_dict()
    
    def add_row_to_return_dict(self):
        if self.selected_row is not None:
            self.return_dict[self.selected_row.name] = self.selected_row
            print("Series addded to return dict: ", self.selected_row)
    
    # def cleanup(self):
    #     self.deleteLater()

##### STANDALONE FUNCTIONS ####################

def update_GNmetrics():
    path = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"
    old_df = pd.read_csv(path, index_col=0)
    print("Number of metrics in existing table: ", len(old_df))
    gnmets = Glassnode.GlassNode_API.UpdateGNMetrics(keys['glassnode'])
    print("Number of metrics in new table: ", len(gnmets))
    path = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"
    gnmets.to_csv(path)

def run_app():
    sources = {'fred': PriceImporter.FREDSearch, 
            'yfinance': js_funcs.search_yf_tickers, 
            'tv': js_funcs.js_search_tv, 
            'coingecko': cG_allshitsPath, 
            'quandl': None, 
            'glassnode': metricsListPath, 
            'abs': abs_index_path}
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    ui.add_sources(sources)
    MainWindow.show()

    #app.aboutToQuit.connect(ui.cleanup)
    app.exec()
    return ui.return_dict

if __name__ == "__main__":

    resultsdict = run_app()
    print("Results dict: \n\n\n", resultsdict)
    # update_GNmetrics()



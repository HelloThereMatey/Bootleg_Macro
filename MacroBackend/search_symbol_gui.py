import pandas as pd
import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

import os
import sys
wd = os.path.dirname(__file__); parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(parent)

from MacroBackend import Utilities, PriceImporter, js_funcs, Glassnode, Pull_Data
from MacroBackend.BEA_Data import bea_data_mate

keys = Utilities.api_keys().keys
abs_index_path = parent+fdel+"User_Data"+fdel+"ABS"+fdel+"ABS_Series_MasterIndex.csv"
cG_allshitsPath = wd+fdel+"AllCG.csv"
metricsListPath = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"
bea_path = wd+fdel+"BEA_Data"+fdel+"Datasets"+fdel+"BEA_First3_Datasets.csv"
watchlists_path_def = parent+fdel+"User_Data"+fdel+"Watchlists"

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
        if isinstance(self._data, pd.Series):
            self._data = self._data.reset_index()
            return 1
        else:
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

import pandas as pd

class Watchlist(dict):
    def __init__(self, watchlist_data=None, metadata_data=None, watchlist_name: str = "base_watchlist", watchlists_path: str = parent+fdel+"User_Data"+fdel+"Watchlists"):
        super().__init__()
        # Initialize watchlist and metadata as pandas DataFrames
        self.name = watchlist_name
        self.watchlists_path = watchlists_path
        self['watchlist'] = pd.DataFrame(watchlist_data) if watchlist_data is not None else pd.DataFrame()
        self['metadata'] = pd.DataFrame(metadata_data) if metadata_data is not None else pd.DataFrame()

    def load_watchlist(self, filepath: str = None):
        # Example method to load watchlist data from an Excel file
        if filepath is not None:
            self['watchlist'] = pd.read_excel(filepath, index_col=0, sheet_name="watchlist")
            self['metadata'] = pd.read_excel(filepath, index_col=0, sheet_name="all_metadata")
            self.name = filepath.split(fdel)[-1].split(".")[0]

        else:
            print("Code was reachable...")
            temp_app = QtWidgets.QApplication.instance()
            fileName, sick = QtWidgets.QFileDialog.getOpenFileName(temp_app, "Choose a watchlist excel file.", self.watchlists_path, "Excel Files (*.xlsx);;All Files (*)", options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)
            # Start the application's event loop
            sys.exit(temp_app.exec())    
            if fileName:
                try:
                    self['watchlist'] = pd.read_excel(fileName, index_col=0, sheet_name="watchlist")
                    self['metadata'] = pd.read_excel(fileName, index_col=0, sheet_name="all_metadata")
                    self.name = fileName.split(fdel)[-1].split(".")[0]
                except Exception as e:
                    print("Error loading watchlist data from file, '.xlsx file may have had the wrong format for a watchlist,\
                          you want two sheets named 'watchlist' and 'all_metadata' with tables that can form dataframes in each. Exception:", e)
                    return None
        # Implement similar for metadata if needed
    
    def append_current_watchlist(self, watchlist_data: pd.DataFrame, metadata_data: pd.DataFrame):
        # Append new data to the current watchlist
        self['watchlist'] = pd.concat([self['watchlist'], watchlist_data], axis=0)
        self['metadata'] = pd.concat([self['metadata'], metadata_data], axis=1)

    def save_watchlist(self, path: str = parent+fdel+"User_Data"+fdel+"Watchlists"):
        # Example method to save watchlist data to an Excel file
        with pd.ExcelWriter(path+fdel+self.name.replace(" ", "_")+".xlsx") as writer:
            self['watchlist'].to_excel(writer, sheet_name='watchlist')
            self['metadata'].to_excel(writer, sheet_name='all_metadata')

    def get_watchlist_data(self, start_date: str = "1990-01-02"):
        """get_watchlist_data method.
        This function takes a Watchlist object and returns a dictionary of pandas Series and/or dataframe objects.
        Data will be pulled from the source listed for each asset/ticker/macrodata code in the watchlist.

        Parameters:

        - Watchlist: search_symbol_gui.Watchlist object
        - start_date: str, default "1990-01-02"
        """

        watchlist = pd.DataFrame(self["watchlist"]); meta = pd.DataFrame(self["metadata"])
        data = {}
        for i in watchlist.index:
            ds = Pull_Data.dataset()
            ds.get_data(source = watchlist.loc[i,"source"], data_code=watchlist.loc[i,"id"], start_date = start_date, \
                        exchange_code = meta.loc["exchange", i])
            data[i] = ds.data
        self["watchlist_datasets"] = data

##### My main window class ####################
class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, MainWindow: QtWidgets.QMainWindow, watchlists_path: str = parent+fdel+"User_Data"+fdel+"Watchlists"):
        super().__init__()
        self.setupUi(MainWindow)
        self.setupWidgets()
        self.connectSignals()
        self.search_results = None
        self.tableheader = None
        self.results_count = 0
        self.selected_row = None
        self.return_dict = {}
        self.return_df = pd.DataFrame()
        self.series_added_count = 0  # Initialize the counter
        self.watchlists_path = watchlists_path
        self.fill_watchlist_box()
        self.current_list = None
        self.previous_selections_wl = []
        self.previous_selections_meta = []  

    def setupUi(self, MainWindow: QtWidgets.QMainWindow):
        # Set the application icon
        icon = QtGui.QIcon(wd+fdel+"app_icon.png")  # Update the path to where your icon is stored
        print("Icon path: ", wd+fdel+"app_icon.png", icon.__str__())
        MainWindow.setWindowIcon(icon)
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Search for the symbols of various time series from a number of sources")
        MainWindow.resize(1617, 600)
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

        self.watchlists = QtWidgets.QComboBox(self.centralwidget)
        self.watchlists.setGeometry(QtCore.QRect(275, 540, 211, 31))
        self.watchlists.setFont(font)
        self.watchlists.setObjectName("watchlists")
        self.watchlabel = QtWidgets.QLabel("Choose a watchlist to add to", parent=self.centralwidget)
        self.watchlabel.setGeometry(QtCore.QRect(90, 535, 200, 40))

        # Save watchlist button
        self.save_watchlist_button = QtWidgets.QPushButton("Save Watchlist", parent=self.centralwidget)
        self.save_watchlist_button.setGeometry(QtCore.QRect(750, 535, 200, 40))  # Adjust the position as needed
        self.save_watchlist_button.setFont(font)
        self.save_watchlist_button.setObjectName("save_watchlist_button")

    def add_sources(self, sources: dict):
        self.sources = sources
        self.source_dropdown.addItems(self.sources.keys())

    def connectSignals(self):
        self.searchstr_entry.textChanged.connect(self.update_searchstr)
        self.source_dropdown.currentIndexChanged.connect(self.dropdown_changed)
        self.run_search.clicked.connect(self.run_search_df)
        self.clear_button.clicked.connect(self.clear_results)
        self.results.doubleClicked.connect(self.select_row)
        self.save_watchlist_button.clicked.connect(self.save_watchlist)
        self.watchlists.currentIndexChanged.connect(self.choose_watchlist)
    
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
                    print("Loading index of time-series data for source: ", self.selected_source, " to dataframe from: ", self.source_table_path)
                    df = pd.read_csv(self.source_table_path, index_col=0)
                    results = Utilities.Search_DF(df, term)
                    
                    if results.empty:
                        print("No results found, check search terms.")
                        results = pd.DataFrame(["No results found, check search terms.",\
                            "The search uses regex to match words exactly so spelling mistakes etc. are not tolerated."], columns = ["Result"], index=[0, 1])
                    elif not results.empty and self.selected_source == 'coingecko':
                        results.rename(columns = {'name': "title"}, inplace=True)
                    elif not results.empty and self.selected_source == 'glassnode':
                        results['id'] = results['path'].apply(lambda x: str(x).split('/')[-1])
                        results['title'] = results['id'].copy()
                    elif not results.empty and self.selected_source == 'abs':
                        results.rename(columns = {'Unnamed: 0': 'line_number', "Series ID": "id", "Data Item Description": "title"}, inplace=True)
                    else:
                        print("Dunno whaat happened here bruv..........")
                        return
            
                elif self.source_function is not None:
                    if self.selected_source == 'fred':
                        results = self.source_function(term, keys['fred'], save_output=False)
                    elif self.selected_source == 'tv':    
                        resdict = self.source_function(searchstr = term)
                        results = pd.DataFrame(resdict).T
                        results.rename(columns = {'id': 'name', "symbol": "id", "description": "title"}, inplace=True)
                    elif self.selected_source == 'yfinance':
                        resdict = self.source_function(searchstr = term)
                        results = resdict['tickers_df']
                        results.rename(columns = {'symbol': 'id', "longname": "title"}, inplace=True)
                    elif self.selected_source == 'bea':
                        results =  self.source_function(term, keys['bea'])
                        results.rename(columns = {'TableId': 'id', "LineDescription": "title", "SeriesCode": "symbol"}, inplace=True)
                    else:
                        print("No source table selected or something like this..... uhhhh...")
                        return    
                
                else:
                    print("No source table selected")
                    return
            if results.empty:   # If no results are found, display a message
                print("No results found, check search terms.")
                results = pd.DataFrame(["No results found, check search terms.",\
                "The search uses regex to match words exactly so spelling mistakes etc. are not tolerated."], columns = ["Result"], index=[0, 1])

            results["source"] = self.selected_source
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
        ser = pd.Series(self.selected_row["id"], name="name", index = ["name"])
        self.selected_row = pd.concat([ser, self.selected_row], axis = 0)  
        self.selected_row = self.selected_row[~self.selected_row.index.duplicated(keep='first')]
        self.selected_row.rename(self.selected_row["id"], inplace=True)
        print("Row selected: ", self.selected_row.name)
        if not "exchange" in self.selected_row.index:
            print("No exchange column found in selected row, adding 'N/A' to exchange column")
            self.selected_row["exchange"] = "N/A"
        self.add_row_to_return_dict() 
    
    def add_row_to_return_dict(self):
        if self.selected_row is not None:
            self.return_dict[self.series_added_count] = self.selected_row
            print("Series addded to return dict: ", self.selected_row.name)
            ser = pd.Series(self.selected_row[["id", "title", "source"]] , name = self.selected_row["name"]).to_frame().T
            self.return_df = pd.concat([self.return_df, ser], axis=0)
            self.series_added_count += 1
    
    def fill_watchlist_box(self):
        # Ensure the directory exists
        if not os.path.exists(self.watchlists_path):
            print(f"Directory {self.watchlists_path} does not exist.")
            return

        # Get all .xlsx files in the directory
        xlsx_files = [f for f in os.listdir(self.watchlists_path) if f.endswith('.xlsx')]
        # Extract filenames without the extension
        watchlist_names = [os.path.splitext(f)[0] for f in xlsx_files]
        
        # Clear current items
        self.watchlists.clear()
        # Add filenames to the QComboBox
        self.watchlists.addItems(watchlist_names)

    def choose_watchlist(self):
        # Get the currently selected watchlist from the dropdown
        selected_watchlist = self.watchlists.currentText()
        
        # Set the current watchlist to the selected one
        self.current_list_name = selected_watchlist
        print(f"Current watchlist set to: {self.current_list_name}")
        self.current_list = Watchlist(watchlist_name=self.current_list_name)
        self.current_list.load_watchlist(filepath=self.watchlists_path+fdel+self.current_list_name+".xlsx")

    def save_watchlist(self):

        watchlist_data = self.return_df
        metadata = org_metadata(self.return_dict)
        print("Watchlist data: \n", watchlist_data, "\n\nMetadata: \n", metadata)

        # Open a save file dialog with .xlsx as the fixed file type
        if self.current_list is None:
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Watchlist", self.watchlists_path,"Excel Files (*.xlsx);;All Files (*)", options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)
            self.current_list_name = fileName.split(fdel)[-1].split(".")[0]
            self.current_list = Watchlist(watchlist_data=watchlist_data, metadata_data=metadata, watchlist_name=self.current_list_name)
        else:
            fileName = self.watchlists_path+fdel+self.current_list_name+".xlsx"
            self.current_list.append_current_watchlist(watchlist_data, metadata)

        if fileName:
            if not fileName.endswith('.xlsx'):
                fileName += '.xlsx'  # Ensure the file has a .xlsx extension
            # Assuming self is an instance of a class that has access to the watchlist and metadata DataFrames
            try:
                self.current_list.save_watchlist(path=self.watchlists_path)
                # Save the watchlist and metadata to the selected file
            except Exception as e:
                print(f"Failed to save watchlist: {e}")
            else:
                print(f"Watchlist saved successfully to: {fileName}")
                self.previous_selections_meta.append(watchlist_data)
                self.previous_selections_wl.append(metadata)
                self.return_dict = {}        # Reset the return dictionary, rest selected series
                self.return_df = pd.DataFrame() # Reset the return dataframe
        else:
            print("Save operation cancelled.")

##### STANDALONE FUNCTIONS ####################

def update_GNmetrics():
    path = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"
    old_df = pd.read_csv(path, index_col=0)
    print("Number of metrics in existing table: ", len(old_df))
    gnmets = Glassnode.GlassNode_API.UpdateGNMetrics(keys['glassnode'])
    print("Number of metrics in new table: ", len(gnmets))
    path = wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv"
    gnmets.to_csv(path)

def org_metadata(series_meta: dict) -> pd.DataFrame:
    #Below is all of the index variables found amougsnt the metadata from all the different sources....
    meta_df = pd.DataFrame(index = ['name', 'id', 'realtime_start', 'realtime_end', 'title','observation_start', 'observation_end', 'frequency', 'frequency_short',
        'units', 'units_short', 'seasonal_adjustment','seasonal_adjustment_short', 'last_updated', 'popularity',
        'group_popularity', 'notes', 'source', 'exchange', 'shortname','quoteType', 'index', 'score', 'typeDisp', 'exchDisp', 'sector',
        'sectorDisp', 'industry', 'industryDisp', 'dispSecIndFlag','isYahooFinance', 'fullExchange', 'screener', 'type', 'getTA', 'symbol',
        'path', 'tier', 'assets', 'currencies', 'resolutions', 'formats','paramsDomain', 'line_number', 'Series Type', 'Series Start',
        'Series End', 'No. Obs.', 'Unit', 'Data Type', 'Freq.','Collection Month', 'Catalogue', 'Table', 'RowNumber', 'LineNumber','ParentLineNumber', 
        'Tier', 'Path', 'Datasetname', 'TableName','ReleaseDate', 'NextReleaseDate', 'SearchScore'])

    for key in series_meta.keys():
        ser = series_meta[key]
        meta_df = pd.concat([meta_df,ser],axis=1)
    meta_df.index.rename("property", inplace=True)
    return meta_df

def run_app():
    sources = {'fred': PriceImporter.FREDSearch, 
            'yfinance': js_funcs.search_yf_tickers, 
            'tv': js_funcs.js_search_tv, 
            'coingecko': cG_allshitsPath, 
            'quandl': None, 
            'glassnode': metricsListPath, 
            'abs': abs_index_path,
            'bea': bea_data_mate.BEA_API_backend.bea_search_metadata}
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    ui.add_sources(sources)
    MainWindow.show()

    #app.aboutToQuit.connect(ui.cleanup)
    app.exec()

    metadata = org_metadata(ui.return_dict)
    if ui.current_list is not None:
        return ui.current_list
    else:
        return ui.return_df, metadata

if __name__ == "__main__":

    # watched = run_app()
    # if isinstance(watched, Watchlist):
    #     print("Watchlist: ", watched.name, "\nWatchlist:\n", watched['watchlist'], "\nMetadata:\n", watched['metadata'])
    # else:
    #     print("Series: chosen: \n", watched[0], "\nMetadata: \n", watched[1])
    wl = Watchlist()
    wl.load_watchlist()
 
from importlib import import_module

#from .options import chart_rip
from . import charting_plotly 
from . import Charting 
from . import Fitting 
from . import js_funcs 
from . import PriceImporter 
from . import Pull_Data 
from . import Utilities 
from . import stats 
from .BEA_Data import bea_data_mate
from .Glassnode import GN_Control

_LAZY_SUBMODULES = {"search_symbol_gui", "watchlist", "AgentSandbox"}


def __getattr__(name):
	if name in _LAZY_SUBMODULES:
		module = import_module(f"{__name__}.{name}")
		globals()[name] = module
		return module
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
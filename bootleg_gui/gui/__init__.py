"""
bootleg_gui.gui — GUI widgets and windows for the watchlist builder.

Lazy-imports pyqt6 to avoid import overhead when the GUI is not used.
"""

from bootleg_gui.gui.watchlist_builder import WatchlistBuilderWindow


def launch():
    """Launch the WatchlistBuilderWindow (convenience function)."""
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = WatchlistBuilderWindow()
    window.show()
    sys.exit(app.exec())

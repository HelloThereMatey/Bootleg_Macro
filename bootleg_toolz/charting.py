"""
Plotly-based charting for bm time series.

Provides simple, high-quality plotting with automatic layout,
dual-axis support, and high-resolution PNG export (scale=3 by default).

Default export: PNG at scale=3 (~3x native resolution, ~300 DPI effective).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# Template and style constants
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATE = "plotly_white"
DEFAULT_HEIGHT = 600
DEFAULT_WIDTH = 1000
DEFAULT_SCALE = 3  # PNG export scale factor (3 = ~300 DPI effective)


# ---------------------------------------------------------------------------
# Core plotting functions
# ---------------------------------------------------------------------------

def plot_series(
    series: pd.Series,
    title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    color: str = "#1f77b4",
    height: int = DEFAULT_HEIGHT,
    width: int = DEFAULT_WIDTH,
    template: str = DEFAULT_TEMPLATE,
    show_grid: bool = True,
    xref: str = "x",
    yref: str = "y",
) -> go.Figure:
    """Plot a single series as a line chart.

    Args:
        series: pandas Series with DatetimeIndex
        title: Chart title (default: series.name)
        yaxis_title: Y-axis label
        color: Line color (hex or named)
        height: Plot height in pixels
        width: Plot width in pixels
        template: Plotly template name
        show_grid: Show grid lines
        xref: X anchor for annotations
        yref: Y anchor for annotations

    Returns:
        plotly.graph_objects.Figure
    """
    # Prepare data — make timezone naive
    s = series.copy()
    if hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_convert('UTC').tz_localize(None)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=s.index,
        y=s.values,
        mode='lines',
        name=title or s.name or 'Value',
        line=dict(color=color, width=1.5),
        hovertemplate='%{x|%Y-%m-%d}<br>%{y:.4f}<extra></extra>',
    ))

    layout_updates = dict(
        title=dict(text=title or s.name or '', x=0.5, xanchor='center'),
        xaxis=dict(
            showgrid=show_grid,
            gridcolor='rgba(0,0,0,0.1)',
            type='date',
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=show_grid,
            gridcolor='rgba(0,0,0,0.1)',
            title=dict(text=yaxis_title or ''),
        ),
        template=template,
        height=height,
        width=width,
        margin=dict(t=60, b=50, l=70, r=40),
        hovermode='x unified',
    )

    fig.update_layout(**layout_updates)
    return fig


def plot_multi(
    series_dict: dict[str, pd.Series],
    title: Optional[str] = None,
    primary_yaxis_title: Optional[str] = None,
    secondary_series: Optional[dict[str, pd.Series]] = None,
    secondary_yaxis_title: Optional[str] = None,
    height: int = 500,
    width: int = 1000,
    template: str = DEFAULT_TEMPLATE,
    colors: Optional[list[str]] = None,
    show_grid: bool = True,
    show_legend: bool = True,
) -> go.Figure:
    """Plot multiple series with optional secondary y-axis.

    Args:
        series_dict: dict of {label: series} for primary (left) axis
        title: Chart title
        primary_yaxis_title: Left y-axis label
        secondary_series: dict of {label: series} for secondary (right) axis
        secondary_yaxis_title: Right y-axis label
        height: Plot height in pixels (default 500 for 10:5 aspect)
        width: Plot width in pixels (default 1000 for 10:5 aspect)
        template: Plotly template name
        colors: Optional list of colors for primary series
        show_grid: Show grid lines
        show_legend: Show legend

    Returns:
        plotly.graph_objects.Figure with dual y-axes
    """
    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    if colors is None:
        colors = default_colors

    # Prepare series — make timezone naive
    def _prep(s):
        s = s.copy()
        if hasattr(s.index, 'tz') and s.index.tz is not None:
            s.index = s.index.tz_convert('UTC').tz_localize(None)
        return s

    primary_prepped = {label: _prep(s) for label, s in series_dict.items()}
    secondary_prepped = (
        {label: _prep(s) for label, s in secondary_series.items()}
        if secondary_series else {}
    )

    has_secondary = bool(secondary_prepped)
    fig = make_subplots(
        specs=[[{"secondary_y": True}]] if has_secondary else None,
    )

    # Add primary series
    for i, (label, series) in enumerate(primary_prepped.items()):
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode='lines',
                name=label,
                line=dict(color=color, width=1.5),
                hovertemplate=f'{label}<br>%{{x|%Y-%m-%d}}<br>%{{y:.4f}}<extra></extra>',
            ),
            secondary_y=False,
        )

    # Add secondary series
    for i, (label, series) in enumerate(secondary_prepped.items()):
        color = colors[(len(primary_prepped) + i) % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode='lines',
                name=label,
                line=dict(color=color, width=1.5, dash='dot'),
                hovertemplate=f'{label}<br>%{{x|%Y-%m-%d}}<br>%{{y:.4f}}<extra></extra>',
            ),
            secondary_y=True,
        )

    # Axis titles
    p_y_title = primary_yaxis_title or ''
    s_y_title = secondary_yaxis_title or ''

    fig.update_layout(
        title=dict(text=title or '', x=0.5, xanchor='center'),
        height=height,
        width=width,
        template=template,
        showlegend=show_legend,
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.2,
            yanchor='top',
            traceorder='normal',
            entrywidth=0.32,
            entrywidthmode='fraction',
        ),
        margin=dict(t=60, b=130, l=70, r=60),
        hovermode='x unified',
        xaxis=dict(
            showgrid=show_grid,
            gridcolor='rgba(0,0,0,0.1)',
            type='date',
        ),
    )

    fig.update_yaxes(
        title_text=p_y_title,
        showgrid=show_grid,
        gridcolor='rgba(0,0,0,0.1)',
        secondary_y=False,
    )

    if has_secondary:
        fig.update_yaxes(
            title_text=s_y_title,
            showgrid=show_grid,
            gridcolor='rgba(0,0,0,0.1)',
            secondary_y=True,
        )

    return fig


def plot_watchlist(
    left: list[tuple],
    right: Optional[list[tuple]] = None,
    plot_title: Optional[str] = None,
    primary_yaxis_title: Optional[str] = None,
    secondary_yaxis_title: Optional[str] = None,
    height: int = DEFAULT_HEIGHT,
    width: int = DEFAULT_WIDTH,
    template: str = DEFAULT_TEMPLATE,
    show_grid: bool = True,
    show_legend: bool = True,
) -> go.Figure:
    """Plot watchlist series with dual y-axis support.

    Args:
        left: List of (metadata, series) tuples for left axis
        right: List of (metadata, series) tuples for right axis
        plot_title: Chart title
        primary_yaxis_title: Left y-axis label
        secondary_yaxis_title: Right y-axis label
        height: Plot height in pixels
        width: Plot width in pixels
        template: Plotly template name
        show_grid: Show grid lines
        show_legend: Show legend

    Returns:
        plotly.graph_objects.Figure
    """
    # Extract primary series dict
    primary = {}
    for meta, series in (left or []):
        label = _series_label(meta, series)
        primary[label] = series

    secondary = {}
    for meta, series in (right or []):
        label = _series_label(meta, series)
        secondary[label] = series

    if not primary and not secondary:
        fig = go.Figure()
        fig.update_layout(title='No data to plot')
        return fig

    if plot_title is None:
        if primary:
            plot_title = list(primary.keys())[0]
        else:
            plot_title = 'Watchlist'

    return plot_multi(
        series_dict=primary,
        title=plot_title,
        primary_yaxis_title=primary_yaxis_title,
        secondary_series=secondary if secondary else None,
        secondary_yaxis_title=secondary_yaxis_title,
        height=height,
        width=width,
        template=template,
        show_grid=show_grid,
        show_legend=show_legend,
    )


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def save_png(
    fig: go.Figure,
    path: Union[str, Path],
    scale: int = DEFAULT_SCALE,
    **kwargs,
) -> Path:
    """Save a plotly figure as high-resolution PNG.

    Args:
        fig: plotly.graph_objects.Figure
        path: Output file path (.png)
        scale: Resolution scale factor (default 3 = ~300 DPI effective).
               scale=2 gives ~200 DPI, scale=1 gives ~100 DPI.
        **kwargs: Passed to fig.write_image (width, height, etc.)

    Returns:
        Path to saved file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(path, scale=scale, **kwargs)
    return path


def save_html(
    fig: go.Figure,
    path: Union[str, Path],
    include_plotlyjs: str = "cdn",
    full_html: bool = True,
    auto_open: bool = False,
) -> Path:
    """Save a plotly figure as interactive HTML.

    Args:
        fig: plotly.graph_objects.Figure
        path: Output file path (.html)
        include_plotlyjs: Where to load plotly.js from ('cdn', 'inline', 'directory')
        full_html: Include full HTML document wrapper
        auto_open: Open file automatically after saving

    Returns:
        Path to saved file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        path,
        include_plotlyjs=include_plotlyjs,
        full_html=full_html,
        auto_open=auto_open,
    )
    return path


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _series_label(meta, series) -> str:
    """Derive a display label from metadata and series."""
    if series is not None and getattr(series, 'name', None):
        return str(series.name)
    if meta is None:
        return 'Series'
    for key in ('title', 'Title', 'id', 'series_id', 'name'):
        try:
            if isinstance(meta, pd.Series):
                val = meta.get(key, None)
            elif isinstance(meta, dict):
                val = meta.get(key, None)
            else:
                val = getattr(meta, key, None)
            if val:
                return str(val)
        except Exception:
            pass
    return 'Series'


def show(fig: go.Figure) -> None:
    """Display a plotly figure (jupyter-compatible)."""
    fig.show()
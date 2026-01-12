"""
Simple NLQ charting module.
Provides dual-axis plotting for Net Liquidity data with comparison assets.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional, Tuple, Union, List
import matplotlib.dates as mdates
import plotly.graph_objects as go


def count_zeros_after_decimal(median_value: float) -> int:
    """Count zeros after decimal point to determine appropriate precision."""
    if median_value < 1 and median_value > 0:
        str_val = str(median_value).split('.')[1]
        return len(str_val) - len(str_val.lstrip('0')) + 1
    else:
        return 1


def equal_spaced_ticks(
    num_ticks: int,
    data: Union[pd.Series, pd.DataFrame, List[float], np.ndarray] = None,
    scale: str = 'linear',
    ymin: float = None,
    ymax: float = None,
    lab_offset: float = None,
    lab_prefix: str = None,
    lab_suffix: str = None,
    return_format: str = 'matplotlib',
    round_to_int: bool = False
) -> Union[Tuple[List[float], List[str]], dict]:
    """
    Generate equally spaced tick positions and labels for matplotlib or plotly charts.
    Works with both linear and log scales to create visually equal spacing.
    
    Parameters:
    -----------
    num_ticks : int
        Number of ticks to generate on the axis.
    data : Union[pd.Series, pd.DataFrame, List[float], np.ndarray], optional
        Data to automatically determine ymin and ymax if not provided.
    scale : str, default 'linear'
        Scale type: 'linear' or 'log'.
    ymin : float, optional
        Minimum value for tick range. Auto-determined from data if None.
    ymax : float, optional
        Maximum value for tick range. Auto-determined from data if None.
    lab_offset : float, optional
        Offset to add to tick labels (not tick positions).
    lab_prefix : str, optional
        Prefix to add to tick labels (e.g., '$').
    lab_suffix : str, optional
        Suffix to add to tick labels (e.g., 'B').
    return_format : str, default 'matplotlib'
        Format to return: 'matplotlib' returns (ticks, labels),
        'plotly' returns dict with tickvals and ticktext.
    round_to_int : bool, default False
        If True, round tick labels to integers instead of using decimal precision.
    
    Returns:
    --------
    Union[Tuple[List[float], List[str]], dict]
        For 'matplotlib': (tick_positions, tick_labels)
        For 'plotly': {'tickmode': 'array', 'tickvals': [...], 'ticktext': [...]}
    
    Examples:
    ---------
    # For matplotlib
    ticks, labels = equal_spaced_ticks(10, data=my_series, scale='log')
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    
    # For plotly
    tick_config = equal_spaced_ticks(10, data=my_series, scale='log', return_format='plotly')
    fig.update_yaxes(**tick_config)
    """
    
    # Determine ymin and ymax from data if not provided
    if data is not None:
        if ymin is None:
            if isinstance(data, pd.DataFrame):
                ymin = data.min().min()
            elif isinstance(data, pd.Series):
                ymin = data.min()
            elif isinstance(data, (list, np.ndarray)):
                ymin = np.min(data)
        
        if ymax is None:
            if isinstance(data, pd.DataFrame):
                ymax = data.max().max()
            elif isinstance(data, pd.Series):
                ymax = data.max()
            elif isinstance(data, (list, np.ndarray)):
                ymax = np.max(data)
    
    if ymin is None or ymax is None:
        raise ValueError("Must provide either data or both ymin and ymax")
    
    # Handle negative values for log scale
    if scale == 'log' and ymin <= 0:
        print(f"Warning: ymin={ymin} is <= 0 for log scale. Adjusting to 0.01")
        ymin = max(0.01, ymax / 10000)
    
    # Determine decimal precision for labels
    median_val = (ymax - ymin) / 2
    decimals = count_zeros_after_decimal(median_val) if median_val < 1 else 2
    
    # Generate tick positions
    if scale == 'log':
        # For log scale, use logspace to get equal visual spacing
        tick_positions = np.logspace(
            start=np.log10(ymin),
            stop=np.log10(ymax),
            num=num_ticks,
            base=10
        )
    elif scale == 'linear':
        # For linear scale, use linspace
        tick_positions = np.linspace(
            start=ymin,
            stop=ymax,
            num=num_ticks
        )
    else:
        raise ValueError("scale must be 'linear' or 'log'")
    
    # Create labels (potentially with offset)
    tick_labels = tick_positions.copy()
    if lab_offset is not None:
        tick_labels = tick_labels + lab_offset
    
    # Round labels for display
    if round_to_int:
        tick_labels = np.round(tick_labels, decimals=0).astype(int)
        tick_labels_str = [str(int(label)) for label in tick_labels]
    else:
        tick_labels = np.round(tick_labels, decimals=decimals)
        tick_labels_str = [str(label) for label in tick_labels]
    
    # Add prefix/suffix if provided
    if lab_prefix is not None:
        tick_labels_str = [lab_prefix + label for label in tick_labels_str]
    if lab_suffix is not None:
        tick_labels_str = [label + lab_suffix for label in tick_labels_str]
    
    # Convert tick positions to list
    tick_positions_list = tick_positions.tolist()
    
    # Return in requested format
    if return_format == 'matplotlib':
        return tick_positions_list, tick_labels_str
    elif return_format == 'plotly':
        return {
            'tickmode': 'array',
            'tickvals': tick_positions_list,
            'ticktext': tick_labels_str
        }
    else:
        raise ValueError("return_format must be 'matplotlib' or 'plotly'")


def plot_nlq_dual_axis(
    nlq_data: pd.Series,
    asset_data: Optional[Dict[str, pd.Series]] = None,
    ma_period: int = 20,
    left_scale: str = 'log',
    right_scale: str = 'log',
    nlq_color: str = '#1f77b4',
    title: str = 'Net Liquidity vs Assets',
    figsize: Tuple[int, int] = (14, 6),
    show_ma: bool = True,
    ma_color: str = '#ff7f0e',
    show_legend: bool = True,
    custom_ticks_left: int = None,
    custom_ticks_right: int = None,
    left_tick_prefix: str = None,
    right_tick_prefix: str = None,
    left_ticks_int: bool = False,
    right_ticks_int: bool = False,
) -> Tuple[plt.Figure, plt.Axes, plt.Axes]:
    """
    Create a dual-axis chart with NLQ on left axis and comparison assets on right axis.
    
    Parameters:
    -----------
    nlq_data : pd.Series
        Net liquidity data series with DatetimeIndex.
    asset_data : Dict[str, pd.Series], optional
        Dictionary of asset data series to plot on right axis. 
        Keys are used as labels, values are pd.Series with DatetimeIndex.
        Maximum 5 series supported.
    ma_period : int, default 20
        Moving average period for NLQ trace.
    left_scale : str, default 'log'
        Scale for left y-axis ('linear' or 'log').
    right_scale : str, default 'log'
        Scale for right y-axis ('linear' or 'log').
    nlq_color : str, default '#1f77b4'
        Color for NLQ trace.
    title : str, default 'Net Liquidity vs Assets'
        Chart title.
    figsize : Tuple[int, int], default (14, 6)
        Figure size in inches.
    show_ma : bool, default True
        Whether to show moving average on NLQ trace.
    ma_color : str, default '#ff7f0e'
        Color for moving average line.
    show_legend : bool, default True
        Whether to display legend.
    custom_ticks_left : int, optional
        Number of custom equally-spaced ticks for left axis. Uses default if None.
    custom_ticks_right : int, optional
        Number of custom equally-spaced ticks for right axis. Uses default if None.
    left_tick_prefix : str, optional
        Prefix for left axis tick labels (e.g., '$').
    right_tick_prefix : str, optional
        Prefix for right axis tick labels (e.g., '$').
    left_ticks_int : bool, default False
        If True, round left axis tick labels to integers.
    right_ticks_int : bool, default False
        If True, round right axis tick labels to integers.
        
    Returns:
    --------
    Tuple[plt.Figure, plt.Axes, plt.Axes]
        Figure and both axes objects for further customization.
    """
    
    # Color palette for right axis assets
    asset_colors = ['#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    # Validate asset_data
    if asset_data is not None and len(asset_data) > 5:
        print("Warning: Maximum 5 asset series supported. Using first 5.")
        asset_data = dict(list(asset_data.items())[:5])
    
    # Create figure and primary axis
    fig, ax_left = plt.subplots(figsize=figsize)
    
    # Plot NLQ on left axis
    ax_left.plot(
        nlq_data.index, 
        nlq_data.values, 
        color=nlq_color, 
        linewidth=1.5, 
        label='Net Liquidity',
        alpha=0.8
    )
    
    # Plot moving average if requested
    if show_ma and ma_period > 0:
        ma = nlq_data.rolling(window=ma_period).mean()
        ax_left.plot(
            ma.index, 
            ma.values, 
            color=ma_color, 
            linewidth=2, 
            label=f'NLQ {ma_period}MA',
            linestyle='--'
        )
    
    # Configure left axis
    ax_left.set_yscale(left_scale)
    ax_left.set_ylabel('Net Liquidity (Bil $)', color=nlq_color, fontsize=12)
    ax_left.tick_params(axis='y', labelcolor=nlq_color)
    ax_left.grid(True, alpha=0.3)
    
    # Apply custom ticks to left axis if requested
    if custom_ticks_left is not None:
        left_ticks, left_labels = equal_spaced_ticks(
            num_ticks=custom_ticks_left,
            data=nlq_data,
            scale=left_scale,
            lab_prefix=left_tick_prefix,
            return_format='matplotlib',
            round_to_int=left_ticks_int
        )
        # Disable minor ticks and set only major ticks
        ax_left.minorticks_off()
        ax_left.set_yticks(left_ticks)
        ax_left.set_yticklabels(left_labels)
        # Remove any default ticks that might remain
        ax_left.tick_params(axis='y', which='minor', length=0)
    
    # Create right axis for assets
    ax_right = ax_left.twinx()
    
    # Plot assets on right axis
    if asset_data is not None:
        for i, (name, series) in enumerate(asset_data.items()):
            color = asset_colors[i % len(asset_colors)]
            ax_right.plot(
                series.index, 
                series.values, 
                color=color, 
                linewidth=1.5, 
                label=name,
                alpha=0.9
            )
    
    # Configure right axis
    ax_right.set_yscale(right_scale)
    ax_right.set_ylabel('Asset Price', fontsize=12)
    
    # Apply custom ticks to right axis if requested
    if custom_ticks_right is not None and asset_data is not None:
        # Combine all asset data to get range
        all_asset_vals = pd.concat(list(asset_data.values()))
        right_ticks, right_labels = equal_spaced_ticks(
            num_ticks=custom_ticks_right,
            data=all_asset_vals,
            scale=right_scale,
            lab_prefix=right_tick_prefix,
            return_format='matplotlib',
            round_to_int=right_ticks_int
        )
        # Disable minor ticks and set only major ticks
        ax_right.minorticks_off()
        ax_right.set_yticks(right_ticks)
        ax_right.set_yticklabels(right_labels)
        # Remove any default ticks that might remain
        ax_right.tick_params(axis='y', which='minor', length=0)
    
    # Configure x-axis
    ax_left.set_xlabel('Date', fontsize=12)
    ax_left.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax_left.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    # Title
    ax_left.set_title(title, fontsize=14, fontweight='bold')
    
    # Combined legend
    if show_legend:
        lines_left, labels_left = ax_left.get_legend_handles_labels()
        lines_right, labels_right = ax_right.get_legend_handles_labels()
        ax_left.legend(
            lines_left + lines_right, 
            labels_left + labels_right, 
            loc='upper left',
            framealpha=0.9
        )
    
    plt.tight_layout()
    
    return fig, ax_left, ax_right


# Example usage
if __name__ == "__main__":
    # Generate sample data for testing
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    
    # Sample NLQ data
    nlq = pd.Series(
        np.cumsum(np.random.randn(500)) + 5000,
        index=dates,
        name='NLQ'
    )
    
    # Sample asset data
    assets = {
        'BTC': pd.Series(np.exp(np.cumsum(np.random.randn(500) * 0.02) + 10), index=dates),
        'SPX': pd.Series(np.exp(np.cumsum(np.random.randn(500) * 0.01) + 8), index=dates),
    }
    
    # Example 1: Basic chart without custom ticks
    fig1, ax_l1, ax_r1 = plot_nlq_dual_axis(
        nlq_data=nlq,
        asset_data=assets,
        ma_period=20,
        left_scale='linear',
        right_scale='log',
        title='Net Liquidity vs BTC & SPX (Default Ticks)'
    )
    
    # Example 2: Chart with custom equally-spaced ticks
    fig2, ax_l2, ax_r2 = plot_nlq_dual_axis(
        nlq_data=nlq,
        asset_data=assets,
        ma_period=20,
        left_scale='log',
        right_scale='log',
        title='Net Liquidity vs BTC & SPX (Custom Equal-Spaced Ticks)',
        custom_ticks_left=8,
        custom_ticks_right=10,
        left_tick_prefix='$',
        right_tick_prefix='$'
    )
    
    # Example 3: Using equal_spaced_ticks function for plotly
    tick_config = equal_spaced_ticks(
        num_ticks=10,
        data=nlq,
        scale='log',
        lab_prefix='$',
        lab_suffix='B',
        return_format='plotly'
    )
    print("Plotly tick config:", tick_config)
    
    plt.show()


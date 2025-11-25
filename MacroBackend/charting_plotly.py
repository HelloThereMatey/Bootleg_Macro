import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
if __name__ == '__main__':
    import Utilities
else:
    from . import Utilities

def fit_trendlines(fig, fit_specs: dict, line_style: dict = None, debug: bool = False):
    """
    Fit polynomial trendlines to traces in a Plotly figure.
    
    Parameters:
    - fig: Plotly Figure object
    - fit_specs: dict {series_name: [order, start, end], ...}
      - order: int, polynomial degree
      - start/end: datetime-like, date string, or int index (None = use all data)
    - line_style: dict of line styling (dash, width, color, etc.)
    
    Returns: modified fig with fitted trendline traces added
    """
    if line_style is None:
        line_style = {'dash': 'dash', 'width': 2}
    
    # Get figure x-limits for extending trendlines
    all_x = []
    for trace in fig.data:
        if trace.x is not None:
            all_x.extend(list(trace.x))
    
    if not all_x:
        return fig
    
    # Determine if datetime or numeric
    try:
        x_range = pd.to_datetime(all_x)
        is_datetime = True
        xlim = [x_range.min(), x_range.max()]
    except:
        x_range = np.array(all_x, dtype=float)
        is_datetime = False
        xlim = [x_range.min(), x_range.max()]
    
    # Process each fit specification
    for series_name, spec in fit_specs.items():
        order = int(spec[0])
        start = spec[1] if len(spec) > 1 else None
        end = spec[2] if len(spec) > 2 else None
        if debug:
            print(f"[trendfit] series={series_name!r} order={order} start={start} end={end}")
        
        # Find matching trace
        trace = None
        for t in fig.data:
            if getattr(t, 'name', None) == series_name:
                trace = t
                break
        
        if trace is None or trace.x is None or trace.y is None:
            if debug:
                print(f"[trendfit] no data for '{series_name}' (trace found={trace is not None})")
            continue
        
        # Convert to arrays
        x = np.array(trace.x)
        y = np.array(trace.y, dtype=float)
        if debug:
            print(f"[trendfit] raw points: x_len={len(x)} y_len={len(y)}")
        
        # Handle datetime conversion for fitting
        if is_datetime:
            x_dt = pd.to_datetime(x)
            x_num = (x_dt - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            x_num = x_num.astype(float)
            if debug:
                print(f"[trendfit] x is datetime, range {x_dt.min()} -> {x_dt.max()}")
        else:
            x_num = x.astype(float)
        
        # Apply start/end slicing
    mask = np.ones(len(x), dtype=bool)
        if start is not None:
            if isinstance(start, int):
                mask[:start] = False
            else:
                if is_datetime:
                    start_dt = pd.to_datetime(start)
                    mask &= (x_dt >= start_dt)
                else:
                    mask &= (x_num >= float(start))
        
        if end is not None:
            if isinstance(end, int):
                mask[end+1:] = False
            else:
                if is_datetime:
                    end_dt = pd.to_datetime(end)
                    mask &= (x_dt <= end_dt)
                else:
                    mask &= (x_num <= float(end))

        x_fit = x_num[mask]
        y_fit = y[mask]
        if debug:
            try:
                # sample first/last few values for quick inspection
                n_sample = 3
                if is_datetime:
                    x_sample = pd.to_datetime(x_dt[mask])
                else:
                    x_sample = x_fit
                print(f"[trendfit] slice points: count={len(x_fit)} sample_x_head={list(x_sample[:n_sample])} sample_x_tail={list(x_sample[-n_sample:])} ")
                print(f"[trendfit] slice y sample_head={list(y_fit[:n_sample])} sample_tail={list(y_fit[-n_sample:])}")
            except Exception as _:
                pass
        
        if len(x_fit) < order + 1:
            if debug:
                print(f"[trendfit] insufficient points after slicing for '{series_name}': need {order+1}, got {len(x_fit)}")
            continue

        # Fit polynomial
        try:
            coeffs = np.polyfit(x_fit, y_fit, order)
            poly = np.poly1d(coeffs)
        except Exception as e:
            if debug:
                print(f"[trendfit] polyfit failed for '{series_name}': {e}")
            continue
        
        # Generate extended x range across full chart limits
        if is_datetime:
            x_extend_dt = pd.date_range(xlim[0], xlim[1], periods=200)
            x_extend_num = (x_extend_dt - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            x_extend_num = x_extend_num.astype(float)
            x_plot = x_extend_dt
        else:
            x_extend_num = np.linspace(xlim[0], xlim[1], 200)
            x_plot = x_extend_num
        
        y_plot = poly(x_extend_num)
        if debug:
            # compute simple R^2 on the fit sample
            try:
                y_pred = poly(x_fit)
                ss_res = np.sum((y_fit - y_pred) ** 2)
                ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
                r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
            except Exception:
                r2 = float('nan')
            try:
                print(f"[trendfit] coeffs={coeffs} r2={r2:.4f} plotted_points={len(x_plot)}")
            except Exception:
                print(f"[trendfit] coeffs={coeffs} r2={r2}")
        
        # Add trendline trace
        import plotly.graph_objects as go
        fig.add_trace(go.Scatter(
            x=x_plot,
            y=y_plot,
            mode='lines',
            name=f"{series_name} (trend {order})",
            line=line_style,
            showlegend=True
        ))
    
    return fig

# Assuming yrange_bot is a tuple or list with two elements: (min_y, max_y)
def yrange_margin(yrange: list, margin_percentage=0.03):
    min_y, max_y = yrange

    y_range = max_y - min_y
    margin = y_range * margin_percentage
    # Adjust the y-range to include the margins
    y0 = min_y - margin
    y1 = max_y + margin
    return y0, y1

def plotly_twoPart_fig(plot_dict: dict, recessions: str = "us"):
    """ Plotly figure with two panels showing line traces in top panel action and bars plus line trace/s in bottom panel.
    Recession periods are highlighted in both panels as grey vertical spans.

    **Parameters:**
    - plot_dict: dict - dictionary containing the data to be plotted. This must have certain keys: 
        - "upper" and "lower" containing the series to be plotted in the top and bottom panels respectively. Series only atm, no df.
        Upper and lower must be a list of pd.Series. Two series at top and two at bottom is all that is supported atm.
        - "labels": this key can contain dicts that specify the labels for the x and y axes, titles for each plot. keys for this key:
            - "x": str - label for the x-axis across both plots
            - "y_upper": str - label for the y-axis on the upper plot.
            - "y_lower": str - label for the y-axis on the lower plot.
        - "titles": str - titles for the plots, containing the following:
            - "main": str - title for the entire plot
            - "upper": str - title for the upper plot
            - "lower": str - title for the lower plot
    *below is an example of the structure of the plot_dict:*
    ```python
    plot_dict = {
        "upper": [series1: pd.Series, series2: pd.Series],
        "lower": [rets, rets.rename("rets_50MA").rolling(50).mean()],  #rets is the returns of series1 (%).
        "titles": {"main": "Some equity indexes....", "upper": "SPX maybe or sumtin like dat...", "lower": "Returns in percentage terms."},
    }
    ```
    - recession_periods: str - string specifying the source of recession periods to be highlighted in the plot. Default is "us" for US recession periods.
    *note:* Currently only US recession periods are supported, I will add support for other countries in the future.

    **Returns:**
    - fig: plotly.graph_objects.Figure - Plotly figure object containing the two-panel plot.
    """

    if "lower" in plot_dict.keys():
        include_lower_plot = True
    include_lower_plot=True

    startdate = min(plot_dict["upper"][0].index.min(), plot_dict["upper"][1].index.min())
    rec_periods = None
    if recessions == "us":
        import PriceImporter
        keys = Utilities.api_keys()
        _, rec_periods = PriceImporter.Recession_Series(keys.keys['fred'], startdate.strftime("%Y-%m-%d"))

    # Create subplots with different row heights
    row_heights = [0.7, 0.3] if include_lower_plot else [1]
    fig = make_subplots(
        rows=2 if include_lower_plot else 1, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.075,  # Adjust the vertical spacing between plots
        subplot_titles=(plot_dict["titles"]["upper"], plot_dict["titles"]["lower"]) if include_lower_plot else [plot_dict["titles"]["upper"]],
    )

    top_data = plot_dict["upper"]
    # Add the price action series to the top panel
    fig.add_trace(
        go.Scatter(x=top_data[0].index, y=top_data[0], mode='lines', name=top_data[0].name, line=dict(color='black', width=2.5)),
        row=1, col=1)
    # Add a second trace to the top panel
    fig.add_trace(
        go.Scatter(x=top_data[1].index, y=top_data[1], mode='lines', name=top_data[1].name, line=dict(color='red')),
        row=1, col=1)

    if include_lower_plot:
        bot_data = plot_dict["lower"]
        # Add the other series as bars to the bottom panel with specified color and opacity
        fig.add_trace(
            go.Bar(x=bot_data[0].index, y=bot_data[0], name=bot_data[0].name, marker=dict(color='blue', line=dict(color='blue')), opacity=1),
            row=2, col=1)
        if len(bot_data) > 1:
            fig.add_trace(
                go.Scatter(x=bot_data[1].index, y=bot_data[1], mode='lines', name=bot_data[1].name, line=dict(color='red', width=1)),
                row=2, col=1)
    
    yrange_top = [min(top_data[0].min(), top_data[0].min()), max(top_data[0].max(), top_data[0].max())]
    yrange_bot = [min(bot_data[0].min(), bot_data[0].min()), max(bot_data[0].max(), bot_data[0].max())] if include_lower_plot else None
    y0, y1 = yrange_margin(yrange_top)
    yb0, yb1 = yrange_margin(yrange_bot) if include_lower_plot else None


    fig.update_layout(
        height=600,  # Set the height of the figure
        width=1000,  # Set the width of the figure
        title_text=plot_dict["titles"]["main"], showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20),  # Reduce whitespace at edges
        grid=dict(rows=2 if include_lower_plot else 1, columns=1),  # Add gridlines
        legend=dict(orientation='h', x=0, y=-0.05, xanchor='left', yanchor='top'),
        font={"family": "Arial, sans-serif", "size": 14, "color": "black"})

    # Set the y-axis of the top plot to log scale and add y-axis labels
    fig.update_yaxes(title=dict(text=plot_dict['titles']['upper'], standoff=1), type="log", row=1, col=1, showgrid=True, gridcolor='black', gridwidth=0.5,
                     showline=True, linewidth=2, linecolor='black', ticks='outside', griddash='dot')
    #tickvals=[10, 20, 50, 100, 200, 500, 1000, 2000, 5000],  # Specify tick values, ticktext=["10", "20", "50", "100", "200", "500", "1000", "2000", "5000"],
    if include_lower_plot:
        fig.update_yaxes(title=dict(text=plot_dict['titles']['lower'], standoff=1), showgrid=True, row=2, col=1, gridcolor='black', gridwidth=0.5,
                         showline=True, linewidth=2, linecolor='black', ticks='outside', zeroline=False, griddash='dot')

    if rec_periods is not None:    
        # Add recession periods as vertical spans to the top panel
        for start_date, end_date in rec_periods:
            # Add a vertical colored span
            fig.add_vrect(
                x0=start_date, x1=end_date,  # start and end points on x-axis
                fillcolor="grey", opacity=0.5,
                layer="below", line_width=0,
            )  
            
        if include_lower_plot:
            # Add recession periods as vertical spans to the bottom panel
            for start_date, end_date in rec_periods:
                fig.add_vrect(
                    x0=start_date, x1=end_date,  # start and end points on x-axis
                    fillcolor="grey", opacity=0.5,
                    layer="below", line_width=0,
                )  

    fig.add_trace( # Add a trace to the top panel to show the recession periods, keep it hidden, show in legend only.
            go.Bar(x=[top_data[0].index[0], top_data[0].index[1]], y=[top_data[0].median(), top_data[0].median()], name="US recession periods (NBER)",
                marker=dict(color='gray', opacity=0), showlegend=True, hoverinfo='skip'), row=1, col=1)
    
    # Update x-axes to show dashed grid lines and add frame
    fig.update_xaxes(showgrid=True, gridcolor='black', gridwidth=0.5, showline=True, linewidth=2, linecolor='black', ticks='outside', row=1, col=1, griddash='dot')
    if include_lower_plot:
        fig.update_xaxes(showgrid=True, gridcolor='black', gridwidth=0.5, showline=True, linewidth=2, linecolor='black', ticks='outside', row=2, col=1, griddash='dot')

    return fig

def add_vlines_and_pct_change(fig, watchlist, date1, date2, series_id, color='red', date_format=None):
    """
    Add two vertical lines at date1 and date2 to fig and compute % change for series_id.
    Uses fig.add_vline to draw vertical lines.
    """
    d1 = pd.to_datetime(date1)
    d2 = pd.to_datetime(date2)

    def _series_from_watchlist_or_fig(sid, fig):
        try:
            s = watchlist["watchlist_datasets"][sid].copy()
            s.index = pd.to_datetime(s.index)
            return s.dropna()
        except Exception:
            for tr in fig.data:
                name = getattr(tr, "name", "")
                if name == sid or sid in str(name):
                    x = pd.to_datetime(np.array(tr.x))
                    y = np.array(tr.y, dtype=float)
                    return pd.Series(y, index=x).dropna()
        raise KeyError(f"Series '{sid}' not found in watchlist or figure traces.")

    s = _series_from_watchlist_or_fig(series_id, fig)

    def _value_at_or_nearest(series, dt):
        dt = pd.to_datetime(dt)
        if dt in series.index:
            return float(series.loc[dt])
        before = series.loc[:dt].dropna()
        if not before.empty:
            return float(before.iloc[-1])
        after = series.loc[dt:].dropna()
        if not after.empty:
            return float(after.iloc[0])
        raise ValueError(f"No valid data in series around {dt}")

    v1 = _value_at_or_nearest(s, d1)
    v2 = _value_at_or_nearest(s, d2)
    pct = (v2 / v1 - 1) * 100 if v1 != 0 else float("inf")

    # add vertical lines using add_vline; ensure they are drawn above traces
    fig.add_vline(x=d1, line=dict(color=color, dash="dash", width=1), layer='above')
    fig.add_vline(x=d2, line=dict(color=color, dash="dash", width=1), layer='above')

    fmt = (lambda dt: pd.to_datetime(dt).strftime(date_format)) if date_format else (lambda dt: str(pd.to_datetime(dt).date()))
    fig.add_annotation(x=d1, xref="x", y=0.03, yref="paper",
                       text=f"{fmt(d1)}", showarrow=False, bgcolor="white", font=dict(color=color), yanchor="top")
    fig.add_annotation(x=d2, xref="x", y=0.03, yref="paper",
                       text=f"{fmt(d2)}", showarrow=False, bgcolor="white", font=dict(color=color), yanchor="top")

    summary_text = f"{series_id} change: {pct:+.2f}% ({v1:.2f} → {v2:.2f})"
    fig.add_annotation(x=0.92, xref="paper", y=1.03, yref="paper",
                       text=summary_text, showarrow=False, bgcolor="white",
                       xanchor="right", font=dict(color=color))

    return {"value_at_date1": v1, "value_at_date2": v2, "pct_change": pct}

def plotly_multiline(df: pd.DataFrame, 
                     x_col: str = None,
                     title: str = "",
                     yaxis_title: str = "",
                     log_y: bool = False,
                     height: int = 800,
                     width: int = 1200):
    """
    Create a multi-line plot using plotly express
    
    Parameters:
        df (pd.DataFrame): DataFrame containing the data
        x_col (str): Name of column to use for x-axis (default: index)
        title (str): Plot title
        yaxis_title (str): Y-axis label
        log_y (bool): Use log scale for y-axis
        height (int): Plot height in pixels
        width (int): Plot width in pixels
    
    Returns:
        px.Figure: Plotly figure object
    """
    
    # If no x column specified, use index
    if x_col is None:
        df = df.reset_index()
        x_col = df.columns[0]
    
    # Create figure
    fig = px.line(df, 
                  x=x_col,
                  y=df.columns,
                  title=title,
                  height=height,
                  width=width,
                  )
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend_title_text='Series',
        yaxis_title=yaxis_title,
        yaxis_type='log' if log_y else 'linear',
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Update line styling
    fig.update_traces(line={'width': 1})
    
    return fig

def dual_axis_plot(left_traces: dict, right_traces: dict, 
                   title: str = "", width: int = 1600, height: int = 500,
                   left_yaxis_title: str = "", right_yaxis_title: str = "") -> go.Figure:
    """
    Create plotly figure with dual y-axes
    
    Parameters:
        left_traces (dict): Dictionary of traces for left y-axis
            Can be either:
            - {'name': pd.Series} pairs
            - {'name': {'x': x_values, 'y': y_values, 'name': 'trace_name', ...}} pairs
        right_traces (dict): Dictionary of traces for right y-axis (same format as left_traces)
        title (str): Plot title
        width (int): Plot width in pixels
        height (int): Plot height in pixels
        left_yaxis_title (str): Title for left y-axis
        right_yaxis_title (str): Title for right y-axis
        
    Returns:
        go.Figure: Plotly figure with dual y-axes
    """
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Helper function to process traces
    def process_trace(trace_name, trace_data, secondary_y=False):
        if isinstance(trace_data, pd.Series):
            # If trace_data is a pandas Series, convert to proper format
            fig.add_trace(
                go.Scatter(
                    x=trace_data.index,
                    y=trace_data.values,
                    name=trace_name
                ),
                secondary_y=secondary_y
            )
        else:
            # If trace_data is already a dict with x, y, etc.
            # Ensure 'name' is set if not already in the dict
            if 'name' not in trace_data:
                trace_data['name'] = trace_name
            fig.add_trace(go.Scatter(**trace_data), secondary_y=secondary_y)
    
    # Add left axis traces
    for name, trace in left_traces.items():
        process_trace(name, trace, secondary_y=False)
        
    # Add right axis traces  
    for name, trace in right_traces.items():
        process_trace(name, trace, secondary_y=True)

    fig.update_layout(
        title=title,
        template="plotly_white",
        width=width,
        height=height,
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.5),
        margin=dict(l=25, r=10, t=40, b=20),  # Reduce whitespace at edges
        font={"family": "Arial, sans-serif", "size": 14, "color": "black"}  # Set font to Arial
    )
    
    # Update y-axes titles
    fig.update_yaxes(title_text=left_yaxis_title, secondary_y=False)
    fig.update_yaxes(title_text=right_yaxis_title, secondary_y=True, showgrid=False)
    
    return fig

def px_bar(data: pd.DataFrame, title: str = "Bar chart", barmode: str = 'group',
           columns: list = None, yax_label: str = "value", right_axis: list = None,
           right_yax_label: str = "value (right)") -> go.Figure:
    """Create bar chart with dual axes using blank series for grouping"""
    
    if isinstance(data, pd.Series):
        data = data.copy().to_frame()
        
    # Use all columns if none specified
    if columns is None and right_axis is None:
        columns = data.columns.tolist()
    elif columns is not None and right_axis is None:
        pass
    elif columns is None and right_axis is not None:
        columns = [col for col in data.columns.tolist() if col not in right_axis]
    else:
        columns = [col for col in columns if col not in right_axis]
        right_axis = [col for col in columns if col not in columns]

    #print("Data columns: ", data.columns, "\n", "Left axis: ", columns, "\n", "Right axis: ", right_axis)
    if right_axis is not None:
        numTraces = len(columns) + len(right_axis)
        if len(columns) > 0 and len(right_axis) > 0:
            for i in range(numTraces -1):
                columns.insert(i+1, "_")
                right_axis.insert(i, "_")

    print("Data columns: ", data.columns, "\n", "Left axis: ", columns, "\n", "Right axis: ", right_axis)
    
    if right_axis is not None and len(right_axis) > 0:
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = make_subplots()
    
    # Add left axis bars
    for col in columns:
        if col == '_':
            blank = pd.Series(np.nan, index = data.index, name = "_blank")
            fig.add_trace(go.Bar(x=data.index, y=blank, name=""), secondary_y=False)
        else:
            fig.add_trace(go.Bar(x=data.index, y=data[col], name=col), secondary_y=False)
    if right_axis is not None:
        # Add right axis bars
        for col in right_axis:
            if col == '_':
                fig.add_trace(go.Bar(x=data.index, y=blank, name=""), secondary_y=True)
            else:
                fig.add_trace(go.Bar(x=data.index, y=data[col], name=col), secondary_y=True)

    # Update layout
    fig.update_layout(
        barmode=barmode,
        title=title,
        margin=dict(l=20, r=20, t=45, b=10),
        font={"family": "Arial, sans-serif", "size": 14, "color": "black"},
        legend=dict(
            orientation="h",
            yanchor="bottom", 
            y=-0.3,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            font=dict(size=14)
        ),
        showlegend=True
    )
    
    # Update axes
    fig.update_yaxes(title_text=yax_label, secondary_y=False, showgrid=True)
    fig.update_xaxes(title_text="Date", showgrid=True)
    fig.update_yaxes(title_text=right_yax_label, secondary_y=True, showgrid=False)

    return fig

def bar_subplots(data: pd.DataFrame, columns: list = None, 
                 title: str = "", height: int = None) -> go.Figure:
    
    """Create bar chart plots, one subplot per series. Using the columns from the supplied dataframe.
    **Parameters: **
    columns: list[str] - the names of the columns that you want to plot in subplots."""

    if isinstance(data, pd.Series):
        data = data.copy().to_frame()

    if columns is None:
        columns = data.columns.tolist()
        
    # Calculate default height based on number of subplots
    if height is None:
        height = 200 * len(columns)  # 200px per subplot
        
    # Create subplots with minimal spacing
    fig = make_subplots(
        rows=len(columns), 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,  # Minimal gap between subplots
        subplot_titles=columns
    )

    # Add traces
    for i, col in enumerate(columns, 1):
        fig.add_trace(
            go.Bar(x=data.index, y=data[col], name=col),
            row=i, 
            col=1
        )

    # Update layout
    fig.update_layout(
        height=height,
        title=dict(text=title, x=0.5, y=0.98),
        margin=dict(l=50, r=20, t=30, b=30),  # Minimal margins
        showlegend = False,
        font=dict(family="Arial, sans-serif", size=12)
    )
    
   # Update x-axis visibility with more ticks
    fig.update_xaxes(
        showticklabels=False, 
        showgrid=True, 
        dtick='M24',
    )
    # Show x labels on bottom plot only with more ticks
    fig.update_xaxes(
        showticklabels=True, 
        row=len(columns),
        dtick='M24',  # Set tick interval to 2 year
    )

    fig.update_yaxes(
        nticks=10,  # Increase number of y-axis ticks
        # minor=dict(ticks="inside", ticklen=3, showgrid=True),  # Add minor ticks
        #tickmode="linear"  # Force linear tick spacing
    )
    
    return fig

def basic_plot(data: pd.Series, metadata: dict = None, title: str = "", yaxis_label: str = "", log_y: bool = False) -> go.Figure:
    """Create a basic plot with a single series"""
    if metadata is not None:
        try:
            title = metadata['title']
        except:
            title = data.name
        try:
            yaxis_label = metadata['Unit']
        except:
            yaxis_label = data.name

    fig = px.line(data, y=data.name, title=title)
    fig.update_layout(
        yaxis_title=yaxis_label, 
        yaxis_type='log' if log_y else 'linear',
        legend=dict(
        orientation="h",
        yanchor="bottom",
        #y=-0.1,  # Position below x-axis
        xanchor="center",
        x=0.5))
    return fig

def dual_axis_basic_plot(primary_data=None, secondary_data=None, 
                        title: str = "", 
                        primary_yaxis_title: str = "Primary Axis",
                        secondary_yaxis_title: str = "Secondary Axis",
                        height: int = 600, width: int = 1000,
                        log_primary: bool = False, log_secondary: bool = False,
                        template: str = "plotly_white") -> go.Figure:
    """
    Create a basic plot with optional secondary y-axis support
    
    Parameters:
        primary_data: pd.Series, pd.DataFrame, or dict of pd.Series for primary (left) y-axis
        secondary_data: pd.Series, pd.DataFrame, or dict of pd.Series for secondary (right) y-axis  
        title (str): Plot title
        primary_yaxis_title (str): Primary y-axis label
        secondary_yaxis_title (str): Secondary y-axis label
        height (int): Plot height in pixels
        width (int): Plot width in pixels
        log_primary (bool): Use log scale for primary y-axis
        log_secondary (bool): Use log scale for secondary y-axis
        template (str): Plotly template to use, options include:
            "plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white", 
            "presentation", "xgridoff", "ygridoff", "gridon", "none":

    Returns:
        go.Figure: Plotly figure with optional dual y-axes
    """
    
    def process_data(data):
        """Convert data to dict of series with proper names"""
        if data is None:
            return {}
        elif isinstance(data, pd.Series):
            return {data.name or 'Series': data}
        elif isinstance(data, pd.DataFrame):
            return {col: data[col] for col in data.columns}
        elif isinstance(data, dict):
            return data
        else:
            raise ValueError("Data must be Series, DataFrame, or dict of Series")
    
    # Process input data
    primary_series = process_data(primary_data)
    secondary_series = process_data(secondary_data)
    
    # Create subplot with secondary y-axis if needed
    has_secondary = len(secondary_series) > 0
    if has_secondary:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()
    
    # Add primary axis traces
    for name, series in primary_series.items():
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                name=name,
                mode='lines'
            ),
            secondary_y=False if has_secondary else None
        )
    
    # Add secondary axis traces
    for name, series in secondary_series.items():
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                name=name,
                mode='lines'
            ),
            secondary_y=True
        )
    
    # Update layout
    fig.update_layout(
        title=title,
        template="plotly_white",
        width=width,
        height=height,
        hovermode="x unified",
        # Horizontal, multi-column legend centered under the x-axis.
        # Note: 'ncols' is available in recent Plotly versions; if your Plotly
        # doesn't support 'ncols' the legend will still be horizontal and centered.
        legend=dict(
            orientation="h",
            x=0.5,
            y=-0.22,               # push legend below x-axis
            xanchor="center",
            yanchor="top",
            bgcolor="rgba(255,255,255,0)",
            bordercolor="rgba(255,255,255,0)",
            #ncols=3
        ),
        # Increase bottom margin to make room for the 3-column legend
        margin=dict(l=50, r=50, t=40, b=110),
        font={"family": "Arial, sans-serif", "size": 14, "color": "black"}
    )
    
    # Update y-axes
    if has_secondary:
        fig.update_yaxes(
            title_text=primary_yaxis_title, 
            secondary_y=False,
            type='log' if log_primary else 'linear'
        )
        fig.update_yaxes(
            title_text=secondary_yaxis_title, 
            secondary_y=True,
            type='log' if log_secondary else 'linear',
            showgrid=False
        )
    else:
        fig.update_yaxes(
            title_text=primary_yaxis_title,
            type='log' if log_primary else 'linear'
        )
    
    #select theme/template
    fig.update_layout(template=template)
    return fig


if __name__ == '__main__':
    # Load the data
    import search_symbol_gui
    watch = search_symbol_gui.Watchlist()
    watch.load_watchlist(filepath = '/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/Watchlists/EquityIndexes/EquityIndexes.xlsx')
    watch.load_watchlist_data()
  
    rets = pd.Series(watch["watchlist_datasets"]['^DJI'], name = "Upper_dataset returns (%)").pct_change()*100
    plot_dict = {
        "upper": [watch["watchlist_datasets"]['^DJI'], watch["watchlist_datasets"]['^NDX']],
        "lower": [rets, rets.rename("rets_50MA").rolling(50).mean()],
        "titles": {"main": "Some equity indexes....", "upper": "SPX maybe or sumtin like dat...", "lower": "Returns in percentage terms."},
    }

    # # Create the figure
    fig = plotly_twoPart_fig(plot_dict)
    fig.show()

    # # Save the figure as an HTML file
    # pio.write_html(fig, file='plotly_figure.html', auto_open=True)
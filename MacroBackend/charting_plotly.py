import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
if __name__ == '__main__':
    import Utilities
else:
    from . import Utilities

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
    Create plotly figure with dual y-axes from trace dicts
    left_traces = {'trace1': {'x': x1, 'y': y1, 'name': 'name1', 'line': {'color': 'blue'}}}
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add left axis traces
    for trace in left_traces.values():
        fig.add_trace(go.Scatter(**trace), secondary_y=False)
        
    # Add right axis traces  
    for trace in right_traces.values():
        fig.add_trace(go.Scatter(**trace), secondary_y=True)

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
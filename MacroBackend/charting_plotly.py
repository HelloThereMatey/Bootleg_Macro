import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
#import numpy as np
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
        fig.add_trace(
            go.Scatter(x=bot_data[1].index, y=bot_data[1], mode='lines', name=bot_data[1].name, line=dict(color='red', width=1)),
            row=2, col=1)
    
    yrange_top = [min(top_data[0].min(), top_data[1].min()), max(top_data[0].max(), top_data[1].max())]
    yrange_bot = [min(bot_data[0].min(), bot_data[1].min()), max(bot_data[0].max(), bot_data[1].max())] if include_lower_plot else None
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

def px_bar(data: pd.DataFrame, title: str = "Bar chart", barmode: str = "group", 
           columns: list = None, yax_label: str = "value") -> go.Figure: 
    """
    Create bar chart using plotly express
    
    Args:
        data (pd.DataFrame): Input DataFrame
        title (str): Chart title
        barmode (str): Bar mode - 'group' or 'stack' 
        columns (list): Columns to plot, defaults to all
        yax_label (str): Y-axis label
    """
    
    if isinstance(data, pd.Series):
        print("Input data is a series, converting to 1D dataframe...")
        data = data.copy().to_frame()
    # Use all columns if none specified
    if columns is None:
        columns = data.columns.tolist()
        print(f"Using all columns: {columns}")
        
    # Create figure using go.Figure instead of px
    fig = go.Figure()
    
    # Add bars for each column
    for col in columns:
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data[col],
                name=col
            )
        )

    # Update layout
    fig.update_layout(
        title=title,
        barmode=barmode,
        margin=dict(l=20, r=20, t=40, b=20),
        font={"family": "Arial, sans-serif", "size": 14, "color": "black"},
        legend=dict(
            orientation="h", 
            yanchor="bottom",
            y=-0.3, 
            xanchor="center",
            x=0.5, 
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            font=dict(size=14)  # Add font size here
        ),
        yaxis_title=yax_label
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
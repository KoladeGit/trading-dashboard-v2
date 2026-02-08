"""
Advanced Trading Charts Module
Professional price charts with entry/exit markers, technical indicators, and trading terminal aesthetics
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

from price_data import price_manager, get_trades_for_symbol, calculate_price_levels

def create_professional_candlestick_chart(
    symbol: str, 
    interval: str = '1h',
    show_volume: bool = True,
    show_indicators: bool = True,
    show_trade_markers: bool = True,
    height: int = 800
) -> go.Figure:
    """
    Create professional candlestick chart with all trading features
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        interval: Timeframe ('1h', '4h', '1d')
        show_volume: Whether to show volume subplot
        show_indicators: Whether to show technical indicators
        show_trade_markers: Whether to show entry/exit markers
        height: Chart height in pixels
        
    Returns:
        Plotly figure with professional styling
    """
    # Get price data
    df = price_manager.get_binance_klines(symbol, interval, 300)
    if df is None or len(df) == 0:
        return create_no_data_chart(symbol)
    
    # Calculate technical indicators
    df = price_manager.calculate_technical_indicators(df)
    
    # Create subplot structure
    if show_volume:
        subplot_specs = [
            [{"secondary_y": False}],  # Price chart
            [{"secondary_y": False}],  # Volume chart  
            [{"secondary_y": False}]   # RSI chart
        ]
        subplot_titles = [f"{symbol} Price Chart", "Volume", "RSI"]
        row_heights = [0.6, 0.2, 0.2]
    else:
        subplot_specs = [
            [{"secondary_y": False}],  # Price chart
            [{"secondary_y": False}]   # RSI chart
        ]
        subplot_titles = [f"{symbol} Price Chart", "RSI"]
        row_heights = [0.8, 0.2]
    
    fig = make_subplots(
        rows=len(subplot_specs),
        cols=1,
        shared_xaxes=True,
        subplot_titles=subplot_titles,
        specs=subplot_specs,
        row_heights=row_heights,
        vertical_spacing=0.05
    )
    
    # === MAIN PRICE CHART ===
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444',
            increasing_fillcolor='rgba(0, 255, 136, 0.3)',
            decreasing_fillcolor='rgba(255, 68, 68, 0.3)',
            line={'width': 1}
        ),
        row=1, col=1
    )
    
    # Technical Indicators
    if show_indicators and len(df) > 20:
        # Moving Averages
        if 'SMA_20' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['SMA_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='#ffaa00', width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        if 'SMA_50' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['SMA_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='#aa00ff', width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        # Bollinger Bands
        if all(col in df.columns for col in ['BB_upper', 'BB_lower', 'BB_middle']):
            # Upper band
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['BB_upper'],
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='rgba(100, 100, 100, 0.3)', width=1, dash='dash'),
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # Lower band
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['BB_lower'],
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='rgba(100, 100, 100, 0.3)', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(100, 100, 100, 0.1)',
                    showlegend=False
                ),
                row=1, col=1
            )
    
    # Support and Resistance Levels
    price_levels = calculate_price_levels(df)
    current_price = df['close'].iloc[-1]
    
    # Add resistance levels
    for level in price_levels['resistance']:
        if level > current_price * 0.95:  # Only show relevant levels
            fig.add_hline(
                y=level,
                line=dict(color='#ff6666', width=1, dash='dot'),
                annotation_text=f"R: {level:.4f}",
                annotation_position="right",
                row=1
            )
    
    # Add support levels
    for level in price_levels['support']:
        if level < current_price * 1.05:  # Only show relevant levels
            fig.add_hline(
                y=level,
                line=dict(color='#66ff66', width=1, dash='dot'),
                annotation_text=f"S: {level:.4f}",
                annotation_position="right",
                row=1
            )
    
    # === TRADE MARKERS ===
    if show_trade_markers:
        trades = get_trades_for_symbol(symbol)
        
        entry_times = []
        entry_prices = []
        entry_annotations = []
        exit_times = []
        exit_prices = []
        exit_annotations = []
        profit_lines_x = []
        profit_lines_y = []
        
        for trade in trades:
            try:
                # Parse timestamps
                entry_time = pd.to_datetime(trade['entry_time'])
                exit_time = pd.to_datetime(trade['exit_time'])
                entry_price = float(trade['entry'])
                exit_price = float(trade['exit'])
                pnl = float(trade['pnl'])
                
                # Check if trade is within chart timeframe
                if (entry_time >= df['timestamp'].min() and 
                    exit_time <= df['timestamp'].max()):
                    
                    entry_times.append(entry_time)
                    entry_prices.append(entry_price)
                    
                    exit_times.append(exit_time)
                    exit_prices.append(exit_price)
                    
                    # Create profit/loss lines
                    profit_lines_x.extend([entry_time, exit_time, None])
                    profit_lines_y.extend([entry_price, exit_price, None])
                    
                    # Annotations
                    entry_annotations.append(f"Entry: ${entry_price:.4f}")
                    exit_annotations.append(f"Exit: ${exit_price:.4f}<br>P&L: ${pnl:+.2f}")
                    
            except Exception as e:
                print(f"Error processing trade marker: {e}")
                continue
        
        # Add entry markers
        if entry_times:
            fig.add_trace(
                go.Scatter(
                    x=entry_times,
                    y=entry_prices,
                    mode='markers',
                    name='Entry Points',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='#00ff00',
                        line=dict(color='#ffffff', width=2)
                    ),
                    text=entry_annotations,
                    hovertemplate='<b>ENTRY</b><br>%{text}<br>Time: %{x}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Add exit markers
        if exit_times:
            fig.add_trace(
                go.Scatter(
                    x=exit_times,
                    y=exit_prices,
                    mode='markers',
                    name='Exit Points',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='#ff0000',
                        line=dict(color='#ffffff', width=2)
                    ),
                    text=exit_annotations,
                    hovertemplate='<b>EXIT</b><br>%{text}<br>Time: %{x}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Add profit/loss connecting lines
        if profit_lines_x:
            fig.add_trace(
                go.Scatter(
                    x=profit_lines_x,
                    y=profit_lines_y,
                    mode='lines',
                    name='Trade P&L Lines',
                    line=dict(color='rgba(255, 255, 0, 0.6)', width=2, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
    
    # === VOLUME CHART ===
    if show_volume and 'volume' in df.columns:
        # Color bars based on price movement
        colors = ['#00ff88' if close >= open else '#ff4444' 
                  for close, open in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7,
                showlegend=False
            ),
            row=2 if show_volume else None, col=1
        )
        
        # Volume SMA
        if 'Volume_SMA' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['Volume_SMA'],
                    mode='lines',
                    name='Volume SMA',
                    line=dict(color='#ffaa00', width=2),
                    showlegend=False
                ),
                row=2, col=1
            )
    
    # === RSI CHART ===
    rsi_row = 3 if show_volume else 2
    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#00aaff', width=2),
                showlegend=False
            ),
            row=rsi_row, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line=dict(color='#ff4444', width=1, dash='dash'), row=rsi_row)
        fig.add_hline(y=30, line=dict(color='#00ff88', width=1, dash='dash'), row=rsi_row)
        fig.add_hline(y=50, line=dict(color='#888888', width=1, dash='dot'), row=rsi_row)
    
    # === PROFESSIONAL STYLING ===
    fig.update_layout(
        title=dict(
            text=f"<b>{symbol}</b> • {interval.upper()} • Professional Trading Terminal",
            font=dict(size=20, color='#ffffff', family='Arial Black'),
            x=0.5
        ),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#1a1a1a',
        font=dict(color='#ffffff', family='Arial'),
        height=height,
        margin=dict(l=80, r=80, t=80, b=40),
        
        # Grid styling
        xaxis=dict(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            color='#cccccc'
        ),
        yaxis=dict(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            color='#cccccc',
            side='right'
        ),
        
        # Legend styling
        legend=dict(
            bgcolor='rgba(26, 26, 26, 0.8)',
            bordercolor='#444444',
            borderwidth=1,
            font=dict(color='#ffffff'),
            orientation='h',
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01
        ),
        
        # Hover styling
        hoverlabel=dict(
            bgcolor='#1a1a1a',
            bordercolor='#444444',
            font=dict(color='#ffffff', family='monospace')
        )
    )
    
    # Update all subplot axes
    for i in range(1, len(subplot_specs) + 1):
        fig.update_xaxes(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            color='#cccccc',
            row=i, col=1
        )
        fig.update_yaxes(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            color='#cccccc',
            side='right',
            row=i, col=1
        )
    
    # Range selector for time navigation
    fig.update_xaxes(
        rangeslider=dict(visible=False),
        rangeselector=dict(
            buttons=list([
                dict(count=24, label="24H", step="hour", stepmode="backward"),
                dict(count=7, label="7D", step="day", stepmode="backward"),
                dict(count=30, label="30D", step="day", stepmode="backward"),
                dict(step="all", label="ALL")
            ]),
            bgcolor='#333333',
            activecolor='#00ff88',
            font=dict(color='#ffffff')
        ),
        row=1, col=1
    )
    
    return fig

def create_multi_symbol_dashboard(
    symbols: List[str], 
    interval: str = '1h',
    max_charts: int = 4
) -> List[go.Figure]:
    """
    Create multiple price charts for different symbols
    
    Args:
        symbols: List of trading pairs
        interval: Timeframe
        max_charts: Maximum number of charts to create
        
    Returns:
        List of Plotly figures
    """
    figures = []
    
    for symbol in symbols[:max_charts]:
        try:
            fig = create_professional_candlestick_chart(
                symbol=symbol,
                interval=interval,
                show_volume=True,
                show_indicators=True,
                show_trade_markers=True,
                height=600
            )
            figures.append(fig)
        except Exception as e:
            print(f"Error creating chart for {symbol}: {e}")
            continue
    
    return figures

def create_portfolio_heatmap(trades_by_symbol: Dict[str, List[Dict]]) -> go.Figure:
    """
    Create a portfolio performance heatmap
    
    Args:
        trades_by_symbol: Dictionary of symbol -> trades list
        
    Returns:
        Plotly heatmap figure
    """
    if not trades_by_symbol:
        return create_no_data_chart("Portfolio Heatmap")
    
    # Calculate performance metrics for each symbol
    symbols = []
    total_pnl = []
    win_rates = []
    trade_counts = []
    
    for symbol, trades in trades_by_symbol.items():
        if not trades:
            continue
            
        symbols.append(symbol.split('/')[0])  # Just the base currency
        
        pnl_sum = sum(trade.get('pnl', 0) for trade in trades)
        total_pnl.append(pnl_sum)
        
        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = wins / len(trades) * 100 if trades else 0
        win_rates.append(win_rate)
        
        trade_counts.append(len(trades))
    
    if not symbols:
        return create_no_data_chart("Portfolio Heatmap")
    
    # Create heatmap matrix
    z_data = [total_pnl, win_rates, trade_counts]
    y_labels = ['Total P&L', 'Win Rate %', 'Trade Count']
    
    # Normalize data for better color representation
    z_normalized = []
    for row in z_data:
        if max(row) - min(row) != 0:
            normalized = [(x - min(row)) / (max(row) - min(row)) for x in row]
        else:
            normalized = [0.5] * len(row)  # All values same
        z_normalized.append(normalized)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_normalized,
        x=symbols,
        y=y_labels,
        colorscale='RdYlGn',
        text=[[f"${pnl:.2f}" for pnl in total_pnl],
              [f"{wr:.1f}%" for wr in win_rates],
              [f"{tc} trades" for tc in trade_counts]],
        texttemplate="%{text}",
        textfont={"color": "white", "size": 12},
        hoverimfo='text'
    ))
    
    fig.update_layout(
        title=dict(
            text="Portfolio Performance Heatmap",
            font=dict(size=18, color='#ffffff'),
            x=0.5
        ),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#1a1a1a',
        font=dict(color='#ffffff'),
        xaxis=dict(side='top'),
        height=300
    )
    
    return fig

def create_no_data_chart(title: str = "No Data Available") -> go.Figure:
    """
    Create a placeholder chart when no data is available
    """
    fig = go.Figure()
    
    fig.add_annotation(
        text=f"📊 {title}<br><br>No price data available",
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=20, color='#888888')
    )
    
    fig.update_layout(
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#1a1a1a',
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    
    return fig

def create_trade_timeline_chart(all_trades: List[Dict]) -> go.Figure:
    """
    Create a timeline chart showing all trades chronologically
    
    Args:
        all_trades: List of all trade dictionaries
        
    Returns:
        Plotly timeline figure
    """
    if not all_trades:
        return create_no_data_chart("Trade Timeline")
    
    # Sort trades by exit time
    sorted_trades = sorted(all_trades, key=lambda x: x.get('exit_time', ''))
    
    timestamps = []
    cumulative_pnl = []
    colors = []
    symbols = []
    pnl_values = []
    
    running_pnl = 0
    
    for trade in sorted_trades:
        try:
            exit_time = pd.to_datetime(trade['exit_time'])
            pnl = float(trade['pnl'])
            symbol = trade.get('symbol', 'Unknown')
            
            running_pnl += pnl
            
            timestamps.append(exit_time)
            cumulative_pnl.append(running_pnl)
            pnl_values.append(pnl)
            symbols.append(symbol)
            
            # Color based on profit/loss
            colors.append('#00ff88' if pnl > 0 else '#ff4444')
            
        except Exception as e:
            print(f"Error processing trade for timeline: {e}")
            continue
    
    if not timestamps:
        return create_no_data_chart("Trade Timeline")
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Cumulative P&L Over Time', 'Individual Trade P&L'],
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1
    )
    
    # Cumulative P&L line
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=cumulative_pnl,
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#00aaff', width=3),
            marker=dict(size=6, color='#00aaff'),
            hovertemplate='<b>Cumulative P&L: $%{y:.2f}</b><br>Date: %{x}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Individual trade bars
    fig.add_trace(
        go.Bar(
            x=timestamps,
            y=pnl_values,
            name='Trade P&L',
            marker_color=colors,
            text=[f"{s}<br>${p:+.2f}" for s, p in zip(symbols, pnl_values)],
            hovertemplate='<b>%{customdata}</b><br>P&L: $%{y:+.2f}<br>Date: %{x}<extra></extra>',
            customdata=symbols
        ),
        row=2, col=1
    )
    
    # Add zero line for reference
    fig.add_hline(y=0, line_dash="dash", line_color="#888888", row=1)
    fig.add_hline(y=0, line_dash="dash", line_color="#888888", row=2)
    
    # Professional styling
    fig.update_layout(
        title=dict(
            text="Trading Performance Timeline",
            font=dict(size=20, color='#ffffff'),
            x=0.5
        ),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#1a1a1a',
        font=dict(color='#ffffff'),
        height=600,
        showlegend=False
    )
    
    # Update axes
    for i in [1, 2]:
        fig.update_xaxes(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            color='#cccccc',
            row=i, col=1
        )
        fig.update_yaxes(
            gridcolor='#333333',
            gridwidth=1,
            showgrid=True,
            color='#cccccc',
            side='right',
            row=i, col=1
        )
    
    return fig
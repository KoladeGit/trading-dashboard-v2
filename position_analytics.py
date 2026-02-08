#!/usr/bin/env python3
"""
Advanced Position Analytics Module
Enhanced risk metrics and performance analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np


def calculate_portfolio_risk_metrics(positions_data, portfolio_value):
    """Calculate comprehensive portfolio-level risk metrics"""
    
    if not positions_data:
        return {
            'total_exposure': 0,
            'concentration_risk': 0,
            'var_95': 0,
            'max_drawdown_risk': 0,
            'correlation_risk': 'LOW',
            'leverage_ratio': 0,
            'risk_score': 0
        }
    
    total_position_value = sum(p['metrics']['position_value'] for p in positions_data.values())
    position_sizes = [p['metrics']['position_size_pct'] for p in positions_data.values()]
    unrealized_pnls = [p['metrics']['unrealized_pnl'] for p in positions_data.values()]
    
    # Concentration risk (largest position as % of portfolio)
    concentration_risk = max(position_sizes) if position_sizes else 0
    
    # Total market exposure
    total_exposure = (total_position_value / portfolio_value * 100) if portfolio_value > 0 else 0
    
    # Simple VaR (95% confidence) - rough estimate based on position volatility
    pnl_volatility = np.std(unrealized_pnls) if len(unrealized_pnls) > 1 else abs(max(unrealized_pnls)) if unrealized_pnls else 0
    var_95 = pnl_volatility * 1.65  # 95% confidence interval
    
    # Maximum potential drawdown (all positions hit stop loss)
    max_drawdown_risk = 0
    for symbol, data in positions_data.items():
        position = data['position']
        metrics = data['metrics']
        stop_price = position.get('stop', 0)
        entry_price = position.get('entry', 0)
        amount = position.get('amount', 0)
        
        if stop_price > 0 and entry_price > 0:
            stop_loss = (entry_price - stop_price) * amount
            max_drawdown_risk += abs(stop_loss)
    
    # Correlation risk assessment (basic)
    crypto_symbols = [s for s in positions_data.keys() if any(c in s for c in ['BTC', 'ETH', 'SOL', 'DOGE', 'ADA'])]
    correlation_risk = 'HIGH' if len(crypto_symbols) >= 3 else 'MEDIUM' if len(crypto_symbols) >= 2 else 'LOW'
    
    # Leverage ratio (total exposure / available capital)
    leverage_ratio = total_exposure / 100
    
    # Overall risk score (0-100)
    risk_score = min(100, (concentration_risk * 0.3 + total_exposure * 0.3 + min(var_95/portfolio_value*100, 50) * 0.4))
    
    return {
        'total_exposure': total_exposure,
        'concentration_risk': concentration_risk,
        'var_95': var_95,
        'max_drawdown_risk': max_drawdown_risk,
        'correlation_risk': correlation_risk,
        'leverage_ratio': leverage_ratio,
        'risk_score': risk_score
    }


def render_risk_dashboard(positions_data, portfolio_value):
    """Render comprehensive risk dashboard"""
    
    risk_metrics = calculate_portfolio_risk_metrics(positions_data, portfolio_value)
    
    st.markdown("### ⚠️ PORTFOLIO RISK ANALYSIS")
    
    # Risk Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_score = risk_metrics['risk_score']
        risk_color = "#ff3333" if risk_score > 70 else "#ff6600" if risk_score > 40 else "#39ff14"
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 2px solid {risk_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                RISK SCORE
            </div>
            <div style="color: {risk_color}; font-size: 2.5rem; font-weight: bold; 
                        text-shadow: 0 0 10px {risk_color}; font-family: monospace;">
                {risk_score:.0f}
            </div>
            <div style="color: #888; font-size: 0.8rem;">
                /100 (DYNAMIC)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        exposure_color = "#ff3333" if risk_metrics['total_exposure'] > 80 else "#ff6600" if risk_metrics['total_exposure'] > 60 else "#39ff14"
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 2px solid {exposure_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                MARKET EXPOSURE
            </div>
            <div style="color: {exposure_color}; font-size: 2.5rem; font-weight: bold; font-family: monospace;">
                {risk_metrics['total_exposure']:.1f}%
            </div>
            <div style="color: #888; font-size: 0.8rem;">
                OF PORTFOLIO
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        concentration_color = "#ff3333" if risk_metrics['concentration_risk'] > 25 else "#ff6600" if risk_metrics['concentration_risk'] > 15 else "#39ff14"
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 2px solid {concentration_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                CONCENTRATION
            </div>
            <div style="color: {concentration_color}; font-size: 2.5rem; font-weight: bold; font-family: monospace;">
                {risk_metrics['concentration_risk']:.1f}%
            </div>
            <div style="color: #888; font-size: 0.8rem;">
                LARGEST POSITION
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        correlation_colors = {"HIGH": "#ff3333", "MEDIUM": "#ff6600", "LOW": "#39ff14"}
        correlation_color = correlation_colors[risk_metrics['correlation_risk']]
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 2px solid {correlation_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                CORRELATION RISK
            </div>
            <div style="color: {correlation_color}; font-size: 1.8rem; font-weight: bold; font-family: monospace;">
                {risk_metrics['correlation_risk']}
            </div>
            <div style="color: #888; font-size: 0.8rem;">
                DIVERSIFICATION
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Advanced Risk Metrics
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 ADVANCED RISK METRICS")
        
        st.markdown(f"""
        <div style="background: #0a0a0a; padding: 15px; border-radius: 8px; border: 1px solid #333;">
            <table style="width: 100%; color: #c9d1d9; font-family: monospace; font-size: 0.9rem;">
                <tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 8px; color: #888;">Value at Risk (95%):</td>
                    <td style="padding: 8px; text-align: right; color: #ff6600;">${risk_metrics['var_95']:.2f}</td>
                </tr>
                <tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 8px; color: #888;">Max Drawdown Risk:</td>
                    <td style="padding: 8px; text-align: right; color: #ff3333;">${risk_metrics['max_drawdown_risk']:.2f}</td>
                </tr>
                <tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 8px; color: #888;">Leverage Ratio:</td>
                    <td style="padding: 8px; text-align: right; color: #39ff14;">{risk_metrics['leverage_ratio']:.2f}x</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #888;">Position Count:</td>
                    <td style="padding: 8px; text-align: right; color: #ff6600;">{len(positions_data)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if positions_data:
            render_position_allocation_chart(positions_data)


def render_position_allocation_chart(positions_data):
    """Render position allocation pie chart"""
    
    symbols = [s.replace('/USDT', '') for s in positions_data.keys()]
    values = [p['metrics']['position_value'] for p in positions_data.values()]
    colors = ['#ff6b35', '#39ff14', '#58a6ff', '#ff3333', '#ff6600', '#9f7aea']
    
    fig = go.Figure(data=[go.Pie(
        labels=symbols,
        values=values,
        hole=.4,
        marker=dict(colors=colors[:len(symbols)], line=dict(color='#0d1117', width=2)),
        textfont=dict(color='white', size=12),
        hovertemplate='<b>%{label}</b><br>Value: $%{value:.2f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text="💼 POSITION ALLOCATION",
            font=dict(size=14, color='#ff6b35', family='monospace'),
            x=0.5
        ),
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9', family='monospace'),
        height=300,
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_performance_heatmap(positions_data):
    """Render position performance heatmap"""
    
    if not positions_data:
        return
    
    symbols = list(positions_data.keys())
    metrics = ['Unrealized P&L %', 'Risk Level', 'Time Held', 'Distance to Target']
    
    # Prepare data matrix
    data_matrix = []
    symbol_labels = []
    
    for symbol in symbols:
        data = positions_data[symbol]
        metrics_data = data['metrics']
        
        symbol_labels.append(symbol.replace('/USDT', ''))
        
        # Normalize metrics for heatmap
        pnl_pct = metrics_data['unrealized_pnl_pct']
        risk_pct = metrics_data['position_size_pct']
        time_hours = metrics_data['hours_held']
        target_dist = metrics_data['dist_to_target_pct']
        
        data_matrix.append([pnl_pct, risk_pct, time_hours, target_dist])
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=data_matrix,
        x=metrics,
        y=symbol_labels,
        colorscale=[[0, '#ff3333'], [0.5, '#ffff00'], [1, '#39ff14']],
        hovertemplate='<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>',
        colorbar=dict(title="Metric Value", titlefont=dict(color='white'))
    ))
    
    fig.update_layout(
        title=dict(
            text="🔥 POSITION PERFORMANCE HEATMAP",
            font=dict(size=16, color='#ff6b35', family='monospace')
        ),
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9', family='monospace'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_position_timeline(positions_data):
    """Render position timeline showing entry times and durations"""
    
    if not positions_data:
        return
    
    fig = go.Figure()
    
    current_time = datetime.now()
    y_pos = 0
    
    for symbol, data in positions_data.items():
        position = data['position']
        metrics = data['metrics']
        
        # Parse entry time
        try:
            entry_time = datetime.fromisoformat(position['time'].replace('Z', ''))
        except:
            entry_time = current_time - timedelta(hours=1)
        
        # Color based on P&L
        color = '#39ff14' if metrics['unrealized_pnl'] >= 0 else '#ff3333'
        
        # Add timeline bar
        fig.add_trace(go.Scatter(
            x=[entry_time, current_time],
            y=[y_pos, y_pos],
            mode='lines+markers',
            name=symbol.replace('/USDT', ''),
            line=dict(color=color, width=8),
            marker=dict(size=12, color=color),
            hovertemplate=f'<b>{symbol}</b><br>' +
                         f'Entry: {entry_time.strftime("%H:%M:%S")}<br>' +
                         f'Duration: {metrics["time_str"]}<br>' +
                         f'P&L: ${metrics["unrealized_pnl"]:+.2f}<extra></extra>'
        ))
        
        y_pos += 1
    
    fig.update_layout(
        title=dict(
            text="⏱️ POSITION TIMELINE • LIVE DURATION TRACKING",
            font=dict(size=16, color='#ff6b35', family='monospace')
        ),
        xaxis_title="Time",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(positions_data))),
            ticktext=[s.replace('/USDT', '') for s in positions_data.keys()],
            showgrid=False
        ),
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9', family='monospace'),
        height=300,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_comprehensive_analytics(positions_data, portfolio_value):
    """Render comprehensive position analytics dashboard"""
    
    if not positions_data:
        st.info("📊 Analytics will appear when positions are active")
        return
    
    st.markdown("---")
    st.markdown("## 📈 COMPREHENSIVE POSITION ANALYTICS")
    
    # Risk Dashboard
    render_risk_dashboard(positions_data, portfolio_value)
    
    # Performance Analytics
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        render_performance_heatmap(positions_data)
    
    with col2:
        render_position_timeline(positions_data)
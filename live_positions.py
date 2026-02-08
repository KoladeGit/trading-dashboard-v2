#!/usr/bin/env python3
"""
Live Position Tracker with Real-time P&L
Enhanced position monitoring for trading dashboard
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_live_prices(symbols):
    """Fetch real-time prices from Binance API"""
    prices = {}
    
    try:
        # Convert symbols to Binance format (e.g., BTC/USDT -> BTCUSDT)
        binance_symbols = [symbol.replace('/', '') for symbol in symbols]
        symbol_param = ','.join(f'"{s}"' for s in binance_symbols)
        
        url = "https://api.binance.com/api/v3/ticker/price"
        
        for symbol in binance_symbols:
            try:
                response = requests.get(f"{url}?symbol={symbol}", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    # Convert back to original format
                    original_symbol = symbol.replace('USDT', '/USDT')
                    prices[original_symbol] = float(data['price'])
                else:
                    st.warning(f"Failed to fetch price for {symbol}: {response.status_code}")
            except Exception as e:
                st.error(f"Error fetching {symbol}: {str(e)}")
                
    except Exception as e:
        st.error(f"Error in price fetch: {str(e)}")
    
    return prices


def calculate_position_metrics(position, current_price, portfolio_value):
    """Calculate comprehensive position metrics"""
    entry_price = position.get('entry', 0)
    amount = position.get('amount', 0)
    stop_price = position.get('stop', 0)
    target_price = position.get('target', 0)
    entry_time_str = position.get('time', '')
    
    if entry_price == 0:
        return None
    
    # Basic P&L calculations
    position_value = current_price * amount
    unrealized_pnl = (current_price - entry_price) * amount
    unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100
    
    # Risk metrics
    position_size_pct = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
    
    # Distance calculations
    dist_to_stop_pct = ((current_price - stop_price) / current_price * 100) if stop_price > 0 else 0
    dist_to_target_pct = ((target_price - current_price) / current_price * 100) if target_price > 0 else 0
    
    # Break-even calculations
    break_even_price = entry_price
    break_even_distance = abs(current_price - break_even_price) / current_price * 100
    
    # Time metrics
    try:
        entry_dt = datetime.fromisoformat(entry_time_str.replace('Z', ''))
        time_in_position = datetime.now() - entry_dt
        hours_held = time_in_position.total_seconds() / 3600
        days_held = time_in_position.days
        
        # Time-weighted return calculation
        if hours_held > 0:
            annualized_return = (unrealized_pnl_pct / hours_held) * 24 * 365
        else:
            annualized_return = 0
            
        # Format time string
        if time_in_position.days > 0:
            time_str = f"{days_held}d {time_in_position.seconds//3600}h"
        elif hours_held >= 1:
            time_str = f"{hours_held:.1f}h"
        else:
            minutes = time_in_position.seconds // 60
            time_str = f"{minutes}m"
            
    except Exception:
        time_str = "N/A"
        hours_held = 0
        annualized_return = 0
    
    # Risk level calculation
    if position_size_pct > 20:
        risk_level = "HIGH"
        risk_color = "#ff3333"
    elif position_size_pct > 10:
        risk_level = "MEDIUM"
        risk_color = "#ff6600"
    else:
        risk_level = "LOW"
        risk_color = "#39ff14"
    
    # Price momentum (basic)
    price_change_from_entry = (current_price - entry_price) / entry_price
    if abs(price_change_from_entry) > 0.05:  # >5% move
        momentum = "HIGH"
    elif abs(price_change_from_entry) > 0.02:  # >2% move
        momentum = "MEDIUM"
    else:
        momentum = "LOW"
    
    return {
        'position_value': position_value,
        'unrealized_pnl': unrealized_pnl,
        'unrealized_pnl_pct': unrealized_pnl_pct,
        'position_size_pct': position_size_pct,
        'dist_to_stop_pct': dist_to_stop_pct,
        'dist_to_target_pct': dist_to_target_pct,
        'break_even_price': break_even_price,
        'break_even_distance': break_even_distance,
        'time_str': time_str,
        'hours_held': hours_held,
        'annualized_return': annualized_return,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'momentum': momentum
    }


def render_position_heat_map(positions_data):
    """Create a position heat map by risk/exposure"""
    if not positions_data:
        return None
    
    symbols = list(positions_data.keys())
    risk_levels = [positions_data[s]['metrics']['position_size_pct'] for s in symbols]
    pnl_values = [positions_data[s]['metrics']['unrealized_pnl'] for s in symbols]
    
    # Create heat map
    fig = go.Figure(data=go.Scatter(
        x=risk_levels,
        y=pnl_values,
        mode='markers+text',
        text=[s.replace('/USDT', '') for s in symbols],
        textposition="middle center",
        marker=dict(
            size=[abs(pnl) * 10 + 20 for pnl in pnl_values],
            color=pnl_values,
            colorscale=[[0, '#ff3333'], [0.5, '#ffff00'], [1, '#39ff14']],
            showscale=True,
            colorbar=dict(title="P&L ($)"),
            line=dict(width=2, color='white')
        ),
        hovertemplate='<b>%{text}</b><br>' +
                      'Risk: %{x:.1f}% of portfolio<br>' +
                      'P&L: $%{y:+.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="🗺️ POSITION HEAT MAP • Risk vs P&L",
        xaxis_title="Position Size (% of Portfolio)",
        yaxis_title="Unrealized P&L ($)",
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9', family='monospace'),
        title_font=dict(size=16, color='#ff6b35')
    )
    
    return fig


def render_live_position_tracker(bot_data, portfolio_value=1000):
    """Render the complete live position tracking interface"""
    
    # Get positions
    positions = bot_data.get('trading_state', {}).get('positions', {})
    
    if not positions:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid #ff6600; 
                    border-radius: 8px; padding: 30px; text-align: center; margin: 20px 0;">
            <h3 style="color: #ff6600; margin-bottom: 15px;">📭 NO ACTIVE POSITIONS</h3>
            <p style="color: #888; font-size: 1.1rem;">Capital is currently idle • Monitoring for entry signals</p>
            <div style="margin-top: 20px; padding: 15px; background: #0a0a0a; border-radius: 5px;">
                <span style="color: #39ff14; font-family: monospace;">STATUS: SCANNING MARKETS █</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get live prices
    symbols = list(positions.keys())
    live_prices = get_live_prices(symbols)
    
    # Calculate metrics for all positions
    positions_data = {}
    total_unrealized_pnl = 0
    total_position_value = 0
    
    for symbol, position in positions.items():
        current_price = live_prices.get(symbol, position.get('entry', 0))
        metrics = calculate_position_metrics(position, current_price, portfolio_value)
        
        if metrics:
            positions_data[symbol] = {
                'position': position,
                'current_price': current_price,
                'metrics': metrics
            }
            total_unrealized_pnl += metrics['unrealized_pnl']
            total_position_value += metrics['position_value']
    
    # Portfolio-level metrics
    portfolio_pnl_pct = (total_unrealized_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
    market_exposure_pct = (total_position_value / portfolio_value * 100) if portfolio_value > 0 else 0
    
    # Header with auto-refresh
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="color: #ff6b35; margin: 0; font-family: monospace;">
            📍 LIVE POSITIONS • REAL-TIME P&L TRACKER
        </h2>
        <div style="color: #39ff14; font-family: monospace; font-size: 0.9rem;">
            🔄 LAST UPDATE: {datetime.now().strftime('%H:%M:%S')} • AUTO-REFRESH: 30s
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Portfolio Summary
    total_pnl_color = "#39ff14" if total_unrealized_pnl >= 0 else "#ff3333"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid {total_pnl_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                TOTAL UNREALIZED P&L
            </div>
            <div style="color: {total_pnl_color}; font-size: 1.8rem; font-weight: bold; 
                        text-shadow: 0 0 10px {total_pnl_color}; font-family: monospace;">
                ${total_unrealized_pnl:+.2f}
            </div>
            <div style="color: {total_pnl_color}; font-size: 1rem; margin-top: 5px;">
                ({portfolio_pnl_pct:+.2f}% of portfolio)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid #39ff14; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                POSITIONS VALUE
            </div>
            <div style="color: #39ff14; font-size: 1.8rem; font-weight: bold; font-family: monospace;">
                ${total_position_value:.2f}
            </div>
            <div style="color: #888; font-size: 1rem; margin-top: 5px;">
                {market_exposure_pct:.1f}% market exposure
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_risk_level = sum(p['metrics']['position_size_pct'] for p in positions_data.values()) / len(positions_data) if positions_data else 0
        risk_color = "#ff3333" if avg_risk_level > 15 else "#ff6600" if avg_risk_level > 10 else "#39ff14"
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid {risk_color}; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                AVG POSITION RISK
            </div>
            <div style="color: {risk_color}; font-size: 1.8rem; font-weight: bold; font-family: monospace;">
                {avg_risk_level:.1f}%
            </div>
            <div style="color: #888; font-size: 1rem; margin-top: 5px;">
                of portfolio per position
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid #ff6600; 
                    border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                ACTIVE POSITIONS
            </div>
            <div style="color: #ff6600; font-size: 1.8rem; font-weight: bold; font-family: monospace;">
                {len(positions_data)}
            </div>
            <div style="color: #888; font-size: 1rem; margin-top: 5px;">
                positions monitoring
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Position Heat Map
    if len(positions_data) > 1:
        st.markdown("---")
        heat_map_fig = render_position_heat_map(positions_data)
        if heat_map_fig:
            st.plotly_chart(heat_map_fig, use_container_width=True)
    
    # Individual Position Cards
    st.markdown("---")
    st.markdown("### 💼 INDIVIDUAL POSITION ANALYSIS")
    
    # Sort positions by unrealized P&L (biggest winners/losers first)
    sorted_positions = sorted(positions_data.items(), 
                             key=lambda x: x[1]['metrics']['unrealized_pnl'], 
                             reverse=True)
    
    # Display positions in columns (max 3 per row)
    for i in range(0, len(sorted_positions), 3):
        cols = st.columns(min(3, len(sorted_positions) - i))
        
        for j, (symbol, data) in enumerate(sorted_positions[i:i+3]):
            with cols[j]:
                render_position_card(symbol, data)


def render_position_card(symbol, data):
    """Render individual position card with all metrics"""
    position = data['position']
    current_price = data['current_price']
    metrics = data['metrics']
    
    # Color coding
    pnl_color = "#39ff14" if metrics['unrealized_pnl'] >= 0 else "#ff3333"
    border_color = pnl_color
    
    # Format price function
    def fmt_price(p):
        if p < 0.01:
            return f"${p:.6f}"
        elif p < 1:
            return f"${p:.4f}"
        elif p < 100:
            return f"${p:.3f}"
        else:
            return f"${p:,.2f}"
    
    # Progress bar for stop to target
    stop_price = position.get('stop', 0)
    target_price = position.get('target', 0)
    entry_price = position.get('entry', 0)
    
    if target_price > stop_price and stop_price > 0:
        price_range = target_price - stop_price
        price_progress = ((current_price - stop_price) / price_range) * 100
        price_progress = max(0, min(100, price_progress))
    else:
        price_progress = 50
    
    # Blinking effect for significant changes
    blink_class = "blink" if abs(metrics['unrealized_pnl_pct']) > 2 else ""
    
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #1a1a1a, #0d0d0d); 
                border: 2px solid {border_color}; 
                border-radius: 10px; 
                padding: 20px; 
                margin-bottom: 20px;
                box-shadow: 0 0 20px rgba(255, 107, 53, 0.3);">
        
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="color: #ff6b35; margin: 0; font-size: 1.3rem; font-family: monospace;">
                {symbol.replace('/USDT', '')}
            </h3>
            <div style="text-align: right;">
                <div style="color: #888; font-size: 0.8rem;">TIME IN POSITION</div>
                <div style="color: #39ff14; font-size: 1rem; font-weight: bold;">⏱ {metrics['time_str']}</div>
            </div>
        </div>
        
        <!-- Price Info -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div>
                <span style="color: #888; font-size: 0.8rem;">ENTRY PRICE</span><br>
                <span style="color: #aaa; font-family: monospace; font-size: 1rem;">{fmt_price(entry_price)}</span>
            </div>
            <div>
                <span style="color: #888; font-size: 0.8rem;">CURRENT PRICE</span><br>
                <span style="color: {pnl_color}; font-family: monospace; font-size: 1rem; font-weight: bold;">
                    {fmt_price(current_price)}
                </span>
            </div>
        </div>
        
        <!-- Main P&L Display -->
        <div style="text-align: center; padding: 15px; background: #0a0a0a; 
                    border: 1px solid {pnl_color}; border-radius: 8px; margin-bottom: 15px;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px;">
                UNREALIZED P&L
            </div>
            <div class="{blink_class}" style="color: {pnl_color}; font-size: 2rem; font-weight: bold; 
                        font-family: monospace; text-shadow: 0 0 10px {pnl_color}; margin-bottom: 5px;">
                ${metrics['unrealized_pnl']:+.4f}
            </div>
            <div style="color: {pnl_color}; font-size: 1.2rem; font-weight: bold;">
                ({metrics['unrealized_pnl_pct']:+.2f}%)
            </div>
        </div>
        
        <!-- Position Details -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; 
                    font-size: 0.9rem; font-family: monospace;">
            <div>
                <span style="color: #888;">Size:</span>
                <span style="color: #aaa; float: right;">{position.get('amount', 0):.6f}</span>
            </div>
            <div>
                <span style="color: #888;">Value:</span>
                <span style="color: #39ff14; float: right;">${metrics['position_value']:.2f}</span>
            </div>
            <div>
                <span style="color: #888;">% of Portfolio:</span>
                <span style="color: {metrics['risk_color']}; float: right; font-weight: bold;">
                    {metrics['position_size_pct']:.1f}%
                </span>
            </div>
            <div>
                <span style="color: #888;">Risk Level:</span>
                <span style="color: {metrics['risk_color']}; float: right; font-weight: bold;">
                    {metrics['risk_level']}
                </span>
            </div>
        </div>
        
        <!-- Advanced Analytics -->
        <div style="background: #0a0a0a; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px;">
                ADVANCED METRICS
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.8rem; font-family: monospace;">
                <div>
                    <span style="color: #888;">Break-even:</span><br>
                    <span style="color: #aaa;">{fmt_price(metrics['break_even_price'])}</span>
                </div>
                <div>
                    <span style="color: #888;">Distance:</span><br>
                    <span style="color: #aaa;">{metrics['break_even_distance']:.2f}%</span>
                </div>
                <div>
                    <span style="color: #888;">Annualized Return:</span><br>
                    <span style="color: {pnl_color};">{metrics['annualized_return']:+.1f}%</span>
                </div>
                <div>
                    <span style="color: #888;">Momentum:</span><br>
                    <span style="color: #ff6600;">{metrics['momentum']}</span>
                </div>
            </div>
        </div>
        
        <!-- Stop Loss & Take Profit -->
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem;">
                <span style="color: #ff3333;">🛑 Stop: {fmt_price(stop_price)}</span>
                <span style="color: #ff3333;">({metrics['dist_to_stop_pct']:.1f}%)</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem;">
                <span style="color: #39ff14;">🎯 Target: {fmt_price(target_price)}</span>
                <span style="color: #39ff14;">({metrics['dist_to_target_pct']:.1f}%)</span>
            </div>
        </div>
        
        <!-- Progress Bar -->
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.7rem;">
                <span style="color: #ff3333;">STOP</span>
                <span style="color: #888;">{price_progress:.0f}%</span>
                <span style="color: #39ff14;">TARGET</span>
            </div>
            <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 6px; 
                        height: 15px; position: relative; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #ff3333, #ff6600, #39ff14); 
                            width: 100%; height: 100%; opacity: 0.4;"></div>
                <div style="position: absolute; left: {price_progress}%; top: 0; width: 4px; 
                            height: 100%; background: white; box-shadow: 0 0 8px white;"></div>
            </div>
        </div>
        
        <!-- Entry Reason -->
        <div style="color: #666; font-size: 0.7rem; font-style: italic; text-align: center; 
                    margin-top: 10px; padding-top: 10px; border-top: 1px solid #333;">
            Entry: {position.get('reason', 'Manual')[:50]}...
        </div>
    </div>
    
    <style>
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0.7; }}
        }}
        .blink {{
            animation: blink 1s infinite;
        }}
    </style>
    """, unsafe_allow_html=True)


# Auto-refresh functionality
def setup_auto_refresh():
    """Setup auto-refresh for real-time updates"""
    st.markdown("""
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function(){
            window.location.reload();
        }, 30000);
    </script>
    """, unsafe_allow_html=True)


# Main integration function
def integrate_live_positions_section(bot_data):
    """Main function to integrate live positions into dashboard"""
    
    # Setup auto-refresh
    setup_auto_refresh()
    
    # Render the live position tracker
    portfolio_value = bot_data.get('account', {}).get('total_usd', 1000)
    render_live_position_tracker(bot_data, portfolio_value)
    
    # Add comprehensive analytics if positions exist
    positions = bot_data.get('trading_state', {}).get('positions', {})
    if positions:
        # Import and render advanced analytics
        try:
            from position_analytics import render_comprehensive_analytics
            
            # Get live prices and calculate metrics for analytics
            symbols = list(positions.keys())
            live_prices = get_live_prices(symbols)
            
            # Calculate metrics for all positions
            positions_data = {}
            for symbol, position in positions.items():
                current_price = live_prices.get(symbol, position.get('entry', 0))
                metrics = calculate_position_metrics(position, current_price, portfolio_value)
                
                if metrics:
                    positions_data[symbol] = {
                        'position': position,
                        'current_price': current_price,
                        'metrics': metrics
                    }
            
            # Render comprehensive analytics
            render_comprehensive_analytics(positions_data, portfolio_value)
            
        except ImportError:
            st.warning("⚠️ Advanced analytics module not available")
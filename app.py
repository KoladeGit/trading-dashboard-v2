#!/usr/bin/env python3
"""
Trading Dashboard - $1K Crypto Mission
NASA Mission Control Aesthetic
Public dashboard - view only, no trade execution
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# Page config
st.set_page_config(
    page_title="MISSION CONTROL • Trading Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load real balance from bot_data.json
def load_bot_data():
    try:
        with open('bot_data.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "account": {"total_usd": 349},
            "trading_state": {"starting_balance": 376.26}
        }

BOT_DATA = load_bot_data()
TOTAL_BALANCE = BOT_DATA.get('account', {}).get('total_usd', 349)
STARTING_BALANCE = BOT_DATA.get('trading_state', {}).get('starting_balance', 376.26)
CURRENT_PNL = TOTAL_BALANCE - STARTING_BALANCE

# Capital allocations
POLYMARKET_ALLOCATION = round(TOTAL_BALANCE * 0.30, 2)  # 30%
NEWS_TRADING_ALLOCATION = round(TOTAL_BALANCE * 0.40, 2)  # 40%
ALGORITHMIC_ALLOCATION = round(TOTAL_BALANCE * 0.30, 2)  # 30%

# NASA Mission Control CSS - no .stApp background override
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    /* Headers and text */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #39ff14;
        text-shadow: 0 0 10px #39ff14, 0 0 20px #39ff14, 0 0 30px #39ff14;
        font-family: 'IBM Plex Mono', monospace !important;
        letter-spacing: 2px;
        text-align: center;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    
    .mission-subtitle {
        font-size: 1.1rem;
        color: #ff6600;
        text-align: center;
        font-weight: 400;
        margin-bottom: 30px;
        letter-spacing: 1px;
        opacity: 0.9;
    }
    
    /* Metric cards - Mission Control style */
    .metric-card {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        border: 1px solid #39ff14;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #39ff14, transparent);
        animation: scan 3s linear infinite;
    }
    
    @keyframes scan {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* Placeholder cards for coming soon */
    .placeholder-card {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        border: 2px dashed #ff6600;
        border-radius: 8px;
        padding: 30px;
        margin: 15px 0;
        text-align: center;
    }
    
    .coming-soon-badge {
        background: linear-gradient(145deg, #ff6600, #cc5200);
        color: #0a0a0a;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 10px;
    }
    
    /* Status indicators */
    .profit { color: #39ff14; font-weight: bold; text-shadow: 0 0 5px #39ff14; }
    .loss { color: #ff3333; font-weight: bold; text-shadow: 0 0 5px #ff3333; }
    .warning { color: #ff6600; font-weight: bold; text-shadow: 0 0 5px #ff6600; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        border: 1px solid #39ff14;
        color: #39ff14 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 5px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #39ff14, #2dd60f) !important;
        color: #0a0a0a !important;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.6);
    }
    
    /* Terminal-style background */
    .terminal-bg {
        background: #0a0a0a;
        border: 1px solid #39ff14;
        border-radius: 5px;
        padding: 20px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
        line-height: 1.4;
        position: relative;
        overflow: hidden;
    }
    
    .terminal-bg::before {
        content: "█";
        position: absolute;
        top: 20px;
        right: 25px;
        color: #39ff14;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    /* Metrics override */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d) !important;
        border: 1px solid #39ff14 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.2) !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #ff6600 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.8rem !important;
        letter-spacing: 1px !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #39ff14 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        text-shadow: 0 0 5px #39ff14 !important;
    }
    
    /* Alert styles */
    .alert-success {
        background: linear-gradient(145deg, #1a4d1a, #0d330d);
        border: 1px solid #39ff14;
        color: #39ff14;
        padding: 15px;
        border-radius: 5px;
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
    
    .alert-warning {
        background: linear-gradient(145deg, #4d3d1a, #33280d);
        border: 1px solid #ff6600;
        color: #ff6600;
        padding: 15px;
        border-radius: 5px;
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
    
    .alert-danger {
        background: linear-gradient(145deg, #4d1a1a, #330d0d);
        border: 1px solid #ff3333;
        color: #ff3333;
        padding: 15px;
        border-radius: 5px;
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
    
    /* Footer styling */
    .footer {
        color: #ff6600;
        text-align: center;
        font-size: 0.8rem;
        margin-top: 50px;
        opacity: 0.7;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Header with Mission Control styling
st.markdown('<p class="main-header">🚀 MISSION CONTROL TRADING DASHBOARD</p>', unsafe_allow_html=True)
st.markdown(f'<p class="mission-subtitle">$1K CRYPTO MISSION • LAST UPDATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} EST</p>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 MISSION CONTROL", "📊 POLYMARKET", "📰 NEWS TRADING", "🔬 BACKTESTING"])

# ============================================
# TAB 1: MISSION CONTROL (Home)
# ============================================
with tab1:
    # Row 1: Primary Mission Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 TOTAL BALANCE",
            f"${TOTAL_BALANCE:,.2f}",
            f"FROM ${STARTING_BALANCE:,.2f}"
        )
    
    with col2:
        pnl_delta = "normal" if CURRENT_PNL >= 0 else "inverse"
        pnl_status = "🟢 PROFIT" if CURRENT_PNL >= 0 else "🔴 LOSS"
        st.metric(
            "📈 CURRENT P&L",
            f"${CURRENT_PNL:+.2f}",
            f"{(CURRENT_PNL/STARTING_BALANCE*100):+.2f}%",
            delta_color=pnl_delta
        )
    
    with col3:
        # Expected daily based on best backtest strategy (RSI+Volume: ~5.15% monthly)
        expected_daily = TOTAL_BALANCE * 0.0017  # ~0.17% daily
        st.metric(
            "📊 EXPECTED DAILY",
            f"${expected_daily:+.2f}",
            "BASED ON BACKTEST"
        )
    
    with col4:
        expected_monthly = TOTAL_BALANCE * 0.0515  # ~5.15% monthly from best strategy
        st.metric(
            "📅 EXPECTED MONTHLY",
            f"${expected_monthly:+.2f}",
            "+5.15% TARGET"
        )
    
    st.divider()
    
    # Row 1.5: OPEN POSITIONS - Live position tracker with unrealized P&L
    st.subheader("📍 OPEN POSITIONS")
    
    # Get positions from trading_state
    positions = BOT_DATA.get('trading_state', {}).get('positions', {})
    markets_data = BOT_DATA.get('markets', [])
    
    # Create market price lookup
    market_prices = {}
    for m in markets_data:
        if m.get('price'):
            market_prices[m['symbol']] = m['price']
    
    if positions:
        # Calculate total unrealized P&L
        total_unrealized_pnl = 0
        total_position_value = 0
        position_cards = []
        
        for symbol, pos in positions.items():
            entry_price = pos.get('entry', 0)
            amount = pos.get('amount', 0)
            stop_price = pos.get('stop', 0)
            target_price = pos.get('target', 0)
            entry_time_str = pos.get('time', '')
            reason = pos.get('reason', 'N/A')
            
            # Get current price from markets
            current_price = market_prices.get(symbol, entry_price)
            
            # Calculate unrealized P&L
            if entry_price > 0:
                unrealized_pnl = (current_price - entry_price) * amount
                unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                unrealized_pnl = 0
                unrealized_pnl_pct = 0
            
            # Position value
            position_value = current_price * amount
            total_position_value += position_value
            total_unrealized_pnl += unrealized_pnl
            
            # Distance to stop and target
            if entry_price > 0 and stop_price > 0:
                dist_to_stop = ((current_price - stop_price) / current_price) * 100
            else:
                dist_to_stop = 0
            
            if entry_price > 0 and target_price > 0:
                dist_to_target = ((target_price - current_price) / current_price) * 100
            else:
                dist_to_target = 0
            
            # Progress bar: where is price between stop and target?
            # 0% = at stop, 100% = at target
            if target_price > stop_price:
                price_range = target_price - stop_price
                price_progress = ((current_price - stop_price) / price_range) * 100
                price_progress = max(0, min(100, price_progress))  # Clamp 0-100
            else:
                price_progress = 50
            
            # Time in position
            try:
                entry_dt = datetime.fromisoformat(entry_time_str.replace('Z', ''))
                time_in_position = datetime.now() - entry_dt
                hours = time_in_position.total_seconds() / 3600
                if hours < 1:
                    time_str = f"{int(time_in_position.total_seconds() / 60)}m"
                elif hours < 24:
                    time_str = f"{hours:.1f}h"
                else:
                    time_str = f"{hours/24:.1f}d"
            except:
                time_str = "N/A"
            
            # Color coding
            pnl_color = "#39ff14" if unrealized_pnl >= 0 else "#ff3333"
            border_color = "#39ff14" if unrealized_pnl >= 0 else "#ff3333"
            
            # Progress bar color: green zone (>66%) yellow (33-66%) red (<33%)
            if price_progress >= 66:
                progress_color = "#39ff14"
            elif price_progress >= 33:
                progress_color = "#ff6600"
            else:
                progress_color = "#ff3333"
            
            # Format prices based on magnitude
            def fmt_price(p):
                if p < 0.01:
                    return f"${p:.6f}"
                elif p < 1:
                    return f"${p:.4f}"
                elif p < 100:
                    return f"${p:.3f}"
                else:
                    return f"${p:,.2f}"
            
            position_cards.append({
                'symbol': symbol,
                'entry_price': entry_price,
                'current_price': current_price,
                'amount': amount,
                'position_value': position_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'stop_price': stop_price,
                'target_price': target_price,
                'dist_to_stop': dist_to_stop,
                'dist_to_target': dist_to_target,
                'price_progress': price_progress,
                'time_str': time_str,
                'reason': reason,
                'pnl_color': pnl_color,
                'border_color': border_color,
                'progress_color': progress_color,
                'fmt_price': fmt_price
            })
        
        # Total Unrealized P&L Summary
        total_pnl_color = "#39ff14" if total_unrealized_pnl >= 0 else "#ff3333"
        total_pnl_pct = (total_unrealized_pnl / total_position_value * 100) if total_position_value > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card" style="border-color: {total_pnl_color}; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="color: #ff6600; font-size: 0.9rem; text-transform: uppercase;">TOTAL UNREALIZED P&L</span>
                <p style="color: {total_pnl_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {total_pnl_color};">
                    ${total_unrealized_pnl:+.2f} ({total_pnl_pct:+.2f}%)
                </p>
            </div>
            <div style="text-align: right;">
                <span style="color: #888; font-size: 0.9rem;">POSITIONS VALUE</span>
                <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">${total_position_value:.2f}</p>
            </div>
            <div style="text-align: right;">
                <span style="color: #888; font-size: 0.9rem;">OPEN POSITIONS</span>
                <p style="color: #ff6600; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{len(positions)}</p>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Position cards - 3 columns
        cols = st.columns(min(3, len(position_cards)))
        
        for idx, pos in enumerate(position_cards):
            col_idx = idx % 3
            with cols[col_idx]:
                fmt = pos['fmt_price']
                st.markdown(f"""
                <div class="metric-card" style="border-color: {pos['border_color']}; padding: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="color: #ff6600; margin: 0; font-size: 1.1rem;">{pos['symbol'].replace('/USDT', '')}</h4>
                        <span style="color: #888; font-size: 0.8rem;">⏱ {pos['time_str']}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #888;">Entry:</span>
                        <span style="color: #aaa;">{fmt(pos['entry_price'])}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #888;">Current:</span>
                        <span style="color: {pos['pnl_color']}; font-weight: bold;">{fmt(pos['current_price'])}</span>
                    </div>
                    
                    <hr style="border-color: #333; margin: 10px 0;">
                    
                    <div style="text-align: center; margin-bottom: 10px;">
                        <span style="color: #888; font-size: 0.8rem;">UNREALIZED P&L</span>
                        <p style="color: {pos['pnl_color']}; font-size: 1.4rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 5px {pos['pnl_color']};">
                            ${pos['unrealized_pnl']:+.4f}
                        </p>
                        <span style="color: {pos['pnl_color']}; font-size: 1rem;">({pos['unrealized_pnl_pct']:+.2f}%)</span>
                    </div>
                    
                    <hr style="border-color: #333; margin: 10px 0;">
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #888; font-size: 0.8rem;">Size:</span>
                        <span style="color: #aaa; font-size: 0.8rem;">{pos['amount']:.6f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="color: #888; font-size: 0.8rem;">Value:</span>
                        <span style="color: #39ff14; font-size: 0.8rem;">${pos['position_value']:.2f}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #ff3333; font-size: 0.8rem;">🛑 Stop: {fmt(pos['stop_price'])}</span>
                        <span style="color: #ff3333; font-size: 0.8rem;">({pos['dist_to_stop']:.1f}% away)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span style="color: #39ff14; font-size: 0.8rem;">🎯 Target: {fmt(pos['target_price'])}</span>
                        <span style="color: #39ff14; font-size: 0.8rem;">({pos['dist_to_target']:.1f}% away)</span>
                    </div>
                    
                    <!-- Progress Bar: Stop to Target -->
                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span style="color: #ff3333; font-size: 0.7rem;">STOP</span>
                            <span style="color: #888; font-size: 0.7rem;">{pos['price_progress']:.0f}%</span>
                            <span style="color: #39ff14; font-size: 0.7rem;">TARGET</span>
                        </div>
                        <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 4px; height: 12px; position: relative; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #ff3333, #ff6600, #39ff14); width: 100%; height: 100%; opacity: 0.3;"></div>
                            <div style="position: absolute; left: {pos['price_progress']}%; top: 0; width: 3px; height: 100%; background: {pos['progress_color']}; box-shadow: 0 0 5px {pos['progress_color']};"></div>
                        </div>
                    </div>
                    
                    <p style="color: #555; font-size: 0.7rem; margin-top: 10px; font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{pos['reason']}">{pos['reason'][:40]}...</p>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        # No open positions
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; text-align: center; padding: 30px;">
            <h4 style="color: #ff6600;">📭 NO OPEN POSITIONS</h4>
            <p style="color: #888; margin-top: 10px;">All capital is currently idle. Positions will appear here when trades are opened.</p>
            <p style="color: #555; font-size: 0.8rem; margin-top: 15px;">Bot is scanning for entry signals...</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 2: P&L PROJECTIONS - REAL MATH FROM TRADE HISTORY
    st.subheader("📊 P&L PROJECTIONS (Calculated from Actual Trades)")
    
    # Calculate real metrics from trade history
    trades = BOT_DATA.get('recent_trades', [])
    total_trades = len(trades)
    
    if total_trades >= 10:
        # Calculate real metrics
        winning_trades_list = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades_list = [t for t in trades if t.get('pnl', 0) <= 0]
        
        win_count = len(winning_trades_list)
        loss_count = len(losing_trades_list)
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t.get('pnl', 0) for t in winning_trades_list) / win_count if win_count > 0 else 0
        avg_loss = abs(sum(t.get('pnl', 0) for t in losing_trades_list) / loss_count) if loss_count > 0 else 0
        
        # Calculate trade frequency (trades per day)
        if total_trades >= 2:
            first_trade_time = datetime.fromisoformat(trades[0].get('entry_time', '').replace('Z', ''))
            last_trade_time = datetime.fromisoformat(trades[-1].get('exit_time', '').replace('Z', ''))
            days_span = max((last_trade_time - first_trade_time).days, 1)
            avg_daily_trades = total_trades / days_span
        else:
            avg_daily_trades = 1
        
        # PROJECTION FORMULA:
        # Daily = (avg_daily_trades × win_rate × avg_win) - (avg_daily_trades × (1-win_rate) × avg_loss)
        daily_expected_wins = avg_daily_trades * win_rate * avg_win
        daily_expected_losses = avg_daily_trades * (1 - win_rate) * avg_loss
        daily_projection = daily_expected_wins - daily_expected_losses
        weekly_projection = daily_projection * 7
        monthly_projection = daily_projection * 30
        
        daily_pct = (daily_projection / TOTAL_BALANCE * 100) if TOTAL_BALANCE > 0 else 0
        weekly_pct = (weekly_projection / TOTAL_BALANCE * 100) if TOTAL_BALANCE > 0 else 0
        monthly_pct = (monthly_projection / TOTAL_BALANCE * 100) if TOTAL_BALANCE > 0 else 0
        
        # Color based on positive/negative
        daily_color = "#39ff14" if daily_projection >= 0 else "#ff3333"
        weekly_color = "#39ff14" if weekly_projection >= 0 else "#ff3333"
        monthly_color = "#39ff14" if monthly_projection >= 0 else "#ff3333"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">📆 DAILY PROJECTION</h4>
            <p style="color: {daily_color}; font-size: 1.5rem; font-weight: bold;">{daily_projection:+.2f}</p>
            <p style="color: #aaa; font-size: 0.9rem;">{daily_pct:+.2f}% of balance</p>
            <hr style="border-color: #333;">
            <p style="color: #888; font-size: 0.8rem;">Avg {avg_daily_trades:.1f} trades/day<br>× {win_rate*100:.1f}% win rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">📅 WEEKLY PROJECTION</h4>
            <p style="color: {weekly_color}; font-size: 1.5rem; font-weight: bold;">{weekly_projection:+.2f}</p>
            <p style="color: #aaa; font-size: 0.9rem;">{weekly_pct:+.2f}% ({avg_daily_trades*7:.0f} trades)</p>
            <hr style="border-color: #333;">
            <p style="color: #888; font-size: 0.8rem;">Avg win: ${avg_win:.2f}<br>Avg loss: ${avg_loss:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">📆 MONTHLY PROJECTION</h4>
            <p style="color: {monthly_color}; font-size: 1.5rem; font-weight: bold;">{monthly_projection:+.2f}</p>
            <p style="color: #aaa; font-size: 0.9rem;">{monthly_pct:+.2f}% ({avg_daily_trades*30:.0f} trades)</p>
            <hr style="border-color: #333;">
            <p style="color: #888; font-size: 0.8rem;">Sample: {total_trades} trades<br>Confidence: Moderate</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show the math
        st.markdown(f"""
        <div class="terminal-bg" style="margin-top: 15px;">
        <h4 style="color: #ff6600;">📐 PROJECTION MATH (TRANSPARENCY)</h4>
        <p style="color: #39ff14; font-family: monospace;">
        Daily = (trades/day × win_rate × avg_win) - (trades/day × loss_rate × avg_loss)<br>
        Daily = ({avg_daily_trades:.2f} × {win_rate:.2f} × ${avg_win:.2f}) - ({avg_daily_trades:.2f} × {1-win_rate:.2f} × ${avg_loss:.2f})<br>
        Daily = ${daily_expected_wins:.2f} - ${daily_expected_losses:.2f} = <strong>${daily_projection:.2f}</strong>
        </p>
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">
        ⚠️ Based on {total_trades} historical trades. Past performance ≠ future results.
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # INSUFFICIENT DATA - Less than 10 trades
        st.markdown(f"""
        <div class="metric-card" style="border-color: #ff6600;">
        <h4 style="color: #ff6600;">⚠️ INSUFFICIENT DATA FOR PROJECTIONS</h4>
        <p style="color: #aaa; font-size: 1.1rem;">
            Need at least <strong>10 trades</strong> for reliable projections.<br>
            Current sample: <strong style="color: #ff6600;">{total_trades} trades</strong>
        </p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">
            📊 <strong>Current Stats (preliminary):</strong><br>
        </p>
        """, unsafe_allow_html=True)
        
        # Show preliminary stats anyway
        if total_trades > 0:
            winning_trades_list = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades_list = [t for t in trades if t.get('pnl', 0) <= 0]
            win_rate = len(winning_trades_list) / total_trades * 100
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            avg_pnl = total_pnl / total_trades
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 WIN RATE", f"{win_rate:.1f}%", f"{len(winning_trades_list)}/{total_trades} trades")
            with col2:
                pnl_color = "normal" if total_pnl >= 0 else "inverse"
                st.metric("💰 TOTAL P&L", f"${total_pnl:+.2f}", f"Avg: ${avg_pnl:+.2f}/trade", delta_color=pnl_color)
            with col3:
                st.metric("📊 TRADES NEEDED", f"{10 - total_trades} more", "For projections")
        
        st.markdown("""
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">
        🔄 Projections will auto-calculate once 10+ trades are recorded.
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 2.5: TRADE HISTORY TABLE
    st.subheader("📜 TRADE HISTORY")
    
    if total_trades > 0:
        # Build trade history data for table
        trade_history = []
        for t in reversed(trades):  # Most recent first
            # Parse entry time for date
            entry_time = t.get('entry_time', '')
            try:
                date_str = datetime.fromisoformat(entry_time.replace('Z', '')).strftime('%Y-%m-%d %H:%M')
            except:
                date_str = entry_time[:16] if entry_time else 'N/A'
            
            # Calculate P&L %
            pnl = t.get('pnl', 0)
            entry_price = t.get('entry', 0)
            exit_price = t.get('exit', 0)
            
            # Use provided pnl_pct or calculate it
            if 'pnl_pct' in t:
                pnl_pct = t['pnl_pct']
            elif entry_price > 0:
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = 0
            
            # Format reason
            reason = t.get('reason', 'N/A').replace('_', ' ').upper()
            
            trade_history.append({
                'Date': date_str,
                'Symbol': t.get('symbol', 'N/A'),
                'Entry': f"${entry_price:,.4f}" if entry_price < 1 else f"${entry_price:,.2f}",
                'Exit': f"${exit_price:,.4f}" if exit_price < 1 else f"${exit_price:,.2f}",
                'P&L': pnl,
                'P&L %': pnl_pct,
                'Reason': reason
            })
        
        trade_df = pd.DataFrame(trade_history)
        
        # Style the dataframe
        def style_pnl(val):
            if isinstance(val, (int, float)):
                color = '#39ff14' if val >= 0 else '#ff3333'
                return f'color: {color}; font-weight: bold;'
            return ''
        
        def format_pnl(val):
            return f"${val:+.2f}"
        
        def format_pnl_pct(val):
            return f"{val:+.2f}%"
        
        # Create styled dataframe
        styled_df = trade_df.style.applymap(
            style_pnl, subset=['P&L', 'P&L %']
        ).format({
            'P&L': format_pnl,
            'P&L %': format_pnl_pct
        })
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=min(400, 60 + len(trade_history) * 35)
        )
        
        # Summary row
        total_pnl_sum = sum(t['P&L'] for t in trade_history)
        pnl_color = "#39ff14" if total_pnl_sum >= 0 else "#ff3333"
        st.markdown(f"""
        <div style="text-align: right; padding: 10px; color: #888;">
            <strong>Total P&L:</strong> <span style="color: {pnl_color}; font-weight: bold;">${total_pnl_sum:+.2f}</span> 
            | <strong>Trades Shown:</strong> {len(trade_history)}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; text-align: center;">
        <h4 style="color: #ff6600;">📭 NO TRADES YET</h4>
        <p style="color: #888;">Trade history will appear here once trades are executed.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 3: Trade Statistics
    st.subheader("📈 TRADE STATISTICS")
    
    # Calculate real trade stats from bot_data
    trades = BOT_DATA.get('recent_trades', BOT_DATA.get('trades', []))
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
    
    total_profit = sum(t.get('pnl', 0) for t in winning_trades)
    total_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
    avg_win = total_profit / len(winning_trades) if winning_trades else 0
    avg_loss = total_loss / len(losing_trades) if losing_trades else 0
    largest_win = max((t.get('pnl', 0) for t in winning_trades), default=0)
    largest_loss = abs(min((t.get('pnl', 0) for t in losing_trades), default=0))
    
    col1, col2 = st.columns(2)
    
    with col1:
        win_note = f"Last: {winning_trades[-1].get('symbol', '?')}" if winning_trades else "📊 No winning trades yet"
        st.markdown(f"""
        <div class="metric-card" style="border-color: #39ff14;">
        <h4 style="color: #39ff14;">✅ WINNING TRADES</h4>
        <p style="color: #39ff14; font-size: 2rem; font-weight: bold;">{len(winning_trades)}</p>
        <hr style="border-color: #333;">
        <p style="color: #aaa;">Total Profit: ${total_profit:.2f}</p>
        <p style="color: #aaa;">Avg Win: ${avg_win:.2f}</p>
        <p style="color: #aaa;">Largest Win: ${largest_win:.2f}</p>
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">{win_note}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        loss_note = f"Last: {losing_trades[-1].get('symbol', '?')}" if losing_trades else "📊 No losing trades yet"
        st.markdown(f"""
        <div class="metric-card" style="border-color: #ff3333;">
        <h4 style="color: #ff3333;">❌ LOSING TRADES</h4>
        <p style="color: #ff3333; font-size: 2rem; font-weight: bold;">{len(losing_trades)}</p>
        <hr style="border-color: #333;">
        <p style="color: #aaa;">Total Loss: ${total_loss:.2f}</p>
        <p style="color: #aaa;">Avg Loss: ${avg_loss:.2f}</p>
        <p style="color: #aaa;">Largest Loss: ${largest_loss:.2f}</p>
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">{loss_note}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 4: PERFORMANCE METRICS
    st.subheader("📊 PERFORMANCE METRICS")
    
    if total_trades > 0:
        # Calculate all metrics
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(wins) / total_trades * 100
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t['pnl'] for t in losses) / len(losses)) if losses else 0
        
        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = abs(sum(t['pnl'] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        best_trade = max(t['pnl'] for t in trades)
        worst_trade = min(t['pnl'] for t in trades)
        
        # Calculate streak (most recent trades)
        streak = 0
        streak_type = None
        for t in reversed(trades):
            is_win = t.get('pnl', 0) > 0
            if streak_type is None:
                streak_type = is_win
                streak = 1
            elif is_win == streak_type:
                streak += 1
            else:
                break
        streak_label = f"{streak}W" if streak_type else f"{streak}L"
        streak_color = "#39ff14" if streak_type else "#ff3333"
        
        # Metric colors
        wr_color = "#39ff14" if win_rate >= 50 else "#ff6600" if win_rate >= 30 else "#ff3333"
        pf_color = "#39ff14" if profit_factor >= 1.5 else "#ff6600" if profit_factor >= 1 else "#ff3333"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">📈 WIN RATE</h4>
            <p style="color: {wr_color}; font-size: 2rem; font-weight: bold;">{win_rate:.1f}%</p>
            <p style="color: #888;">{len(wins)}W / {len(losses)}L</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">🏆 BEST TRADE</h4>
            <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold;">${best_trade:+.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">💰 AVG WIN / LOSS</h4>
            <p style="color: #39ff14; font-size: 1.3rem;">${avg_win:.2f} <span style="color: #888;">win</span></p>
            <p style="color: #ff3333; font-size: 1.3rem;">${avg_loss:.2f} <span style="color: #888;">loss</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">💀 WORST TRADE</h4>
            <p style="color: #ff3333; font-size: 1.5rem; font-weight: bold;">${worst_trade:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">⚖️ PROFIT FACTOR</h4>
            <p style="color: {pf_color}; font-size: 2rem; font-weight: bold;">{profit_factor:.2f}</p>
            <p style="color: #888;">{total_trades} trades</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
            <h4 style="color: #ff6600;">🔥 STREAK</h4>
            <p style="color: {streak_color}; font-size: 2rem; font-weight: bold;">{streak_label}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; text-align: center;">
        <h4 style="color: #ff6600;">📭 NO TRADE DATA</h4>
        <p style="color: #888;">Performance metrics require trade history.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 5: Strategy Summary
    st.subheader("🔬 BACKTESTING STRATEGY SUMMARY")
    
    st.markdown("""
    <div class="terminal-bg">
    <h4 style="color: #ff6600;">TOP 3 PERFORMING STRATEGIES (5m candles, 1 week test period)</h4>
    <p style="color: #888; font-size: 0.8rem; margin-bottom: 15px;">⚠️ Static data - not auto-updating yet</p>
    
    <table style="width: 100%; color: #39ff14; font-family: 'IBM Plex Mono', monospace;">
    <tr style="border-bottom: 1px solid #333;">
        <th style="text-align: left; padding: 10px; color: #ff6600;">RANK</th>
        <th style="text-align: left; padding: 10px; color: #ff6600;">STRATEGY</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">RETURN</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">SHARPE</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">WIN RATE</th>
    </tr>
    <tr>
        <td style="padding: 10px;">🥇</td>
        <td style="padding: 10px;">RSI + Volume Confirmation</td>
        <td style="padding: 10px; text-align: right; color: #39ff14;">+5.15%</td>
        <td style="padding: 10px; text-align: right;">14.64</td>
        <td style="padding: 10px; text-align: right;">40.1%</td>
    </tr>
    <tr>
        <td style="padding: 10px;">🥈</td>
        <td style="padding: 10px;">Multi-Factor Composite</td>
        <td style="padding: 10px; text-align: right; color: #39ff14;">+2.15%</td>
        <td style="padding: 10px; text-align: right;">5.66</td>
        <td style="padding: 10px; text-align: right;">33.3%</td>
    </tr>
    <tr>
        <td style="padding: 10px;">🥉</td>
        <td style="padding: 10px;">RSI Mean Reversion</td>
        <td style="padding: 10px; text-align: right; color: #39ff14;">+2.12%</td>
        <td style="padding: 10px; text-align: right;">6.91</td>
        <td style="padding: 10px; text-align: right;">31.6%</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Capital Allocation Overview
    st.subheader("💰 CAPITAL ALLOCATION")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📰 NEWS TRADING", f"${NEWS_TRADING_ALLOCATION:,.2f}", "40% ALLOCATION")
    
    with col2:
        st.metric("📊 POLYMARKET", f"${POLYMARKET_ALLOCATION:,.2f}", "30% ALLOCATION")
    
    with col3:
        st.metric("🤖 ALGORITHMIC", f"${ALGORITHMIC_ALLOCATION:,.2f}", "30% ALLOCATION")

# ============================================
# TAB 2: POLYMARKET
# ============================================
with tab2:
    st.subheader("📊 POLYMARKET TRADING MODULE")
    
    # Allocated Capital Display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 ALLOCATED CAPITAL", f"${POLYMARKET_ALLOCATION:,.2f}", "30% OF PORTFOLIO")
    
    with col2:
        st.metric("📈 DEPLOYED", "$0.00", "0% UTILIZED")
    
    with col3:
        st.metric("💵 AVAILABLE", f"${POLYMARKET_ALLOCATION:,.2f}", "READY TO DEPLOY")
    
    st.divider()
    
    # Coming Soon Section
    st.markdown("""
    <div class="placeholder-card">
        <span class="coming-soon-badge">🚧 COMING SOON</span>
        <h3 style="color: #39ff14; margin: 15px 0;">POLYMARKET API INTEGRATION</h3>
        <p style="color: #aaa; max-width: 600px; margin: 0 auto;">
            Prediction market trading integration pending. This module will provide:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">📊 ACTIVE MARKETS</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Live market listings</p>
        <p style="color: #888; font-size: 0.9rem;">• Real-time odds tracking</p>
        <p style="color: #888; font-size: 0.9rem;">• Market sentiment analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">📈 OPEN POSITIONS</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Position tracking</p>
        <p style="color: #888; font-size: 0.9rem;">• Entry/exit prices</p>
        <p style="color: #888; font-size: 0.9rem;">• Unrealized P&L</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">💰 P&L TRACKING</h4>
        <p style="color: #666; font-size: 1.5rem;">$0.00</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Realized gains/losses</p>
        <p style="color: #888; font-size: 0.9rem;">• Win rate statistics</p>
        <p style="color: #888; font-size: 0.9rem;">• ROI by market type</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">🎯 MARKET ALERTS</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Price movement alerts</p>
        <p style="color: #888; font-size: 0.9rem;">• Resolution notifications</p>
        <p style="color: #888; font-size: 0.9rem;">• Opportunity detection</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-warning" style="margin-top: 20px;">
    ⏳ API INTEGRATION PENDING • Polymarket API access being configured • Check back soon for live trading features
    </div>
    """, unsafe_allow_html=True)

# ============================================
# TAB 3: NEWS TRADING
# ============================================
with tab3:
    st.subheader("📰 NEWS TRADING MODULE")
    
    # Allocated Capital Display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 ALLOCATED CAPITAL", f"${NEWS_TRADING_ALLOCATION:,.2f}", "40% OF PORTFOLIO")
    
    with col2:
        st.metric("📈 DEPLOYED", "$0.00", "0% UTILIZED")
    
    with col3:
        st.metric("💵 AVAILABLE", f"${NEWS_TRADING_ALLOCATION:,.2f}", "READY TO DEPLOY")
    
    st.divider()
    
    # Coming Soon Section
    st.markdown("""
    <div class="placeholder-card">
        <span class="coming-soon-badge">🚧 COMING SOON</span>
        <h3 style="color: #39ff14; margin: 15px 0;">NEWS TRADING API INTEGRATION</h3>
        <p style="color: #aaa; max-width: 600px; margin: 0 auto;">
            Real-time news sentiment trading integration pending. This module will provide:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">📰 NEWS SIGNALS</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Real-time news feed</p>
        <p style="color: #888; font-size: 0.9rem;">• Sentiment analysis</p>
        <p style="color: #888; font-size: 0.9rem;">• Impact scoring</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">📈 ACTIVE TRADES</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• News-triggered positions</p>
        <p style="color: #888; font-size: 0.9rem;">• Entry/exit tracking</p>
        <p style="color: #888; font-size: 0.9rem;">• Time-based exits</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">🔔 ALERT FEED</h4>
        <p style="color: #666; font-size: 1.5rem;">--</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• Breaking news alerts</p>
        <p style="color: #888; font-size: 0.9rem;">• Market-moving events</p>
        <p style="color: #888; font-size: 0.9rem;">• Telegram notifications</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card" style="border-color: #ff6600; opacity: 0.7;">
        <h4 style="color: #ff6600;">💰 NEWS P&L</h4>
        <p style="color: #666; font-size: 1.5rem;">$0.00</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.9rem;">• News trade performance</p>
        <p style="color: #888; font-size: 0.9rem;">• Win rate by news type</p>
        <p style="color: #888; font-size: 0.9rem;">• Avg reaction time</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-warning" style="margin-top: 20px;">
    ⏳ API INTEGRATION PENDING • News sentiment API being configured • Check back soon for live news trading
    </div>
    """, unsafe_allow_html=True)

# ============================================
# TAB 4: BACKTESTING STRATEGIES
# ============================================
with tab4:
    st.subheader("🔬 BACKTESTING STRATEGIES • NASA ANALYSIS CENTER")
    
    # Backtest Results Summary
    st.markdown("""
    <div class="terminal-bg">
    <h4 style="color: #ff6600; margin-bottom: 20px;">🚀 MISSION: ALTERNATIVE DATA STRATEGY TESTING</h4>
    <p><strong>TEST PERIOD:</strong> 5-minute candles over 1 week</p>
    <p><strong>ASSETS:</strong> BTC, ETH, SOL</p>
    <p><strong>ACCOUNT SIZE:</strong> $350</p>
    <p><strong>STRATEGIES TESTED:</strong> 7</p>
    <p style="color: #ff6600; margin-top: 10px;">⚠️ STATIC DATA - These results are from historical backtests and are not auto-updating yet</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🏆 STRATEGY PERFORMANCE MATRIX")
    
    # Strategy Results Table
    strategy_data = [
        {"RANK": "🥇 1", "STRATEGY": "RSI + Volume Confirmation", "AVG_RETURN": "+5.15%", "SHARPE": 14.64, "MAX_DD": "1.62%", "WIN_RATE": "40.1%", "TRADES": 32, "STATUS": "🟢 OPTIMAL"},
        {"RANK": "🥈 2", "STRATEGY": "Multi-Factor Composite", "AVG_RETURN": "+2.15%", "SHARPE": 5.66, "MAX_DD": "1.26%", "WIN_RATE": "33.3%", "TRADES": 4, "STATUS": "🟢 VIABLE"},
        {"RANK": "🥉 3", "STRATEGY": "RSI Mean Reversion", "AVG_RETURN": "+2.12%", "SHARPE": 6.91, "MAX_DD": "1.76%", "WIN_RATE": "31.6%", "TRADES": 68, "STATUS": "🟡 REVIEW"},
        {"RANK": "4", "STRATEGY": "Bollinger Band Squeeze", "AVG_RETURN": "-0.15%", "SHARPE": -5.06, "MAX_DD": "0.21%", "WIN_RATE": "7.5%", "TRADES": 22, "STATUS": "🔴 AVOID"},
        {"RANK": "5", "STRATEGY": "ATR Volatility Breakout", "AVG_RETURN": "-0.50%", "SHARPE": -2.59, "MAX_DD": "1.48%", "WIN_RATE": "20.1%", "TRADES": 50, "STATUS": "🔴 AVOID"},
        {"RANK": "6", "STRATEGY": "EMA Crossover + Trend", "AVG_RETURN": "-5.69%", "SHARPE": -11.54, "MAX_DD": "7.50%", "WIN_RATE": "10.2%", "TRADES": 214, "STATUS": "🚨 CRITICAL"},
        {"RANK": "7", "STRATEGY": "MACD Momentum", "AVG_RETURN": "-7.21%", "SHARPE": -15.85, "MAX_DD": "9.49%", "WIN_RATE": "10.2%", "TRADES": 310, "STATUS": "🚨 ABORT"},
    ]
    
    strategy_df = pd.DataFrame(strategy_data)
    st.dataframe(
        strategy_df,
        use_container_width=True,
        hide_index=True,
        height=350
    )
    
    # Winning Strategies Details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 TOP PERFORMER: RSI + VOLUME CONFIRMATION")
        st.markdown("""
        <div class="terminal-bg">
        <h4 style="color: #39ff14;">STRATEGY PARAMETERS:</h4>
        <p><strong>BUY:</strong> RSI < 30 AND Volume > 1.5x 20-period avg</p>
        <p><strong>SELL:</strong> RSI > 70 AND Volume > 1.5x 20-period avg</p>
        
        <h4 style="color: #ff6600; margin-top: 20px;">ASSET PERFORMANCE:</h4>
        <p><strong>BTC:</strong> +1.98% (-2.01% vs Buy&Hold)</p>
        <p><strong>ETH:</strong> +6.52% (+0.69% vs Buy&Hold) ⭐</p>
        <p><strong>SOL:</strong> +6.94% (-0.64% vs Buy&Hold) ⭐</p>
        
        <h4 style="color: #ff6600; margin-top: 20px;">MISSION CRITICAL:</h4>
        <p>• Best overall performance: 14.64 Sharpe ratio</p>
        <p>• Volume filter prevents false RSI signals</p>
        <p>• ~10 trades/month = optimal for $350 account</p>
        <p>• ETH and SOL show exceptional results</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🥈 RUNNER-UP: MULTI-FACTOR COMPOSITE")
        st.markdown("""
        <div class="terminal-bg">
        <h4 style="color: #39ff14;">STRATEGY PARAMETERS:</h4>
        <p><strong>SYSTEM:</strong> Score-based (RSI + Volume + Trend)</p>
        <p><strong>BUY:</strong> Score >= 2</p>
        <p><strong>SELL:</strong> Score <= -2</p>
        
        <h4 style="color: #ff6600; margin-top: 20px;">ASSET PERFORMANCE:</h4>
        <p><strong>BTC:</strong> +2.13% (50% win rate) ⭐</p>
        <p><strong>ETH:</strong> +4.33% (50% win rate) ⭐</p>
        <p><strong>SOL:</strong> 0.00% (No signals generated)</p>
        
        <h4 style="color: #ff6600; margin-top: 20px;">MISSION CRITICAL:</h4>
        <p>• Highest win rate: 50% on BTC & ETH</p>
        <p>• Ultra-selective: Only 4 trades total</p>
        <p>• Lowest drawdown: 1.26% max</p>
        <p>• Perfect for small accounts (minimal fees)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Asset-Specific Recommendations
    st.markdown("### 🎯 ASSET-SPECIFIC MISSION PROTOCOLS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">🟠 BTC PROTOCOL</h4>
        <p><strong>PRIMARY:</strong> Multi-Factor Composite</p>
        <p><strong>RETURN:</strong> +2.13%</p>
        <p><strong>WIN RATE:</strong> 50%</p>
        <p><strong>CHARACTERISTICS:</strong> Mean-reverting, needs confirmation</p>
        <p><strong>OPTIMAL:</strong> Fewer, high-conviction trades</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">🔵 ETH PROTOCOL</h4>
        <p><strong>PRIMARY:</strong> RSI + Volume</p>
        <p><strong>RETURN:</strong> +6.52%</p>
        <p><strong>WIN RATE:</strong> 42.9%</p>
        <p><strong>CHARACTERISTICS:</strong> Excellent mean reversion response</p>
        <p><strong>OPTIMAL:</strong> RSI 30/70 levels work perfectly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">🟣 SOL PROTOCOL</h4>
        <p><strong>PRIMARY:</strong> RSI + Volume</p>
        <p><strong>RETURN:</strong> +6.94%</p>
        <p><strong>WIN RATE:</strong> 37.5%</p>
        <p><strong>CHARACTERISTICS:</strong> High volatility, volume critical</p>
        <p><strong>OPTIMAL:</strong> Volume spikes = real moves</p>
        </div>
        """, unsafe_allow_html=True)
    
    # What Works vs What Doesn't
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ MISSION APPROVED PROTOCOLS")
        st.markdown("""
        <div class="alert-success">
        <p><strong>MEAN REVERSION + VOLUME:</strong> Catches true market extremes</p>
        <p><strong>MULTI-FACTOR CONFIRMATION:</strong> Reduces false signals</p>
        <p><strong>LOW TRADE FREQUENCY:</strong> Minimizes fees, higher quality</p>
        <p><strong>RSI EXTREMES (30/70):</strong> Market-tested reversal levels</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ❌ MISSION ABORT PROTOCOLS")
        st.markdown("""
        <div class="alert-danger">
        <p><strong>PURE MOMENTUM (MACD, EMA):</strong> Whipsaws in current market</p>
        <p><strong>HIGH TRADE FREQUENCY:</strong> Fees destroy $350 account</p>
        <p><strong>BREAKOUT CHASING:</strong> False breakouts common on 5m</p>
        <p><strong>SINGLE INDICATOR:</strong> Insufficient edge for mission success</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown(f'<div class="footer">🚀 BUILT FOR THE $1K CRYPTO TRADING MISSION | NASA MISSION CONTROL AESTHETIC | v3.0 | Balance: ${TOTAL_BALANCE:.2f}</div>', unsafe_allow_html=True)

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
    
    # Row 2: P&L Projections
    st.subheader("📊 P&L PROJECTIONS (Based on Backtested Strategies)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">📆 DAILY PROJECTION</h4>
        <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold;">+$0.59</p>
        <p style="color: #aaa; font-size: 0.9rem;">+0.17% (conservative)</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.8rem;">Based on RSI+Volume strategy<br>with 10 trades/month average</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">📅 WEEKLY PROJECTION</h4>
        <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold;">+$4.15</p>
        <p style="color: #aaa; font-size: 0.9rem;">+1.19% (2-3 trades)</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.8rem;">Assuming 40% win rate<br>with 1:3 risk/reward ratio</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4 style="color: #ff6600;">📆 MONTHLY PROJECTION</h4>
        <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold;">+$17.97</p>
        <p style="color: #aaa; font-size: 0.9rem;">+5.15% (10 trades)</p>
        <hr style="border-color: #333;">
        <p style="color: #888; font-size: 0.8rem;">Sharpe ratio: 14.64<br>Max drawdown: 1.62%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 3: Trade Statistics
    st.subheader("📈 TRADE STATISTICS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card" style="border-color: #39ff14;">
        <h4 style="color: #39ff14;">✅ WINNING TRADES</h4>
        <p style="color: #39ff14; font-size: 2rem; font-weight: bold;">0</p>
        <hr style="border-color: #333;">
        <p style="color: #aaa;">Total Profit: $0.00</p>
        <p style="color: #aaa;">Avg Win: $0.00</p>
        <p style="color: #aaa;">Largest Win: $0.00</p>
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">📊 No trades executed yet</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="border-color: #ff3333;">
        <h4 style="color: #ff3333;">❌ LOSING TRADES</h4>
        <p style="color: #ff3333; font-size: 2rem; font-weight: bold;">0</p>
        <hr style="border-color: #333;">
        <p style="color: #aaa;">Total Loss: $0.00</p>
        <p style="color: #aaa;">Avg Loss: $0.00</p>
        <p style="color: #aaa;">Largest Loss: $0.00</p>
        <p style="color: #888; font-size: 0.8rem; margin-top: 10px;">📊 No trades executed yet</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 4: Strategy Summary
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

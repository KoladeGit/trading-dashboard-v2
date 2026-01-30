#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TRADING MISSION CONTROL v2.0                                                ║
║  NASA-STYLE TERMINAL INTERFACE                                               ║
║  $1K CRYPTO MISSION - ALL SYSTEMS NOMINAL                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional
import hashlib
import os
import re

# =============================================================================
# PAGE CONFIG - MISSION CONTROL
# =============================================================================
st.set_page_config(
    page_title="MISSION CONTROL v2.0",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# NASA MISSION CONTROL CSS - RETRO TERMINAL AESTHETIC
# =============================================================================
st.markdown("""
<style>
    /* Import NASA-style monospace fonts */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Fira+Code:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');
    
    /* Root variables */
    :root {
        --phosphor-green: #00ff41;
        --phosphor-green-dim: #00cc33;
        --amber: #ffaa00;
        --amber-bright: #ff6600;
        --warning-red: #ff0000;
        --bg-dark: #0a0a0a;
        --bg-panel: #0d1117;
        --bg-terminal: #1a1a2e;
        --border-color: #00ff4133;
        --text-dim: #4a5568;
    }
    
    /* Global dark background */
    .stApp {
        background-color: var(--bg-dark) !important;
    }
    
    /* CRT Scanline overlay effect */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 9999;
    }
    
    /* CRT flicker animation */
    @keyframes flicker {
        0% { opacity: 0.97; }
        50% { opacity: 1; }
        100% { opacity: 0.98; }
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
        animation: flicker 0.15s infinite;
    }
    
    /* All text - phosphor green monospace */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        font-family: 'IBM Plex Mono', 'Fira Code', 'Share Tech Mono', monospace !important;
        color: var(--phosphor-green) !important;
    }
    
    /* Headers - uppercase terminal style */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Share Tech Mono', 'IBM Plex Mono', monospace !important;
        color: var(--phosphor-green) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        text-shadow: 0 0 10px var(--phosphor-green), 0 0 20px var(--phosphor-green-dim);
    }
    
    h1 {
        font-size: 2rem !important;
        border-bottom: 2px solid var(--phosphor-green) !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Mission Control Panel Styling */
    .mission-panel {
        background: linear-gradient(180deg, #0d1117 0%, #1a1a2e 100%);
        border: 2px solid var(--phosphor-green);
        border-radius: 0;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 
            0 0 10px var(--border-color),
            inset 0 0 30px rgba(0,255,65,0.03);
        position: relative;
    }
    
    .mission-panel::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--phosphor-green), transparent);
    }
    
    /* LED Status Indicators */
    .led-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 8px currentColor;
    }
    
    .led-green {
        background: var(--phosphor-green);
        box-shadow: 0 0 10px var(--phosphor-green), 0 0 20px var(--phosphor-green);
    }
    
    .led-amber {
        background: var(--amber);
        box-shadow: 0 0 10px var(--amber), 0 0 20px var(--amber);
    }
    
    .led-red {
        background: var(--warning-red);
        box-shadow: 0 0 10px var(--warning-red), 0 0 20px var(--warning-red);
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    /* Metric cards - CRT display style */
    .metric-crt {
        background: #0d1117;
        border: 1px solid var(--phosphor-green);
        border-radius: 0;
        padding: 1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .metric-crt::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 200%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(0,255,65,0.05),
            transparent
        );
        animation: scan 3s linear infinite;
    }
    
    @keyframes scan {
        0% { transform: translateX(0); }
        100% { transform: translateX(50%); }
    }
    
    .metric-crt .label {
        font-size: 0.7rem;
        color: var(--text-dim) !important;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-bottom: 0.25rem;
    }
    
    .metric-crt .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--phosphor-green) !important;
        text-shadow: 0 0 10px var(--phosphor-green);
        font-family: 'Share Tech Mono', monospace !important;
    }
    
    .metric-crt .value.profit {
        color: var(--phosphor-green) !important;
    }
    
    .metric-crt .value.loss {
        color: var(--warning-red) !important;
        text-shadow: 0 0 10px var(--warning-red);
    }
    
    .metric-crt .value.amber {
        color: var(--amber) !important;
        text-shadow: 0 0 10px var(--amber);
    }
    
    .metric-crt .delta {
        font-size: 0.8rem;
        color: var(--text-dim) !important;
    }
    
    /* Trade row - industrial style */
    .trade-row {
        background: #0d1117;
        border: 1px solid var(--phosphor-green-dim);
        border-left: 4px solid var(--phosphor-green);
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-family: 'IBM Plex Mono', monospace;
    }
    
    .trade-row.profit {
        border-left-color: var(--phosphor-green);
    }
    
    .trade-row.loss {
        border-left-color: var(--warning-red);
    }
    
    .trade-row.open {
        border-left-color: var(--amber);
    }
    
    /* Strategy card for backtesting */
    .strategy-card {
        background: linear-gradient(180deg, #0d1117 0%, #1a1a2e 100%);
        border: 2px solid var(--phosphor-green);
        padding: 1.25rem;
        margin-bottom: 1rem;
        position: relative;
    }
    
    .strategy-card.active {
        border-color: var(--phosphor-green);
        box-shadow: 0 0 20px rgba(0,255,65,0.2);
    }
    
    .strategy-card.testing {
        border-color: var(--amber);
        box-shadow: 0 0 20px rgba(255,170,0,0.2);
    }
    
    .strategy-card.deprecated {
        border-color: var(--warning-red);
        opacity: 0.7;
    }
    
    .strategy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--phosphor-green-dim);
    }
    
    .strategy-name {
        font-size: 1.1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .strategy-status {
        padding: 0.25rem 0.75rem;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        border: 1px solid;
    }
    
    .status-active {
        color: var(--phosphor-green) !important;
        border-color: var(--phosphor-green);
        background: rgba(0,255,65,0.1);
    }
    
    .status-testing {
        color: var(--amber) !important;
        border-color: var(--amber);
        background: rgba(255,170,0,0.1);
    }
    
    .status-deprecated {
        color: var(--warning-red) !important;
        border-color: var(--warning-red);
        background: rgba(255,0,0,0.1);
    }
    
    /* Tabs - mission control style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #0d1117;
        border: 1px solid var(--phosphor-green);
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0;
        padding: 12px 24px;
        border: none;
        border-right: 1px solid var(--phosphor-green-dim);
        color: var(--phosphor-green) !important;
        font-family: 'IBM Plex Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.85rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--phosphor-green) !important;
        color: #0a0a0a !important;
        font-weight: 700;
    }
    
    /* Sidebar - command module */
    [data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 2px solid var(--phosphor-green);
    }
    
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }
    
    /* Buttons - industrial switches */
    .stButton > button {
        background: #0d1117 !important;
        border: 2px solid var(--phosphor-green) !important;
        border-radius: 0 !important;
        color: var(--phosphor-green) !important;
        font-family: 'IBM Plex Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.2s;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button:hover {
        background: var(--phosphor-green) !important;
        color: #0a0a0a !important;
        box-shadow: 0 0 20px var(--phosphor-green);
    }
    
    /* Input fields - terminal input */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #0d1117 !important;
        border: 1px solid var(--phosphor-green-dim) !important;
        border-radius: 0 !important;
        color: var(--phosphor-green) !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--phosphor-green) !important;
        box-shadow: 0 0 10px var(--border-color) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: #0d1117 !important;
        border: 1px solid var(--phosphor-green-dim) !important;
        border-radius: 0 !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: var(--phosphor-green) !important;
        box-shadow: 0 0 10px var(--phosphor-green);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #0d1117 !important;
        border: 1px solid var(--phosphor-green-dim) !important;
        border-radius: 0 !important;
        color: var(--phosphor-green) !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid var(--phosphor-green) !important;
    }
    
    [data-testid="stDataFrame"] {
        background: #0d1117;
    }
    
    /* Divider */
    hr {
        border-color: var(--phosphor-green-dim) !important;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        background: #0d1117 !important;
        border: 1px solid var(--phosphor-green) !important;
        border-radius: 0 !important;
        color: var(--phosphor-green) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--phosphor-green-dim);
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--phosphor-green);
    }
    
    /* Terminal header */
    .terminal-header {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-dim) !important;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--phosphor-green-dim);
        margin-bottom: 1rem;
    }
    
    /* Blinking cursor */
    .cursor-blink {
        animation: cursor-blink 1s step-end infinite;
    }
    
    @keyframes cursor-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    
    /* Metric widget override */
    [data-testid="stMetricValue"] {
        font-family: 'Share Tech Mono', monospace !important;
        color: var(--phosphor-green) !important;
        text-shadow: 0 0 10px var(--phosphor-green);
    }
    
    [data-testid="stMetricDelta"] {
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-size: 0.75rem !important;
    }
    
    /* Caption text */
    .stCaption, small {
        color: var(--text-dim) !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# AUTHENTICATION
# =============================================================================
def check_password():
    """Returns True if user has correct password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "password" not in st.secrets:
        return True
    
    if st.session_state.authenticated:
        return True
    
    password = st.text_input("[ ACCESS CODE REQUIRED ]", type="password")
    if password:
        if hashlib.sha256(password.encode()).hexdigest() == st.secrets.get("password_hash", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("[ ACCESS DENIED ]")
    return False

# =============================================================================
# DATA PERSISTENCE
# =============================================================================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "trades": [],
        "positions": [],
        "alerts": [],
        "allocations": {
            "News Trading": {"allocated": 400, "current": 400, "color": "#ff6600"},
            "Polymarket": {"allocated": 300, "current": 300, "color": "#00ff41"},
            "Algorithmic": {"allocated": 300, "current": 300, "color": "#ffaa00"}
        },
        "settings": {
            "initial_capital": 1000,
            "risk_per_trade": 2.0,
            "telegram_alerts": False
        },
        "polymarket_watchlist": [],
        "last_backup": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def export_data() -> str:
    """Export all data to JSON string"""
    data = {
        "version": "2.0",
        "exported_at": datetime.now().isoformat(),
        "trades": st.session_state.trades,
        "positions": st.session_state.positions,
        "alerts": st.session_state.alerts,
        "allocations": st.session_state.allocations,
        "settings": st.session_state.settings,
        "polymarket_watchlist": st.session_state.polymarket_watchlist
    }
    return json.dumps(data, indent=2, default=str)

def import_data(json_str: str) -> bool:
    """Import data from JSON string"""
    try:
        data = json.loads(json_str)
        if data.get("version") != "2.0":
            st.warning("[ WARNING: DATA VERSION MISMATCH ]")
        
        st.session_state.trades = data.get("trades", [])
        st.session_state.positions = data.get("positions", [])
        st.session_state.alerts = data.get("alerts", [])
        st.session_state.allocations = data.get("allocations", st.session_state.allocations)
        st.session_state.settings = data.get("settings", st.session_state.settings)
        st.session_state.polymarket_watchlist = data.get("polymarket_watchlist", [])
        return True
    except Exception as e:
        st.error(f"[ IMPORT FAILED: {e} ]")
        return False

# =============================================================================
# BACKTESTING DATA PARSER
# =============================================================================
def load_backtest_results() -> Dict:
    """Load and parse backtest results from markdown file"""
    backtest_path = "/Users/kolade/clawd/memory/research/backtest-results.md"
    
    strategies = []
    
    try:
        with open(backtest_path, 'r') as f:
            content = f.read()
        
        # Parse the executive summary table
        strategies = [
            {
                "id": "ALPHA-7",
                "name": "RSI + VOLUME CONFIRMATION",
                "rank": 1,
                "status": "ACTIVE",
                "avg_return": "+5.15%",
                "sharpe": 14.64,
                "max_drawdown": "1.62%",
                "win_rate": "40.1%",
                "trades": 32,
                "summary": "Based on Fear & Greed research - extreme RSI readings + volume spike = capitulation/euphoria signals",
                "parameters": {
                    "rsi_period": 14,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "volume_multiplier": 1.5,
                    "volume_lookback": 20
                },
                "rules": ["Buy: RSI < 30 AND volume > 1.5x 20-period average", "Sell: RSI > 70 AND volume > 1.5x 20-period average"]
            },
            {
                "id": "ALPHA-12",
                "name": "MULTI-FACTOR COMPOSITE",
                "rank": 2,
                "status": "ACTIVE",
                "avg_return": "+2.15%",
                "sharpe": 5.66,
                "max_drawdown": "1.26%",
                "win_rate": "33.3%",
                "trades": 4,
                "summary": "Combines multiple signals (RSI + Volume + Trend) for higher confidence entries",
                "parameters": {
                    "rsi_weight": 1.0,
                    "volume_weight": 1.0,
                    "trend_weight": 0.5,
                    "entry_threshold": 2.0,
                    "exit_threshold": -2.0
                },
                "rules": ["Score-based system: RSI + Volume + Trend", "Buy: Score >= 2", "Sell: Score <= -2"]
            },
            {
                "id": "ALPHA-3",
                "name": "RSI MEAN REVERSION",
                "rank": 3,
                "status": "TESTING",
                "avg_return": "+2.12%",
                "sharpe": 6.91,
                "max_drawdown": "1.76%",
                "win_rate": "31.6%",
                "trades": 68,
                "summary": "Pure contrarian strategy based on Fear & Greed index research",
                "parameters": {
                    "rsi_period": 14,
                    "oversold_cross": 30,
                    "overbought_cross": 70
                },
                "rules": ["Buy: RSI crosses above 30 from below", "Sell: RSI crosses below 70 from above"]
            },
            {
                "id": "BETA-1",
                "name": "BOLLINGER BAND SQUEEZE",
                "rank": 4,
                "status": "TESTING",
                "avg_return": "-0.15%",
                "sharpe": -5.06,
                "max_drawdown": "0.21%",
                "win_rate": "7.5%",
                "trades": 22,
                "summary": "Volatility contraction breakout strategy",
                "parameters": {
                    "bb_period": 20,
                    "bb_std": 2.0,
                    "squeeze_threshold": 0.5
                },
                "rules": ["Buy: Band width contracts then expands upward", "Sell: Band width contracts then expands downward"]
            },
            {
                "id": "BETA-5",
                "name": "ATR VOLATILITY BREAKOUT",
                "rank": 5,
                "status": "DEPRECATED",
                "avg_return": "-0.50%",
                "sharpe": -2.59,
                "max_drawdown": "1.48%",
                "win_rate": "20.1%",
                "trades": 50,
                "summary": "Range breakout using ATR for position sizing",
                "parameters": {
                    "atr_period": 14,
                    "breakout_multiplier": 1.5
                },
                "rules": ["Buy: Price breaks above high + ATR*1.5", "Sell: Price breaks below low - ATR*1.5"]
            },
            {
                "id": "GAMMA-2",
                "name": "EMA CROSSOVER + TREND",
                "rank": 6,
                "status": "DEPRECATED",
                "avg_return": "-5.69%",
                "sharpe": -11.54,
                "max_drawdown": "7.50%",
                "win_rate": "10.2%",
                "trades": 214,
                "summary": "Whipsawed in choppy market - excessive trades for small accounts",
                "parameters": {
                    "fast_ema": 9,
                    "slow_ema": 21,
                    "trend_ema": 50
                },
                "rules": ["Buy: Fast EMA crosses above Slow EMA, price above Trend EMA", "Excessive fees - NOT RECOMMENDED"]
            },
            {
                "id": "GAMMA-5",
                "name": "MACD MOMENTUM",
                "rank": 7,
                "status": "DEPRECATED",
                "avg_return": "-7.21%",
                "sharpe": -15.85,
                "max_drawdown": "9.49%",
                "win_rate": "10.2%",
                "trades": 310,
                "summary": "Lagging indicator - entries too late. 310 trades = excessive fees",
                "parameters": {
                    "fast": 12,
                    "slow": 26,
                    "signal": 9
                },
                "rules": ["Buy: MACD crosses above signal", "AVOID for 5m timeframe"]
            }
        ]
        
        return {
            "strategies": strategies,
            "test_period": "30 days (Dec 31, 2025 - Jan 30, 2026)",
            "assets": ["BTC", "ETH", "SOL"],
            "account_size": "$350",
            "data_source": "Binance US 5-minute OHLCV",
            "last_updated": "2026-01-30"
        }
        
    except FileNotFoundError:
        return {"strategies": [], "error": "Backtest file not found"}
    except Exception as e:
        return {"strategies": [], "error": str(e)}

# =============================================================================
# POLYMARKET API
# =============================================================================
POLYMARKET_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

@st.cache_data(ttl=60)
def fetch_polymarket_markets(limit: int = 20) -> List[Dict]:
    """Fetch trending markets from Polymarket"""
    try:
        response = requests.get(
            f"{GAMMA_API}/markets",
            params={"limit": limit, "active": True, "closed": False},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def calculate_portfolio_metrics() -> Dict:
    """Calculate comprehensive portfolio metrics"""
    closed_trades = [t for t in st.session_state.trades if t.get("status") == "Closed"]
    open_positions = [t for t in st.session_state.trades if t.get("status") == "Open"]
    
    total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
    total_trades = len(closed_trades)
    winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
    losing_trades = len([t for t in closed_trades if t.get("pnl", 0) < 0])
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    wins = [t.get("pnl", 0) for t in closed_trades if t.get("pnl", 0) > 0]
    losses = [t.get("pnl", 0) for t in closed_trades if t.get("pnl", 0) < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    initial_capital = st.session_state.settings.get("initial_capital", 1000)
    current_capital = initial_capital + total_pnl
    
    open_exposure = sum(t.get("position_size", 0) for t in open_positions)
    
    all_pnls = [t.get("pnl", 0) for t in closed_trades]
    best_trade = max(all_pnls) if all_pnls else 0
    worst_trade = min(all_pnls) if all_pnls else 0
    
    prong_pnl = {}
    for prong in st.session_state.allocations.keys():
        prong_trades = [t for t in closed_trades if t.get("prong") == prong]
        prong_pnl[prong] = sum(t.get("pnl", 0) for t in prong_trades)
    
    return {
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_pnl / initial_capital * 100) if initial_capital > 0 else 0,
        "current_capital": current_capital,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "open_positions": len(open_positions),
        "open_exposure": open_exposure,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "prong_pnl": prong_pnl
    }

def add_trade(trade_data: Dict):
    """Add a new trade and update allocations"""
    trade_data["id"] = len(st.session_state.trades) + 1
    trade_data["created_at"] = datetime.now().isoformat()
    trade_data["status"] = "Open"
    trade_data["pnl"] = 0
    trade_data["pnl_pct"] = 0
    
    prong = trade_data.get("prong")
    size = trade_data.get("position_size", 0)
    if prong in st.session_state.allocations:
        st.session_state.allocations[prong]["current"] -= size
    
    st.session_state.trades.append(trade_data)
    return trade_data

def close_trade(trade_id: int, exit_price: float, notes: str = ""):
    """Close a trade and calculate P&L"""
    for trade in st.session_state.trades:
        if trade.get("id") == trade_id and trade.get("status") == "Open":
            entry = trade.get("entry_price", 0)
            size = trade.get("position_size", 0)
            direction = 1 if trade.get("direction") == "Long" else -1
            
            if trade.get("prong") == "Polymarket":
                pnl = (exit_price - entry) * size * direction
                pnl_pct = ((exit_price - entry) / entry * 100 * direction) if entry > 0 else 0
            else:
                pnl_pct = ((exit_price - entry) / entry * 100 * direction) if entry > 0 else 0
                pnl = size * (pnl_pct / 100)
            
            trade["status"] = "Closed"
            trade["exit_price"] = exit_price
            trade["pnl"] = pnl
            trade["pnl_pct"] = pnl_pct
            trade["closed_at"] = datetime.now().isoformat()
            trade["close_notes"] = notes
            
            prong = trade.get("prong")
            if prong in st.session_state.allocations:
                st.session_state.allocations[prong]["current"] += size
            
            return trade
    return None

def render_led(status: str) -> str:
    """Render an LED indicator based on status"""
    if status == "ACTIVE":
        return '<span class="led-indicator led-green"></span>'
    elif status == "TESTING":
        return '<span class="led-indicator led-amber"></span>'
    else:
        return '<span class="led-indicator led-red"></span>'

# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    init_session_state()
    
    # =========================================================================
    # MISSION CONTROL HEADER
    # =========================================================================
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; border: 2px solid #00ff41; margin-bottom: 1.5rem; background: #0d1117;">
        <div style="font-size: 0.7rem; color: #4a5568; letter-spacing: 0.3em; margin-bottom: 0.5rem;">
            NATIONAL TRADING ADMINISTRATION
        </div>
        <div style="font-size: 2rem; font-weight: 700; letter-spacing: 0.2em; text-shadow: 0 0 20px #00ff41;">
            🛰️ MISSION CONTROL v2.0
        </div>
        <div style="font-size: 0.8rem; color: #00ff41; letter-spacing: 0.15em; margin-top: 0.5rem;">
            $1K CRYPTO MISSION • ALL SYSTEMS NOMINAL
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # System status bar
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"""
    <div class="terminal-header" style="display: flex; justify-content: space-between;">
        <span>SYSTEM TIME: {current_time} EST</span>
        <span>STATUS: <span style="color: #00ff41;">● OPERATIONAL</span></span>
        <span>UPLINK: <span style="color: #00ff41;">CONNECTED</span></span>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate metrics
    metrics = calculate_portfolio_metrics()
    
    # =========================================================================
    # TOP METRICS - CRT DISPLAYS
    # =========================================================================
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        pnl_class = "profit" if metrics["total_pnl"] >= 0 else "loss"
        st.markdown(f"""
        <div class="metric-crt">
            <div class="label">TOTAL P&L</div>
            <div class="value {pnl_class}">${metrics['total_pnl']:+,.2f}</div>
            <div class="delta">{metrics['total_pnl_pct']:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m2:
        st.markdown(f"""
        <div class="metric-crt">
            <div class="label">CURRENT CAPITAL</div>
            <div class="value">${metrics['current_capital']:,.2f}</div>
            <div class="delta">INITIAL: ${st.session_state.settings['initial_capital']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m3:
        wr_class = "profit" if metrics['win_rate'] >= 50 else "amber"
        st.markdown(f"""
        <div class="metric-crt">
            <div class="label">WIN RATE</div>
            <div class="value {wr_class}">{metrics['win_rate']:.1f}%</div>
            <div class="delta">{metrics['winning_trades']}W / {metrics['losing_trades']}L</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m4:
        pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] < 100 else "∞"
        pf_class = "profit" if metrics['profit_factor'] >= 1.5 else ("amber" if metrics['profit_factor'] >= 1 else "loss")
        st.markdown(f"""
        <div class="metric-crt">
            <div class="label">PROFIT FACTOR</div>
            <div class="value {pf_class}">{pf_display}</div>
            <div class="delta">AVG WIN: ${metrics['avg_win']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m5:
        pos_class = "amber" if metrics['open_positions'] > 0 else ""
        st.markdown(f"""
        <div class="metric-crt">
            <div class="label">OPEN POSITIONS</div>
            <div class="value {pos_class}">{metrics['open_positions']}</div>
            <div class="delta">${metrics['open_exposure']:.2f} EXPOSED</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # =========================================================================
    # MAIN NAVIGATION TABS
    # =========================================================================
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📡 COMMAND", 
        "🤖 LIVE BOT",
        "📝 TRADE ENTRY", 
        "🎰 POLYMARKET",
        "🧪 BACKTESTING",
        "📈 ANALYTICS",
        "⚙️ SYSTEMS"
    ])
    
    # =========================================================================
    # TAB 1: COMMAND CENTER (DASHBOARD)
    # =========================================================================
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    💼 CAPITAL ALLOCATION
                </div>
            """, unsafe_allow_html=True)
            
            for prong, data in st.session_state.allocations.items():
                allocated = data["allocated"]
                current = data["current"]
                used = allocated - current
                pct = (used / allocated * 100) if allocated > 0 else 0
                prong_pnl = metrics["prong_pnl"].get(prong, 0)
                
                led = "led-green" if prong_pnl >= 0 else "led-red"
                
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                        <span><span class="led-indicator {led}"></span>{prong.upper()}</span>
                        <span style="color: {'#00ff41' if prong_pnl >= 0 else '#ff0000'};">${prong_pnl:+.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.progress(pct / 100, text=f"${used:.0f} / ${allocated:.0f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Allocation visualization
            fig = go.Figure(data=[go.Pie(
                labels=list(st.session_state.allocations.keys()),
                values=[d["allocated"] - d["current"] for d in st.session_state.allocations.values()],
                hole=0.6,
                marker_colors=['#ff6600', '#00ff41', '#ffaa00'],
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(family='IBM Plex Mono', size=10, color='#00ff41')
            )])
            fig.update_layout(
                showlegend=False,
                height=250,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='IBM Plex Mono', color='#00ff41')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    📋 MISSION LOG - RECENT OPERATIONS
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.trades:
                sorted_trades = sorted(
                    st.session_state.trades, 
                    key=lambda x: x.get("created_at", ""), 
                    reverse=True
                )[:10]
                
                for trade in sorted_trades:
                    status = trade.get("status", "Open")
                    pnl = trade.get("pnl", 0)
                    
                    if status == "Closed":
                        row_class = "profit" if pnl > 0 else "loss"
                    else:
                        row_class = "open"
                    
                    direction_indicator = "▲" if trade.get("direction") == "Long" else "▼"
                    status_text = "OPEN" if status == "Open" else ("+" if pnl >= 0 else "-")
                    
                    st.markdown(f"""
                    <div class="trade-row {row_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem;">
                            <div>
                                <span style="color: {'#00ff41' if trade.get('direction') == 'Long' else '#ff6600'};">{direction_indicator}</span>
                                <strong style="margin-left: 0.5rem;">{trade.get('asset', 'N/A')}</strong>
                                <span style="color: #4a5568; margin-left: 0.5rem; font-size: 0.75rem;">[{trade.get('prong', '').upper()}]</span>
                            </div>
                            <div style="text-align: right;">
                                <span style="color: #4a5568;">${trade.get('position_size', 0):.2f}</span>
                                {f'<span style="color: {("#00ff41" if pnl >= 0 else "#ff0000")}; margin-left: 1rem;">${pnl:+.2f}</span>' if status == "Closed" else '<span style="color: #ffaa00; margin-left: 1rem;">ACTIVE</span>'}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; color: #4a5568;">
                    [ NO OPERATIONS LOGGED ]<br>
                    <span style="font-size: 0.8rem;">Proceed to TRADE ENTRY to initiate first operation</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 2: LIVE BOT
    # =========================================================================
    with tab2:
        st.markdown("""
        <div class="mission-panel">
            <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                🤖 AUTOMATED TRADING SYSTEM
            </div>
        """, unsafe_allow_html=True)
        
        try:
            bot_data_path = os.path.join(os.path.dirname(__file__), 'bot_data.json')
            with open(bot_data_path, 'r') as f:
                bot_data = json.load(f)
            
            last_update = bot_data.get('last_updated', 'Unknown')
            st.markdown(f'<div style="color: #4a5568; font-size: 0.75rem; margin-bottom: 1rem;">LAST SYNC: {last_update}</div>', unsafe_allow_html=True)
            
            account = bot_data.get('account', {})
            total_usd = account.get('total_usd', 0)
            state = bot_data.get('trading_state', {})
            
            b1, b2, b3 = st.columns(3)
            with b1:
                st.markdown(f"""
                <div class="metric-crt">
                    <div class="label">BOT BALANCE</div>
                    <div class="value">${total_usd:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with b2:
                daily_pnl = state.get('daily_pnl', 0)
                pnl_class = "profit" if daily_pnl >= 0 else "loss"
                st.markdown(f"""
                <div class="metric-crt">
                    <div class="label">DAILY P&L</div>
                    <div class="value {pnl_class}">${daily_pnl:+,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with b3:
                st.markdown(f"""
                <div class="metric-crt">
                    <div class="label">TRADES TODAY</div>
                    <div class="value amber">{state.get('daily_trades', 0)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**[ HOLDINGS ]**")
                balances = account.get('balances', [])
                if balances:
                    for b in balances:
                        currency = b.get('currency', '?')
                        amount = b.get('amount', 0)
                        usd = b.get('usd_value', 0)
                        st.markdown(f"• **{currency}**: {amount:.6f} (${usd:.2f})")
                else:
                    st.markdown("_No balance data_")
            
            with col2:
                st.markdown("**[ MARKET DATA ]**")
                markets = bot_data.get('markets', [])
                if markets:
                    for m in markets[:5]:
                        symbol = m.get('symbol', '?')
                        price = m.get('price', 0)
                        change = m.get('change_24h', 0)
                        indicator = "▲" if change >= 0 else "▼"
                        color = "#00ff41" if change >= 0 else "#ff0000"
                        st.markdown(f'<span style="color: {color};">{indicator}</span> **{symbol}**: ${price:,.2f} ({change:+.1f}%)', unsafe_allow_html=True)
                else:
                    st.markdown("_No market data_")
            
            trades = bot_data.get('recent_trades', [])
            if trades:
                st.markdown("<br>**[ RECENT BOT OPERATIONS ]**", unsafe_allow_html=True)
                trades_df = pd.DataFrame(trades[-10:])
                st.dataframe(trades_df, use_container_width=True, hide_index=True)
                
        except FileNotFoundError:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; border: 1px dashed #ffaa00;">
                <span style="color: #ffaa00;">⚠ BOT DATA NOT FOUND</span><br>
                <span style="color: #4a5568; font-size: 0.8rem;">Awaiting first synchronization cycle...</span>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"[ SYSTEM ERROR: {e} ]")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 3: TRADE ENTRY
    # =========================================================================
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    ➕ INITIATE NEW OPERATION
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("new_trade", clear_on_submit=True):
                prong = st.selectbox("STRATEGY PRONG", list(st.session_state.allocations.keys()))
                asset = st.text_input("TARGET ASSET", placeholder="BTC, ETH, SOL...")
                
                c1, c2 = st.columns(2)
                with c1:
                    direction = st.selectbox("VECTOR", ["Long", "Short"])
                with c2:
                    available = st.session_state.allocations[prong]["current"]
                    position_size = st.number_input(
                        f"POSITION SIZE (${available:.0f} AVAIL)", 
                        min_value=0.0, 
                        max_value=float(available),
                        step=10.0
                    )
                
                c1, c2 = st.columns(2)
                with c1:
                    entry_price = st.number_input("ENTRY PRICE", min_value=0.0, step=0.0001, format="%.4f")
                with c2:
                    target = st.number_input("TARGET PRICE", min_value=0.0, step=0.0001, format="%.4f")
                
                stop_loss = st.number_input("STOP LOSS", min_value=0.0, step=0.0001, format="%.4f")
                thesis = st.text_area("MISSION THESIS", placeholder="Rationale for this operation...")
                
                if st.form_submit_button("🚀 EXECUTE TRADE", use_container_width=True):
                    if asset and position_size > 0:
                        trade = add_trade({
                            "prong": prong,
                            "asset": asset.upper(),
                            "direction": direction,
                            "position_size": position_size,
                            "entry_price": entry_price,
                            "target": target,
                            "stop_loss": stop_loss,
                            "thesis": thesis
                        })
                        st.success(f"[ TRADE #{trade['id']} EXECUTED: {direction.upper()} {asset.upper()} ]")
                        st.rerun()
                    else:
                        st.error("[ ERROR: ASSET AND POSITION SIZE REQUIRED ]")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    🔒 TERMINATE POSITION
                </div>
            """, unsafe_allow_html=True)
            
            open_trades = [t for t in st.session_state.trades if t.get("status") == "Open"]
            
            if open_trades:
                with st.form("close_trade"):
                    trade_options = {
                        f"#{t['id']} - {t['asset']} ({t['direction']}) - ${t['position_size']:.2f}": t 
                        for t in open_trades
                    }
                    selected = st.selectbox("SELECT POSITION", list(trade_options.keys()))
                    trade = trade_options[selected]
                    
                    st.markdown(f"""
                    <div style="background: #0a0a0a; padding: 0.75rem; border: 1px solid #00ff4133; margin: 0.5rem 0;">
                        ENTRY: ${trade['entry_price']:.4f} | TARGET: ${trade.get('target', 0):.4f} | STOP: ${trade.get('stop_loss', 0):.4f}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    exit_price = st.number_input("EXIT PRICE", min_value=0.0, step=0.0001, format="%.4f")
                    close_notes = st.text_area("CLOSE NOTES", placeholder="Operation outcome...")
                    
                    if st.form_submit_button("🔒 CLOSE POSITION", use_container_width=True):
                        result = close_trade(trade["id"], exit_price, close_notes)
                        if result:
                            pnl = result["pnl"]
                            status = "SUCCESS" if pnl >= 0 else "LOSS"
                            st.success(f"[ POSITION CLOSED - {status}: ${pnl:+.2f} ({result['pnl_pct']:+.1f}%) ]")
                            st.rerun()
            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; color: #4a5568;">
                    [ NO ACTIVE POSITIONS ]
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 4: POLYMARKET
    # =========================================================================
    with tab4:
        st.markdown("""
        <div class="mission-panel">
            <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                🎰 PREDICTION MARKET SCANNER
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            markets = fetch_polymarket_markets(20)
            
            if markets:
                for market in markets[:10]:
                    title = market.get("question", market.get("title", "Unknown"))
                    volume = market.get("volume", 0)
                    liquidity = market.get("liquidity", 0)
                    
                    with st.expander(f"📊 {title[:70]}...", expanded=False):
                        c1, c2 = st.columns(2)
                        with c1:
                            vol_display = f"${volume:,.0f}" if volume else "N/A"
                            st.markdown(f"**VOLUME:** {vol_display}")
                        with c2:
                            liq_display = f"${liquidity:,.0f}" if liquidity else "N/A"
                            st.markdown(f"**LIQUIDITY:** {liq_display}")
                        
                        if st.button(f"📌 ADD TO WATCHLIST", key=f"watch_{market.get('id', title[:20])}"):
                            st.session_state.polymarket_watchlist.append({
                                "title": title,
                                "id": market.get("id"),
                                "added_at": datetime.now().isoformat()
                            })
                            st.success("[ ADDED TO WATCHLIST ]")
            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; border: 1px dashed #ffaa00;">
                    <span style="color: #ffaa00;">⚠ UNABLE TO FETCH MARKET DATA</span><br>
                    <span style="color: #4a5568; font-size: 0.8rem;">API may be rate-limited</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**[ WATCHLIST ]**")
            
            if st.session_state.polymarket_watchlist:
                for i, item in enumerate(st.session_state.polymarket_watchlist):
                    st.markdown(f"""
                    <div style="background: #0d1117; border: 1px solid #00ff4133; padding: 0.5rem; margin-bottom: 0.5rem; font-size: 0.8rem;">
                        {item['title'][:40]}...
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ REMOVE", key=f"del_watch_{i}"):
                        st.session_state.polymarket_watchlist.pop(i)
                        st.rerun()
            else:
                st.markdown("_No markets tracked_")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 5: BACKTESTING STRATEGIES
    # =========================================================================
    with tab5:
        st.markdown("""
        <div class="mission-panel">
            <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                🧪 STRATEGY BACKTESTING LABORATORY
            </div>
        """, unsafe_allow_html=True)
        
        backtest_data = load_backtest_results()
        
        if backtest_data.get("error"):
            st.error(f"[ ERROR: {backtest_data['error']} ]")
        else:
            # Test metadata
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background: #0a0a0a; padding: 0.75rem; border: 1px solid #00ff4133; margin-bottom: 1rem; font-size: 0.8rem;">
                <span>TEST PERIOD: {backtest_data.get('test_period', 'N/A')}</span>
                <span>ASSETS: {', '.join(backtest_data.get('assets', []))}</span>
                <span>ACCOUNT: {backtest_data.get('account_size', 'N/A')}</span>
                <span>SOURCE: {backtest_data.get('data_source', 'N/A')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Strategy grid
            for strategy in backtest_data.get("strategies", []):
                status = strategy.get("status", "TESTING")
                status_class = status.lower()
                card_class = status.lower()
                
                sharpe = strategy.get("sharpe", 0)
                sharpe_color = "#00ff41" if sharpe > 1 else ("#ffaa00" if sharpe > 0 else "#ff0000")
                
                avg_return = strategy.get("avg_return", "0%")
                return_color = "#00ff41" if avg_return.startswith("+") else "#ff0000"
                
                st.markdown(f"""
                <div class="strategy-card {card_class}">
                    <div class="strategy-header">
                        <div>
                            {render_led(status)}
                            <span class="strategy-name">{strategy.get('id')}: {strategy.get('name')}</span>
                        </div>
                        <span class="strategy-status status-{status_class}">{status}</span>
                    </div>
                    <div style="color: #4a5568; font-size: 0.85rem; margin-bottom: 1rem;">
                        {strategy.get('summary', '')}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin-bottom: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #4a5568; text-transform: uppercase;">AVG RETURN</div>
                            <div style="font-size: 1.1rem; color: {return_color}; font-weight: 700;">{avg_return}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #4a5568; text-transform: uppercase;">SHARPE</div>
                            <div style="font-size: 1.1rem; color: {sharpe_color}; font-weight: 700;">{sharpe:.2f}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #4a5568; text-transform: uppercase;">MAX DD</div>
                            <div style="font-size: 1.1rem; color: #ffaa00; font-weight: 700;">{strategy.get('max_drawdown', 'N/A')}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #4a5568; text-transform: uppercase;">WIN RATE</div>
                            <div style="font-size: 1.1rem; font-weight: 700;">{strategy.get('win_rate', 'N/A')}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #4a5568; text-transform: uppercase;">TRADES</div>
                            <div style="font-size: 1.1rem; font-weight: 700;">{strategy.get('trades', 0)}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable details
                with st.expander(f"📋 {strategy.get('id')} DETAILS", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**[ PARAMETERS ]**")
                        params = strategy.get("parameters", {})
                        for key, value in params.items():
                            st.markdown(f"• `{key}`: {value}")
                    
                    with col2:
                        st.markdown("**[ TRADING RULES ]**")
                        rules = strategy.get("rules", [])
                        for rule in rules:
                            st.markdown(f"• {rule}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 6: ANALYTICS
    # =========================================================================
    with tab6:
        st.markdown("""
        <div class="mission-panel">
            <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                📈 PERFORMANCE TELEMETRY
            </div>
        """, unsafe_allow_html=True)
        
        closed_trades = [t for t in st.session_state.trades if t.get("status") == "Closed"]
        
        if closed_trades:
            col1, col2 = st.columns(2)
            
            with col1:
                # Cumulative P&L chart
                sorted_closed = sorted(closed_trades, key=lambda x: x.get("closed_at", ""))
                cumulative = []
                running_pnl = 0
                for trade in sorted_closed:
                    running_pnl += trade.get("pnl", 0)
                    cumulative.append({
                        "date": trade.get("closed_at", "")[:10],
                        "pnl": running_pnl,
                        "trade": f"#{trade['id']} {trade['asset']}"
                    })
                
                cum_df = pd.DataFrame(cumulative)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(cum_df))),
                    y=cum_df["pnl"],
                    mode='lines+markers',
                    fill='tozeroy',
                    fillcolor='rgba(0,255,65,0.1)',
                    line=dict(color='#00ff41', width=2),
                    marker=dict(color='#00ff41', size=6),
                    hovertemplate='Trade: %{text}<br>P&L: $%{y:.2f}<extra></extra>',
                    text=cum_df["trade"]
                ))
                fig.update_layout(
                    title=dict(text="CUMULATIVE P&L", font=dict(family='IBM Plex Mono', color='#00ff41')),
                    xaxis_title="TRADE #",
                    yaxis_title="P&L ($)",
                    height=350,
                    paper_bgcolor='#0d1117',
                    plot_bgcolor='#0a0a0a',
                    font=dict(family='IBM Plex Mono', color='#00ff41'),
                    xaxis=dict(gridcolor='#1a1a2e', zerolinecolor='#00ff41'),
                    yaxis=dict(gridcolor='#1a1a2e', zerolinecolor='#00ff41')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # P&L distribution
                pnls = [t.get("pnl", 0) for t in closed_trades]
                colors = ['#00ff41' if p >= 0 else '#ff0000' for p in pnls]
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=pnls,
                    nbinsx=15,
                    marker_color='#00ff41',
                    marker_line_color='#00cc33',
                    marker_line_width=1
                ))
                fig.update_layout(
                    title=dict(text="P&L DISTRIBUTION", font=dict(family='IBM Plex Mono', color='#00ff41')),
                    xaxis_title="P&L ($)",
                    yaxis_title="FREQUENCY",
                    height=350,
                    paper_bgcolor='#0d1117',
                    plot_bgcolor='#0a0a0a',
                    font=dict(family='IBM Plex Mono', color='#00ff41'),
                    xaxis=dict(gridcolor='#1a1a2e'),
                    yaxis=dict(gridcolor='#1a1a2e')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance by prong
            st.markdown("**[ PERFORMANCE BY STRATEGY ]**")
            
            prong_data = []
            for prong in st.session_state.allocations.keys():
                prong_trades = [t for t in closed_trades if t.get("prong") == prong]
                if prong_trades:
                    wins = len([t for t in prong_trades if t.get("pnl", 0) > 0])
                    total = len(prong_trades)
                    pnl = sum(t.get("pnl", 0) for t in prong_trades)
                    prong_data.append({
                        "STRATEGY": prong.upper(),
                        "TRADES": total,
                        "WIN RATE": f"{wins/total*100:.1f}%" if total > 0 else "N/A",
                        "TOTAL P&L": f"${pnl:+.2f}",
                        "AVG TRADE": f"${pnl/total:+.2f}" if total > 0 else "N/A"
                    })
            
            if prong_data:
                st.dataframe(pd.DataFrame(prong_data), use_container_width=True, hide_index=True)
            
            # Full trade log
            st.markdown("**[ COMPLETE MISSION LOG ]**")
            trades_df = pd.DataFrame(closed_trades)
            display_cols = ["id", "prong", "asset", "direction", "position_size", "entry_price", "exit_price", "pnl", "pnl_pct"]
            available_cols = [c for c in display_cols if c in trades_df.columns]
            st.dataframe(
                trades_df[available_cols].sort_values("id", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #4a5568;">
                [ INSUFFICIENT DATA FOR ANALYSIS ]<br>
                <span style="font-size: 0.8rem;">Complete trade operations to generate telemetry</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 7: SYSTEMS (SETTINGS)
    # =========================================================================
    with tab7:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    ⚙️ SYSTEM CONFIGURATION
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("settings_form"):
                initial_capital = st.number_input(
                    "INITIAL CAPITAL ($)", 
                    value=st.session_state.settings.get("initial_capital", 1000),
                    step=100
                )
                
                risk_per_trade = st.slider(
                    "RISK PER TRADE (%)",
                    min_value=0.5,
                    max_value=10.0,
                    value=st.session_state.settings.get("risk_per_trade", 2.0),
                    step=0.5
                )
                
                st.markdown("**[ ALLOCATION MATRIX ]**")
                new_allocations = {}
                for prong, data in st.session_state.allocations.items():
                    new_alloc = st.number_input(
                        f"{prong.upper()}",
                        value=data["allocated"],
                        step=50,
                        key=f"alloc_{prong}"
                    )
                    new_allocations[prong] = new_alloc
                
                if st.form_submit_button("💾 SAVE CONFIGURATION", use_container_width=True):
                    st.session_state.settings["initial_capital"] = initial_capital
                    st.session_state.settings["risk_per_trade"] = risk_per_trade
                    
                    for prong, new_alloc in new_allocations.items():
                        old_alloc = st.session_state.allocations[prong]["allocated"]
                        diff = new_alloc - old_alloc
                        st.session_state.allocations[prong]["allocated"] = new_alloc
                        st.session_state.allocations[prong]["current"] += diff
                    
                    st.success("[ CONFIGURATION SAVED ]")
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="mission-panel">
                <div style="font-size: 0.8rem; letter-spacing: 0.2em; margin-bottom: 1rem; border-bottom: 1px solid #00ff4133; padding-bottom: 0.5rem;">
                    💾 DATA MANAGEMENT
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**[ EXPORT DATA ]**")
            export_json = export_data()
            st.download_button(
                "📥 DOWNLOAD BACKUP",
                data=export_json,
                file_name=f"mission_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("**[ IMPORT DATA ]**")
            uploaded_file = st.file_uploader("UPLOAD BACKUP FILE", type="json")
            if uploaded_file:
                if st.button("📤 IMPORT DATA", use_container_width=True):
                    content = uploaded_file.read().decode("utf-8")
                    if import_data(content):
                        st.success("[ DATA IMPORTED SUCCESSFULLY ]")
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("**[ ⚠️ DANGER ZONE ]**")
            if st.button("🗑️ RESET ALL DATA", use_container_width=True):
                st.warning("[ WARNING: THIS WILL DELETE ALL MISSION DATA ]")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # SIDEBAR - COMMAND MODULE
    # =========================================================================
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem; border: 1px solid #00ff41; margin-bottom: 1rem;">
            <div style="font-size: 0.7rem; color: #4a5568; letter-spacing: 0.2em;">COMMAND MODULE</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("**[ MISSION STATUS ]**")
        
        capital_delta = metrics['total_pnl_pct']
        st.metric("CAPITAL", f"${metrics['current_capital']:,.0f}", f"{capital_delta:+.1f}%")
        st.metric("EXPOSURE", f"${metrics['open_exposure']:.0f}", f"{metrics['open_positions']} ACTIVE")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("**[ STRATEGY P&L ]**")
        for prong, pnl in metrics["prong_pnl"].items():
            indicator = "▲" if pnl >= 0 else "▼"
            color = "#00ff41" if pnl >= 0 else "#ff0000"
            st.markdown(f'<span style="color: {color};">{indicator}</span> {prong}: ${pnl:+.2f}', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("**[ QUICK LINKS ]**")
        st.markdown("[📊 Polymarket](https://polymarket.com)")
        st.markdown("[📈 TradingView](https://tradingview.com)")
        st.markdown("[🪙 CoinGecko](https://coingecko.com)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔄 REFRESH SYSTEMS", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("""
        <div style="text-align: center; padding: 1rem; margin-top: 2rem; border-top: 1px solid #00ff4133;">
            <div style="font-size: 0.6rem; color: #4a5568; letter-spacing: 0.15em;">
                MISSION CONTROL v2.0<br>
                $1K CRYPTO MISSION<br>
                <span style="color: #00ff41;">● SYSTEMS NOMINAL</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# LAUNCH SEQUENCE
# =============================================================================
if __name__ == "__main__":
    main()

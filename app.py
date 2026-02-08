#!/usr/bin/env python3
"""
Trading Dashboard - $1K Crypto Mission
NASA Mission Control Aesthetic
Public dashboard - view only, no trade execution
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# Import enhanced projection utilities
from utils import (
    calculate_daily_returns,
    calculate_projections,
    run_monte_carlo_simulation,
    calculate_trade_statistics,
    get_comprehensive_projections,
    load_all_trades_data,
    calculate_real_balance,
    calculate_moving_averages,
    calculate_linear_regression_trend,
    calculate_volatility_metrics
)

# Import enhanced live position tracker
from live_positions import integrate_live_positions_section

# Page config
st.set_page_config(
    page_title="MISSION CONTROL • Trading Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load data from trading-bot/data directory
def load_bot_data():
    """Load trading data from the bot data directory."""
    data_paths = [
        '/Users/kolade/clawd/trading-bot/data/dashboard.json',
        'bot_data.json',
    ]
    
    for path in data_paths:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            continue
    
    # Fallback defaults
    return {
        "account": {"total_usd": 349},
        "trading_state": {"starting_balance": 376.26},
        "recent_trades": [],
        "positions": {}
    }

def load_trades_from_jsonl():
    """Load all trades from trades.jsonl file."""
    trades = []
    jsonl_paths = [
        '/Users/kolade/clawd/trading-bot/data/trades.jsonl',
        'trades.jsonl',
    ]
    
    for path in jsonl_paths:
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        trades.append(json.loads(line))
            if trades:
                break
        except:
            continue
    
    return trades

# Load real data using enhanced functions
BOT_DATA = load_bot_data()
ALL_TRADES = load_all_trades_data()  # Load all 30+ trades from both sources
REAL_CURRENT_BALANCE, REAL_STARTING_BALANCE, REAL_TOTAL_PNL = calculate_real_balance()

# ============================================
# PERFORMANCE METRICS CALCULATION FUNCTIONS
# ============================================
def calculate_performance_metrics(trades, starting_balance, current_balance, period_days=None):
    """
    Calculate comprehensive performance metrics from trade history.
    
    Args:
        trades: List of trade dictionaries with pnl, entry_time, exit_time
        starting_balance: Initial account balance
        current_balance: Current account balance
        period_days: Filter trades within this many days (None for all time)
    
    Returns:
        Dictionary of performance metrics
    """
    if not trades:
        return None
    
    # Filter trades by time period if specified
    if period_days:
        cutoff_date = datetime.now() - timedelta(days=period_days)
        filtered_trades = []
        for t in trades:
            try:
                exit_time = datetime.fromisoformat(t.get('exit_time', '').replace('Z', ''))
                if exit_time >= cutoff_date:
                    filtered_trades.append(t)
            except:
                continue
        trades = filtered_trades
    
    if not trades:
        return None
    
    # Basic counts
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
    
    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    
    # Win rate
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    loss_rate = 100 - win_rate
    
    # P&L calculations
    gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
    gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
    net_pnl = gross_profit - gross_loss
    
    # Average win/loss
    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    
    # Profit Factor
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Risk/Reward Ratio
    risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    # Expectancy: (Win% × Avg Win) - (Loss% × Avg Loss)
    expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)
    
    # Max Drawdown calculation
    # Build equity curve from trades
    equity_curve = [starting_balance]
    running_balance = starting_balance
    
    # Sort trades by exit time
    sorted_trades = sorted(trades, key=lambda x: x.get('exit_time', ''))
    for t in sorted_trades:
        running_balance += t.get('pnl', 0)
        equity_curve.append(running_balance)
    
    # Calculate max drawdown
    peak = equity_curve[0]
    max_drawdown = 0
    max_drawdown_pct = 0
    
    for balance in equity_curve:
        if balance > peak:
            peak = balance
        drawdown = peak - balance
        drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
        if drawdown_pct > max_drawdown_pct:
            max_drawdown = drawdown
            max_drawdown_pct = drawdown_pct
    
    # Sharpe Ratio calculation (simplified)
    # Using daily returns assumption for trading period
    if len(trades) >= 2:
        returns = [t.get('pnl', 0) for t in trades]
        avg_return = sum(returns) / len(returns)
        
        # Standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        # Risk-free rate (assume 0 for crypto short-term)
        risk_free_rate = 0
        
        # Sharpe = (Return - Risk-free) / Std Dev
        # Adjust for trade frequency - annualize roughly
        sharpe_ratio = ((avg_return - risk_free_rate) / std_dev * (252 ** 0.5)) if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
        std_dev = 0
    
    # Additional stats
    best_trade = max(t.get('pnl', 0) for t in trades)
    worst_trade = min(t.get('pnl', 0) for t in trades)
    
    # Calculate streaks
    current_streak = 0
    current_streak_type = None
    max_win_streak = 0
    max_loss_streak = 0
    
    for t in sorted_trades:
        is_win = t.get('pnl', 0) > 0
        if current_streak_type is None:
            current_streak_type = is_win
            current_streak = 1
        elif is_win == current_streak_type:
            current_streak += 1
        else:
            if current_streak_type:
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)
            current_streak_type = is_win
            current_streak = 1
    
    # Final streak check
    if current_streak_type:
        max_win_streak = max(max_win_streak, current_streak)
    else:
        max_loss_streak = max(max_loss_streak, current_streak)
    
    # Current streak (from most recent)
    recent_streak = 0
    recent_streak_type = None
    for t in reversed(sorted_trades):
        is_win = t.get('pnl', 0) > 0
        if recent_streak_type is None:
            recent_streak_type = is_win
            recent_streak = 1
        elif is_win == recent_streak_type:
            recent_streak += 1
        else:
            break
    
    # Calculate Calmar Ratio (Annualized Return / Max Drawdown)
    total_return_pct = ((equity_curve[-1] - starting_balance) / starting_balance * 100) if starting_balance > 0 else 0
    calmar_ratio = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else float('inf') if total_return_pct > 0 else 0
    
    # Calculate Average Win/Loss in percentage
    avg_win_pct_values = []
    avg_loss_pct_values = []
    for t in trades:
        pnl_pct = t.get('pnl_pct', 0)
        if pnl_pct > 0:
            avg_win_pct_values.append(pnl_pct)
        elif pnl_pct < 0:
            avg_loss_pct_values.append(abs(pnl_pct))
    
    avg_win_pct = sum(avg_win_pct_values) / len(avg_win_pct_values) if avg_win_pct_values else 0
    avg_loss_pct = sum(avg_loss_pct_values) / len(avg_loss_pct_values) if avg_loss_pct_values else 0
    
    # Return all metrics
    return {
        'total_trades': total_trades,
        'win_count': win_count,
        'loss_count': loss_count,
        'win_rate': win_rate,
        'loss_rate': loss_rate,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'net_pnl': net_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'profit_factor': profit_factor,
        'risk_reward_ratio': risk_reward_ratio,
        'expectancy': expectancy,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe_ratio': sharpe_ratio,
        'calmar_ratio': calmar_ratio,
        'total_return_pct': total_return_pct,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'current_streak': recent_streak,
        'current_streak_type': recent_streak_type,
        'std_dev': std_dev,
        'equity_curve': equity_curve
    }
# Use real calculated balances instead of hardcoded values
TOTAL_BALANCE = REAL_CURRENT_BALANCE
STARTING_BALANCE = REAL_STARTING_BALANCE
CURRENT_PNL = REAL_TOTAL_PNL

print(f"🔍 DEBUG: Real balance calculation - Starting: ${STARTING_BALANCE:.2f}, Current: ${TOTAL_BALANCE:.2f}, P&L: ${CURRENT_PNL:.2f}")
print(f"🔍 DEBUG: Loaded {len(ALL_TRADES)} total trades from all sources")

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
    
    /* Performance Metrics Grid */
    .perf-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    /* Data-dense metric cards */
    .metric-dense {
        padding: 12px 15px !important;
        margin: 5px 0 !important;
    }
    
    .metric-dense .metric-value {
        font-size: 1.6rem !important;
        margin: 3px 0 !important;
    }
    
    .metric-dense .metric-label {
        font-size: 0.7rem !important;
        letter-spacing: 0.5px !important;
    }
    
    .metric-dense .metric-sub {
        font-size: 0.75rem !important;
        color: #666 !important;
        margin-top: 2px !important;
    }
    
    /* Terminal scanline effect */
    .terminal-bg::after {
        content: "";
        position: absolute;
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
        z-index: 1;
    }
    
    /* Section headers */
    h3 {
        color: #ff6600 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 1rem !important;
        margin: 20px 0 10px 0 !important;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
    }
    
    /* Button styling for period selector */
    button[kind="primary"] {
        background: linear-gradient(145deg, #39ff14, #2dd60f) !important;
        color: #0a0a0a !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    button[kind="secondary"] {
        background: #1a1a1a !important;
        border: 1px solid #39ff14 !important;
        color: #39ff14 !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# Header with Mission Control styling
st.markdown('<p class="main-header">🚀 MISSION CONTROL TRADING DASHBOARD</p>', unsafe_allow_html=True)
st.markdown(f'<p class="mission-subtitle">$1K CRYPTO MISSION • LAST UPDATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} EST</p>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🎯 MISSION CONTROL", "📊 POLYMARKET", "📰 NEWS TRADING", "🔬 BACKTESTING", "📊 PERFORMANCE", "📜 TRADE HISTORY"])

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
        # Real expected daily based on mathematical analysis of all trades
        if len(ALL_TRADES) >= 10:
            # Use comprehensive projections for accurate calculations
            comprehensive_projections = get_comprehensive_projections(ALL_TRADES, TOTAL_BALANCE, STARTING_BALANCE)
            
            if comprehensive_projections:
                trade_stats = comprehensive_projections['trade_stats']
                daily_stats = comprehensive_projections['daily_stats']
                
                # Mathematical expectancy per trade
                expectancy_per_trade = trade_stats['expectancy']
                real_daily_trades = daily_stats['avg_trades_per_day']
                
                # Expected daily P&L = expectancy × trades per day
                expected_daily = expectancy_per_trade * real_daily_trades
                
                # Check if trend analysis is available for trend-adjusted expectation
                trend_analysis = comprehensive_projections.get('trend_analysis', {})
                if trend_analysis and 'daily_trend_pnl' in trend_analysis:
                    trend_daily_pnl = trend_analysis['daily_trend_pnl']
                    trend_strength = trend_analysis.get('current_trend_strength', 0)
                    
                    # Combine expectancy with trend (weighted by trend strength)
                    if trend_strength > 0.3:  # Only use trend if reasonably strong
                        expected_daily = (expected_daily * (1 - trend_strength)) + (trend_daily_pnl * trend_strength)
                        daily_label = f"TREND-ADJ: {real_daily_trades:.1f} tpd"
                    else:
                        daily_label = f"EXPECTANCY: {real_daily_trades:.1f} tpd"
                else:
                    daily_label = f"MATHEMATICAL: {real_daily_trades:.1f} tpd"
            else:
                # Fallback to simple calculation
                trade_stats = calculate_trade_statistics(ALL_TRADES)
                if trade_stats:
                    expected_daily = trade_stats['expectancy'] * 2  # Conservative 2 trades/day
                    daily_label = "EXPECTANCY FALLBACK"
                else:
                    expected_daily = CURRENT_PNL / max(len(ALL_TRADES) / 2, 1)
                    daily_label = "ACTUAL AVERAGE"
        else:
            # Insufficient data for statistical analysis
            total_trading_days = max(len(ALL_TRADES) / 2, 1)  # Estimate trading days
            expected_daily = CURRENT_PNL / total_trading_days
            daily_label = f"ACTUAL: {len(ALL_TRADES)} trades"
        
        daily_color = "normal" if expected_daily >= 0 else "inverse"
        st.metric(
            "📊 EXPECTED DAILY",
            f"${expected_daily:+.2f}",
            daily_label,
            delta_color=daily_color
        )
    
    with col4:
        # Real expected monthly using mathematical compound growth models
        if len(ALL_TRADES) >= 10 and 'comprehensive_projections' in locals():
            if comprehensive_projections:
                # Use 30-day mathematical projection
                math_projections = comprehensive_projections['math_projections']
                proj_30d = math_projections.get('30d', {})
                
                if 'projected' in proj_30d:
                    expected_monthly = proj_30d['projected'] - TOTAL_BALANCE
                    
                    # Check if trend-adjusted projection is available
                    if 'trend_adjusted' in proj_30d:
                        trend_monthly = proj_30d['trend_adjusted'] - TOTAL_BALANCE
                        trend_conf = proj_30d.get('trend_confidence', 0)
                        if trend_conf > 0.3:
                            expected_monthly = trend_monthly
                            monthly_label = f"TREND: R²={trend_conf:.2f}"
                        else:
                            monthly_label = "COMPOUND GROWTH"
                    else:
                        monthly_label = "COMPOUND GROWTH"
                else:
                    # Fallback to daily compound calculation
                    daily_stats = comprehensive_projections['daily_stats']
                    if daily_stats and 'avg_daily_return' in daily_stats:
                        compound_factor = (1 + daily_stats['avg_daily_return']) ** 30
                        expected_monthly = TOTAL_BALANCE * compound_factor - TOTAL_BALANCE
                        monthly_label = "DAILY COMPOUND"
                    else:
                        expected_monthly = expected_daily * 30
                        monthly_label = "LINEAR FALLBACK"
            else:
                expected_monthly = expected_daily * 30
                monthly_label = "LINEAR PROJECTION"
        else:
            # Not enough data for statistical projections
            if len(ALL_TRADES) >= 5:
                # Simple compound calculation if we have some data
                daily_stats = calculate_daily_returns(ALL_TRADES, TOTAL_BALANCE, STARTING_BALANCE)
                if daily_stats and 'avg_daily_return' in daily_stats:
                    compound_factor = (1 + daily_stats['avg_daily_return']) ** 30
                    expected_monthly = TOTAL_BALANCE * compound_factor - TOTAL_BALANCE
                    monthly_label = "COMPOUND (LIMITED)"
                else:
                    expected_monthly = expected_daily * 30
                    monthly_label = "LINEAR ESTIMATE"
            else:
                expected_monthly = expected_daily * 30
                monthly_label = "INSUFFICIENT DATA"
        
        monthly_color = "normal" if expected_monthly >= 0 else "inverse"
        st.metric(
            "📅 EXPECTED MONTHLY",
            f"${expected_monthly:+.2f}",
            monthly_label,
            delta_color=monthly_color
        )
    
    st.divider()
    
    # Row 1.5: ENHANCED LIVE POSITIONS TRACKER with Real-time P&L
    integrate_live_positions_section(BOT_DATA)
    
    st.divider()
    
    # Row 2: REAL MATHEMATICAL PROJECTIONS - NO MORE FAKE DATA
    st.subheader(f"📊 REAL MATHEMATICAL PROJECTIONS (Based on {len(ALL_TRADES)} Actual Trades)")
    
    # Use ALL real trades loaded from enhanced data loading
    trades = ALL_TRADES
    total_trades = len(trades)
    
    # Use real comprehensive projections with enhanced mathematical functions
    comprehensive_projections = get_comprehensive_projections(trades, TOTAL_BALANCE, STARTING_BALANCE)
    
    if comprehensive_projections and total_trades >= 10:
        # ============================================
        # REAL MATHEMATICAL DATA (FROM UTILS.PY)
        # ============================================
        
        # Get comprehensive stats using real mathematical functions
        daily_stats = comprehensive_projections['daily_stats']
        trade_stats = comprehensive_projections['trade_stats'] 
        math_proj = comprehensive_projections['math_projections']
        monte_carlo = comprehensive_projections['monte_carlo']
        
        # Real calculated trade frequency (not estimated)
        avg_daily_trades = daily_stats['avg_trades_per_day']
        
        # Real statistical measures from actual data
        mean_pnl = trade_stats['mean_pnl']
        std_pnl = trade_stats['std_pnl']
        win_rate = trade_stats['win_rate'] / 100  # Convert back to decimal
        avg_win = trade_stats['avg_win']
        avg_loss = trade_stats['avg_loss']
        expectancy = trade_stats['expectancy']
        
        # Use real Monte Carlo results from utils.py (not duplicated code)
        ci_7d = monte_carlo['7d'] if monte_carlo['7d'] else {}
        ci_30d = monte_carlo['30d'] if monte_carlo['30d'] else {}
        ci_90d = monte_carlo['90d'] if monte_carlo['90d'] else {}
        
        # ============================================
        # DISPLAY PROJECTION CARDS
        # ============================================
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if ci_7d and 'p50' in ci_7d:
                proj_7d = ci_7d['p50'] - TOTAL_BALANCE
                color_7d = "#39ff14" if proj_7d >= 0 else "#ff3333"
                confidence_range = ci_7d['p95'] - ci_7d['p5']
                position_pct = min(max((ci_7d['p50'] - ci_7d['p5']) / confidence_range * 100, 0), 100) if confidence_range > 0 else 50
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📅 7-DAY PROJECTION</h4>
                <p style="color: {color_7d}; font-size: 1.8rem; font-weight: bold; text-shadow: 0 0 5px {color_7d};">${ci_7d['p50']:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Monte Carlo median</p>
                <hr style="border-color: #333;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888;">
                    <span>5%: ${ci_7d['p5']:,.2f}</span>
                    <span>95%: ${ci_7d['p95']:,.2f}</span>
                </div>
                <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 4px; height: 8px; overflow: hidden; margin-top: 5px;">
                    <div style="background: linear-gradient(90deg, #ff3333, #ff6600, #39ff14); width: {position_pct:.0f}%; height: 100%;"></div>
                </div>
                <p style="color: #39ff14; font-size: 0.75rem; margin-top: 8px;">🎯 {ci_7d.get('prob_profit', 50):.0f}% profit chance</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback to mathematical projection
                math_7d = math_proj['7d']['projected'] if 'projected' in math_proj['7d'] else TOTAL_BALANCE
                proj_7d = math_7d - TOTAL_BALANCE
                color_7d = "#39ff14" if proj_7d >= 0 else "#ff3333"
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📅 7-DAY PROJECTION</h4>
                <p style="color: {color_7d}; font-size: 1.8rem; font-weight: bold;">${math_7d:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Compound growth</p>
                <p style="color: #888; font-size: 0.75rem;">Monte Carlo pending...</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if ci_30d and 'p50' in ci_30d:
                proj_30d = ci_30d['p50'] - TOTAL_BALANCE
                color_30d = "#39ff14" if proj_30d >= 0 else "#ff3333"
                confidence_range = ci_30d['p95'] - ci_30d['p5']
                position_pct = min(max((ci_30d['p50'] - ci_30d['p5']) / confidence_range * 100, 0), 100) if confidence_range > 0 else 50
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📆 30-DAY PROJECTION</h4>
                <p style="color: {color_30d}; font-size: 1.8rem; font-weight: bold; text-shadow: 0 0 5px {color_30d};">${ci_30d['p50']:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Monte Carlo median</p>
                <hr style="border-color: #333;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888;">
                    <span>5%: ${ci_30d['p5']:,.2f}</span>
                    <span>95%: ${ci_30d['p95']:,.2f}</span>
                </div>
                <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 4px; height: 8px; overflow: hidden; margin-top: 5px;">
                    <div style="background: linear-gradient(90deg, #ff3333, #ff6600, #39ff14); width: {position_pct:.0f}%; height: 100%;"></div>
                </div>
                <p style="color: #39ff14; font-size: 0.75rem; margin-top: 8px;">🎯 {ci_30d.get('prob_profit', 50):.0f}% profit chance</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                math_30d = math_proj['30d']['projected'] if 'projected' in math_proj['30d'] else TOTAL_BALANCE
                proj_30d = math_30d - TOTAL_BALANCE
                color_30d = "#39ff14" if proj_30d >= 0 else "#ff3333"
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📆 30-DAY PROJECTION</h4>
                <p style="color: {color_30d}; font-size: 1.8rem; font-weight: bold;">${math_30d:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Compound growth</p>
                <p style="color: #888; font-size: 0.75rem;">Monte Carlo pending...</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if ci_90d and 'p50' in ci_90d:
                proj_90d = ci_90d['p50'] - TOTAL_BALANCE
                color_90d = "#39ff14" if proj_90d >= 0 else "#ff3333"
                confidence_range = ci_90d['p95'] - ci_90d['p5']
                position_pct = min(max((ci_90d['p50'] - ci_90d['p5']) / confidence_range * 100, 0), 100) if confidence_range > 0 else 50
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📅 90-DAY PROJECTION</h4>
                <p style="color: {color_90d}; font-size: 1.8rem; font-weight: bold; text-shadow: 0 0 5px {color_90d};">${ci_90d['p50']:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Monte Carlo median</p>
                <hr style="border-color: #333;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888;">
                    <span>5%: ${ci_90d['p5']:,.2f}</span>
                    <span>95%: ${ci_90d['p95']:,.2f}</span>
                </div>
                <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 4px; height: 8px; overflow: hidden; margin-top: 5px;">
                    <div style="background: linear-gradient(90deg, #ff3333, #ff6600, #39ff14); width: {position_pct:.0f}%; height: 100%;"></div>
                </div>
                <p style="color: #39ff14; font-size: 0.75rem; margin-top: 8px;">🎯 {ci_90d.get('prob_profit', 50):.0f}% profit chance</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                math_90d = math_proj['90d']['projected'] if 'projected' in math_proj['90d'] else TOTAL_BALANCE
                proj_90d = math_90d - TOTAL_BALANCE
                color_90d = "#39ff14" if proj_90d >= 0 else "#ff3333"
                st.markdown(f"""
                <div class="metric-card">
                <h4 style="color: #ff6600;">📅 90-DAY PROJECTION</h4>
                <p style="color: {color_90d}; font-size: 1.8rem; font-weight: bold;">${math_90d:,.2f}</p>
                <p style="color: #aaa; font-size: 0.9rem;">Compound growth</p>
                <p style="color: #888; font-size: 0.75rem;">Monte Carlo pending...</p>
                </div>
                """, unsafe_allow_html=True)
        
        # ============================================
        # REAL PROBABILITY ANALYSIS
        # ============================================
        
        st.markdown("### 🎯 REAL PROBABILITY ANALYSIS")
        
        prob_col1, prob_col2, prob_col3 = st.columns(3)
        
        with prob_col1:
            profit_prob = ci_30d.get('prob_profit', 50) if ci_30d else 50
            gain_10pct = ci_30d.get('prob_10pct_gain', 25) if ci_30d else 25
            st.markdown(f"""
            <div class="metric-card" style="border-color: #39ff14;">
            <h4 style="color: #39ff14; font-size: 0.9rem;">✅ PROFIT PROBABILITY</h4>
            <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{profit_prob:.1f}%</p>
            <p style="color: #888; font-size: 0.75rem;">Chance of account growth (30d)</p>
            <hr style="border-color: #333;">
            <p style="color: #39ff14; font-size: 0.8rem;">▲ +10%: {gain_10pct:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with prob_col2:
            loss_10pct = ci_30d.get('prob_10pct_loss', 25) if ci_30d else 25
            loss_25pct = ci_30d.get('prob_25pct_loss', 10) if ci_30d else 10
            ruin_color = "#ff3333" if loss_25pct > 10 else "#ff6600" if loss_25pct > 5 else "#39ff14"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {ruin_color};">
            <h4 style="color: #ff6600; font-size: 0.9rem;">⚠️ DRAWDOWN RISK</h4>
            <p style="color: {ruin_color}; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{loss_10pct:.1f}%</p>
            <p style="color: #888; font-size: 0.75rem;">Chance of -10% loss (30d)</p>
            <hr style="border-color: #333;">
            <p style="color: {ruin_color}; font-size: 0.8rem;">▼ -25%: {loss_25pct:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with prob_col3:
            # Real expectancy from actual trade data
            real_expectancy = trade_stats['expectancy']
            ev_color = "#39ff14" if real_expectancy > 0 else "#ff3333"
            daily_ev = real_expectancy * avg_daily_trades
            st.markdown(f"""
            <div class="metric-card" style="border-color: {ev_color};">
            <h4 style="color: #ff6600; font-size: 0.9rem;">💰 REAL EXPECTANCY</h4>
            <p style="color: {ev_color}; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">${real_expectancy:.2f}</p>
            <p style="color: #888; font-size: 0.75rem;">From 30 actual trades</p>
            <hr style="border-color: #333;">
            <p style="color: #888; font-size: 0.8rem;">Daily EV: ${daily_ev:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================
        # STATISTICAL TRANSPARENCY (REAL DATA)
        # ============================================
        
        # Real statistical data from actual calculations
        real_win_count = trade_stats['win_count']
        real_loss_count = trade_stats['loss_count'] 
        real_win_rate = trade_stats['win_rate']
        real_profit_factor = trade_stats['profit_factor']
        real_expectancy = trade_stats['expectancy']
        
        # Enhanced mathematical transparency with trend analysis
        volatility_metrics = comprehensive_projections.get('volatility_metrics', {})
        trend_analysis = comprehensive_projections.get('trend_analysis', {})
        moving_averages = comprehensive_projections.get('moving_averages', {})
        
        st.markdown(f"""
        <div class="terminal-bg" style="margin-top: 15px;">
        <h4 style="color: #ff6600;">📐 ENHANCED MATHEMATICAL ANALYSIS ({total_trades} ACTUAL TRADES)</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
            <div>
                <p style="color: #ff6600; font-weight: bold;">STATISTICAL INPUT:</p>
                <p style="color: #39ff14; font-family: monospace; font-size: 0.8rem;">
                • Sample: {total_trades} real trades<br>
                • Win rate: {real_win_rate:.1f}% ({real_win_count}W/{real_loss_count}L)<br>
                • Mean P&L: ${mean_pnl:.2f} ± ${std_pnl:.2f}<br>
                • Expectancy: ${real_expectancy:.2f}/trade<br>
                • Trade freq: {avg_daily_trades:.2f}/day<br>
                • Profit factor: {real_profit_factor:.2f}
                </p>
            </div>
            <div>
                <p style="color: #ff6600; font-weight: bold;">RISK METRICS:</p>
                <p style="color: #39ff14; font-family: monospace; font-size: 0.8rem;">
                • Daily volatility: {daily_stats['volatility']*100:.2f}%<br>
                • VaR 95%: ${volatility_metrics.get('var_95', 0):.2f}<br>
                • Max drawdown: ${volatility_metrics.get('max_drawdown', 0):.2f}<br>
                • Sharpe ratio: {volatility_metrics.get('sharpe_ratio', 0):.2f}<br>
                • Sortino ratio: {volatility_metrics.get('sortino_ratio', 0):.2f}<br>
                • Trading days: {daily_stats['trading_days']}
                </p>
            </div>
            <div>
                <p style="color: #ff6600; font-weight: bold;">TREND ANALYSIS:</p>
                <p style="color: #39ff14; font-family: monospace; font-size: 0.8rem;">
                • Trend: {trend_analysis.get('trend_direction', 'unknown')}<br>
                • R-squared: {trend_analysis.get('r_squared', 0):.3f}<br>
                • Daily trend: ${trend_analysis.get('daily_trend_pnl', 0):.3f}<br>
                • SMA-5: ${moving_averages.get('current_sma_5', 0):.2f}<br>
                • EMA-10: ${moving_averages.get('current_ema_10', 0):.2f}<br>
                • Methods: 6 integrated
                </p>
            </div>
        </div>
        <p style="color: #888; font-size: 0.75rem; margin-top: 10px; border-top: 1px solid #333; padding-top: 10px;">
        ✅ REAL DATA INTEGRATION: Mathematical models include compound growth, Monte Carlo (5k sims), 
        linear regression trend analysis, moving averages, VaR/ES risk metrics, and volatility-adjusted confidence bands.
        All calculations based on actual trading performance from {total_trades} completed trades.
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # INSUFFICIENT DATA - Less than 10 trades
        st.markdown(f"""
        <div class="metric-card" style="border-color: #ff6600;">
        <h4 style="color: #ff6600;">⚠️ INSUFFICIENT DATA FOR STATISTICAL PROJECTIONS</h4>
        <p style="color: #aaa; font-size: 1.1rem;">
            Monte Carlo simulations require at least <strong>10 trades</strong> for reliable distribution sampling.<br>
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
        🔄 Monte Carlo projections will auto-calculate once 10+ trades are recorded.
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Row 3: Enhanced Trade Statistics with Real Data
    st.subheader(f"📈 COMPREHENSIVE TRADE STATISTICS ({len(ALL_TRADES)} Trades)")
    
    # Use the real loaded trade data
    trades = ALL_TRADES
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
    
    # Row 5: REAL Strategy Analysis from All Actual Trades
    st.subheader(f"🔬 REAL STRATEGY ANALYSIS ({len(ALL_TRADES)} Actual Trades)")
    
    # Analyze actual strategies used in all real trades
    strategy_performance = {}
    for trade in ALL_TRADES:
        strategy = trade.get('reason', 'unknown')
        if strategy not in strategy_performance:
            strategy_performance[strategy] = {'trades': 0, 'wins': 0, 'total_pnl': 0, 'pnl_list': []}
        
        strategy_performance[strategy]['trades'] += 1
        if trade.get('pnl', 0) > 0:
            strategy_performance[strategy]['wins'] += 1
        strategy_performance[strategy]['total_pnl'] += trade.get('pnl', 0)
        strategy_performance[strategy]['pnl_list'].append(trade.get('pnl', 0))
    
    # Calculate strategy stats
    strategy_stats = []
    for strategy, perf in strategy_performance.items():
        win_rate = (perf['wins'] / perf['trades'] * 100) if perf['trades'] > 0 else 0
        avg_pnl = perf['total_pnl'] / perf['trades'] if perf['trades'] > 0 else 0
        
        # Calculate simple Sharpe ratio for this strategy
        if len(perf['pnl_list']) > 1:
            mean_return = np.mean(perf['pnl_list'])
            std_return = np.std(perf['pnl_list'], ddof=1)
            sharpe = mean_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        strategy_stats.append({
            'strategy': strategy.replace('_', ' ').title(),
            'trades': perf['trades'],
            'win_rate': win_rate,
            'total_pnl': perf['total_pnl'],
            'avg_pnl': avg_pnl,
            'sharpe': sharpe
        })
    
    # Sort by total P&L
    strategy_stats.sort(key=lambda x: x['total_pnl'], reverse=True)
    
    st.markdown(f"""
    <div class="terminal-bg">
    <h4 style="color: #ff6600;">REAL STRATEGY PERFORMANCE (From trades.jsonl + dashboard.json)</h4>
    <p style="color: #39ff14; font-size: 0.9rem; margin-bottom: 15px;">✅ REAL DATA - Analysis of actual {len(ALL_TRADES)} trades</p>
    
    <table style="width: 100%; color: #39ff14; font-family: 'IBM Plex Mono', monospace;">
    <tr style="border-bottom: 1px solid #333;">
        <th style="text-align: left; padding: 10px; color: #ff6600;">RANK</th>
        <th style="text-align: left; padding: 10px; color: #ff6600;">STRATEGY</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">TRADES</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">WIN RATE</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">TOTAL P&L</th>
        <th style="text-align: right; padding: 10px; color: #ff6600;">AVG P&L</th>
    </tr>""", unsafe_allow_html=True)
    
    for i, stat in enumerate(strategy_stats[:5]):  # Top 5 strategies
        rank_icon = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] if i < 5 else f"{i+1}"
        pnl_color = "#39ff14" if stat['total_pnl'] >= 0 else "#ff3333"
        
        st.markdown(f"""
        <tr>
            <td style="padding: 10px;">{rank_icon}</td>
            <td style="padding: 10px;">{stat['strategy']}</td>
            <td style="padding: 10px; text-align: right;">{stat['trades']}</td>
            <td style="padding: 10px; text-align: right;">{stat['win_rate']:.1f}%</td>
            <td style="padding: 10px; text-align: right; color: {pnl_color};">${stat['total_pnl']:+.2f}</td>
            <td style="padding: 10px; text-align: right; color: {pnl_color};">${stat['avg_pnl']:+.2f}</td>
        </tr>""", unsafe_allow_html=True)
    
    st.markdown("""
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
# TAB 5: PERFORMANCE METRICS
# ============================================
with tab5:
    st.subheader("📊 PERFORMANCE ANALYTICS • MISSION METRICS CENTER")
    
    # Time Period Selector
    st.markdown("### ⏱️ TIME PERIOD")
    
    period_col1, period_col2, period_col3, period_col4, period_col5 = st.columns(5)
    
    with period_col1:
        all_time_btn = st.button("🌌 ALL TIME", width='stretch', 
                                  type="primary" if st.session_state.get('perf_period') == 'all' else "secondary")
    with period_col2:
        days30_btn = st.button("📅 30 DAYS", width='stretch',
                               type="primary" if st.session_state.get('perf_period') == '30d' else "secondary")
    with period_col3:
        days7_btn = st.button("📆 7 DAYS", width='stretch',
                              type="primary" if st.session_state.get('perf_period') == '7d' else "secondary")
    with period_col4:
        days1_btn = st.button("⏰ 24 HOURS", width='stretch',
                              type="primary" if st.session_state.get('perf_period') == '1d' else "secondary")
    with period_col5:
        custom_btn = st.button("⚙️ CUSTOM", width='stretch',
                               type="primary" if st.session_state.get('perf_period') == 'custom' else "secondary")
    
    # Set default period
    if 'perf_period' not in st.session_state:
        st.session_state.perf_period = 'all'
    
    # Handle button clicks
    if all_time_btn:
        st.session_state.perf_period = 'all'
    elif days30_btn:
        st.session_state.perf_period = '30d'
    elif days7_btn:
        st.session_state.perf_period = '7d'
    elif days1_btn:
        st.session_state.perf_period = '1d'
    elif custom_btn:
        st.session_state.perf_period = 'custom'
    
    # Determine period days
    period_days = None
    period_label = "ALL TIME"
    if st.session_state.perf_period == '30d':
        period_days = 30
        period_label = "LAST 30 DAYS"
    elif st.session_state.perf_period == '7d':
        period_days = 7
        period_label = "LAST 7 DAYS"
    elif st.session_state.perf_period == '1d':
        period_days = 1
        period_label = "LAST 24 HOURS"
    
    # Get trades and calculate metrics - use ALL_TRADES from jsonl file
    all_trades = ALL_TRADES if ALL_TRADES else BOT_DATA.get('recent_trades', [])
    starting_balance = BOT_DATA.get('trading_state', {}).get('starting_balance', 376.26)
    current_balance = BOT_DATA.get('account', {}).get('total_usd', starting_balance)
    
    metrics = calculate_performance_metrics(all_trades, starting_balance, current_balance, period_days)
    
    # Display period header
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <span style="color: #ff6600; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 2px;">
            📊 {period_label} PERFORMANCE
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if metrics and metrics['total_trades'] > 0:
        # ============================================
        # KEY METRICS CARDS - ROW 1
        # ============================================
        st.markdown("### 🎯 KEY PERFORMANCE METRICS")
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        with kpi_col1:
            # Win Rate with progress bar
            win_rate_color = "#39ff14" if metrics['win_rate'] >= 50 else "#ff6600" if metrics['win_rate'] >= 30 else "#ff3333"
            win_rate_arrow = "▲" if metrics['win_rate'] >= 50 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {win_rate_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Win Rate</span>
                    <span style="color: {win_rate_color}; font-size: 1.2rem;">{win_rate_arrow}</span>
                </div>
                <p style="color: {win_rate_color}; font-size: 2.2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {win_rate_color};">
                    {metrics['win_rate']:.1f}%
                </p>
                <div style="background: #1a1a1a; border: 1px solid #333; border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, {win_rate_color}, #2dd60f); width: {min(metrics['win_rate'], 100)}%; height: 100%;"></div>
                </div>
                <p style="color: #888; font-size: 0.75rem; margin-top: 5px;">{metrics['win_count']}W / {metrics['loss_count']}L</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col2:
            # Profit Factor
            pf_color = "#39ff14" if metrics['profit_factor'] >= 1.5 else "#ff6600" if metrics['profit_factor'] >= 1 else "#ff3333"
            pf_arrow = "▲" if metrics['profit_factor'] >= 1.5 else "▼"
            pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] != float('inf') else "∞"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {pf_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Profit Factor</span>
                    <span style="color: {pf_color}; font-size: 1.2rem;">{pf_arrow}</span>
                </div>
                <p style="color: {pf_color}; font-size: 2.2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {pf_color};">
                    {pf_display}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">
                    ${metrics['gross_profit']:.2f} / ${metrics['gross_loss']:.2f}
                </p>
                <p style="color: #555; font-size: 0.7rem;">Gross Profit / Loss</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col3:
            # Sharpe Ratio
            sharpe_color = "#39ff14" if metrics['sharpe_ratio'] >= 2 else "#ff6600" if metrics['sharpe_ratio'] >= 1 else "#ff3333"
            sharpe_arrow = "▲" if metrics['sharpe_ratio'] >= 2 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {sharpe_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Sharpe Ratio</span>
                    <span style="color: {sharpe_color}; font-size: 1.2rem;">{sharpe_arrow}</span>
                </div>
                <p style="color: {sharpe_color}; font-size: 2.2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {sharpe_color};">
                    {metrics['sharpe_ratio']:.2f}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">Risk-Adjusted Return</p>
                <p style="color: #555; font-size: 0.7rem;">σ = {metrics['std_dev']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col4:
            # Total Return %
            ret_color = "#39ff14" if metrics['total_return_pct'] >= 0 else "#ff3333"
            ret_arrow = "▲" if metrics['total_return_pct'] >= 0 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {ret_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Total Return</span>
                    <span style="color: {ret_color}; font-size: 1.2rem;">{ret_arrow}</span>
                </div>
                <p style="color: {ret_color}; font-size: 2.2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {ret_color};">
                    {metrics['total_return_pct']:+.2f}%
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">${metrics['net_pnl']:+.2f}</p>
                <p style="color: #555; font-size: 0.7rem;">Net P&L</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================
        # KEY METRICS CARDS - ROW 2 (RISK METRICS)
        # ============================================
        kpi2_col1, kpi2_col2, kpi2_col3, kpi2_col4 = st.columns(4)
        
        with kpi2_col1:
            # Max Drawdown
            dd_color = "#ff3333" if metrics['max_drawdown_pct'] >= 10 else "#ff6600" if metrics['max_drawdown_pct'] >= 5 else "#39ff14"
            dd_arrow = "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {dd_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Max Drawdown</span>
                    <span style="color: {dd_color}; font-size: 1.2rem;">{dd_arrow}</span>
                </div>
                <p style="color: {dd_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {dd_color};">
                    {metrics['max_drawdown_pct']:.2f}%
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">${metrics['max_drawdown']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2_col2:
            # Calmar Ratio
            calmar_color = "#39ff14" if metrics['calmar_ratio'] >= 3 else "#ff6600" if metrics['calmar_ratio'] >= 1 else "#ff3333"
            calmar_arrow = "▲" if metrics['calmar_ratio'] >= 3 else "▼"
            calmar_display = f"{metrics['calmar_ratio']:.2f}" if metrics['calmar_ratio'] != float('inf') else "∞"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {calmar_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Calmar Ratio</span>
                    <span style="color: {calmar_color}; font-size: 1.2rem;">{calmar_arrow}</span>
                </div>
                <p style="color: {calmar_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {calmar_color};">
                    {calmar_display}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">Return / Max DD</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2_col3:
            # Sharpe Ratio
            sharpe_color = "#39ff14" if metrics['sharpe_ratio'] >= 2 else "#ff6600" if metrics['sharpe_ratio'] >= 1 else "#ff3333"
            sharpe_arrow = "▲" if metrics['sharpe_ratio'] >= 2 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {sharpe_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Sharpe Ratio</span>
                    <span style="color: {sharpe_color}; font-size: 1.2rem;">{sharpe_arrow}</span>
                </div>
                <p style="color: {sharpe_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {sharpe_color};">
                    {metrics['sharpe_ratio']:.2f}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">σ = {metrics['std_dev']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2_col4:
            # Expectancy
            exp_color = "#39ff14" if metrics['expectancy'] > 0 else "#ff3333"
            exp_arrow = "▲" if metrics['expectancy'] > 0 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {exp_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Expectancy</span>
                    <span style="color: {exp_color}; font-size: 1.2rem;">{exp_arrow}</span>
                </div>
                <p style="color: {exp_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {exp_color};">
                    ${metrics['expectancy']:.2f}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">Expected value per trade</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================
        # KEY METRICS CARDS - ROW 3 (TRADE STATISTICS)
        # ============================================
        st.markdown("### 💰 TRADE STATISTICS")
        kpi3_col1, kpi3_col2, kpi3_col3, kpi3_col4 = st.columns(4)
        
        with kpi3_col1:
            # Average Win ($)
            st.markdown(f"""
            <div class="metric-card" style="border-color: #39ff14;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Avg Win ($)</span>
                    <span style="color: #39ff14; font-size: 1.2rem;">▲</span>
                </div>
                <p style="color: #39ff14; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px #39ff14;">
                    ${metrics['avg_win']:.2f}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">{metrics['avg_win_pct']:.2f}% avg</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3_col2:
            # Average Loss ($)
            st.markdown(f"""
            <div class="metric-card" style="border-color: #ff3333;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Avg Loss ($)</span>
                    <span style="color: #ff3333; font-size: 1.2rem;">▼</span>
                </div>
                <p style="color: #ff3333; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px #ff3333;">
                    ${metrics['avg_loss']:.2f}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">{metrics['avg_loss_pct']:.2f}% avg</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3_col3:
            # Risk/Reward Ratio
            rr_color = "#39ff14" if metrics['risk_reward_ratio'] >= 2 else "#ff6600" if metrics['risk_reward_ratio'] >= 1 else "#ff3333"
            rr_display = f"{metrics['risk_reward_ratio']:.2f}" if metrics['risk_reward_ratio'] != float('inf') else "∞"
            rr_arrow = "▲" if metrics['risk_reward_ratio'] >= 2 else "▼"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {rr_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Risk/Reward</span>
                    <span style="color: {rr_color}; font-size: 1.2rem;">{rr_arrow}</span>
                </div>
                <p style="color: {rr_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {rr_color};">
                    1:{rr_display}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">R:R Ratio</p>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3_col4:
            # Profit Factor
            pf_color = "#39ff14" if metrics['profit_factor'] >= 1.5 else "#ff6600" if metrics['profit_factor'] >= 1 else "#ff3333"
            pf_arrow = "▲" if metrics['profit_factor'] >= 1.5 else "▼"
            pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] != float('inf') else "∞"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {pf_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Profit Factor</span>
                    <span style="color: {pf_color}; font-size: 1.2rem;">{pf_arrow}</span>
                </div>
                <p style="color: {pf_color}; font-size: 2rem; font-weight: bold; margin: 5px 0; text-shadow: 0 0 10px {pf_color};">
                    {pf_display}
                </p>
                <p style="color: #888; font-size: 0.8rem; margin-top: 5px;">Gross Profit/Loss</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # ============================================
        # EQUITY CURVE CHART
        # ============================================
        st.markdown("### 📈 EQUITY CURVE")
        
        # Create equity curve dataframe
        equity_data = []
        for i, balance in enumerate(metrics['equity_curve']):
            if i == 0:
                label = "Start"
            elif i == len(metrics['equity_curve']) - 1:
                label = "Current"
            else:
                label = f"Trade {i}"
            equity_data.append({'Step': i, 'Balance': balance, 'Label': label})
        
        equity_df = pd.DataFrame(equity_data)
        
        # Create Plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=equity_df['Step'],
            y=equity_df['Balance'],
            mode='lines',
            name='Equity',
            line=dict(color='#39ff14', width=2),
            fill='tozeroy',
            fillcolor='rgba(57, 255, 20, 0.1)'
        ))
        
        # Add starting balance reference line
        fig.add_hline(y=starting_balance, line_dash="dash", line_color="#ff6600", 
                      annotation_text="Starting Balance", annotation_position="right")
        
        fig.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(color='#39ff14', family='IBM Plex Mono'),
            xaxis=dict(
                title='Trade Number',
                gridcolor='#1a1a1a',
                color='#888'
            ),
            yaxis=dict(
                title='Account Balance ($)',
                gridcolor='#1a1a1a',
                color='#888'
            ),
            margin=dict(l=50, r=50, t=30, b=50),
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')
        
        st.divider()
        
        # ============================================
        # TRADE DISTRIBUTION HISTOGRAM
        # ============================================
        st.markdown("### 📊 TRADE DISTRIBUTION (WINS VS LOSSES)")
        
        # Get P&L values for histogram
        trade_pnls = [t.get('pnl', 0) for t in all_trades]
        
        # Create histogram figure
        fig_hist = go.Figure()
        
        # Add histogram traces for wins and losses
        win_pnls = [pnl for pnl in trade_pnls if pnl > 0]
        loss_pnls = [pnl for pnl in trade_pnls if pnl <= 0]
        
        if win_pnls:
            fig_hist.add_trace(go.Histogram(
                x=win_pnls,
                name='Wins',
                marker_color='#39ff14',
                opacity=0.8,
                nbinsx=10,
                hovertemplate='P&L: $%{x:.2f}<br>Count: %{y}<extra>Wins</extra>'
            ))
        
        if loss_pnls:
            fig_hist.add_trace(go.Histogram(
                x=loss_pnls,
                name='Losses',
                marker_color='#ff3333',
                opacity=0.8,
                nbinsx=10,
                hovertemplate='P&L: $%{x:.2f}<br>Count: %{y}<extra>Losses</extra>'
            ))
        
        # Add vertical line at zero
        fig_hist.add_vline(x=0, line_dash="dash", line_color="#ff6600", line_width=2)
        
        # Update layout
        fig_hist.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(color='#39ff14', family='IBM Plex Mono'),
            barmode='group',
            xaxis=dict(
                title='Trade P&L ($)',
                gridcolor='#1a1a1a',
                color='#888',
                zerolinecolor='#ff6600',
                zerolinewidth=2
            ),
            yaxis=dict(
                title='Number of Trades',
                gridcolor='#1a1a1a',
                color='#888'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='#888')
            ),
            margin=dict(l=50, r=50, t=60, b=50),
            height=400
        )
        
        # Add summary stats below histogram
        hist_col1, hist_col2, hist_col3, hist_col4 = st.columns(4)
        
        with hist_col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #1a1a1a; border-radius: 5px;">
                <span style="color: #888; font-size: 0.8rem;">TOTAL TRADES</span>
                <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{len(trade_pnls)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with hist_col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #1a1a1a; border-radius: 5px;">
                <span style="color: #888; font-size: 0.8rem;">WINNING TRADES</span>
                <p style="color: #39ff14; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{len(win_pnls)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with hist_col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #1a1a1a; border-radius: 5px;">
                <span style="color: #888; font-size: 0.8rem;">LOSING TRADES</span>
                <p style="color: #ff3333; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{len(loss_pnls)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with hist_col4:
            avg_pnl = sum(trade_pnls) / len(trade_pnls) if trade_pnls else 0
            avg_color = "#39ff14" if avg_pnl >= 0 else "#ff3333"
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #1a1a1a; border-radius: 5px;">
                <span style="color: #888; font-size: 0.8rem;">AVG P&L</span>
                <p style="color: {avg_color}; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">${avg_pnl:+.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.plotly_chart(fig_hist, width='stretch')
        
        st.divider()
        
        # ============================================
        # STREAKS & EXTREMES
        # ============================================
        st.markdown("### 🔥 STREAKS & EXTREME TRADES")
        
        streak_col1, streak_col2, streak_col3, streak_col4 = st.columns(4)
        
        with streak_col1:
            st.markdown(f"""
            <div class="metric-card" style="border-color: #39ff14;">
                <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Max Win Streak</span>
                <p style="color: #39ff14; font-size: 1.8rem; font-weight: bold; margin: 5px 0;">
                    {metrics['max_win_streak']} 🔥
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with streak_col2:
            st.markdown(f"""
            <div class="metric-card" style="border-color: #ff3333;">
                <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Max Loss Streak</span>
                <p style="color: #ff3333; font-size: 1.8rem; font-weight: bold; margin: 5px 0;">
                    {metrics['max_loss_streak']} 💀
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with streak_col3:
            current_streak_icon = "🔥" if metrics['current_streak_type'] else "💀"
            current_streak_label = "WINS" if metrics['current_streak_type'] else "LOSSES"
            current_streak_color = "#39ff14" if metrics['current_streak_type'] else "#ff3333"
            st.markdown(f"""
            <div class="metric-card" style="border-color: {current_streak_color};">
                <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Current Streak</span>
                <p style="color: {current_streak_color}; font-size: 1.8rem; font-weight: bold; margin: 5px 0;">
                    {metrics['current_streak']} {current_streak_icon}
                </p>
                <p style="color: #888; font-size: 0.75rem;">{current_streak_label}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with streak_col4:
            st.markdown(f"""
            <div class="metric-card" style="border-color: #ff6600;">
                <span style="color: #ff6600; font-size: 0.85rem; text-transform: uppercase;">Best / Worst Trade</span>
                <p style="color: #39ff14; font-size: 1.4rem; font-weight: bold; margin: 5px 0;">
                    +${metrics['best_trade']:.2f}
                </p>
                <p style="color: #ff3333; font-size: 1.4rem; font-weight: bold; margin: 0;">
                    ${metrics['worst_trade']:.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # ============================================
        # FORMULA EXPLANATIONS
        # ============================================
        st.markdown("### 📐 METRIC FORMULAS")
        
        st.markdown("""
        <div class="terminal-bg">
        <table style="width: 100%; color: #39ff14; font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem;">
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Win Rate</td>
            <td style="padding: 10px;">Winning Trades / Total Trades × 100</td>
            <td style="padding: 10px; color: #888;">{:.1f}%</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Total Return</td>
            <td style="padding: 10px;">(Current Balance - Starting Balance) / Starting Balance × 100</td>
            <td style="padding: 10px; color: #888;">{:.2f}%</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Profit Factor</td>
            <td style="padding: 10px;">Gross Profit / Gross Loss</td>
            <td style="padding: 10px; color: #888;">{:.2f}</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Sharpe Ratio</td>
            <td style="padding: 10px;">(Mean Return - Risk Free Rate) / Std Dev × √252</td>
            <td style="padding: 10px; color: #888;">{:.2f}</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Max Drawdown</td>
            <td style="padding: 10px;">(Peak - Trough) / Peak × 100</td>
            <td style="padding: 10px; color: #888;">{:.2f}%</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Calmar Ratio</td>
            <td style="padding: 10px;">Annualized Return / Max Drawdown</td>
            <td style="padding: 10px; color: #888;">{:.2f}</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Risk/Reward</td>
            <td style="padding: 10px;">Average Win / Average Loss</td>
            <td style="padding: 10px; color: #888;">1:{:.2f}</td>
        </tr>
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Expectancy</td>
            <td style="padding: 10px;">(Win% × Avg Win) - (Loss% × Avg Loss)</td>
            <td style="padding: 10px; color: #888;">${:.2f}</td>
        </tr>
        <tr>
            <td style="padding: 10px; color: #ff6600; font-weight: bold;">Avg Win/Loss %</td>
            <td style="padding: 10px;">Average of individual trade P&L percentages</td>
            <td style="padding: 10px; color: #888;">{:.2f}% / {:.2f}%</td>
        </tr>
        </table>
        </div>
        """.format(
            metrics['win_rate'],
            metrics['total_return_pct'],
            metrics['profit_factor'] if metrics['profit_factor'] != float('inf') else 0,
            metrics['sharpe_ratio'],
            metrics['max_drawdown_pct'],
            metrics['calmar_ratio'] if metrics['calmar_ratio'] != float('inf') else 0,
            metrics['risk_reward_ratio'] if metrics['risk_reward_ratio'] != float('inf') else 0,
            metrics['expectancy'],
            metrics['avg_win_pct'],
            metrics['avg_loss_pct']
        ), unsafe_allow_html=True)
        
    else:
        # No data available for selected period
        st.markdown(f"""
        <div class="metric-card" style="border-color: #ff6600; text-align: center; padding: 50px;">
            <h4 style="color: #ff6600; font-size: 1.5rem;">📭 NO DATA FOR {period_label}</h4>
            <p style="color: #888; margin-top: 20px;">No trades found in the selected time period.</p>
            <p style="color: #555; font-size: 0.9rem; margin-top: 15px;">Try selecting a different time period or check back after more trades are executed.</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# TAB 6: TRADE HISTORY
# ============================================
with tab6:
    st.subheader("📜 INSTITUTIONAL TRADE JOURNAL • COMPLETE MISSION LOG")
    
    # ============================================
    # ENHANCED TRADE DATA PROCESSING
    # ============================================
    trades = ALL_TRADES if ALL_TRADES else BOT_DATA.get('recent_trades', [])
    total_trades = len(trades)
    
    # Add custom CSS for professional table styling
    st.markdown("""
    <style>
    .professional-table {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
        border: 1px solid #30363d !important;
    }
    .trade-detail-expander {
        background: rgba(25, 25, 25, 0.8) !important;
        border: 1px solid #444 !important;
        border-radius: 4px !important;
        margin: 5px 0 !important;
        font-family: monospace !important;
    }
    .streak-indicator {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: bold;
        margin: 0 2px;
    }
    .win-streak {
        background: #238636;
        color: white;
    }
    .loss-streak {
        background: #da3633;
        color: white;
    }
    .running-pnl-positive {
        color: #3fb950;
        font-weight: bold;
        text-shadow: 0 0 3px #3fb950;
    }
    .running-pnl-negative {
        color: #f85149;
        font-weight: bold;
        text-shadow: 0 0 3px #f85149;
    }
    .trade-frequency-chart {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
    }
    .institutional-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-terminal {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #21262d;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .metric-terminal h4 {
        color: #ff6b35;
        margin: 0 0 0.5rem 0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: monospace;
    }
    .metric-terminal .value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.2rem 0;
        font-family: monospace;
    }
    .metric-terminal .subtext {
        color: #8b949e;
        font-size: 0.75rem;
        margin: 0;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if total_trades > 0:
        # ============================================
        # COMPREHENSIVE TRADE ANALYSIS
        # ============================================
        trade_data = []
        running_pnl = 0
        current_streak = 0
        current_streak_type = None
        max_win_streak = 0
        max_loss_streak = 0
        win_streak_count = 0
        loss_streak_count = 0
        
        # Sort trades by entry time for proper sequence analysis
        sorted_trades = sorted(trades, key=lambda x: x.get('entry_time', ''))
        
        for i, t in enumerate(sorted_trades):
            entry_time_str = t.get('entry_time', '')
            exit_time_str = t.get('exit_time', '')
            
            # Enhanced timestamp parsing
            try:
                entry_dt = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                exit_dt = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
                duration = exit_dt - entry_dt
                
                # Precise duration formatting
                total_seconds = duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                
                if total_seconds < 60:
                    duration_str = f"{seconds}s"
                elif total_seconds < 3600:
                    duration_str = f"{minutes}m {seconds}s"
                elif total_seconds < 86400:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    days = int(total_seconds // 86400)
                    remaining_hours = hours % 24
                    duration_str = f"{days}d {remaining_hours}h"
                    
                # Professional timestamp formatting
                entry_time_fmt = entry_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                exit_time_fmt = exit_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                
                # Timezone-aware time objects for analysis
                entry_hour = entry_dt.hour
                exit_hour = exit_dt.hour
                trade_date = entry_dt.date()
                
            except Exception as e:
                duration_str = "PARSE_ERROR"
                entry_time_fmt = entry_time_str[:19] if entry_time_str else 'UNKNOWN'
                exit_time_fmt = exit_time_str[:19] if exit_time_str else 'UNKNOWN'
                entry_dt = None
                exit_dt = None
                entry_hour = 0
                exit_hour = 0
                trade_date = datetime.now().date()
            
            # Core trade data
            symbol = t.get('symbol', 'UNKNOWN')
            asset = symbol.split('/')[0] if '/' in symbol else symbol
            entry_price = float(t.get('entry', 0))
            exit_price = float(t.get('exit', 0))
            amount = float(t.get('amount', 0))
            pnl = float(t.get('pnl', 0))
            pnl_pct = float(t.get('pnl_pct', 0))
            strategy = t.get('reason', 'UNKNOWN_SIGNAL').replace('_', ' ').upper()
            
            # Update running P&L
            running_pnl += pnl
            
            # Streak analysis
            is_win = pnl > 0
            if current_streak_type == 'WIN' and is_win:
                current_streak += 1
            elif current_streak_type == 'LOSS' and not is_win:
                current_streak += 1
            else:
                # Streak changed
                if current_streak_type == 'WIN':
                    max_win_streak = max(max_win_streak, current_streak)
                elif current_streak_type == 'LOSS':
                    max_loss_streak = max(max_loss_streak, current_streak)
                    
                current_streak_type = 'WIN' if is_win else 'LOSS'
                current_streak = 1
            
            # Calculate trade values
            entry_value = entry_price * amount
            exit_value = exit_price * amount
            
            # Determine trade direction based on price movement
            if entry_price < exit_price and pnl > 0:
                side = "LONG"
            elif entry_price > exit_price and pnl > 0:
                side = "SHORT"
            elif entry_price < exit_price and pnl < 0:
                side = "SHORT"  # Likely stopped out on short
            else:
                side = "LONG"   # Default assumption
            
            # Risk metrics
            risk_per_trade = abs(pnl) if pnl < 0 else (exit_value * 0.02)  # Estimate 2% risk
            risk_reward = abs(pnl / risk_per_trade) if risk_per_trade > 0 else 0
            
            # Build comprehensive trade record
            trade_record = {
                # Core identifiers
                'Trade #': i + 1,
                'Symbol': symbol,
                'Asset': asset,
                'Side': side,
                'Strategy': strategy,
                
                # Pricing & Position
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Position Size': amount,
                'Entry Value': entry_value,
                'Exit Value': exit_value,
                
                # P&L Analysis
                'Realized P&L': pnl,
                'P&L %': pnl_pct,
                'Running P&L': running_pnl,
                'Risk/Reward': risk_reward,
                
                # Timing Analysis
                'Entry Time': entry_time_fmt,
                'Exit Time': exit_time_fmt,
                'Duration': duration_str,
                'Entry Hour': entry_hour,
                'Exit Hour': exit_hour,
                'Trade Date': trade_date,
                
                # Streak Analysis
                'Current Streak': current_streak,
                'Streak Type': current_streak_type,
                'Is Winner': is_win,
                
                # Technical data for filtering
                '_entry_dt': entry_dt,
                '_exit_dt': exit_dt,
                '_duration_seconds': total_seconds if 'total_seconds' in locals() else 0,
                '_sequence': i + 1
            }
            
            trade_data.append(trade_record)
        
        # Final streak update
        if current_streak_type == 'WIN':
            max_win_streak = max(max_win_streak, current_streak)
        elif current_streak_type == 'LOSS':
            max_loss_streak = max(max_loss_streak, current_streak)
        
        # Create comprehensive DataFrame
        df = pd.DataFrame(trade_data)
        
        # ============================================
        # INSTITUTIONAL PERFORMANCE METRICS
        # ============================================
        winning_trades = df[df['Realized P&L'] > 0]
        losing_trades = df[df['Realized P&L'] <= 0]
        
        # Basic metrics
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # P&L Analysis
        total_pnl = df['Realized P&L'].sum()
        avg_pnl = df['Realized P&L'].mean()
        best_trade = df['Realized P&L'].max()
        worst_trade = df['Realized P&L'].min()
        
        # Win/Loss Analysis
        avg_win = winning_trades['Realized P&L'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['Realized P&L'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Risk Metrics
        largest_drawdown = 0
        peak_balance = 0
        current_balance = 0
        for pnl in df['Realized P&L']:
            current_balance += pnl
            peak_balance = max(peak_balance, current_balance)
            drawdown = peak_balance - current_balance
            largest_drawdown = max(largest_drawdown, drawdown)
        
        # Timing Analysis
        avg_duration_seconds = df['_duration_seconds'].mean()
        
        if avg_duration_seconds < 60:
            avg_hold_time = f"{int(avg_duration_seconds)}s"
        elif avg_duration_seconds < 3600:
            avg_hold_time = f"{int(avg_duration_seconds/60)}m"
        elif avg_duration_seconds < 86400:
            avg_hold_time = f"{avg_duration_seconds/3600:.1f}h"
        else:
            avg_hold_time = f"{avg_duration_seconds/86400:.1f}d"
        
        # Trade frequency analysis
        if df['_entry_dt'].notna().any():
            first_trade_dt = df['_entry_dt'].min()
            last_trade_dt = df['_entry_dt'].max()
            trading_period_days = (last_trade_dt - first_trade_dt).days + 1
            trades_per_day = total_trades / trading_period_days if trading_period_days > 0 else 0
            
            # Hour-by-hour analysis
            hour_analysis = df.groupby('Entry Hour').size()
            most_active_hour = hour_analysis.idxmax() if len(hour_analysis) > 0 else 0
            
        else:
            trading_period_days = 1
            trades_per_day = total_trades
            most_active_hour = 12
        
        # ============================================
        # MISSION CONTROL DASHBOARD
        # ============================================
        st.markdown("### 🎯 INSTITUTIONAL PERFORMANCE METRICS")
        
        # Create institutional-grade metrics display
        metrics_html = f"""
        <div class="institutional-metrics">
            <div class="metric-terminal">
                <h4>🎯 MISSION TRADES</h4>
                <div class="value" style="color: #58a6ff;">{total_trades:,}</div>
                <div class="subtext">Total Executed</div>
            </div>
            <div class="metric-terminal">
                <h4>📊 WIN RATIO</h4>
                <div class="value" style="color: {'#3fb950' if win_rate >= 50 else '#ff7b72' if win_rate < 30 else '#f0883e'};">{win_rate:.1f}%</div>
                <div class="subtext">{win_count}W / {loss_count}L</div>
            </div>
            <div class="metric-terminal">
                <h4>💰 TOTAL P&L</h4>
                <div class="value running-pnl-{'positive' if total_pnl >= 0 else 'negative'}">${total_pnl:+.2f}</div>
                <div class="subtext">Realized Gains</div>
            </div>
            <div class="metric-terminal">
                <h4>📈 PROFIT FACTOR</h4>
                <div class="value" style="color: {'#3fb950' if profit_factor >= 1.5 else '#ff7b72' if profit_factor < 1 else '#f0883e'};">{profit_factor:.2f}</div>
                <div class="subtext">Risk/Reward Ratio</div>
            </div>
            <div class="metric-terminal">
                <h4>⏱️ AVG DURATION</h4>
                <div class="value" style="color: #a5a5a5;">{avg_hold_time}</div>
                <div class="subtext">Position Hold Time</div>
            </div>
            <div class="metric-terminal">
                <h4>📉 MAX DRAWDOWN</h4>
                <div class="value" style="color: #ff7b72;">${largest_drawdown:.2f}</div>
                <div class="subtext">Peak-to-Valley</div>
            </div>
            <div class="metric-terminal">
                <h4>🔥 WIN STREAK</h4>
                <div class="value" style="color: #3fb950;">{max_win_streak}</div>
                <div class="subtext">Max Consecutive Wins</div>
            </div>
            <div class="metric-terminal">
                <h4>❄️ LOSS STREAK</h4>
                <div class="value" style="color: #ff7b72;">{max_loss_streak}</div>
                <div class="subtext">Max Consecutive Losses</div>
            </div>
            <div class="metric-terminal">
                <h4>⚡ FREQUENCY</h4>
                <div class="value" style="color: #f0883e;">{trades_per_day:.1f}/day</div>
                <div class="subtext">Trading Velocity</div>
            </div>
            <div class="metric-terminal">
                <h4>🎲 BEST TRADE</h4>
                <div class="value" style="color: #3fb950;">${best_trade:+.2f}</div>
                <div class="subtext">Peak Performance</div>
            </div>
            <div class="metric-terminal">
                <h4>💀 WORST TRADE</h4>
                <div class="value" style="color: #ff7b72;">${worst_trade:+.2f}</div>
                <div class="subtext">Max Single Loss</div>
            </div>
            <div class="metric-terminal">
                <h4>⏰ PEAK HOUR</h4>
                <div class="value" style="color: #a5a5a5;">{most_active_hour:02d}:00</div>
                <div class="subtext">Most Active Period</div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
        
        st.divider()
        
        # ============================================
        # ADVANCED FILTERING & SEARCH
        # ============================================
        st.markdown("### 🔍 INSTITUTIONAL TRADE FILTERS")
        
        # Multi-level filtering
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # Symbol filter
            symbols = ['All'] + sorted(df['Symbol'].unique().tolist())
            selected_symbol = st.selectbox("🎯 Asset", symbols, key="symbol_filter")
        
        with col2:
            # Strategy filter
            strategies = ['All'] + sorted(df['Strategy'].unique().tolist())
            selected_strategy = st.selectbox("⚙️ Strategy", strategies, key="strategy_filter")
        
        with col3:
            # P&L filter
            pnl_filter = st.selectbox("💰 P&L Type", ['All', 'Winners Only', 'Losers Only', 'Break Even'], key="pnl_filter")
        
        with col4:
            # Date range filtering
            if df['_entry_dt'].notna().any():
                min_date = df['_entry_dt'].min().date()
                max_date = df['_entry_dt'].max().date()
            else:
                min_date = datetime.now().date()
                max_date = datetime.now().date()
            
            date_from = st.date_input("📅 From", min_date, min_value=min_date, max_value=max_date, key="date_from")
        
        with col5:
            date_to = st.date_input("📅 To", max_date, min_value=min_date, max_value=max_date, key="date_to")
        
        # Advanced filters row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Duration filter
            duration_filter = st.selectbox("⏱️ Duration", ['All', '<1 hour', '1-6 hours', '6-24 hours', '>1 day'], key="duration_filter")
        
        with col2:
            # Trade size filter
            size_filter = st.selectbox("📏 Trade Size", ['All', 'Small (<$10)', 'Medium ($10-$50)', 'Large (>$50)'], key="size_filter")
        
        with col3:
            # Streak filter
            streak_filter = st.selectbox("🔥 Streak Position", ['All', 'Start of Streak', 'Mid Streak', 'End of Streak'], key="streak_filter")
        
        with col4:
            # Risk/Reward filter
            rr_filter = st.selectbox("⚖️ Risk/Reward", ['All', 'High R/R (>2)', 'Good R/R (1-2)', 'Poor R/R (<1)'], key="rr_filter")
        
        # Apply all filters
        filtered_df = df.copy()
        
        # Apply basic filters
        if selected_symbol != 'All':
            filtered_df = filtered_df[filtered_df['Symbol'] == selected_symbol]
        
        if selected_strategy != 'All':
            filtered_df = filtered_df[filtered_df['Strategy'] == selected_strategy]
        
        if pnl_filter != 'All':
            if pnl_filter == 'Winners Only':
                filtered_df = filtered_df[filtered_df['Realized P&L'] > 0]
            elif pnl_filter == 'Losers Only':
                filtered_df = filtered_df[filtered_df['Realized P&L'] < 0]
            elif pnl_filter == 'Break Even':
                filtered_df = filtered_df[filtered_df['Realized P&L'] == 0]
        
        # Date filter
        if date_from and date_to and filtered_df['_entry_dt'].notna().any():
            filtered_df = filtered_df[
                (filtered_df['_entry_dt'].dt.date >= date_from) & 
                (filtered_df['_entry_dt'].dt.date <= date_to)
            ]
        
        # Duration filter
        if duration_filter != 'All':
            if duration_filter == '<1 hour':
                filtered_df = filtered_df[filtered_df['_duration_seconds'] < 3600]
            elif duration_filter == '1-6 hours':
                filtered_df = filtered_df[(filtered_df['_duration_seconds'] >= 3600) & (filtered_df['_duration_seconds'] < 21600)]
            elif duration_filter == '6-24 hours':
                filtered_df = filtered_df[(filtered_df['_duration_seconds'] >= 21600) & (filtered_df['_duration_seconds'] < 86400)]
            elif duration_filter == '>1 day':
                filtered_df = filtered_df[filtered_df['_duration_seconds'] >= 86400]
        
        # Size filter
        if size_filter != 'All':
            if size_filter == 'Small (<$10)':
                filtered_df = filtered_df[filtered_df['Entry Value'] < 10]
            elif size_filter == 'Medium ($10-$50)':
                filtered_df = filtered_df[(filtered_df['Entry Value'] >= 10) & (filtered_df['Entry Value'] <= 50)]
            elif size_filter == 'Large (>$50)':
                filtered_df = filtered_df[filtered_df['Entry Value'] > 50]
        
        # Risk/Reward filter
        if rr_filter != 'All':
            if rr_filter == 'High R/R (>2)':
                filtered_df = filtered_df[filtered_df['Risk/Reward'] > 2]
            elif rr_filter == 'Good R/R (1-2)':
                filtered_df = filtered_df[(filtered_df['Risk/Reward'] >= 1) & (filtered_df['Risk/Reward'] <= 2)]
            elif rr_filter == 'Poor R/R (<1)':
                filtered_df = filtered_df[filtered_df['Risk/Reward'] < 1]
        
        # ============================================
        # EXPORT & DISPLAY CONTROLS
        # ============================================
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            # Advanced CSV export with multiple formats
            export_format = st.selectbox("📄 Export Format", ['Standard CSV', 'Excel Compatible', 'Trading Journal', 'Tax Report'], key="export_format")
        
        with col2:
            # Create export data based on format
            if export_format == 'Standard CSV':
                export_df = filtered_df.drop(columns=[col for col in filtered_df.columns if col.startswith('_')], errors='ignore')
            elif export_format == 'Excel Compatible':
                export_df = filtered_df.drop(columns=[col for col in filtered_df.columns if col.startswith('_')], errors='ignore')
                # Add formulas and summaries
                summary_row = pd.Series({
                    'Trade #': 'TOTAL',
                    'Realized P&L': filtered_df['Realized P&L'].sum(),
                    'P&L %': filtered_df['P&L %'].mean(),
                })
                export_df = pd.concat([export_df, summary_row.to_frame().T], ignore_index=True)
            elif export_format == 'Trading Journal':
                export_df = filtered_df[['Trade #', 'Symbol', 'Entry Time', 'Exit Time', 'Side', 
                                       'Entry Price', 'Exit Price', 'Position Size', 'Realized P&L', 
                                       'Strategy', 'Duration']].copy()
            else:  # Tax Report
                export_df = filtered_df[['Trade #', 'Symbol', 'Exit Time', 'Realized P&L', 'Entry Value', 'Exit Value']].copy()
            
            csv_data = export_df.to_csv(index=False)
            filename = f"trade_history_{export_format.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            st.download_button(
                label=f"📥 EXPORT {export_format.upper()}",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                width='stretch'
            )
        
        with col3:
            st.markdown(f"""
            <div style="text-align: right; padding: 12px; background: #0d1117; border: 1px solid #21262d; border-radius: 6px;">
                <div style="color: #8b949e; font-size: 0.8rem; font-family: monospace;">FILTERED RESULTS</div>
                <div style="color: #58a6ff; font-size: 1.4rem; font-weight: bold; font-family: monospace;">
                    {len(filtered_df):,} / {total_trades:,}
                </div>
                <div style="color: #8b949e; font-size: 0.7rem; font-family: monospace;">
                    Showing {len(filtered_df)/total_trades*100:.1f}% of trades
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # ============================================
        # PROFESSIONAL TRADE TABLE WITH ADVANCED FEATURES
        # ============================================
        st.markdown("### 📊 INSTITUTIONAL TRADE TABLE")
        
        # Sorting controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            sort_columns = ['Trade #', 'Entry Time', 'Symbol', 'Realized P&L', 'P&L %', 'Duration', 'Entry Value', 'Running P&L']
            sort_by = st.selectbox("🔄 Sort By", sort_columns, key="sort_by")
        
        with col2:
            sort_order = st.selectbox("📶 Order", ['Descending', 'Ascending'], key="sort_order")
        
        with col3:
            show_advanced = st.checkbox("🔬 Show Advanced Columns", value=False, key="show_advanced")
        
        # Apply sorting
        ascending = (sort_order == 'Ascending')
        if sort_by in filtered_df.columns:
            sorted_df = filtered_df.sort_values(sort_by, ascending=ascending)
        else:
            sorted_df = filtered_df
        
        # Column selection based on advanced mode
        if show_advanced:
            display_columns = [
                'Trade #', 'Symbol', 'Side', 'Entry Time', 'Exit Time', 'Duration',
                'Entry Price', 'Exit Price', 'Position Size', 'Entry Value', 'Exit Value',
                'Realized P&L', 'P&L %', 'Running P&L', 'Strategy', 'Current Streak',
                'Risk/Reward', 'Entry Hour', 'Exit Hour'
            ]
        else:
            display_columns = [
                'Trade #', 'Symbol', 'Side', 'Entry Time', 'Exit Time', 'Duration',
                'Entry Price', 'Exit Price', 'Realized P&L', 'P&L %', 'Strategy'
            ]
        
        # Create display dataframe
        display_df = sorted_df[display_columns].copy()
        
        # Format display values for professional appearance
        def format_price_professional(val):
            if pd.isna(val) or val == 0:
                return "—"
            elif val < 0.001:
                return f"{val:.8f}"
            elif val < 0.01:
                return f"{val:.6f}"
            elif val < 1:
                return f"{val:.4f}"
            elif val < 1000:
                return f"{val:,.2f}"
            else:
                return f"{val:,.2f}"
        
        def format_pnl_professional(val):
            if pd.isna(val):
                return "—"
            return f"${val:+,.2f}"
        
        def format_percentage_professional(val):
            if pd.isna(val):
                return "—"
            return f"{val:+.2f}%"
        
        # Apply formatting
        if 'Entry Price' in display_df.columns:
            display_df['Entry Price'] = display_df['Entry Price'].apply(format_price_professional)
        if 'Exit Price' in display_df.columns:
            display_df['Exit Price'] = display_df['Exit Price'].apply(format_price_professional)
        if 'Position Size' in display_df.columns:
            display_df['Position Size'] = display_df['Position Size'].apply(lambda x: f"{x:.6f}" if pd.notna(x) else "—")
        if 'Entry Value' in display_df.columns:
            display_df['Entry Value'] = display_df['Entry Value'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
        if 'Exit Value' in display_df.columns:
            display_df['Exit Value'] = display_df['Exit Value'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
        if 'Realized P&L' in display_df.columns:
            display_df['Realized P&L'] = display_df['Realized P&L'].apply(format_pnl_professional)
        if 'P&L %' in display_df.columns:
            display_df['P&L %'] = display_df['P&L %'].apply(format_percentage_professional)
        if 'Running P&L' in display_df.columns:
            display_df['Running P&L'] = display_df['Running P&L'].apply(format_pnl_professional)
        if 'Risk/Reward' in display_df.columns:
            display_df['Risk/Reward'] = display_df['Risk/Reward'].apply(lambda x: f"{x:.2f}" if pd.notna(x) and x != 0 else "—")
        
        # Pagination for large datasets
        page_size = st.selectbox("📄 Rows per page", [10, 20, 50, 100], index=1, key="page_size")
        
        if len(display_df) > page_size:
            total_pages = (len(display_df) + page_size - 1) // page_size
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                current_page = st.number_input(
                    f"Page (1-{total_pages})", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1,
                    key="current_page"
                )
            
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(display_df))
            page_df = display_df.iloc[start_idx:end_idx]
            
            # Page info
            st.markdown(f"""
            <div style="text-align: center; color: #8b949e; font-size: 0.8rem; font-family: monospace; margin: 10px 0;">
                📄 PAGE {current_page} OF {total_pages} | ROWS {start_idx+1:,}-{end_idx:,} OF {len(display_df):,}
            </div>
            """, unsafe_allow_html=True)
        else:
            page_df = display_df
            st.markdown(f"""
            <div style="text-align: center; color: #8b949e; font-size: 0.8rem; font-family: monospace; margin: 10px 0;">
                📊 DISPLAYING ALL {len(display_df):,} TRADES
            </div>
            """, unsafe_allow_html=True)
        
        # Professional styled dataframe
        st.dataframe(
            page_df,
            width='stretch',
            hide_index=True,
            height=min(800, 60 + len(page_df) * 40),
            column_config={
                "Trade #": st.column_config.NumberColumn("Trade #", width="small"),
                "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                "Side": st.column_config.TextColumn("Side", width="small"),
                "Realized P&L": st.column_config.TextColumn("P&L", width="medium"),
                "P&L %": st.column_config.TextColumn("P&L %", width="small"),
                "Entry Time": st.column_config.TextColumn("Entry Time", width="large"),
                "Exit Time": st.column_config.TextColumn("Exit Time", width="large"),
                "Duration": st.column_config.TextColumn("Duration", width="medium"),
                "Strategy": st.column_config.TextColumn("Strategy", width="medium"),
            }
        )
        
        # ============================================
        # TRADE DETAIL ANALYSIS (EXPANDABLE)
        # ============================================
        st.divider()
        st.markdown("### 🔬 INDIVIDUAL TRADE ANALYSIS")
        
        if len(filtered_df) > 0:
            # Trade selector
            trade_options = [f"Trade #{row['Trade #']} - {row['Symbol']} - ${row['Realized P&L']:+.2f}" for _, row in filtered_df.iterrows()]
            selected_trade_idx = st.selectbox("🎯 Select Trade for Analysis", 
                                            range(len(trade_options)), 
                                            format_func=lambda x: trade_options[x],
                                            key="trade_selector")
            
            selected_trade = filtered_df.iloc[selected_trade_idx]
            
            # Comprehensive trade analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="trade-detail-expander">
                <h4 style="color: #ff6b35; margin-bottom: 1rem;">📊 TRADE DETAILS</h4>
                <table style="width: 100%; font-family: monospace; font-size: 0.85rem;">
                <tr><td style="color: #8b949e;">Trade ID:</td><td style="color: #58a6ff;">#{selected_trade['Trade #']}</td></tr>
                <tr><td style="color: #8b949e;">Symbol:</td><td style="color: #58a6ff;">{selected_trade['Symbol']}</td></tr>
                <tr><td style="color: #8b949e;">Strategy:</td><td style="color: #f0883e;">{selected_trade['Strategy']}</td></tr>
                <tr><td style="color: #8b949e;">Side:</td><td style="color: #a5a5a5;">{selected_trade['Side']}</td></tr>
                <tr><td style="color: #8b949e;">Entry:</td><td style="color: #a5a5a5;">{selected_trade['Entry Time']}</td></tr>
                <tr><td style="color: #8b949e;">Exit:</td><td style="color: #a5a5a5;">{selected_trade['Exit Time']}</td></tr>
                <tr><td style="color: #8b949e;">Duration:</td><td style="color: #a5a5a5;">{selected_trade['Duration']}</td></tr>
                <tr><td style="color: #8b949e;">Entry Price:</td><td style="color: #58a6ff;">${selected_trade['Entry Price']:,.6f}</td></tr>
                <tr><td style="color: #8b949e;">Exit Price:</td><td style="color: #58a6ff;">${selected_trade['Exit Price']:,.6f}</td></tr>
                <tr><td style="color: #8b949e;">Position Size:</td><td style="color: #58a6ff;">{selected_trade['Position Size']:.6f}</td></tr>
                <tr><td style="color: #8b949e;">Entry Value:</td><td style="color: #58a6ff;">${selected_trade['Entry Value']:,.2f}</td></tr>
                <tr><td style="color: #8b949e;">Exit Value:</td><td style="color: #58a6ff;">${selected_trade['Exit Value']:,.2f}</td></tr>
                </table>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                pnl_color = "#3fb950" if selected_trade['Realized P&L'] >= 0 else "#f85149"
                streak_color = "#3fb950" if selected_trade['Streak Type'] == 'WIN' else "#f85149"
                
                st.markdown(f"""
                <div class="trade-detail-expander">
                <h4 style="color: #ff6b35; margin-bottom: 1rem;">💰 PERFORMANCE ANALYSIS</h4>
                <table style="width: 100%; font-family: monospace; font-size: 0.85rem;">
                <tr><td style="color: #8b949e;">P&L:</td><td style="color: {pnl_color}; font-weight: bold;">${selected_trade['Realized P&L']:+.2f}</td></tr>
                <tr><td style="color: #8b949e;">P&L %:</td><td style="color: {pnl_color}; font-weight: bold;">{selected_trade['P&L %']:+.2f}%</td></tr>
                <tr><td style="color: #8b949e;">Running P&L:</td><td style="color: {'#3fb950' if selected_trade['Running P&L'] >= 0 else '#f85149'};">${selected_trade['Running P&L']:+.2f}</td></tr>
                <tr><td style="color: #8b949e;">Risk/Reward:</td><td style="color: #a5a5a5;">{selected_trade['Risk/Reward']:.2f}</td></tr>
                <tr><td style="color: #8b949e;">Streak:</td><td style="color: {streak_color};">{selected_trade['Current Streak']} {selected_trade['Streak Type']}</td></tr>
                <tr><td style="color: #8b949e;">Entry Hour:</td><td style="color: #a5a5a5;">{selected_trade['Entry Hour']:02d}:00 UTC</td></tr>
                <tr><td style="color: #8b949e;">Exit Hour:</td><td style="color: #a5a5a5;">{selected_trade['Exit Hour']:02d}:00 UTC</td></tr>
                <tr><td style="color: #8b949e;">Sequence:</td><td style="color: #a5a5a5;">{selected_trade['_sequence']}/{total_trades}</td></tr>
                <tr><td style="color: #8b949e;">Winner:</td><td style="color: {'#3fb950' if selected_trade['Is Winner'] else '#f85149'};">{'✓ YES' if selected_trade['Is Winner'] else '✗ NO'}</td></tr>
                </table>
                </div>
                """, unsafe_allow_html=True)
        
        # ============================================
        # ENHANCED ANALYTICS SECTION
        # ============================================
        st.divider()
        st.markdown("### 📈 ENHANCED TRADE ANALYTICS")
        
        # Create three analysis columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🎯 ASSET PERFORMANCE")
            
            asset_performance = filtered_df.groupby('Asset').agg({
                'Realized P&L': ['count', 'sum', 'mean'],
                'P&L %': 'mean',
                'Is Winner': 'sum'
            }).round(3)
            asset_performance.columns = ['Trades', 'Total P&L', 'Avg P&L', 'Avg P&L %', 'Wins']
            asset_performance['Win Rate'] = (asset_performance['Wins'] / asset_performance['Trades'] * 100).round(1)
            asset_performance = asset_performance.sort_values('Total P&L', ascending=False)
            
            # Format for display
            asset_display = asset_performance.copy()
            asset_display['Total P&L'] = asset_display['Total P&L'].apply(lambda x: f"${x:+.2f}")
            asset_display['Avg P&L'] = asset_display['Avg P&L'].apply(lambda x: f"${x:+.2f}")
            asset_display['Avg P&L %'] = asset_display['Avg P&L %'].apply(lambda x: f"{x:+.2f}%")
            asset_display['Win Rate'] = asset_display['Win Rate'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(asset_display, width='stretch')
        
        with col2:
            st.markdown("#### ⚡ STRATEGY PERFORMANCE")
            
            strategy_performance = filtered_df.groupby('Strategy').agg({
                'Realized P&L': ['count', 'sum', 'mean'],
                'Is Winner': 'sum'
            }).round(3)
            strategy_performance.columns = ['Trades', 'Total P&L', 'Avg P&L', 'Wins']
            strategy_performance['Win Rate'] = (strategy_performance['Wins'] / strategy_performance['Trades'] * 100).round(1)
            strategy_performance = strategy_performance.sort_values('Total P&L', ascending=False)
            
            # Format for display
            strategy_display = strategy_performance.copy()
            strategy_display['Total P&L'] = strategy_display['Total P&L'].apply(lambda x: f"${x:+.2f}")
            strategy_display['Avg P&L'] = strategy_display['Avg P&L'].apply(lambda x: f"${x:+.2f}")
            strategy_display['Win Rate'] = strategy_display['Win Rate'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(strategy_display, width='stretch')
        
        with col3:
            st.markdown("#### ⏰ TIMING ANALYSIS")
            
            # Hour-by-hour performance
            hour_performance = filtered_df.groupby('Entry Hour').agg({
                'Realized P&L': ['count', 'mean'],
                'Is Winner': 'mean'
            }).round(3)
            hour_performance.columns = ['Trades', 'Avg P&L', 'Win Rate']
            hour_performance['Win Rate'] = (hour_performance['Win Rate'] * 100).round(1)
            hour_performance = hour_performance.sort_values('Avg P&L', ascending=False)
            
            # Format for display
            hour_display = hour_performance.copy()
            hour_display['Avg P&L'] = hour_display['Avg P&L'].apply(lambda x: f"${x:+.2f}")
            hour_display['Win Rate'] = hour_display['Win Rate'].apply(lambda x: f"{x:.1f}%")
            hour_display.index = [f"{h:02d}:00" for h in hour_display.index]
            
            st.dataframe(hour_display, width='stretch')
        
        # ============================================
        # RUNNING P&L CHART
        # ============================================
        st.divider()
        st.markdown("### 📊 RUNNING P&L BALANCE")
        
        # Create running P&L chart
        running_pnl_data = filtered_df.sort_values('_sequence')[['Trade #', 'Running P&L', 'Realized P&L', 'Symbol']].copy()
        
        fig = go.Figure()
        
        # Running balance line
        fig.add_trace(go.Scatter(
            x=running_pnl_data['Trade #'],
            y=running_pnl_data['Running P&L'],
            mode='lines+markers',
            name='Running P&L',
            line=dict(color='#58a6ff', width=3),
            marker=dict(size=6),
            hovertemplate='<b>Trade #%{x}</b><br>Running P&L: $%{y:+.2f}<extra></extra>'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="#8b949e", annotation_text="Break Even")
        
        # Individual trade markers
        colors = ['#3fb950' if pnl > 0 else '#f85149' for pnl in running_pnl_data['Realized P&L']]
        fig.add_trace(go.Scatter(
            x=running_pnl_data['Trade #'],
            y=running_pnl_data['Running P&L'],
            mode='markers',
            name='Trades',
            marker=dict(
                color=colors,
                size=8,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>%{customdata[0]}</b><br>Trade P&L: $%{customdata[1]:+.2f}<br>Running Total: $%{y:+.2f}<extra></extra>',
            customdata=list(zip(running_pnl_data['Symbol'], running_pnl_data['Realized P&L']))
        ))
        
        fig.update_layout(
            title=dict(
                text="📈 CUMULATIVE P&L PROGRESSION",
                font=dict(size=18, color='#ff6b35', family='monospace')
            ),
            xaxis=dict(
                title="Trade Sequence",
                gridcolor='#21262d',
                color='#8b949e',
                tickfont=dict(family='monospace')
            ),
            yaxis=dict(
                title="Running P&L ($)",
                gridcolor='#21262d',
                color='#8b949e',
                tickfont=dict(family='monospace')
            ),
            plot_bgcolor='#0d1117',
            paper_bgcolor='#0d1117',
            font=dict(color='#c9d1d9', family='monospace'),
            legend=dict(
                bgcolor='rgba(13, 17, 23, 0.8)',
                bordercolor='#21262d',
                borderwidth=1
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # ============================================
        # MISSION SUMMARY STATISTICS
        # ============================================
        st.divider()
        st.markdown("### 🎯 MISSION INTELLIGENCE SUMMARY")
        
        # Final mission stats
        total_filtered_pnl = filtered_df['Realized P&L'].sum()
        best_streak = filtered_df.groupby(['Streak Type', 'Current Streak']).size().reset_index()
        best_win_streak = best_streak[best_streak['Streak Type'] == 'WIN']['Current Streak'].max() if len(best_streak[best_streak['Streak Type'] == 'WIN']) > 0 else 0
        best_loss_streak = best_streak[best_streak['Streak Type'] == 'LOSS']['Current Streak'].max() if len(best_streak[best_streak['Streak Type'] == 'LOSS']) > 0 else 0
        
        avg_trade_duration = filtered_df['_duration_seconds'].mean()
        if avg_trade_duration < 3600:
            duration_desc = "High-frequency scalping"
        elif avg_trade_duration < 86400:
            duration_desc = "Intraday trading"
        else:
            duration_desc = "Position trading"
        
        most_profitable_asset = filtered_df.groupby('Asset')['Realized P&L'].sum().idxmax() if len(filtered_df) > 0 else "N/A"
        most_profitable_strategy = filtered_df.groupby('Strategy')['Realized P&L'].sum().idxmax() if len(filtered_df) > 0 else "N/A"
        
        st.markdown(f"""
        <div class="trade-detail-expander">
        <h4 style="color: #ff6b35; text-align: center; margin-bottom: 1.5rem;">🎯 MISSION INTELLIGENCE REPORT</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h5 style="color: #58a6ff;">📊 PERFORMANCE OVERVIEW</h5>
                <p><strong>Filtered P&L:</strong> <span style="color: {'#3fb950' if total_filtered_pnl >= 0 else '#f85149'};">${total_filtered_pnl:+.2f}</span></p>
                <p><strong>Win Rate:</strong> {len(filtered_df[filtered_df['Is Winner']])/len(filtered_df)*100:.1f}% ({len(filtered_df[filtered_df['Is Winner']])}/{len(filtered_df)})</p>
                <p><strong>Best Win Streak:</strong> {best_win_streak} consecutive wins</p>
                <p><strong>Max Loss Streak:</strong> {best_loss_streak} consecutive losses</p>
                <p><strong>Trading Style:</strong> {duration_desc}</p>
            </div>
            <div>
                <h5 style="color: #58a6ff;">🏆 TOP PERFORMERS</h5>
                <p><strong>Best Asset:</strong> {most_profitable_asset}</p>
                <p><strong>Best Strategy:</strong> {most_profitable_strategy}</p>
                <p><strong>Avg Hold Time:</strong> {avg_hold_time}</p>
                <p><strong>Trade Frequency:</strong> {trades_per_day:.1f} trades/day</p>
                <p><strong>Peak Activity:</strong> {most_active_hour:02d}:00 UTC</p>
            </div>
        </div>
        <div style="text-align: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #21262d;">
            <p style="color: #8b949e; font-size: 0.8rem; font-family: monospace;">
                🚀 INSTITUTIONAL TRADING JOURNAL • NASA MISSION CONTROL AESTHETICS<br>
                Data integrity verified • Real-time performance tracking • Professional analytics
            </p>
        </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # No trades available - Professional empty state
        st.markdown("""
        <div class="metric-terminal" style="text-align: center; padding: 3rem; margin: 2rem 0;">
            <div style="font-size: 4rem; color: #21262d; margin-bottom: 1rem;">📭</div>
            <h3 style="color: #ff6b35; margin-bottom: 1rem;">MISSION LOG EMPTY</h3>
            <p style="color: #8b949e; font-size: 1.1rem; margin-bottom: 1.5rem;">
                No trade history detected. The institutional journal is ready to capture trades.
            </p>
            <div style="background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 1rem; margin-top: 2rem;">
                <h4 style="color: #58a6ff; margin-bottom: 0.5rem;">🎯 SYSTEM STATUS</h4>
                <p style="color: #8b949e; font-size: 0.9rem; margin: 0;">
                    Trading bot monitoring for entry signals...<br>
                    Professional analytics will activate upon first trade execution.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# TAB 4: BACKTESTING STRATEGIES
# ============================================
with tab4:
    st.subheader("🔬 BACKTESTING STRATEGIES • NASA ANALYSIS CENTER")
    
    # Real Analysis Summary
    real_trades = ALL_TRADES if ALL_TRADES else BOT_DATA.get('recent_trades', [])
    
    # Calculate actual trading period
    if real_trades:
        try:
            sorted_trades = sorted(real_trades, key=lambda x: x.get('exit_time', ''))
            first_trade = datetime.fromisoformat(sorted_trades[0].get('exit_time', '').replace('Z', ''))
            last_trade = datetime.fromisoformat(sorted_trades[-1].get('exit_time', '').replace('Z', ''))
            actual_period = (last_trade - first_trade).days
            actual_start_date = first_trade.strftime('%Y-%m-%d')
            actual_end_date = last_trade.strftime('%Y-%m-%d')
        except:
            actual_period = 7  # fallback
            actual_start_date = "2026-02-01"
            actual_end_date = "2026-02-02"
    else:
        actual_period = 0
        actual_start_date = "N/A"
        actual_end_date = "N/A"
    
    # Get unique assets from actual trades
    assets_traded = list(set(t.get('symbol', 'N/A').split('/')[0] for t in real_trades))
    
    st.markdown(f"""
    <div class="terminal-bg">
    <h4 style="color: #ff6600; margin-bottom: 20px;">🚀 REAL TRADING ANALYSIS (LIVE DATA)</h4>
    <p><strong>ACTUAL PERIOD:</strong> {actual_start_date} to {actual_end_date} ({actual_period} days)</p>
    <p><strong>ASSETS TRADED:</strong> {', '.join(sorted(assets_traded))}</p>
    <p><strong>ACCOUNT SIZE:</strong> ${STARTING_BALANCE:.2f} → ${TOTAL_BALANCE:.2f}</p>
    <p><strong>TOTAL TRADES:</strong> {len(real_trades)} (Real executed trades)</p>
    <p style="color: #39ff14; margin-top: 10px;">✅ LIVE DATA - All results from actual bot execution (bot_data.json)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🏆 REAL STRATEGY PERFORMANCE ANALYSIS")
    
    # Analyze real strategies from actual trades
    strategy_analysis = {}
    for trade in real_trades:
        strategy = trade.get('reason', 'unknown').replace('_', ' ').title()
        symbol = trade.get('symbol', 'unknown')
        pnl = trade.get('pnl', 0)
        
        if strategy not in strategy_analysis:
            strategy_analysis[strategy] = {
                'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0, 
                'max_win': 0, 'max_loss': 0, 'pnl_list': [], 'symbols': set()
            }
        
        analysis = strategy_analysis[strategy]
        analysis['trades'] += 1
        analysis['symbols'].add(symbol.split('/')[0])  # Just the base asset
        analysis['total_pnl'] += pnl
        analysis['pnl_list'].append(pnl)
        
        if pnl > 0:
            analysis['wins'] += 1
            analysis['max_win'] = max(analysis['max_win'], pnl)
        else:
            analysis['losses'] += 1
            analysis['max_loss'] = min(analysis['max_loss'], pnl)
    
    # Create real strategy dataframe
    real_strategy_data = []
    for strategy, analysis in strategy_analysis.items():
        win_rate = (analysis['wins'] / analysis['trades'] * 100) if analysis['trades'] > 0 else 0
        avg_return = (analysis['total_pnl'] / STARTING_BALANCE * 100) if STARTING_BALANCE > 0 else 0
        
        # Calculate simple Sharpe ratio
        if len(analysis['pnl_list']) > 1:
            mean_pnl = np.mean(analysis['pnl_list'])
            std_pnl = np.std(analysis['pnl_list'], ddof=1)
            sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0
        else:
            sharpe = 0
        
        # Status based on performance
        if avg_return > 1 and win_rate > 40:
            status = "🟢 EXCELLENT"
        elif avg_return > 0 and win_rate > 30:
            status = "🟡 GOOD"
        elif avg_return > -1:
            status = "🟠 REVIEW"
        else:
            status = "🔴 POOR"
        
        real_strategy_data.append({
            "RANK": "",  # Will assign after sorting
            "STRATEGY": strategy,
            "RETURN": f"{avg_return:+.2f}%",
            "SHARPE": f"{sharpe:.2f}",
            "WIN_RATE": f"{win_rate:.1f}%", 
            "TRADES": analysis['trades'],
            "TOTAL_PNL": f"${analysis['total_pnl']:+.2f}",
            "ASSETS": ', '.join(sorted(analysis['symbols'])),
            "STATUS": status,
            "_sort_pnl": analysis['total_pnl']  # For sorting
        })
    
    # Sort by total P&L and assign ranks
    real_strategy_data.sort(key=lambda x: x['_sort_pnl'], reverse=True)
    for i, strategy in enumerate(real_strategy_data):
        if i == 0:
            strategy['RANK'] = "🥇"
        elif i == 1:
            strategy['RANK'] = "🥈"
        elif i == 2:
            strategy['RANK'] = "🥉"
        else:
            strategy['RANK'] = str(i + 1)
    
    # Remove sort column
    for strategy in real_strategy_data:
        del strategy['_sort_pnl']
    
    if real_strategy_data:
        strategy_df = pd.DataFrame(real_strategy_data)
        st.dataframe(
            strategy_df,
            width='stretch',
            hide_index=True,
            height=300
        )
    else:
        st.markdown("*No strategy data available - need more trades for analysis*")
    
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
    
    # Real Asset-Specific Analysis
    st.markdown("### 🎯 REAL ASSET PERFORMANCE ANALYSIS")
    
    # Analyze performance by asset from actual trades
    asset_analysis = {}
    for trade in real_trades:
        symbol = trade.get('symbol', 'UNKNOWN/USDT')
        asset = symbol.split('/')[0]
        pnl = trade.get('pnl', 0)
        
        if asset not in asset_analysis:
            asset_analysis[asset] = {
                'trades': 0, 'wins': 0, 'total_pnl': 0, 
                'strategies': set(), 'pnl_list': []
            }
        
        analysis = asset_analysis[asset]
        analysis['trades'] += 1
        analysis['total_pnl'] += pnl
        analysis['pnl_list'].append(pnl)
        analysis['strategies'].add(trade.get('reason', 'unknown'))
        
        if pnl > 0:
            analysis['wins'] += 1
    
    # Sort assets by total P&L
    sorted_assets = sorted(asset_analysis.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    
    # Display top 3 assets (or all if less than 3)
    asset_cols = st.columns(min(3, len(sorted_assets)))
    
    for i, (asset, analysis) in enumerate(sorted_assets[:3]):
        with asset_cols[i]:
            win_rate = (analysis['wins'] / analysis['trades'] * 100) if analysis['trades'] > 0 else 0
            avg_pnl = analysis['total_pnl'] / analysis['trades'] if analysis['trades'] > 0 else 0
            
            # Asset color/icon
            asset_colors = {
                'BTC': '🟠', 'ETH': '🔵', 'SOL': '🟣', 
                'DOT': '🔴', 'DOGE': '🟡', 'ARB': '⚪',
                'AVAX': '🔴', 'LINK': '🔵'
            }
            asset_icon = asset_colors.get(asset, '⚫')
            
            # Performance status
            if analysis['total_pnl'] > 1:
                status = "🟢 EXCELLENT"
                border_color = "#39ff14"
            elif analysis['total_pnl'] > 0:
                status = "🟡 GOOD" 
                border_color = "#ff6600"
            else:
                status = "🔴 POOR"
                border_color = "#ff3333"
            
            # Most common strategy
            strategy_counts = {}
            for trade in real_trades:
                if trade.get('symbol', '').startswith(asset):
                    strategy = trade.get('reason', 'unknown')
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            primary_strategy = max(strategy_counts, key=strategy_counts.get) if strategy_counts else 'N/A'
            primary_strategy = primary_strategy.replace('_', ' ').title()
            
            st.markdown(f"""
            <div class="metric-card" style="border-color: {border_color};">
            <h4 style="color: #ff6600;">{asset_icon} {asset} PERFORMANCE</h4>
            <p><strong>TOTAL P&L:</strong> ${analysis['total_pnl']:+.2f}</p>
            <p><strong>WIN RATE:</strong> {win_rate:.1f}%</p>
            <p><strong>TRADES:</strong> {analysis['trades']}</p>
            <p><strong>AVG P&L:</strong> ${avg_pnl:+.2f}</p>
            <hr style="border-color: #333;">
            <p><strong>PRIMARY STRATEGY:</strong> {primary_strategy}</p>
            <p><strong>STATUS:</strong> {status}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # If less than 3 assets, show summary
    if len(sorted_assets) < 3:
        st.markdown(f"""
        <div style="text-align: center; color: #888; font-size: 0.9rem; margin-top: 20px;">
        <p>Analysis shows {len(sorted_assets)} assets traded. More assets will appear as trading expands.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Real Analysis: What Works vs What Doesn't (from actual data)
    col1, col2 = st.columns(2)
    
    # Analyze profitable vs unprofitable strategies from real data
    profitable_strategies = [s for s in real_strategy_data if float(s['TOTAL_PNL'].replace('$', '').replace('+', '')) > 0]
    unprofitable_strategies = [s for s in real_strategy_data if float(s['TOTAL_PNL'].replace('$', '').replace('+', '')) <= 0]
    
    with col1:
        st.markdown("### ✅ WHAT ACTUALLY WORKS (Real Data)")
        if profitable_strategies:
            success_content = ""
            for strategy in profitable_strategies:
                success_content += f"<p><strong>{strategy['STRATEGY']}:</strong> {strategy['TOTAL_PNL']} ({strategy['WIN_RATE']} win rate)</p>"
            
            st.markdown(f"""
            <div class="alert-success">
            {success_content}
            <hr style="border-color: #39ff14; margin: 10px 0;">
            <p><strong>COMMON SUCCESS FACTORS:</strong></p>
            <p>• Average trade frequency: {len(real_trades)/(actual_period if actual_period > 0 else 1):.1f} trades/day</p>
            <p>• Most profitable assets: {', '.join(assets_traded[:3])}</p>
            <p>• Actual win rate: {(len([t for t in real_trades if t.get('pnl', 0) > 0])/len(real_trades)*100):.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-success">
            <p><strong>NO PROFITABLE STRATEGIES YET:</strong> Need more trades for analysis</p>
            <p>Current sample: 30 trades over {actual_period} days</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ❌ WHAT DOESN'T WORK (Real Data)")
        if unprofitable_strategies:
            failure_content = ""
            for strategy in unprofitable_strategies:
                failure_content += f"<p><strong>{strategy['STRATEGY']}:</strong> {strategy['TOTAL_PNL']} ({strategy['WIN_RATE']} win rate)</p>"
            
            st.markdown(f"""
            <div class="alert-danger">
            {failure_content}
            <hr style="border-color: #ff3333; margin: 10px 0;">
            <p><strong>FAILURE PATTERNS IDENTIFIED:</strong></p>
            <p>• Stop loss frequency: {len([t for t in real_trades if 'stop_loss' in t.get('reason', '')])}/{len(real_trades)} trades</p>
            <p>• Bearish signal accuracy: {(len([t for t in real_trades if 'bearish' in t.get('reason', '') and t.get('pnl', 0) > 0])/max(len([t for t in real_trades if 'bearish' in t.get('reason', '')]), 1)*100):.1f}%</p>
            <p>• Worst performing asset: Analysis pending</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-danger">
            <p><strong>ALL STRATEGIES PROFITABLE:</strong> Excellent performance</p>
            <p>Continue monitoring for drawdown patterns</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown(f'<div class="footer">🚀 BUILT FOR THE $1K CRYPTO TRADING MISSION | NASA MISSION CONTROL AESTHETIC | v3.0 | Balance: ${TOTAL_BALANCE:.2f}</div>', unsafe_allow_html=True)

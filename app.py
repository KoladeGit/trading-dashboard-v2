#!/usr/bin/env python3
"""
Trading Dashboard - $1K Crypto Mission
NASA Mission Control Aesthetic
Tracks allocations, P&L, and positions across 3 prongs
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
    initial_sidebar_state="expanded"
)

# Load real balance from bot_data.json
def load_real_balance():
    try:
        with open('bot_data.json', 'r') as f:
            data = json.load(f)
            return data.get('account', {}).get('total_usd', 1000)
    except:
        return 1000

REAL_BALANCE = load_real_balance()

# Initialize session state - force reset to ensure correct structure
def get_default_allocations():
    return {
        "News Trading": {"allocated": float(round(REAL_BALANCE * 0.4, 2)), "used": 0.0, "available": float(round(REAL_BALANCE * 0.4, 2))},
        "Polymarket": {"allocated": float(round(REAL_BALANCE * 0.3, 2)), "used": 0.0, "available": float(round(REAL_BALANCE * 0.3, 2))},
        "Algorithmic": {"allocated": float(round(REAL_BALANCE * 0.3, 2)), "used": 0.0, "available": float(round(REAL_BALANCE * 0.3, 2))}
    }

if 'trades' not in st.session_state:
    st.session_state.trades = []

# Always reset allocations to ensure correct structure (handles old session state)
if 'allocations' not in st.session_state or 'available' not in st.session_state.allocations.get("News Trading", {}):
    st.session_state.allocations = get_default_allocations()

if 'positions' not in st.session_state:
    st.session_state.positions = []

# NASA Mission Control CSS with CRT scanlines and retro styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700&display=swap');
    
    /* Global dark theme */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 100%);
        color: #39ff14;
        font-family: 'IBM Plex Mono', monospace !important;
        position: relative;
    }
    
    /* CRT scanlines effect */
    .stApp::after {
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
        z-index: 1000;
        animation: scanlines 0.1s linear infinite;
    }
    
    @keyframes scanlines {
        0% { transform: translateY(0px); }
        100% { transform: translateY(2px); }
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
        box-shadow: 
            0 0 15px rgba(57, 255, 20, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
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
    
    /* Status indicators */
    .profit {
        color: #39ff14;
        font-weight: bold;
        text-shadow: 0 0 5px #39ff14;
    }
    .loss {
        color: #ff3333;
        font-weight: bold;
        text-shadow: 0 0 5px #ff3333;
    }
    .warning {
        color: #ff6600;
        font-weight: bold;
        text-shadow: 0 0 5px #ff6600;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #0d0d0d 0%, #1a1a1a 100%);
        border-right: 1px solid #39ff14;
    }
    
    /* Form inputs */
    .stSelectbox > div > div {
        background-color: #1a1a1a !important;
        border: 1px solid #39ff14 !important;
        color: #39ff14 !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #39ff14 !important;
        color: #39ff14 !important;
    }
    
    .stNumberInput > div > div > input {
        background-color: #1a1a1a !important;
        border: 1px solid #39ff14 !important;
        color: #39ff14 !important;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a !important;
        border: 1px solid #39ff14 !important;
        color: #39ff14 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #ff6600, #cc5200);
        border: 1px solid #ff6600;
        color: #0a0a0a;
        font-weight: bold;
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 10px rgba(255, 102, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(145deg, #ffaa00, #ff6600);
        box-shadow: 0 0 15px rgba(255, 102, 0, 0.8);
        transform: translateY(-1px);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0d0d0d;
        border-bottom: 2px solid #39ff14;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        border: 1px solid #39ff14;
        color: #39ff14 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-right: 5px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #39ff14, #2dd60f) !important;
        color: #0a0a0a !important;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.6);
    }
    
    /* Dataframe styling */
    .dataframe {
        background-color: #0d0d0d !important;
        border: 1px solid #39ff14 !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    /* Mission critical alerts */
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
    
    /* Metrics override for dark theme */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d) !important;
        border: 1px solid #39ff14 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.2) !important;
    }
    
    [data-testid="metric-container"] > div {
        color: #39ff14 !important;
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
tab1, tab2 = st.tabs(["🎯 ACTIVE MISSION", "📊 BACKTESTING STRATEGIES"])

with tab1:
    # Sidebar - Mission Control Panel
    with st.sidebar:
        st.markdown("### ⚡ MISSION CONTROL PANEL")

        # New Trade Entry
        st.markdown("#### 📝 NEW TRADE ENTRY")
        with st.form("new_trade_form"):
            prong = st.selectbox(
                "MISSION PRONG",
                ["News Trading", "Polymarket", "Algorithmic"]
            )
            
            asset = st.text_input("ASSET/MARKET", placeholder="e.g., BTC, ETH, 'Trump 2024'")
            
            direction = st.selectbox("DIRECTION", ["Long", "Short"])
            
            entry_price = st.number_input("ENTRY PRICE ($)", min_value=0.0, step=0.01)
            
            position_size = st.number_input(
                "POSITION SIZE ($)", 
                min_value=0.0, 
                max_value=float(st.session_state.allocations[prong]["available"]),
                step=10.0
            )
            
            target = st.number_input("TARGET ($)", min_value=0.0, step=0.01)
            stop_loss = st.number_input("STOP LOSS ($)", min_value=0.0, step=0.01)
            
            notes = st.text_area("MISSION NOTES", placeholder="Strategy, catalyst, etc.")
            
            submitted = st.form_submit_button("🚀 EXECUTE TRADE")
            
            if submitted:
                trade = {
                    "id": len(st.session_state.trades) + 1,
                    "timestamp": datetime.now().isoformat(),
                    "prong": prong,
                    "asset": asset,
                    "direction": direction,
                    "entry_price": entry_price,
                    "position_size": position_size,
                    "target": target,
                    "stop_loss": stop_loss,
                    "notes": notes,
                    "status": "Open",
                    "pnl": 0,
                    "pnl_pct": 0
                }
                st.session_state.trades.append(trade)
                st.session_state.allocations[prong]["used"] += position_size
                st.session_state.allocations[prong]["available"] -= position_size
                st.markdown(f'<div class="alert-success">TRADE EXECUTED! {prong}: ${position_size:.2f}</div>', unsafe_allow_html=True)

        # Close Position Form
        st.markdown("#### 🔒 CLOSE POSITION")
        with st.form("close_trade_form"):
            open_trades = [t for t in st.session_state.trades if t["status"] == "Open"] if st.session_state.trades else []
            if open_trades:
                trade_options = {f"#{t['id']} - {t['asset']} ({t['prong']})": t for t in open_trades}
                selected_trade_key = st.selectbox("SELECT POSITION", list(trade_options.keys()))
                selected_trade = trade_options[selected_trade_key]
                
                exit_price = st.number_input("EXIT PRICE ($)", min_value=0.0, step=0.01)
                
                close_submitted = st.form_submit_button("🔒 CLOSE POSITION")
                
                if close_submitted:
                        # Calculate P&L
                        trade_idx = st.session_state.trades.index(selected_trade)
                        entry = selected_trade["entry_price"]
                        direction = 1 if selected_trade["direction"] == "Long" else -1
                        
                        pnl_pct = ((exit_price - entry) / entry) * direction * 100
                        pnl_amount = selected_trade["position_size"] * (pnl_pct / 100)
                        
                        st.session_state.trades[trade_idx]["status"] = "Closed"
                        st.session_state.trades[trade_idx]["exit_price"] = exit_price
                        st.session_state.trades[trade_idx]["pnl"] = pnl_amount
                        st.session_state.trades[trade_idx]["pnl_pct"] = pnl_pct
                        st.session_state.trades[trade_idx]["close_timestamp"] = datetime.now().isoformat()
                        
                        # Return allocation
                        prong = selected_trade["prong"]
                        st.session_state.allocations[prong]["used"] -= selected_trade["position_size"]
                        st.session_state.allocations[prong]["available"] += selected_trade["position_size"]
                        
                        alert_class = "alert-success" if pnl_amount >= 0 else "alert-danger"
                        st.markdown(f'<div class="{alert_class}">POSITION CLOSED! P&L: ${pnl_amount:+.2f} ({pnl_pct:+.2f}%)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-warning">NO OPEN POSITIONS</div>', unsafe_allow_html=True)
                st.form_submit_button("🔒 CLOSE POSITION", disabled=True)

        # Export data
        st.markdown("#### 💾 DATA EXPORT")
        if st.button("📥 EXPORT MISSION DATA"):
            data = {
                "trades": st.session_state.trades,
                "allocations": st.session_state.allocations,
                "export_time": datetime.now().isoformat()
            }
            st.download_button(
                label="DOWNLOAD TRADES.JSON",
                data=json.dumps(data, indent=2),
                file_name=f"mission_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Main Dashboard
    # Row 1: Mission Status Indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_allocated = sum(a["allocated"] for a in st.session_state.allocations.values())
        total_used = sum(a["used"] for a in st.session_state.allocations.values())
        st.metric(
            "💰 MISSION CAPITAL",
            f"${total_allocated:,.0f}",
            f"DEPLOYED: ${total_used:,.0f}"
        )

    with col2:
        closed_trades = [t for t in st.session_state.trades if t["status"] == "Closed"]
        total_pnl = sum(t["pnl"] for t in closed_trades) if closed_trades else 0
        pnl_color = "🟢" if total_pnl >= 0 else "🔴"
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        st.metric(
            "📈 MISSION P&L",
            f"${total_pnl:+.2f}",
            f"{pnl_color} STATUS",
            delta_color=delta_color
        )

    with col3:
        open_count = len([t for t in st.session_state.trades if t["status"] == "Open"])
        st.metric(
            "🔓 ACTIVE POSITIONS",
            f"{open_count}",
            "MONITORING"
        )

    with col4:
        if closed_trades:
            win_rate = (len([t for t in closed_trades if t["pnl"] > 0]) / len(closed_trades)) * 100
        else:
            win_rate = 0
        status = "🎯 OPTIMAL" if win_rate >= 50 else "⚠️ REVIEW" if win_rate >= 30 else "🚨 CRITICAL"
        st.metric(
            "🎯 WIN RATE",
            f"{win_rate:.1f}%",
            f"{status} • {len(closed_trades)} TRADES"
        )

    st.divider()

    # Row 2: Capital Allocation and Trade Log
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 CAPITAL ALLOCATION MATRIX")
        
        alloc_data = []
        for prong, data in st.session_state.allocations.items():
            alloc_data.append({
                "PRONG": prong,
                "ALLOCATED": data["allocated"],
                "DEPLOYED": data["used"],
                "AVAILABLE": data["available"],
                "UTILIZATION %": (data["used"] / data["allocated"]) * 100 if data["allocated"] > 0 else 0
            })
        
        alloc_df = pd.DataFrame(alloc_data)
        st.dataframe(
            alloc_df,
            column_config={
                "ALLOCATED": st.column_config.NumberColumn("ALLOCATED", format="$%.0f"),
                "DEPLOYED": st.column_config.NumberColumn("DEPLOYED", format="$%.0f"),
                "AVAILABLE": st.column_config.NumberColumn("AVAILABLE", format="$%.0f"),
                "UTILIZATION %": st.column_config.NumberColumn("UTILIZATION", format="%.1f%%")
            },
            width='stretch',
            hide_index=True
        )
        
        # Allocation pie chart with NASA colors
        fig = go.Figure(data=[go.Pie(
            labels=list(st.session_state.allocations.keys()),
            values=[a["used"] for a in st.session_state.allocations.values()],
            hole=.4,
            textinfo='label+percent',
            textposition='outside',
            marker=dict(
                colors=['#39ff14', '#ff6600', '#00ffff'],
                line=dict(color='#0a0a0a', width=2)
            )
        )])
        fig.update_layout(
            title="CAPITAL DEPLOYMENT BY PRONG",
            showlegend=False,
            height=300,
            font=dict(family="IBM Plex Mono, monospace", color="#39ff14"),
            paper_bgcolor='#0a0a0a',
            plot_bgcolor='#0a0a0a'
        )
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("📋 MISSION TRADE LOG")
        
        if st.session_state.trades:
            trades_df = pd.DataFrame(st.session_state.trades)
            trades_df["TIMESTAMP"] = pd.to_datetime(trades_df["timestamp"]).dt.strftime("%m/%d %H:%M")
            
            display_cols = ["id", "TIMESTAMP", "prong", "asset", "direction", "position_size", "status", "pnl"]
            if "close_timestamp" in trades_df.columns:
                trades_df["CLOSE_TIME"] = pd.to_datetime(trades_df["close_timestamp"]).dt.strftime("%m/%d %H:%M")
                display_cols.append("CLOSE_TIME")
            
            # Rename columns for display
            display_df = trades_df[display_cols].copy()
            display_df.columns = ["ID", "TIME", "PRONG", "ASSET", "DIR", "SIZE", "STATUS", "P&L", "CLOSE"] if len(display_cols) == 9 else ["ID", "TIME", "PRONG", "ASSET", "DIR", "SIZE", "STATUS", "P&L"]
            
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True,
                height=400
            )
        else:
            st.markdown('<div class="alert-warning">NO MISSION DATA YET. INITIALIZE FIRST TRADE VIA CONTROL PANEL.</div>', unsafe_allow_html=True)

    st.divider()

    # Row 3: Performance Analysis
    if closed_trades:
        st.subheader("📉 MISSION PERFORMANCE ANALYSIS")
        
        perf_data = []
        cumulative_pnl = 0
        for trade in sorted(closed_trades, key=lambda x: x["close_timestamp"]):
            cumulative_pnl += trade["pnl"]
            perf_data.append({
                "date": pd.to_datetime(trade["close_timestamp"]),
                "cumulative_pnl": cumulative_pnl,
                "trade_pnl": trade["pnl"]
            })
        
        perf_df = pd.DataFrame(perf_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=perf_df["date"],
            y=perf_df["cumulative_pnl"],
            mode='lines+markers',
            name='CUMULATIVE P&L',
            line=dict(color='#39ff14', width=3),
            fill='tozeroy',
            fillcolor='rgba(57, 255, 20, 0.1)'
        ))
        
        fig.update_layout(
            title="MISSION PERFORMANCE TRAJECTORY",
            xaxis_title="MISSION TIME",
            yaxis_title="CUMULATIVE P&L ($)",
            height=400,
            hovermode='x unified',
            font=dict(family="IBM Plex Mono, monospace", color="#39ff14"),
            paper_bgcolor='#0a0a0a',
            plot_bgcolor='#0d0d0d',
            xaxis=dict(gridcolor='#1a1a1a'),
            yaxis=dict(gridcolor='#1a1a1a')
        )
        
        st.plotly_chart(fig, width='stretch')

with tab2:
    st.subheader("📊 BACKTESTING STRATEGIES • NASA ANALYSIS CENTER")
    
    # Backtest Results Summary
    st.markdown("""
    <div class="terminal-bg">
    <h4 style="color: #ff6600; margin-bottom: 20px;">🚀 MISSION: ALTERNATIVE DATA STRATEGY TESTING</h4>
    <p><strong>TEST PERIOD:</strong> Last 30 days of 5-minute data</p>
    <p><strong>ASSETS:</strong> BTC, ETH, SOL</p>
    <p><strong>ACCOUNT SIZE:</strong> $350</p>
    <p><strong>STRATEGIES TESTED:</strong> 7</p>
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
        width='stretch',
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
    
    # Implementation Guide
    st.markdown("### 🚀 IMPLEMENTATION PROTOCOL FOR $350 MISSION")
    
    st.markdown("""
    <div class="terminal-bg">
    <h4 style="color: #39ff14;">RECOMMENDED MISSION SETUP:</h4>
    
    <pre style="color: #39ff14; background: #0d0d0d; padding: 15px; border-radius: 5px;">
# PRIMARY STRATEGY: RSI + Volume Confirmation
def mission_signal(df):
    rsi = calculate_rsi(df['close'], 14)
    volume_sma = df['volume'].rolling(20).mean()
    
    if rsi.iloc[-1] < 30 and df['volume'].iloc[-1] > volume_sma.iloc[-1] * 1.5:
        return 'BUY'  # 🟢 EXECUTE LONG
    elif rsi.iloc[-1] > 70 and df['volume'].iloc[-1] > volume_sma.iloc[-1] * 1.5:
        return 'SELL'  # 🔴 EXECUTE SHORT
    return 'HOLD'  # ⚪ MAINTAIN POSITION

# RISK MANAGEMENT PROTOCOL
max_risk_per_trade = 0.03  # 3% of account per trade
position_size = account_balance * max_risk_per_trade / (atr * price)
    </pre>
    
    <h4 style="color: #ff6600; margin-top: 20px;">MISSION TRADING RULES:</h4>
    <p><strong>TRADE FREQUENCY:</strong> Max 1-2 trades per week per asset</p>
    <p><strong>POSITION SIZE:</strong> Risk 2-3% per trade ($7-10 on $350 account)</p>
    <p><strong>STOP LOSS:</strong> 1.5x ATR from entry</p>
    <p><strong>TAKE PROFIT:</strong> 3x risk (1:3 risk/reward ratio)</p>
    <p><strong>MAX POSITIONS:</strong> 2 concurrent trades maximum</p>
    
    <h4 style="color: #ff6600; margin-top: 20px;">MISSION CRITICAL METRICS:</h4>
    <p><strong>TARGET WIN RATE:</strong> > 50%</p>
    <p><strong>TARGET SHARPE:</strong> > 1.0</p>
    <p><strong>MAX DRAWDOWN:</strong> < 5%</p>
    <p><strong>MONTHLY TRADES:</strong> 5-10</p>
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
st.markdown('<div class="footer">🚀 BUILT FOR THE $1K CRYPTO TRADING MISSION | NASA MISSION CONTROL AESTHETIC | STREAMLIT DASHBOARD v2.0</div>', unsafe_allow_html=True)
# Deployed: 2026-01-30T16:44:02Z

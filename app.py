#!/usr/bin/env python3
"""
Trading Dashboard v2.0 - $1K Crypto Mission
Multi-prong tracking with real-time analytics
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

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Trading Mission v2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# AUTHENTICATION (Simple password protection)
# =============================================================================
def check_password():
    """Returns True if user has correct password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Check if password is set in secrets
    if "password" not in st.secrets:
        return True  # No password configured, allow access
    
    if st.session_state.authenticated:
        return True
    
    password = st.text_input("🔐 Enter Password", type="password")
    if password:
        if hashlib.sha256(password.encode()).hexdigest() == st.secrets.get("password_hash", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
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
            "News Trading": {"allocated": 400, "current": 400, "color": "#FF6B6B"},
            "Polymarket": {"allocated": 300, "current": 300, "color": "#4ECDC4"},
            "Algorithmic": {"allocated": 300, "current": 300, "color": "#45B7D1"}
        },
        "settings": {
            "initial_capital": 1000,
            "risk_per_trade": 2.0,  # percentage
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
            st.warning("Data version mismatch, attempting import anyway...")
        
        st.session_state.trades = data.get("trades", [])
        st.session_state.positions = data.get("positions", [])
        st.session_state.alerts = data.get("alerts", [])
        st.session_state.allocations = data.get("allocations", st.session_state.allocations)
        st.session_state.settings = data.get("settings", st.session_state.settings)
        st.session_state.polymarket_watchlist = data.get("polymarket_watchlist", [])
        return True
    except Exception as e:
        st.error(f"Import failed: {e}")
        return False

# =============================================================================
# POLYMARKET API
# =============================================================================
POLYMARKET_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

@st.cache_data(ttl=60)
def fetch_polymarket_markets(limit: int = 20) -> List[Dict]:
    """Fetch trending markets from Polymarket"""
    try:
        # Use gamma API for market listings
        response = requests.get(
            f"{GAMMA_API}/markets",
            params={"limit": limit, "active": True, "closed": False},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.warning(f"Could not fetch Polymarket data: {e}")
        return []

@st.cache_data(ttl=30)
def fetch_market_price(condition_id: str) -> Optional[float]:
    """Fetch current price for a specific market"""
    try:
        response = requests.get(
            f"{POLYMARKET_API}/price",
            params={"token_id": condition_id},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 0))
        return None
    except:
        return None

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Custom metric card */
    .metric-card {
        background: linear-gradient(135deg, #1E2329 0%, #2D3748 100%);
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #3D4852;
        margin-bottom: 1rem;
    }
    
    .metric-card h4 {
        color: #9CA3AF;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    
    .metric-card .value.profit { color: #10B981; }
    .metric-card .value.loss { color: #EF4444; }
    
    /* Trade row */
    .trade-row {
        background: #1E2329;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #3B82F6;
    }
    
    .trade-row.closed { border-left-color: #6B7280; }
    .trade-row.profit { border-left-color: #10B981; }
    .trade-row.loss { border-left-color: #EF4444; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2329;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0E1117;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def calculate_portfolio_metrics() -> Dict:
    """Calculate comprehensive portfolio metrics"""
    closed_trades = [t for t in st.session_state.trades if t.get("status") == "Closed"]
    open_positions = [t for t in st.session_state.trades if t.get("status") == "Open"]
    
    # Basic metrics
    total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
    total_trades = len(closed_trades)
    winning_trades = len([t for t in closed_trades if t.get("pnl", 0) > 0])
    losing_trades = len([t for t in closed_trades if t.get("pnl", 0) < 0])
    
    # Win rate
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Average win/loss
    wins = [t.get("pnl", 0) for t in closed_trades if t.get("pnl", 0) > 0]
    losses = [t.get("pnl", 0) for t in closed_trades if t.get("pnl", 0) < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    # Profit factor
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    # Current capital
    initial_capital = st.session_state.settings.get("initial_capital", 1000)
    current_capital = initial_capital + total_pnl
    
    # Open exposure
    open_exposure = sum(t.get("position_size", 0) for t in open_positions)
    
    # Best/worst trade
    all_pnls = [t.get("pnl", 0) for t in closed_trades]
    best_trade = max(all_pnls) if all_pnls else 0
    worst_trade = min(all_pnls) if all_pnls else 0
    
    # By prong breakdown
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
    
    # Update allocation
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
            
            # Calculate P&L
            if trade.get("prong") == "Polymarket":
                # For Polymarket: exit_price is the probability (0-1)
                pnl = (exit_price - entry) * size * direction
                pnl_pct = ((exit_price - entry) / entry * 100 * direction) if entry > 0 else 0
            else:
                # For crypto: standard percentage calculation
                pnl_pct = ((exit_price - entry) / entry * 100 * direction) if entry > 0 else 0
                pnl = size * (pnl_pct / 100)
            
            trade["status"] = "Closed"
            trade["exit_price"] = exit_price
            trade["pnl"] = pnl
            trade["pnl_pct"] = pnl_pct
            trade["closed_at"] = datetime.now().isoformat()
            trade["close_notes"] = notes
            
            # Return allocation
            prong = trade.get("prong")
            if prong in st.session_state.allocations:
                st.session_state.allocations[prong]["current"] += size
            
            return trade
    return None

# =============================================================================
# MAIN APP
# =============================================================================
def main():
    init_session_state()
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("# ⚡ Trading Mission v2.0")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Calculate metrics
    metrics = calculate_portfolio_metrics()
    
    # ==========================================================================
    # TOP METRICS ROW
    # ==========================================================================
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        pnl_color = "profit" if metrics["total_pnl"] >= 0 else "loss"
        st.markdown(f"""
        <div class="metric-card">
            <h4>💰 Total P&L</h4>
            <div class="value {pnl_color}">${metrics['total_pnl']:+,.2f}</div>
            <small style="color: #9CA3AF">{metrics['total_pnl_pct']:+.1f}%</small>
        </div>
        """, unsafe_allow_html=True)
    
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📊 Current Capital</h4>
            <div class="value">${metrics['current_capital']:,.2f}</div>
            <small style="color: #9CA3AF">of ${st.session_state.settings['initial_capital']:,}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎯 Win Rate</h4>
            <div class="value">{metrics['win_rate']:.1f}%</div>
            <small style="color: #9CA3AF">{metrics['winning_trades']}W / {metrics['losing_trades']}L</small>
        </div>
        """, unsafe_allow_html=True)
    
    with m4:
        pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] < 100 else "∞"
        st.markdown(f"""
        <div class="metric-card">
            <h4>📈 Profit Factor</h4>
            <div class="value">{pf_display}</div>
            <small style="color: #9CA3AF">Avg W: ${metrics['avg_win']:.2f}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🔓 Open Positions</h4>
            <div class="value">{metrics['open_positions']}</div>
            <small style="color: #9CA3AF">${metrics['open_exposure']:.2f} exposed</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==========================================================================
    # MAIN TABS
    # ==========================================================================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "🤖 Live Bot",
        "📝 Trade Entry", 
        "🎰 Polymarket", 
        "📈 Analytics",
        "⚙️ Settings"
    ])
    
    # ==========================================================================
    # TAB 1: DASHBOARD
    # ==========================================================================
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("💼 Capital Allocation")
            
            # Allocation bars
            for prong, data in st.session_state.allocations.items():
                allocated = data["allocated"]
                current = data["current"]
                used = allocated - current
                pct = (used / allocated * 100) if allocated > 0 else 0
                
                st.markdown(f"**{prong}**")
                st.progress(pct / 100, text=f"${used:.0f} / ${allocated:.0f} ({pct:.0f}%)")
                
                # P&L by prong
                prong_pnl = metrics["prong_pnl"].get(prong, 0)
                pnl_style = "color: #10B981" if prong_pnl >= 0 else "color: #EF4444"
                st.markdown(f"<small style='{pnl_style}'>P&L: ${prong_pnl:+.2f}</small>", unsafe_allow_html=True)
                st.markdown("---")
            
            # Allocation pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(st.session_state.allocations.keys()),
                values=[d["allocated"] - d["current"] for d in st.session_state.allocations.values()],
                hole=0.5,
                marker_colors=[d["color"] for d in st.session_state.allocations.values()],
                textinfo='label+percent',
                textposition='outside'
            )])
            fig.update_layout(
                showlegend=False,
                height=250,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📋 Recent Trades")
            
            if st.session_state.trades:
                # Sort by most recent
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
                        row_class = ""
                    
                    direction_emoji = "🟢" if trade.get("direction") == "Long" else "🔴"
                    status_badge = "🔓" if status == "Open" else ("✅" if pnl >= 0 else "❌")
                    
                    st.markdown(f"""
                    <div class="trade-row {row_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{direction_emoji} {trade.get('asset', 'N/A')}</strong>
                                <span style="color: #9CA3AF; margin-left: 10px;">{trade.get('prong', '')}</span>
                            </div>
                            <div>
                                <span style="color: #9CA3AF;">${trade.get('position_size', 0):.2f}</span>
                                {f'<span style="color: {"#10B981" if pnl >= 0 else "#EF4444"}; margin-left: 10px;">${pnl:+.2f}</span>' if status == "Closed" else ""}
                                <span style="margin-left: 10px;">{status_badge}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No trades yet. Head to 'Trade Entry' to log your first trade!")
    
    # ==========================================================================
    # TAB 2: LIVE BOT
    # ==========================================================================
    with tab2:
        st.subheader("🤖 Automated Trading Bot")
        
        # Load bot data
        try:
            import os
            bot_data_path = os.path.join(os.path.dirname(__file__), 'bot_data.json')
            with open(bot_data_path, 'r') as f:
                bot_data = json.load(f)
            
            last_update = bot_data.get('last_updated', 'Unknown')
            st.caption(f"Last sync: {last_update}")
            
            # Account summary
            account = bot_data.get('account', {})
            total_usd = account.get('total_usd', 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Bot Balance", f"${total_usd:,.2f}")
            with col2:
                state = bot_data.get('trading_state', {})
                daily_pnl = state.get('daily_pnl', 0)
                st.metric("📊 Daily P&L", f"${daily_pnl:+,.2f}")
            with col3:
                daily_trades = state.get('daily_trades', 0)
                st.metric("🔢 Trades Today", daily_trades)
            
            st.divider()
            
            # Balances
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**💼 Holdings**")
                balances = account.get('balances', [])
                if balances:
                    for b in balances:
                        currency = b.get('currency', '?')
                        amount = b.get('amount', 0)
                        usd = b.get('usd_value', 0)
                        st.markdown(f"• **{currency}**: {amount:.6f} (${usd:.2f})")
                else:
                    st.info("No balance data")
            
            with col2:
                st.markdown("**📈 Markets**")
                markets = bot_data.get('markets', [])
                if markets:
                    for m in markets[:5]:
                        symbol = m.get('symbol', '?')
                        price = m.get('price', 0)
                        change = m.get('change_24h', 0)
                        emoji = "🟢" if change >= 0 else "🔴"
                        st.markdown(f"{emoji} **{symbol}**: ${price:,.2f} ({change:+.1f}%)")
                else:
                    st.info("No market data")
            
            st.divider()
            
            # Performance
            perf = bot_data.get('performance', {})
            if perf.get('total_trades', 0) > 0:
                st.markdown("**📊 Bot Performance**")
                p1, p2, p3, p4 = st.columns(4)
                with p1:
                    st.metric("Total Trades", perf.get('total_trades', 0))
                with p2:
                    st.metric("Win Rate", f"{perf.get('win_rate', 0)}%")
                with p3:
                    st.metric("Total P&L", f"${perf.get('total_pnl', 0):+.2f}")
                with p4:
                    st.metric("Winning", perf.get('winning_trades', 0))
            
            # Recent trades
            trades = bot_data.get('recent_trades', [])
            if trades:
                st.markdown("**📜 Recent Bot Trades**")
                trades_df = pd.DataFrame(trades[-10:])
                st.dataframe(trades_df, use_container_width=True, hide_index=True)
            
        except FileNotFoundError:
            st.warning("⚠️ Bot data not found. Waiting for first sync...")
            st.info("The trading bot syncs data hourly. Check back soon!")
        except Exception as e:
            st.error(f"Error loading bot data: {e}")
    
    # ==========================================================================
    # TAB 3: TRADE ENTRY
    # ==========================================================================
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ New Trade")
            
            with st.form("new_trade", clear_on_submit=True):
                prong = st.selectbox("Strategy Prong", list(st.session_state.allocations.keys()))
                asset = st.text_input("Asset/Market", placeholder="e.g., BTC, ETH, 'Trump wins 2024'")
                
                c1, c2 = st.columns(2)
                with c1:
                    direction = st.selectbox("Direction", ["Long", "Short"])
                with c2:
                    available = st.session_state.allocations[prong]["current"]
                    position_size = st.number_input(
                        f"Size (${available:.0f} avail)", 
                        min_value=0.0, 
                        max_value=float(available),
                        step=10.0
                    )
                
                c1, c2 = st.columns(2)
                with c1:
                    entry_price = st.number_input("Entry Price", min_value=0.0, step=0.0001, format="%.4f")
                with c2:
                    target = st.number_input("Target", min_value=0.0, step=0.0001, format="%.4f")
                
                stop_loss = st.number_input("Stop Loss", min_value=0.0, step=0.0001, format="%.4f")
                thesis = st.text_area("Trade Thesis", placeholder="Why are you taking this trade?")
                
                if st.form_submit_button("🚀 Enter Trade", use_container_width=True):
                    if asset and position_size > 0:
                        trade = add_trade({
                            "prong": prong,
                            "asset": asset,
                            "direction": direction,
                            "position_size": position_size,
                            "entry_price": entry_price,
                            "target": target,
                            "stop_loss": stop_loss,
                            "thesis": thesis
                        })
                        st.success(f"✅ Trade #{trade['id']} entered: {direction} {asset}")
                        st.rerun()
                    else:
                        st.error("Please fill in asset and position size")
        
        with col2:
            st.subheader("🔒 Close Position")
            
            open_trades = [t for t in st.session_state.trades if t.get("status") == "Open"]
            
            if open_trades:
                with st.form("close_trade"):
                    trade_options = {
                        f"#{t['id']} - {t['asset']} ({t['direction']}) - ${t['position_size']:.2f}": t 
                        for t in open_trades
                    }
                    selected = st.selectbox("Select Position", list(trade_options.keys()))
                    trade = trade_options[selected]
                    
                    st.info(f"Entry: ${trade['entry_price']:.4f} | Target: ${trade.get('target', 0):.4f} | Stop: ${trade.get('stop_loss', 0):.4f}")
                    
                    exit_price = st.number_input("Exit Price", min_value=0.0, step=0.0001, format="%.4f")
                    close_notes = st.text_area("Close Notes", placeholder="What happened?")
                    
                    if st.form_submit_button("🔒 Close Position", use_container_width=True):
                        result = close_trade(trade["id"], exit_price, close_notes)
                        if result:
                            pnl = result["pnl"]
                            emoji = "🎉" if pnl >= 0 else "😤"
                            st.success(f"{emoji} Position closed! P&L: ${pnl:+.2f} ({result['pnl_pct']:+.1f}%)")
                            st.rerun()
            else:
                st.info("No open positions to close")
    
    # ==========================================================================
    # TAB 4: POLYMARKET
    # ==========================================================================
    with tab4:
        st.subheader("🎰 Polymarket Live")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            markets = fetch_polymarket_markets(20)
            
            if markets:
                for market in markets[:10]:
                    title = market.get("question", market.get("title", "Unknown"))
                    volume = market.get("volume", 0)
                    liquidity = market.get("liquidity", 0)
                    
                    # Get outcomes/prices
                    outcomes = market.get("outcomes", [])
                    
                    with st.expander(f"📊 {title[:80]}...", expanded=False):
                        c1, c2 = st.columns(2)
                        with c1:
                            vol_display = f"${volume:,.0f}" if volume else "N/A"
                            st.metric("Volume", vol_display)
                        with c2:
                            liq_display = f"${liquidity:,.0f}" if liquidity else "N/A"
                            st.metric("Liquidity", liq_display)
                        
                        if outcomes:
                            for outcome in outcomes[:2]:
                                name = outcome if isinstance(outcome, str) else outcome.get("name", "?")
                                price = outcome.get("price", "?") if isinstance(outcome, dict) else "?"
                                st.write(f"• {name}: {price}")
                        
                        if st.button(f"📌 Add to Watchlist", key=f"watch_{market.get('id', title[:20])}"):
                            st.session_state.polymarket_watchlist.append({
                                "title": title,
                                "id": market.get("id"),
                                "added_at": datetime.now().isoformat()
                            })
                            st.success("Added to watchlist!")
            else:
                st.warning("Could not fetch Polymarket data. API may be rate-limited.")
                st.info("Tip: You can manually enter Polymarket trades in the Trade Entry tab.")
        
        with col2:
            st.subheader("📌 Watchlist")
            
            if st.session_state.polymarket_watchlist:
                for i, item in enumerate(st.session_state.polymarket_watchlist):
                    with st.container():
                        st.markdown(f"**{item['title'][:50]}...**")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("🗑️", key=f"del_watch_{i}"):
                                st.session_state.polymarket_watchlist.pop(i)
                                st.rerun()
                        with c2:
                            if st.button("📝 Trade", key=f"trade_watch_{i}"):
                                st.info("Head to Trade Entry tab with this market")
                        st.divider()
            else:
                st.info("No markets in watchlist. Browse markets on the left and add some!")
    
    # ==========================================================================
    # TAB 5: ANALYTICS
    # ==========================================================================
    with tab5:
        st.subheader("📈 Performance Analytics")
        
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
                    fillcolor='rgba(59, 130, 246, 0.2)',
                    line=dict(color='#3B82F6', width=3),
                    hovertemplate='Trade: %{text}<br>Cumulative P&L: $%{y:.2f}<extra></extra>',
                    text=cum_df["trade"]
                ))
                fig.update_layout(
                    title="Cumulative P&L",
                    xaxis_title="Trade #",
                    yaxis_title="P&L ($)",
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # P&L distribution
                pnls = [t.get("pnl", 0) for t in closed_trades]
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=pnls,
                    nbinsx=20,
                    marker_color=['#10B981' if p >= 0 else '#EF4444' for p in sorted(pnls)]
                ))
                fig.update_layout(
                    title="P&L Distribution",
                    xaxis_title="P&L ($)",
                    yaxis_title="Frequency",
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance by prong
            st.subheader("📊 Performance by Strategy")
            
            prong_data = []
            for prong in st.session_state.allocations.keys():
                prong_trades = [t for t in closed_trades if t.get("prong") == prong]
                if prong_trades:
                    wins = len([t for t in prong_trades if t.get("pnl", 0) > 0])
                    total = len(prong_trades)
                    pnl = sum(t.get("pnl", 0) for t in prong_trades)
                    prong_data.append({
                        "Strategy": prong,
                        "Trades": total,
                        "Win Rate": f"{wins/total*100:.1f}%" if total > 0 else "N/A",
                        "Total P&L": f"${pnl:+.2f}",
                        "Avg Trade": f"${pnl/total:+.2f}" if total > 0 else "N/A"
                    })
            
            if prong_data:
                st.dataframe(pd.DataFrame(prong_data), use_container_width=True, hide_index=True)
            
            # Trade log
            st.subheader("📜 Full Trade History")
            trades_df = pd.DataFrame(closed_trades)
            display_cols = ["id", "prong", "asset", "direction", "position_size", "entry_price", "exit_price", "pnl", "pnl_pct"]
            available_cols = [c for c in display_cols if c in trades_df.columns]
            st.dataframe(
                trades_df[available_cols].sort_values("id", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No closed trades yet. Complete some trades to see analytics!")
    
    # ==========================================================================
    # TAB 6: SETTINGS
    # ==========================================================================
    with tab6:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ Configuration")
            
            with st.form("settings_form"):
                initial_capital = st.number_input(
                    "Initial Capital ($)", 
                    value=st.session_state.settings.get("initial_capital", 1000),
                    step=100
                )
                
                risk_per_trade = st.slider(
                    "Risk Per Trade (%)",
                    min_value=0.5,
                    max_value=10.0,
                    value=st.session_state.settings.get("risk_per_trade", 2.0),
                    step=0.5
                )
                
                st.markdown("**Allocation Adjustment**")
                new_allocations = {}
                for prong, data in st.session_state.allocations.items():
                    new_alloc = st.number_input(
                        f"{prong} Allocation",
                        value=data["allocated"],
                        step=50,
                        key=f"alloc_{prong}"
                    )
                    new_allocations[prong] = new_alloc
                
                if st.form_submit_button("💾 Save Settings"):
                    st.session_state.settings["initial_capital"] = initial_capital
                    st.session_state.settings["risk_per_trade"] = risk_per_trade
                    
                    for prong, new_alloc in new_allocations.items():
                        old_alloc = st.session_state.allocations[prong]["allocated"]
                        diff = new_alloc - old_alloc
                        st.session_state.allocations[prong]["allocated"] = new_alloc
                        st.session_state.allocations[prong]["current"] += diff
                    
                    st.success("Settings saved!")
                    st.rerun()
        
        with col2:
            st.subheader("💾 Data Management")
            
            # Export
            st.markdown("**Export Data**")
            export_json = export_data()
            st.download_button(
                "📥 Download Backup",
                data=export_json,
                file_name=f"trading_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.divider()
            
            # Import
            st.markdown("**Import Data**")
            uploaded_file = st.file_uploader("Upload backup file", type="json")
            if uploaded_file:
                if st.button("📤 Import Data", use_container_width=True):
                    content = uploaded_file.read().decode("utf-8")
                    if import_data(content):
                        st.success("Data imported successfully!")
                        st.rerun()
            
            st.divider()
            
            # Reset
            st.markdown("**⚠️ Danger Zone**")
            if st.button("🗑️ Reset All Data", type="secondary", use_container_width=True):
                st.warning("This will delete all trades and reset allocations!")
                if st.button("Yes, I'm sure - DELETE EVERYTHING", type="primary"):
                    for key in ["trades", "positions", "alerts", "polymarket_watchlist"]:
                        st.session_state[key] = []
                    st.session_state.allocations = {
                        "News Trading": {"allocated": 400, "current": 400, "color": "#FF6B6B"},
                        "Polymarket": {"allocated": 300, "current": 300, "color": "#4ECDC4"},
                        "Algorithmic": {"allocated": 300, "current": 300, "color": "#45B7D1"}
                    }
                    st.success("All data reset!")
                    st.rerun()
    
    # ==========================================================================
    # SIDEBAR
    # ==========================================================================
    with st.sidebar:
        st.markdown("### ⚡ Quick Stats")
        st.metric("Capital", f"${metrics['current_capital']:,.0f}", f"{metrics['total_pnl_pct']:+.1f}%")
        st.metric("Open", f"{metrics['open_positions']}", f"${metrics['open_exposure']:.0f}")
        
        st.divider()
        
        st.markdown("### 📊 By Strategy")
        for prong, pnl in metrics["prong_pnl"].items():
            color = "🟢" if pnl >= 0 else "🔴"
            st.markdown(f"{color} **{prong}**: ${pnl:+.2f}")
        
        st.divider()
        
        st.markdown("### 🔗 Quick Links")
        st.markdown("[Polymarket](https://polymarket.com)")
        st.markdown("[TradingView](https://tradingview.com)")
        st.markdown("[CoinGecko](https://coingecko.com)")
        
        st.divider()
        
        st.caption("v2.0 | Built for the $1K Mission")

# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    main()

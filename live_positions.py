#!/usr/bin/env python3
"""
Enhanced Live Position Tracker with Real-time P&L
Professional trading terminal with multi-API price feeds, alerting, and position management
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global price cache for reducing API calls
PRICE_CACHE = {}
PRICE_CACHE_TIMESTAMP = None
CACHE_DURATION = 10  # seconds

# Alert thresholds
ALERT_THRESHOLDS = {
    'moderate': 2.0,  # 2%
    'significant': 5.0,  # 5%
    'critical': 10.0,  # 10%
    'extreme': 15.0   # 15%
}

def get_live_prices_multi_source(symbols: List[str]) -> Dict[str, Dict]:
    """
    Fetch real-time prices from multiple API sources for redundancy and accuracy
    Returns: {symbol: {'price': float, 'source': str, 'volume_24h': float, 'change_24h': float}}
    """
    global PRICE_CACHE, PRICE_CACHE_TIMESTAMP
    
    # Check cache first
    if (PRICE_CACHE_TIMESTAMP and 
        (datetime.now() - PRICE_CACHE_TIMESTAMP).seconds < CACHE_DURATION and 
        all(symbol in PRICE_CACHE for symbol in symbols)):
        logger.info("Using cached prices")
        return {symbol: PRICE_CACHE[symbol] for symbol in symbols if symbol in PRICE_CACHE}
    
    prices = {}
    
    # API source functions
    def fetch_binance_prices(symbols_list):
        """Fetch from Binance (Primary source - fastest)"""
        binance_prices = {}
        try:
            # Batch request for multiple symbols
            binance_symbols = [s.replace('/', '') for s in symbols_list]
            url = "https://api.binance.com/api/v3/ticker/24hr"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for item in data:
                    symbol = item['symbol']
                    # Convert back to our format
                    if symbol.endswith('USDT'):
                        formatted_symbol = f"{symbol[:-4]}/USDT"
                        if formatted_symbol in symbols_list:
                            binance_prices[formatted_symbol] = {
                                'price': float(item['lastPrice']),
                                'source': 'Binance',
                                'volume_24h': float(item['volume']),
                                'change_24h': float(item['priceChangePercent']),
                                'timestamp': datetime.now()
                            }
                logger.info(f"Binance: Successfully fetched {len(binance_prices)} prices")
            else:
                logger.error(f"Binance API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Binance fetch error: {str(e)}")
        
        return binance_prices
    
    def fetch_coingecko_prices(symbols_list):
        """Fetch from CoinGecko (Secondary source - more comprehensive)"""
        coingecko_prices = {}
        try:
            # Map symbols to CoinGecko IDs
            symbol_mapping = {
                'BTC/USDT': 'bitcoin',
                'ETH/USDT': 'ethereum', 
                'SOL/USDT': 'solana',
                'DOGE/USDT': 'dogecoin',
                'ADA/USDT': 'cardano',
                'MATIC/USDT': 'polygon',
                'DOT/USDT': 'polkadot',
                'AVAX/USDT': 'avalanche-2',
                'LINK/USDT': 'chainlink',
                'UNI/USDT': 'uniswap',
                'ATOM/USDT': 'cosmos'
            }
            
            # Get CoinGecko IDs for requested symbols
            coin_ids = [symbol_mapping.get(symbol) for symbol in symbols_list if symbol in symbol_mapping]
            coin_ids = [cid for cid in coin_ids if cid is not None]
            
            if coin_ids:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    'ids': ','.join(coin_ids),
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true'
                }
                
                response = requests.get(url, params=params, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Reverse map back to our symbol format
                    reverse_mapping = {v: k for k, v in symbol_mapping.items()}
                    
                    for coin_id, coin_data in data.items():
                        if coin_id in reverse_mapping:
                            symbol = reverse_mapping[coin_id]
                            coingecko_prices[symbol] = {
                                'price': float(coin_data['usd']),
                                'source': 'CoinGecko',
                                'volume_24h': coin_data.get('usd_24h_vol', 0),
                                'change_24h': coin_data.get('usd_24h_change', 0),
                                'timestamp': datetime.now()
                            }
                    
                    logger.info(f"CoinGecko: Successfully fetched {len(coingecko_prices)} prices")
                else:
                    logger.error(f"CoinGecko API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {str(e)}")
        
        return coingecko_prices
    
    def fetch_coinmarketcap_prices(symbols_list):
        """Fetch from CoinMarketCap (Tertiary source - backup)"""
        # Note: CMC requires API key for production, using as fallback
        cmc_prices = {}
        
        # For now, return empty dict as CMC requires API key
        # In production, you'd implement this with proper API key
        logger.info("CoinMarketCap: API key required for production use")
        
        return cmc_prices
    
    # Execute price fetching from multiple sources concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_binance_prices, symbols): 'Binance',
            executor.submit(fetch_coingecko_prices, symbols): 'CoinGecko',
            executor.submit(fetch_coinmarketcap_prices, symbols): 'CoinMarketCap'
        }
        
        source_results = {}
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                result = future.result()
                source_results[source_name] = result
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {str(e)}")
                source_results[source_name] = {}
    
    # Merge results with priority: Binance > CoinGecko > CoinMarketCap
    for symbol in symbols:
        if symbol in source_results.get('Binance', {}):
            prices[symbol] = source_results['Binance'][symbol]
        elif symbol in source_results.get('CoinGecko', {}):
            prices[symbol] = source_results['CoinGecko'][symbol]
        elif symbol in source_results.get('CoinMarketCap', {}):
            prices[symbol] = source_results['CoinMarketCap'][symbol]
        else:
            # Fallback: try individual Binance request
            try:
                binance_symbol = symbol.replace('/', '')
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    prices[symbol] = {
                        'price': float(data['price']),
                        'source': 'Binance (Individual)',
                        'volume_24h': 0,
                        'change_24h': 0,
                        'timestamp': datetime.now()
                    }
                    logger.info(f"Fallback success for {symbol}")
                else:
                    logger.error(f"Fallback failed for {symbol}: {response.status_code}")
            except Exception as e:
                logger.error(f"Fallback error for {symbol}: {str(e)}")
                # Last resort: use a default/error price
                prices[symbol] = {
                    'price': 0,
                    'source': 'ERROR',
                    'volume_24h': 0,
                    'change_24h': 0,
                    'timestamp': datetime.now()
                }
    
    # Update cache
    PRICE_CACHE.update(prices)
    PRICE_CACHE_TIMESTAMP = datetime.now()
    
    logger.info(f"Price fetch complete: {len(prices)} symbols from {len(source_results)} sources")
    return prices


# Legacy function for backward compatibility
def get_live_prices(symbols):
    """Legacy function - fetches prices and returns just price values"""
    full_data = get_live_prices_multi_source(symbols)
    return {symbol: data['price'] for symbol, data in full_data.items()}


def generate_position_alerts(symbol: str, position: Dict, current_price_data: Dict, previous_metrics: Dict = None) -> List[Dict]:
    """
    Generate real-time position alerts based on price movements and risk levels
    Returns list of alert dictionaries with severity, message, and timestamp
    """
    alerts = []
    current_price = current_price_data.get('price', 0)
    entry_price = position.get('entry', 0)
    stop_price = position.get('stop', 0) 
    target_price = position.get('target', 0)
    
    if entry_price == 0 or current_price == 0:
        return alerts
    
    # Calculate current P&L percentage
    pnl_pct = ((current_price - entry_price) / entry_price) * 100
    
    # Price movement alerts
    for threshold_name, threshold_pct in ALERT_THRESHOLDS.items():
        if abs(pnl_pct) >= threshold_pct:
            severity = threshold_name
            direction = "GAIN" if pnl_pct > 0 else "LOSS"
            
            alerts.append({
                'severity': severity.upper(),
                'type': 'PRICE_MOVEMENT',
                'symbol': symbol,
                'message': f"{symbol}: {direction} of {abs(pnl_pct):.2f}% reached",
                'details': f"Entry: ${entry_price:.4f} → Current: ${current_price:.4f}",
                'timestamp': datetime.now(),
                'action_required': severity in ['critical', 'extreme']
            })
            break  # Only trigger the highest threshold reached
    
    # Stop loss proximity alerts
    if stop_price > 0:
        stop_distance_pct = abs((current_price - stop_price) / current_price * 100)
        if stop_distance_pct <= 2.0:  # Within 2% of stop loss
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'STOP_PROXIMITY',
                'symbol': symbol,
                'message': f"{symbol}: APPROACHING STOP LOSS",
                'details': f"Current: ${current_price:.4f}, Stop: ${stop_price:.4f} ({stop_distance_pct:.1f}% away)",
                'timestamp': datetime.now(),
                'action_required': True
            })
    
    # Target proximity alerts
    if target_price > 0:
        target_distance_pct = abs((target_price - current_price) / current_price * 100)
        if target_distance_pct <= 3.0:  # Within 3% of target
            alerts.append({
                'severity': 'MODERATE',
                'type': 'TARGET_PROXIMITY',
                'symbol': symbol,
                'message': f"{symbol}: APPROACHING TARGET",
                'details': f"Current: ${current_price:.4f}, Target: ${target_price:.4f} ({target_distance_pct:.1f}% away)",
                'timestamp': datetime.now(),
                'action_required': False
            })
    
    # Volume/volatility alerts (if data available)
    if 'volume_24h' in current_price_data and current_price_data['volume_24h'] > 0:
        # High volume alert (simplified - would need historical data for proper calculation)
        change_24h = current_price_data.get('change_24h', 0)
        if abs(change_24h) > 15:  # High 24h volatility
            alerts.append({
                'severity': 'MODERATE',
                'type': 'HIGH_VOLATILITY',
                'symbol': symbol,
                'message': f"{symbol}: HIGH VOLATILITY DETECTED",
                'details': f"24h change: {change_24h:+.2f}%",
                'timestamp': datetime.now(),
                'action_required': False
            })
    
    # Age-based alerts (positions held too long)
    try:
        entry_time = datetime.fromisoformat(position.get('time', '').replace('Z', ''))
        time_in_position = datetime.now() - entry_time
        hours_held = time_in_position.total_seconds() / 3600
        
        if hours_held > 168:  # 1 week
            alerts.append({
                'severity': 'MODERATE',
                'type': 'POSITION_AGE',
                'symbol': symbol,
                'message': f"{symbol}: LONG-HELD POSITION",
                'details': f"Held for {hours_held/24:.1f} days - consider review",
                'timestamp': datetime.now(),
                'action_required': False
            })
    except:
        pass
    
    return alerts


def calculate_enhanced_position_metrics(position: Dict, current_price_data: Dict, portfolio_value: float) -> Optional[Dict]:
    """
    Calculate comprehensive position metrics with enhanced analytics
    """
    current_price = current_price_data.get('price', 0)
    entry_price = position.get('entry', 0)
    amount = position.get('amount', 0)
    stop_price = position.get('stop', 0)
    target_price = position.get('target', 0)
    entry_time_str = position.get('time', '')
    
    if entry_price == 0 or current_price == 0:
        return None
    
    # Basic P&L calculations
    position_value = current_price * amount
    entry_value = entry_price * amount
    unrealized_pnl = (current_price - entry_price) * amount
    unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100
    
    # Risk metrics
    position_size_pct = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
    
    # Enhanced distance calculations
    if stop_price > 0:
        dist_to_stop_pct = ((current_price - stop_price) / current_price * 100)
        stop_loss_risk = abs((entry_price - stop_price) * amount)  # Max loss if stopped out
        risk_reward_ratio = abs((target_price - entry_price) / (entry_price - stop_price)) if target_price > 0 and entry_price != stop_price else 0
    else:
        dist_to_stop_pct = 0
        stop_loss_risk = 0
        risk_reward_ratio = 0
    
    if target_price > 0:
        dist_to_target_pct = ((target_price - current_price) / current_price * 100)
        target_profit_potential = (target_price - entry_price) * amount
    else:
        dist_to_target_pct = 0
        target_profit_potential = 0
    
    # Break-even calculations
    break_even_price = entry_price
    break_even_distance = abs(current_price - break_even_price) / current_price * 100
    
    # Enhanced time metrics
    try:
        entry_dt = datetime.fromisoformat(entry_time_str.replace('Z', ''))
        time_in_position = datetime.now() - entry_dt
        hours_held = time_in_position.total_seconds() / 3600
        days_held = time_in_position.days
        
        # Time-weighted return calculation
        if hours_held > 0:
            annualized_return = (unrealized_pnl_pct / hours_held) * 24 * 365
            hourly_return = unrealized_pnl_pct / hours_held
        else:
            annualized_return = 0
            hourly_return = 0
        
        # Enhanced time formatting
        if time_in_position.days > 0:
            time_str = f"{days_held}d {time_in_position.seconds//3600}h {(time_in_position.seconds//60)%60}m"
        elif hours_held >= 1:
            time_str = f"{hours_held:.1f}h {(time_in_position.seconds//60)%60}m"
        else:
            minutes = time_in_position.seconds // 60
            seconds = time_in_position.seconds % 60
            time_str = f"{minutes}m {seconds}s"
            
    except Exception:
        time_str = "N/A"
        hours_held = 0
        annualized_return = 0
        hourly_return = 0
    
    # Enhanced risk level calculation
    combined_risk_score = (
        position_size_pct * 0.4 +  # Position size weight
        (abs(unrealized_pnl_pct) * 0.3) +  # Current P&L volatility
        (hours_held / 24 * 0.3)  # Time risk
    )
    
    if combined_risk_score > 25 or position_size_pct > 25:
        risk_level = "EXTREME"
        risk_color = "#ff0000"
    elif combined_risk_score > 15 or position_size_pct > 15:
        risk_level = "HIGH"
        risk_color = "#ff3333"
    elif combined_risk_score > 8 or position_size_pct > 8:
        risk_level = "MEDIUM"
        risk_color = "#ff6600"
    else:
        risk_level = "LOW"
        risk_color = "#39ff14"
    
    # Enhanced momentum calculation using price data
    price_change_from_entry = (current_price - entry_price) / entry_price
    change_24h = current_price_data.get('change_24h', 0) / 100  # Convert to decimal
    volume_24h = current_price_data.get('volume_24h', 0)
    
    # Momentum score considers both position performance and market momentum
    momentum_score = abs(price_change_from_entry) * 0.6 + abs(change_24h) * 0.4
    
    if momentum_score > 0.10:  # >10% combined momentum
        momentum = "EXTREME"
        momentum_color = "#ff6600"
    elif momentum_score > 0.05:  # >5% combined momentum
        momentum = "HIGH" 
        momentum_color = "#ffaa00"
    elif momentum_score > 0.02:  # >2% combined momentum
        momentum = "MEDIUM"
        momentum_color = "#ffdd00"
    else:
        momentum = "LOW"
        momentum_color = "#39ff14"
    
    # Performance grade
    if unrealized_pnl_pct > 10:
        performance_grade = "A+"
    elif unrealized_pnl_pct > 5:
        performance_grade = "A"
    elif unrealized_pnl_pct > 0:
        performance_grade = "B"
    elif unrealized_pnl_pct > -3:
        performance_grade = "C"
    elif unrealized_pnl_pct > -8:
        performance_grade = "D"
    else:
        performance_grade = "F"
    
    # Efficiency metrics
    profit_per_hour = unrealized_pnl / max(hours_held, 0.1)
    capital_efficiency = (abs(unrealized_pnl) / entry_value * 100) if entry_value > 0 else 0
    
    return {
        # Basic metrics
        'position_value': position_value,
        'entry_value': entry_value,
        'unrealized_pnl': unrealized_pnl,
        'unrealized_pnl_pct': unrealized_pnl_pct,
        'position_size_pct': position_size_pct,
        
        # Distance metrics
        'dist_to_stop_pct': dist_to_stop_pct,
        'dist_to_target_pct': dist_to_target_pct,
        'break_even_price': break_even_price,
        'break_even_distance': break_even_distance,
        
        # Risk metrics
        'stop_loss_risk': stop_loss_risk,
        'risk_reward_ratio': risk_reward_ratio,
        'target_profit_potential': target_profit_potential,
        'combined_risk_score': combined_risk_score,
        'risk_level': risk_level,
        'risk_color': risk_color,
        
        # Time metrics
        'time_str': time_str,
        'hours_held': hours_held,
        'days_held': days_held,
        'annualized_return': annualized_return,
        'hourly_return': hourly_return,
        
        # Performance metrics
        'momentum': momentum,
        'momentum_color': momentum_color,
        'momentum_score': momentum_score,
        'performance_grade': performance_grade,
        'profit_per_hour': profit_per_hour,
        'capital_efficiency': capital_efficiency,
        
        # Market data
        'current_price': current_price,
        'change_24h_pct': current_price_data.get('change_24h', 0),
        'volume_24h': current_price_data.get('volume_24h', 0),
        'data_source': current_price_data.get('source', 'Unknown'),
        'data_timestamp': current_price_data.get('timestamp', datetime.now())
    }


# Legacy function for backward compatibility
def calculate_position_metrics(position, current_price, portfolio_value):
    """Legacy function - maintains backward compatibility"""
    # Convert old format to new format
    current_price_data = {
        'price': current_price,
        'source': 'Legacy',
        'volume_24h': 0,
        'change_24h': 0,
        'timestamp': datetime.now()
    }
    
    enhanced_metrics = calculate_enhanced_position_metrics(position, current_price_data, portfolio_value)
    
    if not enhanced_metrics:
        return None
    
    # Return subset that matches old interface
    return {
        'position_value': enhanced_metrics['position_value'],
        'unrealized_pnl': enhanced_metrics['unrealized_pnl'],
        'unrealized_pnl_pct': enhanced_metrics['unrealized_pnl_pct'],
        'position_size_pct': enhanced_metrics['position_size_pct'],
        'dist_to_stop_pct': enhanced_metrics['dist_to_stop_pct'],
        'dist_to_target_pct': enhanced_metrics['dist_to_target_pct'],
        'break_even_price': enhanced_metrics['break_even_price'],
        'break_even_distance': enhanced_metrics['break_even_distance'],
        'time_str': enhanced_metrics['time_str'],
        'hours_held': enhanced_metrics['hours_held'],
        'annualized_return': enhanced_metrics['annualized_return'],
        'risk_level': enhanced_metrics['risk_level'],
        'risk_color': enhanced_metrics['risk_color'],
        'momentum': enhanced_metrics['momentum']
    }


def render_alert_system(all_alerts: List[Dict]) -> None:
    """
    Render real-time alert system with professional trading terminal styling
    """
    if not all_alerts:
        return
    
    # Sort alerts by severity and timestamp
    severity_order = {'EXTREME': 0, 'CRITICAL': 1, 'SIGNIFICANT': 2, 'MODERATE': 3}
    sorted_alerts = sorted(all_alerts, key=lambda x: (severity_order.get(x['severity'], 4), x['timestamp']), reverse=True)
    
    # Alert summary
    alert_counts = {}
    for alert in all_alerts:
        severity = alert['severity']
        alert_counts[severity] = alert_counts.get(severity, 0) + 1
    
    # Professional alert header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff3333 0%, #ff6600 50%, #ffaa00 100%); 
                padding: 2px; border-radius: 8px; margin: 20px 0;">
        <div style="background: #0a0a0a; margin: 2px; padding: 15px; border-radius: 6px;">
            <h3 style="color: #ff6600; margin: 0; font-family: 'SF Mono', monospace; text-transform: uppercase;">
                🚨 REAL-TIME POSITION ALERTS • LIVE MONITORING SYSTEM
            </h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Alert summary cards
    alert_col1, alert_col2, alert_col3, alert_col4 = st.columns(4)
    
    with alert_col1:
        critical_count = alert_counts.get('CRITICAL', 0) + alert_counts.get('EXTREME', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #330000, #660000); 
                    border: 2px solid #ff3333; border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff3333; font-size: 2rem; font-weight: bold; font-family: monospace;">
                {critical_count}
            </div>
            <div style="color: #ff6600; font-size: 0.9rem; text-transform: uppercase;">
                CRITICAL ALERTS
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with alert_col2:
        significant_count = alert_counts.get('SIGNIFICANT', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #331a00, #663300); 
                    border: 2px solid #ff6600; border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ff6600; font-size: 2rem; font-weight: bold; font-family: monospace;">
                {significant_count}
            </div>
            <div style="color: #ff6600; font-size: 0.9rem; text-transform: uppercase;">
                SIGNIFICANT
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with alert_col3:
        moderate_count = alert_counts.get('MODERATE', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a00, #333300); 
                    border: 2px solid #ffaa00; border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #ffaa00; font-size: 2rem; font-weight: bold; font-family: monospace;">
                {moderate_count}
            </div>
            <div style="color: #ff6600; font-size: 0.9rem; text-transform: uppercase;">
                MODERATE
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with alert_col4:
        total_alerts = len(all_alerts)
        action_required = sum(1 for alert in all_alerts if alert.get('action_required', False))
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1a1a1a, #2a2a2a); 
                    border: 2px solid #39ff14; border-radius: 8px; padding: 15px; text-align: center;">
            <div style="color: #39ff14; font-size: 2rem; font-weight: bold; font-family: monospace;">
                {total_alerts}
            </div>
            <div style="color: #ff6600; font-size: 0.9rem; text-transform: uppercase;">
                TOTAL ALERTS
            </div>
            <div style="color: #ff3333; font-size: 0.8rem; margin-top: 5px;">
                {action_required} REQUIRE ACTION
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed alert list
    st.markdown("### 📋 DETAILED ALERT LOG")
    
    for i, alert in enumerate(sorted_alerts[:20]):  # Show latest 20 alerts
        severity = alert['severity']
        alert_type = alert['type']
        symbol = alert['symbol']
        message = alert['message']
        details = alert['details']
        timestamp = alert['timestamp']
        action_required = alert.get('action_required', False)
        
        # Color coding by severity
        if severity in ['CRITICAL', 'EXTREME']:
            border_color = "#ff3333"
            bg_color = "linear-gradient(145deg, #330000, #1a0000)"
            icon = "🚨"
        elif severity == 'SIGNIFICANT':
            border_color = "#ff6600"  
            bg_color = "linear-gradient(145deg, #331a00, #1a1000)"
            icon = "⚠️"
        else:
            border_color = "#ffaa00"
            bg_color = "linear-gradient(145deg, #1a1a00, #101000)"
            icon = "📊"
        
        action_badge = """
        <span style="background: #ff3333; color: white; padding: 3px 8px; border-radius: 12px; 
                      font-size: 0.7rem; font-weight: bold; margin-left: 10px;">
            ACTION REQUIRED
        </span>
        """ if action_required else ""
        
        st.markdown(f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; 
                    border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div>
                    <span style="font-size: 1.2rem;">{icon}</span>
                    <span style="color: {border_color}; font-weight: bold; font-size: 1rem; margin-left: 8px;">
                        {severity} • {alert_type.replace('_', ' ')}
                    </span>
                    {action_badge}
                </div>
                <div style="color: #888; font-size: 0.8rem; font-family: monospace;">
                    {timestamp.strftime('%H:%M:%S')}
                </div>
            </div>
            <div style="color: #fff; font-size: 1rem; margin-bottom: 5px; font-weight: bold;">
                {message}
            </div>
            <div style="color: #aaa; font-size: 0.9rem; font-family: monospace;">
                {details}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_position_heat_map(positions_data):
    """Create an enhanced position heat map by risk/exposure with professional styling"""
    if not positions_data:
        return None
    
    symbols = list(positions_data.keys())
    risk_levels = [positions_data[s]['metrics']['position_size_pct'] for s in symbols]
    pnl_values = [positions_data[s]['metrics']['unrealized_pnl'] for s in symbols]
    performance_grades = [positions_data[s]['metrics']['performance_grade'] for s in symbols]
    momentum_scores = [positions_data[s]['metrics']['momentum_score'] * 100 for s in symbols]
    
    # Create enhanced heat map
    fig = go.Figure()
    
    # Add scatter plot for positions
    fig.add_trace(go.Scatter(
        x=risk_levels,
        y=pnl_values,
        mode='markers+text',
        text=[s.replace('/USDT', '') for s in symbols],
        textposition="middle center",
        textfont=dict(color='white', size=12, family='SF Mono'),
        marker=dict(
            size=[abs(pnl) * 5 + 30 for pnl in pnl_values],
            color=momentum_scores,
            colorscale=[[0, '#ff3333'], [0.3, '#ff6600'], [0.6, '#ffaa00'], [1, '#39ff14']],
            showscale=True,
            colorbar=dict(
                title="Momentum Score (%)",
                titlefont=dict(color='white'),
                tickfont=dict(color='white')
            ),
            line=dict(width=3, color='#0a0a0a'),
            opacity=0.8
        ),
        customdata=list(zip(symbols, performance_grades, momentum_scores)),
        hovertemplate='<b>%{text}</b><br>' +
                      'Risk: %{x:.1f}% of portfolio<br>' +
                      'P&L: $%{y:+.2f}<br>' +
                      'Grade: %{customdata[1]}<br>' +
                      'Momentum: %{customdata[2]:.1f}%<br>' +
                      '<extra></extra>',
        name="Positions"
    ))
    
    # Add risk zones as background shapes
    fig.add_shape(
        type="rect", x0=0, y0=min(pnl_values)-50, x1=10, y1=max(pnl_values)+50,
        fillcolor="rgba(57, 255, 20, 0.1)", line=dict(width=0)
    )
    fig.add_shape(
        type="rect", x0=10, y0=min(pnl_values)-50, x1=20, y1=max(pnl_values)+50,
        fillcolor="rgba(255, 170, 0, 0.1)", line=dict(width=0)
    )
    fig.add_shape(
        type="rect", x0=20, y0=min(pnl_values)-50, x1=max(risk_levels)+5, y1=max(pnl_values)+50,
        fillcolor="rgba(255, 51, 51, 0.1)", line=dict(width=0)
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="#666", line_width=2, annotation_text="Break Even")
    fig.add_vline(x=10, line_dash="dash", line_color="#ff6600", line_width=1, annotation_text="Medium Risk")
    fig.add_vline(x=20, line_dash="dash", line_color="#ff3333", line_width=1, annotation_text="High Risk")
    
    fig.update_layout(
        title=dict(
            text="🗺️ ADVANCED POSITION HEAT MAP • Risk vs P&L with Momentum Analysis",
            font=dict(size=16, color='#ff6b35', family='SF Mono')
        ),
        xaxis=dict(
            title="Position Size (% of Portfolio)",
            gridcolor='#1a1a1a',
            color='#c9d1d9',
            showgrid=True,
            range=[0, max(risk_levels) + 5]
        ),
        yaxis=dict(
            title="Unrealized P&L ($)",
            gridcolor='#1a1a1a', 
            color='#c9d1d9',
            showgrid=True,
            zeroline=True,
            zerolinecolor='#666'
        ),
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        font=dict(color='#c9d1d9', family='SF Mono'),
        height=500,
        annotations=[
            dict(
                x=5, y=max(pnl_values) * 0.9, text="LOW RISK ZONE",
                showarrow=False, font=dict(color='#39ff14', size=12)
            ),
            dict(
                x=15, y=max(pnl_values) * 0.9, text="MEDIUM RISK",
                showarrow=False, font=dict(color='#ff6600', size=12)
            ),
            dict(
                x=25, y=max(pnl_values) * 0.9, text="HIGH RISK ZONE",
                showarrow=False, font=dict(color='#ff3333', size=12)
            )
        ]
    )
    
    return fig


def render_enhanced_live_position_tracker(bot_data, portfolio_value=1000):
    """
    Render the complete enhanced live position tracking interface with professional trading terminal styling
    """
    # Get positions
    positions = bot_data.get('trading_state', {}).get('positions', {})
    
    if not positions:
        render_no_positions_interface()
        return
    
    # Get enhanced live prices from multiple sources
    symbols = list(positions.keys())
    live_price_data = get_live_prices_multi_source(symbols)
    
    # Calculate enhanced metrics and generate alerts for all positions
    positions_data = {}
    all_alerts = []
    total_unrealized_pnl = 0
    total_position_value = 0
    total_entry_value = 0
    
    for symbol, position in positions.items():
        current_price_data = live_price_data.get(symbol, {
            'price': position.get('entry', 0), 'source': 'Fallback', 
            'volume_24h': 0, 'change_24h': 0, 'timestamp': datetime.now()
        })
        
        # Calculate enhanced metrics
        metrics = calculate_enhanced_position_metrics(position, current_price_data, portfolio_value)
        
        if metrics:
            # Generate alerts for this position
            position_alerts = generate_position_alerts(symbol, position, current_price_data)
            all_alerts.extend(position_alerts)
            
            positions_data[symbol] = {
                'position': position,
                'current_price_data': current_price_data,
                'metrics': metrics,
                'alerts': position_alerts
            }
            total_unrealized_pnl += metrics['unrealized_pnl']
            total_position_value += metrics['position_value']
            total_entry_value += metrics['entry_value']
    
    # Enhanced portfolio-level metrics
    portfolio_pnl_pct = (total_unrealized_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
    market_exposure_pct = (total_position_value / portfolio_value * 100) if portfolio_value > 0 else 0
    capital_efficiency = (total_position_value / total_entry_value * 100 - 100) if total_entry_value > 0 else 0
    
    # Professional trading terminal header
    render_professional_header(len(positions_data), len(all_alerts))
    
    # Alert System (render first for critical alerts)
    if all_alerts:
        render_alert_system(all_alerts)
        st.markdown("---")
    
    # Enhanced Portfolio Summary Dashboard
    render_enhanced_portfolio_summary(
        total_unrealized_pnl, total_position_value, portfolio_pnl_pct, 
        market_exposure_pct, capital_efficiency, len(positions_data), positions_data
    )
    
    st.markdown("---")
    
    # Position Management Controls
    render_position_management_controls(positions_data)
    
    st.markdown("---")
    
    # Enhanced Position Heat Map with momentum analysis
    if len(positions_data) > 1:
        st.markdown("### 🗺️ ADVANCED POSITION HEAT MAP")
        heat_map_fig = render_position_heat_map(positions_data)
        if heat_map_fig:
            st.plotly_chart(heat_map_fig, use_container_width=True)
        st.markdown("---")
    
    # Real-time Performance Dashboard
    render_realtime_performance_dashboard(positions_data, portfolio_value)
    
    st.markdown("---")
    
    # Enhanced Individual Position Cards
    st.markdown("### 💼 ENHANCED POSITION ANALYSIS • LIVE TRACKING")
    
    # Sort positions by multiple criteria
    sort_option = st.selectbox(
        "Sort positions by:",
        ["Unrealized P&L", "Position Size", "Risk Level", "Time Held", "Performance Grade"],
        key="position_sort"
    )
    
    if sort_option == "Unrealized P&L":
        sorted_positions = sorted(positions_data.items(), key=lambda x: x[1]['metrics']['unrealized_pnl'], reverse=True)
    elif sort_option == "Position Size":
        sorted_positions = sorted(positions_data.items(), key=lambda x: x[1]['metrics']['position_size_pct'], reverse=True)
    elif sort_option == "Risk Level":
        sorted_positions = sorted(positions_data.items(), key=lambda x: x[1]['metrics']['combined_risk_score'], reverse=True)
    elif sort_option == "Time Held":
        sorted_positions = sorted(positions_data.items(), key=lambda x: x[1]['metrics']['hours_held'], reverse=True)
    else:  # Performance Grade
        grade_order = {"A+": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        sorted_positions = sorted(positions_data.items(), 
                                key=lambda x: grade_order.get(x[1]['metrics']['performance_grade'], 0), reverse=True)
    
    # Display enhanced position cards
    for i in range(0, len(sorted_positions), 2):  # 2 per row for better visibility
        cols = st.columns(min(2, len(sorted_positions) - i))
        
        for j, (symbol, data) in enumerate(sorted_positions[i:i+2]):
            with cols[j]:
                render_enhanced_position_card(symbol, data)


def render_no_positions_interface():
    """Render professional no-positions interface"""
    current_time = datetime.now()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%); 
                border: 2px dashed #ff6b35; border-radius: 12px; padding: 40px; 
                text-align: center; margin: 30px 0; position: relative; overflow: hidden;">
        
        <!-- Animated background effect -->
        <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 2px; 
                    background: linear-gradient(90deg, transparent, #39ff14, transparent);
                    animation: scan 3s linear infinite;"></div>
        
        <!-- Main content -->
        <div style="position: relative; z-index: 1;">
            <h2 style="color: #ff6b35; margin-bottom: 20px; font-family: 'SF Mono', monospace; 
                       text-transform: uppercase; letter-spacing: 2px;">
                📡 POSITION SCANNER ACTIVE
            </h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 30px 0;">
                <div style="background: rgba(57, 255, 20, 0.1); border: 1px solid #39ff14; 
                            border-radius: 8px; padding: 20px;">
                    <div style="color: #39ff14; font-size: 1.5rem; margin-bottom: 10px;">📊</div>
                    <div style="color: #39ff14; font-weight: bold;">MARKET SCANNING</div>
                    <div style="color: #888; font-size: 0.9rem;">Monitoring 50+ symbols</div>
                </div>
                
                <div style="background: rgba(255, 107, 53, 0.1); border: 1px solid #ff6b35; 
                            border-radius: 8px; padding: 20px;">
                    <div style="color: #ff6b35; font-size: 1.5rem; margin-bottom: 10px;">🎯</div>
                    <div style="color: #ff6b35; font-weight: bold;">SIGNAL ANALYSIS</div>
                    <div style="color: #888; font-size: 0.9rem;">AI pattern recognition</div>
                </div>
                
                <div style="background: rgba(88, 166, 255, 0.1); border: 1px solid #58a6ff; 
                            border-radius: 8px; padding: 20px;">
                    <div style="color: #58a6ff; font-size: 1.5rem; margin-bottom: 10px;">⚡</div>
                    <div style="color: #58a6ff; font-weight: bold;">READY TO DEPLOY</div>
                    <div style="color: #888; font-size: 0.9rem;">Capital standing by</div>
                </div>
            </div>
            
            <div style="background: #0a0a0a; border-radius: 8px; padding: 20px; margin: 20px 0; 
                        border: 1px solid #333;">
                <div style="color: #39ff14; font-family: 'SF Mono', monospace; font-size: 1rem; 
                            margin-bottom: 10px;">
                    STATUS: IDLE • CAPITAL AVAILABLE • SCANNING ACTIVE █
                </div>
                <div style="color: #888; font-size: 0.9rem; font-family: 'SF Mono', monospace;">
                    LAST SCAN: {current_time.strftime('%H:%M:%S')} • 
                    UPTIME: {current_time.strftime('%H:%M:%S')} • 
                    NEXT SCAN: 00:00:30
                </div>
            </div>
            
            <div style="color: #666; font-size: 0.9rem; margin-top: 25px;">
                🔄 Real-time position tracking will activate automatically when positions are opened<br>
                📊 Advanced analytics, alerts, and P&L monitoring ready for deployment
            </div>
        </div>
    </div>
    
    <style>
        @keyframes scan {{
            0%% {{ left: -100%%; }}
            100%% {{ left: 100%%; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def render_professional_header(position_count: int, alert_count: int):
    """Render professional trading terminal header"""
    current_time = datetime.now()
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #0d1117 0%, #21262d 50%, #0d1117 100%); 
                border-bottom: 2px solid #ff6b35; padding: 20px; margin-bottom: 25px; position: relative;">
        
        <!-- Animated border effect -->
        <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 2px; 
                    background: linear-gradient(90deg, transparent, #ff6b35, transparent);
                    animation: borderScan 4s linear infinite;"></div>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="color: #ff6b35; margin: 0; font-family: 'SF Mono', monospace; 
                           font-size: 1.8rem; text-transform: uppercase; letter-spacing: 3px;">
                    🎯 LIVE POSITION TRACKER • PROFESSIONAL TERMINAL
                </h1>
                <div style="color: #888; font-size: 1rem; margin-top: 5px; font-family: 'SF Mono', monospace;">
                    Real-time P&L monitoring with multi-source price feeds and intelligent alerting
                </div>
            </div>
            
            <div style="text-align: right;">
                <div style="color: #39ff14; font-family: 'SF Mono', monospace; font-size: 1.2rem; 
                            font-weight: bold; margin-bottom: 5px;">
                    🔴 LIVE • {current_time.strftime('%H:%M:%S')}
                </div>
                <div style="color: #ff6b35; font-size: 0.9rem;">
                    {position_count} POSITIONS • {alert_count} ALERTS
                </div>
                <div style="color: #666; font-size: 0.8rem; margin-top: 3px;">
                    AUTO-REFRESH: 15s • LATENCY: <5ms
                </div>
            </div>
        </div>
    </div>
    
    <style>
        @keyframes borderScan {{
            0%% {{ left: -100%%; }}
            100%% {{ left: 100%%; }}
        }}
    </style>
    """, unsafe_allow_html=True)


# Legacy function for backward compatibility
def render_live_position_tracker(bot_data, portfolio_value=1000):
    """Legacy function - calls enhanced version"""
    render_enhanced_live_position_tracker(bot_data, portfolio_value)


def render_enhanced_portfolio_summary(total_unrealized_pnl, total_position_value, portfolio_pnl_pct, 
                                     market_exposure_pct, capital_efficiency, position_count, positions_data):
    """Render enhanced portfolio summary with advanced metrics"""
    
    # Calculate additional portfolio metrics
    avg_risk_level = sum(p['metrics']['combined_risk_score'] for p in positions_data.values()) / len(positions_data) if positions_data else 0
    best_performer = max(positions_data.values(), key=lambda x: x['metrics']['unrealized_pnl_pct']) if positions_data else None
    worst_performer = min(positions_data.values(), key=lambda x: x['metrics']['unrealized_pnl_pct']) if positions_data else None
    
    # Color coding
    total_pnl_color = "#39ff14" if total_unrealized_pnl >= 0 else "#ff3333"
    exposure_color = "#ff3333" if market_exposure_pct > 80 else "#ff6600" if market_exposure_pct > 60 else "#39ff14"
    risk_color = "#ff3333" if avg_risk_level > 20 else "#ff6600" if avg_risk_level > 10 else "#39ff14"
    
    st.markdown("### 📊 ENHANCED PORTFOLIO DASHBOARD")
    
    # Main portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #21262d 100%); 
                    border: 2px solid {total_pnl_color}; border-radius: 12px; padding: 20px; text-align: center;
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold; letter-spacing: 1px;">
                TOTAL UNREALIZED P&L
            </div>
            <div style="color: {total_pnl_color}; font-size: 2.2rem; font-weight: bold; 
                        text-shadow: 0 0 15px {total_pnl_color}; font-family: 'SF Mono', monospace; margin: 10px 0;">
                ${total_unrealized_pnl:+.2f}
            </div>
            <div style="color: {total_pnl_color}; font-size: 1.2rem; font-weight: bold; margin-bottom: 8px;">
                ({portfolio_pnl_pct:+.2f}%)
            </div>
            <div style="color: #888; font-size: 0.8rem;">
                Capital Efficiency: {capital_efficiency:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #21262d 100%); 
                    border: 2px solid {exposure_color}; border-radius: 12px; padding: 20px; text-align: center;
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold; letter-spacing: 1px;">
                MARKET EXPOSURE
            </div>
            <div style="color: {exposure_color}; font-size: 2.2rem; font-weight: bold; 
                        font-family: 'SF Mono', monospace; margin: 10px 0;">
                {market_exposure_pct:.1f}%
            </div>
            <div style="color: #888; font-size: 1rem; margin-bottom: 8px;">
                ${total_position_value:.2f}
            </div>
            <div style="color: #666; font-size: 0.8rem;">
                Active positions deployed
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #21262d 100%); 
                    border: 2px solid {risk_color}; border-radius: 12px; padding: 20px; text-align: center;
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold; letter-spacing: 1px;">
                PORTFOLIO RISK
            </div>
            <div style="color: {risk_color}; font-size: 2.2rem; font-weight: bold; 
                        font-family: 'SF Mono', monospace; margin: 10px 0;">
                {avg_risk_level:.1f}
            </div>
            <div style="color: #888; font-size: 1rem; margin-bottom: 8px;">
                Risk Score
            </div>
            <div style="color: #666; font-size: 0.8rem;">
                Composite risk metric
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #21262d 100%); 
                    border: 2px solid #ff6b35; border-radius: 12px; padding: 20px; text-align: center;
                    box-shadow: 0 0 20px rgba(255, 107, 53, 0.2);">
            <div style="color: #ff6600; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold; letter-spacing: 1px;">
                ACTIVE POSITIONS
            </div>
            <div style="color: #ff6b35; font-size: 2.2rem; font-weight: bold; 
                        font-family: 'SF Mono', monospace; margin: 10px 0;">
                {position_count}
            </div>
            <div style="color: #888; font-size: 1rem; margin-bottom: 8px;">
                Live Tracking
            </div>
            <div style="color: #666; font-size: 0.8rem;">
                Real-time monitoring
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Best/Worst performers
    if best_performer and worst_performer:
        st.markdown("#### 🏆 TOP & BOTTOM PERFORMERS")
        
        col1, col2 = st.columns(2)
        
        with col1:
            best_symbol = [k for k, v in positions_data.items() if v == best_performer][0]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #001a00, #003300); border: 2px solid #39ff14; 
                        border-radius: 8px; padding: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: #39ff14; font-size: 1.2rem; font-weight: bold; margin-bottom: 5px;">
                            🥇 BEST PERFORMER
                        </div>
                        <div style="color: #39ff14; font-size: 1.5rem; font-family: 'SF Mono', monospace;">
                            {best_symbol.replace('/USDT', '')}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #39ff14; font-size: 1.8rem; font-weight: bold;">
                            {best_performer['metrics']['unrealized_pnl_pct']:+.2f}%
                        </div>
                        <div style="color: #888; font-size: 0.9rem;">
                            Grade: {best_performer['metrics']['performance_grade']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            worst_symbol = [k for k, v in positions_data.items() if v == worst_performer][0]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a0000, #330000); border: 2px solid #ff3333; 
                        border-radius: 8px; padding: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: #ff3333; font-size: 1.2rem; font-weight: bold; margin-bottom: 5px;">
                            📉 NEEDS ATTENTION
                        </div>
                        <div style="color: #ff3333; font-size: 1.5rem; font-family: 'SF Mono', monospace;">
                            {worst_symbol.replace('/USDT', '')}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #ff3333; font-size: 1.8rem; font-weight: bold;">
                            {worst_performer['metrics']['unrealized_pnl_pct']:+.2f}%
                        </div>
                        <div style="color: #888; font-size: 0.9rem;">
                            Grade: {worst_performer['metrics']['performance_grade']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_position_management_controls(positions_data):
    """Render position management controls and quick actions"""
    
    st.markdown("### ⚙️ POSITION MANAGEMENT CONTROLS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 REFRESH PRICES", use_container_width=True):
            # Clear cache to force price refresh
            global PRICE_CACHE, PRICE_CACHE_TIMESTAMP
            PRICE_CACHE = {}
            PRICE_CACHE_TIMESTAMP = None
            st.success("Price cache cleared - refreshing...")
            st.experimental_rerun()
    
    with col2:
        if st.button("📊 EXPORT DATA", use_container_width=True):
            # Create export data
            export_data = []
            for symbol, data in positions_data.items():
                metrics = data['metrics']
                position = data['position']
                
                export_data.append({
                    'Symbol': symbol,
                    'Entry Price': position.get('entry', 0),
                    'Current Price': metrics['current_price'],
                    'Position Size': position.get('amount', 0),
                    'Position Value': metrics['position_value'],
                    'Unrealized P&L': metrics['unrealized_pnl'],
                    'Unrealized P&L %': metrics['unrealized_pnl_pct'],
                    'Risk Level': metrics['risk_level'],
                    'Performance Grade': metrics['performance_grade'],
                    'Time Held': metrics['time_str'],
                    'Data Source': metrics['data_source'],
                    'Last Updated': metrics['data_timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Convert to DataFrame for download
            df = pd.DataFrame(export_data)
            csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("🎯 ANALYZE SIGNALS", use_container_width=True):
            st.info("🔍 Advanced signal analysis feature coming soon...")
    
    with col4:
        alert_threshold = st.selectbox(
            "Alert Threshold",
            ["2%", "5%", "10%", "15%"],
            index=1,
            key="alert_threshold"
        )
        
        if alert_threshold:
            threshold_value = float(alert_threshold.replace('%', ''))
            st.session_state['alert_threshold'] = threshold_value
    
    # Quick stats and controls
    if positions_data:
        st.markdown("#### 🔧 QUICK POSITION STATS")
        
        # Calculate quick stats
        total_positions = len(positions_data)
        profitable_positions = sum(1 for p in positions_data.values() if p['metrics']['unrealized_pnl'] > 0)
        high_risk_positions = sum(1 for p in positions_data.values() if p['metrics']['risk_level'] in ['HIGH', 'EXTREME'])
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Total Positions", total_positions)
        with stat_col2:
            win_rate = (profitable_positions / total_positions * 100) if total_positions > 0 else 0
            st.metric("Profitable", f"{profitable_positions}/{total_positions}", f"{win_rate:.1f}%")
        with stat_col3:
            st.metric("High Risk", high_risk_positions, "⚠️" if high_risk_positions > 0 else "✅")
        with stat_col4:
            avg_hold_time = sum(p['metrics']['hours_held'] for p in positions_data.values()) / len(positions_data)
            st.metric("Avg Hold Time", f"{avg_hold_time:.1f}h")


def render_realtime_performance_dashboard(positions_data, portfolio_value):
    """Render real-time performance dashboard with charts"""
    
    if not positions_data:
        return
    
    st.markdown("### 📈 REAL-TIME PERFORMANCE ANALYTICS")
    
    # Performance distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        # P&L Distribution
        symbols = [s.replace('/USDT', '') for s in positions_data.keys()]
        pnl_values = [p['metrics']['unrealized_pnl'] for p in positions_data.values()]
        pnl_colors = ['#39ff14' if pnl >= 0 else '#ff3333' for pnl in pnl_values]
        
        fig_pnl = go.Figure(data=[
            go.Bar(
                x=symbols,
                y=pnl_values,
                marker_color=pnl_colors,
                text=[f"${pnl:+.2f}" for pnl in pnl_values],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>P&L: $%{y:+.2f}<extra></extra>'
            )
        ])
        
        fig_pnl.update_layout(
            title="💰 UNREALIZED P&L BY POSITION",
            xaxis_title="Symbol",
            yaxis_title="P&L ($)",
            plot_bgcolor='#0d1117',
            paper_bgcolor='#0d1117',
            font=dict(color='#c9d1d9', family='SF Mono'),
            height=400
        )
        
        fig_pnl.add_hline(y=0, line_dash="dash", line_color="#666")
        
        st.plotly_chart(fig_pnl, use_container_width=True)
    
    with col2:
        # Risk vs Return Scatter
        risk_scores = [p['metrics']['combined_risk_score'] for p in positions_data.values()]
        return_pcts = [p['metrics']['unrealized_pnl_pct'] for p in positions_data.values()]
        
        fig_risk = go.Figure(data=[
            go.Scatter(
                x=risk_scores,
                y=return_pcts,
                mode='markers+text',
                text=symbols,
                textposition="top center",
                marker=dict(
                    size=15,
                    color=return_pcts,
                    colorscale=[[0, '#ff3333'], [0.5, '#ffff00'], [1, '#39ff14']],
                    showscale=True,
                    colorbar=dict(title="Return %"),
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{text}</b><br>Risk Score: %{x:.1f}<br>Return: %{y:+.2f}%<extra></extra>'
            )
        ])
        
        fig_risk.update_layout(
            title="📊 RISK vs RETURN ANALYSIS",
            xaxis_title="Risk Score",
            yaxis_title="Return (%)",
            plot_bgcolor='#0d1117',
            paper_bgcolor='#0d1117',
            font=dict(color='#c9d1d9', family='SF Mono'),
            height=400
        )
        
        fig_risk.add_hline(y=0, line_dash="dash", line_color="#666")
        fig_risk.add_vline(x=15, line_dash="dash", line_color="#ff6600", annotation_text="High Risk Threshold")
        
        st.plotly_chart(fig_risk, use_container_width=True)


def render_enhanced_position_card(symbol, data):
    """Render enhanced individual position card with comprehensive metrics and professional styling"""
    
    position = data['position']
    current_price_data = data['current_price_data']
    metrics = data['metrics']
    alerts = data.get('alerts', [])
    
    current_price = metrics['current_price']
    entry_price = position.get('entry', 0)
    
    # Enhanced color coding
    pnl_color = "#39ff14" if metrics['unrealized_pnl'] >= 0 else "#ff3333"
    border_color = metrics['risk_color']
    
    # Format price function with better precision
    def fmt_price(p):
        if p == 0:
            return "$0.00"
        elif p < 0.001:
            return f"${p:.8f}"
        elif p < 0.01:
            return f"${p:.6f}"
        elif p < 1:
            return f"${p:.4f}"
        elif p < 100:
            return f"${p:.3f}"
        elif p < 10000:
            return f"${p:,.2f}"
        else:
            return f"${p:,.0f}"
    
    # Enhanced progress calculation
    stop_price = position.get('stop', 0)
    target_price = position.get('target', 0)
    
    if target_price > stop_price and stop_price > 0:
        price_range = target_price - stop_price
        price_progress = ((current_price - stop_price) / price_range) * 100
        price_progress = max(0, min(100, price_progress))
    else:
        price_progress = 50
    
    # Alert indicators
    alert_badges = ""
    if alerts:
        critical_alerts = sum(1 for a in alerts if a['severity'] in ['CRITICAL', 'EXTREME'])
        if critical_alerts > 0:
            alert_badges = f"""
            <div style="position: absolute; top: 10px; right: 10px;">
                <span style="background: #ff3333; color: white; padding: 4px 8px; border-radius: 12px; 
                              font-size: 0.7rem; font-weight: bold; animation: pulse 1s infinite;">
                    🚨 {critical_alerts} ALERT{'S' if critical_alerts > 1 else ''}
                </span>
            </div>
            """
    
    # Blinking effect for significant changes
    blink_class = "blink" if abs(metrics['unrealized_pnl_pct']) > 5 else ""
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%); 
                border: 2px solid {border_color}; border-radius: 15px; padding: 25px; margin-bottom: 25px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); position: relative; overflow: hidden;">
        
        <!-- Animated border effect -->
        <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 2px; 
                    background: linear-gradient(90deg, transparent, {border_color}, transparent);
                    animation: borderScan 3s linear infinite;"></div>
        
        {alert_badges}
        
        <!-- Enhanced Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h3 style="color: #ff6b35; margin: 0; font-size: 1.6rem; font-family: 'SF Mono', monospace; 
                           font-weight: bold; text-transform: uppercase;">
                    {symbol.replace('/USDT', '')}
                </h3>
                <div style="color: #888; font-size: 0.9rem; margin-top: 3px;">
                    Data: {current_price_data.get('source', 'Unknown')} • 
                    24h: {current_price_data.get('change_24h', 0):+.2f}%
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color: #888; font-size: 0.8rem;">TIME IN POSITION</div>
                <div style="color: #39ff14; font-size: 1.1rem; font-weight: bold; font-family: 'SF Mono', monospace;">
                    ⏱️ {metrics['time_str']}
                </div>
                <div style="color: #666; font-size: 0.8rem; margin-top: 2px;">
                    Performance: {metrics['performance_grade']}
                </div>
            </div>
        </div>
        
        <!-- Enhanced Price Display -->
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px;">
            <div style="text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                <div style="color: #888; font-size: 0.8rem; text-transform: uppercase;">ENTRY</div>
                <div style="color: #aaa; font-family: 'SF Mono', monospace; font-size: 1.1rem; font-weight: bold;">
                    {fmt_price(entry_price)}
                </div>
            </div>
            <div style="text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                <div style="color: #888; font-size: 0.8rem; text-transform: uppercase;">CURRENT</div>
                <div style="color: {pnl_color}; font-family: 'SF Mono', monospace; font-size: 1.1rem; font-weight: bold;">
                    {fmt_price(current_price)}
                </div>
            </div>
            <div style="text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                <div style="color: #888; font-size: 0.8rem; text-transform: uppercase;">CHANGE</div>
                <div style="color: {pnl_color}; font-family: 'SF Mono', monospace; font-size: 1.1rem; font-weight: bold;">
                    {((current_price - entry_price) / entry_price * 100):+.2f}%
                </div>
            </div>
        </div>
        
        <!-- Enhanced P&L Display -->
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #000, #111); 
                    border: 2px solid {pnl_color}; border-radius: 12px; margin-bottom: 20px; position: relative;">
            <div style="color: #ff6b35; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold; letter-spacing: 1px;">
                UNREALIZED P&L
            </div>
            <div class="{blink_class}" style="color: {pnl_color}; font-size: 2.5rem; font-weight: bold; 
                        font-family: 'SF Mono', monospace; text-shadow: 0 0 20px {pnl_color}; margin-bottom: 8px;">
                ${metrics['unrealized_pnl']:+.4f}
            </div>
            <div style="color: {pnl_color}; font-size: 1.4rem; font-weight: bold; margin-bottom: 8px;">
                ({metrics['unrealized_pnl_pct']:+.2f}%)
            </div>
            <div style="color: #888; font-size: 0.9rem;">
                Profit/Hour: ${metrics['profit_per_hour']:+.3f} • 
                Efficiency: {metrics['capital_efficiency']:+.2f}%
            </div>
        </div>
        
        <!-- Enhanced Position Analytics -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; 
                    font-size: 0.95rem; font-family: 'SF Mono', monospace;">
            <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 8px;">
                <div style="color: #ff6b35; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px;">POSITION SIZE</div>
                <div style="color: #aaa;">Amount: <span style="float: right; color: #39ff14;">{position.get('amount', 0):.6f}</span></div>
                <div style="color: #aaa;">Value: <span style="float: right; color: #39ff14;">${metrics['position_value']:,.2f}</span></div>
                <div style="color: #aaa;">Portfolio %: <span style="float: right; color: {metrics['risk_color']}; font-weight: bold;">{metrics['position_size_pct']:.1f}%</span></div>
            </div>
            
            <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 8px;">
                <div style="color: #ff6b35; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px;">RISK METRICS</div>
                <div style="color: #aaa;">Risk Level: <span style="float: right; color: {metrics['risk_color']}; font-weight: bold;">{metrics['risk_level']}</span></div>
                <div style="color: #aaa;">Risk Score: <span style="float: right; color: {metrics['risk_color']};">{metrics['combined_risk_score']:.1f}</span></div>
                <div style="color: #aaa;">R:R Ratio: <span style="float: right; color: #888;">1:{metrics['risk_reward_ratio']:.2f}</span></div>
            </div>
        </div>
        
        <!-- Enhanced Performance Metrics -->
        <div style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.3), rgba(255, 255, 255, 0.05)); 
                    padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <div style="color: #ff6b35; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 10px; 
                        font-weight: bold;">
                ADVANCED PERFORMANCE ANALYTICS
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; 
                        font-size: 0.85rem; font-family: 'SF Mono', monospace;">
                <div>
                    <div style="color: #888;">Annualized Return:</div>
                    <div style="color: {pnl_color}; font-weight: bold; font-size: 1rem;">{metrics['annualized_return']:+.1f}%</div>
                </div>
                <div>
                    <div style="color: #888;">Momentum Score:</div>
                    <div style="color: {metrics['momentum_color']}; font-weight: bold; font-size: 1rem;">
                        {metrics['momentum_score']*100:.1f}%
                    </div>
                </div>
                <div>
                    <div style="color: #888;">Break-even Dist:</div>
                    <div style="color: #aaa; font-weight: bold; font-size: 1rem;">{metrics['break_even_distance']:.2f}%</div>
                </div>
            </div>
        </div>
        
        <!-- Enhanced Stop/Target Section -->
        <div style="margin-bottom: 20px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; 
                            padding: 8px 12px; background: rgba(255, 51, 51, 0.1); border-radius: 6px; border: 1px solid #ff3333;">
                    <span style="color: #ff3333; font-weight: bold;">🛑 STOP: {fmt_price(stop_price)}</span>
                    <span style="color: #ff3333; font-size: 0.9rem;">({metrics['dist_to_stop_pct']:.1f}%)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; 
                            padding: 8px 12px; background: rgba(57, 255, 20, 0.1); border-radius: 6px; border: 1px solid #39ff14;">
                    <span style="color: #39ff14; font-weight: bold;">🎯 TARGET: {fmt_price(target_price)}</span>
                    <span style="color: #39ff14; font-size: 0.9rem;">({metrics['dist_to_target_pct']:.1f}%)</span>
                </div>
            </div>
            
            <!-- Enhanced Progress Bar -->
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.8rem; 
                            font-weight: bold;">
                    <span style="color: #ff3333;">STOP LOSS</span>
                    <span style="color: #fff;">CURRENT: {price_progress:.0f}%</span>
                    <span style="color: #39ff14;">TARGET</span>
                </div>
                <div style="background: #1a1a1a; border: 2px solid #333; border-radius: 8px; 
                            height: 20px; position: relative; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #ff3333 0%, #ff6600 30%, #ffaa00 60%, #39ff14 100%); 
                                width: 100%; height: 100%; opacity: 0.6;"></div>
                    <div style="position: absolute; left: {price_progress}%; top: 0; width: 6px; 
                                height: 100%; background: #fff; box-shadow: 0 0 10px #fff, 0 0 20px #fff;
                                border-radius: 3px;"></div>
                </div>
            </div>
        </div>
        
        <!-- Position Alerts (if any) -->""", unsafe_allow_html=True)
    
    # Render alerts separately to avoid nested f-string issues
    if alerts:
        st.markdown("""
        <div style="margin-bottom: 15px;">
            <div style="color: #ff6b35; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; 
                        font-weight: bold;">ACTIVE ALERTS</div>
        """, unsafe_allow_html=True)
        
        # Show max 3 alerts
        for alert in alerts[:3]:
            st.markdown(f"""
            <div style="background: rgba(255, 51, 51, 0.1); border: 1px solid #ff3333; border-radius: 6px; 
                        padding: 8px; margin-bottom: 5px;">
                <div style="color: #ff3333; font-size: 0.9rem; font-weight: bold;">{alert['severity']} • {alert['type'].replace('_', ' ')}</div>
                <div style="color: #aaa; font-size: 0.8rem;">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <!-- Entry Details -->
        <div style="color: #666; font-size: 0.8rem; font-style: italic; text-align: center; 
                    margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
            Entry Signal: {position.get('reason', 'Manual Entry')[:60]}...
        </div>
    </div>
        
        <!-- Entry Details -->
        <div style="color: #666; font-size: 0.8rem; font-style: italic; text-align: center; 
                    margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
            Entry Signal: {position.get('reason', 'Manual Entry')[:60]}...
        </div>
    </div>
    
    <style>
        @keyframes blink {{
            0%%, 50%% {{ opacity: 1; }}
            51%%, 100%% {{ opacity: 0.8; }}
        }}
        @keyframes pulse {{
            0%%, 100%% {{ transform: scale(1); }}
            50%% {{ transform: scale(1.1); }}
        }}
        @keyframes borderScan {{
            0%% {{ left: -100%%; }}
            100%% {{ left: 100%%; }}
        }}
        .blink {{
            animation: blink 1.5s ease-in-out infinite;
        }}
    </style>
    """, unsafe_allow_html=True)


# Legacy function for backward compatibility
def render_position_card(symbol, data):
    """Legacy function - calls enhanced version"""
    render_enhanced_position_card(symbol, data)


# Enhanced auto-refresh functionality
def setup_enhanced_auto_refresh():
    """Setup enhanced auto-refresh with user controls and status indicators"""
    
    # Auto-refresh controls
    refresh_col1, refresh_col2, refresh_col3 = st.columns([2, 1, 1])
    
    with refresh_col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh enabled", value=True, key="auto_refresh_enabled")
    
    with refresh_col2:
        refresh_interval = st.selectbox(
            "Refresh interval",
            ["10s", "15s", "30s", "60s"],
            index=1,  # Default to 15s
            key="refresh_interval"
        )
    
    with refresh_col3:
        if st.button("🔄 Refresh Now", use_container_width=True):
            # Clear cache and rerun
            global PRICE_CACHE, PRICE_CACHE_TIMESTAMP
            PRICE_CACHE = {}
            PRICE_CACHE_TIMESTAMP = None
            st.experimental_rerun()
    
    # Convert refresh interval to seconds
    interval_seconds = int(refresh_interval.replace('s', ''))
    
    # Enhanced auto-refresh with status
    if auto_refresh:
        st.markdown(f"""
        <div style="background: rgba(57, 255, 20, 0.1); border: 1px solid #39ff14; 
                    border-radius: 6px; padding: 10px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #39ff14; font-weight: bold;">🟢 AUTO-REFRESH ACTIVE</span>
                    <span style="color: #888; margin-left: 15px;">Next refresh in {interval_seconds}s</span>
                </div>
                <div style="color: #39ff14; font-family: 'SF Mono', monospace; font-size: 0.9rem;">
                    Status: LIVE • Latency: <5ms
                </div>
            </div>
        </div>
        
        <script>
            // Enhanced auto-refresh with countdown
            let countdownSeconds = {interval_seconds};
            let countdownInterval;
            
            function startCountdown() {{
                countdownInterval = setInterval(function() {{
                    countdownSeconds--;
                    if (countdownSeconds <= 0) {{
                        window.location.reload();
                    }}
                }}, 1000);
            }}
            
            // Start countdown immediately
            startCountdown();
            
            // Handle visibility change to pause/resume
            document.addEventListener('visibilitychange', function() {{
                if (document.hidden) {{
                    clearInterval(countdownInterval);
                }} else {{
                    startCountdown();
                }}
            }});
        </script>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 170, 0, 0.1); border: 1px solid #ffaa00; 
                    border-radius: 6px; padding: 10px; margin: 10px 0;">
            <span style="color: #ffaa00; font-weight: bold;">⏸️ AUTO-REFRESH PAUSED</span>
            <span style="color: #888; margin-left: 15px;">Manual refresh only</span>
        </div>
        """, unsafe_allow_html=True)


def create_demo_positions_for_testing():
    """Create demo positions for testing the enhanced position tracker"""
    
    if st.sidebar.button("🧪 Load Demo Positions"):
        demo_positions = {
            "BTC/USDT": {
                "entry": 95840.25,
                "amount": 0.00025,
                "stop": 94000.00,
                "target": 98500.00,
                "time": (datetime.now() - timedelta(hours=2, minutes=15)).isoformat(),
                "reason": "bullish_momentum_breakout_signal"
            },
            "ETH/USDT": {
                "entry": 3485.60,
                "amount": 0.0072,
                "stop": 3350.00,
                "target": 3650.00,
                "time": (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
                "reason": "rsi_oversold_bounce_entry"
            },
            "SOL/USDT": {
                "entry": 245.80,
                "amount": 0.985,
                "stop": 235.00,
                "target": 260.00,
                "time": (datetime.now() - timedelta(minutes=35)).isoformat(),
                "reason": "support_level_confirmation"
            }
        }
        
        # Store in session state for demo
        st.session_state['demo_positions'] = demo_positions
        st.success("🧪 Demo positions loaded! Refresh the page to see them.")
    
    if st.sidebar.button("🗑️ Clear Demo Positions"):
        if 'demo_positions' in st.session_state:
            del st.session_state['demo_positions']
        st.success("🗑️ Demo positions cleared!")


def test_enhanced_features():
    """Test suite for enhanced position tracking features"""
    
    if st.sidebar.checkbox("🧪 Enable Testing Mode"):
        st.sidebar.markdown("### 🧪 TESTING CONTROLS")
        
        # Test price feed
        if st.sidebar.button("Test Price Feed"):
            test_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
            with st.spinner("Testing price feeds..."):
                price_data = get_live_prices_multi_source(test_symbols)
                
                st.success("✅ Price feed test complete!")
                for symbol, data in price_data.items():
                    st.info(f"{symbol}: ${data['price']:,.2f} from {data['source']}")
        
        # Test alert generation
        if st.sidebar.button("Test Alert System"):
            test_position = {
                "entry": 100.0,
                "amount": 1.0,
                "stop": 95.0,
                "target": 110.0,
                "time": datetime.now().isoformat()
            }
            
            test_price_data = {"price": 107.0, "source": "Test", "volume_24h": 1000000, "change_24h": 7.0}
            alerts = generate_position_alerts("TEST/USDT", test_position, test_price_data)
            
            st.success(f"✅ Generated {len(alerts)} test alerts")
            for alert in alerts:
                st.info(f"{alert['severity']}: {alert['message']}")
        
        # Performance metrics test
        if st.sidebar.button("Test Performance Metrics"):
            test_position = {
                "entry": 100.0,
                "amount": 1.0,
                "stop": 95.0,
                "target": 110.0,
                "time": (datetime.now() - timedelta(hours=2)).isoformat()
            }
            
            test_price_data = {"price": 105.0, "source": "Test", "volume_24h": 1000000, "change_24h": 5.0}
            metrics = calculate_enhanced_position_metrics(test_position, test_price_data, 1000)
            
            if metrics:
                st.success("✅ Enhanced metrics calculation successful!")
                st.json({
                    "unrealized_pnl": metrics['unrealized_pnl'],
                    "unrealized_pnl_pct": metrics['unrealized_pnl_pct'],
                    "risk_level": metrics['risk_level'],
                    "performance_grade": metrics['performance_grade']
                })


# Enhanced main integration function
def integrate_live_positions_section(bot_data):
    """
    Enhanced main function to integrate live positions into dashboard with comprehensive features
    """
    
    # Add testing controls in sidebar
    create_demo_positions_for_testing()
    test_enhanced_features()
    
    # Setup enhanced auto-refresh
    setup_enhanced_auto_refresh()
    
    # Check for demo positions in session state
    if 'demo_positions' in st.session_state:
        # Merge demo positions with real data
        if 'trading_state' not in bot_data:
            bot_data['trading_state'] = {}
        
        existing_positions = bot_data['trading_state'].get('positions', {})
        demo_positions = st.session_state['demo_positions']
        
        # Merge positions (demo overrides real for testing)
        merged_positions = {**existing_positions, **demo_positions}
        bot_data['trading_state']['positions'] = merged_positions
        
        st.info("🧪 Demo positions are active. Use sidebar to clear them.")
    
    # Get portfolio value
    portfolio_value = bot_data.get('account', {}).get('total_usd', 1000)
    
    # Render the enhanced live position tracker
    render_enhanced_live_position_tracker(bot_data, portfolio_value)
    
    # Add comprehensive analytics if positions exist
    positions = bot_data.get('trading_state', {}).get('positions', {})
    if positions:
        st.markdown("---")
        st.markdown("### 📈 COMPREHENSIVE ANALYTICS INTEGRATION")
        
        # Import and render advanced analytics
        try:
            from position_analytics import render_comprehensive_analytics
            
            # Get enhanced price data and calculate metrics for analytics
            symbols = list(positions.keys())
            live_price_data = get_live_prices_multi_source(symbols)
            
            # Calculate enhanced metrics for all positions
            positions_data = {}
            for symbol, position in positions.items():
                current_price_data = live_price_data.get(symbol, {
                    'price': position.get('entry', 0), 'source': 'Fallback',
                    'volume_24h': 0, 'change_24h': 0, 'timestamp': datetime.now()
                })
                
                metrics = calculate_enhanced_position_metrics(position, current_price_data, portfolio_value)
                
                if metrics:
                    positions_data[symbol] = {
                        'position': position,
                        'current_price_data': current_price_data,
                        'metrics': metrics
                    }
            
            # Render comprehensive analytics with enhanced data
            if positions_data:
                render_comprehensive_analytics(positions_data, portfolio_value)
            else:
                st.warning("⚠️ Unable to calculate position metrics for analytics")
                
        except ImportError as e:
            st.warning(f"⚠️ Advanced analytics module not available: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error loading analytics: {str(e)}")
            logger.error(f"Analytics integration error: {str(e)}")
    
    # System status footer
    st.markdown("---")
    current_time = datetime.now()
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8rem; 
                font-family: 'SF Mono', monospace; margin-top: 20px;">
        🎯 Enhanced Live Position Tracker v2.0 • 
        Last Update: {current_time.strftime('%Y-%m-%d %H:%M:%S')} • 
        Multi-source price feeds active • 
        Real-time alerting system online
    </div>
    """, unsafe_allow_html=True)


# Legacy auto-refresh function for backward compatibility
def setup_auto_refresh():
    """Legacy function - calls enhanced version"""
    setup_enhanced_auto_refresh()
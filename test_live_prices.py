#!/usr/bin/env python3
"""
Test script for live price feeds
"""

import requests
import json

def test_binance_api():
    """Test Binance API connectivity and price fetching"""
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT']
    
    print("🔍 Testing Binance API connectivity...")
    
    for symbol in test_symbols:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                formatted_symbol = symbol.replace('USDT', '/USDT')
                print(f"✅ {formatted_symbol}: ${price:,.4f}")
            else:
                print(f"❌ {symbol}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {symbol}: {str(e)}")
    
    print("\n🔍 Testing multiple symbol fetch...")
    try:
        # Test fetching all at once (if needed for optimization later)
        symbols_param = ','.join([f'"{s}"' for s in test_symbols])
        print(f"Symbol parameter: [{symbols_param}]")
        
        # For now, individual calls work better
        all_prices = {}
        for symbol in test_symbols:
            response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                original_symbol = symbol.replace('USDT', '/USDT')
                all_prices[original_symbol] = float(data['price'])
        
        print(f"✅ Successfully fetched {len(all_prices)} prices")
        for symbol, price in all_prices.items():
            print(f"   {symbol}: ${price:,.4f}")
            
    except Exception as e:
        print(f"❌ Multiple fetch error: {e}")

def test_position_calculations():
    """Test position calculation functions"""
    
    print("\n🧮 Testing position calculations...")
    
    # Sample position data
    test_position = {
        'entry': 95000.0,
        'amount': 0.001,
        'stop': 93000.0,
        'target': 98000.0,
        'time': '2026-02-07T18:00:00'
    }
    
    current_price = 96500.0  # Test current price
    portfolio_value = 1000.0
    
    # Basic calculations
    position_value = current_price * test_position['amount']
    unrealized_pnl = (current_price - test_position['entry']) * test_position['amount']
    unrealized_pnl_pct = ((current_price - test_position['entry']) / test_position['entry']) * 100
    position_size_pct = (position_value / portfolio_value * 100)
    
    print(f"📊 Test Position Metrics:")
    print(f"   Entry Price: ${test_position['entry']:,.2f}")
    print(f"   Current Price: ${current_price:,.2f}")
    print(f"   Position Size: {test_position['amount']} units")
    print(f"   Position Value: ${position_value:.2f}")
    print(f"   Unrealized P&L: ${unrealized_pnl:+.4f} ({unrealized_pnl_pct:+.2f}%)")
    print(f"   Portfolio %: {position_size_pct:.1f}%")
    
    # Risk calculations
    dist_to_stop_pct = ((current_price - test_position['stop']) / current_price * 100)
    dist_to_target_pct = ((test_position['target'] - current_price) / current_price * 100)
    
    print(f"📏 Distance Metrics:")
    print(f"   Distance to Stop: {dist_to_stop_pct:.1f}%")
    print(f"   Distance to Target: {dist_to_target_pct:.1f}%")
    
    print("✅ All calculations completed successfully!")

if __name__ == "__main__":
    test_binance_api()
    test_position_calculations()
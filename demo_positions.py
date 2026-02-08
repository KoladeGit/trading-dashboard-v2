#!/usr/bin/env python3
"""
Demo script to add sample positions to bot_data.json for testing the live position tracker
"""

import json
from datetime import datetime, timedelta

# Create demo positions with realistic data
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
    },
    "DOGE/USDT": {
        "entry": 0.3842,
        "amount": 650.0,
        "stop": 0.3650,
        "target": 0.4100,
        "time": (datetime.now() - timedelta(hours=4, minutes=22)).isoformat(),
        "reason": "whale_accumulation_pattern"
    }
}

def add_demo_positions():
    """Add demo positions to bot_data.json"""
    
    # Load current bot data
    try:
        with open('/Users/kolade/clawd/trading-dashboard-v2/bot_data.json', 'r') as f:
            bot_data = json.load(f)
    except:
        print("Error: Could not load bot_data.json")
        return
    
    # Add demo positions
    if 'trading_state' not in bot_data:
        bot_data['trading_state'] = {}
    
    bot_data['trading_state']['positions'] = demo_positions
    bot_data['last_updated'] = datetime.now().isoformat()
    
    # Update account balance to show realistic portfolio value
    if 'account' not in bot_data:
        bot_data['account'] = {}
    bot_data['account']['total_usd'] = 1250.75  # Demo portfolio value
    
    # Save updated data
    try:
        with open('/Users/kolade/clawd/trading-dashboard-v2/bot_data.json', 'w') as f:
            json.dump(bot_data, f, indent=2)
        print("✅ Demo positions added successfully!")
        print(f"Added {len(demo_positions)} demo positions:")
        for symbol in demo_positions:
            print(f"  - {symbol}")
    except Exception as e:
        print(f"❌ Error saving bot_data.json: {e}")

def remove_demo_positions():
    """Remove demo positions from bot_data.json"""
    
    try:
        with open('/Users/kolade/clawd/trading-dashboard-v2/bot_data.json', 'r') as f:
            bot_data = json.load(f)
    except:
        print("Error: Could not load bot_data.json")
        return
    
    # Clear positions
    if 'trading_state' in bot_data:
        bot_data['trading_state']['positions'] = {}
    
    bot_data['last_updated'] = datetime.now().isoformat()
    
    try:
        with open('/Users/kolade/clawd/trading-dashboard-v2/bot_data.json', 'w') as f:
            json.dump(bot_data, f, indent=2)
        print("✅ Demo positions removed successfully!")
    except Exception as e:
        print(f"❌ Error saving bot_data.json: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        remove_demo_positions()
    else:
        add_demo_positions()
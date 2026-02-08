#!/usr/bin/env python3
"""
Quick test of the enhanced live position tracker
"""

import streamlit as st
import json
from live_positions import integrate_live_positions_section

# Simple test app
st.set_page_config(
    page_title="Live Position Tracker Test",
    page_icon="📍",
    layout="wide"
)

# Load bot data
try:
    with open('bot_data.json', 'r') as f:
        bot_data = json.load(f)
    
    st.title("🚀 LIVE POSITION TRACKER TEST")
    
    # Show current positions count
    positions = bot_data.get('trading_state', {}).get('positions', {})
    st.write(f"📊 Found {len(positions)} positions in bot_data.json")
    
    # Run the enhanced live position tracker
    integrate_live_positions_section(bot_data)
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.write("Make sure bot_data.json exists with demo positions")
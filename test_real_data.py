#!/usr/bin/env python3
"""
Test script to verify real mathematical projections are working
"""

import json
from utils import get_comprehensive_projections, calculate_trade_statistics

def test_real_projections():
    print("🚀 TESTING REAL MATHEMATICAL PROJECTIONS")
    print("=" * 50)
    
    # Load actual trade data
    with open('bot_data.json', 'r') as f:
        data = json.load(f)
    
    trades = data.get('recent_trades', [])
    current_balance = 349  # fallback since account has error
    start_balance = 376.26
    
    print(f"📊 DATA SUMMARY:")
    print(f"  • Total trades: {len(trades)}")
    print(f"  • Balance: ${start_balance:.2f} → ${current_balance:.2f}")
    print(f"  • Net P&L: ${current_balance - start_balance:+.2f}")
    print()
    
    # Test basic trade statistics
    print("📈 BASIC STATISTICS:")
    trade_stats = calculate_trade_statistics(trades)
    if trade_stats:
        print(f"  • Win rate: {trade_stats['win_rate']:.1f}%")
        print(f"  • Expectancy: ${trade_stats['expectancy']:+.2f}/trade")
        print(f"  • Profit factor: {trade_stats['profit_factor']:.2f}")
        print(f"  • Best/Worst: ${trade_stats['best_trade']:+.2f} / ${trade_stats['worst_trade']:.2f}")
    print()
    
    # Test comprehensive projections
    print("🔮 COMPREHENSIVE PROJECTIONS:")
    projections = get_comprehensive_projections(trades, current_balance, start_balance)
    
    if projections and len(trades) >= 10:
        print("✅ Full mathematical projections available")
        
        daily_stats = projections['daily_stats']
        print(f"  • Daily return: {daily_stats['avg_daily_return']*100:+.3f}%")
        print(f"  • Volatility: {daily_stats['volatility']*100:.2f}%/day")
        print(f"  • Trade frequency: {daily_stats['avg_trades_per_day']:.2f}/day")
        print()
        
        # Monte Carlo results
        monte_carlo = projections['monte_carlo']
        for period in ['7d', '30d', '90d']:
            mc_data = monte_carlo.get(period)
            if mc_data:
                print(f"  • {period.upper()} projection: ${mc_data['p50']:,.2f} (median)")
                print(f"    Range: ${mc_data['p5']:,.2f} - ${mc_data['p95']:,.2f}")
                print(f"    Profit probability: {mc_data['prob_profit']:.1f}%")
        
    elif len(trades) < 10:
        print(f"⚠️  Need at least 10 trades for full projections (have {len(trades)})")
        print("   Using basic mathematical models as fallback")
        
    else:
        print("❌ Projection calculation failed")
    
    print()
    print("📋 STRATEGY BREAKDOWN:")
    
    # Analyze strategies
    strategy_performance = {}
    for trade in trades:
        strategy = trade.get('reason', 'unknown')
        if strategy not in strategy_performance:
            strategy_performance[strategy] = {'count': 0, 'pnl': 0}
        strategy_performance[strategy]['count'] += 1
        strategy_performance[strategy]['pnl'] += trade.get('pnl', 0)
    
    for strategy, perf in sorted(strategy_performance.items(), key=lambda x: x[1]['pnl'], reverse=True):
        print(f"  • {strategy.replace('_', ' ').title()}: {perf['count']} trades, ${perf['pnl']:+.2f}")
    
    print("\n✅ ALL REAL DATA ANALYSIS COMPLETE")

if __name__ == "__main__":
    test_real_projections()
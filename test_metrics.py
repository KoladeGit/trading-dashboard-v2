#!/usr/bin/env python3
import json
from datetime import datetime, timedelta

def load_trades_from_jsonl():
    trades = []
    with open('/Users/kolade/clawd/trading-bot/data/trades.jsonl', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                trades.append(json.loads(line))
    return trades

def calculate_performance_metrics(trades, starting_balance, current_balance, period_days=None):
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
    
    # Expectancy
    expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)
    
    # Max Drawdown calculation
    equity_curve = [starting_balance]
    running_balance = starting_balance
    
    sorted_trades = sorted(trades, key=lambda x: x.get('exit_time', ''))
    for t in sorted_trades:
        running_balance += t.get('pnl', 0)
        equity_curve.append(running_balance)
    
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
    
    # Sharpe Ratio calculation
    if len(trades) >= 2:
        returns = [t.get('pnl', 0) for t in trades]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        sharpe_ratio = (avg_return / std_dev * (252 ** 0.5)) if std_dev > 0 else 0
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
    
    if current_streak_type:
        max_win_streak = max(max_win_streak, current_streak)
    else:
        max_loss_streak = max(max_loss_streak, current_streak)
    
    # Current streak
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
        'profit_factor': profit_factor,
        'risk_reward_ratio': risk_reward_ratio,
        'expectancy': expectancy,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe_ratio': sharpe_ratio,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'current_streak': recent_streak,
        'current_streak_type': recent_streak_type,
        'std_dev': std_dev,
        'equity_curve': equity_curve
    }

# Load and calculate
trades = load_trades_from_jsonl()
metrics = calculate_performance_metrics(trades, 376.26, 274.58)

print('=== PERFORMANCE METRICS ===')
print(f"Total Trades: {metrics['total_trades']}")
print(f"Win Rate: {metrics['win_rate']:.1f}% ({metrics['win_count']}W / {metrics['loss_count']}L)")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}% (${metrics['max_drawdown']:.2f})")
print(f"Average Win: ${metrics['avg_win']:.2f}")
print(f"Average Loss: ${metrics['avg_loss']:.2f}")
print(f"Risk/Reward: 1:{metrics['risk_reward_ratio']:.2f}")
print(f"Expectancy: ${metrics['expectancy']:.2f}")
print(f"Net P&L: ${metrics['net_pnl']:.2f}")
print(f"Best Trade: ${metrics['best_trade']:.2f}")
print(f"Worst Trade: ${metrics['worst_trade']:.2f}")
print(f"Current Streak: {metrics['current_streak']} {'Wins' if metrics['current_streak_type'] else 'Losses'}")
print(f"Max Win Streak: {metrics['max_win_streak']}")
print(f"Max Loss Streak: {metrics['max_loss_streak']}")

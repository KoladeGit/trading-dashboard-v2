"""
Trading Dashboard Projection Utilities
Real mathematical calculations for performance projections
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


def calculate_daily_returns(trades: List[Dict], current_balance: float, start_balance: float) -> Dict:
    """
    Calculate daily returns from trade history.
    
    Returns dict with:
    - daily_returns: list of daily return percentages
    - avg_daily_return: mean daily return
    - volatility: standard deviation of daily returns
    - total_days: number of trading days
    """
    if not trades:
        return None
    
    # Sort trades by exit time
    sorted_trades = sorted(trades, key=lambda x: x.get('exit_time', ''))
    
    # Get date range
    try:
        first_trade = datetime.fromisoformat(sorted_trades[0].get('exit_time', '').replace('Z', ''))
        last_trade = datetime.fromisoformat(sorted_trades[-1].get('exit_time', '').replace('Z', ''))
        total_days = max((last_trade - first_trade).days, 1)
    except:
        total_days = max(len(trades) / 2, 1)  # Fallback estimate
    
    # Group P&L by day
    daily_pnls = {}
    for trade in sorted_trades:
        try:
            exit_time = datetime.fromisoformat(trade.get('exit_time', '').replace('Z', ''))
            day_key = exit_time.date()
            if day_key not in daily_pnls:
                daily_pnls[day_key] = 0
            daily_pnls[day_key] += trade.get('pnl', 0)
        except:
            continue
    
    if not daily_pnls:
        return None
    
    # Calculate daily returns as percentages
    # Use running balance approach for accuracy
    running_balance = start_balance
    daily_returns = []
    
    for day_key in sorted(daily_pnls.keys()):
        day_pnl = daily_pnls[day_key]
        day_return = day_pnl / running_balance if running_balance > 0 else 0
        daily_returns.append(day_return)
        running_balance += day_pnl
    
    if not daily_returns:
        return None
    
    avg_daily_return = np.mean(daily_returns)
    volatility = np.std(daily_returns, ddof=1) if len(daily_returns) > 1 else 0.01  # Minimum 1% vol
    
    return {
        'daily_returns': daily_returns,
        'avg_daily_return': avg_daily_return,
        'volatility': volatility,
        'total_days': total_days,
        'trading_days': len(daily_pnls),
        'avg_trades_per_day': len(trades) / total_days if total_days > 0 else 0
    }


def calculate_projections(
    current_balance: float,
    avg_daily_return: float,
    volatility: float,
    days: int,
    confidence_z: float = 1.96  # 95% confidence
) -> Dict:
    """
    Calculate balance projections using compound returns with confidence intervals.
    
    Formula:
    - Projected = current × (1 + daily_return)^days
    - Upper CI = current × (1 + daily_return + z×volatility)^days
    - Lower CI = current × (1 + daily_return - z×volatility)^days
    """
    # Base projection (compound growth)
    growth_factor = (1 + avg_daily_return) ** days
    projected_balance = current_balance * growth_factor
    
    # Confidence intervals
    upper_factor = (1 + avg_daily_return + confidence_z * volatility) ** days
    lower_factor = (1 + avg_daily_return - confidence_z * volatility) ** days
    
    upper_balance = current_balance * upper_factor
    lower_balance = current_balance * lower_factor
    
    # Ensure lower bound is reasonable (not negative)
    lower_balance = max(lower_balance, current_balance * 0.1)  # Floor at 10% of current
    
    return {
        'projected': projected_balance,
        'upper_95': upper_balance,
        'lower_95': lower_balance,
        'expected_pnl': projected_balance - current_balance,
        'upper_pnl': upper_balance - current_balance,
        'lower_pnl': lower_balance - current_balance,
        'return_pct': (growth_factor - 1) * 100,
        'upper_return_pct': (upper_factor - 1) * 100,
        'lower_return_pct': (lower_factor - 1) * 100
    }


def run_monte_carlo_simulation(
    pnl_history: List[float],
    starting_balance: float,
    n_simulations: int = 5000,
    n_trades: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run Monte Carlo simulation using bootstrapped sampling from historical P&L.
    
    Returns:
    - simulations: array of shape (n_simulations, n_trades+1) with balance paths
    - final_balances: array of final balances for each simulation
    """
    if not pnl_history or len(pnl_history) < 5:
        return None, None
    
    simulations = []
    final_balances = []
    
    for _ in range(n_simulations):
        balance = starting_balance
        path = [balance]
        
        for _ in range(n_trades):
            # Sample with replacement from historical P&L distribution
            trade_pnl = np.random.choice(pnl_history)
            balance += trade_pnl
            path.append(max(balance, 0.01))  # Prevent negative balance
        
        simulations.append(path)
        final_balances.append(balance)
    
    return np.array(simulations), np.array(final_balances)


def calculate_trade_statistics(trades: List[Dict]) -> Dict:
    """
    Calculate comprehensive trade statistics from trade history.
    """
    if not trades:
        return None
    
    total_trades = len(trades)
    pnl_values = [t.get('pnl', 0) for t in trades]
    
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
    
    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    win_rate = win_count / total_trades if total_trades > 0 else 0
    
    # P&L stats
    gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
    gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
    net_pnl = gross_profit - gross_loss
    
    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    
    # Profit factor
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Risk/reward
    risk_reward = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    # Expectancy
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    # Statistical measures
    mean_pnl = np.mean(pnl_values)
    std_pnl = np.std(pnl_values, ddof=1) if len(pnl_values) > 1 else 0
    
    # Best/worst trades
    best_trade = max(pnl_values) if pnl_values else 0
    worst_trade = min(pnl_values) if pnl_values else 0
    
    # Calculate streaks
    sorted_trades = sorted(trades, key=lambda x: x.get('exit_time', ''))
    
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for t in sorted_trades:
        if t.get('pnl', 0) > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
    
    # Current streak (from most recent)
    current_streak = 0
    current_streak_type = None
    for t in reversed(sorted_trades):
        is_win = t.get('pnl', 0) > 0
        if current_streak_type is None:
            current_streak_type = is_win
            current_streak = 1
        elif is_win == current_streak_type:
            current_streak += 1
        else:
            break
    
    return {
        'total_trades': total_trades,
        'win_count': win_count,
        'loss_count': loss_count,
        'win_rate': win_rate * 100,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'net_pnl': net_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'risk_reward': risk_reward,
        'expectancy': expectancy,
        'mean_pnl': mean_pnl,
        'std_pnl': std_pnl,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'current_streak': current_streak,
        'current_streak_type': current_streak_type,
        'pnl_values': pnl_values
    }


def get_comprehensive_projections(
    trades: List[Dict],
    current_balance: float,
    start_balance: float
) -> Optional[Dict]:
    """
    Get comprehensive projections using multiple methods.
    
    Returns dict with both mathematical projections and Monte Carlo results.
    """
    if not trades or len(trades) < 10:
        return None
    
    # Calculate daily returns and volatility
    daily_stats = calculate_daily_returns(trades, current_balance, start_balance)
    if not daily_stats:
        return None
    
    # Get trade statistics
    trade_stats = calculate_trade_statistics(trades)
    
    # Mathematical projections (compound returns with confidence)
    proj_7d = calculate_projections(
        current_balance,
        daily_stats['avg_daily_return'],
        daily_stats['volatility'],
        7
    )
    
    proj_30d = calculate_projections(
        current_balance,
        daily_stats['avg_daily_return'],
        daily_stats['volatility'],
        30
    )
    
    proj_90d = calculate_projections(
        current_balance,
        daily_stats['avg_daily_return'],
        daily_stats['volatility'],
        90
    )
    
    # Monte Carlo simulation
    trades_7d = int(7 * daily_stats['avg_trades_per_day'])
    trades_30d = int(30 * daily_stats['avg_trades_per_day'])
    trades_90d = int(90 * daily_stats['avg_trades_per_day'])
    
    mc_7d = run_monte_carlo_simulation(trade_stats['pnl_values'], current_balance, 5000, max(trades_7d, 5))
    mc_30d = run_monte_carlo_simulation(trade_stats['pnl_values'], current_balance, 5000, max(trades_30d, 10))
    mc_90d = run_monte_carlo_simulation(trade_stats['pnl_values'], current_balance, 5000, max(trades_90d, 20))
    
    # Calculate Monte Carlo percentiles
    def get_mc_percentiles(final_balances, starting_balance):
        if final_balances is None or len(final_balances) == 0:
            return None
        return {
            'p5': np.percentile(final_balances, 5),
            'p25': np.percentile(final_balances, 25),
            'p50': np.percentile(final_balances, 50),
            'p75': np.percentile(final_balances, 75),
            'p95': np.percentile(final_balances, 95),
            'prob_profit': np.mean(final_balances > starting_balance) * 100,
            'prob_10pct_gain': np.mean(final_balances > starting_balance * 1.10) * 100,
            'prob_10pct_loss': np.mean(final_balances < starting_balance * 0.90) * 100,
            'prob_25pct_loss': np.mean(final_balances < starting_balance * 0.75) * 100
        }
    
    return {
        'daily_stats': daily_stats,
        'trade_stats': trade_stats,
        'math_projections': {
            '7d': proj_7d,
            '30d': proj_30d,
            '90d': proj_90d
        },
        'monte_carlo': {
            '7d': get_mc_percentiles(mc_7d[1], current_balance) if mc_7d[1] is not None else None,
            '30d': get_mc_percentiles(mc_30d[1], current_balance) if mc_30d[1] is not None else None,
            '90d': get_mc_percentiles(mc_90d[1], current_balance) if mc_90d[1] is not None else None
        },
        'methods': {
            'compound_growth': 'current × (1 + daily_return)^days',
            'confidence_interval': '±1.96σ volatility bands',
            'monte_carlo': '5,000 bootstrapped simulations'
        }
    }

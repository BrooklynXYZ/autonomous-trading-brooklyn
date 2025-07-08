import pandas as pd
import numpy as np
import warnings
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import load_config
from src.data.market_data import get_historical_data
from src.data.indicators import (compute_sma, compute_rsi, compute_macd, 
                               compute_bollinger_bands, compute_volume_indicators, compute_atr)
from src.ai.ensemble_model import EnsembleTradingModel
from src.ai.signal_generator import SignalGenerator
from src.ai.risk_analyzer import RiskAnalyzer

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def run_single_symbol_backtest(symbol, config, initial_capital):
    """
    Runs a backtest for a single trading symbol with dynamic risk management.
    """
    print(f"\n{'='*20} Starting Backtest for {symbol} {'='*20}")
    
    trade_period_days = 90
    train_period_days = 90
    total_days = trade_period_days + train_period_days
    
    # 1. Load Data
    df = get_historical_data(symbol, interval='1h', period=f'{total_days}d')
    if df.empty:
        print(f"Could not fetch data for {symbol}. Skipping.")
        return None

    # 2. Feature Engineering
    df['sma_20'] = compute_sma(df, window=20)
    df['sma_50'] = compute_sma(df, window=50)
    df['rsi'] = compute_rsi(df)
    df['macd'] = compute_macd(df)
    bb_data = compute_bollinger_bands(df)
    df = pd.concat([df, bb_data], axis=1)
    vol_data = compute_volume_indicators(df)
    df = pd.concat([df, vol_data], axis=1)
    df['atr'] = compute_atr(df) # Add ATR for risk management
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    if df.empty:
        print(f"Not enough data for {symbol} after feature engineering. Skipping.")
        return None

    # 3. Train-Test Split
    train_size = int(len(df) * 0.5)
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]

    features = ['sma_20', 'sma_50', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'volume_ma', 'atr']
    X_train = train_df[features]
    y_train = train_df['target']
    X_test = test_df[features]

    # 4. Train Model
    print(f"Training model for {symbol}...")
    model = EnsembleTradingModel()
    model.train(X_train, y_train)

    # 5. Simulation Environment
    signal_generator = SignalGenerator(model, symbol)
    risk_analyzer = RiskAnalyzer(risk_per_trade=config.risk_per_trade)
    
    cash = initial_capital
    asset_holdings = 0.0
    stop_loss_price = 0
    take_profit_price = 0
    
    print(f"Running simulation for {symbol}...")
    # Simulation Loop
    for i in range(len(test_df)):
        current_price = test_df['Close'].iloc[i]
        current_atr = test_df['atr'].iloc[i]

        # Check for stop-loss or take-profit if a position is open
        if asset_holdings > 0:
            if current_price <= stop_loss_price:
                cash += asset_holdings * stop_loss_price # Exit at stop price
                asset_holdings = 0
                stop_loss_price, take_profit_price = 0, 0
                continue 
            if current_price >= take_profit_price:
                cash += asset_holdings * take_profit_price # Exit at take profit price
                asset_holdings = 0
                stop_loss_price, take_profit_price = 0, 0
                continue

        # Generate signal if not in a position
        if asset_holdings == 0:
            signal = signal_generator.generate_signal(X_test.iloc[i:i+1].values, test_df.iloc[:i+1])

            if signal == 'buy':
                position_size_usd = risk_analyzer.calculate_position_size(cash, 0.02) # Fixed 2% for size calc
                if position_size_usd > cash: position_size_usd = cash
                
                amount_to_buy = position_size_usd / current_price
                asset_holdings += amount_to_buy
                cash -= position_size_usd
                
                # Set dynamic SL/TP using ATR
                stop_loss_price = current_price - (current_atr * config.stop_loss_atr_multiplier)
                take_profit_price = current_price + (current_atr * config.take_profit_atr_multiplier)

    # Calculate final portfolio value for this symbol
    final_portfolio_value = cash + asset_holdings * test_df['Close'].iloc[-1]
    
    print(f"Final Portfolio Value for {symbol}: ${final_portfolio_value:.2f}")
    return final_portfolio_value


def run_multi_symbol_backtest():
    """
    Orchestrates a multi-symbol backtest with compounding profits.
    """
    print("🚀 Starting Multi-Symbol Backtest with Compounding...")

    try:
        config = load_config('config/main.yaml')
    except FileNotFoundError:
        print("❌ Error: config/main.yaml not found. Please ensure the file exists.")
        return

    initial_capital = 10.0
    trading_pairs = config.trading_pairs  # Access the trading pairs from the config
    if not trading_pairs:
        print("❌ No trading pairs defined in config/main.yaml. Exiting.")
        return

    # Start with the initial capital
    current_capital = initial_capital
    total_final_value = 0
    successful_backtests = 0

    for symbol in trading_pairs:
        print(f"\n💰 Allocating ${current_capital:.2f} to {symbol}...")
        final_value = run_single_symbol_backtest(symbol, config, current_capital)
        if final_value is not None:
            current_capital = final_value  # Reinvest the profits/losses into the next symbol
            total_final_value += final_value
            successful_backtests += 1

    if successful_backtests == 0:
        print("\nNo backtests were completed successfully.")
        return

    # Aggregate and Display Final Results
    print("\n" + "="*50)
    print("       📊 AGGREGATE BACKTEST RESULTS WITH COMPOUNDING")
    print("="*50)
    print(f"Initial Total Portfolio Value: ${initial_capital:.2f}")
    print(f"Final Total Portfolio Value:   ${current_capital:.2f}")
    
    total_return_pct = (current_capital - initial_capital) / initial_capital * 100
    print(f"Total Return:                  {total_return_pct:.2f}%")
    
    print("\n" + "="*50)
    print("🎯 Goal: $10 → $1000 (9900% return)")
    goal_achieved_pct = ((current_capital - 10) / (1000 - 10)) * 100
    print(f"Achievement: {max(0, goal_achieved_pct):.2f}% of goal")
    print("="*50)

if __name__ == "__main__":
    run_multi_symbol_backtest()
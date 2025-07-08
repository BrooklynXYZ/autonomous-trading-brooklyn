import pandas as pd
import numpy as np
from core.config import load_config
from data.market_data import get_historical_data
from data.indicators import compute_sma, compute_rsi
from ai.model import TradingModel
from ai.signal_generator import SignalGenerator
from ai.risk_analyzer import RiskAnalyzer
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def run_backtest():
    """
    Runs a backtest of the trading strategy.
    """
    print("Starting backtest...")

    # 1. Configuration
    try:
        main_config = load_config('config/main.yaml')
    except FileNotFoundError:
        print("Error: config/main.yaml not found.")
        return
        
    initial_capital = 10.0
    trade_period_days = 90
    train_period_days = 90
    total_days = trade_period_days + train_period_days
    symbol = f"{main_config.base_currency}-{main_config.quote_currency}"
    
    # 2. Load Data
    print(f"Fetching {total_days} days of historical data for {symbol}...")
    df = get_historical_data(symbol, interval='1h', period=f'{total_days}d')
    if df.empty:
        print(f"Could not fetch historical data for {symbol}. Please check the symbol or your connection.")
        return

    # 3. Feature Engineering
    df['sma'] = compute_sma(df)
    df['rsi'] = compute_rsi(df)
    # For backtesting, we'll use a neutral sentiment score as we don't have historical sentiment data.
    df['sentiment'] = 0.5 
    
    # Create a simple target variable for training: 1 if price increases in the next hour, 0 otherwise
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)

    # 4. Train-Test Split
    train_size = int(len(df) * (train_period_days / total_days))
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]

    features = ['sma', 'rsi', 'sentiment']
    X_train = train_df[features]
    y_train = train_df['target']
    X_test = test_df[features]

    if X_train.empty or y_train.empty:
        print("Not enough data to train the model. Try a longer period.")
        return

    # 5. Train Model
    print("Training the AI model...")
    model = TradingModel()
    model.train(X_train, y_train)
    print("Model training complete.")

    # 6. Setup Simulation Environment
    signal_generator = SignalGenerator(model)
    risk_analyzer = RiskAnalyzer(risk_per_trade=main_config.risk_per_trade)
    
    # Simulation variables
    cash = initial_capital
    asset_holdings = 0.0
    portfolio_value = initial_capital
    stop_loss_pct = 0.02 # 2% stop-loss
    
    portfolio_history = []

    print(f"\nRunning simulation for {trade_period_days} days...")
    # 7. Simulation Loop
    for i in range(len(test_df)):
        current_price = test_df['Close'].iloc[i]
        
        # Generate signal
        current_features = X_test.iloc[i:i+1]
        signal = signal_generator.generate_signal(current_features.values)

        # Execute trades
        if signal == 'buy' and cash > 0:
            position_size_usd = risk_analyzer.calculate_position_size(cash, stop_loss_pct)
            if position_size_usd > cash:
                position_size_usd = cash # Use all available cash if calculated size is too large
            
            amount_to_buy = position_size_usd / current_price
            asset_holdings += amount_to_buy
            cash -= position_size_usd
            # print(f"BUY: {amount_to_buy:.6f} {main_config.base_currency} at ${current_price:.2f}")

        elif signal == 'sell' and asset_holdings > 0:
            cash += asset_holdings * current_price
            asset_holdings = 0
            # print(f"SELL: All holdings at ${current_price:.2f}")

        # Update portfolio value for this timestep
        portfolio_value = cash + asset_holdings * current_price
        portfolio_history.append(portfolio_value)

    # 8. Results
    print("\n--- Backtest Results ---")
    print(f"Initial Portfolio Value: ${initial_capital:.2f}")
    print(f"Final Portfolio Value:   ${portfolio_value:.2f}")
    
    total_return_pct = (portfolio_value - initial_capital) / initial_capital * 100
    print(f"Total Return:            {total_return_pct:.2f}%")
    
    print("\nBacktest complete. To run, use the command:")
    print("python scripts/backtest.py")


if __name__ == "__main__":
    run_backtest()
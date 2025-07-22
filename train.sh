# 1. Collect market data
echo "📊 Collecting historical data..."
python scripts/collect_data.py

# 2. Prepare features  
echo "🔧 Engineering features..."
python scripts/prepare_features.py

# 3. Train the model
echo "🤖 Training RL model..."
python scripts/train_model.py

# 4. Test the system
echo "✅ Testing trading system..."
python src/main.py

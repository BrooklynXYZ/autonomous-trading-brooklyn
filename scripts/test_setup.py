"""Test the setup and integration"""

import sys
import os
sys.path.append('src')

def test_imports():
    """Test if all imports work"""
    try:
        import torch
        import numpy as np
        import pandas as pd
        from trading.recall_client import RecallClient
        from models.rl_model import PPONetwork
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_model_loading():
    """Test model creation and loading"""
    try:
        from models.rl_model import PPONetwork
        model = PPONetwork()
        
        # Test forward pass
        import torch
        dummy_input = torch.randn(1, 46)
        output = model(dummy_input)
        print("✅ Model creation and forward pass successful")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_recall_client():
    """Test Recall client setup"""
    try:
        from trading.recall_client import RecallClient
        client = RecallClient()
        print("✅ Recall client initialization successful")
        return True
    except Exception as e:
        print(f"❌ Recall client test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing setup...")
    
    tests = [
        ("Import Test", test_imports),
        ("Model Test", test_model_loading), 
        ("Client Test", test_recall_client)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System is ready for trading.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()

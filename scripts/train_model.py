import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add src to path
sys.path.append('src')

from models.rl_model import PPONetwork
from models.trading_environment import TradingEnvironment

class PPOTrainer:
    def __init__(self, env, lr=3e-4, gamma=0.99, eps_clip=0.2, k_epochs=4):
        self.env = env
        self.lr = lr
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.k_epochs = k_epochs
        
        # Initialize model
        self.model = PPONetwork()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        
        self.memory = []
        
    def collect_rollouts(self, n_steps=2000):
        """Collect training rollouts"""
        
        state = self.env.reset()
        rollouts = []
        
        for step in range(n_steps):
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            with torch.no_grad():
                action, log_prob, value = self.model.act(state_tensor)
            
            next_state, reward, done, info = self.env.step(action)
            
            rollouts.append({
                'state': state,
                'action': action[0],
                'reward': reward,
                'log_prob': log_prob[0].item(),
                'value': value.item(),
                'done': done
            })
            
            state = next_state
            
            if done:
                state = self.env.reset()
        
        return rollouts
    
    def compute_returns_and_advantages(self, rollouts):
        """Compute discounted returns and advantages"""
        
        returns = []
        advantages = []
        
        # Compute returns
        discounted_return = 0
        for rollout in reversed(rollouts):
            if rollout['done']:
                discounted_return = 0
            discounted_return = rollout['reward'] + self.gamma * discounted_return
            returns.insert(0, discounted_return)
        
        returns = torch.tensor(returns, dtype=torch.float32)
        
        # Compute advantages (simple version)
        values = torch.tensor([r['value'] for r in rollouts], dtype=torch.float32)
        advantages = returns - values
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        return returns, advantages
    
    def update_policy(self, rollouts):
        """Update policy using PPO"""
        
        # Extract data
        states = torch.tensor([r['state'] for r in rollouts], dtype=torch.float32)
        actions = torch.tensor([r['action'] for r in rollouts], dtype=torch.long)
        old_log_probs = torch.tensor([r['log_prob'] for r in rollouts], dtype=torch.float32)
        
        # Compute returns and advantages
        returns, advantages = self.compute_returns_and_advantages(rollouts)
        
        # PPO update
        for _ in range(self.k_epochs):
            # Get current policy predictions
            action_probs, _, values = self.model(states)
            
            # Calculate new log probabilities
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            
            # Ratio for clipping
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Clipped surrogate objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # Value loss
            value_loss = nn.MSELoss()(values.squeeze(), returns)
            
            # Entropy bonus
            entropy_loss = -dist.entropy().mean()
            
            # Total loss
            total_loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss
            
            # Update
            self.optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
            self.optimizer.step()
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'entropy_loss': entropy_loss.item()
        }
    
    def train(self, n_episodes=500):
        """Main training loop"""
        
        print("🚀 Starting PPO Training...")
        
        best_reward = float('-inf')
        
        for episode in range(n_episodes):
            # Collect rollouts
            rollouts = self.collect_rollouts(n_steps=1000)
            
            # Update policy
            loss_info = self.update_policy(rollouts)
            
            # Calculate episode metrics
            episode_reward = sum(r['reward'] for r in rollouts)
            episode_length = len(rollouts)
            
            # Save best model
            if episode_reward > best_reward:
                best_reward = episode_reward
                torch.save(self.model.state_dict(), 'data/models/best_model.pth')
                print(f"💾 New best model saved! Reward: {best_reward:.4f}")
            
            # Log progress
            if episode % 10 == 0:
                print(f"Episode {episode:4d} | Reward: {episode_reward:8.4f} | "
                      f"Length: {episode_length:4d} | "
                      f"Policy Loss: {loss_info['policy_loss']:.4f}")
        
        print("✅ Training completed!")

def load_training_data():
    """Load processed training data"""
    
    # For simplified training, create synthetic data
    # In production, load from data/processed/
    
    n_samples = 10000
    n_features = 46
    
    # Generate synthetic market data
    np.random.seed(42)
    data = np.random.randn(n_samples, n_features).astype(np.float32)
    
    # Add some structure to make it more realistic
    for i in range(1, n_samples):
        data[i] = 0.95 * data[i-1] + 0.05 * data[i]  # Add some persistence
    
    return data

def main():
    """Main training function"""
    
    # Create models directory
    os.makedirs('data/models', exist_ok=True)
    
    # Load training data
    print("📊 Loading training data...")
    training_data = load_training_data()
    
    # Create trading environment
    print("🏗️  Creating trading environment...")
    env = TradingEnvironment(training_data)
    
    # Create trainer
    print("🤖 Initializing PPO trainer...")
    trainer = PPOTrainer(env)
    
    # Start training
    trainer.train(n_episodes=200)  # Reduced for quick training
    
    print("🎯 Training pipeline completed!")

if __name__ == "__main__":
    main()

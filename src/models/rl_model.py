import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
import numpy as np

class PPONetwork(nn.Module):
    """PPO Network for trading decisions"""
    
    def __init__(self, state_dim=46, action_dim=6, hidden_dim=256):
        super(PPONetwork, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Shared feature extraction layers
        self.shared_layers = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim//2),
            nn.ReLU()
        )
        
        # Policy head (actor) - for base token actions
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim//2, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Value head (critic)
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim//2, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, state):
        """Forward pass through the network"""
        
        shared_features = self.shared_layers(state)
        
        action_probs = self.policy_head(shared_features)
        value = self.value_head(shared_features)
        
        return action_probs, action_probs, value  # Return twice for compatibility
    
    def act(self, state):
        """Sample action from policy"""
        
        action_probs, _, value = self.forward(state)
        
        action_dist = Categorical(action_probs)
        action = action_dist.sample()
        
        return [action.item()], [action_dist.log_prob(action)], value
    
    def evaluate(self, states, actions):
        """Evaluate states and actions for training"""
        
        action_probs, _, values = self.forward(states)
        
        action_dist = Categorical(action_probs)
        action_logprobs = action_dist.log_prob(actions)
        dist_entropy = action_dist.entropy()
        
        return action_logprobs, values.squeeze(), dist_entropy 
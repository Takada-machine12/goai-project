# ai/network.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class GoNeuralNetwork(nn.Module):
    def __init__(self, board_size=9, num_channels=256):
        super(GoNeuralNetwork, self).__init__()
        
        self.board_size = board_size
        self.input_channels = 17
        self.num_channels = num_channels
        
        # 共通の畳み込み層
        self.conv1 = nn.Conv2d(self.input_channels, num_channels, 3, padding=1)
        self.conv2 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        self.conv3 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        
        # Policy Head
        self.policy_conv = nn.Conv2d(num_channels, 2, 1)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size + 1)
        
        # Value Head
        self.value_conv = nn.Conv2d(num_channels, 1, 1)
        self.value_fc1 = nn.Linear(board_size * board_size, 256)
        self.value_fc2 = nn.Linear(256, 1)
        
    def forword(self, x):
        # 共通部分
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        
        # Policy Head
        policy = F.relu(self.policy_conv(x))
        policy = policy.view(-1, 2 * self.board_size * self.board_size)
        policy = self.policy_fc(policy)
        policy_probs = F.softmax(policy, dim=1)
        
        # Value Head
        value = F.relu(self.value_conv(x))
        value = value.view(-1, self.board_size * self.board_size)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))
        
        return policy_probs, value
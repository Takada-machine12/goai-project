# ai/network.py
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class ResidualBlock(nn.Module):
    """残差ブロック - AlphaGoで使用される基本ブロック"""
    
    def __init__(self, num_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(num_channels)
        self.conv2 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(num_channels)
        
    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual  # 残差接続
        return F.relu(out)


class ImprovedGoNeuralNetwork(nn.Module):
    """改良された囲碁ニューラルネットワーク（AlphaGoスタイル）"""
    
    def __init__(self, board_size=9, num_channels=256, num_residual_blocks=19):
        super(ImprovedGoNeuralNetwork, self).__init__()
        
        self.board_size = board_size
        self.num_channels = num_channels
        
        # 入力特徴: 17チャンネル
        self.input_channels = 17
        
        # 初期畳み込み層
        self.initial_conv = nn.Conv2d(self.input_channels, num_channels, 3, padding=1)
        self.initial_bn = nn.BatchNorm2d(num_channels)
        
        # 残差ブロック
        self.residual_blocks = nn.ModuleList([
            ResidualBlock(num_channels) for _ in range(num_residual_blocks)
        ])
        
        # Policy Head（行動確率出力）
        self.policy_conv = nn.Conv2d(num_channels, 2, 1)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size + 1)
        
        # Value Head（局面評価出力）
        self.value_conv = nn.Conv2d(num_channels, 1, 1)
        self.value_bn = nn.BatchNorm2d(1)
        self.value_fc1 = nn.Linear(board_size * board_size, 256)
        self.value_fc2 = nn.Linear(256, 1)
        
        # 重みの初期化
        self._initialize_weights()
    
    def forward(self, x):
        """順伝播"""
        # 初期畳み込み
        x = F.relu(self.initial_bn(self.initial_conv(x)))
        
        # 残差ブロック
        for block in self.residual_blocks:
            x = block(x)
        
        # Policy Head
        policy = F.relu(self.policy_bn(self.policy_conv(x)))
        policy = policy.view(policy.size(0), -1)  # フラット化
        policy = self.policy_fc(policy)
        policy_probs = F.softmax(policy, dim=1)
        
        # Value Head
        value = F.relu(self.value_bn(self.value_conv(x)))
        value = value.view(value.size(0), -1)  # フラット化
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))
        
        return policy_probs, value
    
    def _initialize_weights(self):
        """重みの初期化"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def predict(self, game_state):
        """
        ゲーム状態から予測を行う
        
        Args:
            game_state: ゲーム状態
            
        Returns:
            action_probs: 行動確率
            value: 状態価値
        """
        self.eval()
        features = self._game_state_to_features(game_state)
        
        with torch.no_grad():
            action_probs, value = self.forward(features)
            return action_probs.cpu().numpy().flatten(), value.cpu().item()
    
    def _game_state_to_features(self, game_state):
        """ゲーム状態を特徴量に変換"""
        board_size = game_state.board.size
        features = np.zeros((17, board_size, board_size), dtype=np.float32)
        
        # 基本的な特徴
        current_player = game_state.current_player
        
        # チャンネル0: 現在のプレイヤーの石
        features[0] = (game_state.board.board == current_player).astype(np.float32)
        
        # チャンネル1: 相手プレイヤーの石
        features[1] = (game_state.board.board == -current_player).astype(np.float32)
        
        # チャンネル2: 空の位置
        features[2] = (game_state.board.board == 0).astype(np.float32)
        
        # チャンネル3: 1手前の盤面（履歴情報）
        if hasattr(game_state, 'previous_board') and game_state.previous_board is not None:
            features[3] = (game_state.previous_board == current_player).astype(np.float32)
            features[4] = (game_state.previous_board == -current_player).astype(np.float32)
        
        # チャンネル5: 2手前の盤面
        if hasattr(game_state, 'board_history') and len(game_state.board_history) >= 2:
            prev_board = game_state.board_history[-2]
            features[5] = (prev_board == current_player).astype(np.float32)
            features[6] = (prev_board == -current_player).astype(np.float32)
        
        # チャンネル7: 合法手マスク
        legal_moves = game_state.get_legal_moves()
        for move in legal_moves:
            if move is not None:  # パス以外
                x, y = move
                if 0 <= x < board_size and 0 <= y < board_size:
                    features[7, x, y] = 1.0
        
        # チャンネル8: 現在のプレイヤー（全面に1または-1）
        features[8] = np.full((board_size, board_size), current_player, dtype=np.float32)
        
        # チャンネル9-10: 石の集合（連）の情報
        self._add_group_features(features[9:11], game_state.board.board, board_size)
        
        # チャンネル11-12: アタリ（取られそうな石）の情報
        self._add_atari_features(features[11:13], game_state, board_size)
        
        # チャンネル13-14: 呼吸点（リバティ）の数
        self._add_liberty_features(features[13:15], game_state, board_size)
        
        # チャンネル15: エッジからの距離
        self._add_distance_features(features[15], board_size)
        
        # チャンネル16: 全て1（バイアス項）
        features[16] = np.ones((board_size, board_size), dtype=np.float32)
        
        return torch.FloatTensor(features).unsqueeze(0)
    
    def _add_group_features(self, features, board, board_size):
        """石の集合（連）の特徴を追加"""
        visited = np.zeros((board_size, board_size), dtype=bool)
        
        for i in range(board_size):
            for j in range(board_size):
                if not visited[i, j] and board[i, j] != 0:
                    group = self._get_group(board, i, j, board_size)
                    group_size = len(group)
                    
                    # グループサイズに基づく特徴
                    for x, y in group:
                        visited[x, y] = True
                        if board[x, y] == 1:  # 黒
                            features[0, x, y] = min(group_size / 10.0, 1.0)
                        else:  # 白
                            features[1, x, y] = min(group_size / 10.0, 1.0)
    
    def _add_atari_features(self, features, game_state, board_size):
        """アタリ（取られそうな石）の特徴を追加"""
        board = game_state.board.board
        
        for i in range(board_size):
            for j in range(board_size):
                if board[i, j] != 0:
                    liberties = self._count_liberties(board, i, j, board_size)
                    if liberties == 1:  # アタリ状態
                        if board[i, j] == 1:  # 黒
                            features[0, i, j] = 1.0
                        else:  # 白
                            features[1, i, j] = 1.0
    
    def _add_liberty_features(self, features, game_state, board_size):
        """呼吸点（リバティ）数の特徴を追加"""
        board = game_state.board.board
        
        for i in range(board_size):
            for j in range(board_size):
                if board[i, j] != 0:
                    liberties = self._count_liberties(board, i, j, board_size)
                    liberty_feature = min(liberties / 8.0, 1.0)  # 正規化
                    
                    if board[i, j] == 1:  # 黒
                        features[0, i, j] = liberty_feature
                    else:  # 白
                        features[1, i, j] = liberty_feature
    
    def _add_distance_features(self, feature, board_size):
        """エッジからの距離特徴を追加"""
        for i in range(board_size):
            for j in range(board_size):
                distance_to_edge = min(i, j, board_size - 1 - i, board_size - 1 - j)
                feature[i, j] = distance_to_edge / (board_size // 2)
    
    def _get_group(self, board, start_x, start_y, board_size):
        """指定位置から始まる連を取得"""
        color = board[start_x, start_y]
        if color == 0:
            return set()
        
        group = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            if (x, y) in group:
                continue
                
            group.add((x, y))
            
            # 隣接する同色の石を探す
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < board_size and 0 <= ny < board_size and
                    board[nx, ny] == color and (nx, ny) not in group):
                    stack.append((nx, ny))
        
        return group
    
    def _count_liberties(self, board, x, y, board_size):
        """指定位置の石の連の呼吸点数を数える"""
        group = self._get_group(board, x, y, board_size)
        liberties = set()
        
        for gx, gy in group:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = gx + dx, gy + dy
                if (0 <= nx < board_size and 0 <= ny < board_size and
                    board[nx, ny] == 0):
                    liberties.add((nx, ny))
        
        return len(liberties)


class NetworkTrainer:
    """ニューラルネットワークの訓練を管理するクラス"""
    
    def __init__(self, network, lr=0.001, weight_decay=1e-4):
        self.network = network
        self.optimizer = torch.optim.Adam(network.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = torch.optim.lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.9)
        
    def train_step(self, batch_states, batch_mcts_probs, batch_values):
        """
        一回の訓練ステップを実行
        
        Args:
            batch_states: バッチ状態
            batch_mcts_probs: MCTS確率分布
            batch_values: 実際の勝敗
            
        Returns:
            loss: 損失値
        """
        self.network.train()
        self.optimizer.zero_grad()
        
        # 予測
        pred_probs, pred_values = self.network(batch_states)
        
        # 損失計算
        value_loss = F.mse_loss(pred_values.squeeze(), batch_values)
        policy_loss = -torch.sum(batch_mcts_probs * torch.log(pred_probs + 1e-8)) / batch_states.size(0)
        
        total_loss = value_loss + policy_loss
        
        # 逆伝播
        total_loss.backward()
        self.optimizer.step()
        
        return total_loss.item(), value_loss.item(), policy_loss.item()
    
    def save_model(self, filepath):
        """モデルを保存"""
        torch.save({
            'model_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
        }, filepath)
        print(f"モデルを保存しました: {filepath}")
    
    def load_model(self, filepath):
        """モデルを読み込み"""
        try:
            checkpoint = torch.load(filepath, map_location='cpu')
            self.network.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            print(f"モデルを読み込みました: {filepath}")
            return True
        except Exception as e:
            print(f"モデルの読み込みに失敗しました: {e}")
            return False


class SimpleGoNetwork(nn.Module):
    """軽量版の囲碁ニューラルネットワーク（テスト用）"""
    
    def __init__(self, board_size=9, num_channels=64):
        super(SimpleGoNetwork, self).__init__()
        
        self.board_size = board_size
        self.input_channels = 17
        
        # 簡単な畳み込み層
        self.conv1 = nn.Conv2d(self.input_channels, num_channels, 3, padding=1)
        self.conv2 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        self.conv3 = nn.Conv2d(num_channels, num_channels, 3, padding=1)
        
        # Policy Head
        self.policy_conv = nn.Conv2d(num_channels, 2, 1)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size + 1)
        
        # Value Head
        self.value_conv = nn.Conv2d(num_channels, 1, 1)
        self.value_fc1 = nn.Linear(board_size * board_size, 64)
        self.value_fc2 = nn.Linear(64, 1)
        
    def forward(self, x):
        # 畳み込み層
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        
        # Policy Head
        policy = F.relu(self.policy_conv(x))
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)
        policy_probs = F.softmax(policy, dim=1)
        
        # Value Head
        value = F.relu(self.value_conv(x))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))
        
        return policy_probs, value
    
    def _game_state_to_features(self, game_state):
        """ゲーム状態を特徴量に変換（簡略版）"""
        board_size = game_state.board.size
        features = np.zeros((17, board_size, board_size), dtype=np.float32)
        
        current_player = game_state.current_player
        
        # 基本的な特徴のみ
        features[0] = (game_state.board.board == current_player).astype(np.float32)
        features[1] = (game_state.board.board == -current_player).astype(np.float32)
        features[2] = (game_state.board.board == 0).astype(np.float32)
        features[8] = np.full((board_size, board_size), current_player, dtype=np.float32)
        features[16] = np.ones((board_size, board_size), dtype=np.float32)
        
        return torch.FloatTensor(features).unsqueeze(0)
    
    def predict(self, game_state):
        """予測実行"""
        self.eval()
        features = self._game_state_to_features(game_state)
        
        with torch.no_grad():
            action_probs, value = self.forward(features)
            return action_probs.cpu().numpy().flatten(), value.cpu().item()


def test_network():
    """ネットワークのテスト"""
    print("ニューラルネットワークのテスト開始...")
    
    # 改良版ネットワークをテスト
    print("\n=== 改良版ネットワーク ===")
    network = ImprovedGoNeuralNetwork(board_size=9, num_channels=128, num_residual_blocks=4)
    
    # ダミーデータでテスト
    batch_size = 2
    dummy_input = torch.randn(batch_size, 17, 9, 9)
    
    # 順伝播テスト
    policy_probs, values = network(dummy_input)
    
    print(f"入力形状: {dummy_input.shape}")
    print(f"方策出力形状: {policy_probs.shape}")
    print(f"価値出力形状: {values.shape}")
    print(f"方策の和: {torch.sum(policy_probs, dim=1)}")
    print(f"価値の範囲: {torch.min(values):.3f} ~ {torch.max(values):.3f}")
    
    # 簡単版ネットワークもテスト
    print("\n=== 簡単版ネットワーク ===")
    simple_network = SimpleGoNetwork(board_size=9, num_channels=32)
    policy_probs2, values2 = simple_network(dummy_input)
    
    print(f"方策出力形状: {policy_probs2.shape}")
    print(f"価値出力形状: {values2.shape}")
    print(f"方策の和: {torch.sum(policy_probs2, dim=1)}")
    print(f"価値の範囲: {torch.min(values2):.3f} ~ {torch.max(values2):.3f}")
    
    # パラメータ数の比較
    def count_parameters(model):
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\n改良版パラメータ数: {count_parameters(network):,}")
    print(f"簡単版パラメータ数: {count_parameters(simple_network):,}")
    
    print("\nニューラルネットワークのテスト完了！")


def create_test_game_state():
    """テスト用のゲーム状態を作成"""
    from go_engine.game import Game
    
    game = Game(board_size=9)
    
    # いくつかの石を配置
    game.make_move((2, 2))  # 黒
    game.make_move((2, 3))  # 白
    game.make_move((3, 2))  # 黒
    game.make_move((3, 3))  # 白
    
    return game


def test_with_real_game():
    """実際のゲーム状態でテスト"""
    print("\n実際のゲーム状態でのテスト...")
    
    game = create_test_game_state()
    
    # ネットワークで予測
    network = SimpleGoNetwork(board_size=9, num_channels=32)
    action_probs, value = network.predict(game)
    
    print(f"行動確率の形状: {action_probs.shape}")
    print(f"行動確率の和: {np.sum(action_probs):.3f}")
    print(f"状態価値: {value:.3f}")
    print(f"最も確率の高い行動インデックス: {np.argmax(action_probs)}")
    
    # インデックスを座標に変換
    best_action_idx = np.argmax(action_probs)
    if best_action_idx == 9 * 9:
        print("推奨行動: パス")
    else:
        x = best_action_idx // 9
        y = best_action_idx % 9
        print(f"推奨行動: ({x}, {y})")


if __name__ == "__main__":
    test_network()
    test_with_real_game()
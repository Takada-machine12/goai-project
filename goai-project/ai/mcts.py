# ai/mcts.py
import math
import random
import numpy as np
import torch
from copy import deepcopy
from collections import defaultdict

class MCTSNode:
    def __init__(self, game_state, parent=None, move=None, prior_prob=0.0):
        """
        MCTSノードの初期化
        
        Args:
            game_state: ゲームの状態
            parent: 親ノード
            move: このノードに到達するための手
            prior_prob: 事前確率（ニューラルネットワークから）
        """
        self.game_state = game_state  # ゲーム状態のコピー
        self.parent = parent
        self.move = move  # このノードに到達した手
        self.children = {}  # 子ノード {move: MCTSNode}
        
        # MCTS統計
        self.visit_count = 0  # 訪問回数
        self.value_sum = 0.0  # 累積値
        self.prior_prob = prior_prob  # 事前確率
        
        # 展開済みかどうか
        self.is_expanded = False
        
    def is_leaf(self):
        """葉ノードかどうかを判定"""
        return len(self.children) == 0
    
    def get_value(self):
        """平均値を取得"""
        if self.visit_count == 0:
            return 0.0
        return self.value_sum / self.visit_count
    
    def select_child(self, c_puct=1.0):
        """
        UCB1アルゴリズムで最適な子ノードを選択
        
        Args:
            c_puct: 探索の強さを制御するパラメータ
            
        Returns:
            選択された子ノード
        """
        best_score = -float('inf')
        best_child = None
        
        for child in self.children.values():
            # UCB1スコアの計算
            # Q(s,a) + c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))
            
            exploitation = child.get_value()  # 活用項
            
            if child.visit_count == 0:
                exploration = float('inf')  # 未訪問ノードは優先
            else:
                exploration = (c_puct * child.prior_prob * 
                             math.sqrt(self.visit_count) / child.visit_count)
            
            score = exploitation + exploration
            
            if score > best_score:
                best_score = score
                best_child = child
                
        return best_child
    
    def expand(self, legal_moves, action_probs):
        """
        ノードを展開して子ノードを作成
        
        Args:
            legal_moves: 合法手のリスト
            action_probs: 各手の事前確率
        """
        for move in legal_moves:
            # 新しいゲーム状態を作成
            new_game_state = deepcopy(self.game_state)
            new_game_state.make_move(move)
            
            # 事前確率を取得
            move_idx = self._move_to_index(move, new_game_state.board.size)
            prior = action_probs[move_idx] if move_idx < len(action_probs) else 0.0
            
            # 子ノードを作成
            child = MCTSNode(new_game_state, parent=self, move=move, prior_prob=prior)
            self.children[move] = child
            
        self.is_expanded = True
    
    def backup(self, value):
        """
        バックプロパゲーション: 値を親ノードに伝播
        
        Args:
            value: 評価値
        """
        self.visit_count += 1
        self.value_sum += value
        
        if self.parent:
            # プレイヤーが変わるので値を反転
            self.parent.backup(-value)
    
    def _move_to_index(self, move, board_size):
        """手をインデックスに変換"""
        if move is None:  # パス
            return board_size * board_size
        x, y = move
        return x * board_size + y


class MCTS:
    def __init__(self, neural_network=None, num_simulations=800, c_puct=1.0, 
                 add_dirichlet_noise=False, dirichlet_alpha=0.03, dirichlet_epsilon=0.25):
        """
        モンテカルロ木探索の初期化
        
        Args:
            neural_network: 評価用ニューラルネットワーク
            num_simulations: シミュレーション回数
            c_puct: UCBの探索パラメータ
            add_dirichlet_noise: ディリクレノイズを追加するか
            dirichlet_alpha: ディリクレ分布のパラメータ
            dirichlet_epsilon: ノイズの混合比率
        """
        self.neural_network = neural_network
        self.num_simulations = num_simulations
        self.c_puct = c_puct
        self.add_dirichlet_noise = add_dirichlet_noise
        self.dirichlet_alpha = dirichlet_alpha
        self.dirichlet_epsilon = dirichlet_epsilon
        
    def search(self, game_state):
        """
        MCTSを実行して最適な手を探索
        
        Args:
            game_state: 現在のゲーム状態
            
        Returns:
            action_probs: 各手の確率分布
        """
        # ルートノードを作成
        root = MCTSNode(deepcopy(game_state))
        
        # 指定回数のシミュレーションを実行
        for _ in range(self.num_simulations):
            self._simulate(root)
        
        # 訪問回数に基づいて行動確率を計算
        return self._get_action_probs(root, game_state.board.size)
    
    def _simulate(self, node):
        """
        1回のMCTSシミュレーションを実行
        
        Args:
            node: 開始ノード
        """
        # 1. 選択フェーズ: 葉ノードまで選択
        current = node
        while not current.is_leaf() and not current.game_state.game_over:
            current = current.select_child(self.c_puct)
        
        # 2. 展開フェーズ: 葉ノードを展開
        if not current.game_state.game_over and not current.is_expanded:
            legal_moves = current.game_state.get_legal_moves()
            
            if self.neural_network:
                # ニューラルネットワークで評価
                action_probs, value = self._evaluate_with_network(current.game_state)
            else:
                # ランダムポリシー
                board_size = current.game_state.board.size
                action_probs = np.ones(board_size * board_size + 1) / (board_size * board_size + 1)
                value = self._random_rollout(current.game_state)
            
            # ディリクレノイズを追加（ルートノードのみ）
            if self.add_dirichlet_noise and current == node:
                action_probs = self._add_dirichlet_noise(action_probs)
            
            current.expand(legal_moves, action_probs)
            
        else:
            # 終端ノードの場合
            if current.game_state.game_over:
                value = self._evaluate_terminal_state(current.game_state)
            elif self.neural_network:
                _, value = self._evaluate_with_network(current.game_state)
            else:
                value = self._random_rollout(current.game_state)
        
        # 3. バックプロパゲーション
        current.backup(value)
    
    def _evaluate_with_network(self, game_state):
        """
        ニューラルネットワークでゲーム状態を評価
        
        Args:
            game_state: ゲーム状態
            
        Returns:
            action_probs: 行動確率分布
            value: 状態価値
        """
        # ゲーム状態を特徴量に変換
        features = self._game_state_to_features(game_state)
        
        with torch.no_grad():
            # ニューラルネットワークで予測
            action_probs, value = self.neural_network(features)
            
            # テンソルをnumpy配列に変換
            action_probs = action_probs.cpu().numpy().flatten()
            value = value.cpu().item()
            
            # 現在のプレイヤーに応じて値を調整
            if game_state.current_player == -1:  # 白の場合
                value = -value
                
        return action_probs, value
    
    def _random_rollout(self, game_state):
        """
        ランダムロールアウトで終局まで対局
        
        Args:
            game_state: ゲーム状態
            
        Returns:
            結果（勝ち: 1, 負け: -1, 引き分け: 0）
        """
        temp_state = deepcopy(game_state)
        original_player = temp_state.current_player
        
        # 最大手数を制限（無限ループ防止）
        max_moves = temp_state.board.size * temp_state.board.size * 2
        
        for _ in range(max_moves):
            if temp_state.game_over:
                break
                
            legal_moves = temp_state.get_legal_moves()
            if not legal_moves:
                break
                
            # ランダムに手を選択
            move = random.choice(legal_moves)
            temp_state.make_move(move)
        
        # ゲーム結果を評価
        return self._evaluate_terminal_state(temp_state) * (1 if original_player == temp_state.current_player else -1)
    
    def _evaluate_terminal_state(self, game_state):
        """
        終端状態の評価
        
        Args:
            game_state: ゲーム状態
            
        Returns:
            評価値
        """
        # 簡単なスコアリング（実際の囲碁ルールより簡略化）
        black_stones = np.sum(game_state.board.board == 1)
        white_stones = np.sum(game_state.board.board == -1)
        
        if black_stones > white_stones:
            return 1.0 if game_state.current_player == 1 else -1.0
        elif white_stones > black_stones:
            return 1.0 if game_state.current_player == -1 else -1.0
        else:
            return 0.0
    
    def _game_state_to_features(self, game_state):
        """
        ゲーム状態をニューラルネットワークの入力特徴量に変換
        
        Args:
            game_state: ゲーム状態
            
        Returns:
            特徴量テンソル
        """
        board_size = game_state.board.size
        
        # 17チャンネルの特徴マップを作成
        features = np.zeros((17, board_size, board_size), dtype=np.float32)
        
        # チャンネル0: 現在のプレイヤーの石
        features[0] = (game_state.board.board == game_state.current_player).astype(np.float32)
        
        # チャンネル1: 相手プレイヤーの石
        features[1] = (game_state.board.board == -game_state.current_player).astype(np.float32)
        
        # チャンネル2: 空の場所
        features[2] = (game_state.board.board == 0).astype(np.float32)
        
        # チャンネル3: 合法手
        legal_moves = game_state.get_legal_moves()
        for move in legal_moves:
            if move is not None:  # パス以外
                x, y = move
                features[3, x, y] = 1.0
        
        # チャンネル4-16: その他の特徴（履歴、アタリ状況など）
        # 簡略化のため、定数で埋める
        features[4:] = 0.5
        
        # バッチ次元を追加してテンソルに変換
        return torch.FloatTensor(features).unsqueeze(0)
    
    def _add_dirichlet_noise(self, action_probs):
        """
        ディリクレノイズを追加（探索の多様性向上）
        
        Args:
            action_probs: 元の行動確率
            
        Returns:
            ノイズが追加された行動確率
        """
        noise = np.random.dirichlet(self.dirichlet_alpha * np.ones(len(action_probs)))
        return (1 - self.dirichlet_epsilon) * action_probs + self.dirichlet_epsilon * noise
    
    def _get_action_probs(self, root, board_size, temperature=1.0):
        """
        ルートノードから行動確率を計算
        
        Args:
            root: ルートノード
            board_size: 盤面サイズ
            temperature: 温度パラメータ（0で決定論的）
            
        Returns:
            行動確率分布
        """
        action_counts = np.zeros(board_size * board_size + 1)
        
        # 各子ノードの訪問回数を取得
        for move, child in root.children.items():
            move_idx = child._move_to_index(move, board_size) if move else board_size * board_size
            action_counts[move_idx] = child.visit_count
        
        if temperature == 0:
            # 決定論的選択
            action_probs = np.zeros_like(action_counts)
            best_action = np.argmax(action_counts)
            action_probs[best_action] = 1.0
        else:
            # 温度を適用
            action_counts = action_counts ** (1.0 / temperature)
            action_probs = action_counts / np.sum(action_counts)
        
        return action_probs
    
    def get_best_move(self, game_state):
        """
        最適な手を取得
        
        Args:
            game_state: 現在のゲーム状態
            
        Returns:
            最適な手
        """
        action_probs = self.search(game_state)
        best_action_idx = np.argmax(action_probs)
        
        board_size = game_state.board.size
        
        if best_action_idx == board_size * board_size:
            return None  # パス
        else:
            x = best_action_idx // board_size
            y = best_action_idx % board_size
            return (x, y)


class MCTSPlayer:
    """MCTSを使用するプレイヤー"""
    
    def __init__(self, neural_network=None, num_simulations=800, c_puct=1.0):
        self.mcts = MCTS(neural_network, num_simulations, c_puct)
        
    def get_move(self, game_state):
        """手を取得"""
        return self.mcts.get_best_move(game_state)
    
    def get_action_probs(self, game_state, temperature=1.0):
        """行動確率分布を取得（学習用）"""
        action_probs = self.mcts.search(game_state)
        
        if temperature == 0:
            # 決定論的選択
            best_idx = np.argmax(action_probs)
            probs = np.zeros_like(action_probs)
            probs[best_idx] = 1.0
            return probs
        else:
            # 温度を適用
            action_probs = action_probs ** (1.0 / temperature)
            return action_probs / np.sum(action_probs)
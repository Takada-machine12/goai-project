# ai/training.py
import torch
import numpy as np
import random
from collections import deque
import pickle
import os
from tqdm import tqdm
from copy import deepcopy

from .network import ImprovedGoNeuralNetwork, NetworkTrainer
from .mcts import MCTSPlayer
from go_engine.game import Game

class SelfPlayTrainingSystem:
    """自己対戦による学習システム"""
    
    def __init__(self, board_size=9, network_config=None, training_config=None):
        """
        初期化
        
        Args:
            board_size: 盤面サイズ
            network_config: ネットワーク設定
            training_config: 訓練設定
        """
        self.board_size = board_size
        
        # デフォルト設定
        if network_config is None:
            network_config = {
                'num_channels': 256,
                'num_residual_blocks': 10,
                'lr': 0.001,
                'weight_decay': 1e-4
            }
        
        if training_config is None:
            training_config = {
                'num_iterations': 100,
                'num_self_play_games': 25,
                'num_mcts_simulations': 400,
                'num_training_epochs': 10,
                'batch_size': 32,
                'memory_size': 100000,
                'c_puct': 1.0,
                'temperature_threshold': 30,
                'model_save_interval': 10
            }
        
        self.network_config = network_config
        self.training_config = training_config
        
        # ニューラルネットワークの初期化
        self.network = ImprovedGoNeuralNetwork(
            board_size=board_size,
            num_channels=network_config['num_channels'],
            num_residual_blocks=network_config['num_residual_blocks']
        )
        
        # トレーナーの初期化
        self.trainer = NetworkTrainer(
            self.network,
            lr=network_config['lr'],
            weight_decay=network_config['weight_decay']
        )
        
        # 経験メモリ（リプレイバッファ）
        self.memory = deque(maxlen=training_config['memory_size'])
        
        # 統計情報
        self.iteration_stats = []
        
    def train(self, save_dir='trained_models'):
        """
        メイン訓練ループ
        
        Args:
            save_dir: モデル保存ディレクトリ
        """
        os.makedirs(save_dir, exist_ok=True)
        
        print("🎮 囲碁AI自己対戦学習開始！")
        print(f"盤面サイズ: {self.board_size}x{self.board_size}")
        print(f"訓練反復回数: {self.training_config['num_iterations']}")
        print(f"自己対戦ゲーム数/反復: {self.training_config['num_self_play_games']}")
        print(f"MCTS シミュレーション数: {self.training_config['num_mcts_simulations']}")
        
        for iteration in range(1, self.training_config['num_iterations'] + 1):
            print(f"\n=== 反復 {iteration}/{self.training_config['num_iterations']} ===")
            
            # 1. 自己対戦でデータを生成
            print("🎯 自己対戦データ生成中...")
            self_play_data = self.generate_self_play_data()
            
            # 2. メモリに追加
            self.memory.extend(self_play_data)
            print(f"📊 総メモリサイズ: {len(self.memory)}")
            
            # 3. ネットワークを訓練
            if len(self.memory) >= self.training_config['batch_size']:
                print("🧠 ニューラルネットワーク訓練中...")
                training_stats = self.train_network()
                
                # 統計を記録
                stats = {
                    'iteration': iteration,
                    'memory_size': len(self.memory),
                    'games_played': len(self_play_data),
                    **training_stats
                }
                self.iteration_stats.append(stats)
                
                print(f"📈 訓練損失: {training_stats['avg_total_loss']:.4f}")
                print(f"📈 価値損失: {training_stats['avg_value_loss']:.4f}")
                print(f"📈 方策損失: {training_stats['avg_policy_loss']:.4f}")
            
            # 4. 定期的にモデルを保存
            if iteration % self.training_config['model_save_interval'] == 0:
                model_path = os.path.join(save_dir, f'model_iteration_{iteration}.pt')
                self.trainer.save_model(model_path)
                print(f"💾 モデル保存: {model_path}")
                
                # 統計も保存
                stats_path = os.path.join(save_dir, f'stats_iteration_{iteration}.pkl')
                with open(stats_path, 'wb') as f:
                    pickle.dump(self.iteration_stats, f)
        
        # 最終モデルを保存
        final_model_path = os.path.join(save_dir, 'final_model.pt')
        self.trainer.save_model(final_model_path)
        print(f"✅ 訓練完了！最終モデル: {final_model_path}")
    
    def generate_self_play_data(self):
        """
        自己対戦でデータを生成
        
        Returns:
            自己対戦データのリスト
        """
        all_data = []
        
        # MCTSプレイヤーを作成
        mcts_player = MCTSPlayer(
            neural_network=self.network,
            num_simulations=self.training_config['num_mcts_simulations'],
            c_puct=self.training_config['c_puct']
        )
        
        for game_idx in tqdm(range(self.training_config['num_self_play_games']), 
                           desc="自己対戦"):
            game_data = self.play_single_game(mcts_player)
            all_data.extend(game_data)
        
        return all_data
    
    def play_single_game(self, mcts_player):
        """
        1回の自己対戦ゲームを実行
        
        Args:
            mcts_player: MCTSプレイヤー
            
        Returns:
            ゲームデータ
        """
        game = Game(self.board_size)
        game_data = []
        
        move_count = 0
        max_moves = self.board_size * self.board_size * 2  # 最大手数制限
        
        while not game.game_over and move_count < max_moves:
            # 現在の状態を保存
            current_state = deepcopy(game)
            
            # 温度パラメータ（序盤は高く、終盤は低く）
            temperature = 1.0 if move_count < self.training_config['temperature_threshold'] else 0.1
            
            # MCTSで行動確率を取得
            action_probs = mcts_player.get_action_probs(game, temperature=temperature)
            
            # 行動をサンプリング
            action_idx = np.random.choice(len(action_probs), p=action_probs)
            
            # インデックスを手に変換
            if action_idx == self.board_size * self.board_size:
                move = None  # パス
            else:
                x = action_idx // self.board_size
                y = action_idx % self.board_size
                move = (x, y)
            
            # データを記録（状態、行動確率、現在のプレイヤー）
            game_data.append({
                'state': current_state,
                'action_probs': action_probs,
                'current_player': game.current_player
            })
            
            # 手を実行
            success = game.make_move(move)
            if not success:
                # 不正な手の場合、ゲームを終了
                break
                
            move_count += 1
        
        # ゲーム結果を決定
        winner = self.determine_winner(game)
        
        # 各データポイントに結果を追加
        for data in game_data:
            # 勝者を現在のプレイヤーの視点から評価
            if winner == 0:  # 引き分け
                data['value'] = 0.0
            elif winner == data['current_player']:
                data['value'] = 1.0  # 勝ち
            else:
                data['value'] = -1.0  # 負け
        
        return game_data
    
    def determine_winner(self, game):
        """
        ゲームの勝者を決定（簡単なスコアリング）
        
        Args:
            game: ゲーム状態
            
        Returns:
            勝者 (1: 黒, -1: 白, 0: 引き分け)
        """
        board = game.board.board
        black_stones = np.sum(board == 1)
        white_stones = np.sum(board == -1)
        
        # 簡単な地の計算（空点を最も近い色に割り当て）
        black_territory, white_territory = self.count_territory(game)
        
        black_score = black_stones + black_territory
        white_score = white_stones + white_territory + 6.5  # コミ
        
        if black_score > white_score:
            return 1  # 黒の勝ち
        elif white_score > black_score:
            return -1  # 白の勝ち
        else:
            return 0  # 引き分け
    
    def count_territory(self, game):
        """
        簡単な地の計算
        
        Args:
            game: ゲーム状態
            
        Returns:
            (黒の地, 白の地)
        """
        board = game.board.board
        visited = np.zeros_like(board, dtype=bool)
        black_territory = 0
        white_territory = 0
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i, j] == 0 and not visited[i, j]:
                    # 空点から始まる領域を探索
                    territory, owner = self.flood_fill_territory(board, i, j, visited)
                    
                    if owner == 1:  # 黒の地
                        black_territory += territory
                    elif owner == -1:  # 白の地
                        white_territory += territory
        
        return black_territory, white_territory
    
    def flood_fill_territory(self, board, start_x, start_y, visited):
        """
        Flood fillで地を計算
        
        Args:
            board: 盤面
            start_x, start_y: 開始位置
            visited: 訪問済みマスク
            
        Returns:
            (地の大きさ, 所有者)
        """
        if board[start_x, start_y] != 0 or visited[start_x, start_y]:
            return 0, 0
        
        territory_points = []
        stack = [(start_x, start_y)]
        neighboring_colors = set()
        
        while stack:
            x, y = stack.pop()
            if visited[x, y]:
                continue
                
            visited[x, y] = True
            territory_points.append((x, y))
            
            # 隣接する点をチェック
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    if board[nx, ny] == 0 and not visited[nx, ny]:
                        stack.append((nx, ny))
                    elif board[nx, ny] != 0:
                        neighboring_colors.add(board[nx, ny])
        
        # 地の所有者を決定
        if len(neighboring_colors) == 1:
            owner = next(iter(neighboring_colors))
            return len(territory_points), owner
        else:
            return 0, 0  # 中立地
    
    def train_network(self):
        """
        ネットワークを訓練
        
        Returns:
            訓練統計
        """
        total_losses = []
        value_losses = []
        policy_losses = []
        
        # メモリからランダムサンプリング
        batch_size = self.training_config['batch_size']
        epochs = self.training_config['num_training_epochs']
        
        for epoch in range(epochs):
            # バッチをサンプリング
            batch_indices = random.sample(range(len(self.memory)), 
                                        min(batch_size, len(self.memory)))
            batch_data = [self.memory[i] for i in batch_indices]
            
            # バッチを準備
            batch_states = []
            batch_action_probs = []
            batch_values = []
            
            for data in batch_data:
                # 状態を特徴量に変換
                features = self.network._game_state_to_features(data['state'])
                batch_states.append(features.squeeze(0))
                batch_action_probs.append(data['action_probs'])
                batch_values.append(data['value'])
            
            # テンソルに変換
            batch_states = torch.stack(batch_states)
            batch_action_probs = torch.FloatTensor(batch_action_probs)
            batch_values = torch.FloatTensor(batch_values)
            
            # 訓練ステップ
            total_loss, value_loss, policy_loss = self.trainer.train_step(
                batch_states, batch_action_probs, batch_values
            )
            
            total_losses.append(total_loss)
            value_losses.append(value_loss)
            policy_losses.append(policy_loss)
        
        # 学習率を更新
        self.trainer.scheduler.step()
        
        return {
            'avg_total_loss': np.mean(total_losses),
            'avg_value_loss': np.mean(value_losses),
            'avg_policy_loss': np.mean(policy_losses)
        }
    
    def load_model(self, model_path):
        """訓練済みモデルを読み込み"""
        self.trainer.load_model(model_path)
        print(f"✅ モデル読み込み完了: {model_path}")
    
    def evaluate_against_random(self, num_games=10):
        """
        ランダムプレイヤーとの対戦で評価
        
        Args:
            num_games: 対戦ゲーム数
            
        Returns:
            勝率
        """
        mcts_player = MCTSPlayer(
            neural_network=self.network,
            num_simulations=200,  # 評価時は少し軽く
            c_puct=self.training_config['c_puct']
        )
        
        wins = 0
        
        for game_idx in tqdm(range(num_games), desc="評価対戦"):
            game = Game(self.board_size)
            
            # ランダムに先手後手を決定
            ai_is_black = random.choice([True, False])
            
            move_count = 0
            max_moves = self.board_size * self.board_size * 2
            
            while not game.game_over and move_count < max_moves:
                if (game.current_player == 1 and ai_is_black) or \
                   (game.current_player == -1 and not ai_is_black):
                    # AIの手番
                    move = mcts_player.get_move(game)
                else:
                    # ランダムプレイヤーの手番
                    legal_moves = game.get_legal_moves()
                    move = random.choice(legal_moves) if legal_moves else None
                
                if not game.make_move(move):
                    break
                    
                move_count += 1
            
            # 勝者判定
            winner = self.determine_winner(game)
            
            if (winner == 1 and ai_is_black) or (winner == -1 and not ai_is_black):
                wins += 1
        
        win_rate = wins / num_games
        print(f"🏆 対ランダム勝率: {win_rate:.2%} ({wins}/{num_games})")
        return win_rate


# 使用例
def main():
    """メイン実行関数"""
    
    # 訓練システムを初期化
    training_system = SelfPlayTrainingSystem(
        board_size=9,
        network_config={
            'num_channels': 128,  # 軽量化
            'num_residual_blocks': 6,  # 軽量化
            'lr': 0.002,
            'weight_decay': 1e-4
        },
        training_config={
            'num_iterations': 50,  # 少なめでテスト
            'num_self_play_games': 10,  # 少なめでテスト
            'num_mcts_simulations': 200,  # 軽量化
            'num_training_epochs': 5,
            'batch_size': 16,
            'memory_size': 10000,
            'c_puct': 1.0,
            'temperature_threshold': 15,
            'model_save_interval': 10
        }
    )
    
    # 訓練実行
    training_system.train()
    
    # ランダムプレイヤーとの対戦で評価
    training_system.evaluate_against_random(num_games=5)


if __name__ == "__main__":
    main()
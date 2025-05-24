# main.py - 高度なAI機能統合版
import torch
import argparse
import os
from go_engine.game import Game
from ai.network import ImprovedGoNeuralNetwork
from ai.mcts import MCTSPlayer
from ai.training import SelfPlayTrainingSystem

def human_vs_ai_game(model_path=None, board_size=9, mcts_simulations=400):
    """
    人間対AI対戦
    
    Args:
        model_path: 学習済みモデルのパス
        board_size: 盤面サイズ
        mcts_simulations: MCTSシミュレーション数
    """
    print("🎮 人間 vs AI 対戦開始！")
    
    # ゲームを初期化
    game = Game(board_size)
    
    # AIプレイヤーを初期化
    if model_path and os.path.exists(model_path):
        print(f"✅ 学習済みモデルを読み込み: {model_path}")
        network = ImprovedGoNeuralNetwork(board_size=board_size)
        checkpoint = torch.load(model_path, map_location='cpu')
        network.load_state_dict(checkpoint['model_state_dict'])
        ai_player = MCTSPlayer(network, num_simulations=mcts_simulations)
    else:
        print("⚠️ 学習済みモデルが見つかりません。ランダムAIを使用します。")
        ai_player = MCTSPlayer(None, num_simulations=mcts_simulations)
    
    # 人間が黒（先手）かどうかを選択
    while True:
        choice = input("先手（黒）で対戦しますか？ (y/n): ").lower()
        if choice in ['y', 'yes']:
            human_is_black = True
            break
        elif choice in ['n', 'no']:
            human_is_black = False
            break
        else:
            print("yまたはnで答えてください。")
    
    print(f"あなたは{'黒（先手）' if human_is_black else '白（後手）'}です。")
    print("手の入力形式: x,y (例: 3,4) またはパスの場合は 'pass'")
    print("ゲームを終了するには 'quit' と入力してください。\n")
    
    move_count = 0
    max_moves = board_size * board_size * 2
    
    while not game.game_over and move_count < max_moves:
        # 現在の盤面を表示
        print(f"\n=== {move_count + 1}手目 ===")
        print(f"現在のプレイヤー: {'黒' if game.current_player == 1 else '白'}")
        display_board_with_coordinates(game.board)
        
        is_human_turn = ((game.current_player == 1 and human_is_black) or 
                        (game.current_player == -1 and not human_is_black))
        
        if is_human_turn:
            # 人間の手番
            move = get_human_move(game)
            if move == "quit":
                print("ゲームを終了します。")
                return
        else:
            # AIの手番
            print("🤖 AIが思考中...")
            move = ai_player.get_move(game)
            if move is None:
                print("AIがパスしました。")
            else:
                print(f"AIの手: ({move[0]}, {move[1]})")
        
        # 手を実行
        success = game.make_move(move)
        if not success:
            print("❌ 不正な手です。")
            continue
            
        move_count += 1
    
    # ゲーム終了
    print("\n🏁 ゲーム終了！")
    display_board_with_coordinates(game.board)
    
    # 勝者判定（簡易版）
    determine_and_display_winner(game)

def get_human_move(game):
    """
    人間からの入力を取得
    
    Args:
        game: ゲーム状態
        
    Returns:
        手またはコマンド
    """
    legal_moves = game.get_legal_moves()
    
    while True:
        try:
            user_input = input("あなたの手を入力してください: ").strip().lower()
            
            if user_input == "quit":
                return "quit"
            elif user_input == "pass":
                if None in legal_moves:
                    return None
                else:
                    print("パスできません。合法手を入力してください。")
                    continue
            
            # 座標入力の解析
            parts = user_input.replace(" ", "").split(",")
            if len(parts) != 2:
                print("形式が正しくありません。x,y の形式で入力してください（例: 3,4）")
                continue
            
            x, y = int(parts[0]), int(parts[1])
            move = (x, y)
            
            if move in legal_moves:
                return move
            else:
                print("❌ その位置には打てません。別の位置を試してください。")
                print_legal_moves(legal_moves, game.board.size)
                
        except ValueError:
            print("数値を入力してください。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

def print_legal_moves(legal_moves, board_size):
    """合法手を表示"""
    moves = [move for move in legal_moves if move is not None]
    if len(moves) > 10:  # 多すぎる場合は一部のみ表示
        print(f"合法手の例: {moves[:10]}... (他 {len(moves)-10} 手)")
    else:
        print(f"合法手: {moves}")
    if None in legal_moves:
        print("パスも可能です。")

def display_board_with_coordinates(board):
    """座標付きで盤面を表示"""
    size = board.size
    
    # 列番号を表示
    print("   ", end="")
    for j in range(size):
        print(f"{j:2}", end=" ")
    print()
    
    # 盤面を表示
    for i in range(size):
        print(f"{i:2} ", end="")
        for j in range(size):
            if board.board[i, j] == 1:
                print(" B", end=" ")
            elif board.board[i, j] == -1:
                print(" W", end=" ")
            else:
                print(" .", end=" ")
        print()

def determine_and_display_winner(game):
    """勝者を判定して表示"""
    board = game.board.board
    black_stones = (board == 1).sum()
    white_stones = (board == -1).sum()
    
    print(f"\n📊 最終結果:")
    print(f"黒石: {black_stones}")
    print(f"白石: {white_stones}")
    
    # 簡易スコアリング
    if black_stones > white_stones:
        print("🏆 黒の勝利！")
    elif white_stones > black_stones:
        print("🏆 白の勝利！")
    else:
        print("🤝 引き分け！")

def ai_vs_ai_game(model1_path=None, model2_path=None, board_size=9, 
                  mcts_simulations=400, display_moves=True):
    """
    AI同士の対戦
    
    Args:
        model1_path: プレイヤー1のモデルパス
        model2_path: プレイヤー2のモデルパス
        board_size: 盤面サイズ
        mcts_simulations: MCTSシミュレーション数
        display_moves: 手順を表示するか
    """
    print("🤖 AI vs AI 対戦開始！")
    
    # ゲームを初期化
    game = Game(board_size)
    
    # AI プレイヤー1 (黒)
    if model1_path and os.path.exists(model1_path):
        network1 = ImprovedGoNeuralNetwork(board_size=board_size)
        checkpoint1 = torch.load(model1_path, map_location='cpu')
        network1.load_state_dict(checkpoint1['model_state_dict'])
        player1 = MCTSPlayer(network1, num_simulations=mcts_simulations)
        print(f"✅ プレイヤー1（黒）: {model1_path}")
    else:
        player1 = MCTSPlayer(None, num_simulations=mcts_simulations)
        print("⚠️ プレイヤー1（黒）: ランダムAI")
    
    # AI プレイヤー2 (白)
    if model2_path and os.path.exists(model2_path):
        network2 = ImprovedGoNeuralNetwork(board_size=board_size)
        checkpoint2 = torch.load(model2_path, map_location='cpu')
        network2.load_state_dict(checkpoint2['model_state_dict'])
        player2 = MCTSPlayer(network2, num_simulations=mcts_simulations)
        print(f"✅ プレイヤー2（白）: {model2_path}")
    else:
        player2 = MCTSPlayer(None, num_simulations=mcts_simulations)
        print("⚠️ プレイヤー2（白）: ランダムAI")
    
    move_count = 0
    max_moves = board_size * board_size * 2
    
    while not game.game_over and move_count < max_moves:
        if display_moves:
            print(f"\n=== {move_count + 1}手目 ===")
            print(f"現在のプレイヤー: {'黒' if game.current_player == 1 else '白'}")
            display_board_with_coordinates(game.board)
        
        # 現在のプレイヤーに応じてAIを選択
        current_player = player1 if game.current_player == 1 else player2
        
        # AIの手を取得
        move = current_player.get_move(game)
        
        if display_moves:
            if move is None:
                print("パス")
            else:
                print(f"手: ({move[0]}, {move[1]})")
        
        # 手を実行
        success = game.make_move(move)
        if not success:
            print("❌ AIが不正な手を選択しました。")
            break
            
        move_count += 1
    
    # 最終結果
    print("\n🏁 ゲーム終了！")
    display_board_with_coordinates(game.board)
    determine_and_display_winner(game)
    
    return game

def train_new_model(board_size=9, config_type="light"):
    """
    新しいモデルを訓練
    
    Args:
        board_size: 盤面サイズ
        config_type: 設定タイプ ("light", "standard", "heavy")
    """
    print(f"🧠 新しいモデルの訓練開始 (設定: {config_type})")
    
    # 設定を選択
    if config_type == "light":
        network_config = {
            'num_channels': 64,
            'num_residual_blocks': 4,
            'lr': 0.002,
            'weight_decay': 1e-4
        }
        training_config = {
            'num_iterations': 20,
            'num_self_play_games': 5,
            'num_mcts_simulations': 100,
            'num_training_epochs': 3,
            'batch_size': 16,
            'memory_size': 5000,
            'c_puct': 1.0,
            'temperature_threshold': 10,
            'model_save_interval': 5
        }
    elif config_type == "standard":
        network_config = {
            'num_channels': 128,
            'num_residual_blocks': 8,
            'lr': 0.001,
            'weight_decay': 1e-4
        }
        training_config = {
            'num_iterations': 50,
            'num_self_play_games': 10,
            'num_mcts_simulations': 200,
            'num_training_epochs': 5,
            'batch_size': 32,
            'memory_size': 20000,
            'c_puct': 1.0,
            'temperature_threshold': 20,
            'model_save_interval': 10
        }
    else:  # heavy
        network_config = {
            'num_channels': 256,
            'num_residual_blocks': 16,
            'lr': 0.001,
            'weight_decay': 1e-4
        }
        training_config = {
            'num_iterations': 100,
            'num_self_play_games': 25,
            'num_mcts_simulations': 400,
            'num_training_epochs': 10,
            'batch_size': 64,
            'memory_size': 50000,
            'c_puct': 1.0,
            'temperature_threshold': 30,
            'model_save_interval': 10
        }
    
    # 訓練システムを初期化
    training_system = SelfPlayTrainingSystem(
        board_size=board_size,
        network_config=network_config,
        training_config=training_config
    )
    
    # 訓練実行
    training_system.train()
    
    # 評価
    print("\n📊 訓練完了後の評価:")
    training_system.evaluate_against_random(num_games=10)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='囲碁AI システム')
    parser.add_argument('mode', choices=['train', 'play', 'ai_vs_ai', 'demo'], 
                       help='実行モード')
    parser.add_argument('--board-size', type=int, default=9, 
                       help='盤面サイズ (デフォルト: 9)')
    parser.add_argument('--model', type=str, default='trained_models/final_model.pt',
                       help='モデルファイルのパス')
    parser.add_argument('--model2', type=str, default=None,
                       help='AI vs AI用の2番目のモデル')
    parser.add_argument('--simulations', type=int, default=400,
                       help='MCTSシミュレーション数')
    parser.add_argument('--config', choices=['light', 'standard', 'heavy'], 
                       default='standard', help='訓練設定')
    
    args = parser.parse_args()
    
    if args.mode == 'train':
        # 新しいモデルを訓練
        train_new_model(args.board_size, args.config)
        
    elif args.mode == 'play':
        # 人間 vs AI 対戦
        human_vs_ai_game(args.model, args.board_size, args.simulations)
        
    elif args.mode == 'ai_vs_ai':
        # AI vs AI 対戦
        ai_vs_ai_game(args.model, args.model2, args.board_size, args.simulations)
        
    elif args.mode == 'demo':
        # デモ: ランダムAI同士の対戦
        print("🎮 デモモード: ランダムAI同士の対戦")
        ai_vs_ai_game(None, None, args.board_size, 100, display_moves=True)

def quick_demo():
    """簡単なデモ実行"""
    print("🎮 囲碁AI システム - クイックデモ")
    print("ランダムAI同士の対戦を実行します...")
    
    game = Game(board_size=9)
    
    # 軽量なMCTSプレイヤーを作成
    player1 = MCTSPlayer(None, num_simulations=50)  # 軽量化
    player2 = MCTSPlayer(None, num_simulations=50)  # 軽量化
    
    move_count = 0
    max_moves = 81 * 2  # 9x9 * 2
    
    while not game.game_over and move_count < max_moves:
        print(f"\n=== {move_count + 1}手目 ===")
        print(f"現在のプレイヤー: {'黒' if game.current_player == 1 else '白'}")
        display_board_with_coordinates(game.board)
        
        # 現在のプレイヤーに応じてAIを選択
        current_player = player1 if game.current_player == 1 else player2
        
        # AIの手を取得
        move = current_player.get_move(game)
        
        if move is None:
            print("パス")
        else:
            print(f"手: ({move[0]}, {move[1]})")
        
        # 手を実行
        success = game.make_move(move)
        if not success:
            print("❌ 不正な手")
            break
            
        move_count += 1
        
        # 30手でデモ終了
        if move_count >= 30:
            print("デモ終了（30手）")
            break
    
    print("\n🏁 デモ終了！")
    display_board_with_coordinates(game.board)
    determine_and_display_winner(game)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # 引数がない場合はクイックデモ
        quick_demo()
    else:
        # 引数がある場合は通常のmain関数
        main()
# main.py
import torch
import random
from go_engine.game import Game
from ai.network import GoNeuralNetwork

def main():
    # ゲームの初期化
    game = Game(board_size=9)
    
    # モデルの初期化
    model = GoNeuralNetwork(board_size=9)
    
    # モデルのロード（存在する場合）
    try:
        model.load_state_dict(torch.load('trained_models/model.pt'))
        print("モデルをロードしました")
    except:
        print("新しいモデルを初期化しました")
    
    # ゲームループ（シンプルな例）
    turn_count = 0
    max_turns = 50  # 最大ターン数を制限して無限ループを防ぐ
    
    while not game.game_over and turn_count < max_turns:
        # 現在の盤面を表示
        print(f"ターン {turn_count+1}, プレイヤー: {'黒' if game.current_player == 1 else '白'}")
        game.board.display()
        
        # 合法手をランダムに選択（シンプルな実装）
        legal_moves = game.get_legal_moves()
        
        # パスを除く合法手
        non_pass_moves = [move for move in legal_moves if move is not None]
        
        if non_pass_moves:
            # 合法手が存在する場合はランダムに選択
            move = random.choice(non_pass_moves)
        else:
            # 合法手がない場合はパス
            move = None
        
        # 手を適用
        if move is not None:
            print(f"手を打ちます: ({move[0]}, {move[1]})")
        else:
            print("パスします")
            
        success = game.make_move(move)
        
        if not success:
            print("不正な手です")
        
        turn_count += 1
    
    # ゲーム終了
    if game.game_over:
        print("ゲーム終了（2回連続パス）")
    else:
        print(f"最大ターン数({max_turns})に達したため終了")
    
    # 最終盤面の表示
    game.board.display()

if __name__ == "__main__":
    main()
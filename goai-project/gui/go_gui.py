# gui/go_gui.py
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from go_engine.game import Game
from ai.network import ImprovedGoNeuralNetwork
from ai.mcts import MCTSPlayer
import torch

class GoGUI:
    def __init__(self, board_size=9):
        self.board_size = board_size
        self.cell_size = 40  # 各マスのサイズ
        self.margin = 30     # 盤面の余白
        self.stone_radius = 15  # 石の半径
        
        # ゲーム状態
        self.game = Game(board_size)
        self.ai_player = None
        self.human_is_black = True
        self.game_mode = "human_vs_ai"  # human_vs_ai, ai_vs_ai, human_vs_human
        self.ai_thinking = False
        
        # GUI初期化
        self.setup_gui()
        self.setup_board()
        self.load_ai_model()
        
    def setup_gui(self):
        """GUIの基本設定"""
        self.root = tk.Tk()
        self.root.title("囲碁AI - Go Game")
        self.root.resizable(False, False)
        
        # メインフレーム
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10)
        
        # 上部コントロールパネル
        self.setup_control_panel(main_frame)
        
        # 盤面キャンバス
        canvas_size = self.cell_size * (self.board_size - 1) + 2 * self.margin
        self.canvas = tk.Canvas(
            main_frame, 
            width=canvas_size, 
            height=canvas_size,
            bg='#DEB887',  # 木目調の色
            highlightthickness=2,
            highlightbackground='#8B7355'
        )
        self.canvas.pack(pady=10)
        
        # 下部情報パネル
        self.setup_info_panel(main_frame)
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
    def setup_control_panel(self, parent):
        """上部コントロールパネルの設定"""
        control_frame = tk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ゲームモード選択
        mode_frame = tk.LabelFrame(control_frame, text="ゲームモード")
        mode_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="human_vs_ai")
        modes = [
            ("人間 vs AI", "human_vs_ai"),
            ("AI vs AI", "ai_vs_ai"),
            ("人間 vs 人間", "human_vs_human")
        ]
        
        for text, value in modes:
            tk.Radiobutton(
                mode_frame, 
                text=text, 
                variable=self.mode_var, 
                value=value,
                command=self.on_mode_change
            ).pack(anchor=tk.W)
        
        # ゲーム操作
        game_frame = tk.LabelFrame(control_frame, text="ゲーム操作")
        game_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(game_frame, text="新しいゲーム", command=self.new_game).pack(pady=2)
        tk.Button(game_frame, text="パス", command=self.pass_move).pack(pady=2)
        tk.Button(game_frame, text="投了", command=self.resign_game).pack(pady=2)
        
        # AI設定
        ai_frame = tk.LabelFrame(control_frame, text="AI設定")
        ai_frame.pack(side=tk.LEFT)
        
        tk.Label(ai_frame, text="思考時間:").pack()
        self.thinking_time = tk.Scale(
            ai_frame, 
            from_=1, to=10, 
            orient=tk.HORIZONTAL, 
            length=100
        )
        self.thinking_time.set(3)
        self.thinking_time.pack()
        
        tk.Label(ai_frame, text="MCTS回数:").pack()
        self.mcts_simulations = tk.Scale(
            ai_frame, 
            from_=50, to=500, 
            orient=tk.HORIZONTAL, 
            length=100
        )
        self.mcts_simulations.set(200)
        self.mcts_simulations.pack()
        
    def setup_info_panel(self, parent):
        """下部情報パネルの設定"""
        info_frame = tk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 現在の状態表示
        self.status_label = tk.Label(
            info_frame, 
            text="黒の番です",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack()
        
        # スコア表示
        score_frame = tk.Frame(info_frame)
        score_frame.pack(pady=5)
        
        tk.Label(score_frame, text="捕獲した石:").pack(side=tk.LEFT)
        self.score_label = tk.Label(
            score_frame, 
            text="黒: 0, 白: 0",
            font=("Arial", 10)
        )
        self.score_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 進行状況バー（AI思考中用）
        self.progress_frame = tk.Frame(info_frame)
        self.progress_label = tk.Label(self.progress_frame, text="AI思考中...")
        self.progress_label.pack()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='indeterminate', 
            length=200
        )
        self.progress_bar.pack(pady=5)
        
    def setup_board(self):
        """盤面の描画"""
        self.canvas.delete("all")
        
        # 格子線の描画
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            y = self.margin + i * self.cell_size
            
            # 縦線
            self.canvas.create_line(
                x, self.margin, 
                x, self.margin + (self.board_size - 1) * self.cell_size,
                fill='black', width=1
            )
            
            # 横線
            self.canvas.create_line(
                self.margin, y,
                self.margin + (self.board_size - 1) * self.cell_size, y,
                fill='black', width=1
            )
        
        # 星の位置（9x9盤面の場合）
        if self.board_size == 9:
            star_positions = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
            for sx, sy in star_positions:
                x = self.margin + sx * self.cell_size
                y = self.margin + sy * self.cell_size
                self.canvas.create_oval(
                    x-3, y-3, x+3, y+3,
                    fill='black'
                )
        
        # 座標ラベル（オプション）
        self.draw_coordinates()
        
        # 石の描画
        self.draw_stones()
        
    def draw_coordinates(self):
        """座標ラベルの描画"""
        # 列ラベル（A-I）
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            label = chr(ord('A') + i)
            self.canvas.create_text(
                x, self.margin - 15,
                text=label, font=("Arial", 10)
            )
            self.canvas.create_text(
                x, self.margin + (self.board_size - 1) * self.cell_size + 15,
                text=label, font=("Arial", 10)
            )
        
        # 行ラベル（1-9）
        for i in range(self.board_size):
            y = self.margin + i * self.cell_size
            label = str(self.board_size - i)
            self.canvas.create_text(
                self.margin - 15, y,
                text=label, font=("Arial", 10)
            )
            self.canvas.create_text(
                self.margin + (self.board_size - 1) * self.cell_size + 15, y,
                text=label, font=("Arial", 10)
            )
    
    def draw_stones(self):
        """石の描画"""
        # 既存の石を削除
        self.canvas.delete("stone")
        self.canvas.delete("last_move")
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.game.board.board[i, j]
                if stone != 0:
                    x = self.margin + j * self.cell_size
                    y = self.margin + i * self.cell_size
                    
                    # 石の色
                    color = 'black' if stone == 1 else 'white'
                    outline_color = 'white' if stone == 1 else 'black'
                    
                    # 石の描画
                    self.canvas.create_oval(
                        x - self.stone_radius, y - self.stone_radius,
                        x + self.stone_radius, y + self.stone_radius,
                        fill=color, outline=outline_color, width=2,
                        tags="stone"
                    )
        
        # 最後の手をハイライト
        if hasattr(self.game, 'last_move') and self.game.last_move:
            lx, ly = self.game.last_move
            x = self.margin + ly * self.cell_size
            y = self.margin + lx * self.cell_size
            self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                outline='red', width=3,
                tags="last_move"
            )
    
    def on_canvas_click(self, event):
        """キャンバスクリック時の処理"""
        if self.ai_thinking:
            return
            
        # クリック位置を盤面座標に変換
        board_x, board_y = self.pixel_to_board(event.x, event.y)
        
        if board_x is None or board_y is None:
            return
            
        # 人間の手番チェック
        if self.game_mode == "human_vs_ai":
            is_human_turn = (
                (self.game.current_player == 1 and self.human_is_black) or
                (self.game.current_player == -1 and not self.human_is_black)
            )
            if not is_human_turn:
                return
        
        # 手を試行
        if self.make_move(board_x, board_y):
            self.update_display()
            
            # AI vs AI または AI の手番の場合
            if self.game_mode == "ai_vs_ai" or (
                self.game_mode == "human_vs_ai" and not self.ai_thinking
            ):
                self.root.after(500, self.ai_move)  # 少し遅延してAIの手
    
    def pixel_to_board(self, px, py):
        """画面座標を盤面座標に変換"""
        # 最も近い交点を求める
        board_x = round((py - self.margin) / self.cell_size)
        board_y = round((px - self.margin) / self.cell_size)
        
        # 盤面の範囲内かチェック
        if 0 <= board_x < self.board_size and 0 <= board_y < self.board_size:
            return board_x, board_y
        return None, None
    
    def on_mouse_move(self, event):
        """マウス移動時の処理（プレビュー表示）"""
        if self.ai_thinking:
            return
            
        # 既存のプレビューを削除
        self.canvas.delete("preview")
        
        # プレビュー石の描画
        board_x, board_y = self.pixel_to_board(event.x, event.y)
        if board_x is not None and board_y is not None:
            if self.game.is_legal_move(board_x, board_y, self.game.current_player):
                x = self.margin + board_y * self.cell_size
                y = self.margin + board_x * self.cell_size
                
                color = 'gray' if self.game.current_player == 1 else 'lightgray'
                self.canvas.create_oval(
                    x - self.stone_radius, y - self.stone_radius,
                    x + self.stone_radius, y + self.stone_radius,
                    fill=color, outline='gray', width=1,
                    tags="preview"
                )
    
    def make_move(self, x, y):
        """手を実行"""
        success = self.game.make_move((x, y))
        if success:
            self.game.last_move = (x, y)  # 最後の手を記録
        return success
    
    def pass_move(self):
        """パス"""
        if self.ai_thinking:
            return
            
        success = self.game.make_move(None)
        if success:
            self.game.last_move = None
            self.update_display()
            
            if self.game_mode == "human_vs_ai":
                self.root.after(500, self.ai_move)
    
    def ai_move(self):
        """AIの手"""
        if self.ai_thinking or not self.ai_player:
            return
            
        self.ai_thinking = True
        self.progress_frame.pack(pady=5)
        self.progress_bar.start()
        
        def ai_think():
            try:
                # AIの手を取得
                move = self.ai_player.get_move(self.game)
                
                # UIスレッドで手を実行
                self.root.after(0, lambda: self.execute_ai_move(move))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_ai_error(str(e)))
        
        # 別スレッドでAI思考
        threading.Thread(target=ai_think, daemon=True).start()
    
    def execute_ai_move(self, move):
        """AIの手を実行（UIスレッド）"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.ai_thinking = False
        
        if move:
            success = self.make_move(move[0], move[1])
            self.game.last_move = move
        else:
            success = self.game.make_move(None)
            self.game.last_move = None
        
        if success:
            self.update_display()
            
            # AI vs AI の場合は次のAIの手
            if self.game_mode == "ai_vs_ai" and not self.game.game_over:
                self.root.after(1000, self.ai_move)
    
    def handle_ai_error(self, error_msg):
        """AIエラーの処理"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.ai_thinking = False
        messagebox.showerror("AIエラー", f"AIの思考中にエラーが発生しました:\n{error_msg}")
    
    def update_display(self):
        """表示の更新"""
        self.draw_stones()
        self.update_status()
        
        # ゲーム終了チェック
        if self.game.game_over:
            self.show_game_result()
    
    def update_status(self):
        """ステータス表示の更新"""
        if self.game.game_over:
            self.status_label.config(text="ゲーム終了")
        else:
            current_player = "黒" if self.game.current_player == 1 else "白"
            self.status_label.config(text=f"{current_player}の番です")
        
        # スコア更新
        black_captured = self.game.captured_stones.get(1, 0)
        white_captured = self.game.captured_stones.get(-1, 0)
        self.score_label.config(text=f"黒: {black_captured}, 白: {white_captured}")
    
    def show_game_result(self):
        """ゲーム結果の表示"""
        # 簡易スコアリング
        board = self.game.board.board
        black_stones = (board == 1).sum()
        white_stones = (board == -1).sum()
        
        if black_stones > white_stones:
            result = "黒の勝利！"
        elif white_stones > black_stones:
            result = "白の勝利！"
        else:
            result = "引き分け！"
        
        messagebox.showinfo(
            "ゲーム終了", 
            f"{result}\n\n黒石: {black_stones}\n白石: {white_stones}"
        )
    
    def new_game(self):
        """新しいゲーム"""
        self.game = Game(self.board_size)
        self.ai_thinking = False
        self.setup_board()
        self.update_status()
        
        # AI vs AI の場合は自動開始
        if self.game_mode == "ai_vs_ai":
            self.root.after(1000, self.ai_move)
    
    def resign_game(self):
        """投了"""
        if messagebox.askyesno("確認", "投了しますか？"):
            self.game.game_over = True
            current_player = "黒" if self.game.current_player == 1 else "白"
            messagebox.showinfo("投了", f"{current_player}が投了しました")
    
    def on_mode_change(self):
        """ゲームモード変更"""
        self.game_mode = self.mode_var.get()
        self.new_game()
    
    def load_ai_model(self):
        """AIモデルの読み込み"""
        model_path = "trained_models/final_model.pt"
        
        try:
            if os.path.exists(model_path):
                network = ImprovedGoNeuralNetwork(board_size=self.board_size)
                checkpoint = torch.load(model_path, map_location='cpu')
                network.load_state_dict(checkpoint['model_state_dict'])
                self.ai_player = MCTSPlayer(
                    network, 
                    num_simulations=self.mcts_simulations.get()
                )
                print("✅ AIモデルを読み込みました")
            else:
                self.ai_player = MCTSPlayer(None, num_simulations=100)
                print("⚠️ ランダムAIを使用します")
        except Exception as e:
            self.ai_player = MCTSPlayer(None, num_simulations=100)
            print(f"⚠️ モデル読み込みエラー: {e}")
    
    def run(self):
        """GUIの実行"""
        self.root.mainloop()


def main():
    """メイン実行関数"""
    print("🎮 囲碁AI GUI を起動しています...")
    
    try:
        app = GoGUI(board_size=9)
        app.run()
    except KeyboardInterrupt:
        print("\n👋 ゲームを終了します")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
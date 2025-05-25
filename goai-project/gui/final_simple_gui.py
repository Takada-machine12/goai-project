# gui/final_simple_gui.py - 最終版シンプル囲碁GUI
import tkinter as tk
from tkinter import messagebox
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from go_engine.game import Game
    from go_engine.board import BLACK, WHITE, EMPTY
    print("✅ ゲームエンジン読み込み成功")
except ImportError as e:
    print(f"❌ ゲームエンジン読み込みエラー: {e}")
    sys.exit(1)

class FinalSimpleGoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("囲碁AI - 最終版")
        self.root.geometry("800x700")
        self.root.configure(bg='#2c3e50')
        
        # 設定
        self.board_size = 9
        
        # ゲーム初期化
        self.game = Game(self.board_size)
        if not hasattr(self.game, 'captured_stones'):
            self.game.captured_stones = {1: 0, -1: 0}
        
        # ボタン配列
        self.buttons = []
        
        self.setup_gui()
        self.create_simple_board()
        
    def setup_gui(self):
        """GUI設定"""
        # タイトル
        title_label = tk.Label(
            self.root,
            text="🎮 囲碁AI - 最終版",
            font=('Arial', 24, 'bold'),
            fg='white', bg='#2c3e50'
        )
        title_label.pack(pady=15)
        
        # ゲーム情報フレーム
        info_frame = tk.Frame(self.root, bg='#34495e', bd=3, relief=tk.RAISED)
        info_frame.pack(pady=10)
        
        # 現在のプレイヤー表示
        self.status_label = tk.Label(
            info_frame,
            text="現在: 黒の番",
            font=('Arial', 18, 'bold'),
            fg='white', bg='#34495e'
        )
        self.status_label.pack(pady=10, padx=20)
        
        # 手数表示
        self.move_label = tk.Label(
            info_frame,
            text="手数: 0",
            font=('Arial', 14),
            fg='white', bg='#34495e'
        )
        self.move_label.pack(pady=5)
        
        # ボタン操作パネル
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=15)
        
        tk.Button(
            button_frame, text="新しいゲーム",
            command=self.new_game,
            font=('Arial', 14, 'bold'), width=12, height=2,
            bg='#3498db', fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame, text="パス",
            command=self.pass_move,
            font=('Arial', 14, 'bold'), width=8, height=2,
            bg='#f39c12', fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame, text="終了",
            command=self.root.quit,
            font=('Arial', 14, 'bold'), width=8, height=2,
            bg='#e74c3c', fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
    def create_simple_board(self):
        """シンプルで確実な盤面を作成"""
        # 盤面フレーム
        board_container = tk.Frame(self.root, bg='#8B4513', bd=8, relief=tk.RAISED)
        board_container.pack(pady=20)
        
        # 盤面グリッド
        board_frame = tk.Frame(board_container, bg='#DEB887', bd=2)
        board_frame.pack(padx=15, pady=15)
        
        # ボタン配列を作成
        self.buttons = []
        for i in range(self.board_size):
            row = []
            for j in range(self.board_size):
                btn = tk.Button(
                    board_frame,
                    text="",
                    width=4,
                    height=2,
                    font=('Arial', 16, 'bold'),
                    bg='#DEB887',
                    activebackground='#F5DEB3',
                    relief=tk.FLAT,
                    bd=1,
                    command=lambda r=i, c=j: self.on_button_click(r, c)
                )
                btn.grid(row=i, column=j, padx=1, pady=1)
                row.append(btn)
            self.buttons.append(row)
        
        # 星の位置をマーク
        if self.board_size == 9:
            star_positions = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
            for x, y in star_positions:
                self.buttons[x][y].config(text="✦", fg='#8B4513')
        
        self.update_board_display()
        
    def on_button_click(self, row, col):
        """ボタンクリック処理"""
        print(f"ボタンクリック: ({row}, {col}) - 現在のプレイヤー: {self.game.current_player}")
        
        try:
            if self.game.is_legal_move(row, col):
                # 現在のプレイヤーを保存
                current_player = self.game.current_player
                
                success = self.game.make_move((row, col))
                if success:
                    print(f"手の実行成功: ({row}, {col}) - プレイヤー: {current_player}")
                    self.update_board_display()
                else:
                    messagebox.showwarning("無効な手", "その位置には打てません")
            else:
                messagebox.showwarning("無効な手", "その位置には打てません")
        except Exception as e:
            print(f"エラー: {e}")
            messagebox.showerror("エラー", f"手の実行でエラー: {e}")
            
    def update_board_display(self):
        """盤面表示更新"""
        print("盤面表示更新中...")
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.game.board.get_color(i, j)
                btn = self.buttons[i][j]
                
                print(f"位置({i},{j}): 石の色={stone}")
                
                if stone == BLACK:  # 黒石 (1)
                    btn.config(
                        text="●", 
                        fg='#000000',  # 黒色
                        bg='#DEB887', 
                        font=('Arial', 24, 'bold'),
                        relief=tk.RAISED,
                        bd=2
                    )
                    print(f"黒石配置: ({i},{j})")
                    
                elif stone == WHITE:  # 白石 (-1)
                    btn.config(
                        text="●", 
                        fg='#FFFFFF',  # 白色
                        bg='#000000',  # 背景を黒にして白石を見やすく
                        font=('Arial', 24, 'bold'),
                        relief=tk.RAISED,
                        bd=2
                    )
                    print(f"白石配置: ({i},{j})")
                    
                else:  # 空の場所 (0)
                    # 星の位置チェック
                    if self.board_size == 9 and (i, j) in [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]:
                        btn.config(
                            text="✦", 
                            fg='#8B4513', 
                            bg='#DEB887',
                            font=('Arial', 12),
                            relief=tk.FLAT,
                            bd=1
                        )
                    else:
                        btn.config(
                            text="", 
                            fg='#8B4513', 
                            bg='#DEB887',
                            font=('Arial', 12),
                            relief=tk.FLAT,
                            bd=1
                        )
        
        self.update_status()
        
    def update_status(self):
        """ステータス更新"""
        if self.game.game_over:
            self.status_label.config(text="ゲーム終了", fg='#e74c3c')
        else:
            current = "黒" if self.game.current_player == BLACK else "白"
            color = "#000000" if self.game.current_player == BLACK else "#FFFFFF"
            self.status_label.config(text=f"現在: {current}の番", fg=color)
        
        move_count = len(self.game.move_history)
        self.move_label.config(text=f"手数: {move_count}")
        
        if self.game.game_over:
            self.show_game_end()
            
    def pass_move(self):
        """パス"""
        print(f"パス実行 - 現在のプレイヤー: {self.game.current_player}")
        success = self.game.make_move(None)
        if success:
            self.update_board_display()
            
    def new_game(self):
        """新しいゲーム"""
        print("新しいゲーム開始...")
        self.game = Game(self.board_size)
        if not hasattr(self.game, 'captured_stones'):
            self.game.captured_stones = {1: 0, -1: 0}
        self.update_board_display()
        
    def show_game_end(self):
        """ゲーム終了"""
        # 簡易的な勝敗判定
        board = self.game.board.board
        black_count = (board == BLACK).sum()
        white_count = (board == WHITE).sum()
        
        if black_count > white_count:
            winner = "黒の勝利！"
        elif white_count > black_count:
            winner = "白の勝利！"
        else:
            winner = "引き分け！"
            
        messagebox.showinfo("ゲーム終了", 
                           f"{winner}\n\n黒石: {black_count}\n白石: {white_count}\n手数: {len(self.game.move_history)}")
        
    def run(self):
        """実行"""
        print("🎮 最終版GUI起動完了")
        self.root.mainloop()

def main():
    print("=== 最終版 囲碁AI ===")
    
    try:
        app = FinalSimpleGoGUI()
        app.run()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

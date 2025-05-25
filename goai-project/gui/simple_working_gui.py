# gui/simple_working_gui.py - 確実に動作する簡易GUI
import tkinter as tk
from tkinter import messagebox
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 安全なインポート
try:
    from go_engine.game import Game
    from go_engine.board import BLACK, WHITE, EMPTY
    print("✅ ゲームエンジン読み込み成功")
except ImportError as e:
    print(f"❌ ゲームエンジン読み込みエラー: {e}")
    sys.exit(1)

class SimpleWorkingGUI:
    def __init__(self):
        # まずrootウィンドウを作成
        self.root = tk.Tk()
        self.root.title("囲碁AI - 動作確認版")
        self.root.geometry("700x600")
        self.root.configure(bg='#34495e')
        
        # 設定
        self.board_size = 9
        self.cell_size = 40
        self.margin = 30
        self.stone_radius = 15
        
        # ゲーム初期化
        self.game = Game(self.board_size)
        
        # captured_stonesがない場合は追加
        if not hasattr(self.game, 'captured_stones'):
            self.game.captured_stones = {1: 0, -1: 0}
        
        self.setup_gui()
        
        # Mac対応：GUI表示後に盤面描画をスケジュール
        self.root.after(500, self.initial_board_setup)
        self.draw_board()
        
    def setup_gui(self):
        """GUI設定"""
        # メインフレーム
        main_frame = tk.Frame(self.root, bg='#34495e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上部：コントロールパネル
        control_frame = tk.Frame(main_frame, bg='#2c3e50', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # タイトル
        title_label = tk.Label(
            control_frame, 
            text="🎮 囲碁AI - 動作確認版", 
            font=('Arial', 16, 'bold'),
            fg='white', bg='#2c3e50'
        )
        title_label.pack(pady=10)
        
        # ボタンフレーム
        button_frame = tk.Frame(control_frame, bg='#2c3e50')
        button_frame.pack(pady=5)
        
        # ボタン
        tk.Button(
            button_frame, text="新しいゲーム", 
            command=self.new_game,
            font=('Arial', 12), width=12, height=2,
            bg='#3498db', fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="パス", 
            command=self.pass_move,
            font=('Arial', 12), width=8, height=2,
            bg='#f39c12', fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="テスト", 
            command=self.test_button,
            font=('Arial', 12), width=8, height=2,
            bg='#2ecc71', fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="終了", 
            command=self.root.quit,
            font=('Arial', 12), width=8, height=2,
            bg='#e74c3c', fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        # 中央：盤面フレーム
        board_frame = tk.Frame(main_frame, bg='#8b4513', relief=tk.RAISED, bd=3)
        board_frame.pack(expand=True, pady=5)
        
        # キャンバス
        canvas_size = self.board_size * self.cell_size + 2 * self.margin
        self.canvas = tk.Canvas(
            board_frame,
            width=canvas_size,
            height=canvas_size,
            bg='#f5deb3',  # より明るいベージュ
            highlightthickness=2,
            highlightbackground='#000000'  # 黒い枠
        )
        # キャンバスを描画後に盤面を描画
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        
        # キャンバスが実際に表示されるまで待機してから盤面描画
        self.root.after(100, self.draw_board)
        
        # 下部：情報パネル
        info_frame = tk.Frame(main_frame, bg='#2c3e50', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 現在のプレイヤー
        self.current_player_label = tk.Label(
            info_frame,
            text="現在: 黒の番",
            font=('Arial', 14, 'bold'),
            fg='white', bg='#2c3e50'
        )
        self.current_player_label.pack(pady=5)
        
        # 手数と捕獲情報
        info_details = tk.Frame(info_frame, bg='#2c3e50')
        info_details.pack(pady=5)
        
        self.move_count_label = tk.Label(
            info_details,
            text="手数: 0",
            font=('Arial', 12),
            fg='white', bg='#2c3e50'
        )
        self.move_count_label.pack(side=tk.LEFT, padx=10)
        
        self.captured_label = tk.Label(
            info_details,
            text="捕獲 - 黒:0 白:0",
            font=('Arial', 12),
            fg='white', bg='#2c3e50'
        )
        self.captured_label.pack(side=tk.LEFT, padx=10)
        
    def force_canvas_resize(self, target_size):
        """キャンバスサイズを強制的に設定"""
        print(f"キャンバスサイズを強制設定: {target_size}")
        
        # 複数の方法でサイズを設定
        self.canvas.config(width=target_size, height=target_size)
        self.canvas.configure(width=target_size, height=target_size)
        
        # 強制更新
        self.canvas.update_idletasks()
        self.canvas.update()
        
        # 再確認
        actual_width = self.canvas.winfo_width()
        actual_height = self.canvas.winfo_height()
        print(f"強制設定後のサイズ: {actual_width} x {actual_height}")
        
        # 盤面を描画
        self.draw_board()
        
    def draw_board(self):
        """盤面描画"""
        print("盤面描画開始...")
        
        # キャンバスサイズを再確認
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            print(f"描画時のキャンバスサイズ: {canvas_width} x {canvas_height}")
            
            # サイズが不正な場合は再試行
            if canvas_width <= 1 or canvas_height <= 1:
                print("キャンバスサイズが不正、再試行します...")
                expected_size = self.board_size * self.cell_size + 2 * self.margin
                self.root.after(300, lambda: self.force_canvas_resize(expected_size))
                return
        except:
            print("キャンバスサイズの取得に失敗")
            return
        
        self.canvas.delete("all")
        
        # 背景を描画（Mac対応）
        self.canvas.create_rectangle(
            5, 5, canvas_width-5, canvas_height-5,
            fill='#f5deb3', outline='#000000', width=3,
            tags="background"
        )
        
        # 格子線 - より確実な描画
        print("格子線描画中...")
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            y = self.margin + i * self.cell_size
            
            # 縦線
            line1 = self.canvas.create_line(
                x, self.margin,
                x, self.margin + (self.board_size - 1) * self.cell_size,
                fill='#000000', width=2, tags="grid"
            )
            
            # 横線
            line2 = self.canvas.create_line(
                self.margin, y,
                self.margin + (self.board_size - 1) * self.cell_size, y,
                fill='#000000', width=2, tags="grid"
            )
            
            if i == 0:  # 最初の線のみログ出力
                print(f"線描画成功: 縦線{line1}, 横線{line2}")
        
        # 星の位置
        if self.board_size == 9:
            star_positions = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
            for sx, sy in star_positions:
                x = self.margin + sy * self.cell_size
                y = self.margin + sx * self.cell_size
                star = self.canvas.create_oval(
                    x-4, y-4, x+4, y+4,
                    fill='#000000', outline='#000000', tags="star"
                )
                if sx == 4 and sy == 4:  # 天元のみログ出力
                    print(f"天元描画: {star} at ({x}, {y})")
        
        # 強制的に描画を反映
        self.canvas.update_idletasks()
        self.canvas.update()
        
        # 石の描画
    def initial_board_setup(self):
        """初期盤面のセットアップ（Mac対応）"""
        print("初期盤面セットアップ開始...")
        expected_size = self.board_size * self.cell_size + 2 * self.margin
        self.force_canvas_resize(expected_size)
        
    def draw_stones(self):
        """石の描画"""
        self.canvas.delete("stone")
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.game.board.get_color(i, j)
                if stone != EMPTY:
                    x = self.margin + j * self.cell_size
                    y = self.margin + i * self.cell_size
                    
                    # 石の色 - よりコントラストの高い色
                    fill_color = '#000000' if stone == BLACK else '#ffffff'
                    outline_color = '#ffffff' if stone == BLACK else '#000000'
                    
                    self.canvas.create_oval(
                        x - self.stone_radius, y - self.stone_radius,
                        x + self.stone_radius, y + self.stone_radius,
                        fill=fill_color, outline=outline_color, width=3,
                        tags="stone"
                    )
                    print(f"石描画: {fill_color} at ({x}, {y})")
        
        self.update_info()
        
    def on_click(self, event):
        """クリック処理"""
        try:
            # デバッグ：クリック座標を表示
            print(f"クリック座標: x={event.x}, y={event.y}")
            
            # 座標変換
            board_x = round((event.y - self.margin) / self.cell_size)
            board_y = round((event.x - self.margin) / self.cell_size)
            
            print(f"盤面座標: board_x={board_x}, board_y={board_y}")
            
            # 範囲チェック
            if 0 <= board_x < self.board_size and 0 <= board_y < self.board_size:
                print(f"座標チェックOK、合法手判定中...")
                
                # 合法手チェック
                try:
                    is_legal = self.game.is_legal_move(board_x, board_y)
                    print(f"合法手判定: {is_legal}")
                    
                    if is_legal:
                        success = self.game.make_move((board_x, board_y))
                        print(f"手の実行結果: {success}")
                        
                        if success:
                            print("石を配置、画面更新中...")
                            self.draw_stones()
                        else:
                            messagebox.showwarning("無効な手", "その位置には打てません")
                    else:
                        messagebox.showwarning("無効な手", "その位置には打てません")
                        
                except Exception as e:
                    print(f"合法手判定エラー: {e}")
                    messagebox.showerror("エラー", f"手の判定でエラー: {e}")
            else:
                print(f"座標が範囲外: {board_x}, {board_y}")
                
        except Exception as e:
            print(f"クリック処理エラー: {e}")
            messagebox.showerror("エラー", f"クリック処理でエラー: {e}")
        
    def pass_move(self):
        """パス"""
        success = self.game.make_move(None)
        if success:
            self.update_info()
            
            if self.game.game_over:
                self.show_game_end()
                
    def new_game(self):
        """新しいゲーム"""
        print("新しいゲーム開始...")
        self.game = Game(self.board_size)
        if not hasattr(self.game, 'captured_stones'):
            self.game.captured_stones = {1: 0, -1: 0}
        print("ゲーム初期化完了、盤面再描画中...")
        self.draw_board()
        print("新しいゲーム完了")
        
    def test_button(self):
        """テストボタン（ボタン動作確認用）"""
        print("テストボタンがクリックされました！")
        messagebox.showinfo("テスト", "ボタンは正常に動作しています！")
        
    def update_info(self):
        """情報更新"""
        # 現在のプレイヤー
        current = "黒" if self.game.current_player == BLACK else "白"
        if self.game.game_over:
            self.current_player_label.config(text="ゲーム終了")
        else:
            self.current_player_label.config(text=f"現在: {current}の番")
        
        # 手数
        move_count = len(self.game.move_history)
        self.move_count_label.config(text=f"手数: {move_count}")
        
        # 捕獲情報
        black_captured = self.game.captured_stones.get(BLACK, 0)
        white_captured = self.game.captured_stones.get(WHITE, 0)
        self.captured_label.config(text=f"捕獲 - 黒:{black_captured} 白:{white_captured}")
        
    def show_game_end(self):
        """ゲーム終了"""
        messagebox.showinfo("ゲーム終了", "2回連続パスでゲーム終了です")
        
    def run(self):
        """実行"""
        print("🎮 GUI起動完了")
        self.root.mainloop()

def main():
    print("=== 囲碁AI 動作確認版 ===")
    
    try:
        app = SimpleWorkingGUI()
        app.run()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
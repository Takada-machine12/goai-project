# gui/mac_simple_gui.py - Mac対応の超シンプル囲碁GUI
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


class MacSimpleGoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("囲碁AI - Mac対応版")
        self.root.geometry("800x700")
        self.root.configure(bg="white")

        # 設定
        self.board_size = 9
        self.cell_size = 50  # より大きく
        self.margin = 50  # より大きく

        # ゲーム初期化
        self.game = Game(self.board_size)
        if not hasattr(self.game, "captured_stones"):
            self.game.captured_stones = {1: 0, -1: 0}

        # ボタン配列で盤面を表現（確実に見える方法）
        self.buttons = []

        self.setup_gui()
        self.create_button_board()

    def setup_gui(self):
        """GUI設定"""
        # タイトル
        title_label = tk.Label(
            self.root,
            text="🎮 囲碁AI - Mac対応版",
            font=("Arial", 20, "bold"),
            bg="white",
        )
        title_label.pack(pady=10)

        # 現在のプレイヤー表示
        self.status_label = tk.Label(
            self.root, text="現在: 黒の番", font=("Arial", 16, "bold"), bg="white"
        )
        self.status_label.pack(pady=5)

        # 手数表示
        self.move_label = tk.Label(
            self.root, text="手数: 0", font=("Arial", 14), bg="white"
        )
        self.move_label.pack(pady=5)

        # ボタン操作パネル
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="新しいゲーム",
            command=self.new_game,
            font=("Arial", 12),
            width=12,
            height=2,
            bg="#3498db",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="パス",
            command=self.pass_move,
            font=("Arial", 12),
            width=8,
            height=2,
            bg="#f39c12",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="終了",
            command=self.root.quit,
            font=("Arial", 12),
            width=8,
            height=2,
            bg="#e74c3c",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)

    def create_button_board(self):
        """本格的な囲碁盤面を作成"""
        # 盤面全体のフレーム - 木目調
        board_container = tk.Frame(self.root, bg="#8B4513", bd=10, relief=tk.RAISED)
        board_container.pack(pady=20)

        # 座標ラベル用のフレーム
        coord_frame = tk.Frame(board_container, bg="#8B4513")
        coord_frame.pack(padx=10, pady=10)

        # 列ラベル（上）
        top_labels = tk.Frame(coord_frame, bg="#8B4513")
        top_labels.grid(row=0, column=1, sticky="ew")

        labels = "ABCDEFGHJKLMNOPQRS"  # Iを除く囲碁式
        for j in range(self.board_size):
            tk.Label(
                top_labels,
                text=labels[j],
                bg="#8B4513",
                fg="white",
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=j, padx=12)

        # 左側の行ラベル
        left_labels = tk.Frame(coord_frame, bg="#8B4513")
        left_labels.grid(row=1, column=0, sticky="ns")

        for i in range(self.board_size):
            tk.Label(
                left_labels,
                text=str(self.board_size - i),
                bg="#8B4513",
                fg="white",
                font=("Arial", 10, "bold"),
            ).grid(row=i, column=0, pady=8)

        # 盤面フレーム - 真ん中
        board_frame = tk.Frame(coord_frame, bg="#DEB887", bd=2, relief=tk.SUNKEN)
        board_frame.grid(row=1, column=1)

        # 右側の行ラベル
        right_labels = tk.Frame(coord_frame, bg="#8B4513")
        right_labels.grid(row=1, column=2, sticky="ns")

        for i in range(self.board_size):
            tk.Label(
                right_labels,
                text=str(self.board_size - i),
                bg="#8B4513",
                fg="white",
                font=("Arial", 10, "bold"),
            ).grid(row=i, column=0, pady=8)

        # 列ラベル（下）
        bottom_labels = tk.Frame(coord_frame, bg="#8B4513")
        bottom_labels.grid(row=2, column=1, sticky="ew")

        for j in range(self.board_size):
            tk.Label(
                bottom_labels,
                text=labels[j],
                bg="#8B4513",
                fg="white",
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=j, padx=12)

        # ボタン配列を作成 - より小さく、囲碁らしく
        self.buttons = []
        for i in range(self.board_size):
            row = []
            for j in range(self.board_size):
                # 各交点をボタンで表現
                btn = tk.Button(
                    board_frame,
                    text="",
                    width=3,
                    height=1,
                    font=("Arial", 14, "bold"),
                    bg="#DEB887",  # 木目調
                    activebackground="#F5DEB3",
                    relief=tk.FLAT,
                    bd=0,
                    highlightthickness=0,
                    command=lambda r=i, c=j: self.on_button_click(r, c),
                )
                btn.grid(row=i, column=j, padx=0, pady=0)
                row.append(btn)
            self.buttons.append(row)

        # 星の位置をマーク
        if self.board_size == 9:
            star_positions = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
            for x, y in star_positions:
                self.buttons[x][y].config(text="⚫", fg="#654321", font=("Arial", 8))

        self.update_board_display()

    def on_button_click(self, row, col):
        """ボタンクリック処理"""
        print(f"ボタンクリック: ({row}, {col})")

        try:
            if self.game.is_legal_move(row, col):
                success = self.game.make_move((row, col))
                if success:
                    print(f"手の実行成功: ({row}, {col})")
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

                if stone == BLACK:
                    # 黒石 - 本物の囲碁石らしく
                    btn.config(
                        text="●",
                        fg="#000000",
                        bg="#DEB887",
                        font=("Arial", 18, "bold"),
                        relief=tk.RAISED,
                        bd=2,
                    )
                elif stone == WHITE:
                    # 白石 - 本物の囲碁石らしく
                    btn.config(
                        text="●",
                        fg="#FFFFFF",
                        bg="#DEB887",
                        font=("Arial", 18, "bold"),
                        relief=tk.RAISED,
                        bd=2,
                    )
                else:
                    # 空の場所
                    if self.board_size == 9 and (i, j) in [
                        (2, 2),
                        (2, 6),
                        (6, 2),
                        (6, 6),
                        (4, 4),
                    ]:
                        # 星の位置 - 小さな黒点
                        btn.config(
                            text="⚫",
                            fg="#654321",
                            bg="#DEB887",
                            font=("Arial", 8),
                            relief=tk.FLAT,
                            bd=0,
                        )
                    else:
                        # 空の交点 - 線を表現
                        # 端の処理
                        if i == 0:  # 上端
                            if j == 0:  # 左上角
                                text = "┌"
                            elif j == self.board_size - 1:  # 右上角
                                text = "┐"
                            else:  # 上辺
                                text = "┬"
                        elif i == self.board_size - 1:  # 下端
                            if j == 0:  # 左下角
                                text = "└"
                            elif j == self.board_size - 1:  # 右下角
                                text = "┘"
                            else:  # 下辺
                                text = "┴"
                        elif j == 0:  # 左辺
                            text = "├"
                        elif j == self.board_size - 1:  # 右辺
                            text = "┤"
                        else:  # 内部
                            text = "┼"

                        btn.config(
                            text=text,
                            fg="#654321",
                            bg="#DEB887",
                            font=("Arial", 12),
                            relief=tk.FLAT,
                            bd=0,
                        )

        self.update_status()

    def update_status(self):
        """ステータス更新"""
        current = "黒" if self.game.current_player == BLACK else "白"
        if self.game.game_over:
            self.status_label.config(text="ゲーム終了")
        else:
            self.status_label.config(text=f"現在: {current}の番")

        move_count = len(self.game.move_history)
        self.move_label.config(text=f"手数: {move_count}")

        if self.game.game_over:
            self.show_game_end()

    def pass_move(self):
        """パス"""
        print("パス実行...")
        success = self.game.make_move(None)
        if success:
            self.update_board_display()

    def new_game(self):
        """新しいゲーム"""
        print("新しいゲーム開始...")
        self.game = Game(self.board_size)
        if not hasattr(self.game, "captured_stones"):
            self.game.captured_stones = {1: 0, -1: 0}
        self.update_board_display()

    def show_game_end(self):
        """ゲーム終了"""
        messagebox.showinfo("ゲーム終了", "2回連続パスでゲーム終了です")

    def run(self):
        """実行"""
        print("🎮 Mac対応GUI起動完了")
        self.root.mainloop()


def main():
    print("=== Mac対応 囲碁AI ===")

    try:
        app = MacSimpleGoGUI()
        app.run()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

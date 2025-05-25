# gui/advanced_gui.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import time
import os
import sys
import json
import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from go_engine.game import Game
from ai.network import ImprovedGoNeuralNetwork
from ai.mcts import MCTSPlayer
import torch
import numpy as np

class AdvancedGoGUI:
    def __init__(self, board_size=9):
        self.board_size = board_size
        self.cell_size = 45
        self.margin = 40
        self.stone_radius = 18
        
        # 色設定
        self.colors = {
            'board': '#DEB887',
            'line': '#8B7355',
            'black_stone': '#1C1C1C',
            'white_stone': '#F5F5F5',
            'last_move': '#FF4444',
            'legal_hint': '#90EE90',
            'preview': '#D3D3D3'
        }
        
        # ゲーム状態
        self.game = Game(board_size)
        self.ai_player = None
        self.human_is_black = True
        self.game_mode = "human_vs_ai"
        self.ai_thinking = False
        
        # GUI設定
        self.show_legal_moves = tk.BooleanVar(value=False)
        self.auto_save = tk.BooleanVar(value=True)
        self.show_coordinates = tk.BooleanVar(value=True)
        self.animate_stones = tk.BooleanVar(value=True)
        
        # 履歴管理
        self.game_history = []
        self.current_history_index = -1
        
        # 統計情報
        self.game_start_time = time.time()
        self.ai_move_times = []
        self.total_moves = 0
        
        # GUI初期化
        self.setup_gui()
        self.setup_board()
        self.load_ai_model()
        self.start_game_timer()
        
    def setup_gui(self):
        """拡張GUIの設定"""
        self.root = tk.Tk()
        self.root.title("囲碁AI Pro - Advanced Go Game")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # メニューバー
        self.setup_menubar()
        
        # メインフレーム（PanedWindow使用）
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左パネル（盤面）
        self.setup_board_panel()
        
        # 右パネル（コントロール）
        self.setup_control_panel()
        
        # ステータスバー
        self.setup_statusbar()
        
    def setup_menubar(self):
        """メニューバーの設定"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="新しいゲーム", command=self.new_game, accelerator="Ctrl+N")
        file_menu.add_command(label="ゲームを保存", command=self.save_game, accelerator="Ctrl+S")
        file_menu.add_command(label="ゲームを読み込み", command=self.load_game, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit, accelerator="Ctrl+Q")
        
        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(label="戻る", command=self.undo_move, accelerator="Ctrl+Z")
        edit_menu.add_command(label="進む", command=self.redo_move, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="パス", command=self.pass_move, accelerator="Space")
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        view_menu.add_checkbutton(label="合法手をハイライト", variable=self.show_legal_moves, command=self.update_board_display)
        view_menu.add_checkbutton(label="座標を表示", variable=self.show_coordinates, command=self.setup_board)
        view_menu.add_checkbutton(label="アニメーション", variable=self.animate_stones)
        view_menu.add_checkbutton(label="自動保存", variable=self.auto_save)
        view_menu.add_separator()
        view_menu.add_command(label="設定", command=self.show_settings)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="操作方法", command=self.show_help)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
        
        # キーボードショートカット
        self.root.bind('<Control-n>', lambda e: self.new_game())
        self.root.bind('<Control-s>', lambda e: self.save_game())
        self.root.bind('<Control-o>', lambda e: self.load_game())
        self.root.bind('<Control-z>', lambda e: self.undo_move())
        self.root.bind('<Control-y>', lambda e: self.redo_move())
        self.root.bind('<space>', lambda e: self.pass_move())
        
    def setup_board_panel(self):
        """盤面パネルの設定"""
        board_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(board_frame, weight=2)
        
        # 盤面キャンバス
        canvas_size = self.cell_size * (self.board_size - 1) + 2 * self.margin
        self.canvas = tk.Canvas(
            board_frame,
            width=canvas_size,
            height=canvas_size,
            bg=self.colors['board'],
            highlightthickness=2,
            highlightbackground=self.colors['line']
        )
        self.canvas.pack(expand=True, padx=10, pady=10)
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        
    def setup_control_panel(self):
        """コントロールパネルの設定"""
        control_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(control_frame, weight=1)
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(control_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ゲームタブ
        self.setup_game_tab()
        
        # AIタブ
        self.setup_ai_tab()
        
        # 履歴タブ
        self.setup_history_tab()
        
        # 統計タブ
        self.setup_stats_tab()
        
    def setup_game_tab(self):
        """ゲームタブの設定"""
        game_frame = ttk.Frame(self.notebook)
        self.notebook.add(game_frame, text="ゲーム")
        
        # 現在の状況
        status_group = ttk.LabelFrame(game_frame, text="現在の状況")
        status_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_player_label = ttk.Label(status_group, text="黒の番", font=("Arial", 12, "bold"))
        self.current_player_label.pack(pady=5)
        
        self.captured_label = ttk.Label(status_group, text="捕獲: 黒 0, 白 0")
        self.captured_label.pack()
        
        self.moves_label = ttk.Label(status_group, text="手数: 0")
        self.moves_label.pack()
        
        # ゲームモード
        mode_group = ttk.LabelFrame(game_frame, text="ゲームモード")
        mode_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="human_vs_ai")
        modes = [
            ("人間 vs AI", "human_vs_ai"),
            ("AI vs AI", "ai_vs_ai"),
            ("人間 vs 人間", "human_vs_human")
        ]
        
        for text, value in modes:
            ttk.Radiobutton(
                mode_group,
                text=text,
                variable=self.mode_var,
                value=value,
                command=self.on_mode_change
            ).pack(anchor=tk.W, padx=5)
        
        # 先手後手選択
        color_group = ttk.LabelFrame(game_frame, text="人間の色")
        color_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.color_var = tk.StringVar(value="black")
        ttk.Radiobutton(color_group, text="黒（先手）", variable=self.color_var, value="black", command=self.on_color_change).pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(color_group, text="白（後手）", variable=self.color_var, value="white", command=self.on_color_change).pack(anchor=tk.W, padx=5)
        
        # ゲーム操作
        action_group = ttk.LabelFrame(game_frame, text="操作")
        action_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_group, text="新しいゲーム", command=self.new_game).pack(fill=tk.X, pady=2)
        ttk.Button(action_group, text="パス", command=self.pass_move).pack(fill=tk.X, pady=2)
        ttk.Button(action_group, text="投了", command=self.resign_game).pack(fill=tk.X, pady=2)
        
        # 履歴操作
        history_group = ttk.LabelFrame(game_frame, text="履歴操作")
        history_group.pack(fill=tk.X, padx=5, pady=5)
        
        history_buttons = ttk.Frame(history_group)
        history_buttons.pack(fill=tk.X, pady=2)
        
        ttk.Button(history_buttons, text="戻る", command=self.undo_move).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        ttk.Button(history_buttons, text="進む", command=self.redo_move).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        
    def setup_ai_tab(self):
        """AIタブの設定"""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="AI設定")
        
        # AI強度設定
        strength_group = ttk.LabelFrame(ai_frame, text="AI強度")
        strength_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(strength_group, text="MCTS シミュレーション数:").pack(anchor=tk.W)
        self.mcts_var = tk.IntVar(value=200)
        self.mcts_scale = ttk.Scale(
            strength_group, 
            from_=50, to=1000, 
            variable=self.mcts_var,
            orient=tk.HORIZONTAL
        )
        self.mcts_scale.pack(fill=tk.X, padx=5, pady=2)
        self.mcts_label = ttk.Label(strength_group, text="200")
        self.mcts_label.pack()
        
        self.mcts_var.trace('w', self.update_mcts_label)
        
        # 思考時間制限
        ttk.Label(strength_group, text="思考時間制限 (秒):").pack(anchor=tk.W, pady=(10,0))
        self.thinking_time_var = tk.IntVar(value=5)
        self.thinking_time_scale = ttk.Scale(
            strength_group,
            from_=1, to=30,
            variable=self.thinking_time_var,
            orient=tk.HORIZONTAL
        )
        self.thinking_time_scale.pack(fill=tk.X, padx=5, pady=2)
        self.thinking_time_label = ttk.Label(strength_group, text="5秒")
        self.thinking_time_label.pack()
        
        self.thinking_time_var.trace('w', self.update_thinking_time_label)
        
        # AI情報
        info_group = ttk.LabelFrame(ai_frame, text="AI情報")
        info_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.ai_status_label = ttk.Label(info_group, text="AIモデル: 読み込み中...")
        self.ai_status_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # モデル選択
        model_group = ttk.LabelFrame(ai_frame, text="モデル選択")
        model_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(model_group, text="モデルを選択", command=self.select_ai_model).pack(fill=tk.X, pady=2)
        ttk.Button(model_group, text="モデルを再読み込み", command=self.reload_ai_model).pack(fill=tk.X, pady=2)
        
        # AI思考表示
        thinking_group = ttk.LabelFrame(ai_frame, text="AI思考状況")
        thinking_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.ai_thinking_label = ttk.Label(thinking_group, text="待機中")
        self.ai_thinking_label.pack(padx=5, pady=2)
        
        self.thinking_progress = ttk.Progressbar(thinking_group, mode='indeterminate')
        self.thinking_progress.pack(fill=tk.X, padx=5, pady=2)
        
    def setup_history_tab(self):
        """履歴タブの設定"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="履歴")
        
        # 手順リスト
        moves_group = ttk.LabelFrame(history_frame, text="手順")
        moves_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # スクロールバー付きリストボックス
        list_frame = ttk.Frame(moves_group)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.moves_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.moves_listbox.yview)
        self.moves_listbox.config(yscrollcommand=scrollbar.set)
        
        self.moves_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.moves_listbox.bind('<<ListboxSelect>>', self.on_move_select)
        
        # 履歴操作
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_controls, text="履歴をクリア", command=self.clear_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="SGF保存", command=self.save_sgf).pack(side=tk.LEFT, padx=2)
        
    def setup_stats_tab(self):
        """統計タブの設定"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="統計")
        
        # ゲーム統計
        game_stats_group = ttk.LabelFrame(stats_frame, text="ゲーム統計")
        game_stats_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.total_moves_label = ttk.Label(game_stats_group, text="総手数: 0")
        self.total_moves_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.game_time_label = ttk.Label(game_stats_group, text="経過時間: 00:00")
        self.game_time_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.black_stones_label = ttk.Label(game_stats_group, text="黒石: 0")
        self.black_stones_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.white_stones_label = ttk.Label(game_stats_group, text="白石: 0")
        self.white_stones_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # AI統計
        ai_stats_group = ttk.LabelFrame(stats_frame, text="AI統計")
        ai_stats_group.pack(fill=tk.X, padx=5, pady=5)
        
        self.ai_moves_label = ttk.Label(ai_stats_group, text="AI手数: 0")
        self.ai_moves_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.avg_thinking_time_label = ttk.Label(ai_stats_group, text="平均思考時間: 0.0秒")
        self.avg_thinking_time_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.fastest_move_label = ttk.Label(ai_stats_group, text="最速手: 0.0秒")
        self.fastest_move_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.slowest_move_label = ttk.Label(ai_stats_group, text="最遅手: 0.0秒")
        self.slowest_move_label.pack(anchor=tk.W, padx=5, pady=2)
        
    def setup_statusbar(self):
        """ステータスバーの設定"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.statusbar, text="準備完了")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # 時計表示
        self.clock_label = ttk.Label(self.statusbar, text="")
        self.clock_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # プログレスバー（AI思考中用）
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.statusbar, 
            variable=self.progress_var,
            mode='indeterminate',
            length=200
        )
        
    def setup_board(self):
        """盤面の初期描画"""
        self.canvas.delete("all")
        self.draw_board_background()
        self.draw_grid()
        self.draw_star_points()
        if self.show_coordinates.get():
            self.draw_coordinates()
        self.draw_stones()
        
    def draw_board_background(self):
        """盤面背景の描画"""
        # 木目調の背景
        self.canvas.create_rectangle(
            0, 0, 
            self.canvas.winfo_reqwidth(), 
            self.canvas.winfo_reqheight(),
            fill=self.colors['board'], 
            outline=""
        )
        
    def draw_grid(self):
        """格子線の描画"""
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            y = self.margin + i * self.cell_size
            
            # 縦線
            self.canvas.create_line(
                x, self.margin,
                x, self.margin + (self.board_size - 1) * self.cell_size,
                fill=self.colors['line'], width=1, tags="grid"
            )
            
            # 横線
            self.canvas.create_line(
                self.margin, y,
                self.margin + (self.board_size - 1) * self.cell_size, y,
                fill=self.colors['line'], width=1, tags="grid"
            )
            
    def draw_star_points(self):
        """星の位置の描画"""
        if self.board_size == 9:
            star_positions = [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
        elif self.board_size == 13:
            star_positions = [(3, 3), (3, 9), (9, 3), (9, 9), (6, 6)]
        elif self.board_size == 19:
            star_positions = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
        else:
            star_positions = []
            
        for sx, sy in star_positions:
            x = self.margin + sy * self.cell_size
            y = self.margin + sx * self.cell_size
            self.canvas.create_oval(
                x-3, y-3, x+3, y+3,
                fill=self.colors['line'],
                tags="star"
            )
            
    def draw_coordinates(self):
        """座標ラベルの描画"""
        # 列ラベル（A-S、Iを除く）
        labels = "ABCDEFGHJKLMNOPQRS"
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            label = labels[i]
            
            self.canvas.create_text(
                x, self.margin - 20,
                text=label, font=("Arial", 10), tags="coordinates"
            )
            self.canvas.create_text(
                x, self.margin + (self.board_size - 1) * self.cell_size + 20,
                text=label, font=("Arial", 10), tags="coordinates"
            )
            
        # 行ラベル（1-19）
        for i in range(self.board_size):
            y = self.margin + i * self.cell_size
            label = str(self.board_size - i)
            
            self.canvas.create_text(
                self.margin - 20, y,
                text=label, font=("Arial", 10), tags="coordinates"
            )
            self.canvas.create_text(
                self.margin + (self.board_size - 1) * self.cell_size + 20, y,
                text=label, font=("Arial", 10), tags="coordinates"
            )
            
    def draw_stones(self):
        """石の描画"""
        self.canvas.delete("stone")
        self.canvas.delete("last_move")
        self.canvas.delete("legal_hint")
        
        # 石の描画
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.game.board.board[i, j]
                if stone != 0:
                    self.draw_stone(i, j, stone)
                    
        # 合法手のヒント表示
        if self.show_legal_moves.get():
            self.draw_legal_moves()
            
        # 最後の手のマーク
        if hasattr(self.game, 'last_move') and self.game.last_move:
            lx, ly = self.game.last_move
            self.draw_last_move_marker(lx, ly)
            
    def draw_stone(self, board_x, board_y, color, animate=False):
        """個別の石を描画"""
        x = self.margin + board_y * self.cell_size
        y = self.margin + board_x * self.cell_size
        
        stone_color = self.colors['black_stone'] if color == 1 else self.colors['white_stone']
        outline_color = self.colors['white_stone'] if color == 1 else self.colors['black_stone']
        
        if animate and self.animate_stones.get():
            self.animate_stone_placement(x, y, stone_color, outline_color)
        else:
            self.canvas.create_oval(
                x - self.stone_radius, y - self.stone_radius,
                x + self.stone_radius, y + self.stone_radius,
                fill=stone_color, outline=outline_color, width=2,
                tags="stone"
            )
            
    def animate_stone_placement(self, x, y, fill_color, outline_color):
        """石配置のアニメーション"""
        steps = 8
        max_radius = self.stone_radius
        
        def animate_step(step):
            if step <= steps:
                radius = int(max_radius * step / steps)
                
                self.canvas.delete("animating_stone")
                
                if radius > 0:
                    self.canvas.create_oval(
                        x - radius, y - radius,
                        x + radius, y + radius,
                        fill=fill_color, outline=outline_color, width=2,
                        tags="animating_stone"
                    )
                
                self.root.after(30, lambda: animate_step(step + 1))
            else:
                self.canvas.delete("animating_stone")
                self.canvas.create_oval(
                    x - max_radius, y - max_radius,
                    x + max_radius, y + max_radius,
                    fill=fill_color, outline=outline_color, width=2,
                    tags="stone"
                )
                
        animate_step(1)
        
    def draw_legal_moves(self):
        """合法手のヒント描画"""
        legal_moves = self.game.get_legal_moves()
        for move in legal_moves:
            if move is not None:
                mx, my = move
                x = self.margin + my * self.cell_size
                y = self.margin + mx * self.cell_size
                
                self.canvas.create_oval(
                    x - 8, y - 8, x + 8, y + 8,
                    outline=self.colors['legal_hint'], width=2,
                    tags="legal_hint"
                )
                
    def draw_last_move_marker(self, board_x, board_y):
        """最後の手のマーカー描画"""
        x = self.margin + board_y * self.cell_size
        y = self.margin + board_x * self.cell_size
        
        self.canvas.create_oval(
            x - 8, y - 8, x + 8, y + 8,
            outline=self.colors['last_move'], width=3,
            tags="last_move"
        )
        
    def update_board_display(self):
        """盤面表示の更新"""
        self.draw_stones()
        
    # イベントハンドラ
    def on_canvas_click(self, event):
        """キャンバスクリックの処理"""
        if self.ai_thinking:
            return
            
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
                
        # 手を実行
        if self.make_move_with_animation(board_x, board_y):
            self.update_all_displays()
            
            # AIの手番
            if self.should_ai_move():
                self.root.after(500, self.ai_move)
                
    def on_mouse_move(self, event):
        """マウス移動の処理"""
        if self.ai_thinking:
            return
            
        self.canvas.delete("preview")
        
        board_x, board_y = self.pixel_to_board(event.x, event.y)
        if board_x is not None and board_y is not None:
            if self.game.is_legal_move(board_x, board_y, self.game.current_player):
                x = self.margin + board_y * self.cell_size
                y = self.margin + board_x * self.cell_size
                
                color = self.colors['preview']
                self.canvas.create_oval(
                    x - self.stone_radius, y - self.stone_radius,
                    x + self.stone_radius, y + self.stone_radius,
                    fill=color, outline='gray', width=1,
                    tags="preview"
                )
                
    def on_mouse_leave(self, event):
        """マウス離脱の処理"""
        self.canvas.delete("preview")
        
    def pixel_to_board(self, px, py):
        """画面座標を盤面座標に変換"""
        board_x = round((py - self.margin) / self.cell_size)
        board_y = round((px - self.margin) / self.cell_size)
        
        if 0 <= board_x < self.board_size and 0 <= board_y < self.board_size:
            return board_x, board_y
        return None, None
        
    # ゲーム制御メソッド
    def make_move_with_animation(self, x, y):
        """アニメーション付きの手の実行"""
        if self.game.is_legal_move(x, y, self.game.current_player):
            # 履歴に追加
            self.add_to_history()
            
            # 手を実行
            success = self.game.make_move((x, y))
            if success:
                self.game.last_move = (x, y)
                self.total_moves += 1
                
                # アニメーション付きで石を描画
                self.draw_stone(x, y, -self.game.current_player, animate=True)
                
                return True
        return False
        
    def should_ai_move(self):
        """AIが手を打つべきかチェック"""
        if self.game.game_over:
            return False
            
        if self.game_mode == "ai_vs_ai":
            return True
        elif self.game_mode == "human_vs_ai":
            is_ai_turn = (
                (self.game.current_player == 1 and not self.human_is_black) or
                (self.game.current_player == -1 and self.human_is_black)
            )
            return is_ai_turn
        return False
        
    def ai_move(self):
        """AIの手"""
        if self.ai_thinking or not self.ai_player:
            return
            
        self.ai_thinking = True
        self.ai_thinking_label.config(text="思考中...")
        self.thinking_progress.pack(fill=tk.X, padx=5, pady=2)
        self.thinking_progress.start()
        self.status_label.config(text="AI思考中...")
        
        def ai_think():
            try:
                start_time = time.time()
                move = self.ai_player.get_move(self.game)
                think_time = time.time() - start_time
                
                self.ai_move_times.append(think_time)
                self.root.after(0, lambda: self.execute_ai_move(move, think_time))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_ai_error(str(e)))
        
        threading.Thread(target=ai_think, daemon=True).start()
    
    def execute_ai_move(self, move, think_time):
        """AIの手を実行（UIスレッド）"""
        self.thinking_progress.stop()
        self.thinking_progress.pack_forget()
        self.ai_thinking = False
        self.ai_thinking_label.config(text="待機中")
        self.status_label.config(text="準備完了")
        
        if move:
            success = self.make_move_with_animation(move[0], move[1])
            self.game.last_move = move
        else:
            success = self.game.make_move(None)
            self.game.last_move = None
        
        if success:
            self.update_all_displays()
            
            # AI vs AI の場合は次のAIの手
            if self.game_mode == "ai_vs_ai" and not self.game.game_over:
                self.root.after(1000, self.ai_move)
    
    def handle_ai_error(self, error_msg):
        """AIエラーの処理"""
        self.thinking_progress.stop()
        self.thinking_progress.pack_forget()
        self.ai_thinking = False
        self.ai_thinking_label.config(text="エラー")
        self.status_label.config(text="AIエラー")
        messagebox.showerror("AIエラー", f"AIの思考中にエラーが発生しました:\n{error_msg}")
        
    def pass_move(self):
        """パス"""
        if self.ai_thinking:
            return
            
        self.add_to_history()
        success = self.game.make_move(None)
        if success:
            self.game.last_move = None
            self.total_moves += 1
            self.update_all_displays()
            
            if self.should_ai_move():
                self.root.after(500, self.ai_move)
    
    def resign_game(self):
        """投了"""
        if messagebox.askyesno("確認", "投了しますか？"):
            self.game.game_over = True
            current_player = "黒" if self.game.current_player == 1 else "白"
            winner = "白" if self.game.current_player == 1 else "黒"
            messagebox.showinfo("投了", f"{current_player}が投了しました\n{winner}の勝利です")
            self.update_all_displays()
    
    def new_game(self):
        """新しいゲーム"""
        if self.total_moves > 0:
            if not messagebox.askyesno("確認", "現在のゲームを終了して新しいゲームを開始しますか？"):
                return
                
        self.game = Game(self.board_size)
        self.ai_thinking = False
        self.game_start_time = time.time()
        self.ai_move_times = []
        self.total_moves = 0
        self.game_history = []
        self.current_history_index = -1
        
        self.setup_board()
        self.update_all_displays()
        self.clear_move_list()
        
        # AI vs AI の場合は自動開始
        if self.game_mode == "ai_vs_ai":
            self.root.after(1000, self.ai_move)
    
    def on_mode_change(self):
        """ゲームモード変更"""
        self.game_mode = self.mode_var.get()
        self.new_game()
    
    def on_color_change(self):
        """人間の色変更"""
        self.human_is_black = (self.color_var.get() == "black")
        
        # AI vs Human で、AIが先手の場合は即座にAIの手
        if (self.game_mode == "human_vs_ai" and 
            self.game.current_player == 1 and not self.human_is_black and 
            self.total_moves == 0):
            self.root.after(500, self.ai_move)
    
    # 履歴管理
    def add_to_history(self):
        """現在の状態を履歴に追加"""
        game_copy = Game(self.board_size)
        game_copy.board.board = self.game.board.board.copy()
        game_copy.current_player = self.game.current_player
        game_copy.captured_stones = self.game.captured_stones.copy()
        game_copy.game_over = self.game.game_over
        
        # 現在位置以降の履歴を削除
        self.game_history = self.game_history[:self.current_history_index + 1]
        self.game_history.append(game_copy)
        self.current_history_index += 1
    
    def undo_move(self):
        """手を戻る"""
        if self.ai_thinking:
            return
            
        if self.current_history_index > 0:
            self.current_history_index -= 1
            self.restore_from_history()
    
    def redo_move(self):
        """手を進む"""
        if self.ai_thinking:
            return
            
        if self.current_history_index < len(self.game_history) - 1:
            self.current_history_index += 1
            self.restore_from_history()
    
    def restore_from_history(self):
        """履歴から状態を復元"""
        if 0 <= self.current_history_index < len(self.game_history):
            history_game = self.game_history[self.current_history_index]
            
            self.game.board.board = history_game.board.board.copy()
            self.game.current_player = history_game.current_player
            self.game.captured_stones = history_game.captured_stones.copy()
            self.game.game_over = history_game.game_over
            
            self.update_all_displays()
    
    def clear_history(self):
        """履歴をクリア"""
        if messagebox.askyesno("確認", "履歴をクリアしますか？"):
            self.game_history = []
            self.current_history_index = -1
            self.clear_move_list()
    
    # UI更新メソッド
    def update_mcts_label(self, *args):
        """MCTSラベルの更新"""
        value = self.mcts_var.get()
        self.mcts_label.config(text=str(value))
        
        # AIプレイヤーの設定を更新
        if self.ai_player:
            self.ai_player.num_simulations = value
        
    def update_thinking_time_label(self, *args):
        """思考時間ラベルの更新"""
        value = self.thinking_time_var.get()
        self.thinking_time_label.config(text=f"{value}秒")
        
    def update_all_displays(self):
        """全ての表示を更新"""
        self.update_board_display()
        self.update_game_info()
        self.update_move_list()
        self.update_statistics()
        
        if self.game.game_over:
            self.show_game_result()
            
    def update_game_info(self):
        """ゲーム情報の更新"""
        # 現在のプレイヤー
        current = "黒" if self.game.current_player == 1 else "白"
        if self.game.game_over:
            self.current_player_label.config(text="ゲーム終了")
        else:
            self.current_player_label.config(text=f"{current}の番")
            
        # 捕獲した石
        black_captured = self.game.captured_stones.get(1, 0)
        white_captured = self.game.captured_stones.get(-1, 0)
        self.captured_label.config(text=f"捕獲: 黒 {black_captured}, 白 {white_captured}")
        
        # 手数
        self.moves_label.config(text=f"手数: {self.total_moves}")
        
    def update_move_list(self):
        """手順リストの更新"""
        self.moves_listbox.delete(0, tk.END)
        
        if hasattr(self.game, 'move_history'):
            for i, move in enumerate(self.game.move_history):
                player = "黒" if i % 2 == 0 else "白"
                if move is None:
                    move_text = f"{i+1}. {player}: パス"
                else:
                    # 座標を囲碁式に変換
                    col = chr(ord('A') + move[1]) if move[1] < 8 else chr(ord('A') + move[1] + 1)
                    row = self.board_size - move[0]
                    move_text = f"{i+1}. {player}: {col}{row}"
                
                self.moves_listbox.insert(tk.END, move_text)
    
    def clear_move_list(self):
        """手順リストをクリア"""
        self.moves_listbox.delete(0, tk.END)
        
    def update_statistics(self):
        """統計情報の更新"""
        # ゲーム統計
        self.total_moves_label.config(text=f"総手数: {self.total_moves}")
        
        # 経過時間
        elapsed = int(time.time() - self.game_start_time)
        minutes, seconds = divmod(elapsed, 60)
        self.game_time_label.config(text=f"経過時間: {minutes:02d}:{seconds:02d}")
        
        # 石の数
        board = self.game.board.board
        black_stones = np.sum(board == 1)
        white_stones = np.sum(board == -1)
        self.black_stones_label.config(text=f"黒石: {black_stones}")
        self.white_stones_label.config(text=f"白石: {white_stones}")
        
        # AI統計
        ai_moves = len(self.ai_move_times)
        self.ai_moves_label.config(text=f"AI手数: {ai_moves}")
        
        if self.ai_move_times:
            avg_time = sum(self.ai_move_times) / len(self.ai_move_times)
            fastest = min(self.ai_move_times)
            slowest = max(self.ai_move_times)
            
            self.avg_thinking_time_label.config(text=f"平均思考時間: {avg_time:.1f}秒")
            self.fastest_move_label.config(text=f"最速手: {fastest:.1f}秒")
            self.slowest_move_label.config(text=f"最遅手: {slowest:.1f}秒")
        
    def start_game_timer(self):
        """ゲームタイマーの開始"""
        def update_clock():
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.clock_label.config(text=current_time)
            self.root.after(1000, update_clock)
        
        update_clock()
        
    def on_move_select(self, event):
        """手順選択時の処理"""
        selection = self.moves_listbox.curselection()
        if selection:
            move_index = selection[0]
            # 選択された手まで復元する機能を実装可能
            
    # AI関連メソッド
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
                    num_simulations=self.mcts_var.get()
                )
                self.ai_status_label.config(text="AIモデル: 学習済みモデル読み込み済み")
                self.status_label.config(text="学習済みAI準備完了")
            else:
                self.ai_player = MCTSPlayer(None, num_simulations=self.mcts_var.get())
                self.ai_status_label.config(text="AIモデル: ランダムAI使用中")
                self.status_label.config(text="ランダムAI準備完了")
        except Exception as e:
            self.ai_player = MCTSPlayer(None, num_simulations=self.mcts_var.get())
            self.ai_status_label.config(text=f"AIモデル: エラー - {str(e)[:30]}...")
            self.status_label.config(text="AI読み込みエラー")
    
    def select_ai_model(self):
        """AIモデルを選択"""
        filename = filedialog.askopenfilename(
            title="AIモデルを選択",
            filetypes=[("PyTorch models", "*.pt"), ("All files", "*.*")]
        )
        if filename:
            try:
                network = ImprovedGoNeuralNetwork(board_size=self.board_size)
                checkpoint = torch.load(filename, map_location='cpu')
                network.load_state_dict(checkpoint['model_state_dict'])
                self.ai_player = MCTSPlayer(
                    network, 
                    num_simulations=self.mcts_var.get()
                )
                self.ai_status_label.config(text=f"AIモデル: {os.path.basename(filename)}")
                self.status_label.config(text="新しいAIモデル読み込み完了")
            except Exception as e:
                messagebox.showerror("エラー", f"モデルの読み込みに失敗しました:\n{e}")
    
    def reload_ai_model(self):
        """AIモデルを再読み込み"""
        self.load_ai_model()
        
    # ファイル操作
    def save_game(self):
        """ゲームの保存"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                game_data = {
                    'board_size': self.board_size,
                    'board': self.game.board.board.tolist(),
                    'current_player': self.game.current_player,
                    'move_history': getattr(self.game, 'move_history', []),
                    'captured_stones': self.game.captured_stones,
                    'game_over': self.game.game_over,
                    'total_moves': self.total_moves,
                    'game_mode': self.game_mode,
                    'human_is_black': self.human_is_black,
                    'save_time': datetime.datetime.now().isoformat()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(game_data, f, ensure_ascii=False, indent=2)
                    
                self.status_label.config(text=f"ゲームを保存: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました:\n{e}")
                
    def load_game(self):
        """ゲームの読み込み"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                    
                # ゲーム状態を復元
                self.game = Game(game_data['board_size'])
                self.game.board.board = np.array(game_data['board'])
                self.game.current_player = game_data['current_player']
                self.game.captured_stones = game_data['captured_stones']
                self.game.game_over = game_data['game_over']
                
                if 'move_history' in game_data:
                    self.game.move_history = game_data['move_history']
                
                if 'total_moves' in game_data:
                    self.total_moves = game_data['total_moves']
                    
                if 'game_mode' in game_data:
                    self.game_mode = game_data['game_mode']
                    self.mode_var.set(self.game_mode)
                    
                if 'human_is_black' in game_data:
                    self.human_is_black = game_data['human_is_black']
                    self.color_var.set("black" if self.human_is_black else "white")
                
                self.update_all_displays()
                self.status_label.config(text=f"ゲームを読み込み: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"読み込みに失敗しました:\n{e}")

    def save_sgf(self):
        """SGF形式で保存"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".sgf",
            filetypes=[("SGF files", "*.sgf"), ("All files", "*.*")]
        )
        if filename:
            try:
                sgf_content = self.generate_sgf()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sgf_content)
                self.status_label.config(text=f"SGF保存: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("エラー", f"SGF保存に失敗しました:\n{e}")
    
    def generate_sgf(self):
        """SGF形式のコンテンツを生成"""
        sgf = f"(;GM[1]FF[4]SZ[{self.board_size}]"
        sgf += f"DT[{datetime.datetime.now().strftime('%Y-%m-%d')}]"
        sgf += "AP[GoAI Advanced GUI]"
        
        if hasattr(self.game, 'move_history'):
            for i, move in enumerate(self.game.move_history):
                color = "B" if i % 2 == 0 else "W"
                if move is None:
                    sgf += f";{color}[]"
                else:
                    col = chr(ord('a') + move[1])
                    row = chr(ord('a') + move[0])
                    sgf += f";{color}[{col}{row}]"
        
        sgf += ")"
        return sgf

    # ダイアログ表示
    def show_game_result(self):
        """ゲーム結果の表示"""
        board = self.game.board.board
        black_stones = np.sum(board == 1)
        white_stones = np.sum(board == -1)
        
        if black_stones > white_stones:
            result = "黒の勝利！"
        elif white_stones > black_stones:
            result = "白の勝利！"
        else:
            result = "引き分け！"
        
        messagebox.showinfo(
            "ゲーム終了", 
            f"{result}\n\n黒石: {black_stones}\n白石: {white_stones}\n総手数: {self.total_moves}"
        )
    
    def show_settings(self):
        """設定ダイアログ"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("設定")
        settings_window.geometry("400x500")
        settings_window.resizable(False, False)
        
        # 表示設定
        display_frame = ttk.LabelFrame(settings_window, text="表示設定")
        display_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(display_frame, text="合法手をハイライト", variable=self.show_legal_moves).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(display_frame, text="座標を表示", variable=self.show_coordinates).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(display_frame, text="アニメーション", variable=self.animate_stones).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(display_frame, text="自動保存", variable=self.auto_save).pack(anchor=tk.W, padx=5, pady=2)
        
        # 色設定
        color_frame = ttk.LabelFrame(settings_window, text="色設定")
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(color_frame, text="盤面色を変更", command=self.change_board_color).pack(pady=2)
        ttk.Button(color_frame, text="デフォルトに戻す", command=self.reset_colors).pack(pady=2)
        
        # 適用ボタン
        ttk.Button(settings_window, text="適用", command=lambda: [self.setup_board(), settings_window.destroy()]).pack(pady=10)
    
    def change_board_color(self):
        """盤面色の変更"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.colors['board'])
        if color[1]:
            self.colors['board'] = color[1]
            self.setup_board()
    
    def reset_colors(self):
        """色設定をリセット"""
        self.colors = {
            'board': '#DEB887',
            'line': '#8B7355',
            'black_stone': '#1C1C1C',
            'white_stone': '#F5F5F5',
            'last_move': '#FF4444',
            'legal_hint': '#90EE90',
            'preview': '#D3D3D3'
        }
        self.setup_board()
    
    def show_help(self):
        """ヘルプダイアログ"""
        help_text = """
囲碁AI Pro - 操作方法

【基本操作】
• 石を打つ: 盤面をクリック
• パス: パスボタンまたはスペースキー
• 投了: 投了ボタン

【キーボードショートカット】
• Ctrl+N: 新しいゲーム
• Ctrl+S: ゲーム保存
• Ctrl+O: ゲーム読み込み
• Ctrl+Z: 手を戻る
• Ctrl+Y: 手を進む
• Space: パス

【ゲームモード】
• 人間 vs AI: AIと対戦
• AI vs AI: AI同士の対戦を観戦
• 人間 vs 人間: 2人対戦

【AI設定】
• MCTS シミュレーション数で強さ調整
• 思考時間制限で快適性調整

【その他の機能】
• ゲーム履歴の保存・読み込み
• SGF形式でのエクスポート
• 詳細な統計情報表示
• 合法手のハイライト表示
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("ヘルプ")
        help_window.geometry("500x600")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_about(self):
        """バージョン情報"""
        about_text = """
囲碁AI Pro
Advanced Go Game with AI

Version: 1.0.0
Based on: MCTS + Deep Neural Network

Features:
• Monte Carlo Tree Search (MCTS)
• Deep Learning with PyTorch
• Self-play training system
• Advanced GUI with animations
• Game save/load functionality
• Comprehensive statistics

Developed with ❤️ for Go enthusiasts
        """
        messagebox.showinfo("バージョン情報", about_text)
    
    def run(self):
        """GUIの実行"""
        self.root.mainloop()


def main():
    """メイン実行関数"""
    print("🎮 高度な囲碁AI GUI を起動しています...")
    
    try:
        app = AdvancedGoGUI(board_size=9)
        app.run()
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
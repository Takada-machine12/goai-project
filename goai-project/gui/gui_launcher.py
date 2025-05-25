# gui_launcher.py - GUIランチャー
import tkinter as tk
from tkinter import messagebox
import os
import sys

def launch_simple_gui():
    """シンプルGUIを起動"""
    try:
        from gui.go_gui import GoGUI
        app = GoGUI(board_size=9)
        app.run()
    except ImportError as e:
        messagebox.showerror("エラー", f"GUIモジュールが見つかりません:\n{e}")
    except Exception as e:
        messagebox.showerror("エラー", f"GUIの起動に失敗しました:\n{e}")

def launch_advanced_gui():
    """高度なGUIを起動"""
    try:
        from gui.advanced_gui import AdvancedGoGUI
        app = AdvancedGoGUI(board_size=9)
        app.run()
    except ImportError as e:
        messagebox.showerror("エラー", f"高度なGUIモジュールが見つかりません:\n{e}")
    except Exception as e:
        messagebox.showerror("エラー", f"高度なGUIの起動に失敗しました:\n{e}")

def create_launcher_window():
    """ランチャーウィンドウを作成"""
    root = tk.Tk()
    root.title("囲碁AI - GUI選択")
    root.geometry("400x300")
    root.resizable(False, False)
    
    # メインフレーム
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # タイトル
    title_label = tk.Label(
        main_frame,
        text="囲碁AI システム",
        font=("Arial", 16, "bold")
    )
    title_label.pack(pady=(0, 20))
    
    # 説明
    desc_label = tk.Label(
        main_frame,
        text="使用するGUIを選択してください",
        font=("Arial", 12)
    )
    desc_label.pack(pady=(0, 30))
    
    # シンプルGUIボタン
    simple_btn = tk.Button(
        main_frame,
        text="シンプル GUI",
        font=("Arial", 12),
        width=20,
        height=2,
        command=lambda: [root.destroy(), launch_simple_gui()]
    )
    simple_btn.pack(pady=10)
    
    simple_desc = tk.Label(
        main_frame,
        text="基本的な機能のみ\n軽量で高速",
        font=("Arial", 10),
        fg="gray"
    )
    simple_desc.pack(pady=(0, 20))
    
    # 高度なGUIボタン
    advanced_btn = tk.Button(
        main_frame,
        text="高度な GUI",
        font=("Arial", 12),
        width=20,
        height=2,
        command=lambda: [root.destroy(), launch_advanced_gui()]
    )
    advanced_btn.pack(pady=10)
    
    advanced_desc = tk.Label(
        main_frame,
        text="全機能搭載\nアニメーション・統計・ファイル保存",
        font=("Arial", 10),
        fg="gray"
    )
    advanced_desc.pack(pady=(0, 20))
    
    # コマンドライン起動の説明
    cli_label = tk.Label(
        main_frame,
        text="コマンドライン版:\npython main.py play",
        font=("Arial", 10),
        fg="blue"
    )
    cli_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    create_launcher_window()


# main.py にGUI起動オプションを追加
def add_gui_option_to_main():
    """main.pyにGUIオプションを追加するためのコード例"""
    
    # これを既存のmain.pyのargparserに追加
    gui_code = '''
    # main.pyのargument parserに以下を追加:
    
    parser.add_argument('mode', choices=['train', 'play', 'ai_vs_ai', 'demo', 'gui'], 
                       help='実行モード')
    
    # main関数に以下のケースを追加:
    elif args.mode == 'gui':
        # GUI選択画面を表示
        from gui_launcher import create_launcher_window
        create_launcher_window()
    '''
    
    return gui_code

# 使用方法のドキュメント
usage_doc = """
囲碁AI GUI の使用方法

## インストールと起動

### 必要なライブラリ
tkinter は Python 標準ライブラリなので追加インストール不要

### 起動方法

1. GUI選択画面から起動:
   python gui_launcher.py

2. シンプルGUIを直接起動:
   python gui/go_gui.py

3. 高度なGUIを直接起動:
   python gui/advanced_gui.py

4. main.pyから起動（要修正）:
   python main.py gui

## 機能一覧

### シンプルGUI
- 基本的な対戦機能
- 人間 vs AI
- AI vs AI  
- 人間 vs 人間
- パス・投了
- リアルタイム盤面表示

### 高度なGUI
- シンプルGUI の全機能
- タブ式インターフェース
- アニメーション効果
- 履歴管理（戻る・進む）
- ゲーム保存・読み込み
- 統計情報表示
- AI設定調整
- 合法手ハイライト
- キーボードショートカット

## 操作方法

### 基本操作
- 石を打つ: 盤面をクリック
- パス: パスボタンをクリック
- 投了: 投了ボタンをクリック
- 新しいゲーム: 新しいゲームボタンをクリック

### キーボードショートカット（高度なGUI）
- Ctrl+N: 新しいゲーム
- Ctrl+S: ゲーム保存
- Ctrl+O: ゲーム読み込み
- Ctrl+Z: 手を戻る
- Ctrl+Y: 手を進む

### AI設定
- MCTS シミュレーション数: 50-1000（デフォルト: 200）
- 思考時間制限: 1-30秒（デフォルト: 5秒）
- モデル選択: 学習済みモデルの切り替え

## トラブルシューティング

### GUIが起動しない場合
1. tkinter がインストールされているか確認
2. Python バージョンが 3.6 以上か確認
3. プロジェクトのルートディレクトリから実行

### AIが動作しない場合
1. 学習済みモデル (trained_models/final_model.pt) が存在するか確認
2. PyTorch がインストールされているか確認
3. エラーメッセージを確認

### 動作が重い場合
1. MCTS シミュレーション数を減らす
2. シンプルGUIを使用
3. AI思考時間制限を短く設定
"""

def show_usage():
    """使用方法を表示"""
    usage_window = tk.Toplevel()
    usage_window.title("使用方法")
    usage_window.geometry("600x500")
    
    text_widget = tk.Text(usage_window, wrap=tk.WORD, padx=10, pady=10)
    scrollbar = tk.Scrollbar(usage_window, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.config(yscrollcommand=scrollbar.set)
    
    text_widget.insert(tk.END, usage_doc)
    text_widget.config(state=tk.DISABLED)
    
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def check_requirements():
    """必要な要件をチェック"""
    requirements = {
        'tkinter': True,
        'torch': False,
        'numpy': False,
        'threading': True
    }
    
    try:
        import tkinter
        requirements['tkinter'] = True
    except ImportError:
        requirements['tkinter'] = False
    
    try:
        import torch
        requirements['torch'] = True
    except ImportError:
        requirements['torch'] = False
        
    try:
        import numpy
        requirements['numpy'] = True
    except ImportError:
        requirements['numpy'] = False
        
    return requirements

def show_requirements_check():
    """要件チェック結果を表示"""
    req = check_requirements()
    
    req_window = tk.Toplevel()
    req_window.title("システム要件チェック")
    req_window.geometry("400x300")
    
    main_frame = tk.Frame(req_window, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(main_frame, text="システム要件チェック", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    for lib, status in req.items():
        color = "green" if status else "red"
        symbol = "✓" if status else "✗"
        text = f"{symbol} {lib}: {'OK' if status else 'NG'}"
        
        tk.Label(main_frame, text=text, fg=color, font=("Arial", 12)).pack(anchor=tk.W, pady=2)
    
    # 推奨事項
    tk.Label(main_frame, text="\n推奨事項:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(20, 5))
    
    recommendations = [
        "• tkinter: Python標準ライブラリ（通常は自動でインストール済み）",
        "• torch: pip install torch",
        "• numpy: pip install numpy",
        "• 全てインストール済みの場合、全機能が利用可能です"
    ]
    
    for rec in recommendations:
        tk.Label(main_frame, text=rec, font=("Arial", 10), wraplength=350).pack(anchor=tk.W, pady=1)

def create_enhanced_launcher():
    """拡張ランチャーウィンドウを作成"""
    root = tk.Tk()
    root.title("囲碁AI システム - ランチャー")
    root.geometry("500x400")
    root.resizable(False, False)
    
    # メインフレーム
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # ヘッダー
    header_frame = tk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 30))
    
    title_label = tk.Label(
        header_frame,
        text="🎮 囲碁AI システム",
        font=("Arial", 18, "bold"),
        fg="#2E4057"
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        header_frame,
        text="Advanced Go AI with Deep Learning & MCTS",
        font=("Arial", 11),
        fg="gray"
    )
    subtitle_label.pack(pady=(5, 0))
    
    # メニューフレーム
    menu_frame = tk.Frame(main_frame)
    menu_frame.pack(fill=tk.BOTH, expand=True)
    
    # GUI選択セクション
    gui_section = tk.LabelFrame(menu_frame, text="GUI 選択", font=("Arial", 12, "bold"), padx=10, pady=10)
    gui_section.pack(fill=tk.X, pady=(0, 20))
    
    # シンプルGUI
    simple_frame = tk.Frame(gui_section)
    simple_frame.pack(fill=tk.X, pady=5)
    
    tk.Button(
        simple_frame,
        text="🎯 シンプル GUI",
        font=("Arial", 12, "bold"),
        width=15,
        height=2,
        bg="#4CAF50",
        fg="white",
        command=lambda: [root.destroy(), launch_simple_gui()]
    ).pack(side=tk.LEFT)
    
    tk.Label(
        simple_frame,
        text="基本機能のみ | 軽量・高速 | 初心者向け",
        font=("Arial", 10),
        fg="gray"
    ).pack(side=tk.LEFT, padx=(15, 0))
    
    # 高度なGUI
    advanced_frame = tk.Frame(gui_section)
    advanced_frame.pack(fill=tk.X, pady=5)
    
    tk.Button(
        advanced_frame,
        text="⚡ 高度な GUI",
        font=("Arial", 12, "bold"),
        width=15,
        height=2,
        bg="#2196F3",
        fg="white",
        command=lambda: [root.destroy(), launch_advanced_gui()]
    ).pack(side=tk.LEFT)
    
    tk.Label(
        advanced_frame,
        text="全機能搭載 | アニメーション | 統計・保存機能",
        font=("Arial", 10),
        fg="gray"
    ).pack(side=tk.LEFT, padx=(15, 0))
    
    # その他のオプション
    options_section = tk.LabelFrame(menu_frame, text="その他のオプション", font=("Arial", 12, "bold"), padx=10, pady=10)
    options_section.pack(fill=tk.X, pady=(0, 20))
    
    # ボタン行1
    btn_row1 = tk.Frame(options_section)
    btn_row1.pack(fill=tk.X, pady=2)
    
    tk.Button(
        btn_row1,
        text="📋 使用方法",
        font=("Arial", 10),
        width=12,
        command=show_usage
    ).pack(side=tk.LEFT, padx=(0, 5))
    
    tk.Button(
        btn_row1,
        text="🔧 要件チェック",
        font=("Arial", 10),
        width=12,
        command=show_requirements_check
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_row1,
        text="💻 コマンドライン",
        font=("Arial", 10),
        width=12,
        command=lambda: [root.destroy(), os.system("python main.py")]
    ).pack(side=tk.LEFT, padx=5)
    
    # フッター情報
    footer_frame = tk.Frame(main_frame)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
    
    footer_text = "🚀 学習済みモデル搭載 | MCTS + Neural Network | 自己対戦学習"
    tk.Label(
        footer_frame,
        text=footer_text,
        font=("Arial", 9),
        fg="#666666"
    ).pack()
    
    # 要件チェック
    req = check_requirements()
    all_ok = all(req.values())
    status_color = "green" if all_ok else "orange"
    status_text = "✓ 全ての要件が満たされています" if all_ok else "⚠ 一部の機能が制限される可能性があります"
    
    tk.Label(
        footer_frame,
        text=status_text,
        font=("Arial", 9),
        fg=status_color
    ).pack(pady=(5, 0))
    
    # ウィンドウを中央に配置
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    create_enhanced_launcher()
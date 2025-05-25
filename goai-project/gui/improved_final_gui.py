"""
囲碁AI プロジェクト設定ファイル

このファイルは全ての設定値を一元管理し、
ハードコードされた値を排除することを目的としています。
"""

import os
from pathlib import Path

# ===== プロジェクト基本設定 =====
PROJECT_ROOT = Path(__file__).parent
PROJECT_NAME = "GoAI"
VERSION = "1.0.0"

# ===== ディレクトリ設定 =====
DIRECTORIES = {
    "models": PROJECT_ROOT / "trained_models",
    "logs": PROJECT_ROOT / "logs", 
    "data": PROJECT_ROOT / "data",
    "configs": PROJECT_ROOT / "configs",
    "temp": PROJECT_ROOT / "temp"
}

# ===== 囲碁ゲーム設定 =====
GAME_CONFIG = {
    "default_board_size": 9,
    "supported_board_sizes": [9, 13, 19],
    "default_komi": 6.5,
    "time_limit": None,  # 秒数、Noneで無制限
}

# ===== AI設定 =====
AI_CONFIG = {
    "model_file": "final_model.pt",
    "mcts_simulations": 100,
    "mcts_c_puct": 1.0,
    "neural_network": {
        "input_channels": 17,
        "residual_blocks": 5,
        "filters": 64,
        "value_head_hidden": 64,
        "policy_head_hidden": 64,
    },
    "training": {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10,
        "save_interval": 5,
    }
}

# ===== GUI設定 =====
GUI_CONFIG = {
    "default_gui": "simple",  # "simple", "advanced", "mac"
    "window_size": (800, 600),
    "board_display": {
        "cell_size": 40,
        "margin": 30,
        "stone_radius": 15,
        "colors": {
            "background": "#DEB887",
            "lines": "#000000", 
            "black_stone": "#000000",
            "white_stone": "#FFFFFF",
            "star_points": "#000000",
        }
    },
    "themes": {
        "default": {
            "background": "#F5F5DC",
            "button": "#8FBC8F",
            "text": "#000000",
        },
        "dark": {
            "background": "#2F2F2F",
            "button": "#4F4F4F", 
            "text": "#FFFFFF",
        }
    }
}

# ===== ログ設定 =====
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": PROJECT_ROOT / "logs" / "goai.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# ===== 開発設定 =====
DEV_CONFIG = {
    "debug_mode": os.getenv("GOAI_DEBUG", "false").lower() == "true",
    "profiling": False,
    "verbose_ai": False,
    "gui_debug": False,
}

# ===== ファイルパス設定 =====
def get_model_path(model_name: str = None) -> Path:
    """学習済みモデルのパスを取得"""
    if model_name is None:
        model_name = AI_CONFIG["model_file"]
    return DIRECTORIES["models"] / model_name

def get_log_path(log_name: str = "goai.log") -> Path:
    """ログファイルのパスを取得"""
    return DIRECTORIES["logs"] / log_name

def ensure_directories():
    """必要なディレクトリを作成"""
    for name, path in DIRECTORIES.items():
        path.mkdir(parents=True, exist_ok=True)

# ===== 環境変数による設定上書き =====
def load_env_overrides():
    """環境変数による設定の上書きを適用"""
    # ボードサイズ
    if "GOAI_BOARD_SIZE" in os.environ:
        try:
            size = int(os.environ["GOAI_BOARD_SIZE"])
            if size in GAME_CONFIG["supported_board_sizes"]:
                GAME_CONFIG["default_board_size"] = size
        except ValueError:
            pass
    
    # MCTS シミュレーション回数
    if "GOAI_MCTS_SIMS" in os.environ:
        try:
            sims = int(os.environ["GOAI_MCTS_SIMS"])
            if sims > 0:
                AI_CONFIG["mcts_simulations"] = sims
        except ValueError:
            pass
    
    # GUI テーマ
    if "GOAI_GUI_THEME" in os.environ:
        theme = os.environ["GOAI_GUI_THEME"]
        if theme in GUI_CONFIG["themes"]:
            GUI_CONFIG["default_theme"] = theme

# 初期化時に環境変数を読み込み
load_env_overrides()

# ===== 設定値の検証 =====
def validate_config():
    """設定値の妥当性をチェック"""
    errors = []
    
    # ボードサイズの検証
    if GAME_CONFIG["default_board_size"] not in GAME_CONFIG["supported_board_sizes"]:
        errors.append(f"Invalid board size: {GAME_CONFIG['default_board_size']}")
    
    # AIシミュレーション回数の検証
    if AI_CONFIG["mcts_simulations"] <= 0:
        errors.append(f"MCTS simulations must be positive: {AI_CONFIG['mcts_simulations']}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))

# 設定の検証を実行
validate_config()

# ===== 使用例 =====
if __name__ == "__main__":
    print(f"Project: {PROJECT_NAME} v{VERSION}")
    print(f"Root: {PROJECT_ROOT}")
    print(f"Board size: {GAME_CONFIG['default_board_size']}")
    print(f"MCTS sims: {AI_CONFIG['mcts_simulations']}")
    
    # ディレクトリ作成
    ensure_directories()
    print("Directories created successfully!")
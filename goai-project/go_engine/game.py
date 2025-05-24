# go_engine/game.py
from .board import Board, BLACK, WHITE, EMPTY

class Game:
    def __init__(self, board_size=9):
        self.board = Board(board_size)
        self.current_player = BLACK
        self.passes = 0
        self.game_over = False
        self.move_history = []
        self.board_history = []
        
    def get_legal_moves(self):
        """合法手のリストを取得"""
        legal_moves = []
        for x in range(self.board.size):
            for y in range(self.board.size):
                if self.is_legal_move(x, y):
                    legal_moves.append((x, y))
        # パスは常に合法
        legal_moves.append(None)
        return legal_moves
        
    def is_legal_move(self, x, y):
        """指定された手が合法かどうかチェック"""
        # パスの場合は常に合法
        if x is None and y is None:
            return True
        
        # 盤面の範囲外またはすでに石がある場合は不正
        if not self.board.is_on_board(x, y) or self.board.get_color(x, y) != EMPTY:
            return False
        
        # 簡略版：空いているマスには打てる
        return True
    
    def make_move(self, move):
        """手を実行"""
        if move is None:  # パス
            self.passes += 1
            self.current_player = -self.current_player
            self.move_history.append(None)
            
            # 連続２回のパスでゲーム終了
            if self.passes >= 2:
                self.game_over =True
                
            return True
            
        x, y = move
        if not self.is_legal_move(x, y):
            return False
            
        self.passes = 0
        self.board.place_stone(x, y, self.current_player)
        # 石を取る処理など
        
        self.current_player = -self.current_player
        self.move_history.append((x, y))
            
        return True
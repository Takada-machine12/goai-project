# go_engine/board.py
import numpy as np

# 定数定義
EMPTY = 0
BLACK = 1
WHITE = -1

class Board:
    def __init__(self, size=9):
        self.size = size
        self.board = np.zeros((size, size), dtype=np.int8)
        self.ko = None
        
    def is_on_board(self, x, y):
        """盤面内かどうかチェック"""
        return 0 <= x < self.size and 0 <= y < self.size
    
    def get_adjacent_points(self, x, y):
        """隣接する点を取得"""
        adjacent = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if self.is_on_board(nx, ny):
                adjacent.append((nx, ny))
        return
    
    def get_color(self, x, y):
        """指定位置の石の色を取得"""
        if not self.is_on_board(x, y):
            return None
        return self.board[x, y]
    
    def place_stone(self, x, y, color):
        """石を置く（合法手チェックなし）"""
        self.board[x, y] = color
        
    def remove_stone(self, x, y):
        """石を取り除く"""
        self.board[x, y] = EMPTY
        
    def display(self):
        """盤面を表示"""
        for i in range(self.size):
            row = []
            for j in range(self.size):
                if self.board[i, j] == BLACK:
                    row.append('B')
                elif self.board[i, j] == WHITE:
                    row.append('W')
                else:
                    row.append('.')
            print(''.join(row))
        print()
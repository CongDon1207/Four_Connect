import os
import numpy as np
import streamlit as st
from PIL import Image
from easyAI import TwoPlayerGame, AI_Player, Negamax, SSS

# Set the path to your image files
image_directory = '.'  # Adjust this path to where your images are stored

def check_image_exists(image_path):
    if not os.path.exists(image_path):
        st.error(f"Image not found: {image_path}")
        return False
    return True

class GameController(TwoPlayerGame):
    def __init__(self, players, board=None):
        self.players = players
        self.board = np.zeros((6, 7), dtype=int) if board is None else board
        self.nplayer = 1  # Người chơi 1 bắt đầu
        self.current_player = 1  # Người chơi hiện tại
        self.history = []  # Lưu trữ lịch sử các trạng thái bảng để hỗ trợ Undo

        # Định nghĩa các vị trí và hướng đi
        self.pos_dir = []
        for i in range(6):
            self.pos_dir.append(([i, 0], [0, 1]))  # Hàng ngang
        for i in range(7):
            self.pos_dir.append(([0, i], [1, 0]))  # Cột dọc
        for i in range(3):
            self.pos_dir.append(([i, 0], [1, 1]))  # Đường chéo từ trái qua phải
        for i in range(4):
            self.pos_dir.append(([0, i], [1, 1]))  # Đường chéo từ trên xuống dưới
        for i in range(3):
            self.pos_dir.append(([i, 6], [1, -1]))  # Đường chéo từ phải qua trái
        for i in range(4, 7):
            self.pos_dir.append(([0, i], [1, -1]))  # Đường chéo từ dưới lên trên

    def possible_moves(self):
        return [str(col) for col in range(7) if self.board[0, col] == 0]

    def make_move(self, move):
        if move == "undo":
            if len(self.history) >= 2:
                self.board = self.history.pop()  # Hoàn tác một bước
                self.switch_player()  # Chuyển lại lượt chơi sau khi hoàn tác
                self.board = self.history.pop()  # Hoàn tác bước thứ hai
                self.switch_player()  # Chuyển lại lượt chơi sau khi hoàn tác
            else:
                st.info("Không thể hoàn tác, không có đủ lịch sử để quay lại.")
        else:
            self.history.append(self.board.copy())  # Lưu trữ trạng thái hiện tại trước khi thực hiện nước đi
            column = int(move)
            for row in range(5, -1, -1):
                if self.board[row, column] == 0:
                    self.board[row, column] = self.nplayer
                    break

    def show(self):
        st.session_state.board = self.board.copy()

    def loss_condition(self):
        for positions, direction in self.pos_dir:
            streak = 0
            pos = np.array(positions)
            while (0 <= pos[0] < 6) and (0 <= pos[1] < 7):
                if self.board[pos[0], pos[1]] == self.nopponent:
                    streak += 1
                    if streak == 4:
                        return True
                else:
                    streak = 0
                pos += direction
        return False

    def is_over(self):
        return self.board.all() or self.loss_condition()

    def scoring(self):
        return -100 if self.loss_condition() else 0

    @property
    def nopponent(self):
        return 3 - self.nplayer

    def switch_player(self):
        self.current_player = 3 - self.current_player
        self.nplayer = 3 - self.nplayer

class Human_Player:
    def __init__(self):
        pass

    def ask_move(self, game):
        move = input("Your move (0-6 or 'undo' to undo): ")
        while move not in game.possible_moves():
            move = input("Invalid move. Your move (0-6 or 'undo' to undo): ")
        return move

def load_images():
    # Load images for the game pieces
    red_img_path = os.path.join(image_directory, "red_in_grid.png")
    yellow_img_path = os.path.join(image_directory, "yellow_in_grid.png")
    empty_img_path = os.path.join(image_directory, "image.png")

    # Check if images exist
    if not check_image_exists(red_img_path) or not check_image_exists(yellow_img_path) or not check_image_exists(empty_img_path):
        raise FileNotFoundError("One or more image files are missing.")

    # Load images
    red_img = Image.open(red_img_path)
    yellow_img = Image.open(yellow_img_path)
    empty_img = Image.open(empty_img_path)
    
    return red_img, yellow_img, empty_img

def main():
    st.title("Connect Four")
    mode = st.selectbox("Chọn chế độ chơi", ["Chơi với máy", "Chơi với người"])
    if mode == "Chơi với máy":
        level = st.slider("Chọn mức độ khó", 1, 5, 1)
    else:
        level = None

    red_img, yellow_img, empty_img = load_images()

    if st.button("Bắt đầu trò chơi"):
        if mode == "Chơi với máy":
            algo_neg = Negamax(level) if level <= 3 else SSS(level)
            game = GameController([Human_Player(), AI_Player(algo_neg)])
        else:
            game = GameController([Human_Player(), Human_Player()])

        st.session_state.game = game
        game.show()

        # Nếu là chế độ chơi với máy, cho phép AI thực hiện nước đi đầu tiên nếu AI là người chơi đầu tiên
        if isinstance(game.players[game.current_player - 1], AI_Player):
            ai_move = game.players[game.current_player - 1].ask_move(game)
            game.make_move(ai_move)
            game.switch_player()
            game.show()
    
    if 'game' in st.session_state:
        game = st.session_state.game

        # Hiển thị lưới trò chơi
        grid = st.empty()
        with grid.container():
            for row in range(6):
                cols = st.columns(7)
                for col in range(7):
                    value = game.board[row, col]
                    if value == 0:
                        cols[col].image(empty_img)
                    elif value == 1:
                        cols[col].image(red_img)
                    else:
                        cols[col].image(yellow_img)

        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        columns = [col1, col2, col3, col4, col5, col6, col7]
        
        for col_index, col in enumerate(columns):
            with col:
                if st.button(f"Chọn cột {col_index}"):
                    move = str(col_index)
                    if move in game.possible_moves():
                        game.make_move(move)
                        game.switch_player()
                        game.show()

                        if game.is_over():
                            if game.loss_condition():
                                st.balloons()
                                if mode == "Chơi với máy":
                                    winner = "AI wins!" if isinstance(game.players[game.nopponent - 1], AI_Player) else "You win!"
                                else:
                                    winner = f'Player {game.nopponent} wins!'
                                st.success(winner)
                            else:
                                st.info("It's a draw.")
                            del st.session_state.game
                        else:
                            # Nếu chế độ chơi với máy, để AI thực hiện nước đi sau khi người chơi di chuyển
                            if isinstance(game.players[game.current_player - 1], AI_Player):
                                ai_move = game.players[game.current_player - 1].ask_move(game)
                                game.make_move(ai_move)
                                game.switch_player()
                                game.show()

                                if game.is_over():
                                    if game.loss_condition():
                                        st.balloons()
                                        if mode == "Chơi với máy":
                                            winner = "AI wins!" if isinstance(game.players[game.nopponent - 1], AI_Player) else "You win!"
                                        else:
                                            winner = f'Player {game.nopponent} wins!'
                                        st.success(winner)
                                    else:
                                        st.info("It's a draw.")
                                    del st.session_state.game

        # Cập nhật lưới trò chơi sau khi di chuyển
        with grid.container():
            for row in range(6):
                cols = st.columns(7)
                for col in range(7):
                    value = game.board[row, col]
                    if value == 0:
                        cols[col].image(empty_img)
                    elif value == 1:
                        cols[col].image(red_img)
                    else:
                        cols[col].image(yellow_img)

    if 'game' in st.session_state and st.button("Undo"):
        game.make_move("undo")
        game.switch_player()
        game.show()

        # Cập nhật lưới trò chơi sau khi hoàn tác
        with grid.container():
            for row in range(6):
                cols = st.columns(7)
                for col in range(7):
                    value = game.board[row, col]
                    if value == 0:
                        cols[col].image(empty_img)
                    elif value == 1:
                        cols[col].image(red_img)
                    else:
                        cols[col].image(yellow_img)

if __name__ == "__main__":
    main()

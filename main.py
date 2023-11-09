import datetime as dt
import random
import sqlite3
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTableWidgetItem,
    QVBoxLayout,
)

from ui.file import Ui_MainWindow

__all__ = []


class MyWindow(QMainWindow, Ui_MainWindow):  # Главный класс
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.stackedWidget.setCurrentWidget(self.P_start)

        # /=================== CONST ===================\
        self.value = 10  # Размер поля
        self.size = 550 // self.value  # Размер клеток
        self.count_of_mines = 15  # Количество мин

        self.MINES = None
        self.anti_lose = False
        self.buttons = []
        self.map = None
        self.checked = None
        self.first_move = None
        self.win_detect = None
        self.lose_detect = None
        self.last_lose_square = None
        self.date_start = None
        self.timer = None
        self.time = None
        self.is_running = None
        # \=================== CONST ===================/

        # /=================== BUTTON EVENT ===================\
        self.B_start_play.clicked.connect(self.setting)
        # \=================== BUTTON EVENT ===================/

        # /=================== TABLE UPDATE ===================\
        try:
            with sqlite3.connect("data/database.db") as connect:
                cursor = connect.cursor()
                result = cursor.execute(
                    """
                        SELECT * FROM board
                        ORDER BY time
                    """,
                ).fetchall()

                # Заполнили размеры таблицы
                if result:
                    self.TW.setRowCount(len(result))
                    self.TW.setColumnCount(4)

                    self.TW.clear()
                    self.TW.setHorizontalHeaderLabels(
                        [
                            "Разм. поля",
                            "Кол. мин",
                            "Время",
                            "Дата",
                        ],
                    )
                    for i, elem in enumerate(result):
                        for j, val in enumerate(tuple(elem[1:])):
                            self.TW.setItem(i, j, QTableWidgetItem(str(val)))
                    header = self.TW.horizontalHeader()
                    for i in range(self.TW.columnCount()):
                        header.setSectionResizeMode(i, QHeaderView.Stretch)

                    # Создаем палитру с серыми цветами
                    palette = QPalette()
                    palette.setColor(QPalette.Window, QColor(53, 53, 53))
                    palette.setColor(QPalette.WindowText, Qt.black)
                    palette.setColor(QPalette.Base, QColor(15, 15, 15))
                    palette.setColor(
                        QPalette.AlternateBase,
                        QColor(53, 53, 53),
                    )
                    palette.setColor(QPalette.ToolTipBase, Qt.black)
                    palette.setColor(QPalette.ToolTipText, Qt.white)
                    palette.setColor(QPalette.Text, Qt.white)
                    palette.setColor(QPalette.Button, QColor(53, 53, 53))
                    palette.setColor(QPalette.ButtonText, Qt.white)
                    palette.setColor(QPalette.BrightText, Qt.red)
                    palette.setColor(QPalette.Link, QColor(42, 130, 218))
                    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
                    palette.setColor(QPalette.HighlightedText, Qt.black)

                    # Устанавливаем палитру для нашей таблицы
                    self.TW.setPalette(palette)

                    # Задаем стиль границ для ячеек таблицы
                    self.TW.setStyleSheet(
                        "QTableView { border: 1px solid grey; color: black; "
                        "font-size: 20px;}",
                    )

                    # Задаем стиль для заголовка таблицы
                    self.TW.horizontalHeader().setStyleSheet(
                        "QHeaderView::section { background-color: grey; "
                        "color: white; }",
                    )
        except Exception as e:
            print(e)
        # \=================== TABLE UPDATE ===================/

    def new_game(self):
        self.map = [
            ["." for _ in range(self.value)] for _ in range(self.value)
        ]
        self.MINES = []
        self.checked = set()
        self.first_move = True
        self.win_detect = False
        self.lose_detect = False
        self.last_lose_square = None
        self.update_squares()

    def restart_game(self):
        self.del_last_game()
        self.new_game()

        self.date_start = dt.datetime.now().date()
        self.time = 0
        self.is_running = False

        self.start_timer()

        self.anti_lose = False
        self.update_squares(restart=True)

    def set_color(self):
        for row_index, row in enumerate(self.map):
            for col_index, col in enumerate(row):
                value = self.map[row_index][col_index]
                if value.isdigit():
                    square = row_index * self.value + col_index
                    self.buttons[square].setStyleSheet(
                        "background-color: #f00",
                    )

    def update_texts(self):
        if self.win_detect:
            self.L_3.setText("ПОБЕДА!")
        elif self.lose_detect:
            self.L_3.setText("ПОРАЖЕНИЕ!")
        else:
            self.L_3.setText("")

        len_of_checked_buttons = len(self.checked)
        count_of_left = (
                self.value ** 2 - self.count_of_mines - len_of_checked_buttons
        )
        self.L_2_1.setText(
            f"Размер поля: {self.value}/{self.value}\n"
            f"Количество мин: {self.count_of_mines}\n"
            f"Ост. клеток: {count_of_left}",
        )

    def update_square(self, row, col, restart):
        if not self.first_move or restart:
            square_number = row * self.value + col
            square = self.buttons[square_number]
            content = self.map[row][col]
            if (row, col) not in self.checked and \
                    not self.lose_detect:
                square.setText("")
            elif content == "*":
                square.setText("")
            else:
                if (row, col) in self.checked:
                    if content != "0":
                        square.setText(str(content))
            if (row, col) in self.checked:
                if content.isdigit():
                    if content == "1":
                        color = "#0000b3"
                    elif content == "2":
                        color = "#00b33c"
                    elif content == "3":
                        color = "#b32400"
                    elif content == "4":
                        color = "#000066"
                    else:
                        color = "#000000"
                    square.setStyleSheet(
                        f"color: {color};" f"font-size: 30px;",
                    )
            else:
                square.setStyleSheet("background-color: #c7c5c5;")
            if content == "*":
                square.setText("")
                if self.lose_detect is True:
                    square.setStyleSheet(
                        "background-color: #ff8585;",
                    )
                    if square_number == self.last_lose_square:
                        square.setStyleSheet(
                            "background-color: #fc4e4e;",
                        )

    def update_squares(self, restart=False):
        try:
            self.update_texts()
            for row in range(self.value):
                for col in range(self.value):
                    self.update_square(row, col, restart)
        except Exception as e:
            print(e, "update_squares")

    def on_square_clicked(self, row, col, user_click):
        try:
            if self.first_move:
                self.generate_mines(row * self.value + col)
                self.first_move = False

            # Добавлено условие, чтобы игрок не мог открывать клетки,
            # когда игра закончена
            if not self.win_detect and not self.lose_detect:
                square = row * self.value + col
                if square not in self.MINES and user_click or self.anti_lose:
                    self.open_cell(square)
                elif user_click:
                    self.lose(square)
                self.update_squares()
        except Exception as e:
            print(e)

    def generate_mines(self, first_click):
        board = [i for i in range(self.value * self.value)]
        board.remove(first_click)
        mines = random.sample(board, self.count_of_mines)
        for mine in mines:
            self.MINES.append(mine)
            row, col = mine // self.value, mine % self.value
            self.map[row][col] = "*"

    def open_cell(self, square):
        i, j = square // self.value, square % self.value
        if (i, j) in self.checked:
            return
        self.checked.add((i, j))
        if square in self.MINES:
            self.map[i][j] = "*"
            self.lose(square)
            return
        count = self.get_surrounding_mines(i, j)
        self.map[i][j] = str(count)
        if count == 0:
            for ni, nj in self.get_neighbors(i, j):
                self.open_cell(ni * self.value + nj)
        self.check_win()

    def lose(self, square):
        self.stop_timer()
        if self.anti_lose:
            i, j = square // self.value, square % self.value
            self.map[i][j] = "0"
        else:
            self.lose_detect = True
            self.last_lose_square = square
            for i in range(self.value):
                for j in range(self.value):
                    if i * self.value + j in self.MINES:
                        self.map[i][j] = "*"

            for mine in self.MINES:
                self.buttons[mine].setIcon(QIcon("data/bomb.png"))
            self.buttons[square].setIcon(QIcon("data/boom.png"))

        self.update_squares()

    def check_win(self):
        for i in range(self.value):
            for j in range(self.value):
                if (
                        self.map[i][j] == "."
                        and (i * self.value + j) not in self.MINES
                ):
                    return False
        self.win()
        return True

    def win(self):
        self.set_to_database()

        self.win_detect = True
        self.update_squares()

    def set_to_database(self):
        try:
            difference = self.time
            date = str(self.date_start).split("-")
            date = f"{date[2]}-{date[1]}-{date[0]}"
            with sqlite3.connect("data/database.db") as connect:
                cursor = connect.cursor()

                sql = f"""
                INSERT INTO board(value, mines, time, date)
                VALUES ("{self.value}",
                "{self.count_of_mines}",
                "{difference}",
                "{date}")
                """

                cursor.execute(sql)
                connect.commit()
        except Exception as e:
            print(e)

    def get_surrounding_mines(self, row, col):
        mines = 0
        for r in range(max(0, row - 1), min(self.value - 1, row + 1) + 1):
            for c in range(max(0, col - 1), min(self.value - 1, col + 1) + 1):
                if self.map[r][c] == ".":
                    continue
                if self.map[r][c] == "*":
                    mines += 1
        return mines

    def get_neighbors(self, row, col):
        neighbors = []
        for r in range(max(0, row - 1), min(self.value - 1, row + 1) + 1):
            for c in range(max(0, col - 1), min(self.value - 1, col + 1) + 1):
                if r == row and c == col:
                    continue
                neighbors.append((r, c))
        return neighbors

    def setting_slyders(self):
        # /============= Слайдер размера поля =============\
        self.S_setting_value.setValue(10)
        self.S_setting_value.setPageStep(
            5,
        )  # <--- Это свойство содержит шаг страницы.

        self.S_setting_value.setTickInterval(5)
        self.S_setting_value.setRange(5, 15)
        self.S_setting_value.setFocusPolicy(Qt.StrongFocus)
        self.S_setting_value.setTickPosition(QSlider.TicksBothSides)
        self.S_setting_value.setSingleStep(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.S_setting_value)
        self.setLayout(vbox)

        self.S_setting_value.valueChanged[int].connect(
            self.LCD_setting_value.display,
        )
        self.S_setting_value.valueChanged.connect(self.change_value)
        self.LCD_setting_value.display(10)
        # \============= Слайдер размера поля =============/

        # /============= Слайдер количества мин =============\
        self.S_setting_count.setValue(15)
        self.S_setting_count.setPageStep(
            5,
        )  # <--- Это свойство содержит шаг страницы.

        self.S_setting_count.setTickInterval(5)
        self.S_setting_count.setRange(5, 25)
        self.S_setting_count.setFocusPolicy(Qt.StrongFocus)
        self.S_setting_count.setTickPosition(QSlider.TicksBothSides)
        self.S_setting_count.setSingleStep(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.S_setting_count)
        self.setLayout(vbox)

        self.S_setting_count.valueChanged[int].connect(
            self.LCD_setting_count.display,
        )
        self.S_setting_count.valueChanged.connect(self.change_count)
        self.LCD_setting_count.display(15)
        # \============= Слайдер количества мин =============/

    def change_value(self):
        try:
            value = int(self.LCD_setting_value.value())
            if self.count_of_mines == 25 and value == 5:
                self.S_setting_value.setValue(6)
            else:
                self.value = value
                self.size = 550 // self.value
        except Exception as e:
            print(e)

    def change_count(self):
        try:
            value = int(self.LCD_setting_count.value())
            if self.value == 5 and value == 25:
                self.S_setting_count.setValue(24)
            else:
                self.count_of_mines = value
        except Exception as e:
            print(e)

    def anti_losee(self):
        self.anti_lose = True
        self.play()

    def setting(self):
        self.B_anti_losee.setStyleSheet("border: 0px; ")
        self.B_anti_losee.clicked.connect(self.anti_losee)
        self.stackedWidget.setCurrentWidget(self.P_setting)
        self.setting_slyders()
        # /=================== BUTTON EVENT ===================\
        # Играть:
        self.B_setting_play.clicked.connect(self.play)
        # \=================== BUTTON EVENT ===================/

    def del_last_game(self):
        if self.MINES:
            for mine in self.MINES:
                self.buttons[mine].setIcon(QIcon(""))

    def set_time(self):
        self.L_3.setText(str(self.time_))

    def start_timer(self):
        if not self.is_running:
            self.timer.start(1000)
            self.is_running = True

    def stop_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False

    def update_timer(self):
        self.time += 1
        self.L_1_1.setText(str(self.time))


    def play(self):
        self.new_game()
        self.date_start = dt.datetime.now().date()
        self.timer = QTimer(self)
        self.time = 0
        self.is_running = False

        self.timer.timeout.connect(self.update_timer)

        self.start_timer()

        self.L_2_1.setText(
            f"Размер поля: {self.value}/{self.value}\n"
            f"Количество мин: {self.count_of_mines}\n"
            f"Ост. клеток: {self.value ** 2 - self.count_of_mines}",
        )

        self.stackedWidget.setCurrentWidget(self.P_play)

        self.setLayout(self.gridLayout)

        for i in range(self.value):
            for j in range(self.value):
                button = QPushButton()
                button.setMinimumSize(self.size, self.size)
                button.setMaximumSize(self.size, self.size)

                square = i * self.value + j

                button.setObjectName(f"{square}")

                self.buttons.append(button)

                self.gridLayout.addWidget(button, i, j)

                # /=================== BUTTON EVENT ===================\

                # Открыть клетку:
                button.clicked.connect(self.open_first)
                button.setStyleSheet("background-color: #c7c5c5;")

                # \=================== BUTTON EVENT ===================/

        self.B_restart.clicked.connect(self.restart_game)

        self.B_restart.setIcon(QIcon("data/restart.png"))

        self.L_1.setStyleSheet("font-size: 20px; " "color: #737373; ")

        self.L_1_1.setAlignment(Qt.AlignCenter)

        self.L_1_1.setStyleSheet(
            "font-size: 20px; " "color: #545454; " "text-align: center;",
        )

        self.L_2.setStyleSheet("font-size: 20px; " "color: #737373; ")

        self.L_2_1.setStyleSheet("font-size: 20px; " "color: #545454; ")

        self.L_3.setStyleSheet("font-size: 20px; " "color: #545454; ")

    def open_first(self):
        square = int(self.sender().objectName())
        row, col = square // self.value, square % self.value
        self.on_square_clicked(row, col, True)

    def closeEvent(self, event):  # noqa
        reply = QMessageBox.question(
            self,
            "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()
            QApplication.quit()  # добавленная строка
        else:
            event.ignore()


def create_database():
    with sqlite3.connect("data/database.db") as connect:
        cursor = connect.cursor()

        sql = """
        DROP TABLE IF EXISTS board;
        """

        cursor.execute(sql)

        sql = """
        CREATE TABLE board (
        id    INTEGER PRIMARY KEY AUTOINCREMENT
                      UNIQUE,
        value INTEGER,
        mines INTEGER,
        time  INTEGER,
        date  STRING
        );
        """

        cursor.execute(sql)

        connect.commit()


if __name__ == "__main__":
    create_database()
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.setStyleSheet("background-color: #d6d6d6;")
    mywindow.show()
    sys.exit(app.exec())

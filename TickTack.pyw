import random
import sys
from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QMainWindow, QShortcut

# Количество крестиков (ноликов) в ряд для победы
NWin = 5


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('start.ui', self)
        self.startButton.clicked.connect(self.startGame)
        self.setWindowTitle("Крестики-Нолики")
        self.label_2.setPixmap(QtGui.QPixmap("logo.png"))

    def startGame(self):
        global gamemode
        height_field = self.Height_box.value()
        width_field = self.Width_box.value()
        if self.comboBox.currentText() == 'Против компьютера':
            gamemode = 0
        else:
            gamemode = 1
        self.field = Field(height_field, width_field)
        self.field.show()


class Field(QMainWindow):
    def __init__(self, height_field, width_field):
        super(Field, self).__init__()
        # Количество строк и столбцов поля
        self.height_field, self.width_field = height_field, width_field

        # Кнопки для каждой ячейки
        self.field_buttons = list()
        # Массив содержимого ячеек. Значения: 0-пусто, 1-крестик, 2-нолик
        self.cells = list()
        # Стек сделанных ходов
        self.stack = list()
        # Чей текущий ход. 1-ходят крестики, 2-ходят нолики
        self.move = 1

        self.icon1 = QIcon("krest.png")
        self.icon1.addPixmap(QPixmap("krest.png"),
                             QtGui.QIcon.Disabled, QtGui.QIcon.Off)

        self.icon2 = QIcon("nolik.png")
        self.icon2.addPixmap(QPixmap("nolik.png"),
                             QtGui.QIcon.Disabled, QtGui.QIcon.Off)

        self.shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut.activated.connect(self.undo)

        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 30 * self.width_field,
                         30 * self.height_field)
        self.setWindowTitle("Крестики-Нолики")
        self.setWindowIcon(self.icon1)
        self.makeField()
        self.show()

    # Создание поля
    def makeField(self):
        for y in range(self.height_field):
            self.field_buttons.append([None] * self.width_field)
            self.cells.append([0] * self.width_field)
            for x in range(self.width_field):
                self.field_buttons[y][x] = QPushButton(self)
                self.field_buttons[y][x].resize(30, 30)
                self.field_buttons[y][x].move(x * 30, y * 30)
                self.field_buttons[y][x].setText("")
                self.field_buttons[y][x].xy = x, y
                self.field_buttons[y][x].clicked.connect(self.ManualMove)

    # Проверка координат ячейки на валидность (попадание в поле)
    def is_valid(self, y, x):
        return 0 <= y < self.height_field and 0 <= x < self.width_field

    # Делает ход в ячейку. move - кристик (1) или нолик (2)
    def paintMove(self, y, x, move):
        if move == 1:
            self.field_buttons[y][x].setIcon(self.icon1)
            self.cells[y][x] = move
        else:
            self.field_buttons[y][x].setIcon(self.icon2)
            self.cells[y][x] = move

        self.field_buttons[y][x].setEnabled(False)

    # Для заданной ячейки (y, x) возвращает все локации, в которых она участвует.
    # Локация - это пятерка смежных ячеек
    def get_locations(self, y, x):
        locations = []
        locations.extend(self.get_direction_locations(y, x, 0, 1))
        locations.extend(self.get_direction_locations(y, x, 1, 0))
        locations.extend(self.get_direction_locations(y, x, 1, 1))
        locations.extend(self.get_direction_locations(y, x, -1, 1))

        return locations

    # Для заданной ячейки (y, x) возвращает все локации одного направления, задаваемого смещениями dy, dx.
    # Кроме пятерки в последних двух элементах локации хранятся граничные элементы - начальный и конечный
    def get_direction_locations(self, y, x, dy, dx):
        locations = []
        for t in range(NWin):
            location = []
            for k in range(NWin):
                y1 = y + (k - t) * dy
                x1 = x + (k - t) * dx
                if self.is_valid(y1, x1):
                    location.append((x1, y1, self.cells[y1][x1]))
                else:
                    break
            # Локация полностью набрана
            else:
                # Добавляем начальный граничный элемент, если он есть
                y2 = location[0][1] - dy
                x2 = location[0][0] - dx
                if self.is_valid(y2, x2):
                    location.append((x2, y2, self.cells[y2][x2]))
                else:
                    location.append(None)

                # Добавляем конечный граничный элемент, если он есть
                y2 = location[-2][1] + dy
                x2 = location[-2][0] + dx
                if self.is_valid(y2, x2):
                    location.append((x2, y2, self.cells[y2][x2]))
                else:
                    location.append(None)

                locations.append(location)
        return locations

    # Выполняет ход в ячейку (y, x) текущим игроком и передает ход партнеру
    def MoveTo(self, y, x):
        self.stack.append((y, x, self.move))
        self.paintMove(y, x, self.move)
        if self.checkWin(y, x):
            self.close()
        self.move = 3 - self.move

    # Обработчик ручного (сделанного мышкой) хода
    def ManualMove(self):
        x, y = self.sender().xy
        if self.is_valid(y, x):
            self.MoveTo(y, x)
            if gamemode == 0:
                QTimer.singleShot(10, self.AutoMove)

    # Автоматический ход
    def AutoMove(self):
        (y, x) = self.think()
        if self.is_valid(y, x):
            self.MoveTo(y, x)

    # Отмена хода
    def undo(self):
        # if gamemode == 1:
        if len(self.stack) == 0:
            return
        (y, x) = (self.stack[-1][0], self.stack[-1][1])
        self.field_buttons[y][x].setIcon(QIcon())
        self.field_buttons[y][x].setEnabled(True)
        self.cells[y][x] = 0
        self.stack.pop()
        self.move = 3 - self.move

    # Проверка победителя в окрестностях ячейки (row, col)
    def checkWin(self, row, col):
        locations = self.get_locations(row, col)
        for location in locations:
            for i in range(NWin):
                if location[i][2] != self.move:
                    break
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Игра закончена!")
                if self.move == 1:
                    msg.setText("Победили крестики!")
                else:
                    msg.setText("Победили нолики!")
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec()
                return True
        return False

    # Определение оптимального хода
    def think(self):
        Row = self.height_field // 2
        Col = self.width_field // 2
        Wmax = 0  # Лучшее нападение
        Tmax = 0  # Лучшее нападение+защита
        # Оценим каждую пустую ячейку на поле
        for row in range(self.height_field):
            for col in range(self.width_field):
                if (self.cells[row][col] == 0):
                    # W - нападение, D - защита

                    cell_w = cell_d = 0
                    no_dir = 0
                    for dir in ((0, 1), (1, 0), (1,1), (-1,1)):
                        locations = self.get_direction_locations(row, col, dir[0], dir[1])
                        dir_w = dir_d = 0
                        for location in locations:
                            (loc_w, loc_d) = self.rateLocation(location)
                            # if loc_w + loc_d > dir_w + dir_d or (loc_w + loc_d > dir_w + dir_d and loc_w > dir_w):
                                # dir_w = loc_w
                                # dir_d = loc_d
                            dir_w += loc_w
                            dir_d += loc_d
                        
                        if dir_w or dir_d:
                            no_dir += 1
                            cell_w += dir_w
                            cell_d += dir_d

                    # (W, D) = self.rateCell(row, col)


                    (W, D) = (cell_w, cell_d)
                    if no_dir:
                        if W:
                            W += 2**(no_dir - 1)
                        else:
                            D += 2**(no_dir - 1)
                    # Нападение имеет приоритет над защитой
                    if W + D > Tmax or (W + D == Tmax and W > Wmax):
                        Tmax = W + D
                        Wmax = W
                        Row = row
                        Col = col
                    # Если попалась равносильная ячейка, выбираем случайно
                    elif W + D == Tmax:
                        if random.randint(1, 2) == 1:
                            Row = row
                            Col = col

        return (Row, Col)

    # Оценивает ход в ячейку (row, col)
    def rateCell(self, row, col):
        locations = self.get_locations(row, col)
        W, D = 0, 0
        for location in locations:
            (w, d) = self.rateLocation(location)
            W += w
            D += d

        return (W, D)

    # Оценивает локацию с точки зрения возможного хода
    def rateLocation(self, location):
        # W - нападение, D - защита
        W = D = 0

        for i in range(NWin):
            if location[i][2] == self.move:
                W += 1
                D -= 100
            elif location[i][2] == 3 - self.move:
                W -= 100
                D += 1

        # Если заперты на границах, нужно назначить штраф
        if location[-2] is not None:
            if W < 4 and location[-2][2] == 3 - self.move and location[0][2] == self.move:
                W -= 1
            if D < 4 and location[-2][2] == self.move and location[0][2] == 3 - self.move:
                D -= 1

        if location[-1] is not None:
            if W < 4 and location[-1][2] == 3 - self.move and location[4][2] == self.move:
                W -= 1
            if D < 4 and location[-1][2] == self.move and location[4][2] == 3 - self.move:
                D -= 1

        # Нападение должно иметь больший вес (11>10), иначе будет попадать в ловушку квадратом.
        W = 11**(W - 1) if W > 0 else 0
        D = 10**(D - 1) if D > 0 else 0

        return (W, D)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())

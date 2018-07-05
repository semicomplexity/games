import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout, QAbstractButton, QLabel, QLCDNumber
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtCore import pyqtSlot, QTimer
import numpy as np

class PicButton(QAbstractButton):
    def __init__(self, image_no, i, j, on_click=None, parent=None):
        super(PicButton, self).__init__(parent)
        if image_no == 0:
            filename = 'images/empty_card.gif'
        else:
            filename = 'images/{}.gif'.format(image_no)
        self.pixmap = QPixmap(filename)
        self.click_function = on_click
        if on_click:
            self.clicked.connect(self.on_click)
        self.image_no = image_no
        self.i = i
        self.j = j

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

    def on_click(self):
        self.click_function(self.image_no)

    def replace(self, image_no):
        if image_no == 0:
            filename = 'images/empty_card.gif'
        else:
            filename = 'images/{}.gif'.format(image_no)
        self.pixmap = QPixmap(filename)
        self.image_no = image_no
        self.update()

class PlayArea(QWidget):

    def __init__(self, click_card):
        super().__init__()
        self.selected = {}
        # self.cards = np.random.permutation(range(1, self.total_number_of_cards + 1))
        self.click_card = click_card
        self.no_of_cards_so_far = 0
        self.cards_on_table = []
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        self.pic_buttons = []

        self.setLayout(self.grid)

    def start_game(self, cards):
        count = 0
        positions = {}
        for i in range(4):
            for j in range(3):
                n = cards[count]
                count += 1
                p = PicButton(n, i, j, self.click_card)
                self.pic_buttons.append(p)
                self.grid.addWidget(p, i, j)
                positions[n] = (i, j)
        return positions
    
    def replace_card(self, pos, card):
        index = int(pos[0] * 3 + pos[1])
        self.pic_buttons[index].replace(card)

    def add_extra_cards(self, cards):
        i = len(self.pic_buttons) / 3
        positions = {}
        for j, card in enumerate(cards):
            p = PicButton(card, i, j, self.click_card)
            self.pic_buttons.append(p)
            self.grid.addWidget(p, i, j)
            positions[card] = (i, j)
        return positions

    def remove(self, card, pos):
        pos_index = int(pos[0] * 3 + pos[1])
        print('Removing card in position {}'.format(pos))
        self.pic_buttons[pos_index].deleteLater()

    def move(self, card, cur_pos, new_pos):
        print('Moving {} from {} to {}'.format(card, cur_pos, new_pos))
        cur_pos_index = int(cur_pos[0] * 3 + cur_pos[1])
        # self.pic_buttons[cur_pos_index].replace(0)
        self.pic_buttons[cur_pos_index].deleteLater()
        new_pos_index = int(new_pos[0] * 3 + new_pos[1])
        self.pic_buttons[new_pos_index].replace(card)

    def cleanup_buttons(self, number_of_cards_removed):
        for i in range(number_of_cards_removed):
            # self.pic_buttons[-1].deleteLater()
            self.pic_buttons.pop()


class SelectedCards(QWidget):

    def __init__(self, cards=None):
        super().__init__()
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(10)
        self.buttons = []

        for i in range(3):
            p = PicButton(0, 0, i)
            self.buttons.append(p)
            grid.addWidget(p, 0, i)

        self.setLayout(grid)

    def replace(self, cards):
        for p, new_card in dict(zip(self.buttons, cards)).items():
            p.replace(new_card)

    def replace_one(self, i, card):
        self.buttons[i].replace(card)

class ScoringArea(QWidget):

    def __init__(self, number_of_cards, call_backs):
        super().__init__()
        self.previous_selection = [0, 0, 0]
        self.current_selection = [0, 0, 0]
        self.call_backs = call_backs
        self.number_of_cards = number_of_cards
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel('Previous Selection:'), 0, 0)
        self.prev_selection_buttons = SelectedCards()
        grid.addWidget(self.prev_selection_buttons, 1, 0)

        grid.addWidget(QLabel('CurrentSelection:'), 3, 0)
        self.current_selection_buttons = SelectedCards()
        grid.addWidget(self.current_selection_buttons, 4, 0)

        self.no_set_button = QPushButton("No set",self)
        self.no_set_button.clicked.connect(self.call_backs['no_set'])

        grid.addWidget(self.no_set_button, 6, 0)
        self.my_timer = MyTimer({'start_game': self.call_backs['start_game']})
        self.counter = Counter(self.number_of_cards)
        grid.addWidget(self.my_timer, 8, 0, 10, 0)
        grid.addWidget(self.counter, 14, 1, 15, 1)

        self.setLayout(grid)
    
    def update_counter(self, cards_played):
        self.counter.update_counter(cards_played)

    def stop_timer(self):
        self.my_timer.timer.stop()

    def new_selection(self, cards):
        self.prev_selection_buttons.replace(self.current_selection)
        self.current_selection_buttons.replace(cards)
        self.current_selection = cards

    def start_selection(self, card):
        self.prev_selection_buttons.replace(self.current_selection)
        self.current_selection_buttons.replace([card, 0, 0])
        self.current_selection = [card]

    def add_selection(self, card):
        self.current_selection_buttons.replace_one(len(self.current_selection), card)
        self.current_selection.append(card)

    def remove_selection(self, card):
        self.current_selection.remove(card)
        self.current_selection_buttons.replace(self.current_selection + [0] * (3 - len(self.current_selection)))

    def no_set(self):
        self.play_area.no_set()

    def set_play_area(self, play_area):
        self.play_area = play_area

class Counter(QWidget):

    def __init__(self, number_of_cards):
        super().__init__()
        self.cards_left = number_of_cards
        self.initUI()

    def initUI(self):
        self.lcd = QLCDNumber(self)
        grid = QGridLayout()
        grid.addWidget(self.lcd, 1, 0)
        self.setLayout(grid)

        self.display()

    def update_counter(self, cards_played):
        self.cards_left -= cards_played
        self.display()

    def display(self):
        to_display = "{}".format(self.cards_left)
        self.lcd.setDigitCount(len(to_display))
        self.lcd.display(to_display)

class MyTimer(QWidget):

    def __init__(self, call_backs):
        super().__init__()
        self.seconds = 0
        self.minutes = 0
        self.call_backs = call_backs
        self.initUI()

    def initUI(self):

        self.lcd = QLCDNumber(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Time)

        self.start = QPushButton("Start",self)
        self.start.clicked.connect(self.Start)
        self.stop = QPushButton("Stop",self)
        self.stop.clicked.connect(lambda: self.timer.stop())
        self.reset = QPushButton("Reset",self)
        self.reset.clicked.connect(self.Reset)

        grid = QGridLayout()

        grid.addWidget(self.start, 1, 0)
        grid.addWidget(self.stop, 1, 1)
        grid.addWidget(self.reset, 1, 2)
        grid.addWidget(self.lcd, 2, 0)

        self.setLayout(grid)

    def Reset(self):
        self.timer.stop()
        self.seconds, self.minutes = 0, 0
        time = "{0}:{1}".format(self.minutes, self.seconds)
        self.lcd.setDigitCount(len(time))
        self.lcd.display(time)
 
    def Start(self):
        self.call_backs['start_game']()
        self.timer.start(1000)
     
    def Time(self):
        if self.seconds < 59:
            self.seconds += 1
        else:
            self.seconds = 0
            self.minutes += 1

        time = "{0}:{1}".format(self.minutes, self.seconds)
        self.lcd.setDigitCount(len(time))
        self.lcd.display(time)

class MainGrid(QWidget):

    def __init__(self):
        super().__init__()
        self.total_number_of_cards = 81
        self.initVars()
        self.initUI()

    def initVars(self):
        self.cards = np.random.permutation(range(1, self.total_number_of_cards + 1))
        self.cards_on_table = []
        self.card_positions = {}
        self.cards_selected = []
        self.cards_played_so_far = 0

    def start_game(self):
        self.cards_on_table = self.cards[:12]
        self.card_positions = self.playing_area.start_game(self.cards_on_table)
        self.cards_played_so_far = 12
        self.scoring_area.update_counter(12)

    def click_card(self, n):
        if n == 0:
            return
        cs = self.cards_selected
        if n in cs:
            self.scoring_area.remove_selection(n)
            cs.remove(n)
            return
        cs.append(n)
        if len(cs) == 1:
            self.scoring_area.start_selection(n)
        else:
            self.scoring_area.add_selection(n)
        if len(cs) == 3:
            is_it_a_set = self.is_set(cs, True)
            if is_it_a_set and self.cards_played_so_far < self.total_number_of_cards:
                if len(self.cards_on_table) > 12:
                    cards_to_be_moved = self.cards_on_table[-3:]
                    last_row_selection = np.array([])
                    for card in cards_to_be_moved:
                        if card in cs:
                            last_row_selection = np.append(last_row_selection, card)
                            card_index = np.where(self.cards_on_table == card)[0][0]
                            cards_to_be_moved = np.delete(cards_to_be_moved, np.where(cards_to_be_moved == card)[0][0])
                            pos = self.card_positions[card]
                            self.playing_area.remove(card, pos)
                    if len(cards_to_be_moved) > 0:
                        count = 0
                        for card in cs:
                            if card not in last_row_selection:
                                current_pos = self.card_positions[cards_to_be_moved[count]]
                                new_pos = self.card_positions[card]
                                self.playing_area.move(cards_to_be_moved[count], current_pos, new_pos)
                                self.card_positions[cards_to_be_moved[count]] = new_pos
                                count += 1
                else:
                    ix = self.cards_played_so_far
                    for i in range(3):
                        pos = self.card_positions[cs[i]]
                        new_card = self.cards[ix + i]
                        self.card_positions[new_card] = pos
                        self.playing_area.replace_card(pos, new_card)
                        self.cards_on_table = np.append(self.cards_on_table, new_card)
                    self.scoring_area.update_counter(3)
                    self.cards_played_so_far += 3

                # Delete the selected cards from the table and also delete their positions
                for card in cs:
                    card_index = np.where(self.cards_on_table == card)[0][0]
                    self.cards_on_table = np.delete(self.cards_on_table, card_index)
                    del self.card_positions[card]
            elif is_it_a_set:
                for card in cs:
                    card_index = np.where(self.cards_on_table == card)[0][0]
                    pos = self.card_positions[card]
                    del self.card_positions[card]
                    self.playing_area.replace_card(pos, 0)
                    self.cards_on_table[card_index] = 0
            else:
                print('Not a set')
            self.cards_selected = []

    def is_set(self, cards, to_change=False):
        if to_change:
            pass
            #self.scoring_area.new_selection(cards)
        def check_last_digit(x, y, z):
            a = x % 3
            b = y % 3
            c = z % 3
            if a == b and a == c:
                return True, (x - a) / 3, (y - b) / 3, (z - c) / 3
            if a != b and a != c and b != c:
                return True, (x - a) / 3, (y - b) / 3, (z - c) / 3
            return False, x, y, z
        check, x, y, z = check_last_digit(cards[0] - 1, cards[1] - 1, cards[2] - 1)
        count = 1
        while check and count < 4:
            check, x, y, z = check_last_digit(x, y, z)
            count += 1
        if check and count == 4:
            return True
        return False

    def no_set(self):
        c = []
        for card in self.cards_on_table:
            if card > 0:
                c.append(card)
        n = len(c)
        set_exists = False
        for i in range(n - 2):
            for j in range(i + 1, n - 1):
                for k in range(j + 1, n):
                    if self.is_set([c[i], c[j], c[k]]):
                        print('There is a set: {}, {}, {}'.format(c[i], c[j], c[k]))
                        set_exists = True
                        break
                if set_exists:
                    break
            if set_exists:
                break
        if not set_exists:
            print('Indeed there are no sets')
            if self.cards_played_so_far == self.total_number_of_cards:
                print('End of game')
                self.scoring_area.stop_timer()
            else:
                self.add_three_extra_cards()

    def add_three_extra_cards(self):
        ix = self.cards_played_so_far
        extra_cards = self.cards[[ix, ix + 1, ix + 2]]
        self.cards_played_so_far += 3
        new_positions = self.playing_area.add_extra_cards(extra_cards)
        for i, pos in new_positions.items():
            self.card_positions[i] = pos
        for card in extra_cards:
            self.cards_on_table = np.append(self.cards_on_table, card)
        self.scoring_area.update_counter(3)

    def initUI(self):

        grid = QGridLayout()
        grid.setSpacing(10)

        call_backs = {
                'start_game': self.start_game,
                'no_set': self.no_set
                }
        self.scoring_area = ScoringArea(self.total_number_of_cards, call_backs)
        self.playing_area = PlayArea(self.click_card)
        self.scoring_area.set_play_area(self.playing_area)
        grid.addWidget(self.scoring_area, 0, 1)
        grid.addWidget(self.playing_area, 0, 0)


        self.setLayout(grid)
        self.show()

def main():
    app = QApplication(sys.argv)
    mg = MainGrid()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

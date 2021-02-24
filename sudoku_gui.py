from dataclasses import dataclass
from itertools import cycle
from sudoku import Sudoku
import pygame
import json
import os


class Timer:
    """
    Custom class for time counting
    """
    def __init__(self):
        self._start = 0
        self._time = 0
        self._pause_time = 0
        self._unpause_time = 0
        self._paused = True
        self._stopped = False

    def pause(self):
        """
        Pause time counting (used for user-initiated stopping)
        """
        self._pause_time = self._start - (self._unpause_time - pygame.time.get_ticks())
        self._time += self._pause_time
        self._paused = True

    def unpause(self):
        """
        Unpause time counting
        """
        self._unpause_time = pygame.time.get_ticks() - self._start
        self._paused = False

    def reset(self):
        """
        Resets the time counting
        """
        self._start = 0
        self._time = 0
        self._pause_time = 0
        self._unpause_time = 0
        self._stopped = False

    def stop(self):
        """
        Stops time counting (used for non-user-initiated stopping)
        """
        if not self._stopped:
            stopped_time = self._start - (self._unpause_time - pygame.time.get_ticks())
            self._time += stopped_time
            self._stopped = True

    @property
    def current(self) -> int:
        """
        Getter for current time of counter

        :return: current time of counter (in ms)
        """
        if self._paused or self._stopped:
            return self._time
        return self._time + pygame.time.get_ticks() - self._unpause_time

    @property
    def current_prettified(self) -> str:
        """
        Getter for current time of counter (in format mm:ss)

        :return: current time of counter (mm:ss)
        """
        minutes = str(int((self.current / 1000) // 60)).rjust(2, "0")
        seconds = str(int((self.current / 1000) % 60)).rjust(2, "0")
        return f'{minutes}:{seconds}'

    @property
    def paused(self) -> bool:
        """
        Return if the counter is currently stopped

        :return: True if counter is paused, False otherwise
        """
        return self._paused

    @staticmethod
    def prettify(time_: int) -> str:
        """
        Returns the prettified version of time

        :param time_: time to prettify (in ms)
        :return: time in format MM:SS
        """
        minutes = str(int((time_ / 1000) // 60)).rjust(2, "0")
        seconds = str(int((time_ / 1000) % 60)).rjust(2, "0")
        return f'{minutes}:{seconds}'


class Screen:
    """
    Class for creating pygame window
    """
    def __init__(self, title: str, width: int, height: int, icon: pygame.Surface = None):
        """
        :param title: the title of the window
        :param width: the width of the window
        :param height: the height of the window
        :param icon: the icon of the window
        """
        self._title = title
        self._width = width
        self._height = height
        self._icon = icon
        self._current = False

    def make_current(self) -> pygame.display:
        """
        Enable the pygame window

        :return: a pygame display object
        """
        pygame.display.set_caption(self._title)
        self._current = True
        screen = pygame.display.set_mode((self._width, self._height))
        if self._icon:
            pygame.display.set_icon(self._icon)
        return screen

    def end_current(self):
        """
        Disable the pygame window
        """
        self._current = False

    def check_if_current(self) -> bool:
        """
        Checks if the window is currently active

        :return: True if the window is active, False otherwise
        """
        return self._current

    def update_title(self, title: str):
        """
        Replaces the window's title with the given one

        :param title: the new title of a window
        """
        self._title = title

    def __str__(self):
        return f'Screen {self._title} ({self._width}x{self._height}), active: {self._current}'


class Button:
    """
    Class for creating the button
    """
    def __init__(self, position: tuple, size: tuple = None, border: int = 0, border_color: tuple = (0, 0, 0),
                 color: tuple = (255, 255, 255), image_path: str = None, image_size: tuple = None, text: str = None,
                 font: str = "calibri", font_size: int = 18, text_color: tuple = (0, 0, 0), center_text: bool = False,
                 clickable: bool = True):
        """
        :param position: the position of the button on the screen (x, y)
        :param size: the size of the button (x, y) - required if the button will not contain text
        :param border: the border size of the button
        :param border_color: the border color of the button (RGB)
        :param color: the background color of the button (RGB)
        :param image_path: a path to the button's background image
        :param image_size: the size of the button's background image
        :param text: the text that will be displayed on the button
        :param font: the font of the text
        :param font_size: the size of the font
        :param text_color: the color of the text (RGB)
        :param clickable: if the button is interactive or not
        """
        self._font = pygame.font.SysFont(font, font_size)
        self._text_color = text_color
        self._text = text
        self._text_position = (0, 0)
        self._center_text = center_text
        self._color = color
        self._position = tuple(x - border for x in position)
        # determining the size of the surface
        if size:
            self._size = tuple(x + border * 2 for x in size)
        elif text and not (image_size and image_path):
            self._size = tuple(x + border * 2 for x in self._font.size(text))
        elif text and image_size and image_path:
            self._size = (self._font.size(text)[0] + image_size[0] + border * 2,
                          max(self._font.size(text)[1], image_size[1]) + border * 2)
        self._border = border
        self._border_color = border_color
        self._image = None
        self._image_path = image_path
        self._image_size = image_size if image_size else self._size
        self._clickable = clickable
        self._surface = pygame.Surface(self._size, flags=pygame.SRCALPHA)
        self._surface.fill(color)
        if text:
            self._draw_text()
        if border:
            self._draw_border()
        if image_path:
            self._draw_image()
        else:
            self._rect = pygame.Rect(position, self._size)

    def __str__(self):
        return f'Button pos. {self._position}'

    def _draw_image(self):
        """
        Draws the image on the button surface
        """
        self._image = pygame.image.load(self._image_path)
        self._image = pygame.transform.scale(self._image, self._image_size)
        self._rect = self._image.get_rect(center=tuple(x / 2 for x in self._size)).move(*self._position)
        self._surface.blit(self._image, tuple((x - y) / 2 for x, y in zip(self._size, self._image_size)))

    def _draw_text(self):
        """
        Draws the text on the button surface
        """
        text = self._font.render(self._text, True, self._text_color)
        if self._center_text:
            self._text_position = tuple((x - y) / 2 for x, y in zip(self._size, text.get_size()))
        self._surface.blit(text, self._text_position)

    def _draw_border(self):
        """
        Draws the border on the button surface
        """
        # left border
        pygame.draw.rect(self._surface, self._border_color, pygame.Rect((0, 0), (self._border, self._size[1])))
        # right border
        pygame.draw.rect(self._surface, self._border_color, pygame.Rect((self._size[0] - self._border, 0),
                                                                        (self._border, self._size[1])))
        # top border
        pygame.draw.rect(self._surface, self._border_color, pygame.Rect((0, 0), (self._size[0], self._border)))
        # bottom border
        pygame.draw.rect(self._surface, self._border_color, pygame.Rect((0, self._size[1] - self._border),
                                                                        (self._size[0], self._border)))

    @property
    def surface(self) -> pygame.Surface:
        """
        Getter for the button Surface object

        :return: button in a form of a pygame Surface object
        """
        return self._surface

    @property
    def size(self) -> tuple:
        """
        Getter for button size (including borders)

        :return: the size of the button (x, y)
        """
        return self._size

    @property
    def position(self) -> tuple:
        """
        Getter for button position

        :return: the position of the button (x, y)
        """
        return self._position

    @property
    def text(self) -> str:
        """
        Getter for the text of the button

        :return: the text of the button (returns None if the text was not provided)
        """
        return self._text

    def clickable(self, clickable: bool):
        """
        Determines if the button is allowed to click or not

        :param clickable: True if the button has to be clickable, False otherwise
        """
        self._clickable = clickable

    def check_collision(self, pos: tuple) -> int:
        """
        Checks if the given coordinates are within the button

        :param pos: the coordinates to check
        :return: 1 if the given point is within the button, 0 otherwise
        """
        return self._rect.collidepoint(pos) if self._clickable else 0

    def update_text(self, text: str = None, text_color: tuple = None):
        """
        Replaces the text-related parameters on the button with the given ones

        :param text: the new text to replace the old one
        :param text_color: the new color of the text (RGB)
        """
        self._surface.fill(self._color)
        self._text = text if text else self._text
        self._text_color = text_color if text_color else self._text_color
        self._draw_text()
        if self._border:
            self._draw_border()
        if self._image_path:
            self._draw_image()

    def update_color(self, color: tuple = None, border_color: tuple = None):
        """
        Replaces the background and/or border color of the button

        :param color: the new background color of the button (RGB)
        :param border_color: the new border color of the button (RGB)
        """
        self._surface.fill(self._color)
        self._color = color if color else self._color
        self._border_color = border_color if border_color else self._border_color
        if self._border:
            self._draw_border()
        if self._text:
            self._draw_text()
        if self._image_path:
            self._draw_image()

    def update_image(self, image_path: str = None, image_size: tuple = None):
        """
        Replaces the button image and/or its size with the given ones

        :param image_path: the path to the new image
        :param image_size: the new size of the button image
        """
        self._surface.fill(self._color)
        self._image_path = image_path if image_path else self._image_path
        self._image_size = image_size if image_size else self._image_size
        if self._border:
            self._draw_border()
        if self._text:
            self._draw_text()
        self._draw_image()

    def update_position(self, position: tuple):
        """
        Updates the position of the button

        :param position: the new position of the button
        """
        self._surface.fill(self._color)
        self._position = position

        if self._border:
            self._draw_border()
        if self._text:
            self._draw_text()
        if self._image_path:
            self._draw_image()
        else:
            self._rect = pygame.Rect(self._position, self._size)


@dataclass
class SudokuSquare:
    """
    Class representing the single square on the board
    """
    rect: pygame.Rect
    color: tuple
    selected: bool
    at_intersection: bool
    same_value: bool
    row: int
    col: int
    value: int

    def __init__(self, rect: pygame.Rect, color: tuple, selected: bool, at_intersection: bool, same_value: bool,
                 row: int, col: int, value: int):
        """
        :param rect: pygame Rect class, used to describe the size and the position on the board
        :param color: background color of the square
        :param selected: indicates if the square is currently selected
        :param at_intersection: indicates if the square is in the same 3x3 square, row or column as the selected one
        :param same_value: indicates if the square has the same value as the selected one
        :param row: row number of the square
        :param col: column number of the square
        :param value: the number contained in the square (0 if is empty)
        """
        self.rect = rect
        self.color = color
        self.selected = selected
        self.at_intersection = at_intersection
        self.same_value = same_value
        self.value = value
        self.row = row
        self.col = col
        self.notes = []
        # if the square contains the number at the beginning, it is uneditable
        self.editable = False if self.value != 0 else True
        # if the number in the square collides with any other one
        self.is_wrong = False

    def __str__(self):
        return f'Square ({self.row},{self.col}), value {self.value}'


@dataclass
class Move:
    """
    Class representing the single operation on the sudoku board
    """
    def __init__(self, prev_number: int, prev_notes: list, row: int, col: int):
        """
        :param prev_number: the number in the square before the change
        :param prev_notes: the notes in the square before the change
        :param row: row of the changed square
        :param col: col of the changed square
        """
        self.prev_number = prev_number
        self.prev_notes = prev_notes
        self.row = row
        self.col = col

    def __str__(self):
        return f'Changed {self.prev_number} (notes {self.prev_notes}) on row {self.row}, column {self.col}'


class SudokuGUI:
    """
    Class for creating GUI version of class Sudoku
    """
    def __init__(self):
        # colors as the RGB codes
        self._COLORS = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "gray": (105, 105, 105),
            "lightgray": (211, 211, 211),
            "blue": (0, 0, 128),
            "lightblue": (135, 206, 250),
            "green": (34, 139, 34),
            "lightgreen": (152, 251, 152),
            "orange": (255, 165, 0),
            "red": (255, 0, 0),
            "darkred": (150, 0, 0),
            "lightred": (250, 100, 100),
        }

        # numeric keys codes used in pygame
        self._PY_TO_NUM = {x + 48: x for x in range(1, 10)}
        self._PY_TO_NUM.update({x + 1073741912: x for x in range(1, 10)})
        self._NUM_TO_PY = {v: k for k, v in self._PY_TO_NUM.items()}

        # make directory for keeping statistics
        if not os.path.exists(os.path.expanduser('~/Documents/Sudoku/')):
            os.makedirs(os.path.expanduser('~/Documents/Sudoku/'))
        self._create_stats()
        self._new_record = False
        self._stats_to_save = False
        self._DIFF_TO_STATS = {i: txt for i, txt in zip(range(4), ['easy', 'medium', 'hard', 'expert'])}

        # language strings used in the game
        self._languages = cycle(('pol_PL', 'eng_EN', 'nor_NO', 'spa_ES'))
        self._strings = dict()
        self._change_language(next(self._languages), update=False)

        # screens
        self._ICON = pygame.image.load('resources/images/icon.png')
        self._SCR_WIDTH = 800
        self._SCR_HEIGHT = 600
        self._menu_scr = Screen(self._strings['menu_title'], self._SCR_WIDTH, self._SCR_HEIGHT, self._ICON)
        self._game_scr = Screen(self._strings['game_title'], self._SCR_WIDTH, self._SCR_HEIGHT, self._ICON)
        self._stats_scr = Screen(self._strings['stats_title'], self._SCR_WIDTH, self._SCR_HEIGHT, self._ICON)
        # list of screens with the corresponding loops
        self._screens = [(self._menu_scr, self._menu_loop),
                         (self._stats_scr, self._stats_loop),
                         (self._game_scr, self._game_loop)]
        self._scr = self._menu_scr.make_current()
        self._running = True

        # sudoku board init
        self._difficulty = 0
        self._sudoku_engine = Sudoku()

        # stack storing the last moves (used for undo)
        self._last_moves = []

        # board
        board_size = 504
        self._square_side = board_size / 9
        self._selected_index = (-1, -1)

        # fonts
        self._timer_fnt = pygame.font.SysFont('tahoma', 30)
        self._square_fnt = pygame.font.SysFont('calibri', 40)
        self._square_notes_fnt = pygame.font.SysFont('calibri', 18)
        self._text_fnt = pygame.font.SysFont('calibri', 40)
        self._stats_fnt = pygame.font.SysFont('calibri', 30)
        self._stats_fnt_b = pygame.font.SysFont('calibri', 30, bold=True)
        self._stats_fnt_i = pygame.font.SysFont('calibri', 30, italic=True)

        # sounds
        self._click_snd = pygame.mixer.Sound('resources/sounds/click.mp3')

        # modify the board position by changing these two offsets
        self._square_offset_x = (self._SCR_WIDTH - board_size) / 2 - self._SCR_WIDTH / 16
        self._square_offset_y = (self._SCR_HEIGHT - board_size) / 2

        # timer and its position
        self._timer = Timer()
        self._timer_x = board_size + self._square_offset_x + 25
        self._timer_y = (self._SCR_HEIGHT - board_size) / 2

        # pause image and its position
        self._pause_img = pygame.image.load('resources/images/pause_button.png')
        self._pause_img = pygame.transform.scale(self._pause_img, (200, 200))
        pause_img_offset_x = (self._square_offset_x + board_size / 2) - self._pause_img.get_width() / 2
        pause_img_offset_y = (self._square_offset_y + board_size / 2) - self._pause_img.get_height() / 2
        self._pause_img_rect = self._pause_img.get_rect().move(pause_img_offset_x, pause_img_offset_y)

        # pause button
        pause_btn_size = (38, 38)
        pause_btn_pos = (self._timer_x + 80, self._timer_y)
        self._pause_btn = Button(position=pause_btn_pos,
                                 size=pause_btn_size,
                                 image_path='resources/images/pause_button_small.png',
                                 image_size=(26, 26))

        # unpause button
        self._unpause_btn = Button(position=pause_btn_pos,
                                   size=pause_btn_size,
                                   image_path='resources/images/unpause_button_small.png',
                                   image_size=(26, 26))

        self._notes_mode = False

        # notes position withing the square
        self._NOTES_POS = {i + 1: (self._square_side / 3 * (i % 3), self._square_side / 3 * (i // 3)) for i in range(9)}

        # notes mode button
        self._notes_mode_btn = Button(position=(self._timer_x, self._timer_y + 50),
                                      text=self._get_notes_status(),
                                      font_size=18,
                                      text_color=self._COLORS['black'])

        # numbers buttons
        self._numpad_size = (136, 136)
        numpad_pos = (self._timer_x, self._timer_y + 100)
        self._numpad_btns = [Button(position=(self._numpad_size[0] / 3 * (i % 3) + numpad_pos[0],
                                              self._numpad_size[1] / 3 * (i // 3) + numpad_pos[1]),
                                    size=tuple(x / 3 for x in self._numpad_size),
                                    text=str(i + 1),
                                    font_size=30,
                                    border=1,
                                    center_text=True) for i in range(0, 9)]

        # erase button
        self._erase_btn = Button(position=(numpad_pos[0], numpad_pos[1] + self._numpad_size[1] + 25),
                                 text=self._strings['erase_btn'],
                                 font_size=20,
                                 size=(self._numpad_size[0], 25),
                                 text_color=self._COLORS["black"],
                                 center_text=True)

        # undo button
        self._undo_btn = Button(position=(numpad_pos[0], numpad_pos[1] + self._numpad_size[1] + 60),
                                text=self._strings['undo_btn'],
                                font_size=20,
                                size=(self._numpad_size[0], 25),
                                text_color=self._COLORS["black"],
                                center_text=True)

        # return to menu button
        return_btn_size = (self._numpad_size[0], 40)
        self._return_btn = Button(position=(numpad_pos[0], self._square_offset_y + board_size - return_btn_size[1]),
                                  size=(self._numpad_size[0], 40),
                                  border=2,
                                  text=self._strings['return_btn'],
                                  font_size=24,
                                  text_color=self._COLORS["black"],
                                  center_text=True)

        # lines used to draw the board
        self._lines = [[((i * self._square_side + self._square_offset_x), 0 + self._square_offset_y),
                        ((i * self._square_side + self._square_offset_x), board_size + self._square_offset_y)]
                       for i in range(10)]

        # flag determining presence of the Continue button in main menu
        self._continue = False

        # menu buttons
        self._menu_btn_spacing = 15
        self._menu_btn_size = (300, 100)
        self._continue_btn = Button(position=(0, 0),
                                    size=self._menu_btn_size,
                                    border=4,
                                    text=self._strings['menu_continue_btn'],
                                    font_size=40,
                                    center_text=True)
        self._new_game_btn = Button(position=(0, 0),
                                    size=self._menu_btn_size,
                                    border=4,
                                    text=self._strings['menu_new_game_btn'],
                                    font_size=40,
                                    center_text=True)
        self._stats_btn = Button(position=(0, 0),
                                 size=self._menu_btn_size,
                                 border=4,
                                 text=self._strings['menu_stats_btn'],
                                 font_size=40,
                                 center_text=True)
        self._exit_btn = Button(position=(0, 0),
                                size=self._menu_btn_size,
                                border=4,
                                text=self._strings['menu_exit_btn'],
                                font_size=40,
                                center_text=True)
        self._menu_btns = [self._continue_btn, self._new_game_btn, self._stats_btn, self._exit_btn]
        self._update_menu_layout()

        # language button
        language_btn_size = (60, 33)
        self._language_btn = Button(position=(self._SCR_WIDTH - language_btn_size[0] - 30, 30),
                                    size=language_btn_size,
                                    border=2,
                                    image_size=language_btn_size,
                                    image_path='resources/images/pol_PL.png')

        # surface for the fade effect
        self._faded_surf = pygame.Surface((self._SCR_WIDTH, self._SCR_HEIGHT), flags=pygame.SRCALPHA)
        self._faded_surf.set_alpha(180)
        self._faded_surf.fill(self._COLORS["black"])
        self._faded_diff_choice = False
        self._faded_win = False

        # difficulty buttons
        self._diff_txts = [self._strings[f'menu_diff_btn_{i}'] for i in range(4)]
        diff_btn_size = (300, 75)
        cont_border = 25
        self._diff_btns_cont = pygame.Surface((diff_btn_size[0] + cont_border * 2,
                                               diff_btn_size[1] * 4 + self._menu_btn_spacing * 3 + cont_border * 2))
        self._diff_btns_cont_pos = ((self._SCR_WIDTH - diff_btn_size[0] - cont_border * 2) / 2,
                                    (self._SCR_HEIGHT - self._diff_btns_cont.get_height()) / 2 - cont_border)
        self._diff_btns = [Button(position=((self._SCR_WIDTH - diff_btn_size[0]) / 2,
                                            self._diff_btns_cont_pos[1] + (diff_btn_size[1] + self._menu_btn_spacing)
                                            * i + cont_border),
                                  size=diff_btn_size,
                                  border=4,
                                  text=diff,
                                  font_size=36,
                                  center_text=True) for i, diff in enumerate(self._diff_txts)]

        # statistics screen buttons
        stats_btn_size = (136, 40)
        self._stats_return_btn = Button(position=(self._SCR_WIDTH / 5, self._SCR_HEIGHT - stats_btn_size[1] - 25),
                                        size=stats_btn_size,
                                        border=2,
                                        text=self._strings['stats_return_btn'],
                                        font_size=24,
                                        text_color=self._COLORS["black"],
                                        center_text=True)
        self._stats_reset_btn = Button(position=(self._SCR_WIDTH * 3 / 5, self._SCR_HEIGHT - stats_btn_size[1] - 25),
                                       size=(self._numpad_size[0], 40),
                                       border=2,
                                       text=self._strings['stats_reset_btn'],
                                       font_size=24,
                                       text_color=self._COLORS["black"],
                                       center_text=True)
        self._stats_btns = [self._stats_return_btn, self._stats_reset_btn]

        # win screen
        self._win_surf = pygame.Surface((int(self._SCR_WIDTH * 0.7), int(self._SCR_HEIGHT * 0.7)))
        self._win_surf_pos = ((self._SCR_WIDTH - self._win_surf.get_width()) / 2,
                              (self._SCR_HEIGHT - self._win_surf.get_height()) / 2)
        win_return_btn_size = (300, 75)
        win_return_btn_pos = (self._win_surf_pos[0] + self._win_surf.get_width() / 2 - win_return_btn_size[0] / 2,
                              self._win_surf_pos[1] + self._win_surf.get_height() - win_return_btn_size[1] - 40)
        self._win_return_btn = Button(position=win_return_btn_pos,
                                      size=win_return_btn_size,
                                      border=4,
                                      text=self._strings['win_return_btn'],
                                      font_size=30,
                                      center_text=True)

    def _get_notes_status(self) -> str:
        """
        Gets the text for the notes mode button in the currently chosen language

        :return: the text for the notes mode button
        """
        notes_mode_btn_txt = self._strings["notes_mode_btn"]
        notes_mode_btn_txt += self._strings["notes_mode_on"] if self._notes_mode else self._strings["notes_mode_off"]
        return notes_mode_btn_txt

    def _update_strings(self):
        """
        Updates every in-game string to the ones in the current language
        """
        # screen titles
        self._diff_txts = [self._strings[f'menu_diff_btn_{i}'] for i in range(4)]
        self._menu_scr.update_title(self._strings['menu_title'])
        self._game_scr.update_title(self._strings['game_title'])
        self._stats_scr.update_title(self._strings['stats_title'])
        # refresh the window to set the new title of main menu window
        self._menu_scr.end_current()
        self._menu_scr.make_current()

        # menu buttons
        self._continue_btn.update_text(text=self._strings['menu_continue_btn'])
        self._new_game_btn.update_text(text=self._strings['menu_new_game_btn'])
        self._stats_btn.update_text(text=self._strings['menu_stats_btn'])
        self._exit_btn.update_text(text=self._strings['menu_exit_btn'])
        for text, button in zip(self._diff_txts, self._diff_btns):
            button.update_text(text=text)

        # game buttons
        # the text on the notes mode button is automatically updated on click
        self._erase_btn.update_text(text=self._strings['erase_btn'])
        self._undo_btn.update_text(text=self._strings['undo_btn'])
        self._return_btn.update_text(text=self._strings['return_btn'])
        self._win_return_btn.update_text(text=self._strings['win_return_btn'])

        # stats screen buttons
        self._stats_return_btn.update_text(text=self._strings['stats_return_btn'])
        self._stats_reset_btn.update_text(text=self._strings['stats_reset_btn'])

    def _change_language(self, language: str, update: bool = True):
        """
        Changes the in-game used strings to the given language

        :param language: the language to change the strings to
        :param update: if the buttons has to be updated with the new strings (don't use it in SudokuGUI.__init__!)
        """
        with open(f'resources/languages/{language}.json', encoding='utf-8') as f:
            self._strings = json.load(f)

        if update:
            self._language_btn.update_image(image_path=f'resources/images/{language}.png')
            self._update_strings()
            pygame.display.flip()

    def _update_menu_layout(self):
        """
        Updates the main menu buttons positions depending on the presence of continue button
        """
        start = 0 if self._continue else 1
        menu_y = (self._SCR_HEIGHT - (len(self._menu_btns) - start) * (self._menu_btn_size[1] + self._menu_btn_spacing)) / 2
        menu_x = (self._SCR_WIDTH - self._menu_btn_size[0]) / 2
        for i, button in enumerate(self._menu_btns[start:]):
            button.update_position(position=(menu_x, button.size[1] * i + self._menu_btn_spacing * i + menu_y))

    def _generate_board(self):
        """
        Clears the current board and generate the new one
        """
        self._sudoku_engine.clear_board()
        self._sudoku_engine.generate(self._difficulty)
        self._rects = [[SudokuSquare(rect=pygame.Rect(j * self._square_side, i * self._square_side, self._square_side,
                                                      self._square_side)
                                     .move(self._square_offset_x, self._square_offset_y),
                                     color=self._COLORS['white'],
                                     selected=False,
                                     at_intersection=False,
                                     same_value=False,
                                     row=i,
                                     col=j,
                                     value=self._sudoku_engine.get_value(i, j))
                        for i in range(9)] for j in range(9)]
        self._continue = False

    @staticmethod
    def _check_if_intersects(square: SudokuSquare, other: SudokuSquare) -> bool:
        """
        Checks if the given squares are in the same row, column or 3x3 square

        :param square: the first square to check
        :param other: the second square to check
        :return: True if the squares intersect, False otherwise
        """
        # used for checking 3x3 square
        start_row = 3 * (square.row // 3)
        start_col = 3 * (square.col // 3)

        intersects = False
        if square.row == other.row or square.col == other.col:
            intersects = True
        elif other.row in range(start_row, start_row + 3) and other.col in range(start_col, start_col + 3):
            intersects = True
        return intersects

    def _check_if_same_value(self, square: SudokuSquare):
        """
        Iterates through the whole board and finds the non-empty squares with the same value as the given square

        :param square: the square to compare the value of others with
        """
        for row_other in self._rects:
            for square_other in row_other:
                square_other.at_intersection = self._check_if_intersects(square, square_other)
                if square.value == square_other.value and square.value != 0:
                    square_other.same_value = True

    def _clear_notes(self, square: SudokuSquare):
        """
        Remove the notes from intersecting squares based on the value of the checked square

        :param square: the square of which value will be compared to the notes of other squares
        """
        for row_other in self._rects:
            for square_other in row_other:
                if self._check_if_intersects(square, square_other) and square.value in square_other.notes:
                    square_other.notes.remove(square.value)

    def _select_on_click(self, pos: tuple) -> tuple:
        """
        Returns the square coordinates under the current mouse position (on click)

        :param pos: the mouse position
        :return: row and column of the square - if there is no square under the cursor, returns (-1, -1)
        """
        self._reset_state()
        for row in self._rects:
            for square in row:
                if square.rect.collidepoint(pos) and not self._timer.paused:
                    self._click_snd.play()
                    square.selected = True
                    selected_index = (square.row, square.col)
                    # shows the squares with the same value based on the new selection
                    self._check_if_same_value(square)
                    return selected_index
        # if the mouse is not over any square, return the default index
        return -1, -1

    def _reset_state(self, ignore_wrong: bool = True):
        """
        Resets the state of all squares

        :param ignore_wrong: if True, the is_wrong attribute is not changed
        """
        for row in self._rects:
            for square in row:
                square.at_intersection = False
                square.selected = False
                square.same_value = False
                if not ignore_wrong:
                    square.is_wrong = False

    def _move_selected(self, selected_index: tuple, row_offset: int, col_offset: int) -> tuple:
        """
        Unselects the previous square and selects the new one, based on the given directions

        :param selected_index: row and column of previously selected square
        :param row_offset: horizontal direction of new selection
        :param col_offset: vertical direction of new selection
        :return: row and column of newly selected square
        """
        new_row = selected_index[0]
        new_col = selected_index[1]
        if row_offset:
            # provides the right-left movement continuity
            if new_row == 8 and row_offset > 0:
                new_row = 0
            elif new_row == 0 and row_offset < 0:
                new_row = 8
            else:
                new_row += row_offset
        elif col_offset:
            # provides the top-bottom movement continuity
            if new_col == 8 and col_offset > 0:
                new_col = 0
            elif new_col == 0 and col_offset < 0:
                new_col = 8
            else:
                new_col += col_offset

        self._get_square(*selected_index).selected = False
        self._get_square(new_row, new_col).selected = True

        # updates the squares with the same value based on the new selection
        self._check_if_same_value(self._get_square(new_row, new_col))
        return new_row, new_col

    def _get_square(self, row: int, col: int) -> SudokuSquare:
        """
        Function for getting the SudokuSquare object based on the given row and column

        :param col: the column of desired square
        :param row: the row of desired square
        :return: SudokuSquare object
        """
        return self._rects[col][row]

    def _check_if_correct(self):
        """
        Iterates over the whole board and checks if there is the same value in row, column or corresponding
        3x3 field - if there is, it marks these squares as wrong
        """
        for row in self._rects:
            for square in row:
                for row_other in self._rects:
                    for square_other in row_other:
                        if self._check_if_intersects(square, square_other) and square.value == square_other.value \
                                and square.value != 0 and square is not square_other:
                            square.is_wrong = square_other.is_wrong = True

    def _undo_move(self):
        """
        Reverses the last made move
        """
        try:
            last_move = self._last_moves.pop()
        except IndexError:
            return
        self._get_square(last_move.row, last_move.col).notes = last_move.prev_notes
        self._get_square(last_move.row, last_move.col).value = last_move.prev_number

    def _key_press_handler(self, key: int, selected_index: tuple, ignore_arrows: bool = True) -> tuple:
        """
        Handles the key press events

        :param key: currently pressed key
        :param selected_index: row and column of the currently selected square
        :param ignore_arrows: if the arrow keys has to be ignored
        :return: row and column of the newly selected square
        """
        if key == pygame.K_SPACE:
            self._timer.unpause() if self._timer.paused else self._timer.pause()
        elif key == pygame.K_TAB:
            self._notes_mode = not self._notes_mode
        if selected_index != (-1, -1) and not self._timer.paused:
            selected_square = self._get_square(*selected_index)
            offset = (0, 0)
            ignore_wrong = True
            # keyboard arrows movement
            if not ignore_arrows:
                if key == pygame.K_RIGHT:
                    offset = (0, 1)
                elif key == pygame.K_LEFT:
                    offset = (0, -1)
                elif key == pygame.K_UP:
                    offset = (-1, 0)
                elif key == pygame.K_DOWN:
                    offset = (1, 0)
            # number inputting
            elif key in self._PY_TO_NUM.keys():
                num = self._PY_TO_NUM[key]
                if selected_square.editable:
                    self._click_snd.play()
                    # value writing
                    if not self._notes_mode:
                        prev_num = selected_square.value
                        selected_square.value = num
                        self._last_moves.append(Move(prev_num, selected_square.notes[:],
                                                     selected_square.row, selected_square.col))
                        selected_square.notes.clear()
                        ignore_wrong = False
                        self._clear_notes(selected_square)
                    # notes writing
                    else:
                        if num not in selected_square.notes and not selected_square.value:
                            prev_notes = selected_square.notes[:]
                            selected_square.notes.append(num)
                            self._last_moves.append(Move(selected_square.value, prev_notes,
                                                    selected_square.row, selected_square.col))
                        elif num in selected_square.notes and not selected_square.value:
                            prev_notes = selected_square.notes[:]
                            selected_square.notes.remove(num)
                            self._last_moves.append(Move(selected_square.value, prev_notes,
                                                    selected_square.row, selected_square.col))
            # deleting numbers and notes
            elif key == pygame.K_BACKSPACE or key == pygame.K_DELETE:
                if selected_square.editable:
                    self._click_snd.play()
                    if selected_square.notes:
                        selected_square.notes.clear()
                    prev_num = selected_square.value
                    prev_notes = selected_square.notes[:]
                    selected_square.value = 0
                    self._last_moves.append(Move(prev_num, prev_notes, selected_square.row, selected_square.col))
                    ignore_wrong = False
            self._reset_state(ignore_wrong)
            return self._move_selected(selected_index, *offset)
        return selected_index

    def _movement_handler(self):
        """
        Detects if the arrow key is pressed and provides movement
        """
        pressed_keys = pygame.key.get_pressed()
        arrow_keys = [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]
        for key in arrow_keys:
            if pressed_keys[key]:
                pygame.time.wait(150)
                self._click_snd.play()
                self._selected_index = self._key_press_handler(key, self._selected_index, ignore_arrows=False)

    def _draw_number(self, square):
        """
        Draws the given square value on the board

        :param square: the square whose value is to be displayed
        """
        if square.value:
            if square.editable:
                color = self._COLORS['blue'] if not square.is_wrong else self._COLORS['darkred']
            else:
                color = self._COLORS['black']
            num = self._square_fnt.render(str(square.value), True, color)
            xpos = self._square_offset_x + self._square_side * square.col - self._square_fnt.size(
                str(square.value))[0] / 2 + self._square_side / 2
            ypos = self._square_offset_y + self._square_side * square.row - self._square_fnt.size(
                str(square.value))[1] / 2 + self._square_side / 2 + 2
            self._scr.blit(num, (xpos, ypos))
        elif square.notes:
            color = self._COLORS['gray']
            nums = [self._square_notes_fnt.render(str(note), True, color) for note in square.notes]
            for surface, number in zip(nums, square.notes):
                xpos = self._NOTES_POS[number][0] + self._square_offset_x + self._square_side * square.col \
                       + self._square_notes_fnt.size(str(number))[0] / 2 + 2
                ypos = self._NOTES_POS[number][1] + self._square_offset_y + self._square_side * square.row \
                       + self._square_notes_fnt.size(str(number))[1] / 2 - 7
                self._scr.blit(surface, (xpos, ypos))

    def _draw_board_lines(self, only_border: bool = False):
        """
        Draws the board grid

        :param only_border: if True, only the outside borders will be drawn
        """
        for i, line in enumerate(self._lines):
            if only_border and not (i == 0 or i == len(self._lines) - 1):
                continue
            thickness = 2 if i % 3 == 0 else 1
            # vertical lines
            pygame.draw.line(self._scr, self._COLORS['black'], *line, width=thickness)
            # horizontal lines
            pygame.draw.line(self._scr, self._COLORS['black'],
                             (line[0][1] - self._square_offset_y + self._square_offset_x,
                              line[0][0] - self._square_offset_x + self._square_offset_y),
                             (line[1][1] - self._square_offset_y + self._square_offset_x,
                              line[0][0] - self._square_offset_x + self._square_offset_y),
                             width=thickness)

    def _draw_timer(self, xpos: float, ypos: float):
        """
        Draws the timer on the screen

        :param xpos: x position of the timer
        :param ypos: y position of the timer
        """
        time_ = self._timer_fnt.render(self._timer.current_prettified, True, self._COLORS['black'])
        self._scr.blit(time_, (xpos, ypos))

    def _draw_numpad(self):
        """
        Draws the numpad used for inputting the numbers
        """
        completed_nums = self._check_completion()
        for button in self._numpad_btns:
            # if every number of one type is on the board (and every is correct),
            # deactivate and color the corresponding buttons on the numpad
            if int(button.text) in completed_nums:
                button.update_text(text_color=self._COLORS["green"])
                button.update_color(color=self._COLORS['lightgray'])
                button.clickable(False)
            else:
                button.update_text(text_color=self._COLORS["black"])
                button.update_color(color=self._COLORS['white'])
                button.clickable(True)
            self._scr.blit(button.surface, button.position)

    def _draw_board(self):
        """
        Draws the complete board on the screen
        """
        if self._timer.paused:
            self._draw_board_lines(only_border=True)
            self._scr.blit(self._pause_img, self._pause_img_rect)
            self._scr.blit(self._unpause_btn.surface, self._unpause_btn.position)
        else:
            for row in self._rects:
                for square in row:
                    if square.selected:
                        square.color = self._COLORS['green']
                    elif square.same_value:
                        square.color = self._COLORS['orange']
                    elif square.is_wrong:
                        square.color = self._COLORS['lightred']
                    elif square.at_intersection:
                        square.color = self._COLORS['lightgreen']
                    else:
                        square.color = self._COLORS['white']
                    pygame.draw.rect(self._scr, square.color, square.rect)
                    self._draw_number(square)
            self._draw_board_lines()
            self._scr.blit(self._pause_btn.surface, self._pause_btn.position)
            self._notes_mode_btn.update_text(text=self._get_notes_status())
            self._scr.blit(self._notes_mode_btn.surface, self._notes_mode_btn.position)
            self._draw_numpad()
            self._scr.blit(self._erase_btn.surface, self._erase_btn.position)
            self._scr.blit(self._undo_btn.surface, self._undo_btn.position)
        self._draw_timer(self._timer_x, self._timer_y)
        self._scr.blit(self._return_btn.surface, self._return_btn.position)

    def _button_hover(self, button_list: list, pos: tuple, reset_color: bool = True):
        """
        Creates the hover effect on the buttons within the given list

        :param button_list: the list of button to get the hover effect
        :param pos: the mouse position
        :param reset_color: if the background color has to be reseted from the hovered one
        """
        for button in button_list:
            if button.check_collision(pos) and button.clickable:
                button.update_color(color=self._COLORS['lightgray'])
            if reset_color:
                button.update_color(color=self._COLORS['white'])

    def _check_completion(self) -> list:
        """
        Checks which numbers are completely and correctly filled on the board, and returns them

        :return: the list of correctly and completely filled numbers
        """
        nums = {i: 0 for i in range(1, 10)}
        for row in self._rects:
            for square in row:
                if square.value and not square.is_wrong:
                    nums[square.value] += 1
        nums = [k for k, v in nums.items() if v == 9]
        return nums

    def _check_record(self, diff: str, time_: int) -> bool:
        """
        Checks if the given time for the given difficulty is shorter than the current record

        :param diff: the difficulty of solved sudoku
        :param time_: the time of solving current sudoku
        :return: True if this is a new record, False otherwise
        """
        current_rec = min(self._stats[f'{diff}_times'], default=0)
        return current_rec > time_ or current_rec == 0

    def _check_win(self):
        """
        Checks if the currently fully filled board is the proper solution

        :return: True if the board is filled fully and correctly, False otherwise
        """
        return len(self._check_completion()) == 9

    def _draw_main_menu(self):
        """
        Draws the main menu on the screen
        """
        self._scr.fill(self._COLORS["white"])
        start = 1 if not self._continue else 0
        for button in self._menu_btns[start:]:
            self._scr.blit(button.surface, button.position)
        self._scr.blit(self._language_btn.surface, self._language_btn.position)

    def _draw_difficulty_buttons(self):
        """
        Draws the difficulty buttons after choosing the new game option
        """
        self._diff_btns_cont.fill(self._COLORS["white"])
        for button in self._diff_btns:
            self._diff_btns_cont.blit(button.surface, tuple(x - y for x, y in zip(button.position,
                                                                                  self._diff_btns_cont_pos)))
        self._scr.blit(self._diff_btns_cont, self._diff_btns_cont_pos)

    def _draw_stats(self):
        """
        Draws the statistics on the screen
        """
        def get_best_time(difficulty: str) -> str:
            """
            Gets the best time from the games played with given difficulty

            :param difficulty: the difficulty of the played games
            :return: the best time within the given difficulty
            """
            return Timer().prettify(min(self._stats[f'{difficulty}_times'], default=0))

        def get_avg_time(difficulty: str) -> str:
            """
            Gets the average time from the games played with given difficulty

            :param difficulty: the difficulty of the played games
            :return: the average time within the given difficulty
            """
            if self._stats[f'{difficulty}_count']:
                result = sum(self._stats[f'{difficulty}_times']) // self._stats[f'{difficulty}_count']
            else:
                result = 0
            return Timer().prettify(result)

        def get_games_count(difficulty: str) -> str:
            """
            Gets the number of games played with given difficulty

            :param difficulty: the difficulty of the played games
            :return: the number of games played at the given difficulty
            """
            return str(self._stats[f'{difficulty}_count'])

        self._scr.fill(self._COLORS["white"])

        # difficulty level labels
        diff_headings = [self._stats_fnt_b.render(diff, True, self._COLORS['black']) for diff in self._diff_txts]

        # best time, average time and games played labels
        best_time_txt = self._stats_fnt_i.render(self._strings['stats_best_time'], True, self._COLORS['black'])
        avg_time_txt = self._stats_fnt_i.render(self._strings['stats_avg_time'], True, self._COLORS['black'])
        games_count_txt = self._stats_fnt_i.render(self._strings['stats_games_count'], True, self._COLORS['black'])
        times_headings = [best_time_txt, avg_time_txt, games_count_txt]
        times_x = [self._SCR_WIDTH / 5, self._SCR_WIDTH / 2, self._SCR_WIDTH * 4 / 5]

        # statistics
        formulas = [get_best_time, get_avg_time, get_games_count]
        gap = 10
        for i, (diff, v) in enumerate(zip(diff_headings, self._DIFF_TO_STATS.values())):
            diff_rect = diff.get_rect(center=(self._SCR_WIDTH / 2, diff.get_height() * 4 * i + diff.get_height()))
            self._scr.blit(diff, diff_rect)
            for time_, x in zip(times_headings, times_x):
                time_rect = time_.get_rect(center=(x, diff.get_height() * 4 * i + diff.get_height() * 2 + gap))
                self._scr.blit(time_, time_rect)
            for formula, x in zip(formulas, times_x):
                text = self._stats_fnt.render(formula(v), True, self._COLORS['black'])
                text_rect = text.get_rect(center=(x, diff.get_height() * 4 * i + diff.get_height() * 3 + gap * 2))
                self._scr.blit(text, text_rect)

        for button in self._stats_btns:
            self._scr.blit(button.surface, button.position)

    def _create_stats(self, reset: bool = False):
        """
        Creates the new file for saving the statistics and loads them into game

        :param reset: if the current stats file has to be deleted
        """
        if not os.path.exists(os.path.expanduser('~/Documents/Sudoku/statistics.json')) or reset:
            with open(os.path.expanduser('~/Documents/Sudoku/statistics.json'), 'w+') as f:
                statistics = {"easy_times": [],
                              "easy_count": 0,
                              "medium_times": [],
                              "medium_count": 0,
                              "hard_times": [],
                              "hard_count": 0,
                              "expert_times": [],
                              "expert_count": 0, }
                f.write(json.dumps(statistics))
        with open(os.path.expanduser('~/Documents/Sudoku/statistics.json')) as f:
            self._stats = json.load(f)

    def _save_stats_to_file(self):
        """
        Saves the statistics to a json file
        """
        with open(os.path.expanduser('~/Documents/Sudoku/statistics.json'), 'w+') as f:
            f.write(json.dumps(self._stats))

    def _show_win_screen(self):
        """
        Draws the win screen if the sudoku is completed
        """
        solved_time = self._timer.current
        solved_time_pretty = self._timer.current_prettified
        if self._stats_to_save:
            self._new_record = self._check_record(self._DIFF_TO_STATS[self._difficulty], solved_time)
            self._stats[f'{self._DIFF_TO_STATS[self._difficulty]}_times'].append(solved_time)
            self._stats[f'{self._DIFF_TO_STATS[self._difficulty]}_count'] += 1
            self._save_stats_to_file()
            self._stats_to_save = False

        self._timer.stop()
        self._win_surf.fill(self._COLORS["white"])
        texts = [self._text_fnt.render(self._strings[f'win_txt_0'], True, self._COLORS['black']),
                 self._text_fnt.render(self._strings[f'win_txt_1'] + self._diff_txts[self._difficulty],
                                       True, self._COLORS['black']),
                 self._text_fnt.render(self._strings[f'win_txt_2'], True, self._COLORS['black']),
                 self._text_fnt.render(f'{solved_time_pretty}', True, self._COLORS["black"])]
        if self._new_record:
            texts.append(self._text_fnt.render(self._strings[f'win_txt_3'], True, self._COLORS["black"]))

        for i, text in enumerate(texts, 1):
            rect = text.get_rect(center=(self._win_surf.get_width() / 2, 50 * i))
            self._win_surf.blit(text, rect)
        self._win_surf.blit(self._win_return_btn.surface,
                            tuple(x - y for x, y in zip(self._win_return_btn.position, self._win_surf_pos)))
        self._scr.blit(self._win_surf, self._win_surf_pos)

    def _menu_loop(self):
        """
        Displays the menu screen
        """
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self._faded_diff_choice:
                if self._continue_btn.check_collision(pos) and self._continue:
                    self._click_snd.play()
                    self._menu_scr.end_current()
                    self._scr = self._game_scr.make_current()
                    self._timer.unpause()
                elif self._new_game_btn.check_collision(pos):
                    self._click_snd.play()
                    self._faded_diff_choice = True
                    self._stats_to_save = True
                    self._new_record = False
                    self._last_moves.clear()
                elif self._stats_btn.check_collision(pos):
                    self._click_snd.play()
                    self._menu_scr.end_current()
                    self._scr = self._stats_scr.make_current()
                elif self._exit_btn.check_collision(pos):
                    self._click_snd.play()
                    self._running = False
                elif self._language_btn.check_collision(pos):
                    self._click_snd.play()
                    self._change_language(next(self._languages))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._faded_diff_choice:
                for diff, button in enumerate(self._diff_btns):
                    if button.check_collision(pos):
                        self._click_snd.play()
                        self._difficulty = diff
                        self._generate_board()
                        self._menu_scr.end_current()
                        self._scr = self._game_scr.make_current()
                        self._timer.reset()
                        self._timer.unpause()
                        self._faded_diff_choice = False
                        self._faded_win = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._click_snd.play()
                    self._faded_diff_choice = False

        self._scr.fill(self._COLORS["white"])
        self._draw_main_menu()

        if self._faded_diff_choice:
            self._scr.blit(self._faded_surf, (0, 0))
            self._draw_difficulty_buttons()
            self._button_hover(self._diff_btns, pos)
        else:
            self._button_hover(self._menu_btns, pos)

        pygame.display.flip()

    def _stats_loop(self):
        """
        Displays the statistics screen
        """
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._stats_return_btn.check_collision(pos):
                    self._click_snd.play()
                    self._stats_scr.end_current()
                    self._scr = self._menu_scr.make_current()
                elif self._stats_reset_btn.check_collision(pos):
                    self._click_snd.play()
                    self._create_stats(reset=True)

        self._button_hover(self._stats_btns, pos)

        self._scr.fill(self._COLORS['white'])
        self._draw_stats()
        pygame.display.flip()

    def _game_loop(self):
        """
        Displays the game screen
        """
        self._movement_handler()
        sidebar_clicked = False
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self._faded_win:
                for button in self._numpad_btns:
                    if button.check_collision(pos):
                        self._click_snd.play()
                        self._key_press_handler(self._NUM_TO_PY[int(button.text)], self._selected_index)
                        self._check_if_correct()
                        sidebar_clicked = True
                if self._erase_btn.check_collision(pos) and not self._timer.paused:
                    self._click_snd.play()
                    self._key_press_handler(pygame.K_BACKSPACE, self._selected_index)
                    sidebar_clicked = True
                elif self._undo_btn.check_collision(pos) and not self._timer.paused:
                    self._click_snd.play()
                    self._undo_move()
                    self._reset_state(ignore_wrong=False)
                    self._check_if_correct()
                elif self._pause_btn.check_collision(pos) and not self._timer.paused:
                    self._click_snd.play()
                    self._timer.pause()
                elif self._unpause_btn.check_collision(pos) and self._timer.paused:
                    self._click_snd.play()
                    self._timer.unpause()
                elif self._notes_mode_btn.check_collision(pos) and not self._timer.paused:
                    self._click_snd.play()
                    self._notes_mode = not self._notes_mode
                elif self._return_btn.check_collision(pos):
                    self._click_snd.play()
                    self._game_scr.end_current()
                    self._scr = self._menu_scr.make_current()
                    self._timer.pause()
                    self._continue = True
                    self._update_menu_layout()
                self._selected_index = self._select_on_click(pos) if not sidebar_clicked else self._selected_index
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._faded_win:
                if self._win_return_btn.check_collision(pos):
                    self._click_snd.play()
                    self._faded_win = False
                    self._game_scr.end_current()
                    self._scr = self._menu_scr.make_current()
                    self._continue = False
                    self._update_menu_layout()
            elif event.type == pygame.KEYDOWN and not self._faded_win:
                self._selected_index = self._key_press_handler(event.key, self._selected_index)
                self._check_if_correct()

        self._scr.fill(self._COLORS['white'])
        self._draw_board()

        if self._check_win():
            self._faded_win = True
        else:
            self._button_hover(self._numpad_btns, pos, False)
            self._button_hover([self._return_btn], pos)
        if self._faded_win:
            self._scr.blit(self._faded_surf, (0, 0))
            self._show_win_screen()
            self._button_hover([self._win_return_btn], pos)

        pygame.display.flip()
    pygame.quit()

    def main_loop(self):
        """
        Main GUI handler
        """
        while self._running:
            for screen, loop in self._screens:
                if screen.check_if_current():
                    loop()


if __name__ == '__main__':
    pygame.init()
    sgui = SudokuGUI()
    sgui.main_loop()

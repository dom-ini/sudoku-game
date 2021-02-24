import random


class Sudoku:
    """
    Class for creating the sudoku board
    """
    def __init__(self):
        self._board = [[0 for _ in range(9)] for _ in range(9)]
        # the difficulty level depends on the number of blank squares - change it to modify difficulty
        self._difficulty = {0: 35, 1: 43, 2: 55, 3: 60}

    def print_board(self):
        """
        Prints the sudoku board in the console
        """
        for row in self._board:
            for i in row:
                print(i, end='  ')
            print()

    def _generate_diagonals(self):
        """
        Generates the three diagonal 3x3 squares on the sudoku board (they are indepentent, so it's simply random choice
        of 1-9 set for every square)
        """
        nums = set()
        for x in range(9):
            if not nums:
                nums = {i for i in range(1, 10)}
            start = x - x % 3
            for y in range(start, start + 3):
                num = random.choice(tuple(nums))
                self._board[x][y] = num
                nums.remove(num)

    def clear_board(self):
        """
        Fills the entire board with zeros
        """
        self._board = [[0 for _ in range(9)] for _ in range(9)]

    def generate(self, diff_chosen: int):
        """
        Main function, generates the sudoku board with the given difficulty

        :param diff_chosen: the level of difficulty from 0 to 3 determining the number of blank squares
        """
        self._generate_diagonals()
        self._generate_board(0, 0)
        self._remove_random_fields(diff_chosen)

    def _generate_board(self, i: int, j: int) -> bool:
        """
        Fills the empty squares with values using the backtracking algorithm

        :param i: the row of the square to be filled
        :param j: the column of the square to be filled
        :return: True if the number leads to the solution, False otherwise
        """
        if i == 8 and j == 9:
            return True

        if j == 9:
            i += 1
            j = 0

        # if the given square is not empty, proceed to the next square
        if self._board[i][j] != 0:
            return self._generate_board(i, j + 1)

        # check if the each successive number leads to the solution
        for num in range(1, 10):
            if self._is_num_valid(i, j, num):
                self._board[i][j] = num

                if self._generate_board(i, j + 1):
                    return True

            self._board[i][j] = 0

        return False

    def _is_num_valid(self, row: int, col: int, num: int) -> bool:
        """
        Checks if the number is valid in the given row and column

        :param row: the row of the square to check
        :param col: the row of the square to check
        :param num: the number to be checked for validity
        :return: True if the number in the given square is valid, False otherwise
        """
        if num in self._board[row]:
            return False

        for x in self._board:
            if x[col] == num:
                return False

        start_row = row - row % 3
        start_col = col - col % 3

        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if self._board[i][j] == num:
                    return False

        return True

    def _remove_random_fields(self, diff_chosen: int):
        """
        Remove the random numbers from the board (depending on the chosen level of difficulty)

        :param diff_chosen: the number from range 0-3 determining the number of pre-filled squares on the board (from
        easiest to hardest)
        """
        for _ in range(self._difficulty[diff_chosen]):
            field = 0
            while not field:
                rand_row = random.randint(0, 8)
                rand_col = random.randint(0, 8)
                field = self._board[rand_row][rand_col]

            self._board[rand_row][rand_col] = 0

    @property
    def board(self) -> list:
        """
        Getter for the sudoku board

        :return: current sudoku board as a list of lists
        """
        return self._board

    def get_value(self, row: int, col: int) -> int:
        """
        Gets the value of the square based on the given coordinates

        :param row: the row of desired square
        :param col: the col of desired square
        :return: the value of the square with the given coordinates
        """
        return self._board[row][col]

    def insert_value(self, row: int, col: int, value: int):
        """
        Sets the given value in the square with the given coordinates

        :param row: the row of square to be filled
        :param col: the column of square to be filled
        :param value: the value to insert into the square
        """
        self._board[row][col] = value


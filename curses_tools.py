import curses

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258
GAME_OVER_TITLE = \
    """
       _____                            ____                    
      / ____|                          / __ \                   
     | |  __   __ _  _ __ ___    ___  | |  | |__   __ ___  _ __ 
     | | |_ | / _` || '_ ` _ \  / _ \ | |  | |\ \ / // _ \| '__|
     | |__| || (_| || | | | | ||  __/ | |__| | \ V /|  __/| |   
      \_____| \__,_||_| |_| |_| \___|  \____/   \_/  \___||_|   
    """


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""
    rows_direction = columns_direction = 0
    space_pressed = False
    pressed_key_code = canvas.getch()
    if pressed_key_code == UP_KEY_CODE:
        rows_direction = -1
    elif pressed_key_code == DOWN_KEY_CODE:
        rows_direction = 1
    elif pressed_key_code == RIGHT_KEY_CODE:
        columns_direction = 1
    elif pressed_key_code == LEFT_KEY_CODE:
        columns_direction = -1
    elif pressed_key_code == SPACE_KEY_CODE:
        space_pressed = True
    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False, color=1):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()
    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue
        if row >= rows_number:
            break
        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue
            if column >= columns_number:
                break
            if symbol == ' ':
                continue
            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue
            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol, curses.color_pair(color))


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns

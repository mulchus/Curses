import time
import curses
import asyncio
import random

from itertools import cycle


TIC_TIMEOUT = 0.1
FRAME_THICKNESS = 1
SHIP_HEIGHT = 9
SHIP_WIDTH = 5
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def draw(canvas):
    canvas.border(0)
    canvas.nodelay(True)
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - FRAME_THICKNESS, columns - FRAME_THICKNESS
    rocket_row = max_row / 2
    rocket_column = max_column / 2
    rocket_frames = []
    with open("Animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frames.append(my_file.read())
    with open("Animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frames.append(my_file.read())

    numbers_of_stars = int(max_row * max_column / 40)
    coroutines = []
    for _ in range(numbers_of_stars):
        coroutines.append(
            blink(
                canvas,
                random.randint(FRAME_THICKNESS, max_row - FRAME_THICKNESS),
                random.randint(FRAME_THICKNESS, max_column - FRAME_THICKNESS),
                random.choice('+*.:'),
                random.randint(0, 20),
            )
        )

    coroutines.append(
        animate_spaceship(
            canvas,
            max_row,
            max_column,
            rocket_row,
            rocket_column,
            rocket_frames,
        )
    )

    while True:
        _, _, space_pressed = read_controls(canvas)
        if space_pressed:
            fire_coroutine = fire(canvas, rocket_row, rocket_column + 2, -1, 0)
            coroutines.append(fire_coroutine)

        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        for _ in range(0, offset_tics):  # пауза в offset_tics*0.1 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(0, 20):  # пауза в 2 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):  # пауза в 0.3 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(0, 5):  # пауза в 0.5 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):  # пауза в 0.3 сек
            await asyncio.sleep(0)


async def animate_spaceship(canvas, max_row, max_column, rocket_row, rocket_column, rocket_frames):
    iterator = cycle(rocket_frames)
    while True:
        # Все равно слабая реакция ракеты на клавиатуру, причина - звезды. Без await ракета движется нормально
        rows_direction, columns_direction, _ = read_controls(canvas)
        if rows_direction < 0:
            rocket_row = max(rocket_row + rows_direction, 1)
        elif rows_direction > 0:
            rocket_row = min(rocket_row + rows_direction, max_row - SHIP_HEIGHT)
        elif columns_direction < 0:
            rocket_column = max(rocket_column + columns_direction, 1)
        elif columns_direction > 0:
            rocket_column = min(rocket_column + columns_direction, max_column - SHIP_WIDTH)

        for _ in range(2):
            rocket = next(iterator)
            draw_frame(
                canvas,
                round(rocket_row),
                round(rocket_column),
                rocket,
            )
            await asyncio.sleep(0)

            draw_frame(
                canvas,
                round(rocket_row),
                round(rocket_column),
                rocket,
                negative=True
            )


async def fire(canvas, row, column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def draw_frame(canvas, start_row, start_column, text, negative=False):
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
            canvas.addch(row, column, symbol)


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""
    rows_direction = columns_direction = 0
    space_pressed = False
    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break
        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1
        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1
        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1
        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1
        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True
    return rows_direction, columns_direction, space_pressed


if __name__ == '__main__':
    curses.initscr()
    curses.curs_set(False)
    curses.update_lines_cols()
    curses.wrapper(draw)

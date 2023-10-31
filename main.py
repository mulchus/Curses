import time
import curses
import asyncio
import random

from pathlib import Path
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
BASE_DIR = Path(__file__).resolve().parent / 'Animations'

global coroutines


def draw(canvas):
    global coroutines
    # canvas.border(0)
    canvas.nodelay(True)
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - FRAME_THICKNESS, columns - FRAME_THICKNESS
    rocket_row = int(max_row / 2)
    rocket_column = int(max_column / 2)
    rocket_frames = []
    garbage_files = ('duck.txt', 'hubble.txt', 'lamp.txt', 'trash_large.txt', 'trash_small.txt', 'trash_xl.txt')
    garbage_frames = []
    with open('Animations/rocket_frame_1.txt', 'r') as my_file:
        rocket_frames.append(my_file.read())
    with open('Animations/rocket_frame_2.txt', 'r') as my_file:
        rocket_frames.append(my_file.read())
    for garbage_filename in garbage_files:
        with open(Path(BASE_DIR, garbage_filename), 'r') as garbage_file:
            garbage_frames.append(garbage_file.read())

    numbers_of_stars = int(max_row * max_column / 100)

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
            coroutines,
        )
    )

    coroutines.append(
        fill_orbit_with_garbage(
            canvas,
            max_column,
            garbage_frames
        )
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def sleep(duration):
    for __ in range(duration):  # пауза в duration тактов
        await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    row = 0
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column, garbage_frames):
    global coroutines
    while True:
        coroutines.append(
            fly_garbage(
                canvas,
                column=random.randint(1, max_column - 1),
                garbage_frame=random.choice(garbage_frames),
            )
        )
        await sleep(10)


async def blink(canvas, row, column, symbol, offset_tics):
    while True:
        await sleep(offset_tics)    # пауза в offset_tics тактов
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(3)


async def animate_spaceship(canvas, max_row, max_column, rocket_row, rocket_column, rocket_frames, coroutines):

    def update_coordinates(rocket_row_, rocket_column_):
        rows_direction, columns_direction, space_pressed_ = read_controls(canvas)
        if rows_direction < 0:
            rocket_row_ = max(rocket_row_ + rows_direction, 1)
        elif rows_direction > 0:
            rocket_row_ = min(rocket_row_ + rows_direction, max_row - SHIP_HEIGHT)
        elif columns_direction < 0:
            rocket_column_ = max(rocket_column_ + columns_direction, 1)
        elif columns_direction > 0:
            rocket_column_ = min(rocket_column_ + columns_direction, max_column - SHIP_WIDTH)
        return rocket_row_, rocket_column_, space_pressed_

    for rocket in cycle(rocket_frames):
        rocket_row, rocket_column, space_pressed = update_coordinates(rocket_row, rocket_column)

        if space_pressed:
            fire_coroutine = fire(canvas, rocket_row, rocket_column + 2, -1, 0)
            coroutines.append(fire_coroutine)

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


if __name__ == '__main__':
    curses.initscr()
    curses.curs_set(False)
    curses.update_lines_cols()
    curses.wrapper(draw)

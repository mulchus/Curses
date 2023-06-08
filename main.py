import time
import curses
import asyncio
import random
import curses_tools
from itertools import cycle

TIC_TIMEOUT = 0.1


def draw(canvas):
    canvas.border(0 * 8)
    canvas.refresh()

    (max_row, max_column) = canvas.getmaxyx()

    numbers_of_stars = int(max_row * max_column / 40)
    coroutines = []
    for _ in range(numbers_of_stars):
        coroutines.append(blink(canvas,\
                        random.randint(2, max_row - 2),\
                        random.randint(2, max_column - 2),\
                        random.choice('+*.:')))

    rocket_row = max_row / 2
    rocket_column = max_column / 2
    rocket_frame = []
    with open("Animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame.append(my_file.read())
    with open("Animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame.append(my_file.read())

    rocket_coroutine = animate_spaceship(canvas, rocket_row,\
                                         rocket_column,\
                                         rocket_frame)

    rows_direction = 0
    columns_direction = 0
    space_pressed = False
    fire_coroutine = 0

    while True:

        try:
            canvas.nodelay(True)
            rows_direction, columns_direction, space_pressed =\
                curses_tools.read_controls(canvas)

            if rows_direction:
                if (rocket_row + rows_direction) > 0 and (
                        rocket_row + rows_direction) < (max_row - 9):
                    rocket_row += rows_direction
                elif (rocket_row + rows_direction) <= 0:
                    rocket_row = 1
                elif (rocket_row + rows_direction) >= (max_row - 9):
                    rocket_row = max_row - 10
                rows_direction = 0

            if columns_direction:
                if (rocket_column + columns_direction) > 0 and (
                        rocket_column + columns_direction) < (max_column - 5):
                    rocket_column += columns_direction
                elif (rocket_column + columns_direction) <= 0:
                    rocket_column = 1
                elif (rocket_column + columns_direction) >= (max_column - 5):
                    rocket_column = max_column - 6
                columns_direction = 0

            if space_pressed:
                fire_coroutine = fire(canvas, rocket_row, rocket_column + 2,
                                      -1, 0)
                space_pressed = False
        except StopIteration:
            pass
        canvas.nodelay(False)

        for _ in range(len(coroutines.copy())):
            coroutine = coroutines.copy()[random.randint(0,\
                                        len(coroutines.copy())-1)]
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
            if not len(coroutines):
                break
        canvas.refresh()

        try:
            rocket_coroutine.send(None)
            canvas.refresh()
        except StopIteration:
            rocket_coroutine = animate_spaceship(canvas,\
                                        rocket_row,\
                                        rocket_column,\
                                        rocket_frame)
            pass

        try:
            if fire_coroutine:
                fire_coroutine.send(None)
                canvas.refresh()
        except StopIteration:
            fire_coroutine = 0
            pass

        # canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, symbol):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(0, 20):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(0, 5):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):
            await asyncio.sleep(0)


async def animate_spaceship(canvas, start_row, start_column, rocket_frames):
    """Display animation of rocket, direction can be specified."""

    row, column = start_row, start_column

    iterator = cycle(rocket_frames)

    rocket = next(iterator)

    curses_tools.draw_frame(canvas, round(row), round(column),\
                            rocket)
    for _ in range(0, 2):
        await asyncio.sleep(0)

    curses_tools.draw_frame(canvas, round(row), round(column),\
                            rocket, negative=True)
    await asyncio.sleep(0)

    rocket = next(iterator)

    curses_tools.draw_frame(canvas, round(row), round(column),\
                            rocket)
    for _ in range(0, 2):
        await asyncio.sleep(0)
    curses_tools.draw_frame(canvas, round(row), round(column),\
                            rocket, negative=True)
    await asyncio.sleep(0)


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

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

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


if __name__ == '__main__':
    curses.initscr()
    curses.curs_set(False)
    curses.update_lines_cols()
    curses.wrapper(draw)

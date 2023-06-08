import time
import curses
import asyncio
import random
import curses_tools

from itertools import cycle


TIC_TIMEOUT = 0.1
FRAME_THICKNESS = 1
SHIP_HEIGHT = 9
SHIP_WIDTH = 5


def draw(canvas):
    canvas.border(0)
    canvas.nodelay(True)
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - FRAME_THICKNESS, columns - FRAME_THICKNESS
    numbers_of_stars = int(max_row * max_column / 40)
    coroutines = []
    for _ in range(numbers_of_stars):
        coroutines.append(
            blink(
                canvas,
                random.randint(FRAME_THICKNESS, max_row - FRAME_THICKNESS),
                random.randint(FRAME_THICKNESS, max_column - FRAME_THICKNESS),
                random.choice('+*.:')
            )
        )

    rocket_row = max_row / 2
    rocket_column = max_column / 2
    rocket_frame = []
    with open("Animations/rocket_frame_1.txt", "r") as my_file:
        rocket_frame.append(my_file.read())
    with open("Animations/rocket_frame_2.txt", "r") as my_file:
        rocket_frame.append(my_file.read())

    coroutines.append(
        animate_spaceship(
            canvas,
            rocket_row,
            rocket_column,
            rocket_frame,
        )
    )

    rows_direction = 0
    columns_direction = 0
    space_pressed = False
    fire_coroutine = 0

    while True:
        try:
            rows_direction, columns_direction, space_pressed = curses_tools.read_controls(canvas)

            if rows_direction:
                if 0 < (rocket_row + rows_direction) <= (max_row - SHIP_HEIGHT):
                    rocket_row += rows_direction
                elif (rocket_row + rows_direction) <= 0:
                    rocket_row = 1
                elif (rocket_row + rows_direction) > (max_row - SHIP_HEIGHT):
                    rocket_row = max_row - SHIP_HEIGHT
                rows_direction = 0

            if columns_direction:
                if 0 < (rocket_column + columns_direction) <= (max_column - SHIP_WIDTH):
                    rocket_column += columns_direction
                elif (rocket_column + columns_direction) <= 0:
                    rocket_column = 1
                elif (rocket_column + columns_direction) > (max_column - SHIP_WIDTH):
                    rocket_column = max_column - SHIP_WIDTH
                columns_direction = 0

            if space_pressed:
                fire_coroutine = fire(canvas, rocket_row, rocket_column + 2, -1, 0)
                coroutines.append(fire_coroutine)
                space_pressed = False

        except StopIteration:
            pass

        # for coroutine in coroutines:
        for _ in range(len(coroutines.copy())):
            coroutine = coroutines.copy()[random.randint(0, len(coroutines.copy()) - 1)]

            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
                if coroutine.__name__ == 'animate_spaceship':
                    coroutines.append(
                        animate_spaceship(
                            canvas,
                            rocket_row,
                            rocket_column,
                            rocket_frame
                        )
                    )
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def blink(canvas, row, column, symbol):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(0, 20):  # пауза в 2 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):  # пауза в 0,3 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(0, 5):  # пауза в 0,5 сек
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):  # пауза в 0,3 сек
            await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, rocket_frames):
    """Display animation of rocket, direction can be specified."""

    iterator = cycle(rocket_frames)

    rocket = next(iterator)
    curses_tools.draw_frame(
        canvas,
        round(row),
        round(column),
        rocket,
    )

    await asyncio.sleep(0)

    curses_tools.draw_frame(
        canvas,
        round(row),
        round(column),
        rocket,
        negative=True
    )

    rocket = next(iterator)
    curses_tools.draw_frame(
        canvas,
        round(row),
        round(column),
        rocket,
    )

    await asyncio.sleep(0)

    curses_tools.draw_frame(
        canvas,
        round(row),
        round(column),
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


if __name__ == '__main__':
    curses.initscr()
    curses.curs_set(False)
    curses.update_lines_cols()
    curses.wrapper(draw)

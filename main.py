import time
import curses
import asyncio
import random

from pathlib import Path
from itertools import cycle

import curses_tools
import game_scenario
from physics import update_speed
from curses_tools import read_controls, draw_frame, get_frame_size
from obstacles import Obstacle
from explosion import explode
from game_scenario import get_garbage_delay_tics


TIC_TIMEOUT = 0.1
FRAME_THICKNESS = 1
ROCKET_HEIGHT = 9
ROCKET_WIDTH = 5
START_YEAR = 1957

BASE_DIR = Path(__file__).resolve().parent / 'Animations'

global coroutines
global obstacles
global obstacles_in_last_collisions
global year


def draw(canvas):
    global coroutines
    global obstacles
    global obstacles_in_last_collisions
    global year
    year = START_YEAR
    canvas.nodelay(True)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_RED)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - FRAME_THICKNESS, columns - FRAME_THICKNESS
    rocket_row = int(max_row / 2)
    rocket_column = int(max_column / 2)
    row_speed = column_speed = 0
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

    obstacles = []
    obstacles_in_last_collisions = []
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
        show_year(
            canvas,
            game_scenario.PHRASES,
            rows
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
            row_speed,
            column_speed,
        )
    )

    coroutines.append(
        fill_orbit_with_garbage(
            canvas,
            max_column,
            garbage_frames,
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


async def fly_garbage(canvas, column, garbage_frame, speed=0.2):
    global coroutines
    global obstacles
    global obstacles_in_last_collisions
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    rows_size, columns_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(-10, column, rows_size, columns_size)
    obstacles.append(obstacle)
    while obstacle.row < rows_number:
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.pop(0)
            coroutines.append(
                explode(
                    canvas,
                    obstacle.row + obstacle.rows_size / 2,
                    obstacle.column + obstacle.columns_size / 2,
                )
            )
            return
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, obstacle.row, obstacle.column, garbage_frame, negative=True)
        obstacle.row += speed
    try:
        obstacles.pop(0)
    finally:
        pass


async def fill_orbit_with_garbage(canvas, max_column, garbage_frames):
    global coroutines
    global year
    while True:
        if year >= 1961:
            coroutines.append(
                fly_garbage(
                    canvas,
                    column=random.randint(1, max_column - 1),
                    garbage_frame=random.choice(garbage_frames),
                    speed=1 - get_garbage_delay_tics(year)/100
                )
            )
            await sleep(get_garbage_delay_tics(year))
        else:
            await asyncio.sleep(0)


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


async def animate_spaceship(canvas, max_row, max_column, rocket_row, rocket_column, rocket_frames,
                            row_speed, column_speed):
    global obstacles
    global coroutines

    def update_coordinates(rocket_row_, rocket_column_, row_speed_, column_speed_):
        rows_direction, columns_direction, space_pressed_ = read_controls(canvas)
        row_speed_, column_speed_ = update_speed(row_speed_, column_speed_, rows_direction, columns_direction)

        rocket_row_ += row_speed_
        rocket_row_ = max(rocket_row_, 0)
        rocket_row_ = min(rocket_row_, max_row - ROCKET_HEIGHT + 3)

        rocket_column_ += column_speed_
        rocket_column_ = max(rocket_column_, 1)
        rocket_column_ = min(rocket_column_, max_column - ROCKET_WIDTH)

        return rocket_row_, rocket_column_, row_speed_, column_speed_, space_pressed_

    for rocket in cycle(rocket_frames):
        rocket_row, rocket_column, row_speed, column_speed, space_pressed =\
            update_coordinates(rocket_row, rocket_column, row_speed, column_speed)

        for obstacle in obstacles:
            if obstacle.has_collision(rocket_row, rocket_column, ROCKET_HEIGHT, ROCKET_WIDTH):
                coroutines.append(
                    explode(
                        canvas,
                        rocket_row + ROCKET_HEIGHT / 2,
                        rocket_column + ROCKET_WIDTH / 2,
                    )
                )

                title_rows, title_columns = get_frame_size(curses_tools.GAME_OVER_TITLE)
                coroutines.append(
                    show_gameover(
                        canvas,
                        max_row / 2 - title_rows / 2,
                        max_column / 2 - title_columns / 2,
                    )
                )
                return

        if space_pressed and year >= 2020:
            fire_coroutine = fire(canvas, rocket_row, rocket_column + 2, -1)
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


async def fire(canvas, fire_row, fire_column, rows_speed=-0.8):
    """Display animation of gun shot, direction and speed can be specified."""
    global obstacles
    global obstacles_in_last_collisions

    canvas.addstr(round(fire_row), round(fire_column), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(fire_row), round(fire_column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(fire_row), round(fire_column), ' ')

    fire_row += rows_speed
    symbol = '|'
    rows, columns = canvas.getmaxyx()
    curses.beep()

    while 0 <= fire_row < rows and 0 <= fire_column < columns:
        canvas.addstr(round(fire_row), round(fire_column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(fire_row), round(fire_column), ' ')
        fire_row += rows_speed

        for obstacle in obstacles:
            if obstacle.has_collision(fire_row, fire_column):
                obstacles_in_last_collisions.append(obstacle)
                obstacles = [new_obstacle for new_obstacle in obstacles if new_obstacle != obstacle]
                return


async def show_gameover(canvas, title_row, title_column):
    while True:
        draw_frame(canvas, title_row, title_column, curses_tools.GAME_OVER_TITLE, 0, 4)
        await asyncio.sleep(0)


def draw_year_and_message(canvas, year_, phrase_, rows, color_pair):
    small_window = canvas.derwin(3, 50, rows - 3, 0)
    small_window.addstr(1, 2, f'{year_}: {phrase_}', curses.color_pair(color_pair) | curses.A_BOLD)
    small_window.box()
    small_window.refresh()


async def show_year(canvas, phrases, rows):
    global year
    years = list(phrases)
    color_pair = 2
    for year, phrase in phrases.items():
        try:
            next_year = years[years.index(year) + 1]
        except (ValueError, IndexError):
            next_year = year
        for __ in range(5 * (next_year - year)):
            draw_year_and_message(canvas, year, phrase, rows, color_pair)
            await sleep(1)        # надо как то подстроить время: год = 1,5 сек
    while True:
        color_pair = 3
        draw_year_and_message(canvas, year, phrase, rows, color_pair)
        await sleep(1)        # надо как то подстроить время: год = 1,5 сек


if __name__ == '__main__':
    curses.initscr()
    curses.curs_set(False)
    curses.update_lines_cols()
    curses.wrapper(draw)

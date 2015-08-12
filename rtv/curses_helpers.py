import os
import time
import threading
import curses
from curses import textpad, ascii
from contextlib import contextmanager

from . import config
from .docs import HELP
from .helpers import strip_textpad, clean
from .exceptions import EscapeInterrupt
from six.moves import configparser
from .color import Color

__all__ = ['ESCAPE', 'get_gold', 'show_notification', 'show_help',
           'LoadScreen', 'text_input', 'curses_session',
           'prompt_input', 'add_line', 'get_arrow']

# Curses does define constants for symbols (e.g. curses.ACS_BULLET)
# However, they rely on using the curses.addch() function, which has been
# found to be buggy and a PITA to work with. By defining them as unicode
# points they can be added via the more reliable curses.addstr().
# http://bugs.python.org/issue21088
ESCAPE = 27


def get_gold():
    """
    Return the gilded symbol.
    """

    symbol = u'\u272A' if config.unicode else '*'
    attr = Color.Gold
    return symbol, attr


def get_arrow(likes):
    """
    Return the vote symbol to display, based on the `likes` paramater.
    """

    if likes is None:
        symbol = u'\u2022' if config.unicode else 'o'
        attr = Color.ArrowNone
    elif likes:
        symbol = u'\u25b2' if config.unicode else '^'
        attr = Color.ArrowUp
    else:
        symbol = u'\u25bc' if config.unicode else 'v'
        attr = Color.ArrowDown
    return symbol, attr


def add_line(window, text, row=None, col=None, attr=None):
    """
    Unicode aware version of curses's built-in addnstr method.

    Safely draws a line of text on the window starting at position (row, col).
    Checks the boundaries of the window and cuts off the text if it exceeds
    the length of the window.
    """

    # The following arg combinations must be supported to conform with addnstr
    # (window, text)
    # (window, text, attr)
    # (window, text, row, col)
    # (window, text, row, col, attr)

    cursor_row, cursor_col = window.getyx()
    row = row if row is not None else cursor_row
    col = col if col is not None else cursor_col

    max_rows, max_cols = window.getmaxyx()
    n_cols = max_cols - col - 1
    if n_cols <= 0:
        # Trying to draw outside of the screen bounds
        return

    text = clean(text, n_cols)
    params = [] if attr is None else [attr]
    window.addstr(row, col, text, *params)


def show_notification(stdscr, message):
    """
    Overlay a message box on the center of the screen and wait for user input.

    Params:
        message (list): List of strings, one per line.
    """

    n_rows, n_cols = stdscr.getmaxyx()

    box_width = max(map(len, message)) + 2
    box_height = len(message) + 2

    # Cut off the lines of the message that don't fit on the screen
    box_width = min(box_width, n_cols)
    box_height = min(box_height, n_rows)
    message = message[:box_height-2]

    s_row = (n_rows - box_height) // 2
    s_col = (n_cols - box_width) // 2

    window = stdscr.derwin(box_height, box_width, s_row, s_col)
    window.erase()
    window.border()

    for index, line in enumerate(message, start=1):
        add_line(window, line, index, 1)
    window.refresh()
    ch = stdscr.getch()

    window.clear()
    window = None
    stdscr.refresh()

    return ch


def show_help(stdscr):
    """
    Overlay a message box with the help screen.
    """

    show_notification(stdscr, HELP.splitlines())


class LoadScreen(object):

    """
    Display a loading dialog while waiting for a blocking action to complete.

    This class spins off a seperate thread to animate the loading screen in the
    background.

    Usage:
        #>>> loader = LoadScreen(stdscr)
        #>>> with loader(...):
        #>>>     blocking_request(...)
    """

    def __init__(self, stdscr):

        self._stdscr = stdscr

        self._args = None
        self._animator = None
        self._is_running = None

    def __call__(
            self,
            delay=0.5,
            interval=0.4,
            message='Downloading',
            trail='...'):
        """
        Params:
            delay (float): Length of time that the loader will wait before
                printing on the screen. Used to prevent flicker on pages that
                load very fast.
            interval (float): Length of time between each animation frame.
            message (str): Message to display
            trail (str): Trail of characters that will be animated by the
                loading screen.
        """

        self._args = (delay, interval, message, trail)
        return self

    def __enter__(self):

        self._animator = threading.Thread(target=self.animate, args=self._args)
        self._animator.daemon = True

        self._is_running = True
        self._animator.start()

    def __exit__(self, exc_type, exc_val, exc_tb):

        self._is_running = False
        self._animator.join()

    def animate(self, delay, interval, message, trail):

        start = time.time()
        while (time.time() - start) < delay:
            if not self._is_running:
                return

        message_len = len(message) + len(trail)
        n_rows, n_cols = self._stdscr.getmaxyx()
        s_row = (n_rows - 3) // 2
        s_col = (n_cols - message_len - 1) // 2
        window = self._stdscr.derwin(3, message_len + 2, s_row, s_col)

        while True:
            for i in range(len(trail) + 1):

                if not self._is_running:
                    window.clear()
                    window = None
                    self._stdscr.refresh()
                    return

                window.erase()
                window.border()
                window.addstr(1, 1, message + trail[:i])
                window.refresh()
                time.sleep(interval)

def text_input(window, allow_resize=True):
    """
    Transform a window into a text box that will accept user input and loop
    until an escape sequence is entered.

    If enter is pressed, return the input text as a string.
    If escape is pressed, return None.
    """

    window.clear()

    # Set cursor mode to 1 because 2 doesn't display on some terminals
    curses.curs_set(1)

    # Turn insert_mode off to avoid the recursion error described here
    # http://bugs.python.org/issue13051
    textbox = textpad.Textbox(window, insert_mode=False)
    textbox.stripspaces = 0

    def validate(ch):
        "Filters characters for special key sequences"
        if ch == ESCAPE:
            raise EscapeInterrupt
        if (not allow_resize) and (ch == curses.KEY_RESIZE):
            raise EscapeInterrupt
        # Fix backspace for iterm
        if ch == ascii.DEL:
            ch = curses.KEY_BACKSPACE
        return ch

    # Wrapping in an exception block so that we can distinguish when the user
    # hits the return character from when the user tries to back out of the
    # input.
    try:
        out = textbox.edit(validate=validate)
    except EscapeInterrupt:
        out = None

    curses.curs_set(0)
    return strip_textpad(out)


def prompt_input(window, prompt, hide=False):
    """
    Display a prompt where the user can enter text at the bottom of the screen

    Set hide to True to make the input text invisible.
    """

    attr = Color.Prompt
    n_rows, n_cols = window.getmaxyx()

    if hide:
        prompt += ' ' * (n_cols - len(prompt) - 1)
        window.addstr(n_rows-1, 0, prompt, attr)
        out = window.getstr(n_rows-1, 1)
    else:
        window.addstr(n_rows - 1, 0, prompt, attr)
        window.refresh()
        subwin = window.derwin(1, n_cols - len(prompt),
                               n_rows - 1, len(prompt))
        subwin.attrset(attr)
        out = text_input(subwin)

    return out


@contextmanager
def curses_session():
    """
    Setup terminal and initialize curses.
    """

    try:
        # Curses must wait for some time after the Escape key is pressed to
        # check if it is the beginning of an escape sequence indicating a
        # special key. The default wait time is 1 second, which means that
        # getch() will not return the escape key (27) until a full second
        # after it has been pressed.
        # Turn this down to 25 ms, which is close to what VIM uses.
        # http://stackoverflow.com/questions/27372068
        os.environ['ESCDELAY'] = '25'

        # Initialize curses
        stdscr = curses.initscr()

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)

        # Start color, too.  Harmless if the terminal doesn't have
        # color; user can test with has_color() later on.  The try/catch
        # works around a minor bit of over-conscientiousness in the curses
        # module -- the error return from C start_color() is ignorable.
        try:
            curses.start_color()
        except:
            pass

        Color.init()

        # Hide blinking cursor
        curses.curs_set(0)

        yield stdscr

    finally:

        if stdscr is not None:
            stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

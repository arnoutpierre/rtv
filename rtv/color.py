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

__all__ = ['Color']


class Color(object):

    """
    Colors and themes management
    """

    _colors = {}
    _default_color = -1
    _colors_range = 0

    @classmethod
    def init(cls):
        """
        Initialize color pairs inside of curses using the default background.

        This should be called once during the curses initial setup. Afterwards,
        curses color pairs can be accessed directly through class attributes.
        """

        # Get terminal's colors depth
        cls._colors_range = curses.tigetnum("colors")

        # Assign the terminal's default (background) color to code -1
        curses.use_default_colors()

        cls._colors.update(config.default_colors)
        if config.theme is not None:
            cls._colors.update(cls.load_colors(config.theme))

        for index, (attr, code) in enumerate(cls._colors.items(), start=1):
            code = cls.verify_color(code)
            curses.init_pair(index, code[0], code[1])
            color = curses.color_pair(index)
            for f in code[2:4]: color |= f
            setattr(cls, attr, color)

        # Load levels as colors
        cls._levels = [0]
        for color in config.levels:
            color = cls.verify_color(color)
            index += 1
            curses.init_pair(index, color[0], color[1])
            cls._levels.append(curses.color_pair(index))

    @classmethod
    def verify_color(cls, color_tuple):
        """ Verify colors in color_tuple and return expected tuple """

        color_tuple = list(color_tuple)
        color_tuple[0] = cls.to_allowed(color_tuple[0])
        color_tuple[1] = cls.to_allowed(color_tuple[1])
        return tuple(color_tuple)

    @classmethod
    def is_allowed(cls, color):
        """ Check if color is allowed regarding _colors_range """

        if int(color) < int(cls._colors_range) and int(color) > -2:
            return True
        else:
            return False

    @classmethod
    def to_allowed(cls, color):
        """ Check if color is allowed, if not return default color """

        return color if cls.is_allowed(color) else cls._default_color

    @classmethod
    def load_colors(cls, theme):
        """ Loop in themes and load colors """

        # get all available themes
        themes = cls.load_themes()
        # get theme to use if exists
        if theme in themes.keys():
            theme  = themes[theme]
        else:
            theme = {}

        # compute colors hash
        colors = {}
        # loop in theme entries
        for key in theme:
            values = []
            for value in "".join(theme[key].split()).split(','):
                # check for aliases
                if value in config.color_aliases.keys():
                    values.append(config.color_aliases[value])
                else:
                    # integer is required
                    try:
                        values.append(int(value))
                    except:
                        pass

            colors[key] = values
        return colors

    @classmethod
    def load_themes(cls):
        """ Load all themes in config paths, return theme indexed hash of colors  """

        # compute color config paths
        # should be located in ~/.config/rtv/colors or ~/.rtv/colors
        HOME = os.path.expanduser('~')
        XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))
        color_config_paths = [
            os.path.join(XDG_CONFIG_HOME, 'rtv', 'themes'),
            os.path.join(HOME, '.rtv', 'themes')
        ]

        themes = {}

        # loop in each config path
        # loads every themes found, override when duplicate
        for path in color_config_paths:
            if os.path.exists(path):
                for file_name in os.listdir(path):
                    if file_name.endswith(".cfg"):
                        # init configparser instance
                        config = configparser.ConfigParser()
                        config.optionxform = str

                        # get sections defined in current file
                        file_path = "%s/%s" % (path, file_name)
                        config.read(file_path)
                        # index themes by section id
                        for section in config.sections():
                            themes[section] = dict(config.items(section))

        return themes

    @classmethod
    def get_level(cls, level):
        """ Return color level """

        return cls._levels[level % len(cls._levels)]


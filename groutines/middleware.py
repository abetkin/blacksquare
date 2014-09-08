# -*- coding: utf-8 -*-

from .logger import events as log_events, clear as clear_log
from . import InteractiveScenario

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.config.loader import Config
from IPython.terminal.embed import InteractiveShellEmbed

@magics_class
class EventsMagics(Magics):
    "Magics that hold additional state"

    def __init__(self, shell, scenario):
        super(EventsMagics, self).__init__(shell)
        self.scenario = scenario

    @line_magic
    def events(self, line):
        try:
            self.scenario.result
        except AttributeError:
            self.scenario.wait()

        if line:
            return log_events[int(line) - 1]
        return log_events


class GMiddleware(object):

    def __init__(self):
        self.ipshell = InteractiveShellEmbed(config=Config())

    def process_view(self, request, view_func, view_args, view_kwargs):
        s = InteractiveScenario(view_func, (request,))

        magics = EventsMagics(self.ipshell, s)
        self.ipshell.register_magics(magics)

        clear_log()
        self.ipshell('Hello')

        try:
            return s.result
        except AttributeError:
            return s.wait()

    def get_options(self):
        # A stub.
        # Options can be set in settings.py
        # and overwritten with request arguments
        return {
            'shell_on_start': False,
        }

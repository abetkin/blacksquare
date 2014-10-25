from IPython.core.magic import Magics, magics_class, line_magic
from IPython.config.loader import Config

from ..core.objects import Logger

@magics_class
class BlackMagics(Magics):

    #def __init__(self, *a, **kw):
    #    1

    @line_magic
    def clearlog(self, line):
        1

    @line_magic
    def events(self, line):
        logger = Logger.instance()
        if not line:
            return logger

        event = logger[int(line)]
        return event

    @line_magic
    def bp(self, line):
        1

def load_ipython_extension(ip):
    black_magics = BlackMagics(ip)
    ip.register_magics(black_magics)
    #ip.events.register('pre_run_cell', auto_reload.pre_run_cell)
    #ip.events.register('post_execute', auto_reload.post_execute_hook)

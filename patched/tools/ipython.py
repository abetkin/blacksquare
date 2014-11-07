from IPython.core.magic import Magics, magics_class, line_magic

from ..core.objects import Logger

@magics_class
class BlackMagics(Magics):
    '''
    The `events` magics.
    '''

    @line_magic
    def events(self, line):
        logger = Logger.instance()
        if not line:
            return logger

        event = logger[int(line)]
        return event

def load_ipython_extension(ip):
    ip.register_magics(BlackMagics)

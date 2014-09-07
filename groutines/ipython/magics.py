
from IPython.core.magic import Magics, magics_class, line_magic, \
                                cell_magic, line_cell_magic, get_ipython

@magics_class
class GLoggerMagics(Magics):
    "Magics that hold additional state"

    def __init__(self, shell, data):
        # You must call the parent constructor
        super(GLoggerMagics, self).__init__(shell)
        self.data = data

    @line_magic
    def events(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return line

# This class must then be registered with a manually created instance,
# since its constructor has different arguments from the default:
ip = get_ipython()
magics = StatefulMagics(ip, 'some_data')
ip.register_magics(magics)

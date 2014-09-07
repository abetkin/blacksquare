# -*- coding: utf-8 -*-




from .logger import events as log_events
from . import InteractiveScenario

from IPython.core.magic import Magics, magics_class, line_magic

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
            self.scenario.switch()

        if line:
            return log_events[int(line)]
        return log_events


class GMiddleware(object):

    def __init__(self):
        from IPython.config.loader import Config
        try:
            get_ipython
        except NameError:
            nested = 0
            cfg = Config()
            prompt_config = cfg.PromptManager
            prompt_config.in_template = 'In <\\#>: '
            prompt_config.in2_template = '   .\\D.: '
            prompt_config.out_template = 'Out<\\#>: '
        else:
            print("Running nested copies of IPython.")
            print("The prompts for the nested copy have been modified")
            cfg = Config()
            nested = 1

        # First import the embeddable shell class
        from IPython.terminal.embed import InteractiveShellEmbed

        # Now create an instance of the embeddable shell. The first argument is a
        # string with options exactly as you would type them if you were starting
        # IPython at the system command line. Any parameters you want to define for
        # configuration can thus be specified here.
        self.ipshell = InteractiveShellEmbed(config=Config(),
                               banner1 = 'Dropping into IPython',
                               exit_msg = 'Leaving Interpreter, back to program.')
        magics = EventsMagics(self.ipshell, )


        self.ipshell.register_magics(EventsMagics)


    def process_view(self, request, view_func, view_args, view_kwargs):
        #import ipdb
        #with ipdb.launch_ipdb_on_exception():

        s = InteractiveScenario(view_func, (request,))

        #if self.get_options().get('shell_on_start'):
            #import IPython
            #IPython.embed()


        self.ipshell('Hello')



        #try:
        #    return s.result
        #except AttributeError:
        #    return s.wait()
        #
        ## Shell is shown after the scenario was executed
        #result = s.wait()
        #import IPython
        #IPython.embed()
        #
        #return result


    def get_options(self):
        # A stub.
        # Options can be set in settings.py
        # and overwritten with request arguments
        return {
            'shell_on_start': False,
        }

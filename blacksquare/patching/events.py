import inspect
import sys
import pdb


from ..core.events import Event, LoggableEvent
from .. import get_config, get_context

from IPython.lib.pretty import pretty

from ..util import ParentContextMixin

class FunctionExecuted(ParentContextMixin, LoggableEvent):

    # wrapper -> func
    def __init__(self, args, kwargs, ret):
        #self.wrapper = wrapper
        function = self.context.get('wrapper_func') or self.context['wrapper_func']
        sig = inspect.signature(function) # FIXME
        self.call_args = sig.bind(*args, **kwargs).arguments
        self.rv = ret

    def stop_on_breakpoint(self):
        config = get_config()
        if config.debugger == 'ipdb':
            try:
                import ipdb
                set_trace = ipdb.set_trace
            except:
                set_trace = pdb.set_trace
        else:
            set_trace = pdb.set_trace
        frame = sys._getframe()
        for _ in range(4):
            frame = frame.f_back

        if not config.fake_interactive_shell:
            set_trace(frame)
        else:
            config.fake_interactive_shell(frame.f_locals, frame.f_globals)


    def handle(self):
        if self.index in get_config().breakpoints:
            self.stop_on_breakpoint()
        # auto stop on error ?

    #FIXME
    def __dir__(self):
        names = super().__dir__()
        names.extend(self.call_args.keys())
        return names

    def __getattr__(self, name):
        if name in self.call_args:
            return self.call_args[name]
        raise AttributeError(name)

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Call(...)')
            return
        with p.group(5, 'Call(', ')'):
            #TODO function name
            for attr, value in self.call_args.items():
                p.text('%s = %s,' % (attr, value))
                p.breakable()
            p.text('rv = %s' % self.rv)




class ReplacementFunctionExecuted(FunctionExecuted):

    def _log_pretty_(self, p, cycle):
        if cycle:
            p.text('FunctionCall(...)')
            return
        p.text('Call to ')
        p.text(self.wrapper.wrapped_func.__name__)
        with p.group(2, '', ''):
            p.breakable()
            p.text('( => ')
            p.text(self.wrapper.wrapper_func.__name__)
            p.text(')')


class HookFunctionExecuted(FunctionExecuted):

    def __init__(self, wrapper, args, kwargs, ret):
        self.wrapper = wrapper
        sig = inspect.signature(wrapper._execute)
        self.call_args = sig.bind(*args, **kwargs).arguments
        self.rv = ret

    #TODO: let override this function
    def _log_pretty_(self, p, cycle):
        if cycle:
            p.text('HookFunction(..)')
            return
        p.text(self.wrapper.wrapped_func.__name__) #(a=1,b=..)
        p.text(' returned')
        p.breakable()
        p.text( pretty(self.rv))


class PatchSuiteStart(Event):

    @classmethod
    def handle(cls, suite):
        ctrl = get_config().get_controller_class().instance()
        ctrl.suite_start(suite)


class PatchSuiteFinish(Event):

    @classmethod
    def handle(cls, suite):
        ctrl = get_config().get_controller_class().instance()
        ctrl.suite_finish(suite)


class ContextChange(Event):

    @classmethod
    def handle(cls, name):
        'Nothing yet.'

import inspect
import sys
import pdb


from ..core.events import LoggableEvent
from .. import get_config, get_context


class FunctionExecuted(LoggableEvent):

    def __init__(self, wrapper, args, kwargs, ret):
        self.wrapper = wrapper
        sig = inspect.signature(wrapper._execute)
        self.call_args = sig.bind(*args, **kwargs)
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
        #TODO: auto stop on error
        if self.index in get_config().breakpoints:
            self.stop_on_breakpoint()

    def __str__(self):
        from ..util import obj_formatter
        return obj_formatter.format(self.record_format, self)



class ReplacementFunctionExecuted(FunctionExecuted):

    record_format = (
        "Call to {wrapper.wrapped_func.__name__} ( => "
        "{wrapper.wrapper_func.__name__})")

class HookFunctionExecuted(FunctionExecuted):

    def __init__(self, wrapper, args, kwargs, ret):
        self.wrapper = wrapper
        sig = inspect.signature(wrapper.callable)
        self.call_args = sig.bind(*args, return_value=ret, **kwargs)
        self.rv = ret

    record_format = (
        "Call to {wrapper.wrapped.__name__} ( + "
        "{wrapper.wrapper_func.__name__})")


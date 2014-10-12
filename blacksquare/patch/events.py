import inspect

from ..core.events import LoggableEvent
from ..config.core import Config


class FunctionExecuted(LoggableEvent):

    def __init__(self, wrapper, args, kwargs, rv):
        self.wrapper = wrapper
        sig = inspect.signature(wrapper)
        self.call_args = sig.bind(*args, **kwargs)
        self.rv = rv

    def embed_shell_if_breakpoint(self):
        config = Config.instance()
        if config.is_set_bp_for(self.wrapper):
            from ..manage.context import ContextTree
            ctx = ContextTree.instance()
            if config.test_interactive:
                config.test_interactive(ctx)
                return
            try:
                assert config.use_ipython
                import IPython
                IPython.embed()
            except (ImportError, AssertionError):
                import code
                code.interact(local={'ctx': ctx})

    def handle(self):
        self.embed_shell_if_breakpoint()

    def __str__(self):
        if self.wrapper.replacement:
            record_format = (
                "Call to {wrapper.wrapped.__name__} ( => "
                "{wrapper.patch._replacement_func.__name__})")
        else:
            record_format = (
                "Call to {wrapper.wrapped.__name__} ( + "
                "{wrapper.patch._hook_func.__name__})")
        from ..util import obj_formatter
        return obj_formatter.format(record_format, self)



class ReplacementFunctionExecuted(FunctionExecuted):
    pass

class OriginalFunctionExecuted(FunctionExecuted):
    pass


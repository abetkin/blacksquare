from .core.threadlocal import ThreadLocalMixin

class Config(ThreadLocalMixin):

    global_name = "config"

    def __init__(self):
        # maybe read from somewhere
        self._event_handlers = {}

    def get_event_handlers(self, event_cls):
        return self._event_handlers.get(event_cls, ())

    def register_event_handler(self, event_cls, handler):
        self._event_handlers.setdefault(event_cls, []).append(handler)

    def unregister_event_handler(self, event_cls, handler):
        handlers = self._event_handlers[event_cls]
        handlers.remove(handler)

    def get_controller_class(self):
        from blacksquare.manage.handlers import ManagersStack, GlobalPatches
        return GlobalPatches

    use_ipython = True

    test_interactive = False

    def is_set_bp_for(self, wrapper):
        return False

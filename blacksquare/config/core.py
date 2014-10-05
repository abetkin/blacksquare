from ..core.threadlocal import ThreadLocalMixin

class Config(ThreadLocalMixin):

    global_name = "config"

    def __init__(self):
        'read from somewhere'

    def get_event_handlers(self, event_cls):
        return []

    def get_controller_class(self):
        from blacksquare.manage.handlers import ManagersStack, GlobalPatches
        return GlobalPatches

    use_ipython = True

    test_interactive = False

    def is_set_bp_for(self, wrapper):
        return False

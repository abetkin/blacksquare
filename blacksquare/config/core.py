from ..core.threadlocal import ThreadLocalMixin

class Config(ThreadLocalMixin):


    def __init__(self):
        'read from somewhere'

    def get_event_handlers(self, event_cls):
        return []

    def get_controller_class(self):
        from blacksquare.manager.events import ManagersStack
        return ManagersStack

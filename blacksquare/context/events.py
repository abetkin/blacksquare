
from ..core.events import Event
from ..config.core import Config

class ContextChange(Event):

    @classmethod
    def handle(cls, name):
        ctrl = Config.instance().get_controller_class().instance()
        ctrl.remove_dependency(name)

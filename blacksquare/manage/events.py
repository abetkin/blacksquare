from ..core.events import Event
from ..config.core import Config


class PatchesEnter(Event):
    
    @classmethod
    def handle(cls, patches, manager):
        ctrl = Config.instance().get_controller_class().instance()
        ctrl.add_patches(patches, manager)


class PatchesExit(Event):

    @classmethod
    def handle(cls, manager):
        ctrl = Config.instance().get_controller_class().instance()
        ctrl.manager_exit(manager)


class ContextChange(Event):

    @classmethod
    def handle(cls, name):
        ctrl = Config.instance().get_controller_class().instance()
        ctrl.remove_dependency(name)


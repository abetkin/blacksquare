from ..core.events import Event
from .. import get_config


class PatchesEnter(Event):
    
    @classmethod
    def handle(cls, patches, manager):
        ctrl = get_config().get_controller_class().instance()
        ctrl.add_patches(patches, manager)


class PatchesExit(Event):

    @classmethod
    def handle(cls, manager):
        ctrl = get_config().get_controller_class().instance()
        ctrl.manager_exit(manager)


class ContextChange(Event):

    @classmethod
    def handle(cls, name):
        '''
        ctrl = get_config().get_controller_class().instance()
        ctrl.remove_dependency(name)
        '''


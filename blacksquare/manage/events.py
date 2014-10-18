from ..core.events import Event
from .. import get_config


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


from ..core.events import Event
from ..manager.events import DependenciesTracker

class ContextChange(Event):
    handlers = [DependenciesTracker.remove_dependency]


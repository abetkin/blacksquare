from ..core.events import Event
from ..context import ContextTree

class DependenciesTracker:

    dependencies = {}

    @classmethod
    def process_dependencies(cls, patches):
        tree = ContextTree.instance()
        for patch in patches:
            deps = patch.get_dependencies()
            if not deps:
                patch.on()
            for dep in deps:
                assert dep not in tree
                cls.dependencies.setdefault(dep, set()).add(patch)

    @classmethod
    def remove_dependency(cls, name):
        patches = cls.dependencies.get(name)
        if not patches:
            return
        tree = ContextTree.instance()
        for patch in patches:
            for dep in patch.get_dependencies():
                if dep not in tree:
                    break
            else:
                patch.on()


class SessionStart(Event):
    
    handlers = [DependenciesTracker.process_dependencies]


class SessionEnd(Event):
    pass

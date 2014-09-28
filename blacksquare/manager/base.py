from .events import SessionStart, SessionEnd

class PatchManager:

    def __init__(self, config):
        self.patches = config.get_patches()

    def __enter__(self):
        SessionStart.emit(self.patches)

    def __exit__(self, *exc_info):
        if exc_info[0]: #TODO
            raise
        for patch in self.patches:
            patch.off()
        SessionEnd.emit()


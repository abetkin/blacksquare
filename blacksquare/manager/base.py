from .events import PatchesEnter, PatchesExit

class Patches:

    # context mgr that lets to add patches

    def __init__(self, *patches):
        self.patches = patches

    #@classmethod
    #def add_patches(cls, *patches)

    def __enter__(self):
        PatchesEnter.emit(self.patches, self)
        return self

    def __exit__(self, *exc_info):
        if exc_info[0]: #TODO
            raise
        PatchesExit.emit(self)


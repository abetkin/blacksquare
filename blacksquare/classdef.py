
from . import Container, Patch

class patch(type):
    '''
    '''

    #@classmethod
    #def __prepare__(metacls, name, bases#, attrs=None
    #                ):
    #    return {}



    def __new__(cls, name, bases, classdict):
        try:
            (old_class,) = bases
        except ValueError:
            raise AssertionError("Patch can extend only the class being patched")
        if getattr(cls, 'patch_only', ()):
            classdict = {name: attr for name, attr in classdict.items()
                         if name in cls.patch_only}
        patches = []
        for name, func in classdict.items():
            if getattr(func, 'is_hook', None):
                kw = {'hook': func}
            else:
                kw = {'replacement': func}
            patch = Patch(old_class, name, **kw)
            patches.append(patch)
        return Container(patches)

    #def __init__(cls, *args, attrs=None):
    #    return type.__init__(cls, *args)


##############
'''
class New(Old):

    #repl
    def method(self):
        Old.method(self)
'''


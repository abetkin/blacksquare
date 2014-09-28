
from .base import Container, Patch

class patch(type):
    '''
    '''

    def __new__(cls, name, bases, classdict):
        try:
            (old_class,) = bases
        except ValueError:
            raise AssertionError("Patch can extend only the class being patched")
        classdict = {k:v for k,v in classdict.items() if not k.startswith('__')}
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

        #class Patches(Container):
        #    patches = patches

        return type('Patches', (Container,), {'patches': patches})

##############
'''
class New(Old):

    #repl
    def method(self):
        Old.method(self)
'''


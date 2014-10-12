
from .base import Patch

class patch(type):
    '''
    '''

    def __new__(cls, name, bases, classdict):
        try:
            (old_class,) = bases
        except ValueError:
            raise AssertionError("Patch can extend only the class being patched")
        classdict = {k:v for k,v in classdict.items()
                     if not k.startswith('__') or getattr(v, 'is_patch', False)
                     }
        def patches(*aaaaaaaa):#FIXME
            for name, func in classdict.items():
                if getattr(func, 'is_hook', None):
                    kw = {'hook': func}
                else:
                    kw = {'replacement': func}
                if name not in dir(old_class):
                    kw.update(insert=True)
                patch = Patch(old_class, name, **kw)
                yield patch

        return patches

#
#def meta(patch_class):
#    1

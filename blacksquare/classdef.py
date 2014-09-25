
from . import Container, Patch

def get_patches(old_class, classdict):
    for name, func in classdict.items():
        old_func = getattr(old_class, name) # detach ?
        yield Patch(old_class, old_func, func)


class patch(type):
    '''
    '''

    @classmethod
    def __prepare__(metacls, name, bases#, attrs=None
                    ):
        return {}



    def __new__(cls, name, bases, classdict, #attrs=None
                ):
        # classdict is all we need
        try:
            (old_class,) = bases
        except ValueError:
            print("Can patch only 1 class")
            raise
        if getattr(cls, 'patch_only', ()):
            classdict = {name: attr for name, attr in classdict.items()
                         if name in cls.patch_only}
        #return type.__new__(cls, name, (object,), classdict)
        patches = list(get_patches())
        return Container(patches)

    #def __init__(cls, *args, attrs=None):
    #    return type.__init__(cls, *args)

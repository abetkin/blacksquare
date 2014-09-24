

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
            classdict = {name: attr for name, attr in classdict
                         if name in cls.patch_only}
        #return type.__new__(cls, name, (object,), classdict)
        return

    #def __init__(cls, *args, attrs=None):
    #    return type.__init__(cls, *args)

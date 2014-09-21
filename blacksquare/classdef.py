

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
        if getattr(cls, 'patch_only', None):
            1
        return type.__new__(cls, name, bases, classdict)

    #def __init__(cls, *args, attrs=None):
    #    return type.__init__(cls, *args)

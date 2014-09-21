

class patch(type):
    '''
    '''

    @classmethod
    def __prepare__(metacls, name, bases, attrs=None):
        if not attrs:
            return {}

        def property_(attr):

            def getter(self):
                return getattr(self, '_' + attr)

            def setter(self, value):
                setattr(self, '_' + attr, value)

            return property(getter, setter)

        return {attr: property_(attr) for attr in attrs}


    def __new__(cls, name, bases, classdict, #attrs=None
                ):
        # assert 1 base
        return type.__new__(cls, name, bases , classdict)

    def __init__(cls, *args, attrs=None):
        return type.__init__(cls, *args)

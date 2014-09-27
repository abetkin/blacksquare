import threading

tlocal = threading.local()

class ThreadLocalMixin:

    default_init_args = ()
    default_init_kwargs = {}

    @classmethod
    def get_global_name(cls):
        if hasattr(cls, 'global_name'):
            return cls.global_name
        return cls.__name__.lower()

    def __new__(cls, *args, **kw):
        instance = super(ThreadLocalMixin, cls).__new__(cls, *args, **kw) #PY2 :(
        setattr(tlocal, cls.get_global_name(), instance)
        return instance

    @classmethod
    def instance(cls):
        name = cls.get_global_name()
        if not hasattr(tlocal, name):
            cls(*cls.default_init_args, **cls.default_init_kwargs)
        return getattr(tlocal, name)

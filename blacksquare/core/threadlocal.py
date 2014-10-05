import threading

tlocal = threading.local()

class ThreadLocalMixin:

    default_init_args = ()
    default_init_kwargs = {}

    @classmethod
    def _get_instance(cls):
        obj = tlocal
        for part in cls.global_name.split('.'):
            parent = obj
            obj = getattr(parent, part)
        return obj

    @classmethod
    def _set_instance(cls, instance):
        path, sep, attr = cls.global_name.rpartition('.')
        path = path.split('.') if path else ()
        obj = tlocal
        for part in path:
            parent = obj
            obj = getattr(parent, part)
        setattr(obj, attr, instance)

    @classmethod
    def _make_instance(cls):
        return cls(*cls.default_init_args, **cls.default_init_kwargs)

    def __new__(cls, *args, **kw):
        instance = super(ThreadLocalMixin, cls).__new__(cls, *args, **kw) #PY2 :(
        cls._set_instance(instance)
        return instance

    @classmethod
    def instance(cls):
        try:
            inst = cls._get_instance()
        except AttributeError:
            inst = cls._make_instance()
            cls._set_instance(inst)
        return inst

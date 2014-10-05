import threading

threadlocal = threading.local()

class ThreadLocalMixin:

    @classmethod
    def _get_instance(cls):
        obj = threadlocal
        for part in cls.global_name.split('.'):
            parent = obj
            obj = getattr(parent, part)
        return obj

    @classmethod
    def _set_instance(cls, instance):
        path, sep, attr = cls.global_name.rpartition('.')
        path = path.split('.') if path else ()
        obj = threadlocal
        for part in path:
            parent = obj
            obj = getattr(parent, part)
        setattr(obj, attr, instance)

    @classmethod
    def make_instance(cls):
        'Can be overriden.'
        return cls()

    def __new__(cls, *args, **kw):
        instance = super(ThreadLocalMixin, cls).__new__(cls, *args, **kw) #PY2 :(
        cls._set_instance(instance)
        return instance

    @classmethod
    def instance(cls):
        try:
            inst = cls._get_instance()
        except AttributeError:
            inst = cls.make_instance()
            cls._set_instance(inst)
        return inst

from .base import ThreadLocalMixin

class Config(ThreadLocalMixin):

    def __init__(self):
        'read from somewhere'

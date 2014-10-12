
from .manage.context import ContextTree

def get_context():
    return ContextTree.instance()

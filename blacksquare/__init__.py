

def get_context():
    from .manage.context import ContextTree
    return ContextTree.instance()

def get_config():
    from .config import Config
    return Config.instance()

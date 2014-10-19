from .core.objects import ContextTree, Config

def get_context():
    return ContextTree.instance()

def get_config():
    return Config.instance()

from .core.objects import ContextTree, Config, Logger

def get_context():
    return ContextTree.instance()

def get_config():
    return Config.instance()

def get_logger():
    return Logger.instance()

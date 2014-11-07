__version__ = '0.1'

from .core.objects import Storage, Config, Logger

def get_storage():
    return Storage.instance()

def get_config():
    return Config.instance()

def get_logger():
    return Logger.instance()

from .patching import PatchSuite, patch, wrappers

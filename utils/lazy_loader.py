import importlib

class LazyLoader:
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def __getattr__(self, name):
        if self.module is None:
            self.module = importlib.import_module(self.module_name)
        return getattr(self.module, name)
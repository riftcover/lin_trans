from nice_ui.ui.SingalBridge import DataBridge

class SingletonDataBridge:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DataBridge()
        return cls._instance

data_bridge = SingletonDataBridge.get_instance()

class Singleton(object):

    __instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

class SingletonNew(type):  
    def __init__(cls, name, bases, dict):  
        super(SingletonNew, cls).__init__(name, bases, dict)  
        cls._instance = None  
    
    def __call__(cls, *args, **kw):  
        if cls._instance is None:  
            cls._instance = super(SingletonNew, cls).__call__(*args, **kw)  
        return cls._instance

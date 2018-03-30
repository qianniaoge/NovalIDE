class ProjectConfiguration(object):
    
    PROJECT_SRC_PATH_ADD_TO_PYTHONPATH = 1
    PROJECT_PATH_ADD_TO_PYTHONPATH = 2
    NONE_PATH_ADD_TO_PYTHONPATH = 3
    def __init__(self,name,location,interpreter,is_project_dir_created,pythonpath_pattern):
        self._name = name
        self._location = location
        self._interpreter = interpreter
        self._is_project_dir_created = is_project_dir_created
        self._pythonpath_pattern = pythonpath_pattern
        
    @property
    def Name(self):
        return self._name
        
    @property
    def Location(self):
        return self._location
        
    @property
    def Interpreter(self):
        return self._interpreter
        
    @property
    def IsProjectDirCreated(self):
        return self._is_project_dir_created
        
    @property
    def PythonPathPattern(self):
        return self._pythonpath_pattern
    
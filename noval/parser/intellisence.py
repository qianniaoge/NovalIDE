import noval.util.appdirs as appdirs
import noval.tool.Interpreter as Interpreter
import subprocess
import noval.util.sysutils as sysutilslib
from noval.tool import Singleton 
import os
import threading
import time

class IntellisenceDataLoader(object):
    def __init__(self,data_location):
        self._data_location = data_location
        self.module_dicts = {}
        
    def Start(self,interpreter,p_obj):
        t = threading.Thread(target=self.Load,args=(interpreter,p_obj))
        t.start()
    
    def Load(self,interpreter,p_obj):
       # while p_obj.poll() is not None:
        #    print 'analyse process is still running+++++++++++++++'
         #   time.sleep(1)
        p_obj.wait()
        intellisence_data_path = os.path.join(self._data_location,interpreter.Version)
        if not os.path.exists(intellisence_data_path):
            return
        for filename in os.listdir(intellisence_data_path):
            module_name = '.'.join(filename.split(".")[0:-1])
            self.module_dicts[module_name] = os.path.join(intellisence_data_path,filename)

class IntellisenceManager(object):
    __metaclass__ = Singleton.SingletonNew
    def __init__(self):
        self.data_root_path = os.path.join(appdirs.getAppDataFolder(),"intellisence")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path )
        
    def generate_intellisence_data(self,interpreter):
        sys_path_list = interpreter.SyspathList
        script_path = os.path.join(sysutilslib.mainModuleDir, "noval", "parser", "factory.py")
        cmd_list = [interpreter.Path,script_path,self.data_root_path]
      ##  p = subprocess.Popen(cmd_list,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    ##    subprocess.Popen(cmd_list,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p = subprocess.Popen(cmd_list,shell=False)
        self.load_intellisence_data(Interpreter.InterpreterManager().GetDefaultInterpreter(),p)
        
    def generate_default_intellisence_data(self):
        default_interpreter = Interpreter.InterpreterManager().GetDefaultInterpreter()
        if default_interpreter is None:
            return
        self.generate_intellisence_data(default_interpreter)
        
    def load_intellisence_data(self,interpreter,p_obj):
        self._loader.Start(interpreter,p_obj)

            
            
        
        
        

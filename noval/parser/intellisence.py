import noval.util.appdirs as appdirs
import noval.tool.Interpreter as Interpreter
import subprocess
import noval.util.sysutils as sysutilslib
from noval.tool import Singleton 
import os
import threading
import time
import fileparser
import config

class IntellisenceDataLoader(object):
    def __init__(self,data_location):
        self._data_location = data_location
        self.module_dicts = {}
        
    def Start(self,interpreter,p_obj,progress_dlg):
        t = threading.Thread(target=self.Load,args=(interpreter,p_obj,progress_dlg))
        t.start()
    
    def Load(self,interpreter,p_obj,progress_dlg):
        p_obj.wait()
        interpreter.Analysing = False
        if progress_dlg != None and sysutilslib.isWindows():
            progress_dlg.Destroy()
        root_path = os.path.join(self._data_location,str(interpreter.Id))
        intellisence_data_path = os.path.join(root_path,interpreter.Version)
        if not os.path.exists(intellisence_data_path):
            return
        name_sets = set()
        for filename in os.listdir(intellisence_data_path):
            module_name = '.'.join(filename.split(".")[0:-1])
            name_sets.add(module_name)
        for name in name_sets:
            d = dict(members=os.path.join(intellisence_data_path,name +".$members"),member_list=os.path.join(intellisence_data_path,name +".$memberlist"))
            self.module_dicts[name] = d

class IntellisenceManager(object):
    __metaclass__ = Singleton.SingletonNew
    def __init__(self):
        self.data_root_path = os.path.join(appdirs.getAppDataFolder(),"intellisence")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path )
        
    def generate_intellisence_data(self,interpreter,progress_dlg = None):
        sys_path_list = interpreter.SyspathList
        script_path = os.path.join(sysutilslib.mainModuleDir, "noval", "parser", "factory.py")
        cmd_list = [interpreter.Path,script_path,os.path.join(self.data_root_path,str(interpreter.Id))]
      ##  p = subprocess.Popen(cmd_list,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    ##    subprocess.Popen(cmd_list,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if sysutilslib.isWindows():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        interpreter.Analysing = True
        p = subprocess.Popen(cmd_list,startupinfo=startupinfo)
        self.load_intellisence_data(interpreter,p,progress_dlg)
        
    def generate_default_intellisence_data(self):
        default_interpreter = Interpreter.InterpreterManager().GetDefaultInterpreter()
        if default_interpreter is None:
            return
        self.generate_intellisence_data(default_interpreter)
        
    def load_intellisence_data(self,interpreter,p_obj,progress_dlg):
        self._loader.Start(interpreter,p_obj,progress_dlg)

    def load_member_list(self,member_list_path):
        with open(member_list_path) as f:
            return f.readlines()
        
    def find_name_definition(self,name_defintion):
        name_parts = name_defintion.split(".")
        module_name = name_parts[0].strip()
        name_part_count = len(name_parts)
        if self._loader.module_dicts.has_key(module_name):
            members_path = self._loader.module_dicts[module_name]['members']
            data = fileparser.load(members_path)
            module_path = data['path']
            if name_part_count == 1:
                return module_path,0
            return self.find_definition(module_path,data['childs'],name_parts[1:])
        else:
            return None,-1
        
    def find_definition(self,root_module_path,childs,names):
        for child in childs:
            if child['name'] == (names[0].strip()):
                if len(names) == 1:
                    if child['type'] != config.NODE_MODULE_TYPE:
                        return root_module_path,child['line']
                    else:
                        return child['path'],0
                else:
                    if child['type'] != config.NODE_MODULE_TYPE:
                        return self.find_definition(root_module_path,child['childs'],names[1:])
                    else:
                        members_path = self._loader.module_dicts[child['full_name']]['members']
                        data = fileparser.load(members_path)
                        module_path = data['path']
                        return self.find_definition(child['path'],data['childs'],names[1:])
        return None,-1

            
        
        
        

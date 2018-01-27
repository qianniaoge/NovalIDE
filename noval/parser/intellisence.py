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
import BuiltinModule
from utils import CmpMember
import glob
import nodeast
import scope
import pickle

class ModuleLoader(object):
    CHILD_KEY = "childs"
    NAME_KEY = "name"
    TYPE_KEY = "type"
    LINE_KEY = "line"
    COL_KEY = "col"
    PATH_KEY = "path"
    MEMBERS_KEY = "members"
    MEMBER_LIST_KEY = "member_list"
    FULL_NAME_KEY = "full_name"
    BUILTIN_KEY = "is_builtin"
    def __init__(self,name,members_file,member_list_file,mananger):
        self._name = name
        self._members_file = members_file
        self._member_list_file = member_list_file
        self._manager = mananger
        self._path = None
        self._is_builtin = False
    @property
    def Name(self):
        return self._name

    def LoadMembers(self):
        with open(self._members_file,'rb') as f:
            data = pickle.load(f)
            self._is_builtin = data.get(self._is_builtin,False)
            self._path = data.get(self.PATH_KEY)
            return data

    def LoadMembeList(self):
        with open(self._member_list_file) as f:
            return map(lambda s:s.strip(),f.readlines())

    def GetMemberList(self):
        member_list = self.LoadMembeList()
        member_list.sort(CmpMember)
        return member_list

    def GetMembersWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.GetMembers(names)

    def GetMembers(self,names):
        if len(names) == 0:
            return self.GetMemberList()
        data = self.LoadMembers()
        member = self.GetMember(data[self.CHILD_KEY],names)
        member_list = []
        if member is not None:
            if member[self.TYPE_KEY] == config.NODE_MODULE_TYPE:
                child_module = self._manager.GetModule(member[self.FULL_NAME_KEY])
                member_list = child_module.GetMemberList()
            else:
                if member.has_key(self.CHILD_KEY):
                    for child in member[self.CHILD_KEY]:
                        member_list.append(child[self.NAME_KEY])
        return member_list
        
    def GetMember(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return child
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.GetMember(child[self.CHILD_KEY],names[1:])
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return self.GetMember(data[self.CHILD_KEY],names[1:])
        return None

    def FindDefinitionWithName(self,name):
        strip_name = name.strip()
        if strip_name == "":
            names = []
        else:
            names = strip_name.split(".")
        return self.FindDefinition(names)

    def FindDefinition(self,names):
        data = self.LoadMembers()
        if self._is_builtin:
            return None
        if len(names) == 0:
            return self.MakeModuleScope()
        return self.FindChildDefinition(data[self.CHILD_KEY],names)

    def MakeModuleScope(self):
        module = nodeast.Module(self._name,self._path)
        module_scope = scope.ModuleScope(module,-1)
        return module_scope

    def MakeDefinitionScope(self,child):
        if child.get(self.TYPE_KEY) == config.NODE_MODULE_TYPE:
            child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
            child_module._path = child[self.PATH_KEY]
            return child_module.MakeModuleScope()
        module_scope = self.MakeModuleScope()
        self.MakeChildScope(child,module_scope.Module)
        module_scope.MakeModuleScopes()
        return module_scope.ChildScopes[0]
            
    def MakeChildScope(self,child,parent):
        name = child[self.NAME_KEY]
        line_no = child[self.LINE_KEY]
        col = child[self.COL_KEY]
        if child[self.TYPE_KEY] == config.NODE_FUNCDEF_TYPE:
            node = nodeast.FuncDef(name,line_no,col,parent)
        elif child[self.TYPE_KEY] == config.NODE_CLASSDEF_TYPE:
            node = nodeast.ClassDef(name,line_no,col,parent)
            for class_child in child.get(self.CHILD_KEY,[]):
                self.MakeChildScope(class_child,node)
        elif child[self.TYPE_KEY] == config.NODE_OBJECT_PROPERTY or \
                child[self.TYPE_KEY] == config.NODE_CLASS_PROPERTY:
            node = nodeast.PropertyDef(name,line_no,col,config.ASSIGN_TYPE_UNKNOWN,"",parent)
        elif child[self.TYPE_KEY] == config.NODE_UNKNOWN_TYPE:
            node = nodeast.UnknownNode(line_no,col,parent)
                
    def FindChildDefinition(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return self.MakeDefinitionScope(child)
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.FindChildDefinition(child[self.CHILD_KEY],names[1:])
                    else:
                        child_module = self._manager.GetModule(child[self.FULL_NAME_KEY])
                        data = child_module.LoadMembers()
                        return child_module.FindChildDefinition(child[self.PATH_KEY],data[self.CHILD_KEY],names[1:])
        return None
        
class IntellisenceDataLoader(object):
    def __init__(self,data_location,_builtin_data_location,manager):
        self._data_location = data_location
        self.__builtin_data_location = _builtin_data_location
        self.module_dicts = {}
        self.import_list = []
        self._builtin_module = None
        self._manager = manager
      
    def LodBuiltInData(self):
        builtin_data_path = self.__builtin_data_location
        if not os.path.exists(builtin_data_path):
            return
        self.LoadIntellisenceDirData(builtin_data_path)
    
    def LoadIntellisenceDirData(self,data_path):
        name_sets = set()
        for filepath in glob.glob(os.path.join(data_path,"*.$members")):
            filename = os.path.basename(filepath)
            module_name = '.'.join(filename.split(".")[0:-1])
            name_sets.add(module_name)
        for name in name_sets:
            d = dict(members=os.path.join(data_path,name +".$members"),\
                     member_list=os.path.join(data_path,name +".$memberlist"))
            self.module_dicts[name] = d

    def Load(self,interpreter):
        t = threading.Thread(target=self.LoadInterperterData,args=(interpreter,))
        t.start()
        
    def LoadInterperterData(self,interpreter):
        self.module_dicts.clear()
        self.import_list = []
        root_path = os.path.join(self._data_location,str(interpreter.Id))
        intellisence_data_path = os.path.join(root_path,interpreter.Version)
        if not os.path.exists(intellisence_data_path):
            return
        self.LoadIntellisenceDirData(intellisence_data_path)
        self.LodBuiltInData()
        self.LoadImportList()
        self.LoadBuiltinModule()
        
    def LoadImportList(self):
        for key in self.module_dicts.keys():
            if key.find(".") == -1:
                self.import_list.append(key)
        self.import_list.sort(CmpMember)
        
    @property
    def ImportList(self):
        return self.import_list
        
    def LoadBuiltinModule(self):
        builtin_module_loader = self._manager.GetModule("__builtin__")
        data = builtin_module_loader.LoadMembers()
        self._builtin_module = BuiltinModule.BuiltinModule(builtin_module_loader.Name)
        self._builtin_module.load(data)
        
    @property
    def BuiltinModule(self):
        return self._builtin_module

class IntellisenceManager(object):
    __metaclass__ = Singleton.SingletonNew
    def __init__(self):
        self.data_root_path = os.path.join(appdirs.getAppDataFolder(),"intellisence")
        if sysutilslib.isWindows():
            self._builtin_data_path = self.data_root_path
        else:
            self._builtin_data_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "data","intellisence","builtins")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path,self._builtin_data_path,self)
        self._is_running = False
        self._process_obj = None
        
    def Stop(self):
        if self._process_obj != None and self.IsRunning:
            self._process_obj.kill()
           # self._process_obj.terminate(gracePeriod=2.0)
            #os.killpg( p.pid,signal.SIGUSR1)
    @property
    def IsRunning(self):
        return self._is_running
        
    def generate_intellisence_data(self,interpreter,progress_dlg = None,load_data_end=False):
        sys_path_list = interpreter.SyspathList
        script_path = os.path.join(sysutilslib.mainModuleDir, "noval", "parser", "factory.py")
        database_version = config.DATABASE_VERSION
        cmd_list = [interpreter.Path,script_path,os.path.join(self.data_root_path,str(interpreter.Id)),\
                    database_version]
        if sysutilslib.isWindows():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        interpreter.Analysing = True
        self._is_running = interpreter.Analysing
        self._process_obj = subprocess.Popen(cmd_list,startupinfo=startupinfo)
        self.Wait(interpreter,progress_dlg,load_data_end)
        
    def Wait(self,interpreter,progress_dlg,load_data_end):
        t = threading.Thread(target=self.WaitProcessEnd,args=(interpreter,progress_dlg,load_data_end))
        t.start()
        
    def WaitProcessEnd(self,interpreter,progress_dlg,load_data_end):
        self._process_obj.wait()
        interpreter.Analysing = False
        self._is_running = interpreter.Analysing
        if progress_dlg != None:
            progress_dlg.KeepGoing = False
        if load_data_end:
            self.load_intellisence_data(interpreter)            
        
    def generate_default_intellisence_data(self):
        default_interpreter = Interpreter.InterpreterManager().GetDefaultInterpreter()
        if default_interpreter is None:
            return
        self.generate_intellisence_data(default_interpreter,load_data_end=True)
        
    def load_intellisence_data(self,interpreter):
        self._loader.Load(interpreter)
        
    def GetImportList(self):
        return self._loader.ImportList
        
    def GetBuiltinMemberList(self,name):
        if self._loader.BuiltinModule is None:
            return False,[]
        return self._loader.BuiltinModule.GetBuiltInTypeMembers(name)
        
    def GetMemberList(self,name):
        names = name.split(".")
        name_count = len(names)
        i = 0
        module_name = ""
        while i < name_count:
            fit_name = ".".join(names[:i])
            if self.HasModule(fit_name):
                module_name = fit_name
            else:
                break
        if not self.HasModule(module_name):
            return []
        module = self.GetModule(module_name)
        child_names = names[i:]
        return module.GetMembers(child_names)
        
    def GetBuiltinModule(self):
        return self._loader.BuiltinModule
        
    def GetTypeObjectMembers(self,obj_type):
        if self._loader.BuiltinModule is None or obj_type == config.ASSIGN_TYPE_UNKNOWN:
            return []
        type_obj = self._loader.BuiltinModule.GetTypeNode(obj_type)
        return type_obj.GetMemberList()

    def GetModule(self,name):
        if self._loader.module_dicts.has_key(name):
            return ModuleLoader(name,self._loader.module_dicts[name][ModuleLoader.MEMBERS_KEY],\
                        self._loader.module_dicts[name][ModuleLoader.MEMBER_LIST_KEY],self)
        return None

    def HasModule(self,name):
        return self._loader.module_dicts.has_key(name)

    def GetModuleMembers(self,module_name,child_name):
        modoule = self.GetModule(module_name)
        return modoule.GetMembersWithName(child_name)

    def GetModuleMember(self,module_name,child_name):
        modoule = self.GetModule(module_name)
        return modoule.FindDefinitionWithName(child_name)
        

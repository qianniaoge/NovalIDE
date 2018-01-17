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

class IntellisenceDataLoader(object):
    def __init__(self,data_location):
        self._data_location = data_location
        self.module_dicts = {}
        self.import_list = []
        self._builtin_module = None
      
    def LodBuiltInData(self):
        builtin_data_path = self._data_location
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
        builtin_members_file = os.path.join(self._data_location,"__builtin__.$members")
        self._builtin_module = BuiltinModule.BuiltinModule("__builtin__",builtin_members_file)
        self._builtin_module.load(builtin_members_file)
        
    @property
    def BuiltinModule(self):
        return self._builtin_module

class IntellisenceManager(object):
    __metaclass__ = Singleton.SingletonNew
    CHILD_KEY = "childs"
    NAME_KEY = "name"
    TYPE_KEY = "type"
    LINE_KEY = "line"
    COL_KEY = "col"
    PATH_KEY = "path"
    def __init__(self):
        self.data_root_path = os.path.join(appdirs.getAppDataFolder(),"intellisence")
        self.module_dicts = {}
        self._loader = IntellisenceDataLoader(self.data_root_path )
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
        if progress_dlg != None and sysutilslib.isWindows():
            progress_dlg.Destroy()
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

    def load_member_list(self,member_list_path):
        with open(member_list_path) as f:
            return map(lambda s:s.strip(),f.readlines())
        
    def find_name_definition(self,name_defintion):
        name_parts = name_defintion.split(".")
        module_name = name_parts[0].strip()
        name_part_count = len(name_parts)
        if self._loader.module_dicts.has_key(module_name):
            members_path = self._loader.module_dicts[module_name]['members']
            data = fileparser.load(members_path)
            if data.has_key("is_builtin") and data['is_builtin'] == True:
                return None
            module_path = data[self.PATH_KEY]
            if name_part_count == 1:
                return self.MakeChildScope(data,module_path)
            return self.find_definition(module_path,data[self.CHILD_KEY],name_parts[1:])
        else:
            return None

    def MakeDefScope(self,child,root_path):
        if child[self.TYPE_KEY] == config.NODE_MODULE_TYPE:
            module = nodeast.Module("",child[self.PATH_KEY])
            module_scope = scope.ModuleScope(module,-1)
            return module_scope
        module = nodeast.Module("",root_path)
        module_scope = scope.ModuleScope(module,-1)
        self.MakeChildScope(child,module)
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
                
    def find_definition(self,root_module_path,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return self.MakeDefScope(child,root_module_path)
##                    if child['type'] != config.NODE_MODULE_TYPE:
##                        ##return root_module_path,child['line']
##                        return self.MakeChildScope(child,root_module_path)
##                    else:
##                        return child['path'],0
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.find_definition(root_module_path,child[self.CHILD_KEY],names[1:])
                    else:
                        members_path = self._loader.module_dicts[child['full_name']]['members']
                        data = fileparser.load(members_path)
                        module_path = data[self.PATH_KEY]
                        return self.find_definition(child[self.PATH_KEY],data[self.CHILD_KEY],names[1:])
        return None
        
    def GetBuiltinMemberList(self,name):
        if self._loader.BuiltinModule is None:
            return False,[]
        return self._loader.BuiltinModule.GetBuiltInTypeMembers(name)
        
    def GetMemberList(self,name):
        name_parts = name.split(".")
        name_part_count = len(name_parts)
        if 1 == name_part_count:
            is_builtin_type, member_list = self.GetBuiltinMemberList(name)
            if is_builtin_type:
                return member_list
        module_name = name_parts[0].strip()
        if self._loader.module_dicts.has_key(module_name):
            if 1 == name_part_count:
                member_list_path = self._loader.module_dicts[module_name]['member_list']
                member_list = self.load_member_list(member_list_path)
                member_list.sort(CmpMember)
                return member_list
            else:
                member_list = self.FindModuleMembers(module_name,name_parts[1:])
                member_list.sort(CmpMember)
                return member_list
        return []
                
    def FindModuleMembers(self,module_name,names):
        members_path = self._loader.module_dicts[module_name]['members']
        data = fileparser.load(members_path)
        member = self.FindMember(data[self.CHILD_KEY],names)
        if member is not None:
            if member[self.TYPE_KEY] == config.NODE_MODULE_TYPE:
                member_list_path = self._loader.module_dicts[member['full_name']]['member_list']
                member_list = self.load_member_list(member_list_path)
                return member_list
            else:
                if member.has_key(self.CHILD_KEY):
                    members = []
                    for child in member[self.CHILD_KEY]:
                        members.append(child[self.NAME_KEY])
                    return members
        return []
        
    def FindMember(self,childs,names):
        for child in childs:
            if child[self.NAME_KEY] == (names[0].strip()):
                if len(names) == 1:
                    return child
                else:
                    if child[self.TYPE_KEY] != config.NODE_MODULE_TYPE:
                        return self.FindMember(child[self.CHILD_KEY],names[1:])
                    else:
                        members_path = self._loader.module_dicts[child['full_name']]['members']
                        data = fileparser.load(members_path)
                        module_path = data[self.PATH_KEY]
                        return self.FindMember(data[self.CHILD_KEY],names[1:])
        return None
        
    def GetBuiltinModule(self):
        return self._loader.BuiltinModule
        
    def GetTypeObjectMembers(self,obj_type):
        if self._loader.BuiltinModule is None or obj_type == config.ASSIGN_TYPE_UNKNOWN:
            return []
        type_obj = self._loader.BuiltinModule.GetTypeNode(obj_type)
        return type_obj.GetMemberList()

            
        
        
        

import wx
import sys
import os
from noval.tool.Singleton import Singleton
import noval.util.sysutils as sysutils
from noval.tool.consts import _ 
import pickle
import Interpreter
from noval.util.logger import app_debugLogger
import noval.parser.nodeast as nodeast
import json

class InterpreterManager(Singleton):
    
    interpreters = []
    DefaultInterpreter = None
    CurrentInterpreter = None
    KEY_PREFIX = "interpreters"
    
    def LoadDefaultInterpreter(self):
        if self.LoadPythonInterpretersFromConfig():
            self.SetCurrentInterpreter(self.DefaultInterpreter)
            return
        self.LoadPythonInterpreters()
        if 0 == len(self.interpreters):
            if sysutils.isWindows():
                dlg = wx.MessageDialog(None, _("No Python Interpreter Found In Your Computer,Will Use the Builtin Interpreter Instead"), \
                    _("No Python Interpreter Found"), wx.OK | wx.ICON_WARNING)
            else:
                dlg = wx.MessageDialog(None, _("No Python Interpreter Found!"), _("No Interpreter"), wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
        if sysutils.isWindows():
            self.LoadBuiltinInterpreter()
        if 1 == len(self.interpreters):
            self.MakeDefaultInterpreter()
        elif 1 < len(self.interpreters):
            self.ChooseDefaultInterpreter()
        self.SetCurrentInterpreter(self.DefaultInterpreter)
        self.SavePythonInterpretersConfig()
        
    def ChooseDefaultInterpreter(self):
        choices = []
        for interpreter in self.interpreters:
            choices.append(interpreter.Name)
        dlg = wx.SingleChoiceDialog(None, _("Please Choose Default Interpreter:"), _("Choose Interpreter"),choices)  
        if dlg.ShowModal() == wx.ID_OK:  
            name = dlg.GetStringSelection()
            interpreter = self.GetInterpreterByName(name)
            self.SetDefaultInterpreter(interpreter)
        else:
            wx.MessageBox(_("No Default Interpreter Selected, Application May not run normal!"),\
                          _("Choose Interpreter"),wx.OK | wx.ICON_WARNING)
            del self.interpreters[:]
        dlg.Destroy()
        
    def GetInterpreterByName(self,name):
        for interpreter in self.interpreters:
            if name == interpreter.Name:
                return interpreter
        return None
        
    def GetInterpreterByPath(self,path):
        for interpreter in self.interpreters:
            if path == interpreter.Path:
                return interpreter
        return None
        
    def LoadPythonInterpreters(self):
        if sysutils.isWindows():
            import _winreg
            ROOT_KEY_LIST = [_winreg.HKEY_LOCAL_MACHINE,_winreg.HKEY_CURRENT_USER]
            ROOT_KEY_NAMES = ['LOCAL_MACHINE','CURRENT_USER']
            for k,root_key in enumerate(ROOT_KEY_LIST):
                try:
                    open_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore")  
                    countkey = _winreg.QueryInfoKey(open_key)[0]  
                    keylist = []  
                    for i in range(int(countkey)):  
                        name = _winreg.EnumKey(open_key,i)
                        try:
                            child_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore\%s" % name)
                            install_path = _winreg.QueryValue(child_key,"InstallPath")
                            interpreter = Interpreter.PythonInterpreter(name,os.path.join(install_path,Interpreter.PythonInterpreter.CONSOLE_EXECUTABLE_NAME))
                            if not interpreter.IsValidInterpreter:
                                app_debugLogger.error("interpreter name %s path %s,version %s is not a valid interpreter",interpreter.Name,interpreter.Path,interpreter.Version)
                                continue
                            self.interpreters.append(interpreter)
                            app_debugLogger.info("load python interpreter from regkey success,path is %s,version is %s",interpreter.Path,interpreter.Version)
                            help_key = _winreg.OpenKey(child_key,"Help")
                            help_path = _winreg.QueryValue(help_key,"Main Python Documentation")
                            interpreter.HelpPath = help_path
                            app_debugLogger.info("interpreter %s,help path is %s",interpreter.Name,interpreter.HelpPath)
                        except Exception as e:
                            app_debugLogger.error("read python child regkey %s\\xxx\\%s error:%s",ROOT_KEY_NAMES[k],name,e)
                            continue
                except Exception as e:
                    app_debugLogger.error("load python interpreter from regkey %s error:%s",ROOT_KEY_NAMES[k],e)
                    continue
        else:
            executable_path = sys.executable
            install_path = os.path.dirname(executable_path)
            interpreter = Interpreter.PythonInterpreter("default",executable_path)
            self.interpreters.append(interpreter)
            
    def LoadPythonInterpretersFromConfig(self):
        config = wx.ConfigBase_Get()
        if sysutils.isWindows():
            ###dct = self.ConvertInterpretersToDictList()
            data = config.Read(self.KEY_PREFIX)
            if not data:
                return False
            lst = pickle.loads(data.encode('ascii'))
            for l in lst:
                is_builtin = l.get('is_builtin',False)
                if is_builtin:
                    interpreter = Interpreter.BuiltinPythonInterpreter(l['name'],l['path'],l['id'])
                else:
                    interpreter = Interpreter.PythonInterpreter(l['name'],l['path'],l['id'],True)
                interpreter.Default = l['default']
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                data = {
                    'version': l['version'],
                    'builtins': l['builtins'],
                    #'path_list' is the old key name of sys_path_list,we should make compatible of old version
                    'sys_path_list': l.get('sys_path_list',l.get('path_list')),
                    'python_path_list': l.get('python_path_list',[]),
                    'is_builtin':is_builtin
                }
                interpreter.SetInterpreter(**data)
                interpreter.HelpPath = l.get('help_path','')
                interpreter.Environ.SetEnviron(l.get('environ',{}))
                interpreter.Packages = l.get('packages',{})
                self.interpreters.append(interpreter)
                app_debugLogger.info('load python interpreter from app config success,name is %s,path is %s,version is %s,is builtin %s',\
                                     interpreter.Name,interpreter.Path,interpreter.Version,interpreter.IsBuiltIn)
        else:
            prefix = self.KEY_PREFIX
            data = config.Read(prefix)
            if not data:
                return False
            ids = data.split(os.pathsep)
            for id in ids:
                name = config.Read("%s/%s/Name" % (prefix,id))
                path = config.Read("%s/%s/Path" % (prefix,id))
                is_default = config.ReadInt("%s/%s/Default" % (prefix,id))
                version = config.Read("%s/%s/Version" % (prefix,id))
                sys_paths = config.Read("%s/%s/SysPathList" % (prefix,id))
                python_path_list = config.Read("%s/%s/PythonPathList" % (prefix,id),"")
                builtins = config.Read("%s/%s/Builtins" % (prefix,id))
                environ = json.loads(config.Read("%s/%s/Environ" % (prefix,id),"{}"))
                packages = json.loads(config.Read("%s/%s/Packages" % (prefix,id),"{}"))
                interpreter = Interpreter.PythonInterpreter(name,path,id,True)
                interpreter.Default = is_default
                interpreter.Environ.SetEnviron(environ)
                interpreter.Packages = packages
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                data = {
                    'version': version,
                    'builtins': builtins.split(os.pathsep),
                    'sys_path_list': sys_paths.split(os.pathsep),
                    'python_path_list':python_path_list.split(os.pathsep)
                }
                interpreter.SetInterpreter(**data)
                self.interpreters.append(interpreter)
        
        if len(self.interpreters) > 0:
            return True
        return False
    
    def ConvertInterpretersToDictList(self):
        lst = []
        for interpreter in self.interpreters:
            d = dict(id=interpreter.Id,name=interpreter.Name,version=interpreter.Version,path=interpreter.Path,\
                        default=interpreter.Default,sys_path_list=interpreter.SysPathList,python_path_list=interpreter.PythonPathList,\
                        builtins=interpreter.Builtins,help_path=interpreter.HelpPath,\
                        environ=interpreter.Environ.environ,packages=interpreter.Packages,is_builtin=interpreter.IsBuiltIn)
            lst.append(d)
        return lst
        
    def SavePythonInterpretersConfig(self):
        config = wx.ConfigBase_Get()
        if sysutils.isWindows():
            dct = self.ConvertInterpretersToDictList()
            if dct == []:
                return
            config.Write(self.KEY_PREFIX ,pickle.dumps(dct))   
        else:
            prefix = self.KEY_PREFIX
            id_list = [ str(kl.Id) for kl in self.interpreters ]
            config.Write(prefix,os.pathsep.join(id_list))
            for kl in self.interpreters:
                config.WriteInt("%s/%d/Id"%(prefix,kl.Id),kl.Id)
                config.Write("%s/%d/Name"%(prefix,kl.Id),kl.Name)
                config.Write("%s/%d/Version"%(prefix,kl.Id),kl.Version)
                config.Write("%s/%d/Path"%(prefix,kl.Id),kl.Path)
                config.WriteInt("%s/%d/Default"%(prefix,kl.Id),kl.Default)
                config.Write("%s/%d/SysPathList"%(prefix,kl.Id),os.pathsep.join(kl.SysPathList))
                config.Write("%s/%d/PythonPathList"%(prefix,kl.Id),os.pathsep.join(kl.PythonPathList))
                config.Write("%s/%d/Builtins"%(prefix,kl.Id),os.pathsep.join(kl.Builtins))
                config.Write("%s/%d/Environ"%(prefix,kl.Id),json.dumps(kl.Environ.environ))
                config.Write("%s/%d/Packages"%(prefix,kl.Id),json.dumps(kl.Packages))
        
    def AddPythonInterpreter(self,interpreter_path,name):
        interpreter = Interpreter.PythonInterpreter(name,interpreter_path)
        if not interpreter.IsValidInterpreter:
            raise InterpreterAddError(_("%s is not a valid interpreter path") % interpreter_path)
        interpreter.Name = name
        if self.CheckInterpreterExist(interpreter):
            raise InterpreterAddError(_("interpreter have already exist"))
        self.interpreters.append(interpreter)
        #first interpreter should be the default interpreter by default
        if 1 == len(self.interpreters):
            self.MakeDefaultInterpreter()
            self.SetCurrentInterpreter(self.DefaultInterpreter)
        return interpreter
        
    def RemovePythonInterpreter(self,interpreter):
        #if current interpreter has been removed,choose default interpreter as current interpreter 
        if interpreter == self.CurrentInterpreter:
            self.SetCurrentInterpreter(self.GetDefaultInterpreter())
        self.interpreters.remove(interpreter)
        
    def SetDefaultInterpreter(self,interpreter):
        self.DefaultInterpreter = interpreter
        for kl in self.interpreters:
            if kl.Id == interpreter.Id:
                interpreter.Default = True
            else:
                kl.Default = False
        
    def MakeDefaultInterpreter(self):
        self.DefaultInterpreter = self.interpreters[0]
        self.DefaultInterpreter.Default = True
        
    def GetDefaultInterpreter(self):
        return self.DefaultInterpreter
    
    def GetChoices(self):
        choices = []
        default_index = -1
        for i,interpreter in enumerate(self.interpreters):
            #set current interpreter index as default index
            if interpreter == self.CurrentInterpreter:
                default_index = i
            choices.append(interpreter.Name)
        return choices,default_index
        
    def GetInterpreterById(self,id):
        for interpreter in self.interpreters:
            if interpreter.Id == id:
                return interpreter
        return None
        
    def CheckInterpreterExist(self,interpreter):
        for kb in self.interpreters:
            if kb.Name.lower() == interpreter.Name.lower():
                return True  
            elif kb.Path.lower() == interpreter.Path.lower():
                return True
        return False
        
    @classmethod
    def CheckIdExist(cls,id):
        for kb in cls.interpreters:
            if kb.Id == id:
                return True
        return False
        
    @classmethod        
    def GenerateId(cls):
        id = wx.NewId()
        while cls.CheckIdExist(id):
            id = wx.NewId()
        return id
        
    def IsInterpreterAnalysing(self):
        for kb in self.interpreters:
            if kb.Analysing:
                return True
        return False
        
    @classmethod    
    def SetCurrentInterpreter(cls,interpreter):
        cls.CurrentInterpreter = interpreter
        if interpreter is None:
            return
        #change builtin module name of BuiltinImportNode
        nodeast.BuiltinImportNode.BUILTIN_MODULE_NAME = interpreter.BuiltinModuleName
        
    @classmethod    
    def GetCurrentInterpreter(cls):
        return cls.CurrentInterpreter
        
    def LoadBuiltinInterpreter(self):
        builtin_interpreter = Interpreter.BuiltinPythonInterpreter(_("Builtin_Interpreter"),sys.executable)
        self.interpreters.append(builtin_interpreter)
        
class InterpreterAddError(Exception):
    def __init__(self, error_msg):
        self.msg = error_msg
        
    def __str__(self):
        return repr(self.msg)
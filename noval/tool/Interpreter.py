import os
import sys
import subprocess
from Singleton import *
import wx
import locale
import noval.util.sysutils as sysutils
import pickle
import noval.parser.nodeast as nodeast
import __builtin__
import json
import threading
from noval.util.logger import app_debugLogger
import glob
_ = wx.GetTranslation

class Interpreter(object):
    
    def __init__(self,name,executable_path):
        self._path = executable_path
        self._install_path = os.path.dirname(self._path)
        self._name = name
        
    @property
    def Path(self):
        return self._path
        
    @property
    def InstallPath(self):
        return self._install_path
        
    @property
    def Version(self):
        pass
        
    @property
    def Name(self):
        return self._name
 
    @Name.setter
    def Name(self,name):
        self._name = name
        
    @property
    def Id(self):
        pass   

def GetCommandOutput(command,read_error=False):
    try:
        p = subprocess.Popen(command,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if read_error:
            return p.stderr.read()
        return p.stdout.read()
    except Exception as e:
        app_debugLogger.error("get command %s output error:%s",command,e)
        return ''
    
#this class should inherit from object class
#otherwise the property definition will not valid
class PythonEnvironment(object):
    def __init__(self):
        self._include_system_environ = True
        self.environ = {}
        
    def Exist(self,key):
        return self.environ.has_key(key)
        
    def GetEnviron(self):
        environ = {}
        environ.update(self.environ)
        if self._include_system_environ:
            environ.update(os.environ)
        return environ
        
    def Remove(self,key):
        if self.Exist(key):
            self.environ.pop(key)
            
    def Add(self,key,value):
        if not self.Exist(key):
            self.environ[str(key)] = str(value)
            
    @property
    def IncludeSystemEnviron(self):
        return self._include_system_environ
        
    @IncludeSystemEnviron.setter
    def IncludeSystemEnviron(self,v):
        self._include_system_environ = v
        
    def __iter__(self):
        self.iter = iter(self.environ)
        return self
        
    def next(self):
        return __builtin__.next(self.iter)
        
    def GetCount(self):
        return len(self.environ)
        
    def __getitem__(self,name):
        return self.environ[name]
        
class PythonInterpreter(Interpreter):
    
    CONSOLE_EXECUTABLE_NAME = "python.exe"
    WINDOW_EXECUTABLE_NAME = "pythonw.exe"
    PYTHON3_BUILTIN_MODULE_NAME = 'builtins'
    def __init__(self,name,executable_path,id=None,is_valid_interpreter = False):
        if sysutils.isWindows():
            if os.path.basename(executable_path) == PythonInterpreter.WINDOW_EXECUTABLE_NAME:
                self._window_path = executable_path
                console_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.CONSOLE_EXECUTABLE_NAME)
                self._console_path = console_path
                executable_path = self._console_path
            elif os.path.basename(executable_path) == PythonInterpreter.CONSOLE_EXECUTABLE_NAME:
                self._console_path = executable_path
                window_path = os.path.join(os.path.dirname(executable_path),PythonInterpreter.WINDOW_EXECUTABLE_NAME)
                self._window_path = window_path
                
        super(PythonInterpreter,self).__init__(name,executable_path)
        if id is None:
            self._id = InterpreterManager.GenerateId()
        else:
            self._id = int(id)
        self._is_valid_interpreter = is_valid_interpreter
        self._is_default = False
        self._is_analysing = False
        self._sys_path_list = []
        self._version = "Unknown Version"
        self._builtins = []
        self.Environ = PythonEnvironment()
        self._help_path = ""
        self._is_analysed = False
        self._packages = {}
        self._is_loading_package = False
        #builtin module name which python2 is __builtin__ and python3 is builtins
        self._builtin_module_name = "__builtin__"
        if not is_valid_interpreter:
            self.GetVersion()
        if not is_valid_interpreter and self._is_valid_interpreter:
            self.GetSyspathList()
            self.GetBuiltins()
            
    def GetVersion(self):
        output = GetCommandOutput("%s -V" % self.Path,True).strip().lower()
        version_flag = "python "
        if output.find(version_flag) == -1:
            output = GetCommandOutput("%s -V" % self.Path,False).strip().lower()
            if output.find(version_flag) == -1:
                return
        self._version = output.replace(version_flag,"").strip()
        self._is_valid_interpreter = True
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME

    def IsV27(self):
        versions = self.Version.split('.')
        if int(versions[0]) == 2 and int(versions[1]) == 7:
            return True
        return False

    def IsV26(self):
        versions = self.Version.split('.')
        if int(versions[0]) == 2 and int(versions[1]) == 6:
            return True
        return False

    def IsV2(self):
        versions = self.Version.split('.')
        if int(versions[0]) == 2:
            return True
        return False

    def IsV3(self):
        versions = self.Version.split('.')
        if int(versions[0]) >= 3:
            return True
        return False
        
    def CheckSyntax(self,script_path):
        check_cmd ="%s -c \"import py_compile;py_compile.compile(r'%s')\"" % (self.Path,script_path)
        sys_encoding = locale.getdefaultlocale()[1]
        output = GetCommandOutput(check_cmd.encode(sys_encoding),True).strip()
        if 0 == len(output):
            return True,-1,''
        lower_output = output.lower()
        lines = output.splitlines()
        fileBegin = lines[0].find("File \"")
        fileEnd = lines[0].find("\", line ")
        if -1 != lower_output.find('permission denied:'):
            line = lines[-1]
            pos = line.find(']')
            msg = line[pos+1:].replace("'","").strip()
            msg += ",Perhaps you need to delete it first!"
            return False,-1,msg
        elif fileBegin != -1 and fileEnd != -1:
            lineNum = int(lines[0][fileEnd + 8:].strip())
            return False,lineNum,'\n'.join(lines[1:])

        if self.IsV26():
            '''
            parse such error text:
            Sorry: IndentationError: ('unexpected indent', ('D:\\env\\Noval\\noval\\test\\run_test_input.py', 106, 16, '                ddd\n'))
            '''
            i = lines[0].find(", ('")
            j = lines[0].find(')')
            msg = lines[0][0:i].strip()
            lineNum = int(lines[0][i+1:j].split(',')[1].strip())
        else:
            '''
            parse such error text:
            Sorry: IndentationError: unexpected indent (run_test_input.py, line 106)
            '''
            i = lines[0].find('(')
            j = lines[0].find(')')
            msg = lines[0][0:i].strip()
            lineNum = int(lines[0][i+1:j].split()[-1])
        return False,lineNum,msg
        
    @property
    def Version(self):
        return self._version

    @property
    def HelpPath(self):
        return self._help_path

    @HelpPath.setter
    def HelpPath(self,help_path):
        self._help_path = help_path
         
    @property
    def ConsolePath(self):
         return self._console_path
    @property
    def WindowPath(self):
         return self._window_path
    @property
    def IsValidInterpreter(self):
         return self._is_valid_interpreter
    @property
    def Default(self):
        return self._is_default
        
    @Default.setter
    def Default(self,is_default):
        self._is_default = is_default
        
    def GetSyspathList(self):
        if int(self._version.split(".")[0]) == 2:
            run_cmd ="%s -c \"import sys;print sys.path\"" % (self.Path)
        elif int(self._version.split(".")[0]) == 3:
            run_cmd ="%s -c \"import sys;print (sys.path)\"" % (self.Path)
        output = GetCommandOutput(run_cmd).strip()
        lst = eval(output)
        self._sys_path_list = lst
        
    def GetBuiltins(self):
        if int(self._version.split(".")[0]) == 2:
            run_cmd ="%s -c \"import sys;print sys.builtin_module_names\"" % (self.Path)
        elif int(self._version.split(".")[0]) == 3:
            run_cmd ="%s -c \"import sys;print (sys.builtin_module_names)\"" % (self.Path)
        output = GetCommandOutput(run_cmd).strip()
        lst = eval(output)
        self._builtins = lst
    @property
    def SyspathList(self):
        return self._sys_path_list        
    @property    
    def Builtins(self):
        return self._builtins
        
    def SetInterpreterInfo(self,version,builtins,sys_path_list):
        self._version = version
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME
        assert(0 == len(self._builtins))
        self._builtins = builtins
        assert(0 == len(self._sys_path_list))
        self._sys_path_list = sys_path_list
    @property
    def Analysing(self):
        return self._is_analysing
        
    @Analysing.setter
    def Analysing(self,is_analysing):
        self._is_analysing = is_analysing

    @property
    def IsAnalysed(self):
        return self._is_analysed

    @IsAnalysed.setter
    def IsAnalysed(self,is_analysed):
        self._is_analysed = is_analysed

    @property
    def Id(self):
        return self._id
    @property
    def BuiltinModuleName(self):
        return self._builtin_module_name
        
    def GetPipPath(self):
        if sysutils.isWindows():
            pip_name = "pip.exe"
        else:
            pip_name = "pip"
        python_location = os.path.dirname(self.Path)
        pip_path_list = [os.path.join(python_location,"Scripts",pip_name),os.path.join(python_location,pip_name)]
        for pip_path in pip_path_list:
            if os.path.exists(pip_path):
                return pip_path
        return None
        
    def GetDocPath(self):
        if self._help_path == "":
            if sysutils.isWindows():
                python_location = os.path.dirname(self.Path)
                doc_location = os.path.join(python_location,"Doc")
                file_list = glob.glob(os.path.join(doc_location,"*.chm"))
                if len(file_list) > 0 :
                   self._help_path =  file_list[0]
        
    def LoadPackages(self,ui_panel,force):
        if (not self._is_loading_package and 0 == len(self._packages)) or force:
            t = threading.Thread(target=self.LoadPackageList,args=(ui_panel,))
            t.start()
            
    def LoadPackageList(self,ui_panel):
        self._is_loading_package = True
        pip_path = self.GetPipPath()
        if pip_path is not None:
            command = "%s list" % pip_path
            output = GetCommandOutput(command)
            for line in output.split('\n'):
                if line.strip() == "":
                    continue
                name,raw_version = line.split()[0:2]
                version = raw_version.replace("(","").replace(")","")
                self._packages[name] = version
        self._is_loading_package = False
        ui_panel.LoadPackageEnd(self)
        
    @property
    def Packages(self):
        return self._packages
        
    @Packages.setter
    def Packages(self,packages):
        self._packages = packages
        
    @property
    def IsLoadingPackage(self):
        return self._is_loading_package
         
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
             dlg = wx.MessageDialog(None, _("No Python Interpreter Found!"), _("No Interpreter"), wx.OK | wx.ICON_WARNING)  
             dlg.ShowModal()
             dlg.Destroy()  
        elif 1 == len(self.interpreters):
            self.MakeDefaultInterpreter()
        else:
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
    def LoadPythonInterpreters(self):
        if sysutils.isWindows():
            import _winreg
            ROOT_KEY_LIST = [_winreg.HKEY_LOCAL_MACHINE,_winreg.HKEY_CURRENT_USER]
            for root_key in ROOT_KEY_LIST:
                try:
                    open_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore")  
                    countkey=_winreg.QueryInfoKey(open_key)[0]  
                    keylist = []  
                    for i in range(int(countkey)):  
                        name = _winreg.EnumKey(open_key,i)
                        try:
                            child_key = _winreg.OpenKey(root_key, r"SOFTWARE\Python\Pythoncore\%s" % name)
                            install_path = _winreg.QueryValue(child_key,"InstallPath")
                            interpreter = PythonInterpreter(name,os.path.join(install_path,PythonInterpreter.CONSOLE_EXECUTABLE_NAME))
                            self.interpreters.append(interpreter)

                            help_key = _winreg.OpenKey(child_key,"Help")
                            help_path = _winreg.QueryValue(help_key,"Main Python Documentation")
                            interpreter.HelpPath = help_path
                        except:
                            continue
                except:
                    continue
        else:
            executable_path = sys.executable
            install_path = os.path.dirname(executable_path)
            interpreter = PythonInterpreter("default",executable_path)
            self.interpreters.append(interpreter)
            
    def LoadPythonInterpretersFromConfig(self):
        config = wx.ConfigBase_Get()
        if sysutils.isWindows():
            dct = self.ConvertInterpretersToDictList()
            data = config.Read(self.KEY_PREFIX)
            if not data:
                return False
            lst = pickle.loads(data.encode('ascii'))
            for l in lst:
                interpreter = PythonInterpreter(l['name'],l['path'],l['id'],True)
                interpreter.Default = l['default']
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                interpreter.SetInterpreterInfo(l['version'],l['builtins'],l['path_list'])
                interpreter.HelpPath = l.get('help_path','')
                interpreter.Environ.environ = l.get('environ',{})
                interpreter.Packages = l.get('packages',{})
                self.interpreters.append(interpreter)
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
                builtins = config.Read("%s/%s/Builtins" % (prefix,id))
                environ = json.loads(config.Read("%s/%s/Environ" % (prefix,id),"{}"))
                packages = json.loads(config.Read("%s/%s/Packages" % (prefix,id),"{}"))
                interpreter = PythonInterpreter(name,path,id,True)
                interpreter.Default = is_default
                interpreter.Environ.environ = environ
                interpreter.Packages = packages
                if interpreter.Default:
                    self.SetDefaultInterpreter(interpreter)
                interpreter.SetInterpreterInfo(version,builtins.split(os.pathsep),sys_paths.split(os.pathsep))
                self.interpreters.append(interpreter)
        
        if len(self.interpreters) > 0:
            return True
        return False
    
    def ConvertInterpretersToDictList(self):
        lst = []
        for interpreter in self.interpreters:
            d = dict(id=interpreter.Id,name=interpreter.Name,version=interpreter.Version,path=interpreter.Path,\
                     default=interpreter.Default,path_list=interpreter.SyspathList,builtins=interpreter.Builtins,help_path=interpreter.HelpPath,\
                     environ=interpreter.Environ.environ,packages=interpreter.Packages)
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
                config.Write("%s/%d/SysPathList"%(prefix,kl.Id),os.pathsep.join(kl.SyspathList))
                config.Write("%s/%d/Builtins"%(prefix,kl.Id),os.pathsep.join(kl.Builtins))
                config.Write("%s/%d/Environ"%(prefix,kl.Id),json.dumps(kl.Environ.environ))
                config.Write("%s/%d/Packages"%(prefix,kl.Id),json.dumps(kl.Packages))
        
    def AddPythonInterpreter(self,interpreter_path,name):
        interpreter = PythonInterpreter(name,interpreter_path)
        if not interpreter.IsValidInterpreter:
            raise InterpreterAddError("%s is not a valid interpreter path" % interpreter_path)
        interpreter.Name = name
        if self.CheckInterpreterExist(interpreter):
            raise InterpreterAddError("interpreter have already exist")
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
        
class InterpreterAddError(Exception):
    
    def __init__(self, error_msg):
        self.msg = error_msg
        
    def __str__(self):
        return repr(self.msg)

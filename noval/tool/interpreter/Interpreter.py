import os
import subprocess
import wx
import locale
import noval.util.sysutils as sysutils
import __builtin__
import threading
from noval.util.logger import app_debugLogger
import glob
import manager
import sys
import cStringIO
import py_compile

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
        
    def SetEnviron(self,dct):
        self.environ = {}
        for key in dct:
            #should avoid environment contain unicode string,such as u'xxx'
            if len(key) != len(str(key)) or len(dct[key]) != len(str(dct[key])):
                raise EnvironmentError(_("Environment variable contains invalid character"))
            self.environ[str(key)] = str(dct[key])
            
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
        
class BuiltinPythonInterpreter(Interpreter):
    def __init__(self,name,executable_path,id=None,is_builtin = True):
        super(BuiltinPythonInterpreter,self).__init__(name,executable_path)
        self._is_builtin = is_builtin
        if id is None:
            self._id = manager.InterpreterManager.GenerateId()
        else:
            self._id = int(id)
        self._is_default = False
        self._sys_path_list = sys.path
        self._python_path_list = []
        self._version = ".".join([str(sys.version_info.major),str(sys.version_info.minor),str(sys.version_info.micro)])
        self._builtins = sys.builtin_module_names
        self.Environ = PythonEnvironment()
        self._packages = {}
        self._help_path = ""
        #builtin module name which python2 is __builtin__ and python3 is builtins
        self._builtin_module_name = "__builtin__"
        
    @property
    def IsBuiltIn(self):
        return self._is_builtin
        
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
    def Default(self):
        return self._is_default
        
    @Default.setter
    def Default(self,is_default):
        self._is_default = is_default
        
    @property
    def SysPathList(self):
        return self._sys_path_list
        
    @property
    def PythonPathList(self):
        return self._python_path_list 
        
    @PythonPathList.setter
    def PythonPathList(self,path_list):
        self._python_path_list = path_list
        
    @property    
    def Builtins(self):
        return self._builtins
        
    @property
    def Id(self):
        return self._id
        
    @property
    def BuiltinModuleName(self):
        return self._builtin_module_name
        
    @property
    def Packages(self):
        return self._packages
        
    @Packages.setter
    def Packages(self,packages):
        self._packages = packages
        
    def LoadPackages(self,ui_panel,force):
        ui_panel.LoadPackageEnd(self)
        
    @property
    def IsLoadingPackage(self):
        return False
        
    def SetInterpreter(self,**kwargs):
        self._version = kwargs.get('version')
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME
        self._builtins = kwargs.get('builtins')
        self._sys_path_list = kwargs.get('sys_path_list')
        self._python_path_list = kwargs.get('python_path_list')
        self._is_builtin = kwargs.get('is_builtin')
        
    def IsV2(self):
        return True
        
    def IsV3(self):
        return False
        
    @property
    def Analysing(self):
        return False
    
    @property
    def IsValidInterpreter(self):
         return True
         
    def CheckSyntax(self,script_path):
        origin_stderr = sys.stderr
        sys.stderr = cStringIO.StringIO()
        py_compile.compile(script_path)
        output = sys.stderr.getvalue().strip()
        sys.stderr = origin_stderr
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

        i = lines[0].find('(')
        j = lines[0].find(')')
        msg = lines[0][0:i].strip()
        lineNum = int(lines[0][i+1:j].split()[-1])
        return False,lineNum,msg
        
class PythonInterpreter(BuiltinPythonInterpreter):
    
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
                
        super(PythonInterpreter,self).__init__(name,executable_path,id,False)
        self._is_valid_interpreter = is_valid_interpreter
        self._version = "Unknown Version"
        self._is_analysing = False
        self._is_analysed = False
        self._is_loading_package = False
        if not is_valid_interpreter:
            self.GetVersion()
        if not is_valid_interpreter and self._is_valid_interpreter:
            self.GetSysPathList()
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
    def ConsolePath(self):
         return self._console_path
    @property
    def WindowPath(self):
         return self._window_path
    @property
    def IsValidInterpreter(self):
         return self._is_valid_interpreter
        
    def GetSysPathList(self):
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
    def IsLoadingPackage(self):
        return self._is_loading_package
        
    def SetInterpreter(self,**kwargs):
        BuiltinPythonInterpreter.SetInterpreter(self,**kwargs)
        if self.IsV3():
            self._builtin_module_name = self.PYTHON3_BUILTIN_MODULE_NAME
        
class EnvironmentError(Exception):
    
    def __init__(self, error_msg):
        self.msg = error_msg
        
    def __str__(self):
        return repr(self.msg) 

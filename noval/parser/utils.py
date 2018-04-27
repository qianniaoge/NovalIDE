import os
import sys

def MakeDirs(dirname):
    dirname = os.path.abspath(dirname)
    dirname = dirname.replace("\\","/")
    dirnames = dirname.split("/")
    destdir = ""
    destdir = os.path.join(dirnames[0] + "/",dirnames[1])
    
    if not os.path.exists(destdir):
        os.mkdir(destdir)
        
    for name in dirnames[2:]:
        destdir=os.path.join(destdir,name)
        if not os.path.exists(destdir):
            os.mkdir(destdir)

def get_relative_name(module_path,path_list = sys.path):
    path = os.path.dirname(module_path)
    recent_path = ''
    while True:
        #when route to sys path or root path,such as / or c:\\,skip the circle
        if PathsContainPath(path_list,path) or os.path.dirname(path) == path:
            recent_path = path
            break
        path = os.path.dirname(path)
    path_name = module_path.replace(recent_path + os.sep,'').split('.')[0]
    if os.name == 'nt':
        path_name = path_name.replace(os.sep,'/')
    parts = path_name.split('/')
    if parts[-1] == "__init__":
        relative_module_name = '.'.join(parts[0:-1])
        is_package = True
    else:
        relative_module_name = '.'.join(parts)
        is_package = False
    return relative_module_name,is_package

def strcmp(str1,str2):
    i = 0
    while i<len(str1) and i<len(str2):
        if str1[i] != str2[i]:
            if str1[i] == '_':
                return 1
            elif str2[i] == '_':
                return -1
            outcome = cmp(str1[i],str2[i])
            return outcome
        i += 1
    return cmp(len(str1),len(str2))

def CmpMember(x,y):
    if strcmp(x.lower() , y.lower()) == 1:
        return 1
    return -1
    
def CmpMember2(x,y):
    if x.startswith("_") and not y.startswith("_"):
        return 1
    elif y.startswith("_") and not x.startswith("_"):
        return -1
    if x.lower() > y.lower():
        return 1
    return -1
    
def CompareDatabaseVersion_(new_version,old_version):
    new_verions = new_version.split(".")
    old_versions = old_version.split(".")
    for i,v in enumerate(new_verions):
        if i >= len(old_versions):
            return 1
        if int(v) > int(old_versions[i]):
            return 1
    return 0


def IsNoneOrEmpty(value):
    if value is None:
        return True
    elif value == "":
        return True
    return False

def IsPython3():
    if sys.version_info[0] >= 3:
        return True
    return False

def IsPython2():
    if sys.version_info[0] == 2:
        return True
    return False
    
def ComparePath(path1,path2):
    if os.name == 'nt':
        path1 = path1.replace("/",os.sep).rstrip(os.sep)
        path2 = path2.replace("/",os.sep).rstrip(os.sep)
        return path1.lower() == path2.lower()
    return path1 == path2
    
def PathsContainPath(path_list,path):
    if os.name == 'nt':
        for p in path_list:
            if ComparePath(p,path):
                return True
        return False
    return path in path_list
    
def CalcVersionValue(ver_str="0.0.0"):
    """Calculates a version value from the provided dot-formated string

    1) SPECIFICATION: Version value calculation AA.BBB.CCC
         - major values: < 1     (i.e 0.0.85 = 0.850)
         - minor values: 1 - 999 (i.e 0.1.85 = 1.850)
         - micro values: >= 1000 (i.e 1.1.85 = 1001.850)

    @keyword ver_str: Version string to calculate value of

    """
    ver_str = ''.join([char for char in ver_str
                       if char.isdigit() or char == '.'])
    ver_lvl = ver_str.split(u".")
    if len(ver_lvl) < 3:
        return 0

    major = int(ver_lvl[0]) * 1000
    minor = int(ver_lvl[1])
    if len(ver_lvl[2]) <= 2:
        ver_lvl[2] += u'0'
    micro = float(ver_lvl[2]) / 1000
    return float(major) + float(minor) + micro
    
def CompareDatabaseVersion(new_version,old_version):
    if CalcVersionValue(new_version) <= CalcVersionValue(old_version):
        return 0
    return 1
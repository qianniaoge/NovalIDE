import os
import sys
import utils

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

def get_top_modulename(fullpath):
    path = os.path.dirname(fullpath)
    data_name = ""
    recent_path = ''
    sys.path = [l.lower() for l in sys.path]
    while True:
        if path.lower() in sys.path or os.path.dirname(path) == path:
            recent_path = path
            break
        path = os.path.dirname(path)
    path_name = fullpath.replace(recent_path + os.sep,'').split('.')[0]
    path_name = path_name.replace("\\",'/')
    parts = path_name.split('/')
    if parts[-1] == "__init__":
        data_file_name = '.'.join(parts[0:-1])
        is_package = True
    else:
        data_file_name = '.'.join(parts)
        is_package = False
    return data_file_name,is_package

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
    
def CompareDatabaseVersion(new_version,old_version):
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
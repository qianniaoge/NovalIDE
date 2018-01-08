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

def get_top_modulename(fullpath):
    path = os.path.dirname(fullpath)
    data_name = ""
    recent_path = ''
    while True:
        if path in sys.path:
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
    
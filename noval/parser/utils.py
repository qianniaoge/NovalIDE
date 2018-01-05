import os

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

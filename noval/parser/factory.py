###from __future__ import print_function
import sys
import os
import pickle
import config
import json
import types
import time
###from concurrent import futures
import functools
import multiprocessing
import fileparser
import utils

def generate_builtin_data(dest_path):
    
    def work_builtin_type(builtin_type,recursive=True):
        childs = []
        for name in dir(builtin_type):
            try:
                builtin_attr_intance = getattr(builtin_type,name)
            except:
                continue
            builtin_attr_type = type(builtin_attr_intance)
            if builtin_attr_type == types.TypeType:
                if not recursive:
                    continue
                builtin_attr_childs = work_builtin_type(builtin_attr_intance,False)
                node = dict(name = name,is_builtin=True,type = config.NODE_CLASSDEF_TYPE,childs=builtin_attr_childs)
                childs.append(node)
            elif builtin_attr_type == types.BuiltinFunctionType or builtin_attr_type == types.BuiltinMethodType \
                        or str(builtin_attr_type).find("method_descriptor") != -1:
                node = dict(name = name,is_builtin=True,type = config.NODE_FUNCDEF_TYPE)
                childs.append(node)
            else:
                node = dict(name = name,is_builtin=True,type = config.NODE_OBJECT_PROPERTY)
                childs.append(node)
        return childs
        
    dest_path = os.path.join(dest_path,"builtins")
    utils.MakeDirs(dest_path)
    for built_module in sys.builtin_module_names:
        module_instance = __import__(built_module)
        childs = work_builtin_type(module_instance)
        with open(dest_path + "/" + built_module + ".$memberlist", 'w') as f:
            for node in childs:
                f.write(node['name'])
                f.write('\n')
        module_dict = fileparser.make_module_dict(built_module,'',True,childs)
        with open(dest_path + "/" + built_module + ".$members", 'wb') as j:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_dict, j)
            
def generate_intelligent_data(root_path):
    if isinstance(sys.version_info,tuple):
        version = str(sys.version_info[0]) + "." +  str(sys.version_info[1]) 
        if sys.version_info[2] > 0:
            version += "."
            version += str(sys.version_info[2])
    else:
        version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro)
    dest_path = os.path.join(root_path,version)
    utils.MakeDirs(dest_path)
    sys_path_list = sys.path
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    for path in sys_path_list:
        print ('start parse path data',path)
        scan_sys_path(path,dest_path)

def quick_generate_intelligent_data(root_path):
    version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro)
    dest_path = os.path.join(root_path,version)
    utils.MakeDirs(dest_path)
    sys_path_list = sys.path
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    with futures.ThreadPoolExecutor(max_workers=len(sys_path_list)) as controller:
        future_list = []
        for path in sys_path_list:
            print ('start parse path data',path)
            scan_path_handler = functools.partial(scan_sys_path,path,dest_path)
            scan_path_future = controller.submit(scan_path_handler)
            future_list.append(scan_path_future)
  #      results = futures.wait(future_list,return_when=futures.FIRST_EXCEPTION)
   #     finished, unfinished = results
    #    for future in finished:
     #       future.result()
     
def generate_intelligent_data_by_pool(root_path):
    version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro)
    dest_path = os.path.join(root_path,version)
    utils.MakeDirs(dest_path)
    sys_path_list = sys.path
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    pool = multiprocessing.Pool(processes=len(sys_path_list))
    future_list = []
    for path in sys_path_list:
        print ('start parse path data',path)
        pool.apply_async(scan_sys_path,(path,dest_path))
    pool.close()
    pool.join()
     
def scan_sys_path(src_path,dest_path):
    ignore_path_list = []
    for root,path,files in os.walk(src_path):
        if root != src_path and is_test_dir(root):
            ignore_path_list.append(root)
          ##  print ('path',root,'is a test dir')
            continue
        elif root != src_path and not fileparser.is_package_dir(root):
            ignore_path_list.append(root)
           ### print ('path',root,'is not a package dir')
            continue
        is_path_ignore = False
        for ignore_path in ignore_path_list:
            if root.startswith(ignore_path):
                is_path_ignore = True
                break
        if is_path_ignore:
            continue
        for afile in files:
            fullpath = os.path.join(root,afile)
            ext = os.path.splitext(fullpath)[1]
            if not ext in ['.py','.pyw']:
                continue
            top_module_name,is_package = get_top_modulename(fullpath)
            if top_module_name == "":
                continue
            module_members_file = os.path.join(dest_path,top_module_name+ ".$members")
            if os.path.exists(module_members_file):
             ###   print fullpath,'has been already analyzed'
                continue
            #print get_data_name(fullpath)
           # with open("filelist.txt","a") as f:
            #    print (fullpath,file=f)
            fileparser.dump(fullpath,top_module_name,dest_path,is_package)
           
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
    

    
def is_test_dir(dir_path):
    dir_name = os.path.basename(dir_path)
    if dir_name.lower() == "test" or dir_name.lower() == "tests":
        return True
    else:
        return False
    
if __name__ == "__main__":
    start_time = time.time()
    root_path = sys.argv[1]
  ###  generate_builtin_data('./')
    generate_intelligent_data(root_path)
    ###quick_generate_intelligent_data("interlicense")
    ###generate_intelligent_data_by_pool(root_path)
    end_time = time.time()
    elapse = end_time - start_time
    print ('elapse time:',elapse,'s')
    print ('end............')
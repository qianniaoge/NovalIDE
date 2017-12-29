from __future__ import print_function
import sys
import os
import pickle
import config
import json
import types
import ast


sys.path.append("../../")
import noval.util.sysutils as sysutils

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
    sysutils.MakeDirs(dest_path)
    for built_module in sys.builtin_module_names:
        module_instance = __import__(built_module)
        childs = work_builtin_type(module_instance)
        with open(dest_path + "/" + built_module + ".$memberlist", 'w') as f:
            for node in childs:
                f.write(node['name'])
                f.write('\n')
        with open(dest_path + "/" + built_module + ".$members", 'wb') as j:
            # Pickle dictionary using protocol 0.
            pickle.dump(childs, j)

def generate_intelligent_data(root_path):
    version = str(sys.version_info.major) + "." +  str(sys.version_info.minor) + "."  + str(sys.version_info.micro)
    dest_path = os.path.join(root_path,version)
    sysutils.MakeDirs(dest_path)
    sys_path_list = sys.path
    for i,path in enumerate(sys_path_list):
        sys_path_list[i] = os.path.abspath(path)
    for path in sys_path_list:
        print ('start parse path data',path)
        scan_sys_path(path,dest_path)
        
def scan_sys_path(src_path,dest_path):
    ignore_path_list = []
    for root,path,files in os.walk(src_path):
        if root != src_path and is_test_dir(root):
            ignore_path_list.append(root)
            print ('path',root,'is a test dir')
            continue
        elif root != src_path and not is_package_dir(root):
            ignore_path_list.append(root)
            print ('path',root,'is not a package dir')
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
            print (fullpath)
            #print get_data_name(fullpath)
            dump(fullpath,get_top_modulename(fullpath),dest_path)
           
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
    data_file_name = '.'.join(parts)
    return data_file_name
    
def is_package_dir(dir_name):
    package_file = "__init__.py"
    if os.path.exists(os.path.join(dir_name,package_file)):
        return True
    return False
    
def is_test_dir(dir_path):
    dir_name = os.path.basename(dir_path)
    if dir_name.lower() == "test" or dir_name.lower() == "tests":
        return True
    else:
        return False     
        
def dump(file_name,output_name,dest_path):
    with open(file_name) as f:
        content = f.read()
        try:
            node = ast.parse(content,file_name)
            datas = walk(node)
        except:
            return
        dest_file_name = os.path.join(dest_path,output_name )
        with open(dest_file_name + ".$members", 'wb') as o1:
            # Pickle dictionary using protocol 0.
            pickle.dump(datas, o1)
        with open(dest_file_name + ".$memberlist", 'w') as o2:
            for data in datas:
                o2.write(data['name'])
                o2.write('\n')
def walk(node):
    
    childs = []
    for element in node.body:
        if isinstance(element,ast.FunctionDef):
            ##print ast.dump(element)
            def_name = element.name
            line_no = element.lineno
            col = element.col_offset
            args = []
            for arg in element.args.args:
                ###print arg.id
                if type(arg) == ast.Name:
                    arg = dict(name=arg.id)
                    args.append(arg)
            ##print element.args.defaults
            ###print 'function:' ,def_name,line_no,col
            data = dict(name=def_name,line=line_no,col=col,type=config.NODE_FUNCDEF_TYPE,args=args)
            childs.append(data)
        elif isinstance(element,ast.ClassDef):
            class_name = element.name
            line_no = element.lineno
            col = element.col_offset
           ## print 'class:', class_name,line_no,col
            cls_childs = walk(element)
            data = dict(name=class_name,line=line_no,col=col,type=config.NODE_CLASSDEF_TYPE,childs=cls_childs)
            childs.append(data)
            
        if isinstance(element,ast.Assign):
            targets = element.targets
            line_no = element.lineno
            col = element.col_offset
            for target in targets:
                if type(target) == ast.Tuple:
                    elts = target.elts
                    for elt in elts:
                        name = elt.id
                        data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                        childs.append(data)
                elif type(target) == ast.Name:
                    name = target.id
                    data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                    childs.append(data)
            
    return childs
    
if __name__ == "__main__":
    ##generate_builtin_data('./')
    generate_intelligent_data("interlicense")
    print ('end............')
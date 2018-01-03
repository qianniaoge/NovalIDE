#coding:utf-8
import ast
import os
import pickle
import config
import nodeast
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

def dump(module_path,output_name,dest_path):
    with open(module_path) as f:
        content = f.read()
        try:
            node = ast.parse(content,module_path)
            childs = walk(node)
        except Exception,e:
            print e
            return
        module_name = os.path.basename(module_path).split(".")[0]
        module_dict = make_module_dict(module_name,module_path,False,childs)
        dest_file_name = os.path.join(dest_path,output_name )
        with open(dest_file_name + ".$members", 'wb') as o1:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_dict, o1)
        with open(dest_file_name + ".$memberlist", 'w') as o2:
            for data in childs:
                o2.write(data['name'])
                o2.write('\n')

def make_module_dict(name,path,is_builtin,childs):
    if is_builtin:
        module_data = dict(name=name,is_builtin=True,childs=childs)
    else:
          module_data = dict(name=name,path=path,childs=childs)
    return module_data
                   
def parse(module_path):
    with open(module_path) as f:
        content = f.read()
        node = ast.parse(content,module_path)
        module = nodeast.Module(os.path.basename(module_path).split('.')[0],module_path)
        deep_walk(node,module)
        return module 

def deep_walk(node,parent):
    for element in node.body:
        if isinstance(element,ast.FunctionDef):
            def_name = element.name
            line_no = element.lineno
            col = element.col_offset
            args = []
            is_property_def = False
            for deco in element.decorator_list:
                line_no += 1
                if type(deco) == ast.Name and deco.id == "property":
                    nodeast.PropertyDef(def_name,line_no,col,config.PROPERTY_TYPE_UNKNOWN,parent)
                    is_property_def = True
                    break
            if is_property_def:
                continue
            for arg in element.args.args:
                if type(arg) == ast.Name:
                    arg = dict(name=arg.id)
                    args.append(arg)
            func_def = nodeast.FuncDef(def_name,line_no,col,parent)
            deep_walk(element,func_def)
        elif isinstance(element,ast.ClassDef):
            class_name = element.name
            line_no = element.lineno
            col = element.col_offset
            class_def = nodeast.ClassDef(class_name,line_no,col,parent)
            deep_walk(element,class_def)
        elif isinstance(element,ast.Assign):
            targets = element.targets
            line_no = element.lineno
            col = element.col_offset
            for target in targets:
                if type(target) == ast.Tuple:
                    pass
               #     elts = target.elts
                #    for elt in elts:
                 #       name = elt.value
                  #      print name
                    #    data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                     #   childs.append(data)
                   #     nodeast.PropertyDef(name,line_no,col,config.PROPERTY_TYPE_NONE,parent)
                elif type(target) == ast.Name:
                    name = target.id
                  #  data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                   # childs.append(data)
                    nodeast.PropertyDef(name,line_no,col,config.PROPERTY_TYPE_UNKNOWN,parent)
    
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
            
        elif isinstance(element,ast.Assign):
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

def load(file_name):
    with open(file_name,'rb') as f:
        datas = pickle.load(f)
        import json
        print json.dumps(datas,indent=4)
        
if __name__ == "__main__":
    module = parse(r"G:\work\Noval\noval\test\ast_test_file.py")
    print module
   ## dump(r"G:\work\Noval\noval\test\ast_test_file.py","tt","./")
  ##  load("tt.$members")
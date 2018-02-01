#coding:utf-8
import ast
import os
import config
import nodeast
import sys
import utils
import pickle

reload(sys)
sys.setdefaultencoding("utf-8")

CLASS_METHOD_NAME = "classmethod"
STATIC_METHOD_NAME = "staticmethod"

def GetAstType(ast_type):
    if isinstance(ast_type,ast.Num):
        return config.ASSIGN_TYPE_INT
    elif isinstance(ast_type,ast.Str):
        return config.ASSIGN_TYPE_STR
    elif isinstance(ast_type,ast.List):
        return config.ASSIGN_TYPE_LIST
    elif isinstance(ast_type,ast.Tuple):
        return config.ASSIGN_TYPE_TUPLE
    elif isinstance(ast_type,ast.Dict):
        return config.ASSIGN_TYPE_DICT
    else:
        return config.ASSIGN_TYPE_UNKNOWN

def is_package_dir(dir_name):
    package_file = "__init__.py"
    if os.path.exists(os.path.join(dir_name,package_file)):
        return True
    return False

def get_package_childs(module_path):
    module_dir = os.path.dirname(module_path)
    file_name = os.path.basename(module_path)
    assert(file_name == "__init__.py")
    childs = []
    for file_name in os.listdir(module_dir):
        file_path_name = os.path.join(module_dir,file_name)
        if os.path.isfile(file_path_name) and not file_name.endswith(".py"):
            continue
        if file_name == "__init__.py":
            continue
            
        if os.path.isdir(file_path_name) and not is_package_dir(file_path_name) :
            continue
        if os.path.isfile(file_path_name):
            module_name = '.'.join(os.path.basename(file_name).split('.')[0:-1])
            full_module_name,_ = utils.get_top_modulename(file_path_name)
        else:
            module_name = file_name
            file_path_name = os.path.join(file_path_name,"__init__.py")
            full_module_name,_ = utils.get_top_modulename(file_path_name)
        d = dict(name=module_name,full_name=full_module_name,path=file_path_name,type=config.NODE_MODULE_TYPE)
        childs.append(d)        
    return childs

def fix_ref_module_name(module_dir,ref_module_name):
    ref_module_path = os.path.join(module_dir,ref_module_name + ".py")
    ref_module_package_path = os.path.join(module_dir,ref_module_name)
    ref_module_package_file_path = os.path.join(ref_module_package_path,"__init__.py")
    if os.path.exists(ref_module_path):
        return utils.get_top_modulename(ref_module_path)[0]
    elif os.path.exists(ref_module_package_file_path):
        return utils.get_top_modulename(ref_module_package_file_path)[0]
    elif sys.modules.has_key(ref_module_name):
        return sys.modules[ref_module_name].__name__
    else:
        return ref_module_name

def fix_refs(module_dir,refs):
    for ref in refs:
        ref_module_name = fix_ref_module_name(module_dir,ref['module'])
        ref['module'] = ref_module_name

def dump(module_path,output_name,dest_path,is_package):
    with open(module_path) as f:
        content = f.read()
        try:
            node = ast.parse(content,module_path)
            childs,refs = walk(node)
        except Exception,e:
            print e
            return
        module_name = os.path.basename(module_path).split(".")[0]
        if is_package:
            module_childs = get_package_childs(module_path)
            childs.extend(module_childs)
        else:
            for module_key in sys.modules.keys():
                starts_with_module_name = output_name + "."
                if module_key.startswith(starts_with_module_name):
                    module_instance = sys.modules[module_key]
                    d = dict(name=module_key.replace(starts_with_module_name,""),full_name=module_instance.__name__,\
                            path=module_instance.__file__.rstrip("c"),type=config.NODE_MODULE_TYPE)
                    childs.append(d)
                    break
                    
        module_dict = make_module_dict(module_name,module_path,False,childs,refs)
        fix_refs(os.path.dirname(module_path),refs)
        dest_file_name = os.path.join(dest_path,output_name )
        with open(dest_file_name + ".$members", 'wb') as o1:
            # Pickle dictionary using protocol 0.
            pickle.dump(module_dict, o1)
        with open(dest_file_name + ".$memberlist", 'w') as o2:
            name_sets = set()
            for data in childs:
                name = data['name']
                if name in name_sets:
                    continue
                o2.write(name)
                o2.write('\n')
                name_sets.add(name)
            for ref in refs:
                for name in ref['names']:
                    o2.write( ref['module'] + "/" + name['name'])
                    o2.write('\n')

def make_module_dict(name,path,is_builtin,childs,refs=[]):
    if is_builtin:
        module_data = dict(name=name,is_builtin=True,childs=childs)
    else:
          module_data = dict(name=name,path=path,childs=childs,refs=refs)
    return module_data
                   
def parse(module_path):
    with open(module_path) as f:
        content = f.read()
        node = ast.parse(content,module_path)
        module = nodeast.Module(os.path.basename(module_path).split('.')[0],module_path)
        deep_walk(node,module)
        return module 

def get_attribute_name(node):
    value = node.value
    names = [node.attr]
    while type(value) == ast.Attribute:
        names.append(value.attr)
        value = value.value
    if type(value) == ast.Name:
        names.append(value.id)
    else:
        return None
    return '.'.join(names[::-1])
    
def GetAssignValueType(node):
    value = ""
    if type(node.value) == ast.Call:
        if type(node.value.func) == ast.Name:
            value = node.value.func.id
        elif type(node.value.func) == ast.Attribute:
            value = get_attribute_name(node.value.func)
        value_type = config.ASSIGN_TYPE_OBJECT
        if value is None:
            value_type = config.ASSIGN_TYPE_UNKNOWN
    else:
        value_type = GetAstType(node.value)
    return value_type,value
    
def GetBases(node):
    base_names = []
    for base in node.bases:
        if type(base) == ast.Name:
            base_names.append(base.id)
        elif type(base) == ast.Attribute:
            base_name = get_attribute_name(base)
            base_names.append(base_name)
    return base_names


def make_element_node(element,parent,retain_new):
    if isinstance(element,ast.FunctionDef):
        def_name = element.name
        line_no = element.lineno
        col = element.col_offset
        args = []
        is_property_def = False
        is_class_method = False
        for deco in element.decorator_list:
            line_no += 1
            if type(deco) == ast.Name:
                if deco.id == "property":
                    nodeast.PropertyDef(def_name,line_no,col,"",config.ASSIGN_TYPE_UNKNOWN,parent)
                    is_property_def = True
                    break
                elif deco.id == CLASS_METHOD_NAME or deco.id == STATIC_METHOD_NAME:
                    is_class_method = True
                    break
        if is_property_def:
            return
        is_method = False
        for arg in element.args.args:
            if type(arg) == ast.Name:
                if arg.id == 'self' and parent.Type == config.NODE_CLASSDEF_TYPE:
                    is_method = True
                arg_node = nodeast.ArgNode(arg.id,arg.lineno,arg.col_offset,None)
                args.append(arg_node)
        func_def = nodeast.FuncDef(def_name,line_no,col,parent,is_method=is_method,\
                            is_class_method=is_class_method,args=args)
        deep_walk(element,func_def)
    elif isinstance(element,ast.ClassDef):
        class_name = element.name
        base_names = GetBases(element)
        line_no = element.lineno
        col = element.col_offset
        class_def = nodeast.ClassDef(class_name,line_no,col,parent,bases=base_names)
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
                if parent.HasChild(name):
                    if retain_new:
                        parent.RemoveChild(name)
                    else:
                        continue
                value_type,value = GetAssignValueType(element)
                nodeast.AssignDef(name,line_no,col,value,value_type,parent)
            elif type(target) == ast.Attribute:
                if type(target.value) == ast.Name and target.value.id == "self" and parent.Type == config.NODE_FUNCDEF_TYPE and \
                        parent.IsMethod:
                    name = target.attr
                    if parent.Parent.HasChild(name):
                        if parent.Name == "__init__":
                            parent.Parent.RemoveChild(name)
                        else:
                            continue
                    value_type,value = GetAssignValueType(element)
                    nodeast.PropertyDef(name,line_no,col,value,value_type,parent)
    elif isinstance(element,ast.Import):
        for name in element.names:
            nodeast.ImportNode(name.name,element.lineno,element.col_offset,parent,name.asname)
    elif isinstance(element,ast.ImportFrom):
        module_name = element.module
        if utils.IsNoneOrEmpty(module_name):
            if element.level == 1:
                module_name = "."
            elif element.level == 2:
                module_name = ".."
        else:
            if element.level == 1:
                module_name = "." + module_name
            elif element.level == 2:
                module_name = ".." + module_name
        from_import_node = nodeast.FromImportNode(module_name,element.lineno,element.col_offset,parent)
        for name in element.names:
            nodeast.ImportNode(name.name,element.lineno,element.col_offset,from_import_node,name.asname)
    elif isinstance(element,ast.If):
        for body in element.body:
            make_element_node(body,parent,retain_new)
        for orelse in element.orelse:
            make_element_node(orelse,parent,False)
    else:
        nodeast.UnknownNode(element.lineno,element.col_offset,parent)
    
def deep_walk(node,parent,retain_new=True):
    for element in node.body:
        make_element_node(element,parent,retain_new)

def walk_method_element(node):
    childs = []
    for element in node.body:
        if isinstance(element,ast.Assign):
            targets = element.targets
            line_no = element.lineno
            col = element.col_offset
            for target in targets:
                if type(target) == ast.Attribute:
                    if type(target.value) == ast.Name and target.value.id == "self":
                        name = target.attr
                        data = dict(name=name,line=line_no,col=col,type=config.NODE_OBJECT_PROPERTY)
                        childs.append(data)
    return childs

def make_element_data(element,parent,childs,refs):
    if isinstance(element,ast.FunctionDef):
        def_name = element.name
        line_no = element.lineno
        col = element.col_offset
        args = []
        is_class_method = False
        for deco in element.decorator_list:
            line_no += 1
            if type(deco) == ast.Name:
                if deco.id == CLASS_METHOD_NAME or deco.id == STATIC_METHOD_NAME:
                    is_class_method = True
                    break
        is_method = False
        for arg in element.args.args:
            if type(arg) == ast.Name:
                if arg.id == 'self':
                    is_method = True
                arg = dict(name=arg.id)
                args.append(arg)
        data = dict(name=def_name,line=line_no,col=col,type=config.NODE_FUNCDEF_TYPE,\
                    is_method=is_method,is_class_method=is_class_method,args=args)
        childs.append(data)
        ##parse self method,parent is class definition
        if is_method and isinstance(parent,ast.ClassDef):
            childs.extend(walk_method_element(element))
    elif isinstance(element,ast.ClassDef):
        class_name = element.name
        line_no = element.lineno
        col = element.col_offset
        base_names = GetBases(element)
        cls_childs,_ = walk(element)
        data = dict(name=class_name,line=line_no,col=col,type=config.NODE_CLASSDEF_TYPE,\
                        bases=base_names,childs=cls_childs)
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
    elif isinstance(element,ast.ImportFrom):
        module_name = element.module
        if utils.IsNoneOrEmpty(module_name):
            if element.level == 1:
                module_name = "."
            elif element.level == 2:
                module_name = ".."
        else:
            if element.level == 1:
                module_name = "." + module_name
            elif element.level == 2:
                module_name = ".." + module_name
        names = []
        for name in element.names:
            d = {'name':name.name}
            if name.asname is not None:
                d.update({'asname':name.asname})
            names.append(d)
        data = dict(module=module_name,names=names)
        refs.append(data)
    elif isinstance(element,ast.If):
        for body in element.body:
            make_element_data(body,parent,childs,refs)
        for orelse in element.orelse:
            make_element_data(orelse,parent,childs,refs)
    
def walk(node):
    childs = []
    refs = []
    for element in node.body:
        make_element_data(element,node,childs,refs)
    return childs,refs
        
if __name__ == "__main__":
    
  ###  print get_package_childs(r"C:\Python27\Lib\site-packages\aliyunsdkcore\auth\__init__.py")
  ##  module = parse(r"D:\env\Noval\noval\parser\nodeast.py")
   ## module = parse(r"D:\env\Noval\noval\test\run_test_input.py")
    ##print module
    dump(r"C:\Python27\lib\subprocess.py","subprocess","./",False)
    import pickle
    with open(r"D:\env\Noval\noval\parser\subprocess.$members",'rb') as f:
        datas = pickle.load(f)
   ### print datas['name'],datas['path'],datas['is_builtin']
    import json
    print json.dumps(datas,indent=4)
    

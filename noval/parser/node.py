
import config
import os

class AbstractAst(object):
    def __init__(self,parent,type):
        self._parent = parent
        self._type = type
        self._childs = []
        self.Parent.AppendChild(self)
    
    @property
    def Type(self):
        return _type
        
    @property
    def Parent(self):
        return _parent
        
    def AppendChild(self,node):
        self._childs.append(node)
        
    @property
    def Childs(self):
        return _childs
        
class BuiltinNode(AbstractAst):
    
    def __init__(self,name,type,parent,is_built_in):
        super(Module,self).__init__(parent,type)
        self._is_built_in = is_built_in
        self._name = name
        
    @property
    def Name(self):
        return self._name
        
    @property
    def IsBuiltIn(self):
        return self._is_built_in
        
class Module(BuiltinNode):
    
    def __init__(self,name,path,is_built_in = False):
        super(Module,self).__init__(name,config.NODE_MODULE_TYPE,None,is_built_in)
        self._path = path
        
    @property
    def Path(self):
        return self._path
        
    @Path.setter
    def Path(self,path):
        self._name = os.path.basename(path).split(".")[0]
        self._path = path

class Node(BuiltinNode):
    
    def __init__(self,name,line,col,type,parent,is_built_in = False):
        super(Node,self).__init__(name,type,parent,is_built_in)
        self._name = name
        self._line = line
        self._col = line
        self._type = type

    @property
    def Name(self):
        return self._name
        
    @property
    def Line(self):
        return self._line
    
    @property
    def Col(self):
        return self._col

class FuncDef(Node):
    def __init__(self,name,line,col,parent,args = [],is_decorated = False,is_method = False,is_class_method = False,is_built_in = False):
        super(FuncDef,self).__init__(name,line,col,config.NODE_FUNCDEF_TYPE,parent,is_built_in)
        self._is_decorated = is_decorated
        self._is_method = is_method
        self._is_class_method = is_class_method
        self._args = args
        
    @property
    def IsDecorated(self):
        return self._is_decorated
    
    @property
    def IsMethod(self):
        return self._is_method
        
    @property
    def IsClassMethod(self):
        return self._is_class_method
        
    @property
    def Args(self):
        return self._args

class ClassDef(Node):
    
    def __init__(self,name,line,col,parent,is_decorated = False,is_built_in = False):
        super(ClassDef,self).__init__(name,line,col,config.NODE_CLASSDEF_TYPE,parent,is_built_in)
        self._is_decorated = is_decorated
        self._child_defs = []
        
    @property
    def IsBuiltIn(self):
        return self._is_built_in
        
class PropertyDef(Node):
    
    def __init__(self,name,line,col,attr_type,parent,is_class_property = False,is_built_in = False):
        if is_class_property:
            super(PropertyDef,self).__init__(name,line,col,config.NODE_CLASSDEF_TYPE,parent,is_built_in)
        else:
            super(PropertyDef,self).__init__(name,line,col,config.NODE_OBJECT_PROPERTY,parent,is_built_in)
        self._attr_type = attr_type
    
    @property
    def DefType(self):
        return self._attr_type
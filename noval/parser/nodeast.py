
import config
import os
from utils import CmpMember

class AbstractAst(object):
    def __init__(self,parent,type):
        self._parent = parent
        self._type = type
        self._childs = []
        if self._parent != None:
            self.Parent.AppendChild(self)
    
    @property
    def Type(self):
        return self._type
        
    @property
    def Parent(self):
        return self._parent
        
    def AppendChild(self,node):
        self._childs.append(node)
        
    @property
    def Childs(self):
        return self._childs
        
    def HasChild(self,name):
        for child in self.Childs:
            if child.Name == name:
                return True
        return False
            
    def RemoveChild(self,name):
        for child in self.Childs:
            if child.Name == name:
                self.Childs.remove(child)
                break
        
class BuiltinNode(AbstractAst):
    
    def __init__(self,name,type,parent,is_built_in=True):
        super(BuiltinNode,self).__init__(parent,type)
        self._is_built_in = is_built_in
        self._name = name
        
    @property
    def Name(self):
        return self._name
        
    @property
    def IsBuiltIn(self):
        return self._is_built_in
        
    def GetMemberList(self,sort=True):
        member_list = [child.Name for child in self.Childs if child.Type != config.NODE_UNKNOWN_TYPE]
        if sort:
            member_list.sort(CmpMember)
        return member_list
            
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
        
    def __str__(self):
        print 'module name is',self.Name,'path is',self.Path
        for child in self.Childs:
            print 'module child:', child
        return self.Name
        
class Node(BuiltinNode):
    
    def __init__(self,name,line,col,type,parent,is_built_in = False):
        super(Node,self).__init__(name,type,parent,is_built_in)
        self._line = line
        self._col = col
        
    @property
    def Line(self):
        return self._line
    
    @property
    def Col(self):
        return self._col
        
class ArgNode(Node):
    def __init__(self,name,line,col,parent):
        super(ArgNode,self).__init__(name,line,col,config.NODE_ARG_TYPE,parent)
    def __str__(self):
        print 'type is arg, name is',self.Name,'line is',self.Line,'col is',self.Col
        return self.Name

class FuncDef(Node):
    def __init__(self,name,line,col,parent,args = [],is_decorated = False,is_method = False,is_class_method = False,is_built_in = False):
        super(FuncDef,self).__init__(name,line,col,config.NODE_FUNCDEF_TYPE,parent,is_built_in)
        self._is_decorated = is_decorated
        self._is_method = is_method
        self._is_class_method = is_class_method
        self._args = args
        self._is_constructor = True if self._is_method and self.Name == "__init__" else False
        
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
        
    def __str__(self):
        print 'type is func, name is',self.Name,'args is',self.Args,'line is',self.Line,'col is',self.Col
        for child in self.Childs:
            print 'func child:', child
        return self.Name

    @property
    def IsConstructor(self):
        return self._is_constructor

class ClassDef(Node):
    
    def __init__(self,name,line,col,parent,is_decorated = False,is_built_in = False,bases = []):
        super(ClassDef,self).__init__(name,line,col,config.NODE_CLASSDEF_TYPE,parent,is_built_in)
        self._is_decorated = is_decorated
        self._child_defs = []
        self._bases = bases
        
    def __str__(self):
        print 'type is class, name is',self.Name,'line is',self.Line,'col is',self.Col
        for child in self.Childs:
            print 'class child:', child
        return self.Name
        
    @property        
    def Bases(self):
        return self._bases
        
class AssignDef(Node):
    def __init__(self,name,line,col,value,value_type,parent,node_type = config.NODE_ASSIGN_TYPE,is_built_in = False):
        super(AssignDef,self).__init__(name,line,col,node_type,parent,is_built_in)
        self._value_type = value_type
        self._value = value
    @property
    def ValueType(self):
        return self._value_type
        
    @property
    def Value(self):
        return self._value
        
    def __str__(self):
        print 'type is assign, name is',self.Name,'line is',self.Line,'col is',self.Col
        return self.Name
        
class PropertyDef(AssignDef):
    
    def __init__(self,name,line,col,value,value_type,parent,is_class_property = False,is_built_in = False):
        if is_class_property:
            super(PropertyDef,self).__init__(name,line,col,value,value_type,parent,\
                                config.NODE_CLASS_PROPERTY,is_built_in)
        else:
            super(PropertyDef,self).__init__(name,line,col,value,value_type,parent,\
                                config.NODE_OBJECT_PROPERTY,is_built_in)

    def __str__(self):
        print 'type is property, name is',self.Name,'line is',self.Line,'col is',self.Col
        return self.Name
        
class ImportNode(Node):
     def __init__(self,name,line,col,parent,as_name=None):
        super(ImportNode,self).__init__(name,line,col,config.NODE_IMPORT_TYPE,parent)
        self._as_name = as_name
     @property
     def AsName(self):
         return self._as_name
         
class FromImportNode(Node):
     def __init__(self,name,line,col,parent):
        super(FromImportNode,self).__init__(name,line,col,config.NODE_FROMIMPORT_TYPE,parent)
        
class UnknownNode(Node):
     def __init__(self,line,col,parent):
        super(UnknownNode,self).__init__("___UnknownNode",line,col,config.NODE_UNKNOWN_TYPE,parent)
        
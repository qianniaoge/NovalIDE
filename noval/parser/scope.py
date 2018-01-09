import fileparser
import config

class Scope(object):
    def __init__(self,line_start,line_end,parent=None):
        self._line_start = line_start
        self._line_end = line_end
        self._parent = parent
        self._child_scopes = []
        if self._parent != None:
            self.Parent.AppendChildScope(self)
    @property
    def Parent(self):
        return self._parent       
    @property
    def LineStart(self):
        return self._line_start
    @property
    def LineEnd(self):
        return self._line_end
    @LineEnd.setter
    def LineEnd(self,line):
        self._line_end = line
    @property
    def ChildScopes(self):
        return self._child_scopes
        
    def HasNoChild(self):
        return 0 == len(self._child_scopes)
        
    def AppendChildScope(self,scope):
        self._child_scopes.append(scope)
    
    def IslocateInScope(self,line):
        if self.LineStart <= line and self.LineEnd >= line:
            return True
        return False
        
    def RouteChildScopes(self):
        self.ChildScopes.sort(key=lambda c :c.LineStart)
        last_scope = None
        for child_scope in self.ChildScopes:
            if child_scope.Node.Type == config.NODE_FUNCDEF_TYPE:
                child_scope.RouteChildScopes()
            elif child_scope.Node.Type == config.NODE_CLASSDEF_TYPE:
                child_scope.RouteChildScopes()
            if last_scope is not None:
                last_scope.LineEnd = child_scope.LineStart -1
                last_scope.Parent.LineEnd = last_scope.LineEnd
            last_scope = child_scope
        if last_scope is not None:    
            last_scope.Parent.LineEnd = last_scope.LineEnd
            
    def FindScope(self,line):
        for child_scope in self.ChildScopes:
            if child_scope.IslocateInScope(line):
                if self.IsRoutetoEnd(child_scope):
                    return child_scope
                else:
                    return child_scope.FindScope(line)
                    
    def FindInChildScopes(self,name):
        for child_scope in self.ChildScopes:
            if child_scope.EqualName(name):
                return child_scope.Node.Line
        return -1
        
    def IsRoutetoEnd(self,scope):
        for child_scope in scope.ChildScopes:
            if not child_scope.HasNoChild():
                return False
        return True        
        
    def FindInScope(self,name):
        found_line = -1
        parent = self
        while parent is not None:
            found_line = parent.FindInChildScopes(name)
            if found_line != -1:
                break
            parent = parent.Parent
        return found_line
        
    def FindInScopeByNames(self,names):
        if names[0] == 'self':
            return self.FindInScope(names[1])
        else:
            return self.FindInScope(names[0])
            
    def FindDefinition(self,name):
        return self.FindInScopeByNames(name.split('.'))            
            
class ModuleScope(Scope):
        def __init__(self,module,line_count):
            super(ModuleScope,self).__init__(0,line_count)
            self._module = module
        @property
        def Module(self):
            return self._module
        
        def MakeModuleScopes(self):
            self.MakeScopes(self.Module,self)
            
        def MakeScopes(self,node,parent_scope):
            for child in node.Childs:
                if child.Type == config.NODE_FUNCDEF_TYPE:
                    func_def_scope = FuncDefScope(child,parent_scope)
                    self.MakeScopes(child,func_def_scope)
                elif child.Type == config.NODE_CLASSDEF_TYPE:
                    class_def_scope = ClassDefScope(child,parent_scope)
                    self.MakeScopes(child,class_def_scope)
                elif child.Type == config.NODE_OBJECT_PROPERTY:
                    NameScope(child,parent_scope)
                elif child.Type == config.NODE_IMPORT_TYPE:
                    ImportScope(child,parent_scope)
                elif child.Type == config.NODE_FROMIMPORT_TYPE:
                    from_import_scope = FromImportScope(child,parent_scope)
                    print child.Childs,'++++++++++++++++++'
                    self.MakeScopes(child,from_import_scope)
                elif child.Type == config.NODE_UNKNOWN_TYPE:
                    UnknownScope(child,parent_scope)
                    
        def __str__(self):
            print 'module name is',self.Module.Name,'path is',self.Module.Path
            for child_scope in self.ChildScopes:
                print 'module child:', child_scope
            return self.Module.Name
            
        def FindScope(self,line):
            find_scope = Scope.FindScope(self,line)
            if find_scope == None:
                return self
            return find_scope
                                  
class NodeScope(Scope):
        def __init__(self,node,parent):
            super(NodeScope,self).__init__(node.Line,node.Line,parent)
            self._node= node
        @property
        def Node(self):
            return self._node
        
        def EqualName(self,name):
            return self.Node.Name == name
            
class FuncDefScope(NodeScope):
        def __init__(self,func_def_node,parent):
            super(FuncDefScope,self).__init__(func_def_node,parent)
            
        def __str__(self):
            print 'type is func scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'func scope child:', child
            return self.Node.Name

class ClassDefScope(NodeScope):
        def __init__(self,class_def_node,parent):
            super(ClassDefScope,self).__init__(class_def_node,parent)
            
        def __str__(self):
            print 'type is class scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'class scope child:', child
            return self.Node.Name
 
class NameScope(NodeScope):
        def __init__(self,name_property_node,parent):
            super(NameScope,self).__init__(name_property_node,parent)
            
        def __str__(self):
            print 'type is name scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
class UnknownScope(NodeScope):
        def __init__(self,unknown_type_node,parent):
            super(UnknownScope,self).__init__(unknown_type_node,parent)
            
        def __str__(self):
            print 'type is unknown scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name

class ImportScope(NodeScope):
        def __init__(self,import_node,parent):
            super(ImportScope,self).__init__(import_node,parent)
            
        def __str__(self):
            print 'type is import scope, import name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
class FromImportScope(NodeScope):
        def __init__(self,from_import_node,parent):
            super(FromImportScope,self).__init__(from_import_node,parent)
            
        def __str__(self):
            print 'type is from import scope, from name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
        def EqualName(self,name):
            for child_scope in self.ChildScopes:
                if child_scope.EqualName(name):
                    return True
            return False
            
def search_node_scope(name,node):
    
    for child in node.Childs:
        if child.Name == name:
            return child
            
    return None
 
def search_global_scope(name,module):
    pass
    
if __name__ == "__main__":
    module = fileparser.parse(r"D:\env\Noval\noval\test\ast_test_file.py")
    module_scope = ModuleScope(module,100)
    module_scope.MakeModuleScopes()
    module_scope.RouteChildScopes()
    print module_scope
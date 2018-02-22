import fileparser
import config
from utils import CmpMember
import intellisence
import nodeast

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
            ##exclude child scopes which is import from other modules
            if child_scope.Root.Module.Path != self.Root.Module.Path:
                continue
            if child_scope.Node.Type == config.NODE_FUNCDEF_TYPE:
                child_scope.RouteChildScopes()
            elif child_scope.Node.Type == config.NODE_CLASSDEF_TYPE:
                child_scope.RouteChildScopes()
            if last_scope is not None:
                if child_scope.LineStart > last_scope.LineEnd:
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
                    
    def FindScopeInChildScopes(self,name):
        for child_scope in self.ChildScopes:
            if child_scope.EqualName(name):
                return child_scope
        return None
        
    def IsRoutetoEnd(self,scope):
        for child_scope in scope.ChildScopes:
            if not child_scope.HasNoChild():
                return False
        return True        
        
    def FindScopeInScope(self,name):
        found_scope = None
        parent = self
        while parent is not None:
            found_scope = parent.FindScopeInChildScopes(name)
            if found_scope != None:
                break
            parent = parent.Parent
        return found_scope

    def GetTopScope(self,names):
        find_scope = None
        i = len(names)
        find_name = ""
        while True:
            if i <= 0:
                break
            find_name = ".".join(names[0:i])
            find_scope = self.FindScopeInScope(find_name)
            if find_scope is not None:
                break
            i -= 1
        return find_scope
        
    def FindDefinition(self,name):
        names = name.split('.')
        find_scope = None
        is_self = False
        is_cls = False
        if names[0] == 'self' and len(names) > 1:
            top_scope = self.GetTopScope(names[1:])
            is_self = True
        elif names[0] == 'cls' and len(names) > 1 and self.IsClassMethodScope():
            top_scope = self.GetTopScope(names[1:])
            is_cls = True
        else:
            top_scope = self.GetTopScope(names)
        return top_scope,is_self,is_cls

    def FindDefinitionMember(self,name):
        top_scope,is_self,is_cls = self.FindDefinition(name)
        if top_scope is None:
            return None
        if is_self:
            find_scope_member = top_scope.GetMember(name[5:])
        elif is_cls:
            find_scope_member = top_scope.GetMember(name[4:])
        else:
            find_scope_member = top_scope.GetMember(name)
        return find_scope_member
        
    def FindDefinitionScope(self,name):
        names = name.split('.')
        #when like self. or cls., route to parent class scope
        if names[0] == 'self' or (names[0] == 'cls' and self.IsClassMethodScope()):
            if len(names) == 1:
                return self.Parent
            else:
                return self.FindDefinition('.'.join(names[1:]))[0]
        else:
            return self.FindDefinition(name)[0]

    def IsMethodScope(self):
        return False

    def IsClassMethodScope(self):
        return False

    def MakeBeautyDoc(self,alltext):
        """Returns the formatted calltip string for the document.
        """
        if alltext is None:
            return None
        # split the text into natural paragraphs (a blank line separated)
        paratext = alltext.split("\n\n")
       
        # add text by paragraph until text limit or all paragraphs
        textlimit = 800
        if len(paratext[0]) < textlimit:
            numpara = len(paratext)
            calltiptext = paratext[0]
            ii = 1
            while ii < numpara and \
                  (len(calltiptext) + len(paratext[ii])) < textlimit:
                calltiptext = calltiptext + "\n\n" + paratext[ii]
                ii = ii + 1

            # if not all texts are added, add "[...]"
            if ii < numpara:
                calltiptext = calltiptext + "\n[...]"
        # present the function signature only (first newline)
        else:
            calltiptext = alltext.split("\n")[0]

##        if type(calltiptext) != types.UnicodeType:
##            # Ensure it is unicode
##            try:
##                stcbuff = self.GetBuffer()
##                encoding = stcbuff.GetEncoding()
##                calltiptext = calltiptext.decode(encoding)
##            except Exception, msg:
##                dbg("%s" % msg)

        return calltiptext
            
class ModuleScope(Scope):
        def __init__(self,module,line_count):
            super(ModuleScope,self).__init__(0,line_count)
            self._module = module
        @property
        def Module(self):
            return self._module
        
        def MakeModuleScopes(self):
            self.MakeScopes(self.Module,self)

        def MakeImportScope(self,from_import_scope,parent_scope):
            from_import_name = from_import_scope.Node.Name
            member_names = []
            for child_scope in from_import_scope.ChildScopes:
                #get all import members
                if child_scope.Node.Name == "*":
                    member_names.extend(intellisence.IntellisenceManager().GetModuleMembers(from_import_name,""))
                    break
                #get one import member
                else:
                    member_names.append(child_scope.Node.Name)
            for member_name in member_names:
                member_scope = intellisence.IntellisenceManager().GetModuleMember(from_import_name,member_name)
                if member_scope is not None:
                    parent_scope.AppendChildScope(member_scope)
            
        def MakeScopes(self,node,parent_scope):
            for child in node.Childs:
                if child.Type == config.NODE_FUNCDEF_TYPE:
                    func_def_scope = FuncDefScope(child,parent_scope,self)
                    for arg in child.Args:
                        ArgScope(arg,func_def_scope,self)
                    self.MakeScopes(child,func_def_scope)
                elif child.Type == config.NODE_CLASSDEF_TYPE:
                    class_def_scope = ClassDefScope(child,parent_scope,self)
                    self.MakeScopes(child,class_def_scope)
                elif child.Type == config.NODE_OBJECT_PROPERTY or\
                            child.Type == config.NODE_ASSIGN_TYPE:
                    NameScope(child,parent_scope,self)
                elif child.Type == config.NODE_IMPORT_TYPE:
                    ImportScope(child,parent_scope,self)
                    if child.Parent.Type == config.NODE_FROMIMPORT_TYPE:
                        self.MakeImportScope(parent_scope,parent_scope.Parent)                        
                elif child.Type == config.NODE_FROMIMPORT_TYPE:
                    from_import_scope = FromImportScope(child,parent_scope,self)
                    self.MakeScopes(child,from_import_scope)
                elif child.Type == config.NODE_UNKNOWN_TYPE:
                    UnknownScope(child,parent_scope,self)
                    
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

        def GetMemberList(self,sort=True):
            return intellisence.IntellisenceManager().GetModuleMembers(self.Module.Name,"")

        @property
        def Root(self):
            return self

        def EqualName(self,name):
            return self.Module.Name == name

        def GetMembers(self):
            return self.Module.GetMemberList(False)

        def GetDoc(self):
            return self.MakeBeautyDoc(self.Module.Doc)
                                  
class NodeScope(Scope):
        def __init__(self,node,parent,root):
            super(NodeScope,self).__init__(node.Line,node.Line,parent)
            self._node= node
            self._root = root
        @property
        def Node(self):
            return self._node
        
        def EqualName(self,name):
            return self.Node.Name == name
            
        def GetMemberList(self,sort=True):
            return self.Node.GetMemberList(sort)

        @property
        def Root(self):
            return self._root

        def GetMember(self,name):
            return self

        def MakeFixName(self,name):
            #muse only replace once
            fix_name = name.replace(self.Node.Name,"",1)
            if fix_name.startswith("."):
                fix_name = fix_name[1:]
            return fix_name

        def GetDoc(self):
            return self.MakeBeautyDoc(self.Node.Doc)

class ArgScope(NodeScope):
    def __init__(self,arg_node,parent,root):
        super(ArgScope,self).__init__(arg_node,parent,root)

class FuncDefScope(NodeScope):
        def __init__(self,func_def_node,parent,root):
            super(FuncDefScope,self).__init__(func_def_node,parent,root)
            
        def __str__(self):
            print 'type is func scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'func scope child:', child
            return self.Node.Name

        def MakeFixName(self,name):
            if self.Node.IsMethod:
                name = name.replace("self.","",1)
            fix_name = name.replace(self.Node.Name,"",1)
            if fix_name.startswith("."):
                fix_name = fix_name[1:]
            return fix_name

        def GetMember(self,name):
            fix_name = self.MakeFixName(name)
            if fix_name == "":
                return self
            return None

        def IsMethodScope(self):
            return self.Node.IsMethod

        def IsClassMethodScope(self):
            return self.Node.IsClassMethod

        def GetMemberList(self,sort=True):
            return []

class ClassDefScope(NodeScope):
        INIT_METHOD_NAME = "__init__"
        def __init__(self,class_def_node,parent,root):
            super(ClassDefScope,self).__init__(class_def_node,parent,root)
            
        def __str__(self):
            print 'type is class scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            for child in self.ChildScopes:
                print 'class scope child:', child
            return self.Node.Name
            
        def FindScopeInChildScopes(self,name):
            found_child_scope = Scope.FindScopeInChildScopes(self,name)
            if None == found_child_scope:
                for base in self.Node.Bases:
                    base_scope = self.Parent.FindDefinitionScope(base)
                    if base_scope is not None:
                        if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                            base_child_scope = base_scope.GetMember(base + "."+ name)
                            if base_child_scope != None:
                                return base_child_scope
                        else:
                            base_child_scope = base_scope.FindScopeInChildScopes(name)
                            if base_child_scope != None:
                                return base_child_scope
            return found_child_scope
            
        def UniqueInitMember(self,member_list):
            while member_list.count(self.INIT_METHOD_NAME) > 1:
                member_list.remove(self.INIT_METHOD_NAME)
            
        def GetMemberList(self,sort=True):
            member_list = NodeScope.GetMemberList(self,False)
            for base in self.Node.Bases:
                base_scope = self.Parent.FindDefinitionScope(base)
                if base_scope is not None:
                    if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                        member_list.extend(base_scope.GetImportMemberList(base))
                    else:
                        member_list.extend(base_scope.GetMemberList())
            self.UniqueInitMember(member_list)
            if sort:
                member_list.sort(CmpMember)
            return member_list

        def GetClassMembers(self,sort=True):
            return self.Node.GetClassMembers(sort)

        def GetClassMemberList(self,sort=True):
            member_list = self.GetClassMembers(False)
            for base in self.Node.Bases:
                base_scope = self.Parent.FindDefinitionScope(base)
                if base_scope is not None:
                    if base_scope.Node.Type == config.NODE_IMPORT_TYPE:
                        member_list.extend(base_scope.GetImportMemberList(base))
                    else:
                        member_list.extend(base_scope.GetClassMembers(False))
            self.UniqueInitMember(member_list)
            if sort:
                member_list.sort(CmpMember)
            return member_list

        def GetMember(self,name):
            fix_name = self.MakeFixName(name)
            if fix_name == "":
                return self
            return self.FindScopeInChildScopes(fix_name)
 
class NameScope(NodeScope):
        def __init__(self,name_property_node,parent,root):
            super(NameScope,self).__init__(name_property_node,parent,root)
            
        def __str__(self):
            print 'type is name scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name

        def GetMemberList(self,sort=True):
            member_list = []
            if self.Node.ValueType == config.ASSIGN_TYPE_OBJECT:
                found_scope = self.FindDefinitionScope(self.Node.Value)
                if found_scope is not None:
                    if found_scope.Node.Type == config.NODE_IMPORT_TYPE:
                        member_list = found_scope.GetImportMemberList(self.Node.Value)
                    else:
                        member_list = found_scope.GetMemberList()
            else:
                member_list = intellisence.IntellisenceManager().\
                             GetTypeObjectMembers(self.Node.ValueType)
            if sort:
                member_list.sort(CmpMember)
            return member_list

        def GetMember(self,name):
            fix_name = self.MakeFixName(name)
            if fix_name == "":
                return self
            if self.Node.Value is None:
                return None
            found_scope = self.FindDefinitionScope(self.Node.Value)
            if found_scope is not None:
                if found_scope.Node.Type == config.NODE_IMPORT_TYPE:
                    return found_scope.GetMember(self.Node.Value + "." + fix_name)
                else:
                    return found_scope.GetMember(fix_name)
            return None
            
class UnknownScope(NodeScope):
        def __init__(self,unknown_type_node,parent,root):
            super(UnknownScope,self).__init__(unknown_type_node,parent,root)
            
        def __str__(self):
            print 'type is unknown scope, name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name

class ImportScope(NodeScope):
        def __init__(self,import_node,parent,root):
            super(ImportScope,self).__init__(import_node,parent,root)
            
        def __str__(self):
            print 'type is import scope, import name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name

        def EqualName(self,name):
            if self.Node.AsName is not None:
                return self.Node.AsName == name
            else:
                return NodeScope.EqualName(self,name)

        def MakeFixName(self,name):
            if self.Node.AsName is not None:
                fix_name = name.replace(self.Node.AsName,"",1)
            else:
                fix_name = name.replace(self.Node.Name,"")
            if fix_name.startswith("."):
                fix_name = fix_name[1:]
            return fix_name

        def GetImportMemberList(self,name):
            fix_name = self.MakeFixName(name)
            member_list = intellisence.IntellisenceManager().GetModuleMembers(self.Node.Name,fix_name)
            member_list.sort(CmpMember)
            return member_list

        def GetMember(self,name):
            fix_name = self.MakeFixName(name)
            if fix_name == "":
                return self
            return intellisence.IntellisenceManager().GetModuleMember(self.Node.Name,fix_name)

        def GetDoc(self):
            doc = intellisence.IntellisenceManager().GetModule(self.Node.Name).GetDoc()
            return self.MakeBeautyDoc(doc)
            
class FromImportScope(NodeScope):
        def __init__(self,from_import_node,parent,root):
            super(FromImportScope,self).__init__(from_import_node,parent,root)
            
        def __str__(self):
            print 'type is from import scope, from name is',self.Node.Name,'line start is',self.LineStart,'line end is',self.LineEnd
            return self.Node.Name
            
        def EqualName(self,name):
            for child_scope in self.ChildScopes:
                if child_scope.EqualName(name):
                    return True
            return False
    
if __name__ == "__main__":
    module = fileparser.parse(r"D:\env\Noval\noval\parser\nodeast.py")
    module_scope = ModuleScope(module,100)
    module_scope.MakeModuleScopes()
    module_scope.RouteChildScopes()
    func_scope = module_scope.FindDefinitionScope("FuncDef.__init__")
    print func_scope

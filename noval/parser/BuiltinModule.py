import nodeast
import fileparser
import config

class BuiltinModule(nodeast.BuiltinNode):
    
    type_d = {
        "int":config.ASSIGN_TYPE_INT,
        "str":config.ASSIGN_TYPE_STR,
        "list":config.ASSIGN_TYPE_LIST,
        "tuple":config.ASSIGN_TYPE_TUPLE,
        "dict":config.ASSIGN_TYPE_DICT,
        "float":config.ASSIGN_TYPE_FLOAT,
        "long":config.ASSIGN_TYPE_LONG,
        "bool":config.ASSIGN_TYPE_BOOL,
        "set": config.ASSIGN_TYPE_SET,
        "file": config.ASSIGN_FILE_OBJECT
    }
    
    def __init__(self,name):
        super(BuiltinModule,self).__init__(name,config.NODE_MODULE_TYPE,None,True)
        self.type_objects = {}
        
    def load(self,datas):
        for data in datas['childs']:
            builtin_node = nodeast.BuiltinNode(data['name'],data['type'],self)
            if self.type_d.has_key(data['name']):
                obj_type = self.type_d[data['name']]
                self.type_objects[obj_type] = builtin_node
            if data.has_key("childs"):
                for child in data['childs']:
                    child_node = nodeast.BuiltinNode(child['name'],child['type'],builtin_node)
                
    def GetTypeNode(self,value_type):
        type_obj = self.type_objects[value_type]
        return type_obj
        
    def IsBuiltInTypeOrMethod(self,name):
        return True if self.type_d.has_key(name) else False
            
    def GetBuiltInTypeMembers(self,name):
        if self.IsBuiltInTypeOrMethod(name):
            obj_type = self.type_d[name]
            return True,self.type_objects[obj_type].GetMemberList()
        return False,[]

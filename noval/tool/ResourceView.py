import noval.util.sysutils as sysutils
import os
from noval.tool import Singleton
import wx
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
_ = wx.GetTranslation

def GetRoots():
    roots = []
    if sysutils.isWindows():
        import ctypes
        import os
        for i in range(65,91):
            vol = chr(i) + ':'
            if os.path.isdir(vol):
                roots.append(vol)
    else:
        roots.append("/")
    return roots
    
class ResourceView(object):
    
    DIRECTORY_RES_TYPE = 0
    FILE_RES_TYPE = 1
    __metaclass__ = Singleton.SingletonNew
    def __init__(self,view):
        self._view = view

    def LoadResource(self):
        roots = GetRoots()
        self._view._projectChoice.Clear()
        self._view._projectChoice.InsertItems(roots,0)
        select_index = 0
        self._view._projectChoice.SetSelection(select_index)
        name = self._view._projectChoice.GetString(select_index)
        self.LoadRoot(name)

    def SetRootDir(self,directory):
        if not os.path.isdir(directory):
            raise Exception("%s is not a valid directory" % directory)
        
        self._view._treeCtrl.DeleteAllItems()
        
        # add directory as root
        root = self._view._treeCtrl.AddRoot(directory.replace(":",""))
        if sysutils.isWindows():
            directory += os.sep
   ##     self._view._treeCtrl.SetPyData(root, Directory(directory))
       ### project_view._treeCtrl.SetItemImage(root, self.iconentries['directory'])
     ##   self._view._treeCtrl.Expand(root)
        self.LoadDir(root, directory)
            
    def LoadRoot(self,root):
        self.SetRootDir(root)
    
    def LoadDir(self, item, directory):

        # check if directory exists and is a directory
        if not os.path.isdir(directory):
            raise Exception("%s is not a valid directory" % directory)

        # check if node already has children
        if self._view._treeCtrl.GetChildrenCount(item) == 0:
            # get files in directory
            files = os.listdir(directory)
            # add nodes to tree
            file_count = 0
            for f in files:
                file_count += 1
                # process the file extension to build image list
           ##     imagekey = self.processFileExtension(os.path.join(directory, f))
                # if directory, tell tree it has children
                if os.path.isdir(os.path.join(directory, f)):
                    child = self._view._treeCtrl.AppendItem(item, f,-1)
                    self._view._treeCtrl.SetItemImage(child, \
                                     self._view._treeCtrl._folderClosedIconIndex, wx.TreeItemIcon_Normal)
                    self._view._treeCtrl.SetItemImage(child, \
                                     self._view._treeCtrl._folderOpenIconIndex, wx.TreeItemIcon_Expanded)
                    self._view._treeCtrl.SetItemHasChildren(child, True)
                    # save item path for expanding later
                    self._view._treeCtrl.SetPyData(child, (self.DIRECTORY_RES_TYPE,os.path.join(directory, f)))
                else:
                    #this is a file type 
                    child = self._view._treeCtrl.AppendItem(item, f,-1)
                    self._view._treeCtrl.SetPyData(child, (self.FILE_RES_TYPE,os.path.join(directory, f)))
                    
            if file_count == 0:
                self._view._treeCtrl.SetItemHasChildren(item, False)
                    
    def OpenSelection(self):
        item = self._view._treeCtrl.GetSelection()
        if item == None:
            return
        item_type,item_path = self._view._treeCtrl.GetPyData(item)
        if item_type == self.DIRECTORY_RES_TYPE:
            try:
                self.LoadDir(item,item_path)
                self._view._treeCtrl.Expand(item)
            except Exception,e:
                wx.MessageBox(unicode(e),_("Open Directory Error"))
        else:
            ext = strutils.GetFileExt(item_path)
            if sysutils.IsExtSupportable(ext):
                wx.GetApp().GotoView(item_path,0)
            else:
                try:
                    fileutils.start_file(item_path)
                except:
                    pass
            
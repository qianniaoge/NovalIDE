import noval.util.sysutils as sysutils
import os
from noval.tool import Singleton
import wx
import noval.util.strutils as strutils
import noval.util.fileutils as fileutils
_ = wx.GetTranslation

if sysutils.isWindows():
    from win32com.shell import shell, shellcon
    
    def GetDriveDisplayName(path):
        return shell.SHGetFileInfo(path, 0, shellcon.SHGFI_DISPLAYNAME)[1][3]
        
    def GetRoots():
        roots = []
        import ctypes
        import os
        for i in range(65,91):
            vol = chr(i) + ':'
            if os.path.isdir(vol):
                roots.append([GetDriveDisplayName(vol),wx.ArtProvider.GetBitmap(wx.ART_HARDDISK,wx.ART_CMN_DIALOG,(16,16)),vol])
        return roots
else:
    def GetRoots():
        roots = []
        home_dir = wx.GetHomeDir()
        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN,wx.ART_CMN_DIALOG,(16,16))
        roots.append([_("Home directory"),folder_bmp,home_dir])
        desktop_dir = home_dir + "/Desktop"
        roots.append([_("Desktop"),folder_bmp,desktop_dir])
        roots.append(["/",wx.ArtProvider.GetBitmap(wx.ART_HARDDISK,wx.ART_CMN_DIALOG,(16,16)),"/"])
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
        for root in roots:
            self._view._projectChoice.Append(root[0],root[1],root[2])
        #self._view._projectChoice.InsertItems(roots,0)
        select_index = 0
        self._view._projectChoice.SetSelection(select_index)
        name = self._view._projectChoice.GetClientData(select_index)
        self.LoadRoot(name)

    def SetRootDir(self,directory):
        if not os.path.isdir(directory):
            raise Exception("%s is not a valid directory" % directory)
        
        self._view._treeCtrl.DeleteChildren(self._view._treeCtrl.GetRootItem())
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
                    
    def OpenSelection(self,item):
        item_type,item_path = self._view._treeCtrl.GetPyData(item)
        if item_type == self.DIRECTORY_RES_TYPE:
            try:
                self.LoadDir(item,item_path)
                ##self._view._treeCtrl.Expand(item)
            except Exception,e:
                wx.MessageBox(unicode(e),_("Open Directory Error"))
            self._view._treeCtrl.SelectItem(item)
        else:
            ext = strutils.GetFileExt(item_path)
            if sysutils.IsExtSupportable(ext):
                wx.GetApp().GotoView(item_path,0)
            else:
                try:
                    fileutils.start_file(item_path)
                except:
                    pass
            
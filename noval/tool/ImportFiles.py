import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import wx.lib.agw.customtreectrl as CT
import os
import noval.util.sysutils as sysutilslib
import ProjectEditor
import noval.util.fileutils as fileutils
import threading
from wx.lib.pubsub import pub as Publisher

NOVAL_MSG_UI_IMPORT_FILES_PROGRESS = "noval.msg.fileimport.progress"

class ImportFilesDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,folderPath):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        self._is_importing = False
        self._stop_importing = False
        projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
        self.project_view = projectService.GetView()
        project_path = os.path.dirname(self.project_view.GetDocument().GetFilename())
        self.dest_path = os.path.basename(project_path)
        if folderPath != "":
            self.dest_path = os.path.join(self.dest_path,folderPath)
        if sysutilslib.isWindows():
            self.dest_path = self.dest_path.replace("/",os.sep)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        flagSizer = wx.BoxSizer(wx.HORIZONTAL)
        st_text = wx.StaticText(self,label = _("Local File System"))
        st_text.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        flagSizer.Add(st_text, 1,flag=wx.LEFT|wx.EXPAND,border = SPACE)  
          
        icon = wx.StaticBitmap(self,bitmap = wx.Bitmap(os.path.join(sysutilslib.mainModuleDir, \
                            "noval", "tool", "bmp_source", "python_logo.png")))  
        flagSizer.Add(icon,0,flag=wx.TOP|wx.RIGHT,border = HALF_SPACE)
        boxsizer.Add(flagSizer,0,flag=wx.EXPAND|wx.ALL,border = HALF_SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        line = wx.StaticLine(self)
        lineSizer.Add(line,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.BOTTOM,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        dirLabelText = wx.StaticText(self, -1, _('Source Location:'))
        lineSizer.Add(dirLabelText,0,flag=wx.LEFT,border=SPACE)
        self.dirControl = wx.TextCtrl(self, -1)
        self.Bind(wx.EVT_TEXT,self.ChangeDir)
        lineSizer.Add(self.dirControl,1,flag=wx.LEFT|wx.EXPAND,border=SPACE) 
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.BrowsePath)
        lineSizer.Add(self.browser_btn, 0,flag=wx.LEFT, border=SPACE) 
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        templates = wx.GetApp().GetDocumentManager().GetTemplates()
        iconList = wx.ImageList(16, 16, initialCount = len(templates))
                
        folder_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "packagefolder_obj.gif")
        folder_bmp = wx.Bitmap(folder_bmp_path, wx.BITMAP_TYPE_GIF)
        self.FolderIdx = iconList.Add(folder_bmp)
        
        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._treeCtrl = CT.CustomTreeCtrl(self, size=(300,250),style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE|CT.TR_AUTO_CHECK_CHILD|CT.TR_AUTO_CHECK_PARENT)
        self._treeCtrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.checked_item)
        wx.EVT_LEFT_DOWN(self._treeCtrl, self.OnLeftClick)
        listSizer.Add(self._treeCtrl,flag=wx.LEFT|wx.RIGHT,border=SPACE)
        self._treeCtrl.AssignImageList(iconList)
        
        self.listbox = wx.CheckListBox(self,-1,size=(300,250),choices=[])
        self.Bind(wx.EVT_CHECKLISTBOX,self.CheckBoxFile)
        listSizer.Add(self.listbox,1,flag=wx.TOP|wx.EXPAND,border=0)
        boxsizer.Add(listSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_filter_btn = wx.Button(self, -1, _("File Filters"))
        wx.EVT_BUTTON(self.file_filter_btn, -1, self.ShowFilterFileDialog)
        lineSizer.Add(self.file_filter_btn, 0,flag=wx.LEFT, border=SPACE)
        
        self.select_all_btn = wx.Button(self, -1, _("Select All"))
        wx.EVT_BUTTON(self.select_all_btn, -1, self.SelectAll)
        lineSizer.Add(self.select_all_btn, 0,flag=wx.LEFT, border=SPACE)
        
        self.unselect_all_btn = wx.Button(self, -1, _("UnSelect All"))
        wx.EVT_BUTTON(self.unselect_all_btn, -1, self.UnSelectAll)
        lineSizer.Add(self.unselect_all_btn, 0,flag=wx.LEFT, border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        destdirLabelText = wx.StaticText(self, -1, _('Dest Directory:'))
        lineSizer.Add(destdirLabelText,0,flag=wx.LEFT,border=0)
        self.destDirCtrl = wx.TextCtrl(self, -1,self.dest_path,size=(200,-1))
        self.destDirCtrl.Enable(False)
        lineSizer.Add(self.destDirCtrl,0,flag=wx.LEFT,border=SPACE)
        boxsizer.Add(lineSizer,0,flag = wx.ALL,border = SPACE)
        
        sbox = wx.StaticBox(self, -1, _("Option"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        sboxSizer.Add(wx.CheckBox(self, label="Overwrite existing files without warning"),  flag=wx.LEFT|wx.TOP, border=HALF_SPACE)  
        sboxSizer.Add(wx.CheckBox(self, label="Create top-level folder"),flag=wx.LEFT|wx.TOP, border=HALF_SPACE)
        boxsizer.Add(sboxSizer, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT , border=SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.m_gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        lineSizer.Add(self.m_gauge,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        boxsizer.Add(lineSizer,0,flag = wx.BOTTOM|wx.EXPAND,border = SPACE)
        Publisher.subscribe(self.UpdateImportProgress,NOVAL_MSG_UI_IMPORT_FILES_PROGRESS)
        
        bsizer = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&Import"))
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        self.ok_btn.SetDefault()
        bsizer.AddButton(self.ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        wx.EVT_BUTTON(cancel_btn, -1, self.OnCancelClick)
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(boxsizer)
        self.m_gauge.Hide()
        self.Fit()
        
    def ShowFilterFileDialog(self,event):
        pass
        
    def SelectAll(self,event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None:
            return
        self._treeCtrl.CheckItem(root_item, True)
        self.ListDirFiles(self._treeCtrl.GetSelection(),True,True)
        
    def UnSelectAll(self,event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None:
            return
        self._treeCtrl.CheckItem(root_item, False)
        self.ListDirFiles(self._treeCtrl.GetSelection(),False,True)
        
    def ChangeDir(self,event):
        path = self.dirControl.GetValue().strip()
        if path == "":
            self._treeCtrl.DeleteAllItems()
            return
        if sysutilslib.isWindows():
            path = path.replace("/",os.sep)
        self.ListDirItemFiles(path.rstrip(os.sep))
        
    def checked_item(self, event):
        item = event.GetItem()
        is_item_checked = self._treeCtrl.IsItemChecked(item)
        self.ListDirFiles(item,is_item_checked)
        if is_item_checked:
            self.check_parent_item(item)

    def check_parent_item(self,item):
        parent_item = self._treeCtrl.GetItemParent(item)
        while parent_item:
            #will not cause checked_item event
            if not self._treeCtrl.IsItemChecked(parent_item):
                self._treeCtrl.CheckItem2(parent_item, True,True)
            parent_item = self._treeCtrl.GetItemParent(parent_item)
        
    def OnOKClick(self, event):
        root_item = self._treeCtrl.GetRootItem()
        if root_item is None or not self._treeCtrl.IsItemChecked(root_item):
            wx.MessageBox(_("You don't select any file"))
            return
        file_list = []
        self.RotateItems(root_item,file_list)
        self.m_gauge.Show()
        self.GetSizer().Layout()
        self.Fit()
        self.ok_btn.Enable(False)
        self.dirControl.Enable(False)
        self.browser_btn.Enable(False)
        self.select_all_btn.Enable(False)
        self.unselect_all_btn.Enable(False)
        self.file_filter_btn.Enable(False)
        self.m_gauge.SetRange(len(file_list))
        self._is_importing = True
        self.StartCopyFilesToProject(file_list)
        self.MonitorCopyProgress(file_list,len(file_list))
        
    def OnCancelClick(self, event):
        if self._is_importing:
            self._stop_importing = True
            self.monotor_thread.join()
            self.copy_thread.join()
        self.EndModal(wx.ID_CANCEL)
        
    def StartCopyFilesToProject(self,file_list):
        self.copy_thread = threading.Thread(target = self.CopyFilesToProject,args=(file_list,))
        self.copy_thread.start()
        
    def MonitorCopyProgress(self,file_list,file_count):
        self.monotor_thread = threading.Thread(target = self.ShowCopyProgress,args=(file_list,file_count))
        self.monotor_thread.start()
        
    def ShowCopyProgress(self,file_list,max_file_count):
        while len(file_list) != 0:
            if self._stop_importing:
                break
            wx.MilliSleep(50)
            wx.CallAfter(Publisher.sendMessage, NOVAL_MSG_UI_IMPORT_FILES_PROGRESS, value=max_file_count - len(file_list))
        self._is_importing = False
        if not self._stop_importing:
            self.EndModal(wx.ID_OK)
            
    def UpdateImportProgress(self,value):
        self.m_gauge.SetValue(value)
        
    def CopyFilesToProject(self,file_list):
        while len(file_list) != 0:
            if self._stop_importing:
                break
            for file_path in file_list:
                if self._stop_importing:
                    break
                import time
                time.sleep(1)
                ##if self.project.CopyFileToProject(self,file_path):
                if True:
                    file_list.remove(file_path)
            
    def CheckBoxFile(self,event):
        sel_item = self._treeCtrl.GetSelection()
        if self.listbox.IsChecked(event.GetInt()):
            if not self._treeCtrl.IsItemChecked(sel_item):
                self._treeCtrl.CheckItem2(sel_item, True,True)
        else:
            checked_item_count = 0
            for i in range(self.listbox.GetCount()):
                if self.listbox.IsChecked(i):
                    checked_item_count += 1
            if 0 == checked_item_count:
                self._treeCtrl.CheckItem(sel_item, False)
            
    def IsItemSelected(self,item):
        return self._treeCtrl.GetSelection() == item
        
    def GetCheckedItemFiles(self,item,file_list):
        dir_path = self._treeCtrl.GetPyData(item)
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
                f = os.path.join(dir_path,self.listbox.GetString(i))
                file_list.append(f)
            
    def RotateItems(self,parent_item,file_list):
        if parent_item is None or not self._treeCtrl.IsItemChecked(parent_item):
            return
        dir_path = self._treeCtrl.GetPyData(parent_item)
        if not self.IsItemSelected(parent_item):
            fileutils.GetDirFiles(dir_path,file_list)
        #get checked tree item file list
        else:
            self.GetCheckedItemFiles(parent_item,file_list)
        (item, cookie) = self._treeCtrl.GetFirstChild(parent_item)
        while item:
            if self._treeCtrl.IsItemChecked(item):
                dir_path = self._treeCtrl.GetPyData(item)
                if not self.IsItemSelected(item):
                    fileutils.GetDirFiles(dir_path,file_list)
                #get checked tree item file list    
                else:
                    self.GetCheckedItemFiles(item,file_list)
            self.RotateItems(item,file_list)
            (item, cookie) = self._treeCtrl.GetNextChild(parent_item, cookie)
        
        
    def BrowsePath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                _("Choose the location"), 
                style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        #will cause wx.EVT_TEXT event
        self.dirControl.SetValue(path)
        
    def ListDirItemFiles(self,path):
        self._treeCtrl.DeleteAllItems()
        root_item = self._treeCtrl.AddRoot(os.path.basename(path),ct_type=1)
        self._treeCtrl.SetPyData(root_item,path)
        self._treeCtrl.SetItemImage(root_item,self.FolderIdx,wx.TreeItemIcon_Normal)
        self.ListDirItem(root_item,path)
        self.ListDirFiles(root_item,True,True)
        self._treeCtrl.CheckItem(root_item, True)
        
    def ListDirItem(self,parent_item,path):
        if not os.path.exists(path):
            return
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path):
                item = self._treeCtrl.AppendItem(parent_item, f,ct_type=1)
                self._treeCtrl.SetItemImage(item,self.FolderIdx,wx.TreeItemIcon_Normal)
                self._treeCtrl.SetPyData(item,file_path)
                self.ListDirItem(item,file_path)
        self._treeCtrl.Expand(parent_item)
                
    def OnLeftClick(self, event):
        item, flags = self._treeCtrl.HitTest(event.GetPosition())
        if item is not None and item.IsOk():
            file_path = self._treeCtrl.GetPyData(item)
            checked = self._treeCtrl.IsItemChecked(item)
            self.ListDirFiles(item,checked)
            if not self.IsItemSelected(item):
                self._treeCtrl.SelectItem(item)
        event.Skip()
        
    def ListDirFiles(self,item,checked=True,force=False):
        path = self._treeCtrl.GetPyData(item)
        if not os.path.exists(path):
            self.listbox.Clear()
            return
        if self._treeCtrl.GetSelection() == item and not force:
            for i in range(self.listbox.GetCount()):
                self.listbox.Check(i,checked)
            return
        self.listbox.Clear()
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            if os.path.isfile(file_path):
                i = self.listbox.Append(f)
                self.listbox.Check(i,checked)
                    
                
        
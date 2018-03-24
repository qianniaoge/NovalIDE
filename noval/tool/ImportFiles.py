import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import wx.lib.agw.customtreectrl as CT
import os
import noval.util.sysutils as sysutilslib

class ImportFilesDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)
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
        button = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(button, -1, self.BrowsePath)
        lineSizer.Add(button, 0,flag=wx.LEFT, border=SPACE) 
        boxsizer.Add(lineSizer,0,flag = wx.EXPAND|wx.RIGHT,border = SPACE) 
        
        templates = wx.GetApp().GetDocumentManager().GetTemplates()
        iconList = wx.ImageList(16, 16, initialCount = len(templates))
        self._iconIndexLookup = []
        for template in templates:
            icon = template.GetIcon()
            if icon:
                if icon.GetHeight() != 16 or icon.GetWidth() != 16:
                    icon.SetHeight(16)
                    icon.SetWidth(16)
                    if wx.GetApp().GetDebug():
                        print "Warning: icon for '%s' isn't 16x16, not crossplatform" % template._docTypeName
                iconIndex = iconList.AddIcon(icon)
                self._iconIndexLookup.append((template, iconIndex))
                
        folder_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "packagefolder_obj.gif")
        folder_bmp = wx.Bitmap(folder_bmp_path, wx.BITMAP_TYPE_GIF)
        self.FolderIdx = iconList.Add(folder_bmp)
        
        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._treeCtrl = CT.CustomTreeCtrl(self, size=(300,250),style = wx.BORDER_THEME,agwStyle = wx.TR_DEFAULT_STYLE)
        self._treeCtrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX))
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.checked_item)
        wx.EVT_LEFT_DOWN(self._treeCtrl, self.OnLeftClick)
        self.selitem = None
        listSizer.Add(self._treeCtrl,flag=wx.LEFT|wx.RIGHT,border=SPACE)
        self._treeCtrl.AssignImageList(iconList)
        
        self.listbox = wx.CheckListBox(self,-1,size=(300,250),choices=[])
        listSizer.Add(self.listbox,1,flag=wx.TOP|wx.EXPAND,border=0)
        boxsizer.Add(listSizer,0,flag = wx.EXPAND|wx.BOTTOM|wx.TOP|wx.RIGHT,border = SPACE) 
        
        sbox = wx.StaticBox(self, -1, _("Option"))
        sboxSizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        
        sboxSizer.Add(wx.CheckBox(self, label="Overwrite existing files without warning"),  flag=wx.LEFT|wx.TOP, border=HALF_SPACE)  
        sboxSizer.Add(wx.CheckBox(self, label="Create top-level folder"),flag=wx.LEFT, border=HALF_SPACE)  
        boxsizer.Add(sboxSizer, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT , border=SPACE) 
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.m_gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        lineSizer.Add(self.m_gauge,1,flag = wx.LEFT|wx.EXPAND,border = 0)
        boxsizer.Add(lineSizer,0,flag = wx.BOTTOM|wx.EXPAND,border = SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&Import"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOKClick)
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        boxsizer.Add(bsizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM,HALF_SPACE)
        
        self.SetSizer(boxsizer)
        self.Fit()
        
    def ChangeDir(self,event):
        path = self.dirControl.GetValue()
        self.ListDirItemFiles(path)
        
    def checked_item(self, event):
        item = event.GetItem()
        file_path = self._treeCtrl.GetPyData(item)
        if self._treeCtrl.IsItemChecked(item):
            self.check_child_item(event.GetItem(),True)
            self.check_parent_item(event.GetItem())
            self.ListDirFiles(item,file_path,True)
        else:
            self.check_child_item(item,False)
            self.ListDirFiles(item,file_path,False)
        self.selitem = item

    def check_child_item(self,item,checked=True):
        childs = self.get_childs(item)
        for child in self.get_childs(item):
            self._treeCtrl.CheckItem(child, checked)
            if self._treeCtrl.HasChildren(child):
                self.check_child_item(child,checked)

    def check_parent_item(self,item):
        parent_item = self._treeCtrl.GetItemParent(item)
        while parent_item:
            self._treeCtrl.CheckItem2(parent_item, True,True)
            parent_item = self._treeCtrl.GetItemParent(parent_item)

    def get_childs(self, item_obj):
        item_list = []
        (item, cookie) = self._treeCtrl.GetFirstChild(item_obj)
        while item:
            item_list.append(item)
            (item, cookie) = self._treeCtrl.GetNextChild(item_obj, cookie)
        return item_list
        
    def OnOKClick(self, event):
        self.EndModal(wx.ID_OK)
        
    def GetIconIndexFromName(self,filename):
        template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
        if template:
            for t, iconIndex in self._iconIndexLookup:
                if t is template:
                    return iconIndex
        return -1
        
    def BrowsePath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                _("Choose the location"), 
                style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        self.dirControl.SetValue(path)
        self.ListDirItemFiles(path)
        
    def ListDirItemFiles(self,path):
        self._treeCtrl.DeleteAllItems()
        root_item = self._treeCtrl.AddRoot(os.path.basename(path),ct_type=1)
        self._treeCtrl.SetPyData(root_item,path)
        self._treeCtrl.SetItemImage(root_item,self.FolderIdx,wx.TreeItemIcon_Normal)
        self.ListDirItem(root_item,path)
        self.ListDirFiles(root_item,path)
        self.selitem = root_item
        
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
        self._treeCtrl.Expand(parent_item)
        self._treeCtrl.CheckItem(parent_item, True)
                
    def OnLeftClick(self, event):
        item, flags = self._treeCtrl.HitTest(event.GetPosition())
        if item is not None and item.IsOk():
            file_path = self._treeCtrl.GetPyData(item)
            checked = self._treeCtrl.IsItemChecked(item)
            self.ListDirFiles(item,file_path,checked)
            self._treeCtrl.SelectItem(item)
        event.Skip()
        self.selitem = item
        
    def ListDirFiles(self,item,path,checked=True):
        if not os.path.exists(path):
            self.listbox.Clear()
            return
        if self.selitem == item:
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
                    
                
        
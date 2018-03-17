import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import wx.dataview as dataview
import wx.lib.agw.hyperlink as hl
import os

class SystemEnvironmentVariableDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(300,400)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self,size=(280,380))
        self.dvlc.AppendTextColumn(_('Key'), width=80)
        self.dvlc.AppendTextColumn(_('Value'),width=200)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.SetVariables()
        
    def SetVariables(self):
        for env in os.environ:
            self.dvlc.AppendItem([env, os.environ[env]])
            
class EditAddEnvironmentVariableDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(300,150)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Key: ")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.key_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        lineSizer.Add(self.key_ctrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, SPACE)
        contentSizer.Add(lineSizer, 0, wx.TOP, HALF_SPACE)
    
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Value:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.value_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        lineSizer.Add(self.value_ctrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.TOP, SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 1, wx.EXPAND,SPACE)
        
        self.SetSizer(contentSizer)

class EnvironmentPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self, label=_("Set User Defined Environment Variable:")),0, wx.TOP|wx.EXPAND, SPACE)
        self.dvlc = dataview.DataViewListCtrl(self,size=(500,230))
        self.dvlc.AppendTextColumn(_('Key'), width=100)
        self.dvlc.AppendTextColumn(_('Value'),width=400)
        dataview.EVT_DATAVIEW_SELECTION_CHANGED(self.dvlc, -1, self.UpdateUI)
        left_sizer.Add(self.dvlc, 0,  wx.TOP|wx.EXPAND, HALF_SPACE)
        
        top_sizer.Add(left_sizer, 0, wx.LEFT, 0)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.new_btn = wx.Button(self, -1, _("New.."))
        wx.EVT_BUTTON(self.new_btn, -1, self.NewVariable)
        right_sizer.Add(self.new_btn, 0, wx.TOP|wx.EXPAND, SPACE*3)
        
        self.edit_btn = wx.Button(self, -1, _("Edit"))
        wx.EVT_BUTTON(self.edit_btn, -1, self.EditVariable)
        right_sizer.Add(self.edit_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        self.remove_btn = wx.Button(self, -1, _("Remove..."))
        wx.EVT_BUTTON(self.remove_btn, -1, self.RemoveVariable)
        right_sizer.Add(self.remove_btn, 0, wx.TOP|wx.EXPAND, SPACE)
        
        top_sizer.Add(right_sizer, 0, wx.LEFT, SPACE*2)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._includeCheckBox = wx.CheckBox(self, -1, _("Include System Environment Variable"))
        self.Bind(wx.EVT_CHECKBOX,self.checkInclude,self._includeCheckBox)
        bottom_sizer.Add(self._includeCheckBox, 0, wx.LEFT|wx.ALIGN_BOTTOM)
            
        self.hyperLinkCtrl = hl.HyperLinkCtrl(self, wx.ID_ANY, _("View"))
        self.hyperLinkCtrl.SetColours("BLUE", "BLUE", "BLUE")
        self.hyperLinkCtrl.AutoBrowse(False)
        self.hyperLinkCtrl.SetBold(True)
        self.Bind(hl.EVT_HYPERLINK_LEFT, self.OnGotoLink,self.hyperLinkCtrl)
        bottom_sizer.Add(self.hyperLinkCtrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, SPACE)
        
        box_sizer.Add(top_sizer, 0, wx.BOTTOM, HALF_SPACE)
        box_sizer.Add(bottom_sizer, 0, wx.BOTTOM,0)

        self.SetSizer(box_sizer)
        self.interpreter = None
        
        self.UpdateUI(None)
        
    def checkInclude(self,event):
        if self.interpreter is None:
            return
        include_system_environ = self._includeCheckBox.GetValue()
        self.interpreter.Environ.IncludeSystemEnviron = include_system_environ
        
    def UpdateUI(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.remove_btn.Enable(False)
            self.edit_btn.Enable(False)
        else:
            self.remove_btn.Enable(True)
            self.edit_btn.Enable(True)
        if self.interpreter is None:
            self.new_btn.Enable(False)
        else:
            self.new_btn.Enable(True)
            
    def SetVariables(self,interpreter):
        self.interpreter = interpreter
        self.dvlc.DeleteAllItems()
        for env in self.interpreter.Environ:
            self.dvlc.AppendItem([env,self.interpreter.Environ[env]])
        self._includeCheckBox.SetValue(self.interpreter.Environ.IncludeSystemEnviron)
        self.UpdateUI(None)
            
    def RemoveVariable(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        self.RemoveRowVariable(index)
        self.UpdateUI(None)
        
    def RemoveRowVariable(self,row):
        key = self.dvlc.GetTextValue(row,0)
        ##self.interpreter.environments = filter(lambda e:not e.has_key(key),self.interpreter.environments)
        self.dvlc.DeleteItem(row)
        
    def GetVariableRow(self,key):
        count = self.dvlc.GetStore().GetCount()
        for i in range(count):
            if self.dvlc.GetTextValue(i,0) == key:
                return i
        return -1
        
    def AddVariable(self,key,value):
        if self.CheckKeyExist(key):
            ret = wx.MessageBox(_("Key name has already exist in environment variable,Do you wann't to overwrite it?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
            if ret == wx.YES:
                row = self.GetVariableRow(key)
                assert(row != -1)
                self.RemoveRowVariable(row)
            else:
                return
        self.dvlc.AppendItem([key, value])
        
    def NewVariable(self,event):
        dlg = EditAddEnvironmentVariableDialog(self,-1,_("New Environment Variable"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        key = dlg.key_ctrl.GetValue().strip()
        value = dlg.value_ctrl.GetValue().strip()
        if status == wx.ID_OK and key and value:
            self.AddVariable(key,value)
        self.UpdateUI(None)
        dlg.Destroy()
        
    def EditVariable(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        dlg = EditAddEnvironmentVariableDialog(self,-1,_("Edit Environment Variable"))
        dlg.CenterOnParent()
        old_key = self.dvlc.GetTextValue(index,0)
        dlg.key_ctrl.SetValue(old_key)
        dlg.value_ctrl.SetValue(self.dvlc.GetTextValue(index,1))
        status = dlg.ShowModal()
        key = dlg.key_ctrl.GetValue().strip()
        value = dlg.value_ctrl.GetValue().strip()
        if status == wx.ID_OK and key and value:
            self.dvlc.SetTextValue(key,index,0)
            self.dvlc.SetTextValue(value,index,1)
        self.UpdateUI(None)
        dlg.Destroy()
        
    def OnGotoLink(self,event):
        dlg = SystemEnvironmentVariableDialog(self,-1,_("System Environment Variable"))
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
    
    def CheckKeyExist(self,key):
        for row in range(self.dvlc.GetStore().GetCount()):
            if self.dvlc.GetTextValue(row,0) == key:
                return True
        return False
        
    def GetEnviron(self):
        if self.interpreter is None:
            return
        dct = {}
        for row in range(self.dvlc.GetStore().GetCount()):
            dct[self.dvlc.GetTextValue(row,0)] = self.dvlc.GetTextValue(row,1)
        self.interpreter.Environ.SetEnviron(dct)
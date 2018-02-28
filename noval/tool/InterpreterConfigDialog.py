import wx
import wx.dataview as dataview
import Interpreter
import noval.parser.intellisence as intellisence
import noval.util.sysutils as sysutils
import os
import wx.lib.agw.hyperlink as hl
_ = wx.GetTranslation

SPACE = 10
HALF_SPACE = 5

class AddInterpreterDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(420,150)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Path:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.path_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        lineSizer.Add(self.path_ctrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, HALF_SPACE)
        
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.ChooseExecutablePath)
        lineSizer.Add(self.browser_btn, 0, wx.LEFT|wx.ALIGN_BOTTOM, SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Name:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.name_ctrl = wx.TextCtrl(self, -1, "", size=(190,-1))
        lineSizer.Add(self.name_ctrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        lineSizer.Add(ok_btn, 0, wx.LEFT, SPACE*22)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        lineSizer.Add(cancel_btn, 0, wx.LEFT, SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM|wx.RIGHT, SPACE)
        self.SetSizer(contentSizer)
        
    def ChooseExecutablePath(self,event):
        if sysutils.isWindows():
            descr = _("Executable (*.exe) |*.exe")
        else:
            descr = "All Files (*)|*"
        dlg = wx.FileDialog(self,_("Select Executable Path"),
                            wildcard=descr,style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.path_ctrl.SetValue(path)
            self.name_ctrl.SetValue(path)
            self.path_ctrl.SetInsertionPointEnd()
        dlg.Destroy()  
        
class PythonPathPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.tree_ctrl = wx.TreeCtrl(self, -1, style = wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.tree_ctrl, 1, wx.EXPAND)
        
    def AppendSysPath(self,interpreter):
        self.tree_ctrl.DeleteAllItems()
        root_item = self.tree_ctrl.AddRoot(_("Path List"))
        for path in interpreter.SyspathList:
            if path.strip() == "":
                continue
            self.tree_ctrl.AppendItem(root_item, path)
        self.tree_ctrl.ExpandAll()

class PythonBuiltinsPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.listbox = wx.ListBox(self, -1,style=wx.LB_SINGLE)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.listbox, 1, wx.EXPAND)
        
    def SetBuiltiins(self,interpreter):
        self.listbox.Clear()
        self.listbox.InsertItems(interpreter.Builtins,0)
        

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
        self.dvlc = dataview.DataViewListCtrl(self,size=(510,230))
        self.dvlc.AppendTextColumn(_('Key'), width=100)
        self.dvlc.AppendTextColumn(_('Value'),width=500)
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
        
    def SetVariables(self,interpreter):
        self.interpreter = interpreter
        self.dvlc.DeleteAllItems()
        for env in self.interpreter.Environ:
            self.dvlc.AppendItem([env,self.interpreter.Environ[env]])
        self._includeCheckBox.SetValue(self.interpreter.Environ.IncludeSystemEnviron)
            
    def RemoveVariable(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        self.RemoveRowVariable(index)
        self.UpdateUI(None)
        
    def RemoveRowVariable(self,row):
        key = self.dvlc.GetTextValue(row,0)
        self.interpreter.Environ.Remove(key)
        ##self.interpreter.environments = filter(lambda e:not e.has_key(key),self.interpreter.environments)
        self.dvlc.DeleteItem(row)
        
    def GetVariableRow(self,key):
        count = self.interpreter.Environ.GetCount()
        for i in range(count):
            if self.dvlc.GetTextValue(i,0) == key:
                return i
        return -1
        
    def AddVariable(self,key,value):
        self.interpreter.Environ.Add(key,value)
        self.dvlc.AppendItem([key, value])
        
    def NewVariable(self,event):
        dlg = EditAddEnvironmentVariableDialog(self,-1,_("New Environment Variable"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        key = dlg.key_ctrl.GetValue().strip()
        value = dlg.value_ctrl.GetValue().strip()
        if status == wx.ID_OK and key and value:
            if self.interpreter.Environ.Exist(key):
                 ret = wx.MessageBox(_("Key name has already exist in environment variable,Do you wann't to overwrite it?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
                 if ret == wx.YES:
                    row = self.GetVariableRow(key)
                    assert(row != -1)
                    self.RemoveRowVariable(row)
                    self.AddVariable(key,value)
            else:
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
            self.interpreter.Environ.Remove(old_key)
            self.interpreter.Environ.Add(key,value)
        self.UpdateUI(None)
        dlg.Destroy()
        
    def OnGotoLink(self,event):
        dlg = SystemEnvironmentVariableDialog(self,-1,_("System Environment Variable"))
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        
class InterpreterConfigDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(700,500)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        contentSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dvlc = dataview.DataViewListCtrl(self,size=(510,150))
        self.dvlc.AppendTextColumn(_('Name'), width=100)
        self.dvlc.AppendTextColumn(_('Version'), width=70)
        self.dvlc.AppendTextColumn(_('Path'), width=260)
        self.dvlc.AppendTextColumn(_('Default'), width=70)
        dataview.EVT_DATAVIEW_SELECTION_CHANGED(self.dvlc, -1, self.UpdateUI)
        dataview.EVT_DATAVIEW_ITEM_ACTIVATED(self.dvlc, -1, self.ModifyInterpreterNameDlg)
        contentSizer.Add(self.dvlc, 0, wx.EXPAND, 0)
        top_sizer.Add(contentSizer, 0, wx.LEFT, 0)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.add_btn = wx.Button(self, -1, _("Add"))
        wx.EVT_BUTTON(self.add_btn, -1, self.AddInterpreter)
        right_sizer.Add(self.add_btn, 0, wx.BOTTOM|wx.EXPAND, SPACE)
        
        self.remove_btn = wx.Button(self, -1, _("Remove"))
        wx.EVT_BUTTON(self.remove_btn, -1, self.RemoveInterpreter)
        right_sizer.Add(self.remove_btn, 0, wx.BOTTOM|wx.EXPAND, SPACE)
        
        self.smart_analyse_btn = wx.Button(self, -1, _("Smart Analyse"))
        wx.EVT_BUTTON(self.smart_analyse_btn, -1, self.SmartAnalyseIntreprter)
        right_sizer.Add(self.smart_analyse_btn, 0, wx.BOTTOM|wx.EXPAND, SPACE)
        
        self.set_default_btn = wx.Button(self, -1, _("Set Default"))
        wx.EVT_BUTTON(self.set_default_btn, -1, self.SetDefaultInterpreter)
        right_sizer.Add(self.set_default_btn, 0, wx.BOTTOM|wx.EXPAND, SPACE)
        
        top_sizer.Add(right_sizer, 0, wx.LEFT, SPACE*2)
        
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        nb = wx.Notebook(self,size=(650,330))
        self.path_panel = PythonPathPanel(nb)
        nb.AddPage(self.path_panel, _("Sys Path"))
        self.builtin_panel = PythonBuiltinsPanel(nb)
        nb.AddPage(self.builtin_panel, _("Builtin Modules"))
        self.environment_panel = EnvironmentPanel(nb)
        nb.AddPage(self.environment_panel, _("Environment Variable"))
        bottom_sizer.Add(nb, 0, wx.BOTTOM, HALF_SPACE)
        
        box_sizer.Add(top_sizer, 0, wx.BOTTOM, HALF_SPACE)
        box_sizer.Add(bottom_sizer, 0, wx.BOTTOM,0)

        self.SetSizer(box_sizer) 
        self.ScanAllInterpreters()
        self.UpdateUI(None)
        
        self.Fit()
        
    def ModifyInterpreterNameDlg(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.UpdateUI()
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
        dlg = AddInterpreterDialog(self,-1,_("Modify Interpreter Name"))
        dlg.path_ctrl.SetValue(interpreter.Path)
        dlg.path_ctrl.Enable(False)
        dlg.browser_btn.Enable(False)
        dlg.name_ctrl.SetValue(interpreter.Name)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if 0 == len(dlg.name_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Name is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                name = dlg.name_ctrl.GetValue()
                interpreter.Name = name
                self.dvlc.SetTextValue(interpreter.Name,index,0)
                passedCheck = True
        dlg.Destroy()
        
    def AddInterpreter(self,event):
        dlg = AddInterpreterDialog(self,-1,_("Add Interpreter"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if 0 == len(dlg.path_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Path is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif 0 == len(dlg.name_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Name is empty"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif not os.path.exists(dlg.path_ctrl.GetValue()):
                wx.MessageBox(_("Interpreter Path is not exist"),_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                try:
                    interpreter = Interpreter.InterpreterManager().AddPythonInterpreter(dlg.path_ctrl.GetValue(),dlg.name_ctrl.GetValue())
                    self.AddOneInterpreter(interpreter)
                    self.SmartAnalyse(interpreter)
                    passedCheck = True
                except Exception,e:
                    wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
                    status = dlg.ShowModal()     
        self.UpdateUI(None)
        dlg.Destroy()
        
    def AddOneInterpreter(self,interpreter):
        def GetDefaultFlag(is_default):
            if is_default:
                return _("Yes")
            else:
                return _("No")
        self.dvlc.AppendItem([interpreter.Name,interpreter.Version,interpreter.Path,GetDefaultFlag(interpreter.Default)],interpreter.Id)
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.environment_panel.SetVariables(interpreter)
        self.dvlc.Refresh()
        ###self.dvlc.SelectRow(item_count)
    
    def RemoveInterpreter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
        if interpreter.Default:
            wx.MessageBox(_("Default Interpreter cannot be remove"),_("Warning"),wx.OK|wx.ICON_WARNING,self)
            return
        ret = wx.MessageBox(_("Interpreter remove action cannot be recover,Do you want to continue remove this interpreter?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
        if ret == wx.YES:
            Interpreter.InterpreterManager().RemovePythonInterpreter(interpreter)
            self.ReloadAllInterpreters()
            
        self.UpdateUI(None)
        
    def SetDefaultInterpreter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
        if interpreter.Default:
            return
        Interpreter.InterpreterManager().SetDefaultInterpreter(interpreter)
        self.ReloadAllInterpreters()
        
    def SmartAnalyseIntreprter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
        self.SmartAnalyse(interpreter)

    def SmartAnalyse(self,interpreter):
        interpreter.GetSyspathList()
        interpreter.GetBuiltins()
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.smart_analyse_btn.Enable(False)

        dlg = AnalyseProgressDialog(self)
        intellisence.IntellisenceManager().generate_intellisence_data(interpreter,dlg)
        while True:
            if not dlg.KeepGoing:
                break
            wx.MilliSleep(250)
            wx.Yield()
            dlg.Pulse()
            
        dlg.Destroy()
        self.smart_analyse_btn.Enable(True)
          
    def ScanAllInterpreters(self):
        for interpreter in Interpreter.InterpreterManager.interpreters:
            self.AddOneInterpreter(interpreter)
            
    def ReloadAllInterpreters(self):
        self.dvlc.DeleteAllItems()
        self.ScanAllInterpreters()
        
    def UpdateUI(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.smart_analyse_btn.Enable(False)
            self.remove_btn.Enable(False)
            self.set_default_btn.Enable(False)
        else:
            self.remove_btn.Enable(True)
            self.set_default_btn.Enable(True)
            item = self.dvlc.RowToItem(index)
            id = self.dvlc.GetItemData(item)
            interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
            if Interpreter.InterpreterManager().IsInterpreterAnalysing():
                self.smart_analyse_btn.Enable(False)
            else:
                self.smart_analyse_btn.Enable(True)
            self.path_panel.AppendSysPath(interpreter)
            self.builtin_panel.SetBuiltiins(interpreter)
            self.environment_panel.SetVariables(interpreter)
            
        
class AnalyseProgressDialog(wx.ProgressDialog):
    
    def __init__(self,parent):
        wx.ProgressDialog.__init__(self,_("Interpreter Smart Analyse"),
                               _("Please wait a minute for end analysing"),
                               maximum = 100,
                               parent=parent,
                               style = 0
                                | wx.PD_APP_MODAL
                                | wx.PD_SMOOTH
                                )
        self.KeepGoing = True                                
        
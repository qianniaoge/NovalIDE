import wx
import wx.dataview as dataview
import Interpreter
import noval.parser.intellisence as intellisence
import noval.util.sysutils as sysutils
import os
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
            descr = "All|*.*"
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
        root_item = self.tree_ctrl.AddRoot("Path List")
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

class EnviromentPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self)
        self.dvlc.AppendTextColumn('Key', width=100)
        self.dvlc.AppendTextColumn('Value',width=500)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        
    def SetVariables(self):
        self.dvlc.DeleteAllItems()
        for env in os.environ:
            self.dvlc.AppendItem([env, os.environ[env]])
        
class InterpreterConfigDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(700,500)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        contentSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dvlc = dataview.DataViewListCtrl(self,size=(510,150))
        self.dvlc.AppendTextColumn('Name', width=100)
        self.dvlc.AppendTextColumn('Version', width=70)
        self.dvlc.AppendTextColumn('Path', width=260)
        self.dvlc.AppendTextColumn('Default', width=70)
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
        nb.AddPage(self.path_panel, "Sys Path")
        self.builtin_panel = PythonBuiltinsPanel(nb)
        nb.AddPage(self.builtin_panel, "Builtin Modules")
        self.enviroment_panel = EnviromentPanel(nb)
        nb.AddPage(self.enviroment_panel, "Enviroment Variable")
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
                wx.MessageBox("Interpreter Name is empty",_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                name = dlg.name_ctrl.GetValue()
                interpreter.Name = name
                self.dvlc.SetTextValue(interpreter.Name,index,0)
                passedCheck = True
        dlg.Destroy()
        
    def AddInterpreter(self,event):
        dlg = AddInterpreterDialog(self,-1,_("Add Interpreter Path"))
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if 0 == len(dlg.path_ctrl.GetValue()):
                wx.MessageBox("Interpreter Path is empty",_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif 0 == len(dlg.name_ctrl.GetValue()):
                wx.MessageBox("Interpreter Name is empty",_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            elif not os.path.exists(dlg.path_ctrl.GetValue()):
                wx.MessageBox("Interpreter Path is not exist",_("Error"),wx.OK|wx.ICON_ERROR,self)
                status = dlg.ShowModal()
            else:
                try:
                    interpreter = Interpreter.InterpreterManager().AddPythonInterpreter(dlg.path_ctrl.GetValue(),dlg.name_ctrl.GetValue())
                    self.AddOneInterpreter(interpreter)
                    passedCheck = True
                except Exception,e:
                    wx.MessageBox(e.msg,_("Error"),wx.OK|wx.ICON_ERROR,self)
                    status = dlg.ShowModal()            
        dlg.Destroy()
        
    def AddOneInterpreter(self,interpreter):
        def GetDefaultFlag(is_default):
            if is_default:
                return "Yes"
            else:
                return "No"
        self.dvlc.AppendItem([interpreter.Name,interpreter.Version,interpreter.Path,GetDefaultFlag(interpreter.Default)],interpreter.Id)
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.enviroment_panel.SetVariables()
    
    def RemoveInterpreter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = Interpreter.InterpreterManager().GetInterpreterById(id)
        if interpreter.Default:
            wx.MessageBox("Default Interpreter cannot be remove",_("Warning"),wx.OK|wx.ICON_WARNING,self)
            return
        ret = wx.MessageBox("Interpreter remove action cannot be recover,Do you want to continue remove this interpreter?",_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
        if ret == wx.YES:
            Interpreter.InterpreterManager().RemovePythonInterpreter(interpreter)
            self.ReloadAllInterpreters()
        
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
        interpreter.GetSyspathList()
        interpreter.GetBuiltins()
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.enviroment_panel.SetVariables()
        self.smart_analyse_btn.Enable(False)

        dlg = AnalyseProgressDialog(self)
        if sysutils.isWindows():
            dlg.Pulse()
            intellisence.IntellisenceManager().generate_intellisence_data(interpreter,dlg)
        else:
            interpreter.Analysing = True
            intellisence.IntellisenceManager().generate_intellisence_data(interpreter,dlg)
            self.temp = 0
            while True:
                if not interpreter.Analysing:
                    dlg.Destroy()
                    self.smart_analyse_btn.Enable(True)
                    break
                if self.temp >=100:
                    self.temp = 0
                wx.MilliSleep(50)
                wx.Yield()
                dlg.Update(self.temp)
                self.temp += 1
          
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
            self.enviroment_panel.SetVariables()
            
        
class AnalyseProgressDialog(wx.ProgressDialog):
    
    Parent = None
    def __init__(self,parent):
        wx.ProgressDialog.__init__(self,"Interpreter Smart Analyse",
                               "Please wait a minute for end analysing",
                               maximum = 100,
                               parent=parent,
                               style = 0
                                | wx.PD_APP_MODAL
                                | wx.PD_SMOOTH
                                )
                                
        AnalyseProgressDialog.Parent = parent
        
    def Destroy(self):
        wx.ProgressDialog.Destroy(self)
        AnalyseProgressDialog.Parent.smart_analyse_btn.Enable(True)
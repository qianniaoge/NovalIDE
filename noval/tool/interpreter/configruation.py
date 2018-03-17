import wx
import wx.dataview as dataview
import Interpreter
import noval.parser.intellisence as intellisence
import noval.util.sysutils as sysutils
import os
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import pythonbuiltins
import environment
import packages
import pythonpath
import noval.tool.interpreter.manager as interpretermanager

ID_COPY_INTERPRETER_NAME = wx.NewId()
ID_COPY_INTERPRETER_VERSION = wx.NewId()
ID_COPY_INTERPRETER_PATH = wx.NewId()
ID_MODIFY_INTERPRETER_NAME = wx.NewId()
ID_REMOVE_INTERPRETER = wx.NewId()
ID_NEW_INTERPRETER_VIRTUALENV = wx.NewId()


class NewVirtualEnvProgressDialog(wx.ProgressDialog):
    
    def __init__(self,parent):
        wx.ProgressDialog.__init__(self,_("New Virtual Env"),
                               _("Please wait a minute for end New Virtual Env"),
                               maximum = 100,
                               parent = parent,
                               style = 0
                                | wx.PD_APP_MODAL
                                | wx.PD_SMOOTH
                                )
        self.KeepGoing = True        

class NewVirtualEnvDialog(wx.Dialog):
    def __init__(self,parent,interpreter,dlg_id,title,size=(440,200)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        flexGridSizer = wx.FlexGridSizer(cols = 3, vgap = HALF_SPACE, hgap = HALF_SPACE)
        flexGridSizer.AddGrowableCol(1,1)
        
        flexGridSizer.Add(wx.StaticText(self, -1, _("Name:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self.name_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        flexGridSizer.Add(self.name_ctrl, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        flexGridSizer.Add(wx.StaticText(parent, -1, ""), 0)

        flexGridSizer.Add(wx.StaticText(self, -1, _("Location:")), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self.path_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        self.path_ctrl.SetToolTipString(_("set the location of virtual env"))
        flexGridSizer.Add(self.path_ctrl, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self.browser_btn = wx.Button(self, -1, _("..."),size=(40,-1))
        wx.EVT_BUTTON(self.browser_btn, -1, self.ChooseVirtualEnvPath)
        flexGridSizer.Add(self.browser_btn, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=SPACE)  
        
        flexGridSizer.Add(wx.StaticText(self, -1, _("Base Interpreter:")), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        self._interprterChoice = wx.combo.BitmapComboBox(self, -1, "",choices=[], style=wx.CB_READONLY)
        flexGridSizer.Add(self._interprterChoice, 2, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        flexGridSizer.Add(wx.StaticText(parent, -1, ""), 0)
        
        contentSizer.Add(flexGridSizer, 1, flag=wx.EXPAND|wx.LEFT|wx.TOP,border=SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        #set ok button default focused
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 1, wx.EXPAND|wx.BOTTOM,SPACE)
        self.SetSizer(contentSizer)
        self._interpreter = interpreter
        self.LoadInterpreters()
        
    def LoadInterpreters(self):
        interpreter_image_path = os.path.join(sysutils.mainModuleDir, "noval", "tool", "bmp_source", "python_nature.png")
        interpreter_image = wx.Image(interpreter_image_path,wx.BITMAP_TYPE_ANY)
        interpreter_bmp = wx.BitmapFromImage(interpreter_image)
        for i,interpreter in enumerate(interpretermanager.InterpreterManager.interpreters):
            display_name = "%s (%s)" % (interpreter.Version,interpreter.Path)
            self._interprterChoice.Append(display_name,interpreter_bmp,interpreter.Path)
            if interpreter.Path == self._interpreter.Path:
                self._interprterChoice.SetSelection(i)
        
    def ChooseVirtualEnvPath(self,event):
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                _("Choose the location of Virtual Env"), 
                style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        self.path_ctrl.SetValue(path)


class AddInterpreterDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,size=(420,150)):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=size)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Path:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.path_ctrl = wx.TextCtrl(self, -1, "", size=(200,-1))
        if sysutils.isWindows():
            self.path_ctrl.SetToolTipString(_("set the location of python.exe or pythonw.exe"))
        else:
            self.path_ctrl.SetToolTipString(_("set the location of python interpreter"))
        lineSizer.Add(self.path_ctrl, 0, wx.LEFT|wx.ALIGN_BOTTOM, HALF_SPACE)
        
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.ChooseExecutablePath)
        lineSizer.Add(self.browser_btn, 0, wx.LEFT|wx.ALIGN_BOTTOM, SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(self, -1, _("Interpreter Name:")), 0, wx.ALIGN_CENTER | wx.LEFT, HALF_SPACE)
        self.name_ctrl = wx.TextCtrl(self, -1, "", size=(190,-1))
        self.name_ctrl.SetToolTipString(_("set the name of python interpreter"))
        lineSizer.Add(self.name_ctrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 1, wx.EXPAND,SPACE)
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
        dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU(self.dvlc, -1,self.OnContextMenu)
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
        nb = wx.Notebook(self,size=(650,350))
        self.package_panel = packages.PackagePanel(nb)
        nb.AddPage(self.package_panel, _("Package"))
        self.path_panel = pythonpath.PythonPathPanel(nb)
        nb.AddPage(self.path_panel, _("Search Path"))
        self.builtin_panel = pythonbuiltins.PythonBuiltinsPanel(nb)
        nb.AddPage(self.builtin_panel, _("Builtin Modules"))
        self.environment_panel = environment.EnvironmentPanel(nb)
        nb.AddPage(self.environment_panel, _("Environment Variable"))
        bottom_sizer.Add(nb, 0, wx.BOTTOM, HALF_SPACE)
        
        box_sizer.Add(top_sizer, 0, wx.BOTTOM, HALF_SPACE)
        box_sizer.Add(bottom_sizer, 0, wx.BOTTOM,0)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        wx.EVT_BUTTON(ok_btn, -1, self.OnOK)
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        box_sizer.Add(bsizer, 1, wx.BOTTOM|wx.EXPAND,SPACE)

        self.SetSizer(box_sizer) 
        self.ScanAllInterpreters()
        self.UpdateUI(None)
        
        self.Fit()
        
    def OnContextMenu(self, event):
        menu = wx.Menu()
        x, y = event.GetPosition().x,event.GetPosition().y
        menu.Append(ID_COPY_INTERPRETER_NAME,_("Copy Name"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_NAME, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_NAME, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_COPY_INTERPRETER_VERSION,_("Copy Version"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_VERSION, self.ProcessEvent) 
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_VERSION, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_COPY_INTERPRETER_PATH,_("Copy Path"))
        wx.EVT_MENU(self, ID_COPY_INTERPRETER_PATH, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_COPY_INTERPRETER_PATH, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_MODIFY_INTERPRETER_NAME,_("Modify Name"))
        wx.EVT_MENU(self, ID_MODIFY_INTERPRETER_NAME, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_MODIFY_INTERPRETER_NAME, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_REMOVE_INTERPRETER,_("Remove"))
        wx.EVT_MENU(self, ID_REMOVE_INTERPRETER, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_REMOVE_INTERPRETER, self.ProcessUpdateUIEvent)
        
        menu.Append(ID_NEW_INTERPRETER_VIRTUALENV,_("New VirtualEnv"))
        wx.EVT_MENU(self, ID_NEW_INTERPRETER_VIRTUALENV, self.ProcessEvent)
        wx.EVT_UPDATE_UI(self, ID_NEW_INTERPRETER_VIRTUALENV, self.ProcessUpdateUIEvent)
        
        self.dvlc.PopupMenu(menu,wx.Point(x, y))
        menu.Destroy()
        
    def ProcessEvent(self, event): 
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)   
        id = event.GetId()
        if id == ID_COPY_INTERPRETER_NAME:
            sysutils.CopyToClipboard(interpreter.Name)
            return True
        elif id == ID_COPY_INTERPRETER_VERSION:
            sysutils.CopyToClipboard(interpreter.Version)
            return True
        elif id == ID_COPY_INTERPRETER_PATH:
            sysutils.CopyToClipboard(interpreter.Path)
            return True
        elif id == ID_MODIFY_INTERPRETER_NAME:
            self.ModifyInterpreterNameDlg(None)
            return True
        elif id == ID_REMOVE_INTERPRETER:
            self.RemoveInterpreter(None)
            return True
        elif id == ID_NEW_INTERPRETER_VIRTUALENV:
            dlg = NewVirtualEnvDialog(self,interpreter,-1,_("New Virtual Env"))
            dlg.CenterOnParent()
            status = dlg.ShowModal()
            if status == wx.ID_OK:
                pass
            return True
            
    def ProcessUpdateUIEvent(self, event):
        if self.dvlc.GetSelectedRow() == wx.NOT_FOUND:
            event.Enable(False)
            return False
        event.Enable(True)
        return True
        
    def ModifyInterpreterNameDlg(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            self.UpdateUI()
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)
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
                    interpreter = interpretermanager.InterpreterManager().AddPythonInterpreter(dlg.path_ctrl.GetValue(),dlg.name_ctrl.GetValue())
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
        item_count = self.dvlc.GetStore().GetCount()
        self.dvlc.AppendItem([interpreter.Name,interpreter.Version,interpreter.Path,GetDefaultFlag(interpreter.Default)],interpreter.Id)
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.environment_panel.SetVariables(interpreter)
        self.package_panel.LoadPackages(interpreter)
        self.dvlc.Refresh()
        self.dvlc.SelectRow(item_count)
    
    def RemoveInterpreter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)
        if interpreter.Default:
            wx.MessageBox(_("Default Interpreter cannot be remove"),_("Warning"),wx.OK|wx.ICON_WARNING,self)
            return
        ret = wx.MessageBox(_("Interpreter remove action cannot be recover,Do you want to continue remove this interpreter?"),_("Warning"),wx.YES_NO|wx.ICON_QUESTION,self)
        if ret == wx.YES:
            interpretermanager.InterpreterManager().RemovePythonInterpreter(interpreter)
            self.ReloadAllInterpreters()
            
        self.UpdateUI(None)
        
    def SetDefaultInterpreter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
            
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)
        if interpreter.Default:
            return
        interpretermanager.InterpreterManager().SetDefaultInterpreter(interpreter)
        self.ReloadAllInterpreters()
        
    def SmartAnalyseIntreprter(self,event):
        index = self.dvlc.GetSelectedRow()
        if index == wx.NOT_FOUND:
            return
        item = self.dvlc.RowToItem(index)
        id = self.dvlc.GetItemData(item)
        interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)
        self.SmartAnalyse(interpreter)

    def SmartAnalyse(self,interpreter):
        interpreter.GetDocPath()
        interpreter.GetSysPathList()
        interpreter.GetBuiltins()
        self.package_panel.LoadPackages(interpreter,True)
        self.path_panel.AppendSysPath(interpreter)
        self.builtin_panel.SetBuiltiins(interpreter)
        self.smart_analyse_btn.Enable(False)

        dlg = AnalyseProgressDialog(self)
        try:
            intellisence.IntellisenceManager().generate_intellisence_data(interpreter,dlg)
        except:
            return
        while True:
            if not dlg.KeepGoing:
                break
            wx.MilliSleep(250)
            wx.Yield()
            dlg.Pulse()
            
        dlg.Destroy()
        self.smart_analyse_btn.Enable(True)
          
    def ScanAllInterpreters(self):
        for interpreter in interpretermanager.InterpreterManager.interpreters:
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
            interpreter = interpretermanager.InterpreterManager().GetInterpreterById(id)
            if interpretermanager.InterpreterManager().IsInterpreterAnalysing() or not interpreter.IsValidInterpreter:
                self.smart_analyse_btn.Enable(False)
            else:
                self.smart_analyse_btn.Enable(True)
            self.path_panel.AppendSysPath(interpreter)
            self.builtin_panel.SetBuiltiins(interpreter)
            self.environment_panel.SetVariables(interpreter)
            self.package_panel.LoadPackages(interpreter)
            
    def OnOK(self,event):
        try:
            self.path_panel.GetPythonPathList()
            self.environment_panel.GetEnviron()
            interpretermanager.InterpreterManager().SavePythonInterpretersConfig()
            self.Destroy()
        except Exception as e:
            wx.MessageBox(e.msg,_("Save Interpreter Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
            
        
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
        
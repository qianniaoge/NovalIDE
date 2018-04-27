# -*- coding: utf-8 -*-
import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import noval.tool.WxThreadSafe as WxThreadSafe
import wx.dataview as dataview
import noval.tool.interpreter.manager as interpretermanager
import os
import subprocess
import noval.tool.OutputThread as OutputThread
import threading
import noval.util.strutils as strutils

class ManagePackagesDialog(wx.Dialog):
    
    MANAGE_INSTALL_PACKAGE = 1
    MANAGE_UNINSTALL_PACKAGE = 2
    def __init__(self,parent,dlg_id,title,manage_action,interpreter,package_name=''):
        self.interpreter = interpreter
        self._manage_action = manage_action
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(-1,-1))
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("Type the name of package to install")), 0, wx.ALIGN_CENTER, 0)
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("Type the name of package to uninstall")), 0, wx.ALIGN_CENTER, 0)
        box_sizer.Add(lineSizer, 0,wx.EXPAND| wx.ALL, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("We will download and install it in the interpreter:")), 0, \
                          wx.ALIGN_CENTER | wx.LEFT, SPACE)
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("We will uninstall it in the interpreter:")), 0, \
                          wx.ALIGN_CENTER | wx.LEFT, SPACE)
        choices,default_selection = interpretermanager.InterpreterManager().GetChoices()
        self._interpreterCombo = wx.ComboBox(self, -1,choices=choices,value=self.interpreter.Name, style = wx.CB_READONLY)
        lineSizer.Add(self._interpreterCombo,0, wx.EXPAND|wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0,wx.EXPAND| wx.RIGHT|wx.BOTTOM, SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.value_ctrl = wx.TextCtrl(self, -1, "",size=(-1,-1))
        lineSizer.Add(self.value_ctrl, 1, wx.LEFT|wx.EXPAND, SPACE)
        if self._manage_action == ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE:
            self.value_ctrl.SetValue(package_name)
        self.browser_btn = wx.Button(self, -1, _("Browse..."))
        wx.EVT_BUTTON(self.browser_btn, -1, self.BrowsePath)
        lineSizer.Add(self.browser_btn, 0,flag=wx.LEFT, border=SPACE) 
        box_sizer.Add(lineSizer, 0, flag=wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=SPACE)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            lineSizer.Add(wx.StaticText(self, -1, _("To install the specific version,type \"xxx==1.0.1\"\nTo install more packages,please specific the path of requirements.txt")), \
                          0, wx.ALIGN_CENTER | wx.LEFT, SPACE)
            
        else:
            lineSizer.Add(wx.StaticText(self, -1, _("To uninstall more packages,please specific the path of requirements.txt")), \
                          0, wx.ALIGN_CENTER | wx.LEFT, SPACE)
        box_sizer.Add(lineSizer, 0, wx.RIGHT|wx.BOTTOM|wx.EXPAND, SPACE)
        
        self.detailSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.output_ctrl = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE,size=(-1,250))
        self.output_ctrl.Enable(False)
        self.detailSizer.Add(self.output_ctrl, 1, wx.LEFT|wx.BOTTOM, SPACE)
        box_sizer.Add(self.detailSizer, 0, wx.RIGHT|wx.BOTTOM|wx.EXPAND, SPACE)
        box_sizer.Hide(self.detailSizer)
        
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_btn = wx.Button(self, -1, _("Show Details") + "↓")
        self._show_details = False
        wx.EVT_BUTTON(self.detail_btn, -1, self.ShowHideDetails)
        bsizer.Add(self.detail_btn, 0,flag=wx.LEFT, border=SPACE) 
        
        bsizer.Add(wx.StaticText(self, -1, ""), 1, wx.LEFT|wx.EXPAND, 0)
        
        self.ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        #set ok button default focused
        self.ok_btn.SetDefault()
        wx.EVT_BUTTON(self.ok_btn, -1, self.OnOKClick)
        bsizer.Add(self.ok_btn, 0,flag=wx.RIGHT, border=SPACE) 
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.Add(cancel_btn, 0,flag=wx.RIGHT, border=SPACE) 
        
        box_sizer.Add(bsizer, 0, wx.EXPAND |wx.BOTTOM,SPACE)
        
        self.SetSizer(box_sizer)
        self.Fit()
        
    def ShowHideDetails(self,event):
        if self._show_details:
            self.detail_btn.SetLabel( _("Show Details") + "↓")
            self.GetSizer().Hide(self.detailSizer)
            self._show_details = False 
        else:  
            self.GetSizer().Show(self.detailSizer)  
            self.detail_btn.SetLabel( _("Hide Details") + "↑") 
            self._show_details = True   
        self.GetSizer().Layout()
        self.Fit()
        
    def BrowsePath(self,event):
        descr = _("Text File (*.txt)|*.txt")
        title = _("Choose requirements.txt")
        dlg = wx.FileDialog(self,title ,
                       wildcard = descr,
                       style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        path = dlg.GetPath()
        dlg.Destroy()
        self.value_ctrl.SetValue(path)
        
    def ExecCommandAndOutput(self,command,dlg):
        #shell must be True on linux
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout_thread = OutputThread.OutputThread(p.stdout,p,dlg,call_after=True)
        stdout_thread.start()
        stderr_thread = OutputThread.OutputThread(p.stderr,p,dlg,call_after=True)
        stderr_thread.start()
        p.wait()
        self.EndDialog(p.returncode)
    
    @WxThreadSafe.call_after
    def EndDialog(self,retcode):
        if retcode == 0:
            if self._manage_action == self.MANAGE_INSTALL_PACKAGE:
                wx.MessageBox(_("Install Success"))
            else:
                wx.MessageBox(_("Uninstall Success"))
            self.EndModal(wx.ID_OK)
        else:
            if self._manage_action == self.MANAGE_INSTALL_PACKAGE:
                wx.MessageBox(_("Install Fail"),style=wx.OK|wx.ICON_ERROR)
            else:
                wx.MessageBox(_("Uninstall Fail"),style=wx.OK|wx.ICON_ERROR)
            self.value_ctrl.Enable(True)
            self.ok_btn.Enable(True)
        
    def InstallPackage(self,interpreter):
        package_name = self.value_ctrl.GetValue().strip()
        if os.path.basename(package_name) == "requirements.txt":
            command = strutils.emphasis_path(interpreter.GetPipPath()) + " install -r %s" % (package_name)
        else:
            command = strutils.emphasis_path(interpreter.GetPipPath()) + " install %s" % (package_name)
        self.output_ctrl.write(command + os.linesep)
        self.call_back = self.output_ctrl.write
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def UninstallPackage(self,interpreter):
        package_name = self.value_ctrl.GetValue().strip()
        if os.path.basename(package_name) == "requirements.txt":
            command = interpreter.GetPipPath() + " uninstall -y -r %s" % (package_name)
        else:
            command = interpreter.GetPipPath() + " uninstall -y %s" % (package_name)
        self.output_ctrl.write(command + os.linesep)
        self.call_back = self.output_ctrl.write
        t = threading.Thread(target=self.ExecCommandAndOutput,args=(command,self))
        t.start()
        
    def OnOKClick(self, event):
        if self.value_ctrl.GetValue().strip() == "":
            wx.MessageBox(_("package name is empty"))
            return
        interpreter_name = self._interpreterCombo.GetStringSelection()
        interpreter = interpretermanager.InterpreterManager().GetInterpreterByName(interpreter_name)
        if interpreter.IsBuiltIn or interpreter.GetPipPath() is None:
            wx.MessageBox(_("Could not find pip on the path"),style=wx.OK|wx.ICON_ERROR)
            return
        self.value_ctrl.Enable(False)
        self.ok_btn.Enable(False)
        if self._manage_action == ManagePackagesDialog.MANAGE_INSTALL_PACKAGE:
            self.InstallPackage(interpreter)
        else:
            self.UninstallPackage(interpreter)
        
class PackagePanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self)
        self.dvlc.AppendTextColumn(_('Name'), width=200)
        self.dvlc.AppendTextColumn(_('Version'),width=250)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.install_btn = wx.Button(self, -1, _("Install with pip"))
        wx.EVT_BUTTON(self.install_btn, -1, self.InstallPip)
        right_sizer.Add(self.install_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND, SPACE)
        
        self.uninstall_btn = wx.Button(self, -1, _("Uninstall with pip"))
        wx.EVT_BUTTON(self.uninstall_btn, -1, self.UninstallPip)
        right_sizer.Add(self.uninstall_btn, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND, SPACE)
        self.Sizer.Add(right_sizer, 0, wx.TOP, SPACE)
        self.interpreter = None

    def InstallPip(self,event):
        dlg = ManagePackagesDialog(self,-1,_("Install Package"),ManagePackagesDialog.MANAGE_INSTALL_PACKAGE,self.interpreter)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        if status == wx.ID_OK:
            pass
        dlg.Destroy()
        
    def UninstallPip(self,event):
        index = self.dvlc.GetSelectedRow()
        package_name = ""
        if index != wx.NOT_FOUND:
            package_name = self.dvlc.GetTextValue(index,0)
        dlg = ManagePackagesDialog(self,-1,_("Uninstall Package"),ManagePackagesDialog.MANAGE_UNINSTALL_PACKAGE,self.interpreter,package_name=package_name)
        dlg.CenterOnParent()
        status = dlg.ShowModal()
        if status == wx.ID_OK:
            pass
        dlg.Destroy()
        
    def LoadPackages(self,interpreter,force=False):
        self.interpreter = interpreter
        if self.interpreter is None or self.interpreter.IsBuiltIn or self.interpreter.GetPipPath() is None:
            self.install_btn.Enable(False)
            self.uninstall_btn.Enable(False)
        else:
            self.install_btn.Enable(True)
            self.uninstall_btn.Enable(True)
        self.dvlc.DeleteAllItems()
        interpreter.LoadPackages(self,force)
        if interpreter.IsLoadingPackage:
            self.dvlc.AppendItem([_("Loading Package List....."),""])
            return
        self.LoadPackageList(interpreter)
            
    def LoadPackageList(self,interpreter):
        for name in interpreter.Packages:
            self.dvlc.AppendItem([name,interpreter.Packages[name]])
            
    @WxThreadSafe.call_after
    def LoadPackageEnd(self,interpreter):
        if self.interpreter != interpreter:
            return
        self.dvlc.DeleteAllItems()
        self.LoadPackageList(interpreter)
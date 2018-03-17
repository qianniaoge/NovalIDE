import wx
from consts import SPACE,HALF_SPACE,_
import os
import noval.util.sysutils as sysutils
import Interpreter


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
        self.configure_btn = wx.Button(self, -1, _("..."),size=(40,-1))
        wx.EVT_BUTTON(self.configure_btn, -1, self.ConfigureInterprter)
        flexGridSizer.Add(self.configure_btn, flag=wx.ALIGN_LEFT|wx.RIGHT,border=SPACE)
        
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
        for i,interpreter in enumerate(Interpreter.InterpreterManager.interpreters):
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
            
    def ConfigureInterprter(self,event):
        dlg = InterpreterConfigDialog(self,-1,_("Configure Interpreter"))
        dlg.CenterOnParent()
        dlg.ShowModal()

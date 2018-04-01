import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import ProjectEditor

class PromptMessageDialog(wx.Dialog):
    
    DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YES
    def __init__(self,parent,dlg_id,title,msg):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        #-- icon and message --#
        msgSizer = wx.BoxSizer(wx.HORIZONTAL)
        # icon #
        artID = wx.ART_QUESTION

        bmp = wx.ArtProvider_GetBitmap(artID, wx.ART_MESSAGE_BOX, (48, 48))
        bmpIcon = wx.StaticBitmap(self, -1, bmp)
        msgSizer.Add(bmpIcon, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        # msg #
        txtMsg = wx.StaticText(self, -1, msg, style=wx.ALIGN_CENTRE)
        msgSizer.Add(txtMsg, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        sizer.Add(msgSizer, 0, wx.ALIGN_CENTRE, HALF_SPACE)
        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALL, HALF_SPACE)
        #-- buttons --#
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btnYes = wx.Button(self, wx.ID_YES, _('Yes'))
        btnSizer.Add(btnYes, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_YES, self.OnBtnClick)
        
        btnNo = wx.Button(self, wx.ID_NO, _('No'))
        btnSizer.Add(btnNo, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
                    
        wx.EVT_BUTTON(self, wx.ID_YESTOALL, self.OnBtnClick)
                           
        btnYesAll = wx.Button(self, wx.ID_YESTOALL, _('YestoAll'))
        btnSizer.Add(btnYesAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NO, self.OnBtnClick)
        btnNoAll = wx.Button(self, wx.ID_NOTOALL, _('NotoAll'))
        btnSizer.Add(btnNoAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NOTOALL, self.OnBtnClick)


        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE | wx.TOP|wx.BOTTOM, SPACE)
        #--
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Fit()

    def OnBtnClick(self,event):
        self.EndModal(event.GetId())
        

class FileFilterDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        self.filters = []
        wx.Dialog.__init__(self,parent,dlg_id,title)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        
        boxsizer.Add(wx.StaticText(self, -1, _("Please select file types to to allow added to project:"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.ALL,border=SPACE)
        
        self.listbox = wx.CheckListBox(self,-1,size=(230,320),choices=[])
        boxsizer.Add(self.listbox,0,flag = wx.EXPAND|wx.BOTTOM|wx.RIGHT,border = SPACE)
        
        boxsizer.Add(wx.StaticText(self, -1, _("Other File Extensions:(seperated by ';')"), \
                        style=wx.ALIGN_CENTRE),0,flag=wx.BOTTOM|wx.RIGHT,border=SPACE)
                        
        self.other_extensions_ctrl = wx.TextCtrl(self, -1, "", size=(-1,-1))
        boxsizer.Add(self.other_extensions_ctrl, 0, flag=wx.BOTTOM|wx.RIGHT|wx.EXPAND,border=SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
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
        self.InitFilters()
        
    def OnOKClick(self,event):
        filters = []
        for i in range(self.listbox.GetCount()):
            if self.listbox.IsChecked(i):
               filters.append(self.listbox.GetString(i))
        extension_value = self.other_extensions_ctrl.GetValue().strip()
        if extension_value != "":
            extensions = extension_value.split(";")
            filters.extend(extensions)
        self.filters = [str(fitler.replace("*","").replace(".","")) for fitler in filters]
        self.EndModal(wx.ID_OK)
        
    def InitFilters(self):
        descr = ''
        for temp in wx.GetApp().GetDocumentManager().GetTemplates():
            if temp.IsVisible() and temp.GetDocumentType() != ProjectEditor.ProjectDocument:
                filters = temp.GetFileFilter().split(";")
                for filter in filters:
                    self.listbox.Append(filter)
 
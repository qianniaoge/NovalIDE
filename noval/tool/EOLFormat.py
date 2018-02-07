import wx
import noval.util.sysutils as sysutilslib
import os
_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

ChoiceDialogNameStr = u"ChoiceDialog"

class BasePanelDlg(wx.Dialog):
    """Editra Control Library Base Dialog Class"""
    def __init__(self, parent, id=wx.ID_ANY, title=u"",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, 
                 style=wx.DEFAULT_DIALOG_STYLE, name=u"ECBaseDialog"):
        super(BasePanelDlg, self).__init__(parent, id, title, pos,
                                        size, style, name)

        # Attributes
        self._panel = None

        # Setup
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))

    Panel = property(lambda self: self.GetPanel(),
                     lambda self, val: self.SetPanel(val))

    def GetPanel(self):
        """Get the dialogs main panel"""
        return self._panel

    def SetPanel(self, panel):
        """Set the dialogs main panel"""
        assert isinstance(panel, wx.Panel)
        if self._panel is not None:
            self._panel.Destroy()
        self._panel = panel
        self.Sizer.Add(self._panel, 1, wx.EXPAND)


#-----------------------------------------------------------------------------#
# Decorators

class expose(object):
    """Expose a panels method to a to a specified class
    The specified class must have a GetPanel method

    """
    def __init__(self, cls):
        """@param cls: class to expose the method to"""
        super(expose, self).__init__()
        self.cls = cls

    def __call__(self, funct):
        fname = funct.func_name
        def parentmeth(*args, **kwargs):
            self = args[0]
            return getattr(self.GetPanel(), fname)(*args[1:], **kwargs)
        parentmeth.__name__ = funct.__name__
        parentmeth.__doc__ = funct.__doc__
        setattr(self.cls, fname, parentmeth)

        return funct
		
#--------------------------------------------------------------------------#
class ChoiceDialog(BasePanelDlg):
    """Dialog with a wx.Choice control for showing a list of choices"""
    def __init__(self, parent, id=wx.ID_ANY,
                 msg=u'', title=u'',
                 choices=None, default=u'',
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=0,
                 name=ChoiceDialogNameStr):
        """Create the choice dialog
        @param parent: Parent Window
        @keyword id: Dialog ID
        @keyword msg: Dialog Message
        @keyword title: Dialog Title
        @keyword choices: list of strings
        @keyword default: Default selection
        @keyword pos: Dialog Position
        @keyword size: Dialog Size
        @keyword style: Dialog Style bitmask
        @keyword name: Dialog Name

        """
        super(ChoiceDialog, self).__init__(parent, id, title,
                                           style=wx.CAPTION, pos=pos,
                                           size=size, name=name)
        # Attributes
        panel = ChoicePanel(self, msg=msg,
                                  choices=choices,
                                  default=default,
                                  style=style)
        self.SetPanel(panel)
        self.SetInitialSize()

class ChoicePanel(wx.Panel):
    """Generic Choice dialog panel"""
    def __init__(self, parent, msg=u'', choices=list(),
                 default=u'', style=wx.OK|wx.CANCEL):
        """Create the panel
        @param parent: Parent Window
        @keyword msg: Display message
        @keyword choices: list of strings
        @keyword default: default selection
        @keyword style: panel style

        """
        super(ChoicePanel, self).__init__(parent)

        # Attributes
        self._msg = msg
        self._choices = wx.Choice(self, wx.ID_ANY)
        self._selection = default
        self._selidx = 0
        self._bmp = None
        self._buttons = list()

        # Setup
        self._choices.SetItems(choices)
        if default in choices:
            self._choices.SetStringSelection(default)
            self._selidx = self._choices.GetSelection()
        else:
            self._choices.SetSelection(0)
            self._selidx = 0
            self._selection = self._choices.GetStringSelection()

        # Setup Buttons
        for btn, id_ in ((wx.OK, wx.ID_OK), (wx.CANCEL, wx.ID_CANCEL),
                         (wx.YES, wx.ID_YES), (wx.NO, wx.ID_NO)):
            if btn & style:
                button = wx.Button(self, id_)
                self._buttons.append(button)

        if not len(self._buttons):
            self._buttons.append(wx.Button(self, wx.ID_OK))
            self._buttons.append(wx.Button(self, wx.ID_CANCEL))

        # Layout
        self.__DoLayout(style)

        # Event Handlers
        self.Bind(wx.EVT_CHOICE, self.OnChoice, self._choices)
        self.Bind(wx.EVT_BUTTON, self.OnButton)

    def __DoLayout(self, style):
        """Layout the panel"""
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        caption = wx.StaticText(self, label=self._msg)

        # Layout the buttons
        bsizer = wx.StdDialogButtonSizer()
        for button in self._buttons:
            bsizer.AddButton(button)
            bid = button.GetId()
            if bid in (wx.ID_NO, wx.ID_YES):
                if wx.NO_DEFAULT & style:
                    if bid == wx.ID_NO:
                        button.SetDefault()
                else:
                    if bid == wx.ID_YES:
                        button.SetDefault()
            elif bid == wx.ID_OK:
                button.SetDefault()

        bsizer.Realize()

        vsizer.AddMany([((10, 10), 0), (caption, 0), ((20, 20), 0),
                        (self._choices, 1, wx.EXPAND), ((10, 10), 0),
                        (bsizer, 1, wx.EXPAND),
                        ((10, 10), 0)])

        icon_id = wx.ART_INFORMATION
        for i_id, a_id in ((wx.ICON_ERROR, wx.ART_ERROR),
                     (wx.ICON_WARNING, wx.ART_WARNING)):
            if i_id & style:
                icon_id = a_id
                break

        icon = wx.ArtProvider.GetBitmap(icon_id, wx.ART_MESSAGE_BOX, (64, 64))
        self._bmp = wx.StaticBitmap(self, bitmap=icon)
        bmpsz = wx.BoxSizer(wx.VERTICAL)
        bmpsz.AddMany([((10, 10), 0), (self._bmp, 0, wx.ALIGN_CENTER_VERTICAL),
                       ((10, 30), 0, wx.EXPAND)])
        hsizer.AddMany([((10, 10), 0), (bmpsz, 0, wx.ALIGN_TOP),
                        ((10, 10), 0), (vsizer, 1), ((10, 10), 0)])

        self.SetSizer(hsizer)
        self.SetInitialSize()
        self.SetAutoLayout(True)

    def GetChoiceControl(self):
        """Get the dialogs choice control
        @return: wx.Choice

        """
        return self._choices

    @expose(ChoiceDialog)
    def GetSelection(self):
        """Get the chosen index
        @return: int

        """
        return self._selidx

    @expose(ChoiceDialog)
    def GetStringSelection(self):
        """Get the chosen string
        @return: string

        """
        return self._selection

    def OnButton(self, evt):
        """Handle button events
        @param evt: wx.EVT_BUTTON

        """
        self.GetParent().EndModal(evt.GetId())

    def OnChoice(self, evt):
        """Update the selection
        @param evt: wx.EVT_CHOICE

        """
        if evt.GetEventObject() == self._choices:
            self._selection = self._choices.GetStringSelection()
            self._selidx = self._choices.GetSelection()
        else:
            evt.Skip()

    @expose(ChoiceDialog)
    def SetBitmap(self, bmp):
        """Set the dialogs bitmap
        @param bmp: wx.Bitmap

        """
        self._bmp.SetBitmap(bmp)
        self.Layout()

    @expose(ChoiceDialog)
    def SetChoices(self, choices):
        """Set the dialogs choices
        @param choices: list of strings

        """
        self._choices.SetItems(choices)
        self._choices.SetSelection(0)
        self._selection = self._choices.GetStringSelection()

    @expose(ChoiceDialog)
    def SetSelection(self, sel):
        """Set the selected choice
        @param sel: int

        """
        self._choices.SetSelection(sel)
        self._selection = self._choices.GetStringSelection()
        self._selidx = self._choices.GetSelection()

    @expose(ChoiceDialog)
    def SetStringSelection(self, sel):
        """Set the selected choice
        @param sel: string

        """
        self._choices.SetStringSelection(sel)
        self._selection = self._choices.GetStringSelection()
        self._selidx = self._choices.GetSelection()




class EOLFormatDlg(ChoiceDialog):
    """Dialog for selecting EOL format"""
    def __init__(self, parent, msg=u'', title=u'', selection=0):
        """Create the dialog
        @keyword selection: default selection (wx.stc.STC_EOL_*)

        """
        choices = [_("Old Machintosh (\\r)"), _("Unix (\\n)"),
                   _("Windows (\\r\\n)")]
        self._eol = [wx.stc.STC_EOL_CR, wx.stc.STC_EOL_LF, wx.stc.STC_EOL_CRLF]
        idx = self._eol.index(selection)
        super(EOLFormatDlg, self).__init__(parent, msg=msg, title=title,
                                             choices=choices,
                                             style=wx.YES_NO|wx.YES_DEFAULT)
        self.SetSelection(idx)

        # Setup
        ###bmp = wx.ArtProvider.GetBitmap("doc_props.png", wx.ART_OTHER)
        bmp_Path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "doc_props.png")
        bmp = wx.Bitmap(bmp_Path, wx.BITMAP_TYPE_ANY)
        if bmp.IsOk():
            self.SetBitmap(bmp)
        self.CenterOnParent()

    def GetSelection(self):
        """Get the selected eol mode
        @return: wx.stc.STC_EOL_*

        """
        sel = super(EOLFormatDlg, self).GetSelection()
        return self._eol[sel]

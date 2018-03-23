import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 

class ImportFilesDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,proejct,dlg_id,title)
        boxsizer = wx.BoxSizer(wx.VERTICAL)
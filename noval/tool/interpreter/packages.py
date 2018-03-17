import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 
import noval.tool.WxThreadSafe as WxThreadSafe
import wx.dataview as dataview

class PackagePanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer()
        self.dvlc = dataview.DataViewListCtrl(self)
        self.dvlc.AppendTextColumn(_('Name'), width=200)
        self.dvlc.AppendTextColumn(_('Version'),width=250)
        self.Sizer.Add(self.dvlc, 1, wx.EXPAND)
        self.interpreter = None
        
    def LoadPackages(self,interpreter,force=False):
        self.interpreter = interpreter
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
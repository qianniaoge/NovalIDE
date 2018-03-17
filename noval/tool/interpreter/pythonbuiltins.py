import wx

class PythonBuiltinsPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        self.listbox = wx.ListBox(self, -1,style=wx.LB_SINGLE)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.listbox, 1, wx.EXPAND)
        
    def SetBuiltiins(self,interpreter):
        self.listbox.Clear()
        self.listbox.InsertItems(interpreter.Builtins,0)
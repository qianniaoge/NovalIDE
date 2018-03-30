import wx
import os
import sys

class PyShell(wx.py.shell.Shell):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,\
                size=wx.DefaultSize, style=wx.CLIP_CHILDREN,\
                introText='', locals=None, InterpClass=None,\
                startupScript=None, execStartupScript=True,*args, **kwds):
        super(PyShell,self).__init__(parent,id,pos,size,style,introText,locals,InterpClass,startupScript,execStartupScript,*args, **kwds)
        #remove the left gap if python interpreter view
        self.SetMarginWidth(1, 0)
        
    def setBuiltinKeywords(self):
        super(PyShell,self).setBuiltinKeywords()
        os._exit = sys.exit = 'Click on the close button to leave the application.'
        
    def push(self, command, silent = False):
        try:
            super(PyShell,self).push(command,silent)
        except SystemExit as x:
            self.write(str(x))
            self.run("")
            #sys.exit
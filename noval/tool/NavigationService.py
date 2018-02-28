import wx
import Service
import doctools
import os
import noval.util.sysutils as sysutilslib
from wx.lib.pubsub import pub as Publisher

_ = wx.GetTranslation


NOVAL_MSG_UI_STC_POS_JUMPED = 'noval.msg.file.jump'

ID_NEXT_POS = wx.NewId()
ID_PRE_POS = wx.NewId()

#record previous and current caret postion
def jumpaction(func):
    """Decorator method to notify clients about jump actions"""
    def WrapJump(*args, **kwargs):
        """Wrapper for capturing before/after pos of a jump action"""
        try:
            arg = args[0]
            if isinstance(arg,wx.stc.StyledTextCtrl):
                stc = arg
                doc_view = stc._dynSash._view
            else:
                doc_view = arg
                stc = doc_view.GetCtrl()
            pos = stc.GetCurrentPos()
            line = stc.GetCurrentLine()
            func(*args, **kwargs)
            cpos = stc.GetCurrentPos()
            cline = stc.GetCurrentLine()
            fname = doc_view.GetDocument().GetFilename()

            mdata = dict(fname=fname,
                         prepos=pos, preline=line,
                         lnum=cline, pos=cpos)

            wx.CallAfter(Publisher.sendMessage,NOVAL_MSG_UI_STC_POS_JUMPED,msg=mdata) 
        except wx.PyDeadObjectError:
            pass

    WrapJump.__name__ = func.__name__
    WrapJump.__doc__ = func.__doc__
    return WrapJump

#only record current caret postion
def jumpto(func):
    """Decorator method to notify clients about jump actions"""
    def WrapJumpto(*args, **kwargs):
        """Wrapper for capturing before/after pos of a jump action"""
        try:
            arg = args[0]
            if isinstance(arg,wx.stc.StyledTextCtrl):
                stc = arg
                doc_view = stc._dynSash._view
            else:
                doc_view = arg
                stc = doc_view.GetCtrl()
            func(*args, **kwargs)
            cpos = stc.GetCurrentPos()
            cline = stc.GetCurrentLine()
            fname = doc_view.GetDocument().GetFilename()
            mdata = dict(fname=fname,lnum=cline, pos=cpos)
            wx.CallAfter(Publisher.sendMessage,NOVAL_MSG_UI_STC_POS_JUMPED,msg=mdata) 
        except wx.PyDeadObjectError:
            pass

    WrapJumpto.__name__ = func.__name__
    WrapJumpto.__doc__ = func.__doc__
    return WrapJumpto
class NavigationService(Service.BaseService):

    DocMgr = doctools.DocPositionMgr()

    def __init__(self):
        pass
        
    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != STCTextEditor.TextDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
        
        viewMenu.AppendSeparator()
        viewMenu.Append(ID_NEXT_POS, _("Next Position"), _("Goto next position in history."))
        viewMenu.Append(ID_PRE_POS, _("Previous Position"), _("Goto previous position in history."))
        wx.EVT_MENU(frame, ID_NEXT_POS, frame.ProcessEvent)
        wx.EVT_MENU(frame, ID_PRE_POS, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ID_NEXT_POS, frame.ProcessUpdateUIEvent)
        wx.EVT_UPDATE_UI(frame, ID_PRE_POS, frame.ProcessUpdateUIEvent)

        forward_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "forward.png")
        forward_bmp = wx.Bitmap(forward_bmp_path, wx.BITMAP_TYPE_PNG)
        backward_bmp_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "backward.png")
        backward_bmp = wx.Bitmap(backward_bmp_path, wx.BITMAP_TYPE_PNG)
        toolBar.AddTool(ID_PRE_POS, backward_bmp, shortHelpString = _("Previous Position"), longHelpString = _("Goto previous position in history."))
        toolBar.AddTool(ID_NEXT_POS, forward_bmp, shortHelpString = _("Next Position"), longHelpString = _("Goto next position in history."))
      
    def ProcessEvent(self, event):
        return self.OnNavigateToPos(event)

    def ProcessUpdateUIEvent(self, event):
        return self.OnUpdateNaviUI(event)

    def OnNavigateToPos(self, evt):
        """Handle buffer position history navigation events"""
        e_id = evt.GetId()
        fname, pos = (None, None)
        text_view = self.GetActiveView()
        if text_view is None:
            return False
        cname = text_view.GetDocument().GetFilename()
        cpos = text_view.GetCtrl().GetCurrentPos()
        #when go to next position,current cache pos is current caret pos
        if e_id == ID_NEXT_POS:
            if self.DocMgr.CanNavigateNext():
                fname, pos = self.DocMgr.GetNextNaviPos()
                if (fname, pos) == (cname, cpos):
                    fname, pos = (None, None)
                    tmp = self.DocMgr.GetNextNaviPos()
                    if tmp is not None:
                        fname, pos = tmp
        #while go to previous position,current cache pos is previous caret pos
        elif e_id == ID_PRE_POS:
            if self.DocMgr.CanNavigatePrev():
                fname, pos = self.DocMgr.GetPreviousNaviPos()
                if (fname, pos) == (cname, cpos):
                    fname, pos = (None, None)
                    tmp = self.DocMgr.GetPreviousNaviPos()
                    if tmp is not None:
                        fname, pos = tmp
        else:
            return False
        if fname is not None:
            wx.GetApp().GotoView(fname,-1,pos=pos)
        return True

    def OnUpdateNaviUI(self, evt):
        """UpdateUI handler for position navigator"""
        e_id = evt.Id
        if e_id == ID_NEXT_POS:
            evt.Enable(self.DocMgr.CanNavigateNext())
            return True
        elif e_id == ID_PRE_POS:
            evt.Enable(self.DocMgr.CanNavigatePrev())
            return True
        else:
            return False


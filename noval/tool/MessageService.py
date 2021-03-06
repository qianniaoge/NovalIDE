#----------------------------------------------------------------------------
# Name:         MessageService.py
# Purpose:      Message View Service for pydocview
#
# Author:       Morgan Hua
#
# Created:      9/2/04
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import Service
import STCTextEditor
import WxThreadSafe

#----------------------------------------------------------------------------
# Utility
#----------------------------------------------------------------------------

def ClearMessages():
    messageService = wx.GetApp().GetService(MessageService)
    view = messageService.GetView()
    if view:
        view.ClearLines()


def ShowMessages(messages, clear=False):
    if ((messages != None) and (len(messages) > 0)):
        messageService = wx.GetApp().GetService(MessageService)
        messageService.ShowWindow(True)
        view = messageService.GetView()
        if view:
            if (clear):
                view.ClearLines()
            for message in messages:
                view.AddLines(message)
                view.AddLines("\n")


#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------


class MessageView(Service.ServiceView):
    """ Reusable Message View for any document.
        When an item is selected, the document view is called back (with DoSelectCallback) to highlight and display the corresponding item in the document view.
    """

    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def _CreateControl(self, parent, id):
        txtCtrl = STCTextEditor.TextCtrl(parent, id, bind_left_up_event = False)
        txtCtrl.SetMarginWidth(1, 0)  # hide line numbers
        txtCtrl.SetReadOnly(True)
        txtCtrl.SetEdgeMode(wx.stc.STC_EDGE_NONE)

        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        txtCtrl.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font))
        txtCtrl.SetFontColor(wx.BLACK)
        txtCtrl.StyleClearAll()
        txtCtrl.UpdateStyles()
        wx.EVT_SET_FOCUS(txtCtrl, self.OnFocus)
        #fix the bug when double click the file line and show messagebox which cause wxEVT_MOUSE_CAPTURE_LOST problem
        wx.EVT_MOUSE_CAPTURE_LOST(txtCtrl,self.OnMouseCaptureLost)
        return txtCtrl
        
    def OnMouseCaptureLost(self,event):
        pass

    def GetDocument(self):
        return None

    def OnFocus(self, event):
        wx.GetApp().GetDocumentManager().ActivateView(self)
        event.Skip()

    def ProcessEvent(self, event):
        stcControl = self.GetControl()
        if not isinstance(stcControl, wx.stc.StyledTextCtrl):
            return wx.lib.docview.View.ProcessEvent(self, event)
        id = event.GetId()
        if id == wx.ID_COPY:
            stcControl.Copy()
            return True
        elif id == wx.ID_CLEAR:
            stcControl.Clear()
            return True
        elif id == wx.ID_SELECTALL:
            stcControl.SetSelection(0, -1)
            return True


    def ProcessUpdateUIEvent(self, event):
        stcControl = self.GetControl()
        if not isinstance(stcControl, wx.stc.StyledTextCtrl):
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)
        id = event.GetId()
        if id == wx.ID_CUT or id == wx.ID_PASTE:
            # I don't think cut or paste makes sense from a message/log window.
            event.Enable(False)
            return True
        elif id == wx.ID_COPY:
            event.Enable(stcControl.HasSelection())
            return True
        elif id == wx.ID_CLEAR:
            event.Enable(True)  # wxBug: should be stcControl.CanCut()) but disabling clear item means del key doesn't work in control as expected
            return True
        elif id == wx.ID_SELECTALL:
            event.Enable(stcControl.GetTextLength() > 0)
            return True

        
    #----------------------------------------------------------------------------
    # Service specific methods
    #----------------------------------------------------------------------------

    def ClearLines(self):
        self.GetControl().SetReadOnly(False)
        self.GetControl().ClearAll()
        self.GetControl().SetReadOnly(True)

    @WxThreadSafe.call_after
    def AddLines(self, text):
        self.GetControl().SetCurrentPos(self.GetControl().GetTextLength())
        self.GetControl().SetReadOnly(False)
        self.GetControl().AddText(text)
        self.GetControl().SetReadOnly(True)


    def GetText(self):
        return self.GetControl().GetText()


    def GetCurrentPos(self):
        return self.GetControl().GetCurrentPos()


    def GetCurrLine(self):
        return self.GetControl().GetCurLine()
        
    def GetCurrentLine(self):
        return self.GetControl().GetCurrentLine()

    #----------------------------------------------------------------------------
    # Callback Methods
    #----------------------------------------------------------------------------

    def SetCallback(self, callback):
        """ Sets in the event table for a doubleclick to invoke the given callback.
            Additional calls to this method overwrites the previous entry and only the last set callback will be invoked.
        """
        wx.stc.EVT_STC_DOUBLECLICK(self.GetControl(), self.GetControl().GetId(), callback)



class MessageService(Service.Service):


    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    SHOW_WINDOW = wx.NewId()  # keep this line for each subclass, need unique ID for each Service


    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def _CreateView(self):
        return MessageView(self)

    def GetIconIndex(self):
        return Service.ServiceView.SearchIconIndex

#----------------------------------------------------------------------------
# Name:         CompletionService.py
# Purpose:      Adding and removing line markers in text for easy searching
#
# Author:       Morgan Hua
#
# Created:      10/6/03
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.stc
import wx.lib.docview
import wx.lib.pydocview
import STCTextEditor
_ = wx.GetTranslation


class CompletionService(wx.lib.pydocview.DocService):
    GO_TO_DEFINITION = wx.NewId()
    COMPLETE_WORD_LIST = wx.NewId()
    AUTO_COMPLETE_WORD = wx.NewId()
    LIST_CURRENT_MEMBERS = wx.NewId()
    GOTODEF_MENU_ITEM_TEXT = "Goto Definition"


    def __init__(self):
        pass

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != STCTextEditor.TextDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        editMenu.AppendSeparator()
        editMenu.Append(CompletionService.GO_TO_DEFINITION, _("Goto Definition\tF12"), _("Goto Definition of text"))
        wx.EVT_MENU(frame, CompletionService.GO_TO_DEFINITION, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.GO_TO_DEFINITION, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.COMPLETE_WORD_LIST, _("Completion Word List\tCtrl+Shit+K"), _("List Completion Word List"))
        wx.EVT_MENU(frame, CompletionService.COMPLETE_WORD_LIST, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.COMPLETE_WORD_LIST, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.AUTO_COMPLETE_WORD, _("Auto Complete Word\tCtrl+K"), _("Auto Complete the correct Word"))
        wx.EVT_MENU(frame, CompletionService.AUTO_COMPLETE_WORD, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.AUTO_COMPLETE_WORD, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.LIST_CURRENT_MEMBERS, _("List Members\tCtrl+J"), _("List Members In Current Scope"))
        wx.EVT_MENU(frame, CompletionService.LIST_CURRENT_MEMBERS, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.LIST_CURRENT_MEMBERS, frame.ProcessUpdateUIEvent)

    def ProcessEvent(self, event):
        id = event.GetId()
        if id == CompletionService.GO_TO_DEFINITION:
            return True
        elif id == CompletionService.COMPLETE_WORD_LIST:
            return True
        elif id == CompletionService.AUTO_COMPLETE_WORD:
            return True
        elif id == CompletionService.LIST_CURRENT_MEMBERS:
            return True
        else:
            return False


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == CompletionService.GO_TO_DEFINITION:
            return True
        elif id == CompletionService.COMPLETE_WORD_LIST:
            return True
        elif id == CompletionService.AUTO_COMPLETE_WORD:
            return True
        elif id == CompletionService.LIST_CURRENT_MEMBERS:
            return True
        else:
            return False


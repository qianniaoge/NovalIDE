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
import Service
_ = wx.GetTranslation

SPACE = 10
HALF_SPACE = 5

class MutipleDefinitionDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title,definitions):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        self.listbox = wx.ListBox(self, -1, style=wx.LB_SINGLE)
        contentSizer.Add(self.listbox, 1, wx.EXPAND|wx.BOTTOM,SPACE)
        self.Bind(wx.EVT_LISTBOX, self.OnListBoxSelect, self.listbox)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        lineSizer.Add(ok_btn, 0, wx.LEFT, SPACE*22)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        lineSizer.Add(cancel_btn, 0, wx.LEFT, SPACE)

        contentSizer.Add(lineSizer, 0, wx.BOTTOM|wx.RIGHT, SPACE)
        self.SetSizer(contentSizer)

    def AppendDefinitions(self,definitions):
        for i,definition in enumerate(definitions):
            itemsting = "%s(%d:%d)" % (definition.Path,definition.Line,definition.Col)
            self.listbox.Insert(itemsting, i)
            self.listbox.SetClientData(i, definition)

    def OnListBoxSelect(self, event=None):
        i = self.listbox.GetSelection()
        definition = self.listbox.GetClientData(i)
        wx.GetApp().GotoView(definition.Path,definition.Line)

class CompletionService(Service.BaseService):
    GO_TO_DEFINITION = wx.NewId()
    COMPLETE_WORD_LIST = wx.NewId()
    AUTO_COMPLETE_ID = wx.NewId()
    LIST_CURRENT_MEMBERS = wx.NewId()

    def __init__(self):
        pass

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != STCTextEditor.TextDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        editMenu.AppendSeparator()
        editMenu.Append(CompletionService.GO_TO_DEFINITION, _("Goto Definition\tF12"), _("Goto Definition of current statement"))
        wx.EVT_MENU(frame, CompletionService.GO_TO_DEFINITION, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.GO_TO_DEFINITION, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.COMPLETE_WORD_LIST, _("Completion Word List\tCtrl+Shit+K"), _("List All Completion Word of suggestions"))
        wx.EVT_MENU(frame, CompletionService.COMPLETE_WORD_LIST, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.COMPLETE_WORD_LIST, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.AUTO_COMPLETE_ID, _("&Auto Complete\tCtrl+Shift+Space"), _("Provides suggestions on how to complete the current statement"))
        wx.EVT_MENU(frame, CompletionService.AUTO_COMPLETE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.AUTO_COMPLETE_ID, frame.ProcessUpdateUIEvent)
        editMenu.Append(CompletionService.LIST_CURRENT_MEMBERS, _("List Members\tCtrl+J"), _("List Members of Current statement"))
        wx.EVT_MENU(frame, CompletionService.LIST_CURRENT_MEMBERS, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CompletionService.LIST_CURRENT_MEMBERS, frame.ProcessUpdateUIEvent)

    def ProcessEvent(self, event):
        text_view = self.GetActiveView()
        id = event.GetId()
        if id == CompletionService.GO_TO_DEFINITION:
            text_view.GetCtrl().GotoDefinition()
            return True
        elif id == CompletionService.COMPLETE_WORD_LIST:
            return True
        elif id == CompletionService.AUTO_COMPLETE_ID:
            text_view.OnAutoComplete()
            return True
        elif id == CompletionService.LIST_CURRENT_MEMBERS:
            text_view.GetCtrl().ListMembers(text_view.GetCtrl().GetCurrentPos()-1)
            return True
        else:
            return False

    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == CompletionService.GO_TO_DEFINITION or id == CompletionService.COMPLETE_WORD_LIST\
                or id == CompletionService.AUTO_COMPLETE_ID or id == CompletionService.LIST_CURRENT_MEMBERS:
            event.Enable(False)
            return True
        else:
            return False


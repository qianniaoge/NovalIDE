import wx
import wx.lib.pydocview
import Service
import noval.parser.config as parserconfig
import datetime
import getpass
import os
import noval.util.strutils as strutils
import noval.util.sysutils as sysutilslib
_ = wx.GetTranslation

#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------

TEXT_ID = wx.NewId()
VIEW_WHITESPACE_ID = wx.NewId()
VIEW_EOL_ID = wx.NewId()
VIEW_INDENTATION_GUIDES_ID = wx.NewId()
VIEW_RIGHT_EDGE_ID = wx.NewId()
VIEW_LINE_NUMBERS_ID = wx.NewId()
ZOOM_ID = wx.NewId()
ZOOM_NORMAL_ID = wx.NewId()
ZOOM_IN_ID = wx.NewId()
ZOOM_OUT_ID = wx.NewId()
CHOOSE_FONT_ID = wx.NewId()
WORD_WRAP_ID = wx.NewId()
TEXT_STATUS_BAR_ID = wx.NewId()
ADVANCE_EDIT_ID = wx.NewId()
INSERT_TEXT_ID = wx.NewId()
CONVERT_TO_UPPERCASE_ID = wx.NewId()
CONVERT_TO_LOWER_ID = wx.NewId()
INSERT_DATETIME_ID = wx.NewId()
INSERT_COMMENT_TEMPLATE_ID = wx.NewId()
INSERT_FILE_CONTENT_ID = wx.NewId()
INSERT_DECLARE_ENCODING_ID = wx.NewId()
ID_TAB_TO_SPACE =  wx.NewId()
ID_SPACE_TO_TAB =  wx.NewId()

PYTHON_COMMENT_TEMPLATE = '''#-------------------------------------------------------------------------------
# Name:        {File}
# Purpose:
#
# Author:      {Author}
#
# Created:     {Date}
# Copyright:   (c) {Author} {Year}
# Licence:     <your licence>
#-------------------------------------------------------------------------------
'''

SPACE = 10
HALF_SPACE = 5
class EncodingDeclareDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title,size=(-1,150))
        contentSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.name_ctrl = wx.TextCtrl(self, -1, "# -*- coding: utf-8 -*-",size=(100,-1))
        self.name_ctrl.Enable(False)
        contentSizer.Add(self.name_ctrl, 0, wx.BOTTOM|wx.LEFT|wx.EXPAND , SPACE)
        self.check_box = wx.CheckBox(self, -1,_("Edit"))
        self.Bind(wx.EVT_CHECKBOX,self.onChecked) 
        contentSizer.Add(self.check_box, 0, wx.BOTTOM|wx.LEFT, SPACE)
        
        bsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, _("&Insert"))
        ok_btn.SetDefault()
        bsizer.AddButton(ok_btn)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        bsizer.AddButton(cancel_btn)
        bsizer.Realize()
        contentSizer.Add(bsizer, 1, wx.EXPAND,SPACE)
        self.SetSizer(contentSizer)

    def onChecked(self,event):
        self.name_ctrl.Enable(event.GetEventObject().GetValue())

class TextStatusBar(wx.StatusBar):

    TEXT_MODE_PANEL = 1
    DOCUMENT_ENCODING_PANEL = 2
    LINE_NUMBER_PANEL = 3
    COLUMN_NUMBER_PANEL = 4

    # wxBug: Would be nice to show num key status in statusbar, but can't figure out how to detect if it is enabled or disabled
    def __init__(self, parent, id, style = wx.ST_SIZEGRIP, name = "statusBar"):
        wx.StatusBar.__init__(self, parent, id, style, name)
        self.SetFieldsCount(5)
        self.SetStatusWidths([-1, 50, 80,50, 55])
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnStatusBarLeftDclick) 
        
    def SetDocumentEncoding(self,encoding):
        self.SetStatusText(encoding.upper(), TextStatusBar.DOCUMENT_ENCODING_PANEL)

    def SetInsertMode(self, insert = True):
        if insert:
            newText = _("Ins")
        else:
            newText = _("Over")
        if self.GetStatusText(TextStatusBar.TEXT_MODE_PANEL) != newText:     # wxBug: Need to check if the text has changed, otherwise it flickers under win32
            self.SetStatusText(newText, TextStatusBar.TEXT_MODE_PANEL)

    def SetLineNumber(self, lineNumber):
        newText = _("Ln %i") % lineNumber
        if self.GetStatusText(TextStatusBar.LINE_NUMBER_PANEL) != newText:
            self.SetStatusText(newText, TextStatusBar.LINE_NUMBER_PANEL)

    def SetColumnNumber(self, colNumber):
        newText = _("Col %i") % colNumber
        if self.GetStatusText(TextStatusBar.COLUMN_NUMBER_PANEL) != newText:
            self.SetStatusText(newText, TextStatusBar.COLUMN_NUMBER_PANEL)
            
    def OnStatusBarLeftDclick(self,event):
        panel = self.GetPaneAtPosition(event.GetPosition())
        if panel < 0:
            return
        view = wx.GetApp().GetDocumentManager().GetCurrentView()
        if not view or not hasattr(view,"OnGotoLine"):
            return

        if panel == TextStatusBar.TEXT_MODE_PANEL:
            if view.GetCtrl().GetOvertype():
                self.SetInsertMode(True)
                view.GetCtrl().SetOvertype(False)
            else:
                self.SetInsertMode(False)
                view.GetCtrl().SetOvertype(True)
        elif panel == TextStatusBar.LINE_NUMBER_PANEL or \
             panel == TextStatusBar.COLUMN_NUMBER_PANEL:
            view.OnGotoLine(None)
 
    def GetPaneAtPosition(self,point):
        for i in range(self.GetFieldsCount()):
            rect = self.GetFieldRect(i)
            if rect.Contains(point):
                return i
        return -1
        
    def Reset(self):
        self.SetStatusText("", 0)
        self.SetStatusText("", TextStatusBar.TEXT_MODE_PANEL)
        self.SetStatusText("", TextStatusBar.DOCUMENT_ENCODING_PANEL)
        self.SetStatusText("", TextStatusBar.LINE_NUMBER_PANEL)
        self.SetStatusText("", TextStatusBar.COLUMN_NUMBER_PANEL)
        

class TextService(Service.BaseService):

    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        if document and document.GetDocumentTemplate().GetDocumentType() != TextDocument:
            return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        statusBar = TextStatusBar(frame, TEXT_STATUS_BAR_ID)
        frame.SetStatusBar(statusBar)
        wx.EVT_UPDATE_UI(frame, TEXT_STATUS_BAR_ID, frame.ProcessUpdateUIEvent)

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))

        viewMenu.AppendSeparator()
        textMenu = wx.Menu()
        textMenu.AppendCheckItem(VIEW_WHITESPACE_ID, _("&View Whitespace"), _("Shows or hides whitespace"))
        wx.EVT_MENU(frame, VIEW_WHITESPACE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_WHITESPACE_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_EOL_ID, _("&View End of Line Markers"), _("Shows or hides indicators at the end of each line"))
        wx.EVT_MENU(frame, VIEW_EOL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_EOL_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_INDENTATION_GUIDES_ID, _("&View Indentation Guides"), _("Shows or hides indentations"))
        wx.EVT_MENU(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_RIGHT_EDGE_ID, _("&View Right Edge"), _("Shows or hides the right edge marker"))
        wx.EVT_MENU(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_LINE_NUMBERS_ID, _("&View Line Numbers"), _("Shows or hides the line numbers"))
        wx.EVT_MENU(frame, VIEW_LINE_NUMBERS_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_LINE_NUMBERS_ID, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendMenu(TEXT_ID, _("&Text"), textMenu)
        wx.EVT_UPDATE_UI(frame, TEXT_ID, frame.ProcessUpdateUIEvent)
        
        isWindows = (wx.Platform == '__WXMSW__')

        zoomMenu = wx.Menu()
        zoomMenu.Append(ZOOM_NORMAL_ID, _("Normal Size"), _("Sets the document to its normal size"))
        wx.EVT_MENU(frame, ZOOM_NORMAL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_NORMAL_ID, frame.ProcessUpdateUIEvent)
        if isWindows:
            item = wx.MenuItem(zoomMenu,ZOOM_IN_ID, _("Zoom In\tCtrl+Page Up"), _("Zooms the document to a larger size"))
        else:
            item = wx.MenuItem(zoomMenu,ZOOM_IN_ID, _("Zoom In"), _("Zooms the document to a larger size"))
        item.SetBitmap(getZoomInBitmap())
        zoomMenu.AppendItem(item)
        wx.EVT_MENU(frame, ZOOM_IN_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_IN_ID, frame.ProcessUpdateUIEvent)
        if isWindows:
            item = wx.MenuItem(zoomMenu,ZOOM_OUT_ID, _("Zoom Out\tCtrl+Page Down"), _("Zooms the document to a smaller size"))
        else:
            item = wx.MenuItem(zoomMenu,ZOOM_OUT_ID, _("Zoom Out"), _("Zooms the document to a smaller size"))
        item.SetBitmap(getZoomOutBitmap())
        zoomMenu.AppendItem(item)
        wx.EVT_MENU(frame, ZOOM_OUT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_OUT_ID, frame.ProcessUpdateUIEvent)
        
        viewMenu.AppendMenu(ZOOM_ID, _("&Zoom"), zoomMenu)
        wx.EVT_UPDATE_UI(frame, ZOOM_ID, frame.ProcessUpdateUIEvent)

        formatMenuIndex = menuBar.FindMenu(_("&Format"))
        if formatMenuIndex > -1:
            formatMenu = menuBar.GetMenu(formatMenuIndex)
        else:
            formatMenu = wx.Menu()
        if not menuBar.FindItemById(CHOOSE_FONT_ID):
            formatMenu.Append(CHOOSE_FONT_ID, _("&Font..."), _("Sets the font to use"))
            wx.EVT_MENU(frame, CHOOSE_FONT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, CHOOSE_FONT_ID, frame.ProcessUpdateUIEvent)
        if not menuBar.FindItemById(WORD_WRAP_ID):
            formatMenu.AppendCheckItem(WORD_WRAP_ID, _("Word Wrap"), _("Wraps text horizontally when checked"))
            wx.EVT_MENU(frame, WORD_WRAP_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, WORD_WRAP_ID, frame.ProcessUpdateUIEvent)
        if formatMenuIndex == -1:
            viewMenuIndex = menuBar.FindMenu(_("&View"))
            menuBar.Insert(viewMenuIndex + 1, formatMenu, _("&Format"))

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))

        insertMenu = wx.Menu()
        insertMenu.Append(INSERT_DATETIME_ID, _("Insert Datetime"), _("Insert Datetime to Current Document"))
        wx.EVT_MENU(frame, INSERT_DATETIME_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, INSERT_DATETIME_ID, frame.ProcessUpdateUIEvent)
        insertMenu.Append(INSERT_COMMENT_TEMPLATE_ID, _("Insert Comment Template"), _("Insert Comment Template to Current Document"))
        wx.EVT_MENU(frame, INSERT_COMMENT_TEMPLATE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, INSERT_COMMENT_TEMPLATE_ID, frame.ProcessUpdateUIEvent)

        insertMenu.Append(INSERT_FILE_CONTENT_ID, _("Insert File Content"), _("Insert File Content to Current Document"))
        wx.EVT_MENU(frame, INSERT_FILE_CONTENT_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, INSERT_FILE_CONTENT_ID, frame.ProcessUpdateUIEvent)

        insertMenu.Append(INSERT_DECLARE_ENCODING_ID, _("Insert Encoding Declare"), _("Insert Encoding Declare to Current Document"))
        wx.EVT_MENU(frame, INSERT_DECLARE_ENCODING_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, INSERT_DECLARE_ENCODING_ID, frame.ProcessUpdateUIEvent)
        editMenu.AppendMenu(INSERT_TEXT_ID, _("&Insert"), insertMenu)
        wx.EVT_UPDATE_UI(frame, INSERT_TEXT_ID, frame.ProcessUpdateUIEvent)

        advanceMenu = wx.Menu()
        item = wx.MenuItem(advanceMenu,CONVERT_TO_UPPERCASE_ID, _("Conert To UPPERCASE\tCtrl+Shift+U"), _("Convert Upper Word to Lower Word"))
        uppercase_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "uppercase.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(uppercase_image_path,wx.BITMAP_TYPE_ANY)))
        advanceMenu.AppendItem(item)
            
        wx.EVT_MENU(frame, CONVERT_TO_UPPERCASE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CONVERT_TO_UPPERCASE_ID, frame.ProcessUpdateUIEvent)
        item = wx.MenuItem(advanceMenu,CONVERT_TO_LOWER_ID, _("Conert To lowercase\tCtrl+U"), _("Convert Lower Word to Upper Word"))
        lowercase_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "lowercase.png")
        item.SetBitmap(wx.BitmapFromImage(wx.Image(lowercase_image_path,wx.BITMAP_TYPE_ANY)))
        advanceMenu.AppendItem(item)
        
        wx.EVT_MENU(frame, CONVERT_TO_LOWER_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CONVERT_TO_LOWER_ID, frame.ProcessUpdateUIEvent)

        advanceMenu.Append(ID_TAB_TO_SPACE, _("Tabs To Spaces"), _("Convert tabs to spaces in selected/all text"))
        wx.EVT_MENU(frame, ID_TAB_TO_SPACE, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ID_TAB_TO_SPACE, frame.ProcessUpdateUIEvent)
        advanceMenu.Append(ID_SPACE_TO_TAB, _("Spaces To Tabs"), _("Convert spaces to tabs in selected/all text"))
        wx.EVT_MENU(frame, ID_SPACE_TO_TAB, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ID_SPACE_TO_TAB, frame.ProcessUpdateUIEvent)

        editMenu.AppendMenu(ADVANCE_EDIT_ID, _("&Advance"), advanceMenu)
        wx.EVT_UPDATE_UI(frame, ADVANCE_EDIT_ID, frame.ProcessUpdateUIEvent)

        # wxBug: wxToolBar::GetToolPos doesn't exist, need it to find cut tool and then insert find in front of it.
        toolBar.AddSeparator()
        toolBar.AddTool(ZOOM_IN_ID, getZoomInBitmap(), shortHelpString = _("Zoom In"), longHelpString = _("Zooms the document to a larger size"))
        toolBar.AddTool(ZOOM_OUT_ID, getZoomOutBitmap(), shortHelpString = _("Zoom Out"), longHelpString = _("Zooms the document to a smaller size"))
        toolBar.Realize()

    def ProcessEvent(self, event):
        id = event.GetId()
        text_view = self.GetActiveView()
        if id == CONVERT_TO_UPPERCASE_ID:
            text_view.GetCtrl().UpperCase()
            return True
        elif id == CONVERT_TO_LOWER_ID:
            text_view.GetCtrl().LowerCase()
            return True
        elif id == INSERT_DATETIME_ID:
            text_view.AddText(str(datetime.datetime.now().date()))
            return True
        elif id == INSERT_COMMENT_TEMPLATE_ID:
            file_name = os.path.basename(text_view.GetDocument().GetFilename())
            now_time = datetime.datetime.now()
            comment_template = PYTHON_COMMENT_TEMPLATE.format(File=file_name,Author=getpass.getuser(),Date=now_time.date(),Year=now_time.date().year)
            text_view.GetCtrl().GotoPos(0)
            text_view.AddText(comment_template)
            return True
        elif id == INSERT_FILE_CONTENT_ID:
            dlg = wx.FileDialog(wx.GetApp().GetTopWindow(),_("Select File Path"),
                                wildcard="All|*.*",style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                with open(path) as f:
                    text_view.AddText(f.read())
            return True
        elif id == INSERT_DECLARE_ENCODING_ID:
            lines = text_view.GetTopLines(3)
            coding_name,line_num = strutils.get_python_coding_declare(lines)
            if  coding_name is not None:
                ret = wx.MessageBox(_("The Python Document have already declare coding,Do you want to overwrite it?"),_("Declare Encoding"),wx.YES_NO|wx.ICON_QUESTION,\
                    text_view.GetFrame())
                if ret == wx.YES:
                    text_view.GetCtrl().SetSelection(text_view.GetCtrl().PositionFromLine(line_num),text_view.GetCtrl().PositionFromLine(line_num+1))
                    text_view.GetCtrl().DeleteBack()
                else:
                    return True
            dlg = EncodingDeclareDialog(wx.GetApp().GetTopWindow(),-1,_("Declare Encoding"))
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                text_view.GetCtrl().GotoPos(0)
                text_view.AddText(dlg.name_ctrl.GetValue() + "\n")
            return True
        elif id == ID_TAB_TO_SPACE or id == ID_SPACE_TO_TAB:
            self.ConvertWhitespace(text_view,id)
        else:
            return False

    def ProcessUpdateUIEvent(self, event):
        text_view = self.GetActiveView()
      #  if text_view is None:
       #     event.Enable(False)
        #    return True
        id = event.GetId()
        if (id == TEXT_ID
        or id == VIEW_WHITESPACE_ID
        or id == VIEW_EOL_ID
        or id == VIEW_INDENTATION_GUIDES_ID
        or id == VIEW_RIGHT_EDGE_ID
        or id == VIEW_LINE_NUMBERS_ID
        or id == ZOOM_ID
        or id == ZOOM_NORMAL_ID
        or id == ZOOM_IN_ID
        or id == ZOOM_OUT_ID
        or id == CHOOSE_FONT_ID
        or id == WORD_WRAP_ID
        or id == INSERT_TEXT_ID
        or id == ADVANCE_EDIT_ID):
            event.Enable(False)
            return True
        elif id == CONVERT_TO_UPPERCASE_ID \
                or id == CONVERT_TO_LOWER_ID:
            event.Enable(text_view is not None and text_view.HasSelection())
            return True
        elif id == INSERT_COMMENT_TEMPLATE_ID \
                or id == INSERT_DECLARE_ENCODING_ID:
            event.Enable(text_view is not None and text_view.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER )
            return True
        else:
            return False


    def ConvertWhitespace(self, text_view,mode_id):
        """Convert whitespace from using tabs to spaces or visa versa
        @param mode_id: id of conversion mode

        """
        if mode_id not in (ID_TAB_TO_SPACE, ID_SPACE_TO_TAB):
            return

        text_ctrl = text_view.GetCtrl()
        tabw = text_ctrl.GetIndent()
        pos = text_ctrl.GetCurrentPos()
        sel = text_ctrl.GetSelectedText()
        if mode_id == ID_TAB_TO_SPACE:
            cmd = (u"\t", u" " * tabw)
            tabs = False
        else:
            cmd = (" " * tabw, u"\t")
            tabs = True

        if sel != wx.EmptyString:
            text_ctrl.ReplaceSelection(sel.replace(cmd[0], cmd[1]))
        else:
            text_ctrl.BeginUndoAction()
            part1 = text_ctrl.GetTextRange(0, pos).replace(cmd[0], cmd[1])
            tmptxt = text_ctrl.GetTextRange(pos, text_ctrl.GetLength()).replace(cmd[0], \
                                                                      cmd[1])
            text_ctrl.SetText(part1 + tmptxt)
            text_ctrl.GotoPos(len(part1))
            text_ctrl.SetUseTabs(tabs)
            text_ctrl.EndUndoAction()

from wx import ImageFromStream, BitmapFromImage
import cStringIO
#----------------------------------------------------------------------------
# Menu Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
#----------------------------------------------------------------------
def getZoomInBitmap():
    zoomin_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source","toolbar","zoomin.png")
    zoomin_image = wx.Image(zoomin_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(zoomin_image)

#----------------------------------------------------------------------

def getZoomOutBitmap():
    zoomout_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source","toolbar","zoomout.png")
    zoomout_image = wx.Image(zoomout_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(zoomout_image)

    return ImageFromStream(stream)

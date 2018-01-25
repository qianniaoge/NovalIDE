import wx
import wx.lib.pydocview
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

class TextStatusBar(wx.StatusBar):

    TEXT_MODE_PANEL = 1
    LINE_NUMBER_PANEL = 2
    COLUMN_NUMBER_PANEL = 3

    # wxBug: Would be nice to show num key status in statusbar, but can't figure out how to detect if it is enabled or disabled
    def __init__(self, parent, id, style = wx.ST_SIZEGRIP, name = "statusBar"):
        wx.StatusBar.__init__(self, parent, id, style, name)
        self.SetFieldsCount(4)
        self.SetStatusWidths([-1, 50, 50, 55])
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnStatusBarLeftDclick) 

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

class TextService(wx.lib.pydocview.DocService):

    def __init__(self):
        wx.lib.pydocview.DocService.__init__(self)

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
        textMenu.AppendCheckItem(VIEW_WHITESPACE_ID, _("&Whitespace"), _("Shows or hides whitespace"))
        wx.EVT_MENU(frame, VIEW_WHITESPACE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_WHITESPACE_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_EOL_ID, _("&End of Line Markers"), _("Shows or hides indicators at the end of each line"))
        wx.EVT_MENU(frame, VIEW_EOL_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_EOL_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_INDENTATION_GUIDES_ID, _("&Indentation Guides"), _("Shows or hides indentations"))
        wx.EVT_MENU(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_INDENTATION_GUIDES_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_RIGHT_EDGE_ID, _("&Right Edge"), _("Shows or hides the right edge marker"))
        wx.EVT_MENU(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, VIEW_RIGHT_EDGE_ID, frame.ProcessUpdateUIEvent)
        textMenu.AppendCheckItem(VIEW_LINE_NUMBERS_ID, _("&Line Numbers"), _("Shows or hides the line numbers"))
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
            zoomMenu.Append(ZOOM_IN_ID, _("Zoom In\tCtrl+Page Up"), _("Zooms the document to a larger size"))
        else:
            zoomMenu.Append(ZOOM_IN_ID, _("Zoom In"), _("Zooms the document to a larger size"))
        wx.EVT_MENU(frame, ZOOM_IN_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, ZOOM_IN_ID, frame.ProcessUpdateUIEvent)
        if isWindows:
            zoomMenu.Append(ZOOM_OUT_ID, _("Zoom Out\tCtrl+Page Down"), _("Zooms the document to a smaller size"))
        else:
            zoomMenu.Append(ZOOM_OUT_ID, _("Zoom Out"), _("Zooms the document to a smaller size"))
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
        advanceMenu.Append(CONVERT_TO_UPPERCASE_ID, _("Conert To UPPERCASE\tCtrl+Shift+U"), _("Convert Upper Word to Lower Word"))
        wx.EVT_MENU(frame, CONVERT_TO_UPPERCASE_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CONVERT_TO_UPPERCASE_ID, frame.ProcessUpdateUIEvent)
        advanceMenu.Append(CONVERT_TO_LOWER_ID, _("Conert To lowercase\tCtrl+U"), _("Convert Lower Word to Upper Word"))
        wx.EVT_MENU(frame, CONVERT_TO_LOWER_ID, frame.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, CONVERT_TO_LOWER_ID, frame.ProcessUpdateUIEvent)
        editMenu.AppendMenu(ADVANCE_EDIT_ID, _("&Advance"), advanceMenu)
        wx.EVT_UPDATE_UI(frame, ADVANCE_EDIT_ID, frame.ProcessUpdateUIEvent)

        # wxBug: wxToolBar::GetToolPos doesn't exist, need it to find cut tool and then insert find in front of it.
        toolBar.AddSeparator()
        toolBar.AddTool(ZOOM_IN_ID, getZoomInBitmap(), shortHelpString = _("Zoom In"), longHelpString = _("Zooms the document to a larger size"))
        toolBar.AddTool(ZOOM_OUT_ID, getZoomOutBitmap(), shortHelpString = _("Zoom Out"), longHelpString = _("Zooms the document to a smaller size"))
        toolBar.Realize()

    def ProcessUpdateUIEvent(self, event):
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
        else:
            return False

from wx import ImageFromStream, BitmapFromImage
import cStringIO
#----------------------------------------------------------------------------
# Menu Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
#----------------------------------------------------------------------
def getZoomInData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01TIDAT8\x8d\x8d\x93\xbbJ\x03A\x14\x86\xbf\xd9,\xc6\xd8E%`)VF[{\xc1v\
\xf1\x82\x8f\xb0\xb94\xda\xa5\x13\x11\x8b`\xa9h\x10F\xe3#H.\xa6\x15\xccKhg\
\x10\xc1B\x8bTF\x90\xc0X\x8c3\xbb\xd9\xcdF\x7f\x18\xf6\xec\x9cs\xbe\xfd\xe70\
+\x84\x93"\xacb\xc1W\xe1\xf7\xeb\xfa\x8d`\x82\xdcXcI\x8e\x02AM\x02\t\xe1\xa4\
(\x16|uz)y\x19\xc0\xc9\xdd;\x99\xee!\x00\xd9\xbd\x00\xd6\xaf\x95\xc7B\xac\
\x03\xd3\x1c\xd6\xc2t\x10\xf7\x13\x8e\xe0\x14\x0b\xbe\xa2$m\xf3\xca\xea\xacM\
\xe6\xd2\xc1\xcaWdl>#\x0e\x8c\xed\xe7n\x90|\xa8\x96m\xbc~ y\x04Z\xcd\x86\xda\
\xda\xde\xb1Gq\x00\xb2S\t\xfeB\x9aK\xa8\xb1\x0e\xf2\x15I.\xad\x0bo\x8f\xf4\
\x97\xab\xe7z\x88\x1f\xdf\xf0\xfa9\x1e\xe0x\x9eG\xbf\x16X\xcd\xb8Ar\xc6\xd5\
\x0b4\xd4\xf3\xbcd\x07F_\xc3 \x1e\x0c\xa3Y\x08\x9f\x1f~\xefA\xab\xd9P\x9dN\
\x07\x80\xddcI\xc6\x85\xf9\xb4.8\xabhwK\xbd+6\x16\xf5\xdeZ=%F\x00\xa0\xa7\
\x0b`@F\xc6\xf6\xd3\xc5&@\x0c"\xa2\xff\x82\x01\x85-\xb7\x9a\re\x00QH\x0c0N\
\x06\x1a\x85\xbcym}\x0f\xfe\x92\x19\xdc\xf2~\xdb\xee\xdd\xf7\xf4\xf3_\x0e\
\xa2N\xc2\xfa\x01MYp\xbc\xe4a\x0f\xa9\x00\x00\x00\x00IEND\xaeB`\x82' 

def getZoomInBitmap():
    return BitmapFromImage(getZoomInImage())

def getZoomInImage():
    stream = cStringIO.StringIO(getZoomInData())
    return ImageFromStream(stream)

#----------------------------------------------------------------------
def getZoomOutData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01RIDAT8\x8d\x8d\x93\xbbJ\x03A\x14\x86\xbf\xd9\x04\x93\x90J\x0cj#Dl\
\xf4\x01\xec\x05\xdb\xc5\x0b>B\x92]\x1b+\xed,D\xb0\xb4\x08\x9afc|\x04\xc9\
\x85\xb4>\x84\x95`\x93\x80`\x15\xd8*\x98\x84\xc0X\xcc\xce\xde7\xf8\xc30\x97=\
\xf3\xcd\x7f\xce\xcc\na\xe4\x08\xabQ\xaf\xc9\xf0\xfc\xa5\xf3*X\xa1|b\xa3\xe5\
D\x81 W\x81\x840r4\xea5\xf9\xf0\xe40Y@\xf3+\xf8\xb8\xbe\x16\x8c\xdd\x96\x9d\
\n1\xf4\xc0\xdf\xdc\xb6\x01\xa8\xca\x19[\x05\xfc\x96%aY\x96\x0c\xdb\xae\xca\
\x99\xea7\x8b\x91@w.\xf9x\xbcL\xb8\xf0k\xa0O\x1e{\xd31Q\x1d\xdd\xaaC\xfa\xbd\
\xae<=;\xf7!F<\xd7,md\xc4\xf8\x0e\xf6\xaf\x1d\xb6\x8b*p\xa7\x0c\x95\xd0\x86\
\xc9\x02\xbe\xa7\xe9\x00\xc34M\xdc\x96MA\xa8[,y\xc8r>h\x00ow6\xa6if;\x98K\
\x95\xd6\xef\x12(\xc0t\x99~b8\x7f\xf0\xdeA\xbf\xd7\x95\xc3\xe1\x10\x80\x8b{\
\x87R\x1e*\xde\xd55oTq\xf7Fm\x8ew\xd5\xdaa\'\'"\x00P\xd5\x05\xd0 -m\xfb\xf3\
\xf9\x04 \x01\x11\xf1\x7fA\x83\xc2\x96\xfb\xbd\xae\xd4\x808$\x01H\x93\x86\
\xc6!?\xe6 x\xca\xab\xa4\x0bwp5\xf0\xd7\xdeG\xaa\xff\x97\x83\xb8\x93\xb0\xfe\
\x00\xc3\xa8ov\xfd\xe4\x9c\xa2\x00\x00\x00\x00IEND\xaeB`\x82' 
 

def getZoomOutBitmap():
    return BitmapFromImage(getZoomOutImage())

def getZoomOutImage():
    stream = cStringIO.StringIO(getZoomOutData())
    return ImageFromStream(stream)

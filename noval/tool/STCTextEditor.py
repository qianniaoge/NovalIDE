#----------------------------------------------------------------------------
# Name:         STCTextEditor.py
# Purpose:      Text Editor for wx.lib.pydocview tbat uses the Styled Text Control
#
# Author:       Peter Yared, Morgan Hua
#
# Created:      8/10/03
# CVS-ID:       $Id$
# Copyright:    (c) 2003-2006 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.stc
import wx.lib.docview
import wx.lib.multisash
import string
import FindService
import os
import sys
import chardet
import codecs
import shutil
import FileObserver
import WxThreadSafe
import noval.parser.config as parserconfig
import MarkerService
import TextService
import CompletionService
_ = wx.GetTranslation

#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------

class TextDocument(wx.lib.docview.Document):
    
    DEFAULT_FILE_ENCODING = "ascii"
    
    def __init__(self):
        wx.lib.docview.Document .__init__(self)
        self._inModify = False
        self.file_watcher = FileObserver.FileAlarmWatcher()
        self._is_watched = False
        self.file_encoding = TextDocument.DEFAULT_FILE_ENCODING
        self._is_new_doc = True

    def GetSaveObject(self,filename):
        return codecs.open(filename, 'w',self.file_encoding)

    def DoSaveBefore(self):
        if self._is_watched:
            self.file_watcher.StopWatchFile(self)
    
    def DoSaveBehind(self):
        pass

    def OnSaveDocument(self, filename):
        """
        Constructs an output file for the given filename (which must
        not be empty), and calls SaveObject. If SaveObject returns true, the
        document is set to unmodified; otherwise, an error message box is
        displayed.
        """
        if not filename:
            return False

        msgTitle = wx.GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")

        backupFilename = None
        fileObject = None
        copied = False
        try:
            self.DoSaveBefore()
            # if current file exists, move it to a safe place temporarily
            if os.path.exists(filename):

                # Check if read-only.
                if not os.access(filename, os.W_OK):
                    wx.MessageBox("Could not save '%s'.  No write permission to overwrite existing file." % \
                                  wx.lib.docview.FileNameFromPath(filename),
                                  msgTitle,
                                  wx.OK | wx.ICON_EXCLAMATION,
                                  self.GetDocumentWindow())
                    return False

                backupFilename = "%s.bk%s" % (filename, 1)
                shutil.copy(filename, backupFilename)
                copied = True
            fileObject = self.GetSaveObject(filename)
            self.SaveObject(fileObject)
            fileObject.close()
            fileObject = None
            
            if backupFilename:
                os.remove(backupFilename)
        except:
            # for debugging purposes
          ##  import traceback
            ##traceback.print_exc()

            if fileObject:
                fileObject.close()  # file is still open, close it, need to do this before removal 

            # save failed, remove copied file
            if backupFilename and copied:
                shutil.copy(backupFilename,filename)
                os.remove(backupFilename)

            wx.MessageBox("Could not save '%s'.  %s" % (wx.lib.docview.FileNameFromPath(filename), sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_ERROR,
                          self.GetDocumentWindow())
            self.SetDocumentModificationDate()
            return False

        self.SetDocumentModificationDate()
        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        self._is_watched = True
        self._is_new_doc = False
        self.file_watcher.StartWatchFile(self)
        self.DoSaveBehind()
        #if wx.Platform == '__WXMAC__':  # Not yet implemented in wxPython
        #    wx.FileName(file).MacSetDefaultTypeAndCreator()
        return True

    def DetectFileEncoding(self,filepath):

        file_encoding = TextDocument.DEFAULT_FILE_ENCODING
        try:
            with open(filepath,"rb") as f:
                data = f.read()
                result = chardet.detect(data)
                file_encoding = result['encoding']
        except:
            pass
        if None == file_encoding:
            file_encoding = TextDocument.DEFAULT_FILE_ENCODING
        return file_encoding

    def OnOpenDocument(self, filename):
        """
        Constructs an input file for the given filename (which must not
        be empty), and calls LoadObject. If LoadObject returns true, the
        document is set to unmodified; otherwise, an error message box is
        displayed. The document's views are notified that the filename has
        changed, to give windows an opportunity to update their titles. All of
        the document's views are then updated.
        """
        if not self.OnSaveModified():
            return False

        msgTitle = wx.GetApp().GetAppName()
        if not msgTitle:
            msgTitle = _("File Error")
        self.file_encoding = self.DetectFileEncoding(filename)
        fileObject = None
        try:
            fileObject = codecs.open(filename, 'r',self.file_encoding)
            self.LoadObject(fileObject)
            fileObject.close()
            fileObject = None
        except:
            # for debugging purposes
            import traceback
            traceback.print_exc()

            if fileObject:
                fileObject.close()  # file is still open, close it 

            wx.MessageBox("Could not open '%s'.  %s" % (wx.lib.docview.FileNameFromPath(filename), sys.exc_value),
                          msgTitle,
                          wx.OK | wx.ICON_ERROR,
                          self.GetDocumentWindow())
            return False

        self.SetDocumentModificationDate()
        self.SetFilename(filename, True)
        self.Modify(False)
        self.SetDocumentSaved(True)
        self.UpdateAllViews()
        self.file_watcher.AddFileDoc(self)
        self._is_watched = True
        self._is_new_doc = False
        return True

    @property
    def IsWatched(self):
        return self._is_watched

    @property
    def FileWatcher(self):
        return self.file_watcher

    def SaveObject(self, fileObject):
        view = self.GetFirstView()
        fileObject.write(view.GetValue())
        view.SetModifyFalse()
        return True
        
    def LoadObject(self, fileObject):
        view = self.GetFirstView()
        data = fileObject.read()
        view.SetValue(data)
        view.SetModifyFalse()
        return True

    def IsModified(self):
        filename = self.GetFilename()
        if filename and not os.path.exists(filename) and not self._is_new_doc:
            return True
        view = self.GetFirstView()
        if view:
            return view.IsModified()
        return False
    
    @property
    def IsNewDocument(self):
        return self._is_new_doc

    def Modify(self, modify):
        if self._inModify:
            return
        self._inModify = True
        view = self.GetFirstView()
        if not modify and view:
            view.SetModifyFalse()
        wx.lib.docview.Document.Modify(self, modify)  # this must called be after the SetModifyFalse call above.
        self._inModify = False
        
    def OnCreateCommandProcessor(self):
        # Don't create a command processor, it has its own
        pass

# Use this to override MultiClient.Select to prevent yellow background.  
def MultiClientSelectBGNotYellow(a):     
    a.GetParent().multiView.UnSelect()   
    a.selected = True    
    #a.SetBackgroundColour(wx.Colour(255,255,0)) # Yellow        
    a.Refresh()

class TextView(wx.lib.docview.View):
    MARKER_NUM = 0
    MARKER_MASK = 0x1
    
    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------

    def __init__(self):
        wx.lib.docview.View.__init__(self)
        self._textEditor = None
        self._markerCount = 0
        self._commandProcessor = None
        self._dynSash = None


    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return TextCtrl
    
    def GetLangLexer(self):
        return parserconfig.LANG_NONE_LEXER

    def GetCtrl(self):
        if wx.Platform == "__WXMAC__":
            # look for active one first  
            self._textEditor = self._GetActiveCtrl(self._dynSash)        
            if self._textEditor == None:  # it is possible none are active       
                # look for any existing one      
                self._textEditor = self._FindCtrl(self._dynSash)
        return self._textEditor


    def SetCtrl(self, ctrl):
        self._textEditor = ctrl
                

    def OnCreatePrintout(self):
        """ for Print Preview and Print """
        return TextPrintout(self, self.GetDocument().GetPrintableName())

            
    def OnCreate(self, doc, flags):
        frame = wx.GetApp().CreateDocumentFrame(self, doc, flags, style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        # wxBug: DynamicSashWindow doesn't work on Mac, so revert to
        # multisash implementation
        if wx.Platform == "__WXMAC__":
            wx.lib.multisash.MultiClient.Select = MultiClientSelectBGNotYellow
            self._dynSash = wx.lib.multisash.MultiSash(frame, -1)
            self._dynSash.SetDefaultChildClass(self.GetCtrlClass()) # wxBug:  MultiSash instantiates the first TextCtrl with this call
            
            self._textEditor = self.GetCtrl()  # wxBug: grab the TextCtrl from the MultiSash datastructure
        else:
            self._dynSash = wx.gizmos.DynamicSashWindow(frame, -1, style=wx.CLIP_CHILDREN)
            self._dynSash._view = self
            self._textEditor = self.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
        wx.EVT_LEFT_DOWN(self._textEditor, self.OnLeftClick)
        self._textEditor.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModify)
        
        self._CreateSizer(frame)
        self.Activate()
        frame.Show(True)
        frame.Layout()
        return True


    def OnModify(self, event):
        self.GetDocument().Modify(self._textEditor.GetModify())
        

    def _CreateSizer(self, frame):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._dynSash, 1, wx.EXPAND)
        frame.SetSizer(sizer)


    def OnLeftClick(self, event):
        self.Activate()
        event.Skip()


    def OnUpdate(self, sender = None, hint = None):
        if wx.lib.docview.View.OnUpdate(self, sender, hint):
            return

        if hint == "ViewStuff":
            self.GetCtrl().SetViewDefaults()
        elif hint == "Font":
            font, color = self.GetCtrl().GetFontAndColorFromConfig()
            self.GetCtrl().SetFont(font)
            self.GetCtrl().SetFontColor(color)
            
    def OnActivateView(self, activate, activeView, deactiveView):
        if activate and self.GetCtrl():
            if isinstance(deactiveView,TextView):
                text_ctrl = deactiveView.GetCtrl()
                if text_ctrl and text_ctrl.AutoCompActive():
                    text_ctrl.AutoCompCancel()
            # In MDI mode just calling set focus doesn't work and in SDI mode using CallAfter causes an endless loop
            if self.GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
                self.SetFocus()
            else:
                wx.CallAfter(self.SetFocus)

    def SetFocus(self):
        if self.GetCtrl():
            self.GetCtrl().SetFocus()           
                                
    def OnClose(self, deleteWindow = True):
        if not wx.lib.docview.View.OnClose(self, deleteWindow):
            return False
    
        document = self.GetDocument()
        if document.IsWatched:
            document.FileWatcher.RemoveFileDoc(document)
        self.Activate(False)
        if deleteWindow and self.GetFrame():
            self.GetFrame().Destroy()
        return True


    def ProcessEvent(self, event):        
        id = event.GetId()
        if id == wx.ID_UNDO:
            self.GetCtrl().Undo()
            return True
        elif id == wx.ID_REDO:
            self.GetCtrl().Redo()
            return True
        elif id == wx.ID_CUT:
            self.GetCtrl().Cut()
            return True
        elif id == wx.ID_COPY:
            self.GetCtrl().Copy()
            return True
        elif id == wx.ID_PASTE:
            self.GetCtrl().OnPaste()
            return True
        elif id == wx.ID_CLEAR:
            self.GetCtrl().OnClear()
            return True
        elif id == wx.ID_SELECTALL:
            self.GetCtrl().SelectAll()
            return True
        elif id == TextService.VIEW_WHITESPACE_ID:
            self.GetCtrl().SetViewWhiteSpace(not self.GetCtrl().GetViewWhiteSpace())
            return True
        elif id == TextService.VIEW_EOL_ID:
            self.GetCtrl().SetViewEOL(not self.GetCtrl().GetViewEOL())
            return True
        elif id == TextService.VIEW_INDENTATION_GUIDES_ID:
            self.GetCtrl().SetIndentationGuides(not self.GetCtrl().GetIndentationGuides())
            return True
        elif id == TextService.VIEW_RIGHT_EDGE_ID:
            self.GetCtrl().SetViewRightEdge(not self.GetCtrl().GetViewRightEdge())
            return True
        elif id == TextService.VIEW_LINE_NUMBERS_ID:
            self.GetCtrl().SetViewLineNumbers(not self.GetCtrl().GetViewLineNumbers())
            return True
        elif id == TextService.ZOOM_NORMAL_ID:
            self.GetCtrl().SetZoom(0)
            return True
        elif id == TextService.ZOOM_IN_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_ZOOMIN)
            return True
        elif id == TextService.ZOOM_OUT_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_ZOOMOUT)
            return True
        elif id == TextService.CHOOSE_FONT_ID:
            self.OnChooseFont()
            return True
        elif id == TextService.WORD_WRAP_ID:
            self.GetCtrl().SetWordWrap(not self.GetCtrl().GetWordWrap())
            return True
        elif id == FindService.FindService.FIND_ID:
            self.OnFind()
            return True
        elif id == FindService.FindService.FIND_PREVIOUS_ID:
            self.DoFindText(forceFindPrevious = True)
            return True
        elif id == FindService.FindService.FIND_NEXT_ID:
            self.DoFindText(forceFindNext = True)
            return True
        elif id == FindService.FindService.REPLACE_ID:
            self.OnFind(replace = True)
            return True
        elif id == FindService.FindService.FINDONE_ID:
            self.DoFindText()
            return True
        elif id == FindService.FindService.REPLACEONE_ID:
            self.DoReplaceSel()
            return True
        elif id == FindService.FindService.REPLACEALL_ID:
            self.DoReplaceAll()
            return True
        elif id == FindService.FindService.GOTO_LINE_ID:
            self.OnGotoLine(event)
            return True
        else:
            return wx.lib.docview.View.ProcessEvent(self, event)


    def ProcessUpdateUIEvent(self, event):
        if not self.GetCtrl():
            return False

        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(self.GetCtrl().CanUndo())
            event.SetText(_("&Undo\tCtrl+Z"))  # replace menu string
            return True
        elif id == wx.ID_REDO:
            event.Enable(self.GetCtrl().CanRedo())
            event.SetText(_("&Redo\tCtrl+Y"))  # replace menu string
            return True
        elif (id == wx.ID_CUT
        or id == wx.ID_COPY
        or id == wx.ID_CLEAR):
            event.Enable(self.HasSelection())
            return True
        elif id == wx.ID_PASTE:
            event.Enable(self.GetCtrl().CanPaste())
            return True
        elif id == wx.ID_SELECTALL:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == TextService.TEXT_ID \
                or id == MarkerService.MarkerService.BOOKMARKER_ID \
                or id == TextService.INSERT_TEXT_ID \
                or id == TextService.ADVANCE_EDIT_ID \
                or id == TextService.ZOOM_ID \
                or id == TextService.CHOOSE_FONT_ID:
            event.Enable(True)
            return True
        elif id == TextService.VIEW_WHITESPACE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewWhiteSpace())
            return True
        elif id == TextService.VIEW_EOL_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewEOL())
            return True
        elif id == TextService.VIEW_INDENTATION_GUIDES_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetIndentationGuides())
            return True
        elif id == TextService.VIEW_RIGHT_EDGE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewRightEdge())
            return True
        elif id == TextService.VIEW_LINE_NUMBERS_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            event.Check(self.GetCtrl().GetViewLineNumbers())
            return True
        elif id == TextService.ZOOM_NORMAL_ID:
            event.Enable(self.GetCtrl().GetZoom() != 0)
            return True
        elif id == TextService.ZOOM_IN_ID:
            event.Enable(self.GetCtrl().GetZoom() < 20)
            return True
        elif id == TextService.ZOOM_OUT_ID:
            event.Enable(self.GetCtrl().GetZoom() > -10)
            return True
        elif id == TextService.WORD_WRAP_ID:
            event.Enable(self.GetCtrl().CanWordWrap())
            event.Check(self.GetCtrl().CanWordWrap() and self.GetCtrl().GetWordWrap())
            return True
        elif id == FindService.FindService.FIND_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == FindService.FindService.FIND_PREVIOUS_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText and
                         self._FindServiceHasString() and
                         self.GetCtrl().GetSelection()[0] > 0)
            return True
        elif id == FindService.FindService.FIND_NEXT_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText and
                         self._FindServiceHasString() and
                         self.GetCtrl().GetSelection()[0] < self.GetCtrl().GetLength())
            return True
        elif id == FindService.FindService.REPLACE_ID:
            hasText = self.GetCtrl().GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == FindService.FindService.GOTO_LINE_ID:
            event.Enable(True)
            return True
        elif id == TextService.TEXT_STATUS_BAR_ID:
            self.OnUpdateStatusBar(event)
            return True
        elif id == CompletionService.CompletionService.GO_TO_DEFINITION:
            event.Enable(self.GetCtrl().IsCaretLocateInWord())
            return True
        elif id == CompletionService.CompletionService.LIST_CURRENT_MEMBERS:
            event.Enable(self.GetCtrl().IsListMemberFlag(self.GetCtrl().GetCurrentPos()-1))
            return True
        else:
            return wx.lib.docview.View.ProcessUpdateUIEvent(self, event)


    def _GetParentFrame(self):
        return wx.GetTopLevelParent(self.GetFrame())

    def _GetActiveCtrl(self, parent):    
        """ Walk through the MultiSash windows and find the active Control """   
        if isinstance(parent, wx.lib.multisash.MultiClient) and parent.selected:         
            return parent.child  
        if hasattr(parent, "GetChildren"):       
            for child in parent.GetChildren():   
                found = self._GetActiveCtrl(child)       
                if found:        
                    return found         
        return None      

         
    def _FindCtrl(self, parent):         
        """ Walk through the MultiSash windows and find the first TextCtrl """   
        if isinstance(parent, self.GetCtrlClass()):      
            return parent        
        if hasattr(parent, "GetChildren"):       
            for child in parent.GetChildren():   
                found = self._FindCtrl(child)    
                if found:        
                    return found         
        return None      
 

    #----------------------------------------------------------------------------
    # Methods for TextDocument to call
    #----------------------------------------------------------------------------

    def IsModified(self):
        if not self.GetCtrl():
            return False
        return self.GetCtrl().GetModify()


    def SetModifyFalse(self):
        self.GetCtrl().SetSavePoint()


    def GetValue(self):
        if self.GetCtrl():
            return self.GetCtrl().GetText()
        else:
            return None


    def SetValue(self, value):
        self.GetCtrl().SetText(value)
        self.GetCtrl().UpdateLineNumberMarginWidth()
        self.GetCtrl().EmptyUndoBuffer()

    def AddText(self,text):
        self.GetCtrl().AddText(text)

    def HasSelection(self):
        return self.GetCtrl().HasSelection()

    def GetTopLines(self,line_num):
        lines = []
        for i in range(line_num):
            lines.append(self.GetCtrl().GetLine(i))
        return lines
    #----------------------------------------------------------------------------
    # STC events
    #----------------------------------------------------------------------------

    def OnUpdateStatusBar(self, event):
        statusBar = self._GetParentFrame().GetStatusBar()
        statusBar.SetInsertMode(self.GetCtrl().GetOvertype() == 0)
        statusBar.SetLineNumber(self.GetCtrl().GetCurrentLine() + 1)
        statusBar.SetColumnNumber(self.GetCtrl().GetColumn(self.GetCtrl().GetCurrentPos()) + 1)


    #----------------------------------------------------------------------------
    # Format methods
    #----------------------------------------------------------------------------

    def OnChooseFont(self):
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetInitialFont(self.GetCtrl().GetFont())
        data.SetColour(self.GetCtrl().GetFontColor())
        fontDialog = wx.FontDialog(self.GetFrame(), data)
        fontDialog.CenterOnParent()
        if fontDialog.ShowModal() == wx.ID_OK:
            data = fontDialog.GetFontData()
            self.GetCtrl().SetFont(data.GetChosenFont())
            self.GetCtrl().SetFontColor(data.GetColour())
            self.GetCtrl().UpdateStyles()
        fontDialog.Destroy()


    #----------------------------------------------------------------------------
    # Find methods
    #----------------------------------------------------------------------------

    def OnFind(self, replace = False):
        findService = wx.GetApp().GetService(FindService.FindService)
        if findService:
            findService.ShowFindReplaceDialog(findString = self.GetCtrl().GetSelectedText(), replace = replace)

    def AdjustFindDialogPosition(self,findService):
        start = self.GetCtrl().GetSelectionEnd()
        point = self.GetCtrl().PointFromPosition(start)
        new_point = self.GetCtrl().ClientToScreen(point)
        current_dlg = findService.GetCurrentDialog()
        dlg_rect = current_dlg.GetRect()
        if dlg_rect.Contains(new_point):
            if new_point.y > dlg_rect.GetHeight():
                dlg_rect.Offset(wx.Point(0,new_point.y-20-dlg_rect.GetBottomRight().y))
            else:
                dlg_rect.Offset(wx.Point(0,new_point.y+40-dlg_rect.GetTopLeft().y))
            to_point = wx.Point(dlg_rect.GetX(),dlg_rect.GetY())
            current_dlg.Move(to_point)
    
    def TextNotFound(self,findString,flags,forceFindNext = False, forceFindPrevious = False):
        wx.MessageBox(_("Have been reached the end of document,Can't find \"%s\".") % findString, "Find",
                          wx.OK | wx.ICON_INFORMATION)     
        down = flags & wx.FR_DOWN > 0
        wrap = flags & FindService.FindService.FR_WRAP > 0
        if forceFindPrevious: 
            down = False
            wrap = False 
        elif forceFindNext:
            down = True
            wrap = False
        if wrap & down:
            self.GetCtrl().SetSelectionStart(0)
            self.GetCtrl().SetSelectionEnd(0)
        elif wrap & (not down):
            doc_length = self.GetCtrl().GetLength()
            self.GetCtrl().SetSelectionStart(doc_length)
            self.GetCtrl().SetSelectionEnd(doc_length)
        
    def FindText(self,findString,flags,forceFindNext = False, forceFindPrevious = False):
        startLoc, endLoc = self.GetCtrl().GetSelection()
        wholeWord = flags & wx.FR_WHOLEWORD > 0
        matchCase = flags & wx.FR_MATCHCASE > 0
        regExp = flags & FindService.FindService.FR_REGEXP > 0
        down = flags & wx.FR_DOWN > 0
        wrap = flags & FindService.FindService.FR_WRAP > 0
        
        if forceFindPrevious:   # this is from function keys, not dialog box
            down = False
            wrap = False        # user would want to know they're at the end of file
        elif forceFindNext:
            down = True
            wrap = False        # user would want to know they're at the end of file
            
        minpos = self.GetCtrl().GetSelectionStart()
        maxpos = self.GetCtrl().GetSelectionEnd()
        if minpos != maxpos:
            if down:
                minpos += 1
            else:
                maxpos = minpos - 1
        if down:
            maxpos = self.GetCtrl().GetLength()
        else:
            minpos = 0
        flags =  wx.stc.STC_FIND_MATCHCASE if matchCase else 0
        flags |= wx.stc.STC_FIND_WHOLEWORD if wholeWord else 0
        flags |= wx.stc.STC_FIND_REGEXP if regExp else 0
         #Swap the start and end positions which Scintilla uses to flag backward searches
        if not down:
            tmp_min = minpos
            minpos = maxpos
            maxpos= tmp_min

        return True if self.FindAndSelect(findString,minpos,maxpos,flags) != -1 else False
 
    def FindAndSelect(self,findString,minpos,maxpos,flags):
        index = self.GetCtrl().FindText(minpos,maxpos,findString,flags)
        if -1 != index:
            start = index
            end = index + len(findString.encode('utf-8'))
            self.GetCtrl().SetSelection(start,end)
            self.GetCtrl().EnsureVisibleEnforcePolicy(self.GetCtrl().LineFromPosition(end))  # show bottom then scroll up to top
            self.GetCtrl().EnsureVisibleEnforcePolicy(self.GetCtrl().LineFromPosition(start)) # do this after ensuring bottom is visible
            wx.GetApp().GetTopWindow().PushStatusText(_("Found \"%s\".") % findString)
        return index
        
    def DoFindText(self,forceFindNext = False, forceFindPrevious = False):
        findService = wx.GetApp().GetService(FindService.FindService)
        if not findService:
            return
        findString = findService.GetFindString()
        if len(findString) == 0:
            return -1
        flags = findService.GetFlags()
        if not self.FindText(findString,flags,forceFindNext,forceFindPrevious):
            self.TextNotFound(findString,flags,forceFindNext,forceFindPrevious)
        else:
            if not forceFindNext and not forceFindPrevious:
                self.AdjustFindDialogPosition(findService)
            
    def DoReplaceSel(self):
        findService = wx.GetApp().GetService(FindService.FindService)
        if not findService:
            return
        findString = findService.GetFindString()
        if len(findString) == 0:
            return -1
        replaceString = findService.GetReplaceString()
        flags = findService.GetFlags()
        if not self.SameAsSelected(findString,flags):
            if not self.FindText(findString,flags):
                self.TextNotFound(findString,flags)
            else:
                self.AdjustFindDialogPosition(findService)
            return
        self.GetCtrl().ReplaceSelection(replaceString)
        if not self.FindText(findString,flags):
            self.TextNotFound(findString,flags)
        else:
            self.AdjustFindDialogPosition(findService)
      
    def DoReplaceAll(self):
        findService = wx.GetApp().GetService(FindService.FindService)
        if not findService:
            return
        findString = findService.GetFindString()
        if len(findString) == 0:
            return -1
        replaceString = findService.GetReplaceString()
        flags = findService.GetFlags()
        hit_found = False
        self.GetCtrl().SetSelection(0,0)
        ###self.GetCtrl().HideSelection(True)
        while self.FindText(findString,flags):
            hit_found = True
            self.GetCtrl().ReplaceSelection(replaceString)

        ###self.GetCtrl().HideSelection(False)
        if not hit_found:
            self.TextNotFound(findString,flags)
        
    def SameAsSelected(self,findString,flags):
        start_pos = self.GetCtrl().GetSelectionStart()
        end_pos = self.GetCtrl().GetSelectionEnd()
        wholeWord = flags & wx.FR_WHOLEWORD > 0
        matchCase = flags & wx.FR_MATCHCASE > 0
        regExp = flags & FindService.FindService.FR_REGEXP > 0
        flags =  wx.stc.STC_FIND_MATCHCASE if matchCase else 0
        flags |= wx.stc.STC_FIND_WHOLEWORD if wholeWord else 0
        flags |= wx.stc.STC_FIND_REGEXP if regExp else 0
        #Now use the advanced search functionality of scintilla to determine the result
        self.GetCtrl().SetSearchFlags(flags);
        self.GetCtrl().TargetFromSelection();
        #see what we got
        if self.GetCtrl().SearchInTarget(findString) < 0:
            #no match
            return False
        	#If we got a match, the target is set to the found text
        return (self.GetCtrl().GetTargetStart() == start_pos) and (self.GetCtrl().GetTargetEnd() == end_pos);
        
    def FindTextInLine(self,text,line,col=0):
        line_start = self.GetCtrl().PositionFromLine(line-1)
        line_start += col
        line_end = self.GetCtrl().PositionFromLine(line)
        index = self.GetCtrl().FindText(line_start,line_end,text,0)
        if -1 != index:
            return index,index + len(text)
        return -1,-1

    def _FindServiceHasString(self):
        findService = wx.GetApp().GetService(FindService.FindService)
        if not findService or not findService.GetFindString():
            return False
        return True

    def OnGotoLine(self, event):
        findService = wx.GetApp().GetService(FindService.FindService)
        if findService:
            line_number = self.GetCtrl().GetLineCount()
            line = findService.GetLineNumber(self.GetDocumentManager().FindSuitableParent(),line_number)
            if line > -1:
                line = line - 1
                self.GetCtrl().EnsureVisible(line)
                self.GetCtrl().GotoLine(line)

    def GotoLine(self, lineNum):
        if lineNum > -1:
            lineNum = lineNum - 1  # line numbering for editor is 0 based, we are 1 based.
            self.GetCtrl().EnsureVisibleEnforcePolicy(lineNum)
            self.GetCtrl().GotoLine(lineNum)

    def SetSelection(self, start, end):
        self.GetCtrl().SetSelection(start, end)

    def EnsureVisible(self, line):
        self.GetCtrl().EnsureVisible(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def EnsureVisibleEnforcePolicy(self, line):
        self.GetCtrl().EnsureVisibleEnforcePolicy(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLineCount(self):
        return self.GetCtrl().GetLineCount()
        
    def LineFromPosition(self, pos):
        return self.GetCtrl().LineFromPosition(pos)+1  # line numbering for editor is 0 based, we are 1 based.

    def PositionFromLine(self, line):
        return self.GetCtrl().PositionFromLine(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLineEndPosition(self, line):
        return self.GetCtrl().GetLineEndPosition(line-1)  # line numbering for editor is 0 based, we are 1 based.

    def GetLine(self, lineNum):
        return self.GetCtrl().GetLine(lineNum-1)  # line numbering for editor is 0 based, we are 1 based.

    def MarkerDefine(self):
        """ This must be called after the texteditor is instantiated """
        self.GetCtrl().MarkerDefine(TextView.MARKER_NUM, wx.stc.STC_MARK_CIRCLE, wx.BLACK, wx.BLUE)

    def MarkerToggle(self, lineNum = -1, marker_index=MARKER_NUM, mask=MARKER_MASK):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine()
        if self.GetCtrl().MarkerGet(lineNum) & mask:
            self.GetCtrl().MarkerDelete(lineNum, marker_index)
            self._markerCount -= 1
        else:
            self.GetCtrl().MarkerAdd(lineNum, marker_index)
            self._markerCount += 1

    def MarkerAdd(self, lineNum = -1, marker_index=MARKER_NUM, mask=MARKER_MASK):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine()
        self.GetCtrl().MarkerAdd(lineNum, marker_index)
        self._markerCount += 1

    def MarkerDelete(self, lineNum = -1, marker_index=MARKER_NUM, mask=MARKER_MASK):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine()
        if self.GetCtrl().MarkerGet(lineNum) & mask:
            self.GetCtrl().MarkerDelete(lineNum, marker_index)
            self._markerCount -= 1

    def MarkerDeleteAll(self, marker_num=MARKER_NUM):
        self.GetCtrl().MarkerDeleteAll(marker_num)
        if marker_num == self.MARKER_NUM:
            self._markerCount = 0

    def MarkerNext(self, lineNum = -1):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine() + 1  # start search below current line
        foundLine = self.GetCtrl().MarkerNext(lineNum, self.MARKER_MASK)
        if foundLine == -1:
            # wrap to top of file
            foundLine = self.GetCtrl().MarkerNext(0, self.MARKER_MASK)
            if foundLine == -1:
                wx.GetApp().GetTopWindow().PushStatusText(_("No markers"))
                return        
        self.GotoLine(foundLine + 1)

    def MarkerPrevious(self, lineNum = -1):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine() - 1  # start search above current line
            if lineNum == -1:
                lineNum = self.GetCtrl().GetLineCount()

        foundLine = self.GetCtrl().MarkerPrevious(lineNum, self.MARKER_MASK)
        if foundLine == -1:
            # wrap to bottom of file
            foundLine = self.GetCtrl().MarkerPrevious(self.GetCtrl().GetLineCount(), self.MARKER_MASK)
            if foundLine == -1:
                wx.GetApp().GetTopWindow().PushStatusText(_("No markers"))
                return
        self.GotoLine(foundLine + 1)

    def MarkerExists(self, lineNum = -1, mask=MARKER_MASK):
        if lineNum == -1:
            lineNum = self.GetCtrl().GetCurrentLine()
        if self.GetCtrl().MarkerGet(lineNum) & mask:
            return True
        else:
            return False

    def GetMarkerLines(self, mask=MARKER_MASK):
        retval = []
        for lineNum in range(self.GetCtrl().GetLineCount()):
            if self.GetCtrl().MarkerGet(lineNum) & mask:
                retval.append(lineNum)
        return retval
        
    def GetMarkerCount(self):
        return self._markerCount

    @WxThreadSafe.call_after
    def Alarm(self,alarm_type):
        if alarm_type == FileObserver.FileEventHandler.FILE_MODIFY_EVENT:
            ret = wx.MessageBox("File \"%s\" has already been modified outside,Do You Want to reload it?" % self.GetDocument().GetFilename(), "Reload..",
                           wx.YES_NO  | wx.ICON_QUESTION,self.GetFrame())
            if ret == wx.YES:
                document = self.GetDocument()
                document.OnOpenDocument(document.GetFilename())
                
        elif alarm_type == FileObserver.FileEventHandler.FILE_MOVED_EVENT or \
             alarm_type == FileObserver.FileEventHandler.FILE_DELETED_EVENT:
            ret = wx.MessageBox(_("File \"%s\" has already been moved or deleted outside,Do You Want to keep it in Editor?") % self.GetDocument().GetFilename(), _("Keep Document.."),
                           wx.YES_NO  | wx.ICON_QUESTION ,self.GetFrame())
            document = self.GetDocument()
            if ret == wx.YES:
                document.Modify(True)
            else:
                document.DeleteAllViews()

    def IsUnitTestEnable(self):
        return False

class TextOptionsPanel(wx.Panel):


    def __init__(self, parent, id, configPrefix = "Text", label = "Text", hasWordWrap = True, hasTabs = False, addPage=True, hasFolding=False):
        wx.Panel.__init__(self, parent, id)
        self._configPrefix = configPrefix
        self._hasWordWrap = hasWordWrap
        self._hasTabs = hasTabs
        self._hasFolding = hasFolding
        SPACE = 10
        HALF_SPACE   = 5
        config = wx.ConfigBase_Get()
        self._textFont = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
        fontData = config.Read(self._configPrefix + "EditorFont", "")
        if fontData:
            nativeFont = wx.NativeFontInfo()
            nativeFont.FromString(fontData)
            self._textFont.SetNativeFontInfo(nativeFont)
        self._originalTextFont = self._textFont
        self._textColor = wx.BLACK
        colorData = config.Read(self._configPrefix + "EditorColor", "")
        if colorData:
            red = int("0x" + colorData[0:2], 16)
            green = int("0x" + colorData[2:4], 16)
            blue = int("0x" + colorData[4:6], 16)
            self._textColor = wx.Colour(red, green, blue)
        self._originalTextColor = self._textColor
        fontLabel = wx.StaticText(self, -1, _("Font:"))
        self._sampleTextCtrl = wx.TextCtrl(self, -1, "", size = (125, 21))
        self._sampleTextCtrl.SetEditable(False)
        chooseFontButton = wx.Button(self, -1, _("Choose Font..."))
        wx.EVT_BUTTON(self, chooseFontButton.GetId(), self.OnChooseFont)
        if self._hasWordWrap:
            self._wordWrapCheckBox = wx.CheckBox(self, -1, _("Wrap words inside text area"))
            self._wordWrapCheckBox.SetValue(wx.ConfigBase_Get().ReadInt(self._configPrefix + "EditorWordWrap", False))
        self._viewWhitespaceCheckBox = wx.CheckBox(self, -1, _("Show whitespace"))
        self._viewWhitespaceCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewWhitespace", False))
        self._viewEOLCheckBox = wx.CheckBox(self, -1, _("Show end of line markers"))
        self._viewEOLCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewEOL", False))
        self._viewIndentationGuideCheckBox = wx.CheckBox(self, -1, _("Show indentation guides"))
        self._viewIndentationGuideCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewIndentationGuides", False))
        self._viewRightEdgeCheckBox = wx.CheckBox(self, -1, _("Show right edge"))
        self._viewRightEdgeCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewRightEdge", False))
        self._viewLineNumbersCheckBox = wx.CheckBox(self, -1, _("Show line numbers"))
        self._viewLineNumbersCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewLineNumbers", True))
        if self._hasFolding:
            self._viewFoldingCheckBox = wx.CheckBox(self, -1, _("Show folding"))
            self._viewFoldingCheckBox.SetValue(config.ReadInt(self._configPrefix + "EditorViewFolding", True))
        if self._hasTabs:
            self._hasTabsCheckBox = wx.CheckBox(self, -1, _("Use spaces instead of tabs"))
            self._hasTabsCheckBox.SetValue(not wx.ConfigBase_Get().ReadInt(self._configPrefix + "EditorUseTabs", False))
            indentWidthLabel = wx.StaticText(self, -1, _("Indent Width:"))
            self._indentWidthChoice = wx.Choice(self, -1, choices = ["2", "4", "6", "8", "10"])
            self._indentWidthChoice.SetStringSelection(str(config.ReadInt(self._configPrefix + "EditorIndentWidth", 4)))
        textPanelBorderSizer = wx.BoxSizer(wx.VERTICAL)
        textPanelSizer = wx.BoxSizer(wx.VERTICAL)
        textFontSizer = wx.BoxSizer(wx.HORIZONTAL)
        textFontSizer.Add(fontLabel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP, HALF_SPACE)
        textFontSizer.Add(self._sampleTextCtrl, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, HALF_SPACE)
        textFontSizer.Add(chooseFontButton, 0, wx.ALIGN_RIGHT | wx.LEFT, HALF_SPACE)
        textPanelSizer.Add(textFontSizer, 0, wx.ALL|wx.EXPAND, HALF_SPACE)
        if self._hasWordWrap:
            textPanelSizer.Add(self._wordWrapCheckBox, 0, wx.ALL, HALF_SPACE)
        textPanelSizer.Add(self._viewWhitespaceCheckBox, 0, wx.ALL, HALF_SPACE)
        textPanelSizer.Add(self._viewEOLCheckBox, 0, wx.ALL, HALF_SPACE)
        textPanelSizer.Add(self._viewIndentationGuideCheckBox, 0, wx.ALL, HALF_SPACE)
        textPanelSizer.Add(self._viewRightEdgeCheckBox, 0, wx.ALL, HALF_SPACE)
        textPanelSizer.Add(self._viewLineNumbersCheckBox, 0, wx.ALL, HALF_SPACE)
        if self._hasFolding:
            textPanelSizer.Add(self._viewFoldingCheckBox, 0, wx.ALL, HALF_SPACE)
        if self._hasTabs:
            textPanelSizer.Add(self._hasTabsCheckBox, 0, wx.ALL, HALF_SPACE)
            textIndentWidthSizer = wx.BoxSizer(wx.HORIZONTAL)
            textIndentWidthSizer.Add(indentWidthLabel, 0, wx.ALIGN_LEFT | wx.RIGHT | wx.TOP, HALF_SPACE)
            textIndentWidthSizer.Add(self._indentWidthChoice, 0, wx.ALIGN_LEFT | wx.EXPAND, HALF_SPACE)
            textPanelSizer.Add(textIndentWidthSizer, 0, wx.ALL, HALF_SPACE)
        textPanelBorderSizer.Add(textPanelSizer, 0, wx.ALL|wx.EXPAND, SPACE)
##        styleButton = wx.Button(self, -1, _("Choose Style..."))
##        wx.EVT_BUTTON(self, styleButton.GetId(), self.OnChooseStyle)
##        textPanelBorderSizer.Add(styleButton, 0, wx.ALL, SPACE)
        self.SetSizer(textPanelBorderSizer)
        self.UpdateSampleFont()
        if addPage:
            parent.AddPage(self, _(label))

    def UpdateSampleFont(self):
        nativeFont = wx.NativeFontInfo()
        nativeFont.FromString(self._textFont.GetNativeFontInfoDesc())
        font = wx.NullFont
        font.SetNativeFontInfo(nativeFont)
        font.SetPointSize(self._sampleTextCtrl.GetFont().GetPointSize())  # Use the standard point size
        self._sampleTextCtrl.SetFont(font)
        self._sampleTextCtrl.SetForegroundColour(self._textColor)
        self._sampleTextCtrl.SetValue(str(self._textFont.GetPointSize()) + _(" pt. ") + self._textFont.GetFaceName())
        self._sampleTextCtrl.Refresh()
        self.Layout()


##    def OnChooseStyle(self, event):
##        import STCStyleEditor
##        import os
##        base = os.path.split(__file__)[0]
##        config = os.path.abspath(os.path.join(base, 'stc-styles.rc.cfg'))
##        
##        dlg = STCStyleEditor.STCStyleEditDlg(None,
##                                'Python', 'python',
##                                #'HTML', 'html',
##                                #'XML', 'xml',
##                                config)
##        dlg.CenterOnParent()
##        try:
##            dlg.ShowModal()
##        finally:
##            dlg.Destroy()


    def OnChooseFont(self, event):
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetInitialFont(self._textFont)
        data.SetColour(self._textColor)
        fontDialog = wx.FontDialog(self, data)
        fontDialog.CenterOnParent()
        if fontDialog.ShowModal() == wx.ID_OK:
            data = fontDialog.GetFontData()
            self._textFont = data.GetChosenFont()
            self._textColor = data.GetColour()
            self.UpdateSampleFont()
        fontDialog.Destroy()


    def OnOK(self, optionsDialog):
        config = wx.ConfigBase_Get()
        doViewStuffUpdate = config.ReadInt(self._configPrefix + "EditorViewWhitespace", False) != self._viewWhitespaceCheckBox.GetValue()
        config.WriteInt(self._configPrefix + "EditorViewWhitespace", self._viewWhitespaceCheckBox.GetValue())
        doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewEOL", False) != self._viewEOLCheckBox.GetValue()
        config.WriteInt(self._configPrefix + "EditorViewEOL", self._viewEOLCheckBox.GetValue())
        doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewIndentationGuides", False) != self._viewIndentationGuideCheckBox.GetValue()
        config.WriteInt(self._configPrefix + "EditorViewIndentationGuides", self._viewIndentationGuideCheckBox.GetValue())
        doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewRightEdge", False) != self._viewRightEdgeCheckBox.GetValue()
        config.WriteInt(self._configPrefix + "EditorViewRightEdge", self._viewRightEdgeCheckBox.GetValue())
        doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewLineNumbers", True) != self._viewLineNumbersCheckBox.GetValue()
        config.WriteInt(self._configPrefix + "EditorViewLineNumbers", self._viewLineNumbersCheckBox.GetValue())
        if self._hasFolding:
            doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorViewFolding", True) != self._viewFoldingCheckBox.GetValue()
            config.WriteInt(self._configPrefix + "EditorViewFolding", self._viewFoldingCheckBox.GetValue())
        if self._hasWordWrap:
            doViewStuffUpdate = doViewStuffUpdate or config.ReadInt(self._configPrefix + "EditorWordWrap", False) != self._wordWrapCheckBox.GetValue()
            config.WriteInt(self._configPrefix + "EditorWordWrap", self._wordWrapCheckBox.GetValue())
        if self._hasTabs:
            doViewStuffUpdate = doViewStuffUpdate or not config.ReadInt(self._configPrefix + "EditorUseTabs", True) != self._hasTabsCheckBox.GetValue()
            config.WriteInt(self._configPrefix + "EditorUseTabs", not self._hasTabsCheckBox.GetValue())
            newIndentWidth = int(self._indentWidthChoice.GetStringSelection())
            oldIndentWidth = config.ReadInt(self._configPrefix + "EditorIndentWidth", 4)
            if newIndentWidth != oldIndentWidth:
                doViewStuffUpdate = True
                config.WriteInt(self._configPrefix + "EditorIndentWidth", newIndentWidth)
        doFontUpdate = self._originalTextFont != self._textFont or self._originalTextColor != self._textColor
        config.Write(self._configPrefix + "EditorFont", self._textFont.GetNativeFontInfoDesc())
        config.Write(self._configPrefix + "EditorColor", "%02x%02x%02x" % (self._textColor.Red(), self._textColor.Green(), self._textColor.Blue()))
        if doViewStuffUpdate or doFontUpdate:
            for document in optionsDialog.GetDocManager().GetDocuments():
                if issubclass(document.GetDocumentTemplate().GetDocumentType(), TextDocument):
                    if doViewStuffUpdate:
                        document.UpdateAllViews(hint = "ViewStuff")
                    if doFontUpdate:
                        document.UpdateAllViews(hint = "Font")
               
         
    def GetIcon(self):
        return getTextIcon()

class TextCtrl(wx.stc.StyledTextCtrl):

    def __init__(self, parent, id=-1, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.stc.StyledTextCtrl.__init__(self, parent, id, style=style)

        if isinstance(parent, wx.gizmos.DynamicSashWindow):
            self._dynSash = parent
            self.SetupDSScrollBars()
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_SPLIT, self.OnDSSplit)
            self.Bind(wx.gizmos.EVT_DYNAMIC_SASH_UNIFY, self.OnDSUnify)

        self._font = None
        self._fontColor = None
        
        self.SetVisiblePolicy(wx.stc.STC_VISIBLE_STRICT,1)
        
        self.CmdKeyClear(wx.stc.STC_KEY_ADD, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.stc.STC_KEY_SUBTRACT, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyAssign(wx.stc.STC_KEY_PRIOR, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(wx.stc.STC_KEY_NEXT, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMOUT)
        self.Bind(wx.stc.EVT_STC_ZOOM, self.OnUpdateLineNumberMarginWidth)  # auto update line num width on zoom
        wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
        wx.EVT_KILL_FOCUS(self, self.OnKillFocus)
        wx.EVT_SET_FOCUS(self, self.OnFocus)
        self.SetMargins(0,0)

        self.SetUseTabs(0)
        self.SetTabWidth(4)
        self.SetIndent(4)

        self.SetViewWhiteSpace(False)
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetEdgeMode(wx.stc.STC_EDGE_NONE)
        self.SetEdgeColumn(78)

        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())

        self.UpdateStyles()

        self.SetCaretForeground("BLACK")
        
        self.SetViewDefaults()
        font, color = self.GetFontAndColorFromConfig()

        self.SetFont(font)
        self.SetFontColor(color)
        
        self.SetLineNumberStyle()
        self.MarkerDefineDefault()
        self.SetCaretLineColor((210,210,210),)
        self.SetEdgeMode(wx.stc.STC_EDGE_LINE)

        # for multisash initialization   
        if isinstance(parent, wx.lib.multisash.MultiClient):     
            while parent.GetParent():    
                parent = parent.GetParent()      
                if hasattr(parent, "GetView"):   
                    break        
            if hasattr(parent, "GetView"):       
                textEditor = parent.GetView()._textEditor        
                if textEditor:   
                    doc = textEditor.GetDocPointer()     
                    if doc:      
                        self.SetDocPointer(doc)

    def OnFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return            
        self.SetSelBackground(1, "BLUE")
        self.SetSelForeground(1, "WHITE")
        if hasattr(self, "_dynSash"):
            self._dynSash._view.SetCtrl(self)
        event.Skip()

    def OnKillFocus(self, event):
        # wxBug: On Mac, the STC control may fire a focus/kill focus event
        # on shutdown even if the control is in an invalid state. So check
        # before handling the event.
        if self.IsBeingDeleted():
            return
        self.SetSelBackground(0, "BLUE")
        self.SetSelForeground(0, "WHITE")
        self.SetSelBackground(1, "#C0C0C0")
        # Don't set foreground color, use syntax highlighted default colors.
        event.Skip()
        
    def SetViewDefaults(self, configPrefix="Text", hasWordWrap=True, hasTabs=False, hasFolding=False):
        config = wx.ConfigBase_Get()
        self.SetViewWhiteSpace(config.ReadInt(configPrefix + "EditorViewWhitespace", False))
        self.SetViewEOL(config.ReadInt(configPrefix + "EditorViewEOL", False))
        self.SetIndentationGuides(config.ReadInt(configPrefix + "EditorViewIndentationGuides", False))
        self.SetViewRightEdge(config.ReadInt(configPrefix + "EditorViewRightEdge", False))
        self.SetViewLineNumbers(config.ReadInt(configPrefix + "EditorViewLineNumbers", True))
        if hasFolding:
            self.SetViewFolding(config.ReadInt(configPrefix + "EditorViewFolding", True))
        if hasWordWrap:
            self.SetWordWrap(config.ReadInt(configPrefix + "EditorWordWrap", False))
        if hasTabs:  # These methods do not exist in STCTextEditor and are meant for subclasses
            self.SetUseTabs(config.ReadInt(configPrefix + "EditorUseTabs", False))
            self.SetIndent(config.ReadInt(configPrefix + "EditorIndentWidth", 4))
            self.SetTabWidth(config.ReadInt(configPrefix + "EditorIndentWidth", 4))
        else:
            self.SetUseTabs(True)
            self.SetIndent(4)
            self.SetTabWidth(4)

    def GetDefaultFont(self):
        """ Subclasses should override this """
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
            return wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font)
        else:
            return wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

    def GetDefaultColor(self):
        """ Subclasses should override this """
        return wx.BLACK

    def GetFontAndColorFromConfig(self, configPrefix = "Text"):
        font = self.GetDefaultFont()
        config = wx.ConfigBase_Get()
        fontData = config.Read(configPrefix + "EditorFont", "")
        if fontData:
            nativeFont = wx.NativeFontInfo()
            nativeFont.FromString(fontData)
            font.SetNativeFontInfo(nativeFont)
        color = self.GetDefaultColor()
        colorData = config.Read(configPrefix + "EditorColor", "")
        if colorData:
            red = int("0x" + colorData[0:2], 16)
            green = int("0x" + colorData[2:4], 16)
            blue = int("0x" + colorData[4:6], 16)
            color = wx.Colour(red, green, blue)
        return font, color

    def GetFont(self):
        return self._font
        
    def SetFont(self, font):
        self._font = font
        self.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, self._font)
        
    def GetFontColor(self):
        return self._fontColor

    def SetFontColor(self, fontColor = wx.BLACK):
        self._fontColor = fontColor
        self.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, "#%02x%02x%02x" % (self._fontColor.Red(), self._fontColor.Green(), self._fontColor.Blue()))

    def SetLineNumberStyle(self):
        self.UpdateStyles()
        faces = { 'font' : self.GetFont().GetFaceName(),
          'size' : self.GetFont().GetPointSize(),
          'size2': self.GetFont().GetPointSize()-2,
          'color' : "%02x%02x%02x" % (self.GetFontColor().Red(), self.GetFontColor().Green(), self.GetFontColor().Blue())
        }
        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "face:%(font)s,back:#C0C0C0,face:%(font)s,size:%(size2)d" % faces)
        
    def UpdateStyles(self):
        self.StyleClearAll()
        return

    def EstimatedLineNumberMarginWidth(self):
        lineNum = self.GetLineCount()
        baseNumbers = " %d " % (lineNum)
        lineNum = lineNum/100
        while lineNum >= 10:
            lineNum = lineNum/10
            baseNumbers = baseNumbers + " "
        return self.TextWidth(wx.stc.STC_STYLE_LINENUMBER, baseNumbers) 

    def OnUpdateLineNumberMarginWidth(self, event):
        self.UpdateLineNumberMarginWidth()
            
    def UpdateLineNumberMarginWidth(self):
        if self.GetViewLineNumbers():
            self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())
        
    def MarkerDefineDefault(self):
        """ This must be called after the textcontrol is instantiated """
        self.MarkerDefine(TextView.MARKER_NUM, wx.stc.STC_MARK_ROUNDRECT, wx.BLACK, wx.BLUE)

    def OnClear(self):
        # Used when Delete key is hit.
        sel = self.GetSelection()              
        # Delete the selection or if no selection, the character after the caret.
        if sel[0] == sel[1]:
            self.SetSelection(sel[0], sel[0] + 1)
        else:
            # remove any folded lines also.
            startLine = self.LineFromPosition(sel[0])
            endLine = self.LineFromPosition(sel[1])
            endLineStart = self.PositionFromLine(endLine)
            if startLine != endLine and sel[1] - endLineStart == 0:
                while not self.GetLineVisible(endLine):
                    endLine += 1
                self.SetSelectionEnd(self.PositionFromLine(endLine))          
        self.Clear()

    def OnPaste(self):
        # replace any folded lines also.
        sel = self.GetSelection()
        startLine = self.LineFromPosition(sel[0])
        endLine = self.LineFromPosition(sel[1])
        endLineStart = self.PositionFromLine(endLine)
        if startLine != endLine and sel[1] - endLineStart == 0:
            while not self.GetLineVisible(endLine):
                endLine += 1
            self.SetSelectionEnd(self.PositionFromLine(endLine))
        self.Paste()
        
    def OnKeyPressed(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_NUMPAD_ADD:  #wxBug: For whatever reason, the key accelerators for numpad add and subtract with modifiers are not working so have to trap them here
            if event.ControlDown():
                self.ToggleFoldAll(expand = True, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = True)
            else:
                self.ToggleFold(self.GetCurrentLine())
        elif key == wx.WXK_NUMPAD_SUBTRACT:
            if event.ControlDown():
                self.ToggleFoldAll(expand = False, topLevelOnly = True)
            elif event.ShiftDown():
                self.ToggleFoldAll(expand = False)
            else:
                self.ToggleFold(self.GetCurrentLine())
        else:
            event.Skip()

    #----------------------------------------------------------------------------
    # View Text methods
    #----------------------------------------------------------------------------
    def GetViewRightEdge(self):
        return self.GetEdgeMode() != wx.stc.STC_EDGE_NONE

    def SetViewRightEdge(self, viewRightEdge):
        if viewRightEdge:
            self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        else:
            self.SetEdgeMode(wx.stc.STC_EDGE_NONE)

    def GetViewLineNumbers(self):
        return self.GetMarginWidth(1) > 0

    def SetViewLineNumbers(self, viewLineNumbers = True):
        if viewLineNumbers:
            self.SetMarginWidth(1, self.EstimatedLineNumberMarginWidth())
        else:
            self.SetMarginWidth(1, 0)

    def GetViewFolding(self):
        return self.GetMarginWidth(2) > 0

    def SetViewFolding(self, viewFolding = True):
        if viewFolding:
            self.SetMarginWidth(2, 12)
        else:
            self.SetMarginWidth(2, 0)

    def CanWordWrap(self):
        return True

    def GetWordWrap(self):
        return self.GetWrapMode() == wx.stc.STC_WRAP_WORD

    def SetWordWrap(self, wordWrap):
        if wordWrap:
            self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        else:
            self.SetWrapMode(wx.stc.STC_WRAP_NONE)

    def AddText(self,text):
        try:
            wx.stc.StyledTextCtrl.AddText(self,text)
        except:
            wx.stc.StyledTextCtrl.AddText(self,text.decode("utf-8"))

    def HasSelection(self):
        return self.GetSelectionStart() - self.GetSelectionEnd() != 0  
    #----------------------------------------------------------------------------
    # DynamicSashWindow methods
    #----------------------------------------------------------------------------

    def SetupDSScrollBars(self):
        # hook the scrollbars provided by the wxDynamicSashWindow
        # to this view
        v_bar = self._dynSash.GetVScrollBar(self)
        h_bar = self._dynSash.GetHScrollBar(self)
        v_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        h_bar.Bind(wx.EVT_SCROLL, self.OnDSSBScroll)
        v_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)
        h_bar.Bind(wx.EVT_SET_FOCUS, self.OnDSSBFocus)

        # And set the wxStyledText to use these scrollbars instead
        # of its built-in ones.
        self.SetVScrollBar(v_bar)
        self.SetHScrollBar(h_bar)


    def OnDSSplit(self, evt):
        newCtrl = self._dynSash._view.GetCtrlClass()(self._dynSash, -1, style=wx.NO_BORDER)
        newCtrl.SetDocPointer(self.GetDocPointer())     # use the same document
        self.SetupDSScrollBars()
        if self == self._dynSash._view.GetCtrl():  # originally had focus
            wx.CallAfter(self.SetFocus)  # do this to set colors correctly.  wxBug:  for some reason, if we don't do a CallAfter, it immediately calls OnKillFocus right after our SetFocus.


    def OnDSUnify(self, evt):
        self.SetupDSScrollBars()
        self.SetFocus()  # do this to set colors correctly


    def OnDSSBScroll(self, evt):
        # redirect the scroll events from the _dynSash's scrollbars to the STC
        self.GetEventHandler().ProcessEvent(evt)


    def OnDSSBFocus(self, evt):
        # when the scrollbar gets the focus move it back to the STC
        self.SetFocus()


    def DSProcessEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            if event.GetId() == wx.ID_SELECTALL:
                # force focus so that select all occurs in the window user right clicked on.
                self.SetFocus()

            return self._dynSash._view.ProcessEvent(event)
        return False


    def DSProcessUpdateUIEvent(self, event):
        # wxHack: Needed for customized right mouse click menu items.        
        if hasattr(self, "_dynSash"):
            id = event.GetId()
            if (id == wx.ID_SELECTALL  # allow select all even in non-active window, then force focus to it, see above ProcessEvent
            or id == wx.ID_UNDO
            or id == wx.ID_REDO):
                pass  # allow these actions even in non-active window
            else:  # disallow events in non-active windows.  Cut/Copy/Paste/Delete is too confusing user experience.
                if self._dynSash._view.GetCtrl() != self:
                     event.Enable(False)
                     return True

            return self._dynSash._view.ProcessUpdateUIEvent(event)
        return False

    def SetCaretLineColor(self,color):
        self.SetCaretLineVisible(True)
        self.SetCaretLineBack(color)

    def IsCaretLocateInWord(self):
        return False

    def IsListMemberFlag(self,pos):
        return False
         
class TextPrintout(wx.lib.docview.DocPrintout):
    """ for Print Preview and Print """
    

    def OnPreparePrinting(self):
        """ initialization """
        dc = self.GetDC()

        ppiScreenX, ppiScreenY = self.GetPPIScreen()
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        scaleX = float(ppiPrinterX)/ppiScreenX
        scaleY = float(ppiPrinterY)/ppiScreenY

        pageWidth, pageHeight = self.GetPageSizePixels()
        self._scaleFactorX = scaleX/pageWidth
        self._scaleFactorY = scaleY/pageHeight

        w, h = dc.GetSize()
        overallScaleX = self._scaleFactorX * w
        overallScaleY = self._scaleFactorY * h
        
        txtCtrl = self._printoutView.GetCtrl()
        font, color = txtCtrl.GetFontAndColorFromConfig()

        self._margin = 40
        self._fontHeight = font.GetPointSize() + 1
        self._pageLines = int((h/overallScaleY - (2 * self._margin))/self._fontHeight)
        self._maxLines = txtCtrl.GetLineCount()
        self._numPages, remainder = divmod(self._maxLines, self._pageLines)
        if remainder != 0:
            self._numPages += 1

        spaces = 1
        lineNum = self._maxLines
        while lineNum >= 10:
            lineNum = lineNum/10
            spaces += 1
        self._printFormat = "%%0%sd: %%s" % spaces


    def OnPrintPage(self, page):
        """ Prints the given page of the view """
        dc = self.GetDC()
        
        txtCtrl = self._printoutView.GetCtrl()
        font, color = txtCtrl.GetFontAndColorFromConfig()
        dc.SetFont(font)
        
        w, h = dc.GetSize()
        dc.SetUserScale(self._scaleFactorX * w, self._scaleFactorY * h)
        
        dc.BeginDrawing()
        
        dc.DrawText("%s - page %s" % (self.GetTitle(), page), self._margin, self._margin/2)

        startY = self._margin
        startLine = (page - 1) * self._pageLines
        endLine = min((startLine + self._pageLines), self._maxLines)
        for i in range(startLine, endLine):
            text = txtCtrl.GetLine(i).rstrip()
            startY += self._fontHeight
            if txtCtrl.GetViewLineNumbers():
                dc.DrawText(self._printFormat % (i+1, text), self._margin, startY)
            else:
                dc.DrawText(text, self._margin, startY)
                
        dc.EndDrawing()

        return True


    def HasPage(self, pageNum):
        return pageNum <= self._numPages


    def GetPageInfo(self):
        minPage = 1
        maxPage = self._numPages
        selPageFrom = 1
        selPageTo = self._numPages
        return (minPage, maxPage, selPageFrom, selPageTo)

        
#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import ImageFromStream, BitmapFromImage
import cStringIO


def getTextData():
    return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x015IDAT8\x8d\xad\x90\xb1N\xc2P\x14\x86\xbf\x02/\xe0\xec#\x18g\xc3\xe6T\
\x13':1\x18H\x98\x14\x12\x17G\x177\x17\x9c4a\xc5\xc0d0\xc2\xccdLx\x02^@+\t\
\xc1\x90\xf6r\xdb\xc6\x94\xe5:\\\xdbP)\xc5DOr\x92\x9b{\xff\xfb\xfd\xff9\xc6h\
l+\xbek.\x02\x00\xec\x99\x03\x80\xeb\xf8\\\x9d\x1d\x1bd\xd5hl\xab\xd7O\x15\
\xf7x\xa1\xfb\xeeq\xa4^>\x94\xba\xb8yRF.\xcf\xa6.D\xa0Nw\x18C\xad\xb2\x19\
\x9f\x0f\xca\x165\xd1V\xed\xebZj\x92\xc2\\\x04\xec\x02\xd5\x8a\x89\xb7\xd4\
\x97n\xa8\xe3?\x0f\x86\x08\x19dNP\x00\xf0\x96\xd0\x7f\xd0\t\x84\x0c(U-\x0eK&\
\xd3P\x8bz\xcdV6 \x8a\xed\x86\x99f\xe9\x00{\xe6\xb0\x13\xc2\xa0\xd3\xd7\t\
\x84\x9f\x10\xec\x9dTp\x1d\xb1=A\xa9j\x01\xc4\xb1\x01&\xfe\x9a~\x1d\xe0:Zu\
\x7f\xdb\x05@J/!(\xd6\x1bL\xde\xec\xcd\x00!\x03\xa6!\x1c\x9dVR\x9d\xdf\xe5\
\x96\x04\xd1au\xd3\xab3\xef\x9f_f\x03\xa2\xa5\x15\xeb\x8d\xc4\xc36\xe7\x18 \
\xa5G\xaf\xd9J\xb8f\xcd\xfc\xb3\x0c#\x97\xff\xb58\xadr\x7f\xfa\xfd\x1f\x80/\
\x04\x1f\x8fW\x0e^\xc3\x12\x00\x00\x00\x00IEND\xaeB`\x82" 


def getTextBitmap():
    return BitmapFromImage(getTextImage())

def getTextImage():
    stream = cStringIO.StringIO(getTextData())
    return ImageFromStream(stream)

def getTextIcon():
    return wx.IconFromBitmap(getTextBitmap())





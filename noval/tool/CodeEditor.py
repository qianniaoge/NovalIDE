#----------------------------------------------------------------------------
# Name:         CodeEditor.py
# Purpose:      Abstract Code Editor for pydocview tbat uses the Styled Text Control
#
# Author:       Peter Yared
#
# Created:      8/10/03
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------


import STCTextEditor
import wx
import wx.lib.docview
import OutlineService
import os
import re
import string
import sys
import MarkerService
from UICommon import CaseInsensitiveCompare
import noval.parser.nodeast as nodeast
import noval.parser.intellisence as intellisence
import noval.parser.config as parserconfig
import FindService
import DebugOutputCtrl
import TextService
import noval.util.sysutils as sysutilslib
import EOLFormat
import CompletionService
_ = wx.GetTranslation

ENABLE_FOLD_ID = wx.NewId()
EXPAND_TEXT_ID = wx.NewId()
COLLAPSE_TEXT_ID = wx.NewId()
EXPAND_TOP_ID = wx.NewId()
COLLAPSE_TOP_ID = wx.NewId()
EXPAND_ALL_ID = wx.NewId()
COLLAPSE_ALL_ID = wx.NewId()
CHECK_CODE_ID = wx.NewId()
CLEAN_WHITESPACE = wx.NewId()
COMMENT_LINES_ID = wx.NewId()
UNCOMMENT_LINES_ID = wx.NewId()
INDENT_LINES_ID = wx.NewId()
DEDENT_LINES_ID = wx.NewId()
USE_TABS_ID = wx.NewId()
SET_INDENT_WIDTH_ID = wx.NewId()
FOLDING_ID = wx.NewId()
ID_EOL_MODE      = wx.NewId()
ID_EOL_MAC       = wx.NewId()
ID_EOL_UNIX      = wx.NewId()
ID_EOL_WIN       = wx.NewId()

MODE_MAP = { 
    ID_EOL_MAC  : wx.stc.STC_EOL_CR,
    ID_EOL_UNIX : wx.stc.STC_EOL_LF,
    ID_EOL_WIN  : wx.stc.STC_EOL_CRLF
}


class CodeDocument(STCTextEditor.TextDocument):
    def OnOpenDocument(self, filename):
        if not STCTextEditor.TextDocument.OnOpenDocument(self,filename):
            return False
        view = self.GetFirstView()
        check_eol = wx.ConfigBase_Get().ReadInt("CheckEOL", False)
        if check_eol:
            view.GetCtrl().CheckEOL()
        return True

class CodeView(STCTextEditor.TextView):


    #----------------------------------------------------------------------------
    # Overridden methods
    #----------------------------------------------------------------------------


    def GetCtrlClass(self):
        """ Used in split window to instantiate new instances """
        return CodeCtrl


    def ProcessEvent(self, event):
        id = event.GetId()
        if id == FindService.FindService.REPLACEONE_ID or id == FindService.FindService.FINDONE_ID or\
                id == FindService.FindService.REPLACEALL_ID:
            return STCTextEditor.TextView.ProcessEvent(self, event)            
        focus_ctrl = wx.Window_FindFocus()
        if not isinstance(focus_ctrl,CodeCtrl):
            if isinstance(focus_ctrl,DebugOutputCtrl.DebugOutputCtrl) and id in DebugOutputCtrl.DebugOutputCtrl.ItemIDs:
                return focus_ctrl.DSProcessEvent(event)
            return wx.lib.docview.View.ProcessEvent(self,event)
        if id == EXPAND_TEXT_ID:
            self.GetCtrl().ToggleFold(self.GetCtrl().GetCurrentLine())
            return True
        elif id == COLLAPSE_TEXT_ID:
            self.GetCtrl().ToggleFold(self.GetCtrl().GetCurrentLine())
            return True
        elif id == EXPAND_TOP_ID:
            self.GetCtrl().ToggleFoldAll(expand = True, topLevelOnly = True)
            return True
        elif id == COLLAPSE_TOP_ID:
            self.GetCtrl().ToggleFoldAll(expand = False, topLevelOnly = True)
            return True
        elif id == EXPAND_ALL_ID:
            self.GetCtrl().ToggleFoldAll(expand = True)
            return True
        elif id == COLLAPSE_ALL_ID:
            self.GetCtrl().ToggleFoldAll(expand = False)
            return True
        elif id == CHECK_CODE_ID:
            self.OnCheckCode()
            return True
        elif id == CompletionService.CompletionService.AUTO_COMPLETE_ID:
            self.OnAutoComplete()
            return True
        elif id == CLEAN_WHITESPACE:
            self.OnCleanWhiteSpace()
            return True
        elif id == SET_INDENT_WIDTH_ID:
            self.OnSetIndentWidth()
            return True
        elif id == USE_TABS_ID:
            self.GetCtrl().SetUseTabs(not self.GetCtrl().GetUseTabs())
            return True
        elif id == INDENT_LINES_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_TAB)
            return True
        elif id == DEDENT_LINES_ID:
            self.GetCtrl().CmdKeyExecute(wx.stc.STC_CMD_BACKTAB)
            return True
        elif id == COMMENT_LINES_ID:
            self.OnCommentLines()
            return True
        elif id == UNCOMMENT_LINES_ID:
            self.OnUncommentLines()
            return True
        elif id == ENABLE_FOLD_ID:
            self.GetCtrl().SetViewFolding(not self.GetCtrl().GetViewFolding())
            return True
        elif id == ID_EOL_MAC or id == ID_EOL_UNIX or id == ID_EOL_WIN:
            self.GetCtrl().ConvertLineMode(id)
            return True
        else:
            return STCTextEditor.TextView.ProcessEvent(self, event)


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == FindService.FindService.REPLACEONE_ID or id == FindService.FindService.FINDONE_ID or\
                id == FindService.FindService.REPLACEALL_ID:
            return STCTextEditor.TextView.ProcessUpdateUIEvent(self, event)
        focus_ctrl = wx.Window_FindFocus()
        if not isinstance(focus_ctrl,CodeCtrl):
            if isinstance(focus_ctrl,DebugOutputCtrl.DebugOutputCtrl) and id in DebugOutputCtrl.DebugOutputCtrl.ItemIDs:
                return focus_ctrl.DSProcessUpdateUIEvent(event)
            return False
        if not self.GetCtrl():
           return False                
        if id == EXPAND_TEXT_ID:
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().CanLineExpand(self.GetCtrl().GetCurrentLine()))
            else:
                event.Enable(False)
            return True
        elif id == COLLAPSE_TEXT_ID:
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().CanLineCollapse(self.GetCtrl().GetCurrentLine()))
            else:
                event.Enable(False)
            return True
        elif (id == EXPAND_TOP_ID
        or id == COLLAPSE_TOP_ID
        or id == EXPAND_ALL_ID
        or id == COLLAPSE_ALL_ID):
            if self.GetCtrl().GetViewFolding():
                event.Enable(self.GetCtrl().GetTextLength() > 0)
            else:
                event.Enable(False)
            return True            
        elif (id == CompletionService.CompletionService.AUTO_COMPLETE_ID
        or id == CLEAN_WHITESPACE
        or id == INDENT_LINES_ID
        or id == DEDENT_LINES_ID
        or id == COMMENT_LINES_ID
        or id == UNCOMMENT_LINES_ID):
            event.Enable(self.GetCtrl().GetTextLength() > 0)
            return True
        elif id == CHECK_CODE_ID:
            event.Enable(False)
            return True
        elif id == SET_INDENT_WIDTH_ID:
            event.Enable(True)
            return True
        elif id == FOLDING_ID:
            event.Enable(True)
            return True
        elif id == USE_TABS_ID:
            event.Enable(True)
            event.Check(self.GetCtrl().GetUseTabs())
            return True
        elif id == ENABLE_FOLD_ID:
            event.Enable(True)
            event.Check(self.GetCtrl().GetViewFolding())
            return True
        elif id == ID_EOL_MODE:
            event.Enable(True)
            return True
        elif id == ID_EOL_MAC or id == ID_EOL_UNIX or id == ID_EOL_WIN:
            event.Enable(True)
            event.Check(self.GetCtrl().IsEOLModeId(id))
            return True
        else:
            return STCTextEditor.TextView.ProcessUpdateUIEvent(self, event)
    #----------------------------------------------------------------------------
    # Methods for OutlineService
    #----------------------------------------------------------------------------

    def OnChangeFilename(self):
        wx.lib.docview.View.OnChangeFilename(self)
        if self.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER:
            self.LoadOutline(force=True)
        

    def ClearOutline(self):
        outlineService = wx.GetApp().GetService(OutlineService.OutlineService)
        if not outlineService:
            return

        outlineView = outlineService.GetView()
        if not outlineView:
            return

        outlineView.ClearTreeCtrl()


    def LoadOutline(self, force=False):
        outlineService = wx.GetApp().GetService(OutlineService.OutlineService)
        if not outlineService:
            return
        outlineService.LoadOutline(self, force=force)

    def DoLoadOutlineCallback(self, force=False):
        return False

    def DoSelectCallback(self, node):
        if node and not isinstance(node,nodeast.Module):
            #must enable node line to see
            self.EnsureVisibleEnforcePolicy(node.Line)
            # wxBug: need to select in reverse order (end, start) to place cursor at begining of line,
            #        otherwise, display is scrolled over to the right hard and is hard to view
            if node.Type == parserconfig.NODE_IMPORT_TYPE and node.Parent.Type == parserconfig.NODE_FROMIMPORT_TYPE:
                line = node.Line
                name = node.Name
                line_count = self.GetCtrl().GetLineCount()
                #search from xx import yy as zz
                if node.AsName != None:
                    name = node.AsName
                    col = self.GetCtrl().GetLine(line-1).find(" as ")
                    start,end = self.FindTextInLine(name,line,col)
                    while start == -1 and line < line_count:
                        line += 1
                        col = self.GetCtrl().GetLine(line-1).find(" as ")
                        if col == -1:
                            continue
                        start,end = self.FindTextInLine(name,line,col)
                        if self.GetCtrl().GetLine(line).strip().endswith(")"):
                            break
                #search from xx import yy
                else:
                    col = self.GetCtrl().GetLine(line-1).find(" import ")
                    start,end = self.FindTextInLine(name,line,col)
                    col = 0
                    while start == -1 and line < line_count:
                        line += 1
                        start,end = self.FindTextInLine(name,line,col)
                        if self.GetCtrl().GetLine(line).strip().endswith(")"):
                            break
            #search import xx as yy
            elif node.Type == parserconfig.NODE_IMPORT_TYPE and node.AsName != None:
                col = self.GetCtrl().GetLine(node.Line-1).find(" as ")
                start,end = self.FindTextInLine(node.AsName,node.Line,col)
            else:
                start,end = self.FindTextInLine(node.Name,node.Line)
            if start == -1 or end == -1:
                return
            self.SetSelection(start, end)

##    def checksum(self, bytes):        
##        def rotate_right(c):
##            if c&1:
##                return (c>>1)|0x8000
##            else:
##                return c>>1
##                
##        result = 0
##        for ch in bytes:
##            ch = ord(ch) & 0xFF
##            result = (rotate_right(result)+ch) & 0xFFFF
##        return result
##

    def GenCheckSum(self):
        """ Poor man's checksum.  We'll assume most changes will change the length of the file.
        """
        text = self.GetValue()
        if text:
            return len(text)
        else:
            return 0


    #----------------------------------------------------------------------------
    # Format methods
    #----------------------------------------------------------------------------

    def OnCheckCode(self):
        """ Need to overshadow this for each specific subclass """
        if 0:
            try:
                code = self.GetCtrl().GetText()
                codeObj = compile(code, self.GetDocument().GetFilename(), 'exec')
                self._GetParentFrame().SetStatusText(_("The file successfully compiled"))
            except SyntaxError, (message, (fileName, line, col, text)):
                pos = self.GetCtrl().PositionFromLine(line - 1) + col - 1
                self.GetCtrl().SetSelection(pos, pos)
                self._GetParentFrame().SetStatusText(_("Syntax Error: %s") % message)
            except:
                self._GetParentFrame().SetStatusText("%s: %s" % (sys.exc_info()[0], sys.exc_info()[1]))


    def OnAutoComplete(self):
        self.GetCtrl().AutoCompCancel()
        self.GetCtrl().AutoCompSetAutoHide(0)
        self.GetCtrl().AutoCompSetChooseSingle(True)
        self.GetCtrl().AutoCompSetIgnoreCase(True)
        context, hint = self.GetAutoCompleteHint()
        replaceList, replaceLen = self.GetAutoCompleteKeywordList(context, hint,self.GetCtrl().GetCurrentLine())
        if replaceList and len(replaceList) != 0: 
            self.GetCtrl().AutoCompShow(replaceLen, replaceList)


    def GetAutoCompleteHint(self):
        """ Replace this method with Editor specific method """
        pos = self.GetCtrl().GetCurrentPos()
        if pos == 0:
            return None, None
        if chr(self.GetCtrl().GetCharAt(pos - 1)) == '.':
            pos = pos - 1
            hint = None
        else:
            hint = ''
            
        validLetters = string.letters + string.digits + '_.'
        word = ''
        while (True):
            pos = pos - 1
            if pos < 0:
                break
            char = chr(self.GetCtrl().GetCharAt(pos))
            if char not in validLetters:
                break
            word = char + word
            
        context = word
        if hint is not None:            
            lastDot = word.rfind('.')
            if lastDot != -1:
                context = word[0:lastDot]
                hint = word[lastDot+1:]
                    
        return context, hint
        

    def GetAutoCompleteDefaultKeywords(self):
        """ Replace this method with Editor specific keywords """
        return ['Put', 'Editor Specific', 'Keywords', 'Here']


    def GetAutoCompleteKeywordList(self, context, hint,line):            
        """ Replace this method with Editor specific keywords """
        kw = self.GetAutoCompleteDefaultKeywords()
        
        if hint and len(hint):
            lowerHint = hint.lower()
            filterkw = filter(lambda item: item.lower().startswith(lowerHint), kw)  # remove variables and methods that don't match hint
            kw = filterkw

        if hint:
            replaceLen = len(hint)
        else:
            replaceLen = 0
            
        kw.sort(CaseInsensitiveCompare)
        return " ".join(kw), replaceLen
        

    def OnCleanWhiteSpace(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = string.rstrip(self.GetCtrl().GetLine(lineNo))
            indent = 0
            lstrip = 0
            for char in lineText:
                if char == '\t':
                    indent = indent + self.GetCtrl().GetIndent()
                    lstrip = lstrip + 1
                elif char in string.whitespace:
                    indent = indent + 1
                    lstrip = lstrip + 1
                else:
                    break
            if self.GetCtrl().GetUseTabs():
                indentText = (indent / self.GetCtrl().GetIndent()) * '\t' + (indent % self.GetCtrl().GetIndent()) * ' '
            else:
                indentText = indent * ' '
            lineText = indentText + lineText[lstrip:] + '\n'
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)


    def OnSetIndentWidth(self):
        dialog = wx.TextEntryDialog(self._GetParentFrame(), _("Enter new indent width (2-10):"), _("Set Indent Width"), "%i" % self.GetCtrl().GetIndent())
        dialog.CenterOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            try:
                indent = int(dialog.GetValue())
                if indent >= 2 and indent <= 10:
                    self.GetCtrl().SetIndent(indent)
                    self.GetCtrl().SetTabWidth(indent)
            except:
                pass
        dialog.Destroy()


    def GetIndentWidth(self):
        return self.GetCtrl().GetIndent()
                

    def OnCommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if (len(lineText) > 1 and lineText[0] == '#') or (len(lineText) > 2 and lineText[:2] == '##'):
                newText = newText + lineText
            else:
                newText = newText + "##" + lineText
        self._ReplaceSelectedLines(newText)


    def OnUncommentLines(self):
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetCtrl().GetLine(lineNo)
            if len(lineText) >= 2 and lineText[:2] == "##":
                lineText = lineText[2:]
            elif len(lineText) >= 1 and lineText[:1] == "#":
                lineText = lineText[1:]
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)


    def _GetSelectedLineNumbers(self):
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        return range(self.GetCtrl().LineFromPosition(selStart), self.GetCtrl().LineFromPosition(selEnd))


    def _GetPositionsBoundingSelectedLines(self):
        startPos = self.GetCtrl().GetCurrentPos()
        endPos = self.GetCtrl().GetAnchor()
        if startPos > endPos:
            temp = endPos
            endPos = startPos
            startPos = temp
        if endPos == self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(endPos)):
            endPos = endPos - 1  # If it's at the very beginning of a line, use the line above it as the ending line
        selStart = self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(startPos))
        selEnd = self.GetCtrl().PositionFromLine(self.GetCtrl().LineFromPosition(endPos) + 1)
        return selStart, selEnd


    def _ReplaceSelectedLines(self, text):
        if len(text) == 0:
            return
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        self.GetCtrl().SetSelection(selStart, selEnd)
        self.GetCtrl().ReplaceSelection(text)
        self.GetCtrl().SetSelection(selStart + len(text), selStart)


    def OnUpdate(self, sender = None, hint = None):
        if wx.lib.docview.View.OnUpdate(self, sender, hint):
            return

        if hint == "ViewStuff":
            self.GetCtrl().SetViewDefaults()
        elif hint == "Font":
            font, color = self.GetCtrl().GetFontAndColorFromConfig()
            self.GetCtrl().SetFont(font)
            self.GetCtrl().SetFontColor(color)
        else:
            import DebuggerService
            dbg_service = wx.GetApp().GetService(DebuggerService.DebuggerService)
            if dbg_service:
                dbg_service.SetCurrentBreakpointMarkers(self)


class CodeService(TextService.TextService):


    def __init__(self):
        TextService.TextService.__init__(self)


    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        # TODO NEED TO DO INSTANCEOF CHECK HERE FOR SDI
        #if document and document.GetDocumentTemplate().GetDocumentType() != TextDocument:
        #    return
        if not document and wx.GetApp().GetDocumentManager().GetFlags() & wx.lib.docview.DOC_SDI:
            return

        viewMenu = menuBar.GetMenu(menuBar.FindMenu(_("&View")))
      ###  isWindows = (wx.Platform == '__WXMSW__')

        if not menuBar.FindItemById(EXPAND_TEXT_ID):  # check if below menu items have been already been installed
            foldingMenu = wx.Menu()
            foldingMenu.AppendCheckItem(ENABLE_FOLD_ID, _("&Use Fold Style"), _("Show or hide fold index"))
            wx.EVT_MENU(frame, ENABLE_FOLD_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ENABLE_FOLD_ID, frame.ProcessUpdateUIEvent)
            if sysutilslib.isWindows():
                foldingMenu.Append(EXPAND_TEXT_ID, _("&Expand\tNumpad-Plus"), _("Expands a collapsed block of text"))
            else:
                foldingMenu.Append(EXPAND_TEXT_ID, _("&Expand"), _("Expands a collapsed block of text"))

            wx.EVT_MENU(frame, EXPAND_TEXT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, EXPAND_TEXT_ID, frame.ProcessUpdateUIEvent)
            
            if sysutilslib.isWindows():
                foldingMenu.Append(COLLAPSE_TEXT_ID, _("&Collapse\tNumpad+Minus"), _("Collapse a block of text"))
            else:
                foldingMenu.Append(COLLAPSE_TEXT_ID, _("&Collapse"), _("Collapse a block of text"))
            wx.EVT_MENU(frame, COLLAPSE_TEXT_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, COLLAPSE_TEXT_ID, frame.ProcessUpdateUIEvent)
            
            if sysutilslib.isWindows():
                foldingMenu.Append(EXPAND_TOP_ID, _("Expand &Top Level\tCtrl+Numpad+Plus"), _("Expands the top fold levels in the document"))
            else:
                foldingMenu.Append(EXPAND_TOP_ID, _("Expand &Top Level"), _("Expands the top fold levels in the document"))
            wx.EVT_MENU(frame, EXPAND_TOP_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, EXPAND_TOP_ID, frame.ProcessUpdateUIEvent)
            
            if sysutilslib.isWindows():
                foldingMenu.Append(COLLAPSE_TOP_ID, _("Collapse Top &Level\tCtrl+Numpad+Minus"), _("Collapses the top fold levels in the document"))
            else:
                foldingMenu.Append(COLLAPSE_TOP_ID, _("Collapse Top &Level"), _("Collapses the top fold levels in the document"))
            wx.EVT_MENU(frame, COLLAPSE_TOP_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, COLLAPSE_TOP_ID, frame.ProcessUpdateUIEvent)
            
            if sysutilslib.isWindows():
                foldingMenu.Append(EXPAND_ALL_ID, _("Expand &All\tShift+Numpad+Plus"), _("Expands all of the fold levels in the document"))
            else:
                foldingMenu.Append(EXPAND_ALL_ID, _("Expand &All"), _("Expands all of the fold levels in the document"))
            wx.EVT_MENU(frame, EXPAND_ALL_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, EXPAND_ALL_ID, frame.ProcessUpdateUIEvent)
            
            if sysutilslib.isWindows():
                foldingMenu.Append(COLLAPSE_ALL_ID, _("Colla&pse All\tShift+Numpad+Minus"), _("Collapses all of the fold levels in the document"))
            else:
                foldingMenu.Append(COLLAPSE_ALL_ID, _("Colla&pse All"), _("Collapses all of the fold levels in the document"))
            wx.EVT_MENU(frame, COLLAPSE_ALL_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, COLLAPSE_ALL_ID, frame.ProcessUpdateUIEvent)
            
            viewMenu.AppendMenu(FOLDING_ID, _("&Folding"), foldingMenu)
            wx.EVT_UPDATE_UI(frame, FOLDING_ID, frame.ProcessUpdateUIEvent)

        formatMenuIndex = menuBar.FindMenu(_("&Format"))
        if formatMenuIndex > -1:
            formatMenu = menuBar.GetMenu(formatMenuIndex)
        else:
            formatMenu = wx.Menu()
        if not menuBar.FindItemById(CHECK_CODE_ID):  # check if below menu items have been already been installed
            formatMenu.AppendSeparator()
            formatMenu.Append(CHECK_CODE_ID, _("&Check Code"), _("Checks the document for syntax and indentation errors"))
            wx.EVT_MENU(frame, CHECK_CODE_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, CHECK_CODE_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(CompletionService.CompletionService.AUTO_COMPLETE_ID, _("&Auto Complete\tCtrl+Shift+Space"), _("Provides suggestions on how to complete the current statement"))
            wx.EVT_MENU(frame, CompletionService.CompletionService.AUTO_COMPLETE_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, CompletionService.CompletionService.AUTO_COMPLETE_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(CLEAN_WHITESPACE, _("Clean &Whitespace"), _("Converts leading spaces to tabs or vice versa per 'use tabs' and clears trailing spaces"))
            wx.EVT_MENU(frame, CLEAN_WHITESPACE, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, CLEAN_WHITESPACE, frame.ProcessUpdateUIEvent)
            formatMenu.AppendSeparator()
            formatMenu.Append(INDENT_LINES_ID, _("&Indent Lines\tTab"), _("Indents the selected lines one indent width"))
            wx.EVT_MENU(frame, INDENT_LINES_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, INDENT_LINES_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(DEDENT_LINES_ID, _("&Dedent Lines\tShift+Tab"), _("Dedents the selected lines one indent width"))
            wx.EVT_MENU(frame, DEDENT_LINES_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, DEDENT_LINES_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(COMMENT_LINES_ID, _("Comment &Lines\tCtrl+Q"), _("Comments out the selected lines be prefixing each one with a comment indicator"))
            wx.EVT_MENU(frame, COMMENT_LINES_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, COMMENT_LINES_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(UNCOMMENT_LINES_ID, _("&Uncomment Lines\tCtrl+Shift+Q"), _("Removes comment prefixes from each of the selected lines"))
            wx.EVT_MENU(frame, UNCOMMENT_LINES_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, UNCOMMENT_LINES_ID, frame.ProcessUpdateUIEvent)
            formatMenu.AppendSeparator()
            formatMenu.AppendCheckItem(USE_TABS_ID, _("Use &Tabs"), _("Toggles use of tabs or whitespaces for indents"))
            wx.EVT_MENU(frame, USE_TABS_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, USE_TABS_ID, frame.ProcessUpdateUIEvent)
            formatMenu.Append(SET_INDENT_WIDTH_ID, _("&Set Indent Width..."), _("Sets the indent width"))
            wx.EVT_MENU(frame, SET_INDENT_WIDTH_ID, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, SET_INDENT_WIDTH_ID, frame.ProcessUpdateUIEvent)
        if formatMenuIndex == -1:
            viewMenuIndex = menuBar.FindMenu(_("&View"))
            menuBar.Insert(viewMenuIndex + 1, formatMenu, _("&Format"))

##        accelTable = wx.AcceleratorTable([
##            (wx.ACCEL_NORMAL, wx.WXK_TAB, INDENT_LINES_ID),
##            (wx.ACCEL_SHIFT, wx.WXK_TAB, DEDENT_LINES_ID),
##            eval(_("wx.ACCEL_CTRL, ord('Q'), COMMENT_LINES_ID")),
##            eval(_("wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord('Q'), UNCOMMENT_LINES_ID"))
##            ])
##        frame.SetAcceleratorTable(accelTable)
        if not menuBar.FindItemById(ID_EOL_MODE):
            lineformat_menu = wx.Menu()
            lineformat_menu.AppendCheckItem(ID_EOL_MAC, _("Old Machintosh (\\r)"),
                              _("Format all EOL characters to %s Mode") % \
                              _(u"Old Machintosh (\\r)"))
            wx.EVT_MENU(frame, ID_EOL_MAC, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ID_EOL_MAC, frame.ProcessUpdateUIEvent)
            lineformat_menu.AppendCheckItem(ID_EOL_UNIX, _("Unix (\\n)"),
                              _("Format all EOL characters to %s Mode") % \
                              _(u"Unix (\\n)"))
            wx.EVT_MENU(frame, ID_EOL_UNIX, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ID_EOL_UNIX, frame.ProcessUpdateUIEvent)
            lineformat_menu.AppendCheckItem(ID_EOL_WIN, _("Windows (\\r\\n)"),
                              _("Format all EOL characters to %s Mode") % \
                              _("Windows (\\r\\n)"))
            wx.EVT_MENU(frame, ID_EOL_WIN, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ID_EOL_WIN, frame.ProcessUpdateUIEvent)
            formatMenu.AppendMenu(ID_EOL_MODE, _("EOL Mode"), lineformat_menu)
            wx.EVT_MENU(frame, ID_EOL_MODE, frame.ProcessEvent)
            wx.EVT_UPDATE_UI(frame, ID_EOL_MODE, frame.ProcessUpdateUIEvent)

    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if (id == EXPAND_TEXT_ID
        or id == COLLAPSE_TEXT_ID
        or id == EXPAND_TOP_ID
        or id == COLLAPSE_TOP_ID
        or id == EXPAND_ALL_ID
        or id == COLLAPSE_ALL_ID
        or id == CHECK_CODE_ID
        or id == CompletionService.CompletionService.AUTO_COMPLETE_ID
        or id == CLEAN_WHITESPACE
        or id == SET_INDENT_WIDTH_ID
        or id == USE_TABS_ID
        or id == INDENT_LINES_ID
        or id == DEDENT_LINES_ID
        or id == COMMENT_LINES_ID
        or id == UNCOMMENT_LINES_ID
        or id == FOLDING_ID
        or id == ENABLE_FOLD_ID
        or id == ID_EOL_UNIX
        or id == ID_EOL_MAC
        or id == ID_EOL_WIN
        or id == ID_EOL_MODE):
            event.Enable(False)
            return True
        else:
            return TextService.TextService.ProcessUpdateUIEvent(self, event)


class CodeCtrl(STCTextEditor.TextCtrl):
    CURRENT_LINE_MARKER_NUM = 2
    BREAKPOINT_MARKER_NUM = 1
    CURRENT_LINE_MARKER_MASK = 0x4
    BREAKPOINT_MARKER_MASK = 0x4
    TYPE_POINT_WORD = "."
    TYPE_BLANK_WORD = " "
    TYPE_IMPORT_WORD = "import"
    TYPE_FROM_WORD = "from"
    DEFAULT_WORD_CHARS = string.letters + string.digits + '_'
    
            
    def __init__(self, parent, id=-1, style = wx.NO_FULL_REPAINT_ON_RESIZE, clearTab=True):
        STCTextEditor.TextCtrl.__init__(self, parent, id, style)
        self.SetMouseDwellTime(900)
        self.UsePopUp(False)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        self.SetMarginSensitive(self.BREAKPOINT_MARKER_NUM, False)
        self.SetMarginMask(self.BREAKPOINT_MARKER_NUM, self.BREAKPOINT_MARKER_MASK)
        
        self.SetMarginSensitive(CodeView.BOOK_MARKER_NUM, True)
        self.SetMarginType(CodeView.BOOK_MARKER_NUM, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(CodeView.BOOK_MARKER_NUM, 0x3)
        self.SetMarginWidth(CodeView.BOOK_MARKER_NUM, CodeView.BOOK_MARGIN_WIDTH)

        # Define the current line marker
        self.MarkerDefine(CodeCtrl.CURRENT_LINE_MARKER_NUM, wx.stc.STC_MARK_SHORTARROW, wx.BLACK, (255,255,128))
        # Define the breakpoint marker
        self.MarkerDefine(CodeCtrl.BREAKPOINT_MARKER_NUM, wx.stc.STC_MARK_CIRCLE, wx.BLACK, (255,0,0))
        
        if sysutilslib.isWindows() and clearTab:  # should test to see if menu item exists, if it does, add this workaround
            self.CmdKeyClear(wx.stc.STC_KEY_TAB, 0)  # menu item "Indent Lines" from CodeService.InstallControls() generates another INDENT_LINES_ID event, so we'll explicitly disable the tab processing in the editor
        #Sets whether when a backspace pressed should do indentation unindents
        self.SetBackSpaceUnIndents(True)
        wx.stc.EVT_STC_MARGINCLICK(self, self.GetId(), self.OnMarginClick)
        wx.EVT_KEY_DOWN(self, self.OnKeyPressed)
        wx.stc.EVT_STC_DWELLSTART(self,self.GetId(), self.OnDwellStart)
        wx.stc.EVT_STC_DWELLEND(self, self.GetId(),self.OnDwellEnd)
        if self.GetMatchingBraces(): 
            wx.stc.EVT_STC_UPDATEUI(self, self.GetId(), self.OnUpdateUI)

        if sysutilslib.isWindows():
            STCTextEditor.TextCtrl.SetEOLMode(self,wx.stc.STC_EOL_CRLF)
        else:
            STCTextEditor.TextCtrl.SetEOLMode(self,wx.stc.STC_EOL_LF)

    ##    self.StyleClearAll()
        self.UpdateStyles()
        
        self.SetWordChars(self.DEFAULT_WORD_CHARS)
        self.AutoCompSetIgnoreCase(True)

    def GetMarginsWidth(self):
        margin_width = 0
        if self.GetViewLineNumbers():
            margin_width += self.EstimatedLineNumberMarginWidth()
        if self.GetViewFolding():
            margin_width += CodeView.FOLD_MARGIN_WIDTH
        if self.GetMarginWidth(CodeView.BOOK_MARKER_NUM) > 0:
            margin_width += CodeView.BOOK_MARGIN_WIDTH
        return margin_width
        
    def OnRightUp(self, event):
        if event.GetPosition().x < self.GetMarginsWidth():
            return
        #cancel calltip
        if self.CallTipActive():
            self.CallTipCancel()
        #Hold onto the current line number, no way to get it later.
        self._rightClickPosition = self.PositionFromPoint(event.GetPosition())
        self._rightClickLine = self.LineFromPosition(self._rightClickPosition)
        menu = self.CreatePopupMenu()
        self.PopupMenu(menu, event.GetPosition())
        self._rightClickLine = -1
        self._rightClickPosition = -1
        menu.Destroy()
        

    def CreatePopupMenu(self):
        TOGGLEBREAKPOINT_ID = wx.NewId()
        TOGGLEMARKER_ID = wx.NewId()
        
        menu = wx.Menu()
        itemIDs = [wx.ID_UNDO, wx.ID_REDO, None,
                   wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR, None, wx.ID_SELECTALL]
        menuBar = wx.GetApp().GetTopWindow().GetMenuBar()
        for itemID in itemIDs:
            if not itemID:
                menu.AppendSeparator()
            else:
                item = menuBar.FindItemById(itemID)
                if item:
                    menu.Append(itemID, item.GetLabel())
                    wx.EVT_MENU(self, itemID, self.DSProcessEvent)  # wxHack: for customized right mouse menu doesn't work with new DynamicSashWindow
                    wx.EVT_UPDATE_UI(self, itemID, self.DSProcessUpdateUIEvent)  # wxHack: for customized right mouse menu doesn't work with new DynamicSashWindow
        
        self.Bind(wx.EVT_MENU, self.OnPopToggleBP, id=TOGGLEBREAKPOINT_ID)
        item = wx.MenuItem(menu, TOGGLEBREAKPOINT_ID, _("Toggle Breakpoint"))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopToggleMarker, id=TOGGLEMARKER_ID)
        item = wx.MenuItem(menu, TOGGLEMARKER_ID, _("Toggle Bookmark"))
        menu.AppendItem(item)
        return menu
                
    def DSProcessUpdateUIEvent(self, event):
        id = event.GetId()
      ##  if id ==  CompletionService.CompletionService.GO_TO_DEFINITION:
            ##event.Enable(self.IsCaretLocateInWord())
        ##    return True
        ##else:
        return STCTextEditor.TextCtrl.DSProcessUpdateUIEvent(self,event)
                
    def OnPopToggleBP(self, event):
        """ Toggle break point on right click line, not current line """
        import DebuggerService
        wx.GetApp().GetService(DebuggerService.DebuggerService).OnToggleBreakpoint(event, line=self._rightClickLine)
      
  
    def OnPopToggleMarker(self, event):
        """ Toggle marker on right click line, not current line """
        wx.GetApp().GetDocumentManager().GetCurrentView().MarkerToggle(lineNum = self._rightClickLine)


    def OnPopSyncOutline(self, event):
        lineNum = wx.GetApp().GetDocumentManager().GetCurrentView().LineFromPosition(self._rightClickPosition)
        wx.GetApp().GetService(OutlineService.OutlineService).LoadOutline(wx.GetApp().GetDocumentManager().GetCurrentView(),lineNum=lineNum)
        
    def OnGotoDefinition(self, event):
        self.GotoDefinition()

    def GotoDefinition(self):
        pass

    def ClearCurrentLineMarkers(self):
        self.MarkerDeleteAll(CodeCtrl.CURRENT_LINE_MARKER_NUM)
        
    def ClearCurrentBreakpoinMarkers(self):
        self.MarkerDeleteAll(CodeCtrl.BREAKPOINT_MARKER_NUM)

    def GetDefaultFont(self):
        if wx.Platform == '__WXMSW__':
            font = "Courier New"
        else:
            font = "Courier"
        return wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = font)

    def GetMatchingBraces(self):
        """ Overwrite this method for language specific braces """
        return "[]{}()"

    def CanWordWrap(self):
        return False

    def UpdateStyles(self):
        if not self.GetFont():
            return
        faces = { 'font' : self.GetFont().GetFaceName(),
                  'size' : self.GetFont().GetPointSize(),
                  'size2': self.GetFont().GetPointSize() - 2,
                  'color' : "%02x%02x%02x" % (self.GetFontColor().Red(), self.GetFontColor().Green(), self.GetFontColor().Blue())
                  }
        # Global default styles for all languages
        ###self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:%(font)s,fore:#FFFFFF,size:%(size)d" % faces)
      ##  self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "face:%(font)s,back:#C0C0C0,face:%(font)s,size:%(size2)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, "face:%(font)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,  "face:%(font)s,fore:#000000,back:#70FFFF,size:%(size)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,    "face:%(font)s,fore:#000000,back:#FF0000,size:%(size)d" % faces)

    def GetTypeWord(self,pos):
        start_pos = self.WordStartPosition(pos,True)
        end_pos = self.WordEndPosition(pos,True)
        at = self.GetCharAt(start_pos)
        rem_chars = self.DEFAULT_WORD_CHARS + self.TYPE_POINT_WORD
        while chr(at) in rem_chars:
             if chr(at) == self.TYPE_POINT_WORD:
                 start_pos -=1
                 at = self.GetCharAt(start_pos)
                 while chr(at) == self.TYPE_BLANK_WORD:
                     start_pos -=1
                     at = self.GetCharAt(start_pos)
             else:
                 start_pos -=1
                 at = self.GetCharAt(start_pos)        
        text = self.GetTextRange(start_pos+1,end_pos)
        return text
        
    def OnKeyPressed(self, event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()
        #if autocomp is active,ignore enter key
        if key == wx.WXK_RETURN and not self.AutoCompActive():
            #if found selected text,should delete the selectd text and append a new line
            if self.GetSelectedText():
                self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            else:
                self.DoIndent()
        else:
            STCTextEditor.TextCtrl.OnKeyPressed(self, event)

    def OnDwellStart(self, evt):
        evt.Skip()

    def OnDwellEnd(self, evt):
        evt.Skip()

    def DoIndent(self):
        self.AddText('\n')
        self.EnsureCaretVisible()
        # Need to do a default one for all languges


    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                lineCount = self.GetLineCount()
                expanding = True

                # find out if we are folding or unfolding
                for lineNum in range(lineCount):
                    if self.GetFoldLevel(lineNum) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                        expanding = not self.GetFoldExpanded(lineNum)
                        break;

                self.ToggleFoldAll(expanding)
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())
                if self.GetFoldLevel(lineClicked) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

        elif evt.GetMargin() == 0:
            #This is used to toggle breakpoints via the debugger service.
            import DebuggerService
            db_service = wx.GetApp().GetService(DebuggerService.DebuggerService)
            if db_service:
                db_service.OnToggleBreakpoint(evt, line=self.LineFromPosition(evt.GetPosition()))
            

    def OnUpdateUI(self, evt):
        braces = self.GetMatchingBraces()
        
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in braces:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in braces:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

        evt.Skip()


    def ToggleFoldAll(self, expand = True, topLevelOnly = False):
        i = 0
        lineCount = self.GetLineCount()
        while i < lineCount:
            if not topLevelOnly or (topLevelOnly and self.GetFoldLevel(i) & wx.stc.STC_FOLDLEVELNUMBERMASK  == wx.stc.STC_FOLDLEVELBASE):
                if (expand and self.CanLineExpand(i)) or (not expand and self.CanLineCollapse(i)):
                    self.ToggleFold(i)
            i = i + 1


    def CanLineExpand(self, line):
        return not self.GetFoldExpanded(line)


    def CanLineCollapse(self, line):
        return self.GetFoldExpanded(line) and self.GetFoldLevel(line) & wx.stc.STC_FOLDLEVELHEADERFLAG


    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1
        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & wx.stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)
                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1;
        return line

    def SetMarginFoldStyle(self):
        # Setup a margin to hold fold markers
        self.SetProperty("fold", "1")
        self.SetMarginType(CodeView.FOLD_MARKER_NUM, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(CodeView.FOLD_MARKER_NUM, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(CodeView.FOLD_MARKER_NUM, True)
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,  "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,  "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,    "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,  "white", "black")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS, "white", "black")
        self.SetFoldFlags(16)  ###  WHAT IS THIS VALUE?  WHAT ARE THE OTHER FLAGS?  DOES IT MATTER?

    def SetEOLMode(self,eol_id):
        mode = MODE_MAP.get(eol_id, wx.stc.STC_EOL_LF)
        STCTextEditor.TextCtrl.SetEOLMode(self,mode)

    def IsEOLModeId(self,eol_id):
        mode = MODE_MAP.get(eol_id, wx.stc.STC_EOL_LF)
        return mode == STCTextEditor.TextCtrl.GetEOLMode(self)

    def CheckEOL(self):
        """Checks the EOL mode of the opened document. If the mode
        that the document was saved in is different than the editors
        current mode the editor will switch modes to preserve the eol
        type of the file, if the eol chars are mixed then the editor
        will toggle on eol visibility.
        @postcondition: eol mode is configured to best match file
        @todo: Is showing line endings the best way to show mixed?
        """
        mixed = diff = False
        eol_map = {u"\n" : wx.stc.STC_EOL_LF,
                   u"\r\n" : wx.stc.STC_EOL_CRLF,
                   u"\r" : wx.stc.STC_EOL_CR}

        eol = unichr(self.GetCharAt(self.GetLineEndPosition(0)))
        if eol == u"\r":
            tmp = unichr(self.GetCharAt(self.GetLineEndPosition(0) + 1))
            if tmp == u"\n":
                eol += tmp

        # Is the eol used in the document the same as what is currently set.
        if eol != self.GetEOLChar():
            diff = True

        # Check the lines to see if they are all matching or not.
        LEPFunct = self.GetLineEndPosition
        GCAFunct = self.GetCharAt
        for line in range(self.GetLineCount() - 1):
            end = LEPFunct(line)
            tmp = unichr(GCAFunct(end))
            if tmp == u"\r":
                tmp2 = unichr(GCAFunct(LEPFunct(0) + 1))
                if tmp2 == u"\n":
                    tmp += tmp2
            if tmp != eol:
                mixed = True
                break

        if mixed or diff:
            if mixed:
                # Warn about mixed end of line characters and offer to convert
                msg = _("Mixed EOL characters detected.\n\n"
                        "Would you like to format them to all be the same?")
                dlg = EOLFormat.EOLFormatDlg(wx.GetApp().GetTopWindow(), msg,
                                             _("Format EOL?"),
                                             eol_map.get(eol, self.GetEOLMode()))

                if dlg.ShowModal() == wx.ID_YES:
                    sel = dlg.GetSelection()
                    self.ConvertEOLs(sel)
                    super(STCTextEditor.TextCtrl, self).SetEOLMode(sel)
                dlg.Destroy()
            else:
                # The end of line character is different from the preferred
                # user setting for end of line. So change our eol mode to
                # preserve that of what the document is using.
                mode = eol_map.get(eol, wx.stc.STC_EOL_LF)
                super(STCTextEditor.TextCtrl, self).SetEOLMode(mode)
        else:
            pass

    def ConvertLineMode(self, mode_id):
        """Converts all line endings in a document to a specified
        format.
        @param mode_id: (menu) id of eol mode to set

        """
        self.ConvertEOLs(MODE_MAP[mode_id])
        super(STCTextEditor.TextCtrl, self).SetEOLMode(MODE_MAP[mode_id])

    def GetEOLChar(self):
        """Gets the eol character used in document
        @return: the character used for eol in this document

        """
        m_id = self.GetEOLMode()
        if m_id == wx.stc.STC_EOL_CR:
            return u'\r'
        elif m_id == wx.stc.STC_EOL_CRLF:
            return u'\r\n'
        else:
            return u'\n'

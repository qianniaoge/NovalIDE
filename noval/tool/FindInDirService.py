#----------------------------------------------------------------------------
# Name:         IDEFindService.py
# Purpose:      Find Service for pydocview
#
# Author:       Morgan Hua
#
# Created:      8/15/03
# CVS-ID:       $Id$
# Copyright:    (c) 2004-2005 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import os
from os.path import join
import re
import ProjectEditor
import MessageService
import FindService
import OutlineService
import noval.util.strutils as strutils
import time
import threading
from wx.lib.pubsub import pub as Publisher
import noval.util.fileutils as fileutils
_ = wx.GetTranslation


#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
FILENAME_MARKER = _("Found in file: ")
PROJECT_MARKER = _("Searching project: ")
FILE_MARKER = _("Searching file: ")
FIND_MATCHDIR = "FindMatchDir"
FIND_MATCHDIRSUBFOLDERS = "FindMatchDirSubfolders"

SPACE = 10
HALF_SPACE = 5

class FindTextOption():
    def __init__(self,find_what,dir_string,match_case,\
                    whole_word,reg_expr,searchSubfolders,search_hidden,file_type_list):
        self.DirString = dir_string
        self.SearchSubfolders = searchSubfolders
        self.SearchHidden = search_hidden
        self.FindString = find_what
        self.MatchCase = match_case
        self.WholeWord = whole_word
        self.RegExpr = reg_expr
        self.FileTypes = file_type_list

UPDATE_PROGRESS_SIGNAL_NAME = "UpdateProgress"

class SearchProgressDialog(wx.GenericProgressDialog):
    
    def __init__(self,parent):
        welcome_msg = "Please wait a minute for end find text"
        wx.GenericProgressDialog.__init__(self,"Find Text In Directory",welcome_msg,\
                maximum = 100, parent=parent,\
                    style = 0|wx.PD_APP_MODAL|wx.PD_CAN_ABORT)

        Publisher.subscribe(self.UpdateProgress,UPDATE_PROGRESS_SIGNAL_NAME)
        self.keep_going = True
        
    def UpdateProgress(self,temp,msg):
        keep_going,_ = self.Update(temp,msg)
        self.keep_going = keep_going

class FindInDirService(FindService.FindService):

    #----------------------------------------------------------------------------
    # Constants
    #----------------------------------------------------------------------------
    FINDFILE_ID = wx.NewId()        # for bringing up Find in File dialog box
    FINDALL_ID = wx.NewId()         # for bringing up Find All dialog box
    FINDDIR_ID = wx.NewId()         # for bringing up Find Dir dialog box
    LINE_PREFIX = "Line "


    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        FindService.FindService.InstallControls(self, frame, menuBar, toolBar, statusBar, document)

        editMenu = menuBar.GetMenu(menuBar.FindMenu(_("&Edit")))
        wx.EVT_MENU(frame, FindInDirService.FINDFILE_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindInDirService.FINDFILE_ID, self.ProcessUpdateUIEvent)
        editMenu.Append(FindInDirService.FINDFILE_ID, _("Find in File...\tCtrl+Shift+F"), _("Searches for the specified text in the current file"))
        wx.EVT_MENU(frame, FindInDirService.FINDALL_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindInDirService.FINDALL_ID, self.ProcessUpdateUIEvent)
        editMenu.Append(FindInDirService.FINDALL_ID, _("Find in Project...\tCtrl+Shift+P"), _("Searches for the specified text in all the files in the project"))
        wx.EVT_MENU(frame, FindInDirService.FINDDIR_ID, self.ProcessEvent)
        wx.EVT_UPDATE_UI(frame, FindInDirService.FINDDIR_ID, self.ProcessUpdateUIEvent)
        editMenu.Append(FindInDirService.FINDDIR_ID, _("Find in Directory...\tCtrl+Shift+D"), _("Searches for the specified text in all the files in the directory"))


    def ProcessEvent(self, event):
        id = event.GetId()
        if id == FindInDirService.FINDFILE_ID:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            if hasattr(view, "GetCtrl") and view.GetCtrl() and hasattr(view.GetCtrl(), "GetSelectedText"):
                self.ShowFindInFileDialog(view.GetCtrl().GetSelectedText())
            else:
                self.ShowFindInFileDialog()
            return True
        elif id == FindInDirService.FINDALL_ID:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            if hasattr(view, "GetCtrl") and view.GetCtrl() and hasattr(view.GetCtrl(), "GetSelectedText"):
                self.ShowFindInProjectDialog(view.GetCtrl().GetSelectedText())
            else:
                self.ShowFindInProjectDialog()
            return True
        elif id == FindInDirService.FINDDIR_ID:
            view = wx.GetApp().GetDocumentManager().GetCurrentView()
            if hasattr(view, "GetCtrl") and view.GetCtrl() and hasattr(view.GetCtrl(), "GetSelectedText"):
                self.ShowFindInDirDialog(view.GetCtrl().GetSelectedText())
            else:
                self.ShowFindInDirDialog()
            return True
        else:
            return FindService.FindService.ProcessEvent(self, event)


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == FindInDirService.FINDFILE_ID:
            view = self.GetActiveView()
            if view:  # don't search project model
                event.Enable(True)
            else:
                event.Enable(False)
            return True
        elif id == FindInDirService.FINDALL_ID:
            projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
            if projectService.GetFilesFromCurrentProject():
                event.Enable(True)
            else:
                event.Enable(False)
            return True
        elif id == FindInDirService.FINDDIR_ID:
            event.Enable(True)
        else:
            return FindService.FindService.ProcessUpdateUIEvent(self, event)

    def GetFileTypeList(self,file_type_str):
        if file_type_str == "" or file_type_str == "*.*":
            return []
        type_parts = file_type_str.split(";")
        return [str(part.replace("*.","")) for part in type_parts]

    def FindTextInFile(self,filename,findString,matchCase,wholeWord,regExpr,view):
        found_line = 0
        try:
            docFile = file(filename, 'r')
        except IOError, (code, message):
            print _("Warning, unable to read file: '%s'.  %s") % (filename, message)
            return found_line
        lineNum = 1
        needToDisplayFilename = True
        line = docFile.readline()
        while line:
            count, foundStart, foundEnd, newText = self.DoFind(findString, None, line, 0, 0, True, matchCase, wholeWord, regExpr)
            if count != -1:
                if needToDisplayFilename:
                    view.AddLines(FILENAME_MARKER + filename + "\n")
                    needToDisplayFilename = False
                line = self.LINE_PREFIX + str(lineNum) + ":" + line
                view.AddLines(line)
                found_line += 1
            line = docFile.readline()
            lineNum += 1
        if not needToDisplayFilename:
            view.AddLines("\n")
        view.GetControl().ScrollToLine(view.GetControl().GetLineCount())
        return found_line

    def ShowSearchProgressDialog(self):
        dlg = SearchProgressDialog(parent=wx.GetApp().GetTopWindow())
        dlg.Raise()
        self.progress_dlg = dlg

    def FindTextInFiles(self,find_text_option,view,list_files,cur_pos=0):
        found_line = 0
        for list_file in list_files:
            if not self.progress_dlg.keep_going:
                break
            found_line += self.FindTextInFile(list_file,find_text_option.FindString,\
                               find_text_option.MatchCase, find_text_option.WholeWord,\
                                    find_text_option.RegExpr,view)
            wx.MilliSleep(50)
            wx.SafeYield(self.progress_dlg,True)
            wx.CallAfter(Publisher.sendMessage,UPDATE_PROGRESS_SIGNAL_NAME, \
                    temp=cur_pos,msg="search file:%s" % list_file)
           ## Publisher.sendMessage(UPDATE_PROGRESS_SIGNAL_NAME, temp=temp,msg="search file:%s" % filename)
            cur_pos += 1
        return found_line,cur_pos

    def FindIndir(self,find_text_option,view):
        is_progress_show = False
        start = time.time()
        temp = 0
        total_found_line = 0
        list_files = []
        max_file_count = 1000
        found_file_count = 0
        cur_pos = 0
        # do search in files on disk
        for root, dirs, files in os.walk(find_text_option.DirString):
            if not self.progress_dlg.keep_going:
                break
            if not find_text_option.SearchSubfolders and root != find_text_option.DirString:
                break
            if not find_text_option.SearchHidden and fileutils.is_file_hiden(root):
                continue
            for name in files:
                if find_text_option.FileTypes != []:
                    file_ext = strutils.GetFileExt(name)
                    if file_ext not in find_text_option.FileTypes:
                        continue
                filename = os.path.join(root, name)
                if not find_text_option.SearchHidden and fileutils.is_file_hiden(filename):
                    break
                list_files.append(filename)
                found_file_count += 1
                now = time.time()
                if len(list_files) >= max_file_count:
                    self.progress_dlg.SetRange(found_file_count)
                    found_line,cur_pos = self.FindTextInFiles(find_text_option,view,list_files,cur_pos)
                    total_found_line += found_line
                    list_files = []
               # if now-start > 3 and not is_progress_show:
                #    is_progress_show = True
                 #   self.ShowSearchProgressDialog(data)
        if self.progress_dlg.keep_going:
            wx.CallAfter(self.progress_dlg.SetRange,found_file_count)
            found_line,cur_pos = self.FindTextInFiles(find_text_option,view,list_files,cur_pos)
        total_found_line += found_line
        time.sleep(1)
        wx.CallAfter(self.progress_dlg.Destroy)
        view.AddLines(_("Search completed,Find total %d results.") % total_found_line)
        
    def ShowFindInDirDialog(self, findString=None):
        config = wx.ConfigBase_Get()

        frame = wx.Dialog(wx.GetApp().GetTopWindow(), -1, _("Find in Directory"), size= (320,200))
        borderSizer = wx.BoxSizer(wx.HORIZONTAL)

        contentSizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(frame, -1, _("Directory:")), 0, wx.ALIGN_CENTER | wx.RIGHT, HALF_SPACE)
        dirCtrl = wx.TextCtrl(frame, -1, config.Read(FIND_MATCHDIR, ""), size=(200,-1))
        dirCtrl.SetToolTipString(dirCtrl.GetValue())
        lineSizer.Add(dirCtrl, 0, wx.LEFT, HALF_SPACE)
        findDirButton = wx.Button(frame, -1, _("Browse..."))
        lineSizer.Add(findDirButton, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)

        def OnBrowseButton(event):
            dlg = wx.DirDialog(frame, _("Choose a directory:"), style=wx.DD_DEFAULT_STYLE)
            dir = dirCtrl.GetValue()
            if len(dir):
                dlg.SetPath(dir)
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                dirCtrl.SetValue(dlg.GetPath())
                dirCtrl.SetToolTipString(dirCtrl.GetValue())
                dirCtrl.SetInsertionPointEnd()
            dlg.Destroy()
        wx.EVT_BUTTON(findDirButton, -1, OnBrowseButton)
        
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        subfolderCtrl = wx.CheckBox(frame, -1, _("Search in subdirectories"))
        subfolderCtrl.SetValue(config.ReadInt(FIND_MATCHDIRSUBFOLDERS, True))
        lineSizer.Add(subfolderCtrl,0,wx.LEFT)
        searchHiddenCtrl = wx.CheckBox(frame, -1, _("Search hidden files"))
        lineSizer.Add(searchHiddenCtrl,0,wx.LEFT,SPACE)
        
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)

        lineSizer = wx.BoxSizer(wx.VERTICAL)    # let the line expand horizontally without vertical expansion
        lineSizer.Add(wx.StaticLine(frame, -1, size = (10,-1)), 0, flag=wx.EXPAND)
        contentSizer.Add(lineSizer, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, border=HALF_SPACE)

        if wx.Platform == "__WXMAC__":
            contentSizer.Add((-1, 10), 0, wx.EXPAND)

        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(frame, -1, _("Find what:")), 0, wx.ALIGN_CENTER | wx.RIGHT, HALF_SPACE)
        if not findString:
            findString = config.Read(FindService.FIND_MATCHPATTERN, "")
        findCtrl = wx.TextCtrl(frame, -1, findString, size=(150,-1))
        findCtrl.SetFocus()
        findCtrl.SetSelection(0,-1)
        lineSizer.Add(findCtrl, 0, wx.LEFT, HALF_SPACE)
        
        lineSizer.Add(wx.StaticText(frame, -1, _("File types:")), 0, wx.ALIGN_CENTER |wx.LEFT , HALF_SPACE )
        filetype_Ctrl = wx.TextCtrl(frame, -1, "*.py", size=(100,-1))
        filetype_Ctrl.SetToolTipString(_("Multiple file types seperated by semicolon"))
        filetype_Ctrl.SetFocus()
        filetype_Ctrl.SetSelection(0,-1)
        lineSizer.Add(filetype_Ctrl, 0, wx.LEFT, HALF_SPACE)
        
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        wholeWordCtrl = wx.CheckBox(frame, -1, _("Match whole word only"))
        wholeWordCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHWHOLEWORD, False))
        matchCaseCtrl = wx.CheckBox(frame, -1, _("Match case"))
        matchCaseCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHCASE, False))
        regExprCtrl = wx.CheckBox(frame, -1, _("Regular expression"))
        regExprCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHREGEXPR, False))
        contentSizer.Add(wholeWordCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(matchCaseCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(regExprCtrl, 0, wx.BOTTOM, SPACE)
        borderSizer.Add(contentSizer, 0, wx.TOP | wx.BOTTOM | wx.LEFT, SPACE)

        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        findBtn = wx.Button(frame, wx.ID_OK, _("Find"))
        findBtn.SetDefault()
        BTM_SPACE = HALF_SPACE
        if wx.Platform == "__WXMAC__":
            BTM_SPACE = SPACE
        buttonSizer.Add(findBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(wx.Button(frame, wx.ID_CANCEL), 0)
        borderSizer.Add(buttonSizer, 0, wx.ALL, SPACE)

        frame.SetSizer(borderSizer)
        frame.Fit()

        frame.CenterOnParent()
        status = frame.ShowModal()

        passedCheck = False
        while status == wx.ID_OK and not passedCheck:
            if not os.path.exists(dirCtrl.GetValue()):
                dlg = wx.MessageDialog(frame,
                                       _("'%s' does not exist.") % dirCtrl.GetValue(),
                                       _("Find in Directory"),
                                       wx.OK | wx.ICON_EXCLAMATION
                                       )
                dlg.CenterOnParent()
                dlg.ShowModal()
                dlg.Destroy()

                status = frame.ShowModal()
            elif len(findCtrl.GetValue()) == 0:
                dlg = wx.MessageDialog(frame,
                                       _("'Find what:' cannot be empty."),
                                       _("Find in Directory"),
                                       wx.OK | wx.ICON_EXCLAMATION
                                       )
                dlg.CenterOnParent()
                dlg.ShowModal()
                dlg.Destroy()

                status = frame.ShowModal()
            else:
                passedCheck = True


        # save user choice state for this and other Find Dialog Boxes
        dirString = dirCtrl.GetValue()
        searchSubfolders = subfolderCtrl.IsChecked()
        searchHidden = searchHiddenCtrl.IsChecked()
        self.SaveFindInDirConfig(dirString, searchSubfolders)

        findString = findCtrl.GetValue()
        matchCase = matchCaseCtrl.IsChecked()
        wholeWord = wholeWordCtrl.IsChecked()
        regExpr = regExprCtrl.IsChecked()
        self.SaveFindConfig(findString, wholeWord, matchCase, regExpr)
        
        file_type = filetype_Ctrl.GetValue().strip()
        file_type_list = self.GetFileTypeList(file_type)

        find_text_option = FindTextOption(findString,dirString,matchCase,\
                    wholeWord,regExpr,searchSubfolders,searchHidden,file_type_list)
        frame.Destroy()
        if status == wx.ID_OK:
            messageService = wx.GetApp().GetService(MessageService.MessageService)
            MessageService.MessageView.bottomTab.SetSelection(1)
            messageService.ShowWindow()

            view = messageService.GetView()
            found_line = 0
            if view:
                wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
                
                try:
                    view.ClearLines()
                    view.SetCallback(self.OnJumpToFoundLine)
    
                    view.AddLines(_("Searching for '%s' in '%s'\n\n") % (findString, dirString))
    
                    if os.path.isfile(dirString):
                        try:
                            docFile = file(dirString, 'r')
                            lineNum = 1
                            needToDisplayFilename = True
                            line = docFile.readline()
                            while line:
                                count, foundStart, foundEnd, newText = self.DoFind(findString, None, line, 0, 0, True, matchCase, wholeWord, regExpr)
                                if count != -1:
                                    if needToDisplayFilename:
                                        view.AddLines(FILENAME_MARKER + dirString + "\n")
                                        needToDisplayFilename = False
                                    line = self.LINE_PREFIX + str(lineNum) + ":" + line
                                    view.AddLines(line)
                                    found_line += 1
                                line = docFile.readline()
                                lineNum += 1
                            if not needToDisplayFilename:
                                view.AddLines("\n")
                        except IOError, (code, message):
                            print _("Warning, unable to read file: '%s'.  %s") % (dirString, message)
                    else:
                        self.progress_dlg = None
                        self.ShowSearchProgressDialog()
                        t = threading.Thread(target=self.FindIndir,args = (find_text_option,view))
                        t.start()
                finally:
                    wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

            return True
        else:
            return False


    def SaveFindInDirConfig(self, dirString, searchSubfolders):
        """ Save search dir patterns and flags to registry.

            dirString = search directory
            searchSubfolders = Search subfolders
        """
        config = wx.ConfigBase_Get()
        config.Write(FIND_MATCHDIR, dirString)
        config.WriteInt(FIND_MATCHDIRSUBFOLDERS, searchSubfolders)


    def DoFindIn(self, findString, matchCase, wholeWord, regExpr, currFileOnly=False, jumpToFound=False):
        messageService = wx.GetApp().GetService(MessageService.MessageService)
        if not messageService:
            return  
        messageService.ShowWindow()
        view = messageService.GetView()
        if not view:
            return
        wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        
        try:
            #Switch to messages tab.
            view.GetControl().GetParent().SetSelection(1) 
            view.ClearLines()
            view.SetCallback(self.OnJumpToFoundLine)
    
            projectService = wx.GetApp().GetService(ProjectEditor.ProjectService)
    
            if self.GetActiveView():
                currDoc = self.GetActiveView().GetDocument()
            else:
                currDoc = None
            if currFileOnly:
                if currDoc:
                    projectFilenames = [currDoc.GetFilename()]
                    view.AddLines(FILE_MARKER + currDoc.GetFilename() + "\n\n")
                else:
                    projectFilenames = []
            else:
                projectFilenames = projectService.GetFilesFromCurrentProject()
    
                projView = projectService.GetView()
                if projView:
                    projName = wx.lib.docview.FileNameFromPath(projView.GetDocument().GetFilename())
                    view.AddLines(PROJECT_MARKER + projName + "\n\n")
    
            firstDef = -1
            found_line = 0
            # do search in open files first, open files may have been modified and different from disk because it hasn't been saved
            openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
            openDocsInProject = filter(lambda openDoc: openDoc.GetFilename() in projectFilenames, openDocs)
            if currDoc and currDoc in openDocsInProject:
                # make sure current document is searched first.
                openDocsInProject.remove(currDoc)
                openDocsInProject.insert(0, currDoc)
            for openDoc in openDocsInProject:
                if isinstance(openDoc, ProjectEditor.ProjectDocument):  # don't search project model
                    continue
    
                openDocView = openDoc.GetFirstView()
                # some views don't have a in memory text object to search through such as the PM and the DM
                # even if they do have a non-text searchable object, how do we display it in the message window?
                if not hasattr(openDocView, "GetValue"):
                    continue
                line_count = openDocView.GetLineCount()
     ##           lineNum = 1
                needToDisplayFilename = True
             #   start = 0
              #  end = 0
               # count = 0
                for lineNum in range(line_count):
                    line_text = openDocView.GetLine(lineNum+1)
                    count, foundStart, foundEnd, newText = self.DoFind(findString, None, line_text, 0, 0, True, matchCase, wholeWord, regExpr)
                    if count != -1:
                        if needToDisplayFilename:
                            view.AddLines(FILENAME_MARKER + openDoc.GetFilename() + "\n")
                            needToDisplayFilename = False
    
                ##        lineNum = openDocView.LineFromPosition(foundStart)
                        line = self.LINE_PREFIX + str(lineNum+1) + ":" + line_text
                        view.AddLines(line)
                        if firstDef == -1:
                            firstDef = view.GetControl().GetCurrentLine() - 1
    
##                        start = text.find("\n", foundStart)
                        found_line += 1
  ##                      if start == -1:
    ##                        break
      ##                  end = start
                if not needToDisplayFilename:
                    view.AddLines("\n")
                wx.GetApp().Yield(True)
            openDocNames = map(lambda openDoc: openDoc.GetFilename(), openDocs)
    
            # do search in closed files, skipping the open ones we already searched
            filenames = filter(lambda filename: filename not in openDocNames, projectFilenames)
            for filename in filenames:
                try:
                    docFile = file(filename, 'r')
                except IOError, (code, message):
                    print _("Warning, unable to read file: '%s'.  %s") % (filename, message)
                    continue
    
                lineNum = 1
                needToDisplayFilename = True
                line = docFile.readline()
                while line:
                    count, foundStart, foundEnd, newText = self.DoFind(findString, None, line, 0, 0, True, matchCase, wholeWord, regExpr)
                    if count != -1:
                        if needToDisplayFilename:
                            view.AddLines(FILENAME_MARKER + filename + "\n")
                            needToDisplayFilename = False
                        line = repr(lineNum).zfill(4) + ":" + line
                        view.AddLines(line)
                        if firstDef == -1:
                            firstDef = view.GetControl().GetCurrentLine() - 1
                    line = docFile.readline()
                    lineNum += 1
                if not needToDisplayFilename:
                    view.AddLines("\n")
                wx.GetApp().Yield(True)
    
            view.AddLines(_("Search for '%s' completed, Find total %d results.") % (findString,found_line))
    
            if jumpToFound:
                self.OnJumpToFoundLine(event=None, defLineNum=firstDef)

        finally:
            wx.GetApp().GetTopWindow().SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

    def FindInProject(self, findString):
        self.DoFindIn(findString, matchCase=True, wholeWord=True, regExpr=True, jumpToFound=True)


    def ShowFindInProjectDialog(self, findString=None):
        config = wx.ConfigBase_Get()

        frame = wx.Dialog(wx.GetApp().GetTopWindow(), -1, _("Find in Project"), size= (320,200))
        borderSizer = wx.BoxSizer(wx.HORIZONTAL)

        contentSizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(frame, -1, _("Find what:")), 0, wx.ALIGN_CENTER | wx.RIGHT, HALF_SPACE)
        if not findString:
            findString = config.Read(FindService.FIND_MATCHPATTERN, "")
        findCtrl = wx.TextCtrl(frame, -1, findString, size=(200,-1))
        lineSizer.Add(findCtrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        wholeWordCtrl = wx.CheckBox(frame, -1, _("Match whole word only"))
        wholeWordCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHWHOLEWORD, False))
        matchCaseCtrl = wx.CheckBox(frame, -1, _("Match case"))
        matchCaseCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHCASE, False))
        regExprCtrl = wx.CheckBox(frame, -1, _("Regular expression"))
        regExprCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHREGEXPR, False))
        contentSizer.Add(wholeWordCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(matchCaseCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(regExprCtrl, 0, wx.BOTTOM, SPACE)
        borderSizer.Add(contentSizer, 0, wx.TOP | wx.BOTTOM | wx.LEFT, SPACE)

        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        findBtn = wx.Button(frame, wx.ID_OK, _("Find"))
        findBtn.SetDefault()
        BTM_SPACE = HALF_SPACE
        if wx.Platform == "__WXMAC__":
            BTM_SPACE = SPACE
        buttonSizer.Add(findBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(wx.Button(frame, wx.ID_CANCEL), 0)
        borderSizer.Add(buttonSizer, 0, wx.ALL, SPACE)

        frame.SetSizer(borderSizer)
        frame.Fit()

        frame.CenterOnParent()
        status = frame.ShowModal()

        # save user choice state for this and other Find Dialog Boxes
        findString = findCtrl.GetValue()
        matchCase = matchCaseCtrl.IsChecked()
        wholeWord = wholeWordCtrl.IsChecked()
        regExpr = regExprCtrl.IsChecked()
        self.SaveFindConfig(findString, wholeWord, matchCase, regExpr)

        frame.Destroy()

        if status == wx.ID_OK:
            self.DoFindIn(findString, matchCase, wholeWord, regExpr)
            return True
        else:
            return False


    def ShowFindInFileDialog(self, findString=None):
        config = wx.ConfigBase_Get()

        frame = wx.Dialog(wx.GetApp().GetTopWindow(), -1, _("Find in File"), size= (320,200))
        borderSizer = wx.BoxSizer(wx.HORIZONTAL)

        contentSizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(frame, -1, _("Find what:")), 0, wx.ALIGN_CENTER | wx.RIGHT, HALF_SPACE)
        if not findString:
            findString = config.Read(FindService.FIND_MATCHPATTERN, "")
        findCtrl = wx.TextCtrl(frame, -1, findString, size=(200,-1))
        lineSizer.Add(findCtrl, 0, wx.LEFT, HALF_SPACE)
        contentSizer.Add(lineSizer, 0, wx.BOTTOM, SPACE)
        wholeWordCtrl = wx.CheckBox(frame, -1, _("Match whole word only"))
        wholeWordCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHWHOLEWORD, False))
        matchCaseCtrl = wx.CheckBox(frame, -1, _("Match case"))
        matchCaseCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHCASE, False))
        regExprCtrl = wx.CheckBox(frame, -1, _("Regular expression"))
        regExprCtrl.SetValue(config.ReadInt(FindService.FIND_MATCHREGEXPR, False))
        contentSizer.Add(wholeWordCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(matchCaseCtrl, 0, wx.BOTTOM, SPACE)
        contentSizer.Add(regExprCtrl, 0, wx.BOTTOM, SPACE)
        borderSizer.Add(contentSizer, 0, wx.TOP | wx.BOTTOM | wx.LEFT, SPACE)

        buttonSizer = wx.BoxSizer(wx.VERTICAL)
        findBtn = wx.Button(frame, wx.ID_OK, _("Find"))
        findBtn.SetDefault()
        BTM_SPACE = HALF_SPACE
        if wx.Platform == "__WXMAC__":
            BTM_SPACE = SPACE
        buttonSizer.Add(findBtn, 0, wx.BOTTOM, BTM_SPACE)
        buttonSizer.Add(wx.Button(frame, wx.ID_CANCEL), 0)
        borderSizer.Add(buttonSizer, 0, wx.ALL, SPACE)

        frame.SetSizer(borderSizer)
        frame.Fit()

        frame.CenterOnParent()
        status = frame.ShowModal()

        # save user choice state for this and other Find Dialog Boxes
        findString = findCtrl.GetValue()
        matchCase = matchCaseCtrl.IsChecked()
        wholeWord = wholeWordCtrl.IsChecked()
        regExpr = regExprCtrl.IsChecked()
        self.SaveFindConfig(findString, wholeWord, matchCase, regExpr)

        frame.Destroy()

        if status == wx.ID_OK:
            self.DoFindIn(findString, matchCase, wholeWord, regExpr, currFileOnly=True)
            return True
        else:
            return False


    def OnJumpToFoundLine(self, event=None, defLineNum=-1):
        messageService = wx.GetApp().GetService(MessageService.MessageService)
        if defLineNum == -1:
            lineText, pos = messageService.GetView().GetCurrLine()
        else:
            lineText = messageService.GetView().GetControl().GetLine(defLineNum)
            pos = 0

        if lineText == "\n" or lineText.find(FILENAME_MARKER) != -1 or lineText.find(PROJECT_MARKER) != -1 or lineText.find(FILE_MARKER) != -1:
            return
        lineEnd = lineText.find(":")
        if lineEnd == -1:
            return
        else:
            lineNum = int(lineText[0:lineEnd].replace(self.LINE_PREFIX ,"").strip())

        text = messageService.GetView().GetText()
        if defLineNum == -1:
            curPos = messageService.GetView().GetCurrentPos()
        else:
            curPos = messageService.GetView().GetControl().GetLineEndPosition(defLineNum)

        startPos = text.rfind(FILENAME_MARKER, 0, curPos)
        endPos = text.find("\n", startPos)
        filename = text[startPos + len(FILENAME_MARKER):endPos]

        foundView = None
        openDocs = wx.GetApp().GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if openDoc.GetFilename() == filename:
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            doc = wx.GetApp().GetDocumentManager().CreateDocument(filename, wx.lib.docview.DOC_SILENT|wx.lib.docview.DOC_OPEN_ONCE)
            if doc:
                foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            if hasattr(foundView, "GotoLine"):
                foundView.GotoLine(lineNum)
                startPos = foundView.PositionFromLine(lineNum)
                # wxBug:  Need to select in reverse order, (end, start) to put cursor at head of line so positioning is correct
                #         Also, if we use the correct positioning order (start, end), somehow, when we open a edit window for the first
                #         time, we don't see the selection, it is scrolled off screen
                foundView.SetSelection(startPos - 1 + len(lineText[lineEnd:].rstrip("\n")), startPos)
                wx.GetApp().GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)

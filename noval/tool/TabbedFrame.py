import os
import wx.lib.pydocview
import wx
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import noval.parser.config as parserconfig

_ = wx.GetTranslation

class IDEDocTabbedParentFrame(wx.lib.pydocview.DocTabbedParentFrame):
    
    # wxBug: Need this for linux. The status bar created in pydocview is
    # replaced in IDE.py with the status bar for the code editor. On windows
    # this works just fine, but on linux the pydocview status bar shows up near
    # the top of the screen instead of disappearing. 
    def CreateDefaultStatusBar(self):
       pass
 
    def AppendMenuItem(self,menu,name,callback,separator=False):
       id = wx.NewId()
       menu.Append(id,name)
       wx.EVT_MENU(self, id, callback)       
       if separator:
           menu.AppendSeparator()

    def OnNotebookRightClick(self, event):
        """
        Handles right clicks for the notebook, enabling users to either close
        a tab or select from the available documents if the user clicks on the
        notebook's white space.
        """
        def OnCloseDoc(event):
            doc.DeleteAllViews()
        def OnCloseAllDocs(event):
            self.GetDocumentManager().CloseDocuments(False)
        def OnOpenPathInExplorer(event):
            fileutils.open_file_directory(doc.GetFilename())
        def OnOpenPathInTerminator(event):
            fileutils.open_path_in_terminator(os.path.dirname(doc.GetFilename()))
        def OnCopyFilePath(event):
            sysutilslib.CopyToClipboard(doc.GetFilename())
        def OnCopyFileName(event):
            sysutilslib.CopyToClipboard(os.path.basename(doc.GetFilename()))
        def OnSaveFile(event):
            self.GetDocumentManager().OnFileSave(event)
        def OnSaveFileAs(event):
            self.GetDocumentManager().SaveAsDocument(doc)
        def OnCopyModuleName(event):
            sysutilslib.CopyToClipboard(os.path.basename(doc.GetFilename()).split('.')[0])
        def OnCloseAllWithoutDoc(event):
            for i in range(self._notebook.GetPageCount()-1, -1, -1): # Go from len-1 to 0
                if i != index:
                    doc = self._notebook.GetPage(i).GetView().GetDocument()
                    if not self.GetDocumentManager().CloseDocument(doc, False):
                        return
        index, type = self._notebook.HitTest(event.GetPosition())
        menu = wx.Menu()
        x, y = event.GetX(), event.GetY()
        if index > -1:
            view = self._notebook.GetPage(index).GetView()
            doc = view.GetDocument()
            self.AppendMenuItem(menu,_("Save"),OnSaveFile)
            self.AppendMenuItem(menu,_("SaveAs"),OnSaveFileAs)
            self.AppendMenuItem(menu,_("Close"),OnCloseDoc)
            self.AppendMenuItem(menu,_("CloseAll"),OnCloseAllDocs)
            if self._notebook.GetPageCount() > 1:
                item_name = _("Close All but \"%s\"") % doc.GetPrintableName()
                self.AppendMenuItem(menu,item_name,OnCloseAllWithoutDoc,True)
                tabsMenu = wx.Menu()
                menu.AppendMenu(wx.NewId(), _("Select Tab"), tabsMenu)
            self.AppendMenuItem(menu,_("Open File Path In FileManager"),OnOpenPathInExplorer)
            self.AppendMenuItem(menu,_("Open File Path In Terminator"),OnOpenPathInTerminator)
            self.AppendMenuItem(menu,_("Copy File Path"),OnCopyFilePath)
            self.AppendMenuItem(menu,_("Copy File Name"),OnCopyFileName)
            if view.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER:
                self.AppendMenuItem(menu,_("Copy Module Name"),OnCopyModuleName)
        else:
            y = y - 25  # wxBug: It is offsetting click events in the blank notebook area
            tabsMenu = menu

        if self._notebook.GetPageCount() > 1:
            selectIDs = {}
            for i in range(0, self._notebook.GetPageCount()):
                id = wx.NewId()
                selectIDs[id] = i
                tabsMenu.Append(id, self._notebook.GetPageText(i))
                def OnRightMenuSelect(event):
                    self._notebook.SetSelection(selectIDs[event.GetId()])
                wx.EVT_MENU(self, id, OnRightMenuSelect)

        self._notebook.PopupMenu(menu, wx.Point(x, y))
        menu.Destroy()

    def OnNotebookMouseOver(self, event):
        index, type = self._notebook.HitTest(event.GetPosition())
        if index > -1:
            doc = self._notebook.GetPage(index).GetView().GetDocument()
            self._notebook.SetToolTip(wx.ToolTip(doc.GetFilename()))
        else:
            self._notebook.SetToolTip(wx.ToolTip(""))
        event.Skip()

    def OnMRUFile(self, event):
        """
        Opens the appropriate file when it is selected from the file history
        menu.
        """
        n = event.GetId() - wx.ID_FILE1
        filename = self._docManager.GetHistoryFile(n)
        if filename and os.path.exists(filename):
            self._docManager.CreateDocument(filename, wx.lib.docview.DOC_SILENT)
        else:
            self._docManager.RemoveFileFromHistory(n)
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("File Error")
            if filename:
                wx.MessageBox(_("The file '%s' doesn't exist and couldn't be opened!") % filename,
                              msgTitle,
                              wx.OK | wx.ICON_ERROR,
                              self)

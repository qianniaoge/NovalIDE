#----------------------------------------------------------------------------
# Name:         IDE.py
# Purpose:      IDE using Python extensions to the wxWindows docview framework
#
# Author:       Peter Yared
#
# Created:      5/15/03
# Copyright:    (c) 2003-2005 ActiveGrid, Inc.
# CVS-ID:       $Id$
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.docview
import wx.lib.pydocview
import sys
import wx.grid
import os.path
import noval.util.sysutils as sysutilslib
import noval.util.appdirs as appdirs
import noval.util.logger as logger
import shutil
import interpreter.manager as interpretermanager,interpreter.Interpreter as Interpreter
import noval.parser.intellisence as intellisence
import noval.parser.config as parserconfig
from consts import _,ID_MRU_FILE1,PROJECT_EXTENSION,PROJECT_SHORT_EXTENSION
from noval.util import strutils

# Required for Unicode support with python
# site.py sets this, but Windows builds don't have site.py because of py2exe problems
# If site.py has already run, then the setdefaultencoding function will have been deleted.
if hasattr(sys,"setdefaultencoding"):
    sys.setdefaultencoding("utf-8")

ACTIVEGRID_BASE_IDE = False 
USE_OLD_PROJECTS = False
#----------------------------------------------------------------------------
# Helper functions for command line args
#----------------------------------------------------------------------------

# Since Windows accept command line options with '/', but this character
# is used to denote absolute path names on other platforms, we need to
# conditionally handle '/' style arguments on Windows only.
def printArg(argname):
    output = "'-" + argname + "'"
    if wx.Platform == "__WXMSW__":
        output = output + " or '/" + argname + "'"        
    return output
        
def isInArgs(argname, argv):
    result = False
    if ("-" + argname) in argv:
        result = True
    if wx.Platform == "__WXMSW__" and ("/" + argname) in argv:
        result = True        
    return result

# The default log action in wx is to prompt with a big message box
# which is often inappropriate (for example, if the clipboard data
# is not readable on Mac, we'll get one of these messages repeatedly)
# so just log the errors instead.
# NOTE: This does NOT supress fatal system errors. Only non-fatal ones.
class AppLog(wx.PyLog):
    def __init__(self):
        wx.PyLog.__init__(self)
        self.items = []
        
    def DoLogString(self, message, timeStamp):
        self.items.append(str(timeStamp) + u" " + message.decode())

#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------
class IDEApplication(wx.lib.pydocview.DocApp):

    def __init__(self, redirect=False):
        wx.lib.pydocview.DocApp.__init__(self, redirect=redirect)

    def OnInit(self):
        global ACTIVEGRID_BASE_IDE
        global USE_OLD_PROJECTS
        args = sys.argv

        #init ide logger
        logger.initLogging()

        # Suppress non-fatal errors that might prompt the user even in cases
        # when the error does not impact them.
        #the log will redirect to NovalIDE.exe.log when convert into windows exe with py2exe
        wx.Log_SetActiveTarget(AppLog())
        if "-h" in args or "-help" in args or "--help" in args\
            or (wx.Platform == "__WXMSW__" and "/help" in args):
            print "Usage: ActiveGridAppBuilder.py [options] [filenames]\n"
            # Mac doesn't really support multiple instances for GUI apps
            # and since we haven't got time to test this thoroughly I'm 
            # disabling it for now.
            if wx.Platform != "__WXMAC__":
                print "    option " + printArg("multiple") + " to allow multiple instances of application."
            print "    option " + printArg("debug") + " for debug mode."
            print "    option '-h' or " + printArg("help") + " to show usage information for command."
            print "    option " + printArg("baseide") + " for base IDE mode."
            print "    [filenames] is an optional list of files you want to open when application starts."
            return False
        elif isInArgs("dev", args):
            self.SetAppName(_("NovalBuilderDev"))
            self.SetDebug(False)
        elif isInArgs("debug", args):
            self.SetAppName(_("NovalBuilderDebug"))
            self.SetDebug(True)
            ACTIVEGRID_BASE_IDE = True
            self.SetSingleInstance(False)
        elif isInArgs("baseide", args):
            self.SetAppName(_("NovalIDE"))
            ACTIVEGRID_BASE_IDE = True
        elif isInArgs("tools", args):
            USE_OLD_PROJECTS = True
        else:
            self.SetAppName(_("NovalBuilder"))
            self.SetDebug(False)
        if isInArgs("multiple", args) and wx.Platform != "__WXMAC__":
            self.SetSingleInstance(False)
           
        if not wx.lib.pydocview.DocApp.OnInit(self):
            return False

        self.ShowSplash(getIDESplashBitmap())

        import STCTextEditor
        import TextService
        import FindInDirService
        import MarkerService
        import project as projectlib
        import ProjectEditor
        import PythonEditor
        import OutlineService
        import XmlEditor
        import HtmlEditor
        import TabbedView
        import MessageService
      ##  import OutputService
        import Service
        import ImageEditor
        import PerlEditor
        import PHPEditor
        import wx.lib.ogl as ogl
        import DebuggerService
        import AboutDialog
        import SVNService
        import ExtensionService
        import CompletionService
        import GeneralOption
        import NavigationService
        import TabbedFrame
##        import UpdateLogIniService
                            
        _EDIT_LAYOUTS = True
        self._open_project_path = None                        

        # This creates some pens and brushes that the OGL library uses.
        # It should be called after the app object has been created, but
        # before OGL is used.
        ogl.OGLInitialize()

        config = wx.Config(self.GetAppName(), style = wx.CONFIG_USE_LOCAL_FILE)
        if not config.Exists("MDIFrameMaximized"):  # Make the initial MDI frame maximize as default
            config.WriteInt("MDIFrameMaximized", True)
        if not config.Exists("MDIEmbedRightVisible"):  # Make the properties embedded window hidden as default
            config.WriteInt("MDIEmbedRightVisible", False)

        ##my_locale must be set as app member property,otherwise it will only workable when app start up
        ##it will not workable after app start up,the translation also will not work
        lang_id = GeneralOption.GetLangId(config.Read("Language",""))
        if wx.Locale.IsAvailable(lang_id):
            self.my_locale = wx.Locale(lang_id)
            if self.my_locale.IsOk():
                self.my_locale.AddCatalogLookupPathPrefix(os.path.join(sysutilslib.mainModuleDir,'noval','locale'))
                ibRet = self.my_locale.AddCatalog(self.GetAppName().lower())
                ibRet = self.my_locale.AddCatalog("wxstd")
                self.my_locale.AddCatalog("wxstock")

        docManager = IDEDocManager(flags = self.GetDefaultDocManagerFlags())
        self.SetDocumentManager(docManager)

        # Note:  These templates must be initialized in display order for the "Files of type" dropdown for the "File | Open..." dialog
        defaultTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Any"),
                "*.*",
                _("Any"),
                _(".txt"),
                _("Text Document"),
                _("Text View"),
                STCTextEditor.TextDocument,
                STCTextEditor.TextView,
                wx.lib.docview.TEMPLATE_INVISIBLE,
                icon = STCTextEditor.getTextIcon())
        docManager.AssociateTemplate(defaultTemplate)

        htmlTemplate = wx.lib.docview.DocTemplate(docManager,
                _("HTML"),
                "*.html;*.htm",
                _("HTML"),
                _(".html"),
                _("HTML Document"),
                _("HTML View"),
                HtmlEditor.HtmlDocument,
                HtmlEditor.HtmlView,
                icon = HtmlEditor.getHTMLIcon())
        docManager.AssociateTemplate(htmlTemplate)

        imageTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Image"),
                "*.bmp;*.ico;*.gif;*.jpg;*.jpeg;*.png",
                _("Image"),
                _(".png"),
                _("Image Document"),
                _("Image View"),
                ImageEditor.ImageDocument,
                ImageEditor.ImageView,
                wx.lib.docview.TEMPLATE_NO_CREATE,
                icon = ImageEditor.getImageIcon())
        docManager.AssociateTemplate(imageTemplate)

        perlTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Perl"),
                "*.pl",
                _("Perl"),
                _(".pl"),
                _("Perl Document"),
                _("Perl View"),
                PerlEditor.PerlDocument,
                PerlEditor.PerlView,
                icon = PerlEditor.getPerlIcon())
        docManager.AssociateTemplate(perlTemplate)

        phpTemplate = wx.lib.docview.DocTemplate(docManager,
                _("PHP"),
                "*.php",
                _("PHP"),
                _(".php"),
                _("PHP Document"),
                _("PHP View"),
                PHPEditor.PHPDocument,
                PHPEditor.PHPView,
                icon = PHPEditor.getPHPIcon())
        docManager.AssociateTemplate(phpTemplate)

        projectTemplate = ProjectEditor.ProjectTemplate(docManager,
                _("Project"),
                "*%s" % PROJECT_EXTENSION,
                _("Project"),
                _(PROJECT_EXTENSION),
                _("Project Document"),
                _("Project View"),
                ProjectEditor.ProjectDocument,
                ProjectEditor.ProjectView,
             ###   wx.lib.docview.TEMPLATE_NO_CREATE,
                icon = ProjectEditor.getProjectIcon())
        docManager.AssociateTemplate(projectTemplate)

        pythonTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Python"),
                "*.py;*.pyw",
                _("Python"),
                _(".py"),
                _("Python Document"),
                _("Python View"),
                PythonEditor.PythonDocument,
                PythonEditor.PythonView,
                icon = PythonEditor.getPythonIcon())
        docManager.AssociateTemplate(pythonTemplate)

        textTemplate = wx.lib.docview.DocTemplate(docManager,
                _("Text"),
                "*.text;*.txt",
                _("Text"),
                _(".txt"),
                _("Text Document"),
                _("Text View"),
                STCTextEditor.TextDocument,
                STCTextEditor.TextView,
                icon = STCTextEditor.getTextIcon())
        docManager.AssociateTemplate(textTemplate)

        xmlTemplate = wx.lib.docview.DocTemplate(docManager,
                _("XML"),
                "*.xml",
                _("XML"),
                _(".xml"),
                _("XML Document"),
                _("XML View"),
                XmlEditor.XmlDocument,
                XmlEditor.XmlView,
                icon = XmlEditor.getXMLIcon())
        docManager.AssociateTemplate(xmlTemplate)
        
        pythonService           = self.InstallService(PythonEditor.PythonService(_("Python Interpreter"),embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        if not ACTIVEGRID_BASE_IDE:
            propertyService     = self.InstallService(PropertyService.PropertyService("Properties", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT))
        projectService          = self.InstallService(ProjectEditor.ProjectService(_("Projects/Resources View"), embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT))
        findService             = self.InstallService(FindInDirService.FindInDirService())
        if not ACTIVEGRID_BASE_IDE:
            webBrowserService   = self.InstallService(WebBrowserService.WebBrowserService())  # this must be before webServerService since it sets the proxy environment variable that is needed by the webServerService.
            webServerService    = self.InstallService(WebServerService.WebServerService())  # this must be after webBrowserService since that service sets the proxy environment variables.
        outlineService          = self.InstallService(OutlineService.OutlineService(_("Outline"), embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT))
        filePropertiesService   = self.InstallService(wx.lib.pydocview.FilePropertiesService())
        markerService           = self.InstallService(MarkerService.MarkerService())
        textService             = self.InstallService(TextService.TextService())
        perlService             = self.InstallService(PerlEditor.PerlService())
        phpService              = self.InstallService(PHPEditor.PHPService())
        comletionService        = self.InstallService(CompletionService.CompletionService())
        navigationService       = self.InstallService(NavigationService.NavigationService())
        messageService          = self.InstallService(MessageService.MessageService(_("Search Results"), embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
    ##    outputService          = self.InstallService(OutputService.OutputService("Output", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        debuggerService         = self.InstallService(DebuggerService.DebuggerService("Debugger", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        extensionService        = self.InstallService(ExtensionService.ExtensionService())
        ###optionsService          = self.InstallService(wx.lib.pydocview.DocOptionsService(supportedModes=wx.lib.docview.DOC_MDI))
        optionsService          = self.InstallService(GeneralOption.GeneralOptionsService())
        aboutService            = self.InstallService(wx.lib.pydocview.AboutService(AboutDialog.AboutDialog))
     ###   svnService              = self.InstallService(SVNService.SVNService())
        if not ACTIVEGRID_BASE_IDE:
            helpPath = os.path.join(sysutilslib.mainModuleDir, "activegrid", "tool", "data", "AGDeveloperGuideWebHelp", "AGDeveloperGuideWebHelp.hhp")
            helpService             = self.InstallService(HelpService.HelpService(helpPath))
        if self.GetUseTabbedMDI():
            windowService       = self.InstallService(wx.lib.pydocview.WindowMenuService())
        
        # order of these added determines display order of Options Panels
        optionsService.AddOptionsPanel(ProjectEditor.ProjectOptionsPanel)
       ## optionsService.AddOptionsPanel(DebuggerService.DebuggerOptionsPanel)
        optionsService.AddOptionsPanel(PythonEditor.PythonOptionsPanel)
  ##      optionsService.AddOptionsPanel(PHPEditor.PHPOptionsPanel)
    ##    optionsService.AddOptionsPanel(PerlEditor.PerlOptionsPanel)
        optionsService.AddOptionsPanel(XmlEditor.XmlOptionsPanel)
        optionsService.AddOptionsPanel(HtmlEditor.HtmlOptionsPanel)
        optionsService.AddOptionsPanel(STCTextEditor.TextOptionsPanel)
  ##      optionsService.AddOptionsPanel(SVNService.SVNOptionsPanel)
        optionsService.AddOptionsPanel(ExtensionService.ExtensionOptionsPanel)

        filePropertiesService.AddCustomEventHandler(projectService)

        outlineService.AddViewTypeForBackgroundHandler(PythonEditor.PythonView)
        ###outlineService.AddViewTypeForBackgroundHandler(PHPEditor.PHPView)
        outlineService.AddViewTypeForBackgroundHandler(ProjectEditor.ProjectView) # special case, don't clear outline if in project
        outlineService.AddViewTypeForBackgroundHandler(MessageService.MessageView) # special case, don't clear outline if in message window
        if not ACTIVEGRID_BASE_IDE:
            outlineService.AddViewTypeForBackgroundHandler(DataModelEditor.DataModelView)
            outlineService.AddViewTypeForBackgroundHandler(ProcessModelEditor.ProcessModelView)
            outlineService.AddViewTypeForBackgroundHandler(PropertyService.PropertyView) # special case, don't clear outline if in property window
        outlineService.StartBackgroundTimer()
       
##        projectService.AddLogicalViewFolderDefault(".agp", _("Projects"))
##        projectService.AddLogicalViewFolderDefault(".wsdlag", _("Services"))
##        projectService.AddLogicalViewFolderDefault(".wsdl", _("Services"))
##        projectService.AddLogicalViewFolderDefault(".xsd", _("Data Models"))
##        projectService.AddLogicalViewFolderDefault(".bpel", _("Page Flows"))
##        projectService.AddLogicalViewFolderDefault(".xform", _("Pages"))
##        projectService.AddLogicalViewFolderDefault(".xacml", _("Security"))
##        projectService.AddLogicalViewFolderDefault(".lyt", _("Presentation/Layouts"))
##        projectService.AddLogicalViewFolderDefault(".skn", _("Presentation/Skins"))
##        projectService.AddLogicalViewFolderDefault(".css", _("Presentation/Stylesheets"))
##        projectService.AddLogicalViewFolderDefault(".js", _("Presentation/Javascript"))
##        projectService.AddLogicalViewFolderDefault(".html", _("Presentation/Static"))
##        projectService.AddLogicalViewFolderDefault(".htm", _("Presentation/Static"))
##        projectService.AddLogicalViewFolderDefault(".gif", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".jpeg", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".jpg", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".png", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".ico", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".bmp", _("Presentation/Images"))
##        projectService.AddLogicalViewFolderDefault(".py", _("Code"))
##        projectService.AddLogicalViewFolderDefault(".php", _("Code"))
##        projectService.AddLogicalViewFolderDefault(".pl", _("Code"))
##        projectService.AddLogicalViewFolderDefault(".sql", _("Code"))
##        projectService.AddLogicalViewFolderDefault(".xml", _("Code"))
##        projectService.AddLogicalViewFolderDefault(".dpl", _("Code"))
##        
##        projectService.AddLogicalViewFolderCollapsedDefault(_("Page Flows"), False)
##        projectService.AddLogicalViewFolderCollapsedDefault(_("Pages"), False)
    
        iconPath = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "noval.ico")
        self.SetDefaultIcon(wx.Icon(iconPath, wx.BITMAP_TYPE_ICO))
        if not ACTIVEGRID_BASE_IDE:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT | wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM | wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT
        else:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT | wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM
        if self.GetUseTabbedMDI():
            self.frame = TabbedFrame.IDEDocTabbedParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        else:
            self.frame = TabbedFrame.IDEMDIParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        self.frame.Show(True)
        self.toolbar = self.frame.GetToolBar()
        self.toolbar_combox = self.toolbar.FindControl(DebuggerService.DebuggerService.COMBO_INTERPRETERS_ID)

        wx.lib.pydocview.DocApp.CloseSplash(self)
        self.OpenCommandLineArgs()
        
        if not projectService.LoadSavedProjects() and not docManager.GetDocuments() and self.IsSDI():  # Have to open something if it's SDI and there are no projects...
            projectTemplate.CreateDocument('', wx.lib.docview.DOC_NEW).OnNewDocument()
            
        projectService.SetCurrentProject()
        interpretermanager.InterpreterManager().LoadDefaultInterpreter()
        self.AddInterpreters()
        intellisence.IntellisenceManager().generate_default_intellisence_data()

        self.ShowTipfOfDay()
        wx.UpdateUIEvent.SetUpdateInterval(1000)  # Overhead of updating menus was too much.  Change to update every n milliseconds.
        return True

    def ShowTipfOfDay(self,must_display=False):
        docManager = self.GetDocumentManager()
        tips_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "data", "tips.txt")
        # wxBug: On Mac, having the updates fire while the tip dialog is at front
        # for some reason messes up menu updates. This seems a low-level wxWidgets bug,
        # so until I track this down, turn off UI updates while the tip dialog is showing.
        if os.path.isfile(tips_path):
            config = wx.ConfigBase_Get()
            index = config.ReadInt("TipIndex", 0)
            if must_display:
                showTip = config.ReadInt("ShowTipAtStartup", 1)
                showTipResult = wx.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, index), showAtStartup = showTip)
                if showTipResult != showTip:
                    config.WriteInt("ShowTipAtStartup", showTipResult)
            else:
                self.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, index))
    
    @property
    def MainFrame(self):
        return self.frame
    @property       
    def ToolbarCombox(self):
        return self.toolbar_combox
        
    def GetCurrentInterpreter(self):
        return interpretermanager.InterpreterManager.GetCurrentInterpreter()
        
    def SetCurrentInterpreter(self):
        current_interpreter = interpretermanager.InterpreterManager.GetCurrentInterpreter()
        if current_interpreter is None:
            self.toolbar_combox.SetSelection(-1)
            return
        for i in range(self.toolbar_combox.GetCount()):
            data = self.toolbar_combox.GetClientData(i)
            if data == current_interpreter:
                self.toolbar_combox.SetSelection(i)
                break
                
    def GotoView(self,file_path,lineNum,pos=-1):
        file_path = os.path.abspath(file_path)
        foundView = None
        openDocs = self.GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if openDoc.GetFilename() == file_path:
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            doc = self.GetDocumentManager().CreateDocument(file_path, wx.lib.docview.DOC_SILENT)
            if doc is None:
                return
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            if not hasattr(foundView,"GotoLine"):
                return
            if pos == -1:
                foundView.GotoLine(lineNum)
                startPos = foundView.PositionFromLine(lineNum)
                lineText = foundView.GetCtrl().GetLine(lineNum - 1)
                foundView.SetSelection(startPos, startPos + len(lineText.rstrip("\n")))
            else:
                lineNum = foundView.LineFromPosition(pos)
                foundView.GetCtrl().GotoPos(pos)
            if foundView.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER:
                import OutlineService
                self.GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)


    def GotoViewPos(self,file_path,lineNum,col=0):
        file_path = os.path.abspath(file_path)
        foundView = None
        openDocs = self.GetDocumentManager().GetDocuments()
        for openDoc in openDocs:
            if openDoc.GetFilename() == file_path:
                foundView = openDoc.GetFirstView()
                break

        if not foundView:
            doc = self.GetDocumentManager().CreateDocument(file_path, wx.lib.docview.DOC_SILENT)
            if doc is None:
                return
            foundView = doc.GetFirstView()

        if foundView:
            foundView.GetFrame().SetFocus()
            foundView.Activate()
            startPos = foundView.PositionFromLine(lineNum)
            foundView.GotoPos(startPos+col)
            if foundView.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER:
                import OutlineService
                self.GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)
                
    def AddInterpreters(self):
        cb = self.ToolbarCombox
        cb.Clear()
        for interpreter in interpretermanager.InterpreterManager().interpreters:
            cb.Append(interpreter.Name,interpreter)
        cb.Append(_("Configuration"),)
        self.SetCurrentInterpreter()
        
    def OnExit(self):
        intellisence.IntellisenceManager().Stop()
        wx.lib.pydocview.DocApp.OnExit(self)
        
    def ShowSplash(self, image):
        """
        Shows a splash window with the given image.  Input parameter 'image' can either be a wx.Bitmap or a filename.
        """
        wx.lib.pydocview.DocApp.ShowSplash(self,image)
        #should pause a moment to show splash image on linux os,otherwise it will show white background on linux
        wx.Yield()
    
    @property
    def OpenProjectPath(self):
        return self._open_project_path
        
    def OpenCommandLineArgs(self):
        """
        Called to open files that have been passed to the application from the
        command line.
        """
        args = sys.argv[1:]
        for arg in args:
            if (wx.Platform != "__WXMSW__" or arg[0] != "/") and arg[0] != '-' and os.path.exists(arg):
                if sysutilslib.isWindows():
                    arg = arg.decode("gbk")
                else:
                    arg = arg.decode("utf-8")
                self.GetDocumentManager().CreateDocument(os.path.normpath(arg), wx.lib.docview.DOC_SILENT)
                if strutils.GetFileExt(arg) == PROJECT_SHORT_EXTENSION:
                    self._open_project_path = arg
        

class IDEDocManager(wx.lib.docview.DocManager):

    # Overriding default document creation.
    def OnFileNew(self, event):
        self.CreateDocument('', wx.lib.docview.DOC_NEW)
##        import NewDialog
##        newDialog = NewDialog.NewDialog(wx.GetApp().GetTopWindow())
##        if newDialog.ShowModal() == wx.ID_OK:
##            isTemplate, object = newDialog.GetSelection()
##            if isTemplate:
##                object.CreateDocument('', wx.lib.docview.DOC_NEW)
##            else:
##                import ProcessModelEditor
##                if object == NewDialog.FROM_DATA_SOURCE:
##                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Database Application"), minimalCreate=False, startingType=object)
##                    wiz.RunWizard()
##                elif object == NewDialog.FROM_DATABASE_SCHEMA:
##                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Database Application"), minimalCreate=False, startingType=object)
##                    wiz.RunWizard()
##                elif object == NewDialog.FROM_SERVICE:
##                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Service Application"), minimalCreate=False, startingType=object)
##                    wiz.RunWizard()
##                elif object == NewDialog.CREATE_SKELETON_APP:
##                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Skeleton Application"), minimalCreate=False, startingType=object)
##                    wiz.RunWizard()
##                elif object == NewDialog.CREATE_PROJECT:
##                    import ProjectEditor
##                    for temp in self.GetTemplates():
##                        if isinstance(temp,ProjectEditor.ProjectTemplate):
##                            temp.CreateDocument('', wx.lib.docview.DOC_NEW)
##                            break
##                else:
##                    assert False, "Unknown type returned from NewDialog"


    def SelectDocumentPath(self, templates, flags, save):
        """
        Under Windows, pops up a file selector with a list of filters
        corresponding to document templates. The wxDocTemplate corresponding
        to the selected file's extension is returned.

        On other platforms, if there is more than one document template a
        choice list is popped up, followed by a file selector.

        This function is used in wxDocManager.CreateDocument.
        """
        descr = ''
        for temp in templates:
            if temp.IsVisible():
                if len(descr) > 0:
                    descr = descr + _('|')
                descr = descr + temp.GetDescription() + _(" (") + temp.GetFileFilter() + _(") |") + temp.GetFileFilter()  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        if sysutilslib.isWindows():
            descr = _("All Files(*.*)|*.*|%s") % descr  # spacing is important, make sure there is no space after the "|", it causes a bug on wx_gtk
        else:
            descr = _("All Files (*)|*|%s") % descr 
            
        dlg = wx.FileDialog(self.FindSuitableParent(),
                               _("Select a File"),
                               wildcard=descr,
                               style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
        # dlg.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
            
        if path:  
            theTemplate = self.FindTemplateForPath(path)
            return (theTemplate, path)
        
        return (None, None)       

    def OnFileSaveAs(self, event):
        doc = self.GetCurrentDocument()
        if not doc:
            return
        self.SaveAsDocument(doc)
            
    def SaveAsDocument(self,doc):
        old_file_path = doc.GetFilename()
        if not doc.SaveAs():
            return
        if doc.IsWatched:
            doc.FileWatcher.RemoveFile(old_file_path)

    def OnPrintSetup(self, event):
        data = wx.PageSetupDialogData()
        data.SetMarginTopLeft( (15, 15) )
        data.SetMarginBottomRight( (15, 15) )
        #data.SetDefaultMinMargins(True)
        data.SetPaperId(wx.PAPER_LETTER)
        dlg = wx.PageSetupDialog(wx.GetApp().GetTopWindow(), data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetPageSetupData()
            tl = data.GetMarginTopLeft()
            br = data.GetMarginBottomRight()
        dlg.Destroy()

    def OnCreateFileHistory(self):
        """
        A hook to allow a derived class to create a different type of file
        history. Called from Initialize.
        """
        max_files = int(wx.ConfigBase_Get().Read("MRULength","9"))
        enableMRU = wx.ConfigBase_Get().ReadInt("EnableMRU", True)
        if enableMRU:
            self._fileHistory = wx.FileHistory(maxFiles=max_files,idBase=ID_MRU_FILE1)

#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import BitmapFromImage

#----------------------------------------------------------------------

def getIDESplashBitmap():
    splash_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "tt.png")
    splash_image = wx.Image(splash_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(splash_image)



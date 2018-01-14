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
import shutil
import TabbedFrame
import Interpreter
import noval.parser.intellisence as intellisence
import noval.parser.config as parserconfig

# Required for Unicode support with python
# site.py sets this, but Windows builds don't have site.py because of py2exe problems
# If site.py has already run, then the setdefaultencoding function will have been deleted.
if hasattr(sys,"setdefaultencoding"):
    sys.setdefaultencoding("utf-8")

_ = wx.GetTranslation
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

        # Suppress non-fatal errors that might prompt the user even in cases
        # when the error does not impact them.
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

        if not ACTIVEGRID_BASE_IDE:
            import CmdlineOptions
            if isInArgs(CmdlineOptions.DEPLOY_TO_SERVE_PATH_ARG, args):
                CmdlineOptions.enableDeployToServePath()
            
        if not wx.lib.pydocview.DocApp.OnInit(self):
            return False

        if not ACTIVEGRID_BASE_IDE:
            self.ShowSplash(getSplashBitmap())
        else:
            self.ShowSplash(getIDESplashBitmap())

        import STCTextEditor
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
        import Interpreter
##        import UpdateLogIniService
                            
        if not ACTIVEGRID_BASE_IDE:
            import activegrid.model.basedocmgr as basedocmgr
            import UpdateService
            import DataModelEditor
            import ProcessModelEditor
            import DeploymentService
            import WebServerService
            import WelcomeService
            import XFormEditor
            import PropertyService
            import WSDLEditor
            import WsdlAgEditor
            import XPathEditor
            import XPathExprEditor
            import ImportServiceWizard
            import RoleEditor
            import HelpService
            import WebBrowserService
            import SQLEditor
        _EDIT_LAYOUTS = True
        if not ACTIVEGRID_BASE_IDE:
            import BPELEditor
            if _EDIT_LAYOUTS:
                import LayoutEditor
                import SkinEditor
                        

        # This creates some pens and brushes that the OGL library uses.
        # It should be called after the app object has been created, but
        # before OGL is used.
        ogl.OGLInitialize()

        config = wx.Config(self.GetAppName(), style = wx.CONFIG_USE_LOCAL_FILE)
        if not config.Exists("MDIFrameMaximized"):  # Make the initial MDI frame maximize as default
            config.WriteInt("MDIFrameMaximized", True)
        if not config.Exists("MDIEmbedRightVisible"):  # Make the properties embedded window hidden as default
            config.WriteInt("MDIEmbedRightVisible", False)

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

        if not ACTIVEGRID_BASE_IDE:
            dplTemplate = DeploymentService.DeploymentTemplate(docManager,
                _("Deployment"),
                "*.dpl",
                _("Deployment"),
                _(".dpl"),
                _("Deployment Document"),
                _("Deployment View"),
                XmlEditor.XmlDocument,
                XmlEditor.XmlView,
                wx.lib.docview.TEMPLATE_INVISIBLE,
                icon = DeploymentService.getDPLIcon())
            docManager.AssociateTemplate(dplTemplate)

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

        if not ACTIVEGRID_BASE_IDE:
            identityTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("Identity"),
                    "*.xacml",
                    _("Identity"),
                    _(".xacml"),
                    _("Identity Configuration"),
                    _("Identity View"),
                    RoleEditor.RoleEditorDocument,
                    RoleEditor.RoleEditorView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = XmlEditor.getXMLIcon())
            docManager.AssociateTemplate(identityTemplate)

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
        
        if not ACTIVEGRID_BASE_IDE and _EDIT_LAYOUTS:
            layoutTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("Layout"),
                    "*.lyt",
                    _("Layout"),
                    _(".lyt"),
                    _("Renderer Layouts Document"),
                    _("Layout View"),
                    # Fix the fonts for CDATA XmlEditor.XmlDocument,
                    # XmlEditor.XmlView,
                    LayoutEditor.LayoutEditorDocument,
                    LayoutEditor.LayoutEditorView,
                    icon = LayoutEditor.getLytIcon())
            docManager.AssociateTemplate(layoutTemplate)

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

        if not ACTIVEGRID_BASE_IDE:
            processModelTemplate = ProcessModelEditor.ProcessModelTemplate(docManager,
                _("Process"),
                "*.bpel",
                _("Process"),
                _(".bpel"),
                _("Process Document"),
                _("Process View"),
                ProcessModelEditor.ProcessModelDocument,
                ProcessModelEditor.ProcessModelView,
                wx.lib.docview.TEMPLATE_NO_CREATE,
                icon = ProcessModelEditor.getProcessModelIcon())
            docManager.AssociateTemplate(processModelTemplate)

        projectTemplate = ProjectEditor.ProjectTemplate(docManager,
                _("Project"),
                "*.agp",
                _("Project"),
                _(".agp"),
                _("Project Document"),
                _("Project View"),
                ProjectEditor.ProjectDocument,
                ProjectEditor.ProjectView,
                wx.lib.docview.TEMPLATE_NO_CREATE,
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

        if not ACTIVEGRID_BASE_IDE:
            dataModelTemplate = DataModelEditor.DataModelTemplate(docManager,
                _("Schema"),
                "*.xsd",
                _("Schema"),
                _(".xsd"),
                _("Schema Document"),
                _("Schema View"),
                DataModelEditor.DataModelDocument,
                DataModelEditor.DataModelView,
                icon = DataModelEditor.getDataModelIcon())
            docManager.AssociateTemplate(dataModelTemplate)
            
        if not ACTIVEGRID_BASE_IDE:
            wsdlagTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("Service Reference"),
                    "*.wsdlag",
                    _("Project"),
                    _(".wsdlag"),
                    _("Service Reference Document"),
                    _("Service Reference View"),
                    WsdlAgEditor.WsdlAgDocument,
                    WsdlAgEditor.WsdlAgView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = WSDLEditor.getWSDLIcon())
            docManager.AssociateTemplate(wsdlagTemplate)

        if not ACTIVEGRID_BASE_IDE and _EDIT_LAYOUTS:
            layoutTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("Skin"),
                    "*.skn",
                    _("Skin"),
                    _(".skn"),
                    _("Application Skin"),
                    _("Skin View"),
                    SkinEditor.SkinDocument,
                    SkinEditor.SkinView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = getSkinIcon())
            docManager.AssociateTemplate(layoutTemplate)

        if not ACTIVEGRID_BASE_IDE:
            sqlTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("SQL"),
                    "*.sql",
                    _("SQL"),
                    _(".sql"),
                    _("SQL Document"),
                    _("SQL View"),
                    SQLEditor.SQLDocument,
                    SQLEditor.SQLView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = SQLEditor.getSQLIcon())
            docManager.AssociateTemplate(sqlTemplate)

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

        if not ACTIVEGRID_BASE_IDE:
            wsdlTemplate = WSDLEditor.WSDLTemplate(docManager,
                    _("WSDL"),
                    "*.wsdl",
                    _("WSDL"),
                    _(".wsdl"),
                    _("WSDL Document"),
                    _("WSDL View"),
                    WSDLEditor.WSDLDocument,
                    WSDLEditor.WSDLView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = WSDLEditor.getWSDLIcon())
            docManager.AssociateTemplate(wsdlTemplate)

        if not ACTIVEGRID_BASE_IDE:
            xformTemplate = wx.lib.docview.DocTemplate(docManager,
                    _("XForm"),
                    "*.xform",
                    _("XForm"),
                    _(".xform"),
                    _("XForm Document"),
                    _("XForm View"),
                    XFormEditor.XFormDocument,
                    XFormEditor.XFormView,
                    wx.lib.docview.TEMPLATE_NO_CREATE,
                    icon = XFormEditor.getXFormIcon())
            docManager.AssociateTemplate(xformTemplate)

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

        
        # Note:  Child document types aren't displayed in "Files of type" dropdown
        if not ACTIVEGRID_BASE_IDE:
            viewTemplate = wx.lib.pydocview.ChildDocTemplate(docManager,
                _("XForm"),
                "*.none",
                _("XForm"),
                _(".bpel"),
                _("XFormEditor Document"),
                _("XFormEditor View"),
                XFormEditor.XFormDocument,
                XFormEditor.XFormView,
                icon = XFormEditor.getXFormIcon())
            docManager.AssociateTemplate(viewTemplate)

        if not ACTIVEGRID_BASE_IDE:
            bpelTemplate = wx.lib.pydocview.ChildDocTemplate(docManager,
                _("BPEL"),
                "*.none",
                _("BPEL"),
                _(".bpel"),
                _("BPELEditor Document"),
                _("BPELEditor View"),
                BPELEditor.BPELDocument,
                BPELEditor.BPELView,
                icon = ProcessModelEditor.getProcessModelIcon())
            docManager.AssociateTemplate(bpelTemplate)

        if not ACTIVEGRID_BASE_IDE:
            dataModelChildTemplate = wx.lib.pydocview.ChildDocTemplate(docManager,
                _("Schema"),
                "*.none",
                _("Schema"),
                _(".xsd"),
                _("Schema Document"),
                _("Schema View"),
                DataModelEditor.DataModelChildDocument,
                DataModelEditor.DataModelView,
                icon = DataModelEditor.getDataModelIcon())
            docManager.AssociateTemplate(dataModelChildTemplate)
        
        textService             = self.InstallService(STCTextEditor.TextService())
        pythonService           = self.InstallService(PythonEditor.PythonService("Python Interpreter",embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        perlService             = self.InstallService(PerlEditor.PerlService())
        phpService              = self.InstallService(PHPEditor.PHPService())
        if not ACTIVEGRID_BASE_IDE:
            propertyService     = self.InstallService(PropertyService.PropertyService("Properties", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT))
        projectService          = self.InstallService(ProjectEditor.ProjectService("Projects", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT))
        findService             = self.InstallService(FindInDirService.FindInDirService())
        if not ACTIVEGRID_BASE_IDE:
            webBrowserService   = self.InstallService(WebBrowserService.WebBrowserService())  # this must be before webServerService since it sets the proxy environment variable that is needed by the webServerService.
            webServerService    = self.InstallService(WebServerService.WebServerService())  # this must be after webBrowserService since that service sets the proxy environment variables.
        outlineService          = self.InstallService(OutlineService.OutlineService("Outline", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT))
        filePropertiesService   = self.InstallService(wx.lib.pydocview.FilePropertiesService())
        markerService           = self.InstallService(MarkerService.MarkerService())
        messageService          = self.InstallService(MessageService.MessageService("Search Results", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
    ##    outputService          = self.InstallService(OutputService.OutputService("Output", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        debuggerService         = self.InstallService(DebuggerService.DebuggerService("Debugger", embeddedWindowLocation = wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM))
        if not ACTIVEGRID_BASE_IDE:
            processModelService = self.InstallService(ProcessModelEditor.ProcessModelService())
            viewEditorService   = self.InstallService(XFormEditor.XFormService())
            deploymentService   = self.InstallService(DeploymentService.DeploymentService())
            dataModelService    = self.InstallService(DataModelEditor.DataModelService())
            dataSourceService   = self.InstallService(DataModelEditor.DataSourceService())
            wsdlService         = self.InstallService(WSDLEditor.WSDLService())
            welcomeService      = self.InstallService(WelcomeService.WelcomeService())
        if not ACTIVEGRID_BASE_IDE and _EDIT_LAYOUTS:
            layoutService       = self.InstallService(LayoutEditor.LayoutEditorService())
        extensionService        = self.InstallService(ExtensionService.ExtensionService())
        optionsService          = self.InstallService(wx.lib.pydocview.DocOptionsService(supportedModes=wx.lib.docview.DOC_MDI))
        aboutService            = self.InstallService(wx.lib.pydocview.AboutService(AboutDialog.AboutDialog))
        svnService              = self.InstallService(SVNService.SVNService())
        if not ACTIVEGRID_BASE_IDE:
            helpPath = os.path.join(sysutilslib.mainModuleDir, "activegrid", "tool", "data", "AGDeveloperGuideWebHelp", "AGDeveloperGuideWebHelp.hhp")
            helpService             = self.InstallService(HelpService.HelpService(helpPath))
        if self.GetUseTabbedMDI():
            windowService       = self.InstallService(wx.lib.pydocview.WindowMenuService())
        

        if not ACTIVEGRID_BASE_IDE:
            projectService.AddRunHandler(processModelService)

        # order of these added determines display order of Options Panels
        optionsService.AddOptionsPanel(ProjectEditor.ProjectOptionsPanel)
       ## optionsService.AddOptionsPanel(DebuggerService.DebuggerOptionsPanel)
        if not ACTIVEGRID_BASE_IDE:
            optionsService.AddOptionsPanel(WebServerService.WebServerOptionsPanel)
            optionsService.AddOptionsPanel(DataModelEditor.DataSourceOptionsPanel)
            optionsService.AddOptionsPanel(DataModelEditor.SchemaOptionsPanel)
            optionsService.AddOptionsPanel(WebBrowserService.WebBrowserOptionsPanel)
            optionsService.AddOptionsPanel(ImportServiceWizard.ServiceOptionsPanel)
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
        
        if not ACTIVEGRID_BASE_IDE:
            propertyService.AddViewTypeForBackgroundHandler(DataModelEditor.DataModelView)
            propertyService.AddViewTypeForBackgroundHandler(ProcessModelEditor.ProcessModelView)
            propertyService.AddViewTypeForBackgroundHandler(XFormEditor.XFormView)
            propertyService.AddViewTypeForBackgroundHandler(BPELEditor.BPELView)
            propertyService.AddViewTypeForBackgroundHandler(WSDLEditor.WSDLView)
            propertyService.StartBackgroundTimer()
            
            propertyService.AddCustomCellRenderers(DataModelEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(BPELEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(XFormEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(XPathEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(XPathExprEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(WSDLEditor.GetCustomGridCellRendererDict())
            propertyService.AddCustomCellRenderers(WsdlAgEditor.GetCustomGridCellRendererDict())

            propertyService.AddCustomCellEditors(DataModelEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(BPELEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(XFormEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(XPathEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(XPathExprEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(WSDLEditor.GetCustomGridCellEditorDict())
            propertyService.AddCustomCellEditors(WsdlAgEditor.GetCustomGridCellEditorDict())
        
        if not ACTIVEGRID_BASE_IDE:
            projectService.AddNameDefault(".bpel", projectService.GetDefaultNameCallback)
            projectService.AddNameDefault(".xsd", dataModelService.GetDefaultNameCallback)
            projectService.AddNameDefault(".xform", projectService.GetDefaultNameCallback)
            projectService.AddNameDefault(".wsdl", projectService.GetDefaultNameCallback)
            projectService.AddNameDefault(".wsdlag", projectService.GetDefaultNameCallback)
            projectService.AddNameDefault(".skn", projectService.GetDefaultNameCallback)
            projectService.AddNameDefault(".xacml", projectService.GetDefaultNameCallback)

            projectService.AddFileTypeDefault(".lyt", basedocmgr.FILE_TYPE_LAYOUT)
            projectService.AddFileTypeDefault(".bpel", basedocmgr.FILE_TYPE_PROCESS)
            projectService.AddFileTypeDefault(".xsd", basedocmgr.FILE_TYPE_SCHEMA)
            projectService.AddFileTypeDefault(".wsdlag", basedocmgr.FILE_TYPE_SERVICE)
            projectService.AddFileTypeDefault(".skn", basedocmgr.FILE_TYPE_SKIN)
            projectService.AddFileTypeDefault(".xacml", basedocmgr.FILE_TYPE_IDENTITY)
            projectService.AddFileTypeDefault(".css", basedocmgr.FILE_TYPE_STATIC)
            projectService.AddFileTypeDefault(".js", basedocmgr.FILE_TYPE_STATIC)
            projectService.AddFileTypeDefault(".gif", basedocmgr.FILE_TYPE_STATIC)
            projectService.AddFileTypeDefault(".jpg", basedocmgr.FILE_TYPE_STATIC)
            projectService.AddFileTypeDefault(".jpeg", basedocmgr.FILE_TYPE_STATIC)
            projectService.AddFileTypeDefault(".xform", basedocmgr.FILE_TYPE_XFORM)

        projectService.AddLogicalViewFolderDefault(".agp", _("Projects"))
        projectService.AddLogicalViewFolderDefault(".wsdlag", _("Services"))
        projectService.AddLogicalViewFolderDefault(".wsdl", _("Services"))
        projectService.AddLogicalViewFolderDefault(".xsd", _("Data Models"))
        projectService.AddLogicalViewFolderDefault(".bpel", _("Page Flows"))
        projectService.AddLogicalViewFolderDefault(".xform", _("Pages"))
        projectService.AddLogicalViewFolderDefault(".xacml", _("Security"))
        projectService.AddLogicalViewFolderDefault(".lyt", _("Presentation/Layouts"))
        projectService.AddLogicalViewFolderDefault(".skn", _("Presentation/Skins"))
        projectService.AddLogicalViewFolderDefault(".css", _("Presentation/Stylesheets"))
        projectService.AddLogicalViewFolderDefault(".js", _("Presentation/Javascript"))
        projectService.AddLogicalViewFolderDefault(".html", _("Presentation/Static"))
        projectService.AddLogicalViewFolderDefault(".htm", _("Presentation/Static"))
        projectService.AddLogicalViewFolderDefault(".gif", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".jpeg", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".jpg", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".png", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".ico", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".bmp", _("Presentation/Images"))
        projectService.AddLogicalViewFolderDefault(".py", _("Code"))
        projectService.AddLogicalViewFolderDefault(".php", _("Code"))
        projectService.AddLogicalViewFolderDefault(".pl", _("Code"))
        projectService.AddLogicalViewFolderDefault(".sql", _("Code"))
        projectService.AddLogicalViewFolderDefault(".xml", _("Code"))
        projectService.AddLogicalViewFolderDefault(".dpl", _("Code"))
        
        projectService.AddLogicalViewFolderCollapsedDefault(_("Page Flows"), False)
        projectService.AddLogicalViewFolderCollapsedDefault(_("Pages"), False)
    
        iconPath = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "noval.ico")
        self.SetDefaultIcon(wx.Icon(iconPath, wx.BITMAP_TYPE_ICO))
        if not ACTIVEGRID_BASE_IDE:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT | wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM | wx.lib.pydocview.EMBEDDED_WINDOW_RIGHT
        else:
            embeddedWindows = wx.lib.pydocview.EMBEDDED_WINDOW_TOPLEFT | wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOMLEFT |wx.lib.pydocview.EMBEDDED_WINDOW_BOTTOM
        if self.GetUseTabbedMDI():
            self.frame = TabbedFrame.IDEDocTabbedParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        else:
            self.frame = IDEMDIParentFrame(docManager, None, -1, wx.GetApp().GetAppName(), embeddedWindows=embeddedWindows, minSize=150)
        self.frame.Show(True)
        self.toolbar = self.frame.GetToolBar()
        self.toolbar_combox = self.toolbar.FindControl(DebuggerService.DebuggerService.COMBO_INTERPRETERS_ID)

        wx.lib.pydocview.DocApp.CloseSplash(self)
        self.OpenCommandLineArgs()

        if not projectService.OpenSavedProjects() and not docManager.GetDocuments() and self.IsSDI():  # Have to open something if it's SDI and there are no projects...
            projectTemplate.CreateDocument('', wx.lib.docview.DOC_NEW).OnNewDocument()
            
        tips_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "data", "tips.txt")
            
        # wxBug: On Mac, having the updates fire while the tip dialog is at front
        # for some reason messes up menu updates. This seems a low-level wxWidgets bug,
        # so until I track this down, turn off UI updates while the tip dialog is showing.
        if not ACTIVEGRID_BASE_IDE:
            wx.UpdateUIEvent.SetUpdateInterval(-1)
            UpdateService.UpdateVersionNag()
            appUpdater = UpdateService.AppUpdateService(self)
            appUpdater.RunUpdateIfNewer()
            if not welcomeService.RunWelcomeIfFirstTime():
                if os.path.isfile(tips_path):
                    self.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, 0))
        else:
            if os.path.isfile(tips_path):
                self.ShowTip(docManager.FindSuitableParent(), wx.CreateFileTipProvider(tips_path, 0))
                   
        Interpreter.InterpreterManager().LoadDefaultInterpreter()
        self.AddInterpreters()
        intellisence.IntellisenceManager().generate_default_intellisence_data()
        wx.UpdateUIEvent.SetUpdateInterval(1000)  # Overhead of updating menus was too much.  Change to update every n milliseconds.

        return True
    @property
    def MainFrame(self):
        return self.frame
    @property		
    def ToolbarCombox(self):
        return self.toolbar_combox
        
    def GetCurrentInterpreter(self):
        if 0 == len(Interpreter.InterpreterManager().interpreters):
            return None
        item_index = self.toolbar_combox.GetCurrentSelection()
        if item_index < 0:
            item_index = 0
        data = self.toolbar_combox.GetClientData(item_index)
        if data is None:
            data = self.toolbar_combox.GetClientData(item_index)
        return data
        
    def SetCurrentDefaultInterpreter(self):
        default_interpreter = Interpreter.InterpreterManager().GetDefaultInterpreter()
        if default_interpreter is None:
            self.toolbar_combox.SetSelection(-1)
            return
        for i in range(self.toolbar_combox.GetCount()):
            data = self.toolbar_combox.GetClientData(i)
            if data == default_interpreter:
                self.toolbar_combox.SetSelection(i)
                break
                
    def GotoView(self,file_path,lineNum):
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
			foundView.GotoLine(lineNum)
			startPos = foundView.PositionFromLine(lineNum)
			lineText = foundView.GetCtrl().GetLine(lineNum - 1)
			foundView.SetSelection(startPos, startPos + len(lineText.rstrip("\n")))
			if foundView.GetLangLexer() == parserconfig.LANG_PYTHON_LEXER:
				import OutlineService
				self.GetService(OutlineService.OutlineService).LoadOutline(foundView, lineNum=lineNum)
                
    def AddInterpreters(self):
        cb = self.ToolbarCombox
        cb.Clear()
        for interpreter in Interpreter.InterpreterManager().interpreters:
            cb.Append(interpreter.Name,interpreter)
        cb.Append(_("Configuration"),)
        self.SetCurrentDefaultInterpreter()

class IDEDocManager(wx.lib.docview.DocManager):
    
    # Overriding default document creation.
    def OnFileNew(self, event):
        self.CreateDocument('', wx.lib.docview.DOC_NEW)
        import NewDialog
        newDialog = NewDialog.NewDialog(wx.GetApp().GetTopWindow())
        if newDialog.ShowModal() == wx.ID_OK:
            isTemplate, object = newDialog.GetSelection()
            if isTemplate:
                object.CreateDocument('', wx.lib.docview.DOC_NEW)
            else:
                import ProcessModelEditor
                if object == NewDialog.FROM_DATA_SOURCE:
                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Database Application"), minimalCreate=False, startingType=object)
                    wiz.RunWizard()
                elif object == NewDialog.FROM_DATABASE_SCHEMA:
                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Database Application"), minimalCreate=False, startingType=object)
                    wiz.RunWizard()
                elif object == NewDialog.FROM_SERVICE:
                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Service Application"), minimalCreate=False, startingType=object)
                    wiz.RunWizard()
                elif object == NewDialog.CREATE_SKELETON_APP:
                    wiz = ProcessModelEditor.CreateAppWizard(wx.GetApp().GetTopWindow(), title=_("New Skeleton Application"), minimalCreate=False, startingType=object)
                    wiz.RunWizard()
                elif object == NewDialog.CREATE_PROJECT:
                    import ProjectEditor
                    for temp in self.GetTemplates():
                        if isinstance(temp,ProjectEditor.ProjectTemplate):
                            temp.CreateDocument('', wx.lib.docview.DOC_NEW)
                            break
                else:
                    assert False, "Unknown type returned from NewDialog"

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
       
class IDEMDIParentFrame(wx.lib.pydocview.DocMDIParentFrame):
    
    # wxBug: Need this for linux. The status bar created in pydocview is
    # replaced in IDE.py with the status bar for the code editor. On windows
    # this works just fine, but on linux the pydocview status bar shows up near
    # the top of the screen instead of disappearing. 
    def CreateDefaultStatusBar(self):
       pass

#----------------------------------------------------------------------------
# Icon Bitmaps - generated by encode_bitmaps.py
#----------------------------------------------------------------------------
from wx import BitmapFromImage

#----------------------------------------------------------------------

def getIDESplashBitmap():
    splash_image_path = os.path.join(sysutilslib.mainModuleDir, "noval", "tool", "bmp_source", "splash.jpg")
    splash_image = wx.Image(splash_image_path,wx.BITMAP_TYPE_ANY)
    return BitmapFromImage(splash_image)



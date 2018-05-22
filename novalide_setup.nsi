; 该脚本使用 HM VNISEdit 脚本编辑器向导产生

; 安装程序初始定义常量
!define PRODUCT_NAME "NovalIDE"
!define PRODUCT_VERSION "1.1.0"
!define PRODUCT_PUBLISHER "wukan"
!define PRODUCT_WEB_SITE "http://www.genetalks.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\NovalIDE.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_PROJECT_FILE_EXTENSION ".nov"
!define PRODUCT_PROJECT_FILE "Noval.ProjectFile"
!define PRODUCT_PROJECT_FILE_DESCRIPTION "NovalIDE Project File"
!define PRODUCT_PROJECT_FILE_ICON_KEY "${PRODUCT_PROJECT_FILE}\DefaultIcon"
!define PRODUCT_PROJECT_FILE_OPEN_KEY "${PRODUCT_PROJECT_FILE}\shell\open\command"

SetCompressor lzma

; ------ MUI 现代界面定义 (1.67 版本以上兼容) ------
!include "MUI.nsh"

; MUI 预定义常量
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME
; 许可协议页面
!insertmacro MUI_PAGE_LICENSE "license.txt"
; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY
; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES
; 安装完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\NovalIDE.exe"
!insertmacro MUI_PAGE_FINISH

; 安装卸载过程页面
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装预释放文件
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS
; ------ MUI 现代界面定义结束 ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "NovalIDE_Setup.exe"
InstallDir "$PROGRAMFILES\NovalIDE"
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "dist\wxmsw30u_xrc_vc90.dll"
  CreateDirectory "$SMPROGRAMS\NovalIDE"
  CreateShortCut "$SMPROGRAMS\NovalIDE\NovalIDE.lnk" "$INSTDIR\NovalIDE.exe"
  CreateShortCut "$DESKTOP\NovalIDE.lnk" "$INSTDIR\NovalIDE.exe"
  File "dist\wxmsw30u_stc_vc90.dll"
  File "dist\wxmsw30u_html_vc90.dll"
  File "dist\wxmsw30u_core_vc90.dll"
  File "dist\wxmsw30u_adv_vc90.dll"
  File "dist\wxbase30u_xml_vc90.dll"
  File "dist\wxbase30u_vc90.dll"
  File "dist\wxbase30u_net_vc90.dll"
  File "dist\wxmsw30u_aui_vc90.dll"
  File "dist\wx._xrc.pyd"
  File "dist\wx._wizard.pyd"
  File "dist\wx._windows_.pyd"
  File "dist\wx._stc.pyd"
  File "dist\wx._misc_.pyd"
  File "dist\wx._grid.pyd"
  File "dist\wx._combo.pyd"
  File "dist\wx._gizmos.pyd"
  File "dist\wx._gdi_.pyd"
  File "dist\wx._dataview.pyd"
  File "dist\wx._core_.pyd"
  File "dist\wx._controls_.pyd"
  File "dist\winxpgui.pyd"
  File "dist\wx._aui.pyd"
  File "dist\win32process.pyd"
  File "dist\win32com.shell.shell.pyd"
  File "dist\win32pipe.pyd"
  File "dist\win32gui.pyd"
  File "dist\win32file.pyd"
  File "dist\win32evtlog.pyd"
  File "dist\win32event.pyd"
  File "dist\win32api.pyd"
  File "dist\w9xpopen.exe"
  File "dist\version.txt"
  File "dist\unicodedata.pyd"
  File "dist\psutil._psutil_windows.pyd"
  File "dist\tk85.dll"
  File "dist\tcl85.dll"
  File "dist\select.pyd"
  File "dist\pywintypes27.dll"
  File "dist\pythoncom27.dll"
  File "dist\python27.dll"
  File "dist\pyexpat.pyd"
  File "dist\_sqlite3.pyd"
  File "dist\sqlite3.dll"
  File "dist\NovalIDE.exe"
  File "dist\MSWSOCK.dll"
  File "dist\library.zip"
  File "dist\bz2.pyd"
  File "dist\API-MS-Win-Core-SysInfo-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Synch-L1-1-0.dll"
  File "dist\API-MS-Win-Core-String-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Profile-L1-1-0.dll"
  File "dist\API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
  File "dist\API-MS-Win-Core-ProcessEnvironment-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Misc-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Memory-L1-1-0.dll"
  File "dist\API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Localization-L1-1-0.dll"
  File "dist\API-MS-Win-Core-LibraryLoader-L1-1-0.dll"
  File "dist\API-MS-Win-Core-IO-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Interlocked-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Handle-L1-1-0.dll"
  File "dist\API-MS-Win-Core-ErrorHandling-L1-1-0.dll"
  File "dist\API-MS-Win-Core-DelayLoad-L1-1-0.dll"
  File "dist\API-MS-Win-Core-Debug-L1-1-0.dll"
  File "dist\_win32sysloader.pyd"
  File "dist\_tkinter.pyd"
  File "dist\_ssl.pyd"
  File "dist\_socket.pyd"
  File "dist\_hashlib.pyd"
  File "dist\_ctypes.pyd"
  SetOutPath "$INSTDIR\noval"
  File /r "dist\noval\*.*"
  SetOutPath "$INSTDIR\tcl"
  File /r "dist\tcl\*.*"
  SetOutPath "$APPDATA\NovalIDE\intellisence\builtins"
  File /r "dist\builtins\*.*"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\NovalIDE\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\NovalIDE\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_EXTENSION}" "" "${PRODUCT_PROJECT_FILE}"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE}" "" "${PRODUCT_PROJECT_FILE_DESCRIPTION}"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_ICON_KEY}" "" "$INSTDIR\noval\tool\bmp_source\project.ico"
  WriteRegStr HKCR "${PRODUCT_PROJECT_FILE_OPEN_KEY}" "" "$INSTDIR\NovalIDE.exe $\"%1$\""
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\NovalIDE.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\NovalIDE.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

/******************************
 *  以下是安装程序的卸载部分  *
 ******************************/

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\_ctypes.pyd"
  Delete "$INSTDIR\_hashlib.pyd"
  Delete "$INSTDIR\_socket.pyd"
  Delete "$INSTDIR\_ssl.pyd"
  Delete "$INSTDIR\_tkinter.pyd"
  Delete "$INSTDIR\_win32sysloader.pyd"
  Delete "$INSTDIR\psutil._psutil_windows.pyd"
  Delete "$INSTDIR\API-MS-Win-Core-Debug-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-DelayLoad-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ErrorHandling-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Handle-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Interlocked-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-IO-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-LibraryLoader-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Localization-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Memory-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Misc-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ProcessEnvironment-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-ProcessThreads-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Profile-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-String-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-Synch-L1-1-0.dll"
  Delete "$INSTDIR\API-MS-Win-Core-SysInfo-L1-1-0.dll"
  Delete "$INSTDIR\bz2.pyd"
  Delete "$INSTDIR\library.zip"
  Delete "$INSTDIR\MSWSOCK.dll"
  Delete "$INSTDIR\NovalIDE.exe"
  Delete "$INSTDIR\pyexpat.pyd"
  Delete "$INSTDIR\python27.dll"
  Delete "$INSTDIR\pythoncom27.dll"
  Delete "$INSTDIR\pywintypes27.dll"
  Delete "$INSTDIR\select.pyd"
  Delete "$INSTDIR\tcl85.dll"
  Delete "$INSTDIR\tk85.dll"
  Delete "$INSTDIR\unicodedata.pyd"
  Delete "$INSTDIR\version.txt"
  Delete "$INSTDIR\w9xpopen.exe"
  Delete "$INSTDIR\win32api.pyd"
  Delete "$INSTDIR\win32com.shell.shell.pyd"
  Delete "$INSTDIR\win32event.pyd"
  Delete "$INSTDIR\win32evtlog.pyd"
  Delete "$INSTDIR\win32file.pyd"
  Delete "$INSTDIR\win32gui.pyd"
  Delete "$INSTDIR\win32pipe.pyd"
  Delete "$INSTDIR\win32process.pyd"
  Delete "$INSTDIR\wx._controls_.pyd"
  Delete "$INSTDIR\wx._core_.pyd"
  Delete "$INSTDIR\wx._dataview.pyd"
  Delete "$INSTDIR\wx._gdi_.pyd"
  Delete "$INSTDIR\wx._gizmos.pyd"
  Delete "$INSTDIR\wx._grid.pyd"
  Delete "$INSTDIR\wx._misc_.pyd"
  Delete "$INSTDIR\wx._stc.pyd"
  Delete "$INSTDIR\wx._combo.pyd"
  Delete "$INSTDIR\wx._windows_.pyd"
  Delete "$INSTDIR\wx._wizard.pyd"
  Delete "$INSTDIR\wx._xrc.pyd"
  Delete "$INSTDIR\winxpgui.pyd"
  Delete "$INSTDIR\_sqlite3.pyd"
  Delete "$INSTDIR\sqlite3.dll"
  Delete "$INSTDIR\wx._aui.pyd"
  Delete "$INSTDIR\_sqlite3.pyd"
  Delete "$INSTDIR\sqlite3.dll"
  Delete "$INSTDIR\wxbase30u_net_vc90.dll"
  Delete "$INSTDIR\wxbase30u_vc90.dll"
  Delete "$INSTDIR\wxbase30u_xml_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_adv_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_core_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_html_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_stc_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_xrc_vc90.dll"
  Delete "$INSTDIR\wxmsw30u_aui_vc90.dll"
  Delete "$INSTDIR\NovalIDE.exe.log"

  Delete "$SMPROGRAMS\NovalIDE\Uninstall.lnk"
  Delete "$SMPROGRAMS\NovalIDE\Website.lnk"
  Delete "$DESKTOP\NovalIDE.lnk"
  Delete "$SMPROGRAMS\NovalIDE\NovalIDE.lnk"

  RMDir "$SMPROGRAMS\NovalIDE"

  RMDir /r "$INSTDIR\tcl"
  RMDir /r "$INSTDIR\noval"

  RMDir "$INSTDIR"
/*******************************************
  Delete "$APPDATA\NovalIDE\intellisence\*.*"
  RMDir "$APPDATA\NovalIDE\intellisence\builtins\2"
  RMDir "$APPDATA\NovalIDE\intellisence\builtins\3"
  RMDir "$APPDATA\NovalIDE\intellisence\builtins"
  RMDir /r "$APPDATA\NovalIDE\intellisence"
*******************************************/
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd

#-- 根据 NSIS 脚本编辑规则，所有 Function 区段必须放置在 Section 区段之后编写，以避免安装程序出现未可预知的问题。--#

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "您确实要完全移除 $(^Name) ，及其所有的组件？" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) 已成功地从您的计算机移除。"
FunctionEnd

import wx
import threading
import noval.util.appdirs as appdirs
import noval.parser.utils as parserutils
import os
from wx.lib.pubsub import pub as Publisher
_ = wx.GetTranslation

NOVAL_MSG_UI_DOWNLOAD_PROGRESS = "noval.msg.download.progress"

class DownloadProgressDialog(wx.GenericProgressDialog):
    
    def __init__(self,parent,file_sie,file_name):
        welcome_msg = _("Please wait a minute for Downloading")
        wx.GenericProgressDialog.__init__(self,_("Downloading %s") % file_name,welcome_msg,\
                maximum = file_sie, parent=parent,\
                    style = 0|wx.PD_APP_MODAL|wx.PD_CAN_ABORT)
        Publisher.subscribe(self.UpdateProgress,NOVAL_MSG_UI_DOWNLOAD_PROGRESS)

        self.keep_going = True
        self._progress = 0
        
    def UpdateProgress(self,temp,msg):
        keep_going,_ = self.Update(temp,msg)
        #print temp,keep_going
        self.keep_going = keep_going

class FileDownloader(object):
    
    def __init__(self,file_length,file_name,req,call_back=None):
        self._file_size = file_length
        self._file_name = file_name
        self._req = req
        self._call_back = call_back
    
    def StartDownload(self):
        download_progress_dlg = DownloadProgressDialog(wx.GetApp().GetTopWindow(),int(self._file_size),self._file_name)
        download_tmp_path = os.path.join(appdirs.getAppDataFolder(),"download")
        if not os.path.exists(download_tmp_path):
            parserutils.MakeDirs(download_tmp_path)
        download_file_path = os.path.join(download_tmp_path,self._file_name)
        try:
            self.DownloadFile(download_file_path,download_progress_dlg)
        except:
            return
        download_progress_dlg.Raise()

    def DownloadFile(self,download_file_path,download_progress_dlg):
        t = threading.Thread(target=self.DownloadFileContent,args=(download_file_path,self._req,download_progress_dlg,))
        t.start()
        
    def DownloadFileContent(self,download_file_path,req,download_progress_dlg):
        is_cancel = False
        f = open(download_file_path, "wb")
        try:
            for chunk in req.iter_content(chunk_size=512):
                if chunk:
                    if not download_progress_dlg.keep_going:
                        is_cancel = True
                        break
                    f.write(chunk)
                    download_progress_dlg._progress += len(chunk)
                    Publisher.sendMessage(NOVAL_MSG_UI_DOWNLOAD_PROGRESS,temp = download_progress_dlg._progress,msg="")
        except Exception as e:
            wx.MessageBox(_("Download fail:%s") % e,style=wx.OK|wx.ICON_ERROR)
            wx.CallAfter(download_progress_dlg.Destroy)
            return
        f.close()
        download_progress_dlg.keep_going = False
        wx.CallAfter(download_progress_dlg.Destroy)
        if self._call_back is not None and not is_cancel:
            self._call_back(download_file_path)
import threading

class OutputThread(threading.Thread):
    
    def __init__(self,stdout,process,text_ctrl):
        threading.Thread.__init__(self)
        self._stdout = stdout
        self._process = process
        self._text_ctrl = text_ctrl
        self._is_running = False
        
    def run(self):
        while True:
            self._is_running = True
            out = self._stdout.readline()
            if out == b'':
                if self._process.poll() is not None:
                    self._is_running = False
                    break
            else:
                self._text_ctrl.AddLines(out)
      
                    
    @property
    def IsRunning(self):
        return self._is_running
            
        

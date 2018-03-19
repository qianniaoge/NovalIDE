import threading

class OutputThread(threading.Thread):
    
    def __init__(self,stdout,process,output_ctrl):
        threading.Thread.__init__(self)
        self._stdout = stdout
        self._process = process
        self._output_ctrl = output_ctrl
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
                self._output_ctrl.call_back(out)
      
                    
    @property
    def IsRunning(self):
        return self._is_running
            
        

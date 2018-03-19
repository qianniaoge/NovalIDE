import wx

#used to decorate the func or method which is used in multithread which is very convenient
def call_after(func): 
    def _wrapper(*args, **kwargs): 
        return wx.CallAfter(func, *args, **kwargs) 
    return _wrapper 

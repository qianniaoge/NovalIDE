import wx

def call_after(func): 
    def _wrapper(*args, **kwargs): 
        return wx.CallAfter(func, *args, **kwargs) 
    return _wrapper 

#----------------------------------------------------------------------------
# Name:         noval.py
# Purpose:
#
# Author:       wukan
#
# Created:      3/30/17
# CVS-ID:       $Id$
# Copyright:    (c) 2018- NovalIDE, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------
import wx.lib.pydocview
from tool import IDE
from util import sysutils

import os
import sys
sys.stdout = sys.stderr

if sysutils.isWindows():
    def exitfunc():
        pass

    #register exit func to prevent pop warn dialog when windows exe program exit which is converted by py2exe
    sys.exitfunc = exitfunc

def main():
    # This is here as the base IDE entry point.  Only difference is that -baseide is passed.
    sys.argv.append('-baseide');
    # Put activegrid dir in path so python files can be found from py2exe
    # This code should never do anything when run from the python interpreter
    execDir = os.path.dirname(sys.executable)
    try:
        sys.path.index(execDir)
    except ValueError:
        sys.path.append(execDir)
    app = IDE.IDEApplication(redirect = False)
    app.GetTopWindow().Raise()  # sometimes it shows up beneath other windows.  e.g. running self in debugger
    app.MainLoop()


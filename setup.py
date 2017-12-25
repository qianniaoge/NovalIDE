from distutils.core import setup
import py2exe

setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
      options = { "py2exe":{"dll_excludes":["MSVCP90.dll"]}},
    data_files=[("noval/tool/bmp_source", ["noval/tool/bmp_source/noval.ico"]),
                ("noval/tool/data",["noval/tool/data/tips.txt"])],)

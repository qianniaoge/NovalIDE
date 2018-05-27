import sys
if sys.platform == "win32":
    from distutils.core import setup
    import py2exe
    import glob
    import modulefinder
    import win32com.client
    is_debug = False

    #this block code used to add win32com.shell and win32com.shellcon module to library.zip
    ###******************************************###########
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath('win32com', p)
    for extra in ['win32com.taskscheduler']:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
    ###******************************************###########
    
    for i,argv in enumerate(sys.argv):
        if argv == "debug" or argv == "-debug":
            is_debug = True
            del sys.argv[i]

    if is_debug:
        print 'executable run in console mode'
        setup(console=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = { "py2exe":{"dll_excludes":["MSVCP90.dll"],"packages": ['wx.lib.pubsub']}},
                data_files=[("noval/tool/bmp_source", glob.glob("noval/tool/bmp_source/*.ico") + glob.glob("noval/tool/bmp_source/*.jpg") \
                             + glob.glob("noval/tool/bmp_source/*.png") + glob.glob("noval/tool/bmp_source/*.gif")),
                    ("noval/tool/data",["noval/tool/data/tips.txt"]),
                     ("noval/parser",glob.glob("noval/parser/*.py")),
                      ("noval/locale/en_US/LC_MESSAGES",['noval/locale/en_US/LC_MESSAGES/novalide.mo']),
                       ("noval/locale/zh_CN/LC_MESSAGES",['noval/locale/zh_CN/LC_MESSAGES/novalide.mo']),],)
    else:
        print 'executable run in windows mode'
        setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = { "py2exe":{"dll_excludes":["MSVCP90.dll"],"packages": ['wx.lib.pubsub','csv']}},
                data_files=[("noval/tool/bmp_source", glob.glob("noval/tool/bmp_source/*.ico") + glob.glob("noval/tool/bmp_source/*.jpg") \
                             + glob.glob("noval/tool/bmp_source/*.png") + glob.glob("noval/tool/bmp_source/*.gif")),
                    ("noval/tool/bmp_source/toolbar",glob.glob("noval/tool/bmp_source/toolbar/*.png")),
                    ("noval/tool",glob.glob("noval/tool/DebuggerHarness.py")),
                    ("noval/tool/data",["noval/tool/data/tips.txt"]),
                     ("noval/parser",glob.glob("noval/parser/*.py")),
                      ("noval/locale/en_US/LC_MESSAGES",['noval/locale/en_US/LC_MESSAGES/novalide.mo']),
                       ("noval/locale/zh_CN/LC_MESSAGES",['noval/locale/zh_CN/LC_MESSAGES/novalide.mo']),
                       ('',['version.txt'])],)

elif sys.platform.find('linux') != -1:
    from distutils.core import setup
    from setuptools import find_packages
    
    with open("version.txt") as f:
        version = f.read()

    install_requires = ['wxpython','pyyaml',"watchdog","chardet","pyperclip","psutil"]
    setup(name='NovalIDE',
            version = version,
            description='''noval ide is a cross platform code editor''',
            author='wukan',
            author_email='wekay102200@sohu.com',
            url='https://github.com/noval102200/Noval.git',
            license='Genetalks',
            packages=find_packages(),
            install_requires=install_requires,
            zip_safe=False,
            test_suite='noval.tests',
            package_data={
                'noval': [
                        'tool/data/intellisence/builtins/2/*',
                        'tool/data/intellisence/builtins/3/*',
                        'tool/data/*.txt',
                        'tool/bmp_source/*', 
                        'tool/bmp_source/toolbar/*', 
                        'locale/en_US/LC_MESSAGES/*.mo',
                        'locale/zh_CN/LC_MESSAGES/*.mo'
                        ],
            },
            data_files = [('',['version.txt']),],
            classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy'
            ],
            entry_points="""
            [console_scripts]
            NovalIDE = noval.noval:main
            """
)



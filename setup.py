import sys
if sys.platform == "win32":
    from distutils.core import setup
    import py2exe
    import glob

    setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
          options = { "py2exe":{"dll_excludes":["MSVCP90.dll"]}},
            data_files=[("noval/tool/bmp_source", glob.glob("noval/tool/bmp_source/*.ico") + glob.glob("noval/tool/bmp_source/*.jpg") + glob.glob("noval/tool/bmp_source/*.png")),
                ("noval/tool/data",["noval/tool/data/tips.txt"]),
                 ("noval/parser",glob.glob("noval/parser/*.py")),
                  ("noval/locale/en_US/LC_MESSAGES",['noval/locale/en_US/LC_MESSAGES/novalide.mo']),
                   ("noval/locale/zh_CN/LC_MESSAGES",['noval/locale/zh_CN/LC_MESSAGES/novalide.mo']),],)

elif sys.platform.find('linux') != -1:
    from distutils.core import setup
    from setuptools import find_packages
    
    with open("version.txt") as f:
        version = f.read()

    install_requires = ['wxpython','pyyaml',"watchdog","chardet","pyperclip"]
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
                        'tool/bmp_source/*',
                        'tool/data/*',
                        'tool/data/intellisence/builtins/*',
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



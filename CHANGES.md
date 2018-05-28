Changelog
=========

Changes with latest version of NovalIDE
----------------------------------------------

Version 1.0.0 -------------2017-12-23

- support Cross Platform editor
- support HTML,python,text xml lanauge 
- auto load default python interpreter
- find replace text in open document
- find text in directory files
- convinient to install editor in windows and linux system
- auto detect file modified or deleted without editor
- support mru files and delete invalid file path
- enable show tips when startup application
- multi document tabbed frame style
- auto detect python file encoding when save python document
- enable code margin fold style
- simple support debug or run a python script in editor or terminator 


Version 1.0.1 -------------2017-12-27

- enable check python file syntax
- show caret line background color
- enbale open file path in terminator
- set debug or run script execution dir is script path
- support python script path contains chinese
- optimise debug run mode
- enable kill or stop debug run process
- enable debug have stdin input python script
- enable colorize error output or input text
- enable terminate all running process
- change application splash image
- delete ide splash embed bitmap data
- enable user choose one interpreter from multiple choices
- auto analyse intepreter interllisence data
- go to definition of text


Version 1.0.2 -------------2018-01-08

- implement go to word definition in global scope search
- interligent analyze class self property in class object method
- remove duplicate child name of class object property
- find definition in document scope
- enable sort in outline service
- enable custom context menu in debug output tab,and enable word wrap in line
- can only launch one find or replace dialog instance
- enable to add one interpreter to editor
- add configure interpreter function
- display interpreter sys path list ,builtin modules and environment
- make install packages run in windows system
- show smart analyse progress dialog
- implement file resource view
- enable find location in outline view
- initial implement code completion
- import and from import code completion
- complete type object completion 


Version 1.0.3 -------------2018-01-16

- smart show module and class member completion
- recognize python base type object and show it's member info
- set intellisense database version
- set virtual scope with database members file
- show progress dialog whhen find text in files
- repair search text progress dialog bug
- enable set script parameter and environment
- support create unit test frame of script
- repair py2exe call subprocess.popen error
- repair cannot inspect cp936 encoding error
- add insert and advance edit function
- separate common intellisense data path and builtin intellisense data,which on linux system ,they are not equal
- add builtin intellisense data to linux build package
- enable insert date,comment template and python coding declare to text
- enable gotodef and listmembers shortcut in menu item
- default use right edge mode in text document
- set xml and html parser fold style
- support parse relative import 
- repair relative import position bug
- upgrade intellisense database generation and update database version to 1.0.2
- support go to defition of from import modules and their childs
- optimise memberlist sort algorithm


Version 1.0.4 -------------2018-02-04

- repair show tip bug
- repair open all files bug in linux system
- auto analyse sys moudles intellisense data
- improve and supplement chinese translation
- smart anlalyse class base inherited classes members
- analyse from import members
- update install instructions on linux system of readme
- allow user choose line eol mode
- add icon to Python Interpreter and Search Result,Debug View
- enable click plus button of dir tree to expand child item in resource view
- supplement chinese translation of wx stock id items
- repair bug when load interpreters and set first add interpreter as default interpreter
- repair check syntax bug in python2.6
- partly support smart analyse interpreter data of python3 version
- optimise outline load parse data mechanism and repair load file bug
- implement new auto completion function of menu item
- fix package install bug on linux os
- fix serious bug when load python3 interprter and smart analyse its data when convert to windows exe with py2exe
- add debug mode which will be convert to console exe with py2exe
- prevent pop warn dialog when the windows exe program exit which is converted by py2exe
- fix 'cannot import name Publisher' error when use py2exe convert to windows exe
- fix run python script which path has chinese character on linux os
- close threading.Thread VERBOSE mode in debugger service
- increase mru history file count from 9 to 20 and allow user to set the max MRU item count
- fix right up menu of document position
- fix bug when run script path contain chinese character on windows os


Version 1.0.5 -------------2018-02-13

- enable to open current python interpreter on tools menu
- allow user to set use MRU menu or not
- implement navigation to next or previous position
- analyse class static members intellisense data
- analyse class and function doc declaration
- simple implement project creation
- analyse builtin member doc declaration and show its calltip information
- separate builtin intellisense data to python 2 and 3
- repair python3 parse function args bug
- fix autoindent bug when enter key is pressed
- Sets when a backspace pressed should do indentation unindents
- modify project document definition ,add project name and interpreter to it 
- fix the error of set progress max range when search text in dir 
- enable set enviroment variable of interpreter when debug or run python script
- fix output truncated error when debug python script 
- add function and class argment show tip
- fix application exit bug when interpreter has been uninstalled
- fix the bug of subprocess.popen run error on some computer cause application cann't startup
- set calltip background and foreground color
- fix the bug when debug run python window program the window interface is hidden
- show python interpreter pip package list in configuration
- disable or enable back delete key when debug output has input according to the caret pos
- when load interpreter configuation list,at least select one interprter in datalist view control
- fix get python3 release version error,which is alpha,beta,candidate and final version

Version 1.0.6 -------------2018-03-6

- add drive icon and volument name on resource view
- use multithread to load python pip package
- fix image view display context menu bug
- change python and text file icon
- add project file icon to project and show project root
- show local icon of file when scan disk file on resource view
- when add point and brace symbol to document text will delete selected text
- save folder open state when swith toggle button on resource view
- parse main function node and show main function in outline view
- fix parse file content bug where content encoding is error
- fix parse collections package recursive bug in python3
- when current interpreter is analysing,load intellisense data at end
- try to get python help path in python loation if help path is empty on windows os
- fix image size is not suitable which will invoke corruption on linux os.convernt png image to 16*16
- fix the bug when click the first line of search results view
- allow add or remove python search path,such as directory,zip ,egg and wheel file path
- add new python virtual env function
- fix environment variable contains unicode character bug
- fix add python virtual env bug on linux os
- fix the bug when double click the file line and show messagebox which cause wxEVT_MOUSE_CAPTURE_LOST problem
- adjust the control layout of configuration page
- remove the left gap if python interpreter view
- allow load builtin python interpreter
- enable debug file in python interpreter view with builtin interpreter
- optimise the speed of load outline of parse tree
- change startup splash image of application
- fix bug when show startup splash image on linux os

Version 1.0.7 -------------2018-03-23

- query the running process to stop or not when application exit
- fix the bug when the interpreter path contain empty blank string
- add icon of unittest treectrl item
- add import files to project and show import file progress
- beautify unittest wizard ui interface
- add new project wizard on right menu of project view
- fix the bug of import files on linux os
- fix the coruption problem of debug run script with builtin interpreter
- fix the bug of open file in file explower on windows os
- optimise and fix bug of import project files
- copy files to project dest dir when import files
- fix the bug when load saved projects
- show prompt message dialog when the import files to project have already exist
- enable filter file types when import files to project 
- fix getcwd coruption bug on linux os when currrent path is deleted
- fix file observer bug on linux os when the watched path is deleted
- add open project and save project memu item on project menu and implement the menu action
- add monitor to currrent project to generate intellisense data of the project
- add project icon of NovalIDE project file with the .nov file extension and associated with NovalIDE application
- enable click on the .nov file to open NovalIDE project
- enable add ,delete and manage breakpoints
- enable add package folder in project
- correct the error number count of search text result in project
- enable open project from command line and set as current project
- update nsis script to write project file extension and icon to regsitry
- fix the serious bug of close and delete project
- enable filter file types when import files to project
- fix the bug of project file or path contains chinese character

Version 1.0.8 -------------2018-04-01

- fix create virtualenv bug on linux os
- fix the bug of file watcher when save as the same file
- update english to chinese translation
- replace toolbar old image with new image
- fix a serious breakpoint debug bug
- add icon to meneu item
- enable install and uninstall package
- add breakpoint debug menu item
- show detail progress information of install and uninstall package
- fix the bug of goto definition bug
- fix the bug of kill process fail on linux os
- kill the smart analyse processes when application exit and smart analyse is running
- add project id attribute to project instance
- enable mutiple selections on project files
- delete project regkey config when close project or delete project
- show styled text of binary document
- show file encoding of document on status bar
- save document cache position when close frame and load position data when open document
- enable modify project name with label edit
- set the startup script of project and bold the project startup item
- enable run and debug last settings of project or file
- fix the bug of create unittest when parse file error
- fix the check syntax error of python script bug
- save all open project documents before run
- fix the bug of close all run tabs
- fix the bug of save chinese text document
- allow set the default file encoding of text document
- fix the bug of pip path contains blank when install and uninstall package
- fix the bug of close debugger window when application exit


Version 1.1.0 -------------2018-05-16

- fix the bug of deepcopy run parameter iter attribute
- create novalide web server project
- enable check for app update version on menu item
- enable download update version from web server
- establish the simple novalide web server
- enable delete files and folder from proeject and local file system
- check update version info when application start up
- support install package with pip promote to root user on linux os
- set default logger debug level to info level
- close open project files when delete project files or folders
- support auto check ,download and install new version of app on linux os
- enable rename folder and file item of project
- when renane folder of project,rename the open folder files
- watch the project document,and alarm the document change event
- fix the bug of load python when app startup on some computer
- fix the bug of null encoding when set file encoding
- enable copy and cut files of project,and paste to another position
- add csv module to library zip when use py2exe to pack
- allow add python package folder to project folder item
- fix a bug of load python interpreter from config
- enable drag file items to move files of project to dest
- fix the save as document bug whe the save as document filename is already opened

Version 1.1.1 -------------2018-05-26

- 菜单添加访问官方网站入口
- 允许用户删掉软件自带解释器（内建），只保留一个非内建解释器
- 添加当前文档到工程时，同时修改当前文档路径并优化处理方式
- 设置关闭文档快捷键
- 优化nsis安装脚本，生成带版本号名称的安装包,卸载包时保留智能提示数据文件
- 优化中文文件编码，修复默认ascii文件不能保存中文字符的问题
- 区分python2和python3编码方式处理，python2包含中文提示输入编码声明，python3不需要
- 文本文件另存为时可以选择任何文件后缀类型以及文本后缀类型
- 修复另存文本文件的bug
- 修复运行脚本时脚本目录不存成导致程序异常的BUG
- 项目名称为空时自动恢复正常，取消弹出警告对话框
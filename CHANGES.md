Changelog
=========

Changes with latest version of NovalIDE
----------------------------------------------

Version 1.0.0 -------------2017-12-23
1.support Cross Platform editor
2.support HTML,python,text xml lanauge 
3.auto load default python interpreter
4.find replace text in open document
5.find text in directory files
6.convinient to install editor in windows and linux system
7.auto detect file modified or deleted without editor
8.support mru files and delete invalid file path
9.enable show tips when startup application
10.multi document tabbed frame style
11.auto detect python file encoding when save python document
12.enable code margin fold style
13.simple support debug or run a python script in editor or terminator 


Version 1.0.1 -------------2017-12-27
1.enable check python file syntax
2.show caret line background color
3.enbale open file path in terminator
4.set debug or run script execution dir is script path
5.support python script path contains chinese
6.optimise debug run mode
7.enable kill or stop debug run process
8.enable debug have stdin input python script
9.enable colorize error output or input text
10.enable terminate all running process
11.change application splash image
12.delete ide splash embed bitmap data
13.enable user choose one interpreter from multiple choices
14.auto analyse intepreter interllisence data
15.go to definition of text


Version 1.0.2 -------------2018-01-08
1.implement go to word definition in global scope search
2.interligent analyze class self property in class object method
3.remove duplicate child name of class object property
4.find definition in document scope
5.enable sort in outline service
6.enable custom context menu in debug output tab,and enable word wrap in line
7.can only launch one find or replace dialog instance
8.enable to add one interpreter to editor
9.add configure interpreter function
10.display interpreter sys path list ,builtin modules and environment
11.make install packages run in windows system
12.show smart analyse progress dialog
13.implement file resource view
14.enable find location in outline view
15.initial implement code completion
16.import and from import code completion
17.complete type object completion 


Version 1.0.3 -------------2018-01-16
1.smart show module and class member completion
2.recognize python base type object and show it's member info
3.set intellisense database version
4.set virtual scope with database members file
5.show progress dialog whhen find text in files
6.repair search text progress dialog bug
7.enable set script parameter and environment
8.support create unit test frame of script
9.repair py2exe call subprocess.popen error
10.repair cannot inspect cp936 encoding error
11.add insert and advance edit function
12.separate common intellisense data path and builtin intellisense data,which on linux system ,they are not equal
13.add builtin intellisense data to linux build package
14.enable insert date,comment template and python coding declare to text
15.enable gotodef and listmembers shortcut in menu item
16.default use right edge mode in text document
17.set xml and html parser fold style
18.support parse relative import 
19.repair relative import position bug
20.upgrade intellisense database generation and update database version to 1.0.2
21.support go to defition of from import modules and their childs
22.optimise memberlist sort algorithm


Version 1.0.4 -------------2018-02-04
1.repair show tip bug
2.repair open all files bug in linux system
3.auto analyse sys moudles intellisense data
4.improve and supplement chinese translation
5.smart anlalyse class base inherited classes members
6.analyse from import members
7.update install instructions on linux system of readme
8.allow user choose line eol mode
9.add icon to Python Interpreter and Search Result,Debug View
10.enable click plus button of dir tree to expand child item in resource view
11.supplement chinese translation of wx stock id items
12.repair bug when load interpreters and set first add interpreter as default interpreter
13.repair check syntax bug in python2.6
14.partly support smart analyse interpreter data of python3 version
15.optimise outline load parse data mechanism and repair load file bug
17.implement new auto completion function of menu item
18.fix package install bug on linux os
19.fix serious bug when load python3 interprter and smart analyse its data when convert to windows exe with py2exe
20.add debug mode which will be convert to console exe with py2exe
21.prevent pop warn dialog when the windows exe program exit which is converted by py2exe
22.fix 'cannot import name Publisher' error when use py2exe convert to windows exe
23.fix run python script which path has chinese character on linux os
24.close threading.Thread VERBOSE mode in debugger service
25.increase mru history file count from 9 to 20 and allow user to set the max MRU item count
26.fix right up menu of document position
27.fix bug when run script path contain chinese character on windows os


Version 1.0.5 -------------2018-02-13
1.enable to open current python interpreter on tools menu
2.allow user to set use MRU menu or not
3.add simple navigation to next or previous position function
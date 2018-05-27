![NovalIDE](noval/tool/bmp_source/logo.png)

简介
----------------------------------

NovalIDE是一款开源，跨平台，而且免费的国产多功能，轻便的Python IDE，大小才12M

- 有出色的语法高亮功能,支持多种语言,python,c/c++,html,javascript,xml,css等
- 自动检测，并加载Python解释器，允许用户自由添加删除解释器，并选择相应的解释器运行脚本
- 支持函数智能提示和代码自动完成
- 支持新建NovalIDE工程和从现有代码创建工程，新建工程类型将包括应用程序，Django,Flask,wxPython,Py2exe,Win32,GTK，控制台程序等
- 自动智能分析解释器系统路径下模块文件，并生成智能提示使用的数据文件
- 类VS风格的可停靠窗口，多文档切换模式
- 各种复杂的编辑功能，支持高级编辑功能
- 可以调试以及模拟真实环境的终端方式运行python脚本
- 自动模拟Python解释器环境，并内嵌解释器，不用安装任何python环境，即可运行python程序
- 可以断点调试，单步调试python代码，并能监视，查看变量以及堆栈变化，以及添加，删除，管理断点等
- 可以自由终止，重启以及运行调试环境
- 支持运行多个解释器版本，并在不同版本之间进行切换
- 支持中英文多个语言版本
- 灵活的高扩展性，提供开放式接口支持程序员开发自定义插件
- 强大的包管理器，通过pip一键式安装卸载Python包
- 支持python2.6,2.7版本以及python3.x版本,2.6以前版本未实测

官方网址：[http://www.novalide.com](http://www.novalide.com/)

相关文章: [对一款优秀国产Python IDE---NovalIDE的体验](https://my.oschina.net/u/3728672/blog/1817030)

软件概貌: ![NovalIDE_Screen](noval/tool/bmp_source/images/banner_01.png)

编译
----------------------------------

### 源码依赖包

- Python2.7.11 [Windows下载地址](https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi)
- wxPython(3.0.2) [Windows下载地址](https://jaist.dl.sourceforge.net/project/wxpython/wxPython/3.0.2.0/wxPython3.0-win32-3.0.2.0-py27.exe)
- pywin32(only windows) [Windows下载地址](https://github.com/mhammond/pywin32/releases/download/b223/pywin32-223.win32-py2.7.exe)
- py2exe(only windows) [Windows下载地址](https://jaist.dl.sourceforge.net/project/py2exe/py2exe/0.6.9/py2exe-0.6.9.win64-py2.7.amd64.exe)
- wmi(only windows)
- psutil
- watchdog
- chardet
- pyperclip

### Windows编译

- **源码运行**

```
下载Python2.7，以及wxPython3.0.2，pywin32，py2exe安装包，下载地址见上。
git clone https://gitee.com/wekay/NovalIDE.git
cd NovalIDE

pip install psutil
pip install watchdog
pip install chardet
pip install pyperclip
pip install wmi

运行Python NovalIDE.py
```

- **源码打包**

```
运行python buildide或者python setup.py py2exe
生成dist目下运行NovalIDE.exe
```

### Linux编译

- **Ubuntu**

sudo apt-get install python-wxtools

- **Centos**

sudo yum install wxPython-devel

- ***编译步骤**

...
git clone https://gitee.com/wekay/NovalIDE.git
cd Noval
运行python setup.py install，权限不够请用sudo
最后运行Python NovalIDE.py或者直接运行NovalIDE命令
...

安装
----------------------------------

### Windows安装

从官网：[http://www.novalide.com](http://www.novalide.com/)下载[Windows版本](http://www.novalide.com/member/download_app?lang=zh_cn&os_name=win32)

点击NovalIDE_Setup.exe并依次按安装向导安装，直到完成。

![NovalIDE_WINDOWS_INSTALL](noval/tool/bmp_source/images/windows_insall.png)

### Linux安装

- **Ubuntu**

sudo apt-get install python-wxtools

- **Centos**

sudo yum install wxPython-devel

- ***安装步骤**

...
从官网：[http://www.novalide.com](http://www.novalide.com/)下载[Linux版本](http://www.novalide.com/member/download_app?lang=zh_cn&os_name=linux)
运行命令:tar -xvf NovalIDE.tar.gz解压安装包:NovalIDE.tar.gz
cd NovalIDE-x.x.x
运行sudo python setup.py install
最后输入命令NovalIDE来运行IDE。
...

功能截图
----------------------------------

- 智能提示
![CodeTip1](noval/tool/bmp_source/images/banner_02.png)
![CodeTip2](noval/tool/bmp_source/images/banner_03.png)
![CodeTip3](noval/tool/bmp_source/images/banner_04.png)

- 解释器配置
![InterpreterManage](noval/tool/bmp_source/images/banner_06.png)

- 包管理器
![PipManage](noval/tool/bmp_source/images/banner_07.png)

- 中英文切换
![Zh_En](noval/tool/bmp_source/images/zh_en.png)

- 单元测试
![UnitTest](noval/tool/bmp_source/images/banner_08.png)

- 新建工程
![NewProject](noval/tool/bmp_source/images/project.png)

- 自动加载解释器
![LoadInterpreter](noval/tool/bmp_source/images/interpreter.png)

特别感谢
----------------------------------

- 感谢华俊女士帮助制作官网特效
- 感谢回想之后同学提供官网域名

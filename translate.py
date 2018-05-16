
import subprocess
import os

cmd = r'python C:\Python27\Tools\i18n\pygettext.py -a -d novalide -o novalide.pot -p D:\env\Noval\noval\locale D:\env\Noval\noval'

subprocess.call(cmd)

os.system(r'"C:\Program Files (x86)\Poedit\Poedit.exe" G:\work\Noval\noval\locale\novalide.pot')
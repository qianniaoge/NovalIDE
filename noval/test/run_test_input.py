#coding:utf-8
import os
import sys
import subprocess

#f = open("input.txt")

#sys.stdin = f

#os.popen("python test_input.py")
f = subprocess.Popen(["python","/opt/env/test_boto3/test_input.py"],stdin = subprocess.PIPE,stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
f.stdin.write("ggg\n")
f.stdin.write("ddd\n")
f.stdin.write("bbb\n")
f.stdin.write("ccc\n")


print f.stdout.read()


#f.close()

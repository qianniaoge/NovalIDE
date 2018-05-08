#coding:utf-8
import os
import sql
import datetime
from basedb import *
from noval.tool import Singleton
import noval.util.appdirs as appdirs

import getpass
import noval.util.sysutils as sysutilslib
import datetime
import noval.parser.utils as parserutils
import requests
import json
from noval.util.logger import app_debugLogger

if sysutilslib.isWindows():
    import wmi
    import pythoncom

    def get_host_info():
        c = wmi.WMI ()
        os_name = ''
        os_bit = ''
        sn = ''
        for os_sys in c.Win32_OperatingSystem():
            os_name = os_sys.Caption.encode("UTF8").strip()
            os_bit = os_sys.OSArchitecture.encode("UTF8")
        for physical_disk in c.Win32_DiskDrive():
            sn = physical_disk.SerialNumber.strip()
        return os_name,os_bit,sn
else:
    import platform
    def get_host_info():
        os_name = platform.platform()
        os_bit = platform.architecture()[0]
        sn = 'unkown disk sn'
        r = os.popen("ls -l /dev/disk/by-uuid")
        content = r.read()
        for line in content.split('\n'):
            if line.find("->") != -1:
                sn = line.split()[8].strip()
                break
        return os_name,os_bit,sn

class UserDataDb(BaseDb):
    
    USER_DATA_DB_NAME = "data.db"
    DB_VERSION = "1.0.1"
    ###HOST_SERVER_ADDR = 'http://127.0.0.1:8000'
    HOST_SERVER_ADDR = 'http://www.novalide.com'
    #设置该类是单例
    __metaclass__ = Singleton.SingletonNew

    def __init__(self):
        if sysutilslib.isWindows():
            pythoncom.CoInitialize()
        db_dir = os.path.join(appdirs.getAppDataFolder(),"cache")
        if not os.path.exists(db_dir):
            parserutils.MakeDirs(db_dir)
        self.data_id = None
        self.user_id = None
        db_path = os.path.join(db_dir,self.USER_DATA_DB_NAME)
        super(UserDataDb,self).__init__(db_path)
        self.init_data_db()
        if parserutils.CompareDatabaseVersion(self.DB_VERSION,self.GetDbVersion()):
            self.close()
            os.remove(db_path)
            BaseDb.__init__(self,db_path)
            self.init_data_db()

    @classmethod
    def get_db(cls):
        return UserDataDb()

    def init_data_db(self):
        table_already_exist_flag = 'already exists'
        #创建user表，表存在时不抛异常
        try:
            self.create_table(sql.CREATE_USER_TABLE_SQL,"user")
        except sqlite3.OperationalError,e:
            if str(e).find(table_already_exist_flag) == -1:
                print e
                return 

        try:
            self.create_table(sql.CREATE_USER_DATA_TABLE_SQL,"data")
        except sqlite3.OperationalError,e:
            if str(e).find(table_already_exist_flag) == -1:
                print e
                return 

    def CreateUser(self):
        os_name,os_bit,sn = get_host_info()
        insert_sql = '''
            insert into user(os_bit,os,sn,user_name,version) values (?,?,?,?,?)
        '''
        data = [(os_bit,os_name,sn,getpass.getuser(),self.DB_VERSION)]
        self.save(insert_sql,data)
        
    def GetDbVersion(self):
        sql = "select * from user"
        result = self.fetchone(sql)
        if not result:
            return self.DB_VERSION
        return result[9]

    def GetUser(self):
        sql = "select * from user"
        result = self.fetchone(sql)
        if not result:
            self.CreateUser()
            result = self.fetchone(sql)
        self.user_id = result[0]
        if result[1] == None:
            api_addr = '%s/member/getuser' % (self.HOST_SERVER_ADDR)
            sn = result[4]
            data = self.RequestData(api_addr,arg = {'sn':sn})
            if data is not None and data['code'] != 0:
                api_addr = '%s/member/createuser' % (self.HOST_SERVER_ADDR)
                sn = result[4]
                args = {
                    'sn':sn,
                    'os_bit':result[3],
                    'os_name':result[5],
                    'user_name':result[2]
                }
                data = self.RequestData(api_addr,arg = args,method='post')
                if data is not None and data['code'] == 0:
                    member_id = data['member_id']
                    update_sql = '''
                        update user set user_id='%s' where id=%d
                    ''' % (member_id,self.user_id )
                    self.update(update_sql)
        
    def RecordStart(self):
        self.GetUser()
        insert_sql = '''
            insert into data(user_id,app_version) values (?,?)
        '''
        data = [(self.user_id,sysutilslib.GetAppVersion()),]
        self.data_id = self.save(insert_sql,data)
        
    def RecordEnd(self):
        if self.data_id is None or self.user_id is None:
            return
        update_sql = '''
            update data set end_time='%s' where id=%d
        ''' % (datetime.datetime.now(),self.data_id )
        self.update(update_sql)
        
    def QueryRecord(self):
        sql = "select * from data where id=%d" % self.data_id
        for result in self.fetchall(sql):
            print result
            
    def GetMemberId(self,user_id):
        sql = "select * from user where id=%d" % user_id
        result = self.fetchone(sql)
        if not result:
            return None
        return result[1]
            
    def ShareUserData(self):
        sql = "select * from data"
        for result in self.fetchall(sql):
            if not result[3]:
                api_addr = '%s/member/share_data' % (self.HOST_SERVER_ADDR)
                member_id = self.GetMemberId(result[1])
                if not member_id:
                    continue
                args = {
                    'member_id':member_id,
                    'start_time':result[4],
                    'end_time':result[5],
                    'app_version':result[2],
                }
                data = self.RequestData(api_addr,arg = args,method='post')
                if data is not None and data['code'] == 0:
                    update_sql = '''
                        update data set submited=1 where id=%d
                    ''' % result[0]
                    self.update(update_sql)
            else:
                delete_sql = '''
                delete from data where id=%d
                '''%result[0]
                self.delete(delete_sql)

    def RequestData(self,addr,arg,method='get',timeout = None):
        '''
            发送http api请求,并保存Cookies
        '''
        params = {}
        try:
            if timeout is not None:
                params['timeout'] = timeout
            req = None
            if method == 'get':
                params['params'] = arg
                req = requests.get(addr,**params)
            elif method == 'post':
                req = requests.post(addr,data = arg,**params)
            return req.json()
        except Exception as e:
            app_debugLogger.error('open %s error:%s' ,addr,e)
        return None
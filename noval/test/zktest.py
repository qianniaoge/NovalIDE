# coding: utf-8
# zktest.py

import logging
from os.path import basename, join

from zkclient import ZKClient, zookeeper, watchmethod
import socket
import fcntl
import struct
import json

logging.basicConfig(
    level = logging.DEBUG,
    format = "[%(asctime)s] %(levelname)-8s %(message)s"
)

log = logging

def get_ip_address(ifname):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),  0x8915,\
                 struct.pack('256s', ifname[:15]))[20:24])


def get_name_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname) 
    ip = get_ip_address('eth0')
    return ip,hostname

class GJZookeeper(object):

    #ZK_HOST = "localhost:2181"
    ZK_HOST = "10.0.0.211:2181"
    ROOT = "/ceph"
    MONITOR_PATH = join(ROOT, "monitor")
    MDS_PATH = join(ROOT, "mds")
    OSD_PATH = join(ROOT, "osd")
    MASTERS_NUM = 1
    TIMEOUT = 10000

    def __init__(self, verbose = True):
        self.VERBOSE = verbose
        self.masters = []
        self.is_master = False
        self.path = None

        self.zk = ZKClient(self.ZK_HOST, timeout = self.TIMEOUT)
        self.say("login ok!")
        self.init_ceph_data()
        self.append_osd()

    def init_ceph_data(self):
        """
        create the zookeeper node if not exist
        """
        nodes = (self.ROOT, self.MONITOR_PATH,self.MDS_PATH)
        ip,hostname = get_name_ip()

        for node in nodes:
            if not self.zk.exists(node):
                try:
                    self.zk.create(node, "")
                except:
                    pass
            data = {
                'ip':ip,
                'hostname':hostname
            }
            data_str = json.dumps(data)
            self.zk.set(node,data_str)
    @property
    def is_slave(self):
        return not self.is_master

    def append_osd(self):

        ip,hostname = get_name_ip()
        osd_node_path = self.zk.create(self.OSD_PATH + "/osd_", "{}",flags=zookeeper.EPHEMERAL|zookeeper.SEQUENCE)
        #self.zk.create(osd_node_path + "/alive", "", flags=zookeeper.EPHEMERAL)
        child = self.zk.get_children(self.OSD_PATH)
        osd_number = len(child)
        osd_data_path = '/var/local/osd%d' % (osd_number)
        data = {
            'ip':ip,
            'hostname':hostname,
            'path':osd_data_path,
            'order':osd_number
        }
        data_str = json.dumps(data)
        self.zk.set(osd_node_path,data_str)

    def register(self):
        """
        register a node for this worker
        """
        self.path = self.zk.create(self.WORKERS_PATH + "/worker_", "", flags=zookeeper.EPHEMERAL | zookeeper.SEQUENCE)
        self.path = basename(self.path)
        self.say("register ok! I'm %s" % self.path)
        # check who is the master
        self.get_master()

    def get_master(self):
        """
        get children, and check who is the smallest child
        """
        @watchmethod
        def watcher(event):
            print event,'-----------------------'
            self.say("child changed, try to get master again.")
            self.get_master()

        children = self.zk.get_children(self.WORKERS_PATH, watcher)
        children.sort()
        self.say("%s's children: %s" % (self.WORKERS_PATH, children))

        # check if I'm master
        self.masters = children[:self.MASTERS_NUM]
        if self.path in self.masters:
            self.is_master = True
            self.say("I've become master!")
        else:
            self.say("%s is masters, I'm slave" % self.masters)


    def say(self, msg):
        """
        print messages to screen
        """
        if self.VERBOSE:
            if self.path:
                if self.is_master:
                    log.info("[ %s(%s) ] %s" % (self.path, "master" , msg))
                else:
                    log.info("[ %s(%s) ] %s" % (self.path, "slave", msg))
            else:
                log.info(msg)

def main():
    gj_zookeeper = GJZookeeper()

if __name__ == "__main__":
    main()
    import time
    time.sleep(1000)

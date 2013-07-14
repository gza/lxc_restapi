#!/usr/bin/env python

import time
import argparse

""" Load driver """
from lxc_restapi_driver import LxcRestapiNodeDriver

def main(args):

    #uncomment to enable http debug logging
    #from libcloud.common.base import LoggingConnection
    #LoggingConnection.log = open("/dev/stderr", "w")
    
    url = "http://%s:%s" % (args.ip, args.port)
    
    driver = LxcRestapiNodeDriver(url=url)
    container_name = "demolibcloud"
    
    for node in driver.list_nodes():
        if node.name == container_name:
            print("found %s, destroying it " % node.name)
            driver.destroy_node(node)
    
    print("creating node")
    node = driver.create_node(name=container_name)
        #For now, no need to specify images or size, it is alpha
        #template is always ubuntu
        #full support is expected later...
    
    #@TODO implement wait
    time.sleep(10)
    
    print("Listing nodes")
    for node in driver.list_nodes():
        print("%s, %s" % (node.name, node.public_ips))
    
    print("destroying demonstration node")
    driver.destroy_node(node)

                    
if  __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Lxc Restful Libcloud Example.')
    parser.add_argument('--ip', 
                        nargs='?',
                        help='Ip address to connect to (default: 127.0.0.1)',
                        default="127.0.0.1")
    parser.add_argument('--port',
                        nargs='?',
                        help='tcp port to connect to (default: 8080)',
                        default="8080")
    
    args = parser.parse_args()    
    main(args)
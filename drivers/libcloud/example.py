#!/usr/bin/env python

import time

""" Load driver """
from lxc_api import LxcApiNodeDriver

#uncomment to enable http debug logging
#from libcloud.common.base import LoggingConnection
#LoggingConnection.log = open("/dev/stderr", "w")

driver = LxcApiNodeDriver()
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

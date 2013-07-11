# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Dummy Driver

@note: This driver is out of date
"""
import uuid
import socket
import struct
import json

from libcloud.common.base import Connection, JsonResponse
from libcloud.common.base import LoggingConnection, LoggingHTTPConnection, LibcloudHTTPSConnection
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver, NodeLocation
from libcloud.compute.types import Provider, NodeState

Provider.LXCAPI = "LxcApi"

class LxcApiConnection(Connection):
    """
    LxcApi connection class just for defaults :)
    """
    base_url = "http://localhost:8080"
    responseCls = JsonResponse
    conn_classes = (LoggingHTTPConnection, LibcloudHTTPSConnection)
    
    def __init__(self, *args, **kwargs):
        super(LxcApiConnection, self).__init__(*args, **kwargs)

    def request(self, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(
            {'Content-type': 'application/json', 'Accept': 'application/json'})

        return super(LxcApiConnection, self).request(**kwargs)

class LxcApiNodeDriver(NodeDriver):
    """
    Dummy node driver

    This is a fake driver which appears to always create or destroy
    nodes successfully.

    >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
    >>> driver = DummyNodeDriver(0)
    >>> node=driver.create_node()
    >>> node.public_ips[0]
    '127.0.0.3'
    >>> node.name
    'dummy-3'

    If the credentials you give convert to an integer then the next
    node to be created will be one higher.

    Each time you create a node you will get a different IP address.

    >>> driver = DummyNodeDriver(22)
    >>> node=driver.create_node()
    >>> node.name
    'dummy-23'

    """
    connectionCls =  LxcApiConnection
    name = "LxcApi Node Provider"
    website = 'http://example.com'
    type = Provider.LXCAPI

    NODE_STATE_MAP = {
      "STOPPED": NodeState.TERMINATED,
      "STARTING": NodeState.PENDING,
      "RUNNING": NodeState.RUNNING,
      "STOPPING": NodeState.PENDING,
      "ABORTING": NodeState.PENDING,
      "FREEZING": NodeState.PENDING,
      "FROZEN": NodeState.PENDING,
      "THAWED": NodeState.UNKNOWN
      }
    
    def __init__(self, *args, **kwargs ):
        """
        @param  creds: Credentials
        @type   creds: C{str}

        @rtype: C{None}
        """
        if 'host' in kwargs:
            self.connectionCls.host = kwargs['host']
        if 'port' in kwargs:
            self.connectionCls.port = kwargs['port']
        if 'base_url' in kwargs:
            self.connectionCls.base_url = kwargs['base_url']
   
        self.connection = LxcApiConnection()

    def get_uuid(self, unique_field=None):
        """

        @param  unique_field: Unique field
        @type   unique_field: C{bool}
        @rtype: L{UUID}
        """
        return str(uuid.uuid4())

    def list_nodes(self):
        """
        List the nodes known to a particular driver;
        There are two default nodes created at the beginning

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node_list=driver.list_nodes()
        >>> sorted([node.name for node in node_list ])
        ['dummy-1', 'dummy-2']

        each item in the list returned is a node object from which you
        can carry out any node actions you wish

        >>> node_list[0].reboot()
        True

        As more nodes are added, list_nodes will return them

        >>> node=driver.create_node()
        >>> node.size.id
        's1'
        >>> node.image.id
        'i2'
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-3']

        @inherits: L{NodeDriver.list_nodes}
        """
        listing = self.connection.request(action="/v1/containers", method="GET").parse_body()
        retval = []
        for node in listing['containers']:
            retval.append(self.get_node(node['name']))
        
        return retval

    def reboot_node(self, node):
        """
        Sets the node state to rebooting; in this dummy driver always
        returns True as if the reboot had been successful.

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> node=driver.create_node()
        >>> from libcloud.compute.types import NodeState
        >>> node.state == NodeState.RUNNING
        True
        >>> node.state == NodeState.REBOOTING
        False
        >>> driver.reboot_node(node)
        True
        >>> node.state == NodeState.REBOOTING
        True

        Please note, dummy nodes never recover from the reboot.

        @inherits: L{NodeDriver.reboot_node}
        """
        node.state = NodeState.REBOOTING
        response = self.connection.request(action="/v1/containers/%s/actions/reboot" % node.name, method="POST")
        node.state = NodeState.RUNNNING
        
        return response.success()

    def destroy_node(self, node):
        """
        Sets the node state to terminated and removes it from the node list

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> from libcloud.compute.types import NodeState
        >>> node = [node for node in driver.list_nodes() if node.name == 'dummy-1'][0]
        >>> node.state == NodeState.RUNNING
        True
        >>> driver.destroy_node(node)
        True
        >>> node.state == NodeState.RUNNING
        False
        >>> [node for node in driver.list_nodes() if node.name == 'dummy-1']
        []

        @inherits: L{NodeDriver.destroy_node}
        """
        response = self.connection.request(action="/v1/containers/%s/actions/stop" % node.name, method="POST")
        response = self.connection.request(action="/v1/containers/%s" % node.name , method="DELETE")
        if response.success():
            node.state = NodeState.TERMINATED
            return True
        else:
            return False

    def list_images(self, location=None):
        """
        Returns a list of images as a cloud provider might have

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([image.name for image in driver.list_images()])
        ['Slackware 4', 'Ubuntu 9.04', 'Ubuntu 9.10']

        @inherits: L{NodeDriver.list_images}
        """
        return [
            NodeImage(id=1, name="ubuntu", driver=self)
        ]

    def list_sizes(self, location=None):
        """
        Returns a list of node sizes as a cloud provider might have

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([size.ram for size in driver.list_sizes()])
        [128, 512, 4096, 8192]

        @inherits: L{NodeDriver.list_images}
        """

        return [
            NodeSize(id=1,
                     name="Small",
                     ram=128,
                     disk=4,
                     bandwidth=500,
                     price=4,
                     driver=self)
        ]

    def list_locations(self):
        """
        Returns a list of locations of nodes

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([loc.name + " in " + loc.country for loc in driver.list_locations()])
        ['Island Datacenter in FJ', 'London Loft in GB', "Paul's Room in US"]

        @inherits: L{NodeDriver.list_locations}
        """
        return [NodeLocation(0, '', '', self)]

    def create_node(self, **kwargs):
        """
        Creates a dummy node; the node id is equal to the number of
        nodes in the node list

        >>> from libcloud.compute.drivers.dummy import DummyNodeDriver
        >>> driver = DummyNodeDriver(0)
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2']
        >>> nodeA = driver.create_node()
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-3']
        >>> driver.create_node().name
        'dummy-4'
        >>> driver.destroy_node(nodeA)
        True
        >>> sorted([node.name for node in driver.list_nodes()])
        ['dummy-1', 'dummy-2', 'dummy-4']

        @inherits: L{NodeDriver.create_node}
        """
        name = kwargs['name']
        container = {
                     "cgroups": [],
                     "name": name,
                     "conf": [],
                     "template": {"name":"ubuntu", "args":[]}
                     }
        
        self.connection.request(action="/v1/containers", method="POST", data=json.dumps(container))
        self.connection.request(action="/v1/containers/%s/actions/start" % name, method="POST")
        return self.get_node(name)
    
    def get_node(self, name):
        response = self.connection.request(action="/v1/containers/%s" % name, method="GET")
        container = response.parse_body()
        
        try:
            state = self.NODE_STATE_MAP[container['state']]
        except KeyError:
            state = NodeState.UNKNOWN
                    
        return Node( id=container['name'],
                     name=container['name'],
                     state=state,
                     public_ips=container['ips'],
                     private_ips=[],
                     driver=self,
                     image=self.list_images()[0])
    
def _ip_to_int(ip):
    return socket.htonl(struct.unpack('I', socket.inet_aton(ip))[0])


def _int_to_ip(ip):
    return socket.inet_ntoa(struct.pack('I', socket.ntohl(ip)))

if __name__ == "__main__":
    import doctest

    doctest.testmod()

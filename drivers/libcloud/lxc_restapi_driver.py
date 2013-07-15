
"""
LxcRestapi driver

@note: This driver is in alpha state
"""
import uuid
import json

from libcloud.common.base import Connection, JsonResponse
from libcloud.common.base import LoggingConnection, LoggingHTTPConnection, LibcloudHTTPSConnection
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver, NodeLocation
from libcloud.compute.types import Provider, NodeState

Provider.LXCRESTAPI = "LxcRestapi"

class LxcRestapiConnection(Connection):
    """
    LxcRestapi connection class
    """
    url = "http://localhost:8080/v1"
    responseCls = JsonResponse
    conn_classes = (LoggingHTTPConnection, LibcloudHTTPSConnection)
    
    def __init__(self, *args, **kwargs):
        if 'url' not in kwargs:    
            kwargs['url'] = self.url     
        super(LxcRestapiConnection, self).__init__(*args, **kwargs)

    def request(self, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
            
        kwargs['headers'].update(
            {'Content-type': 'application/json', 'Accept': 'application/json'})
                
        return super(LxcRestapiConnection, self).request(**kwargs)

class LxcRestapiNodeDriver(NodeDriver):
    """
    LxcRestapi node driver

    This is a driver for lxc_restapi

    >>> from lxc_restapi_driver import LxcRestapiNodeDriver
    >>> driver = LxcRestapiNodeDriver()
    >>> node=driver.create_node(name="demolibcloud")
    >>> node.public_ips[0]
    '127.0.0.3'
    >>> node.name
    'dummy-3'
    """
    
    connectionCls =  LxcRestapiConnection
    name = "LxcRestapi Node Provider"
    website = 'https://github.com/gza/lxc_restapi'
    type = "LXCAPI"

    #@todo: figure out what thawed state means
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
        if 'url' in kwargs:
            self.connectionCls.url = kwargs['url']
        super(LxcRestapiNodeDriver, self).__init__('n/a', **kwargs)
    
    def get_uuid(self, unique_field=None):
        """

        @param  unique_field: Unique field
        @type   unique_field: C{bool}
        @rtype: L{UUID}
        """
        return str(uuid.uuid4())

    def list_nodes(self):
        """
        @inherits: L{NodeDriver.list_nodes}
        """
        listing = self.connection.request(action="/v1/containers", method="GET").parse_body()
        retval = []
        for node in listing['containers']:
            retval.append(self.get_node(node['name']))
        
        return retval

    def reboot_node(self, node):
        """
        @inherits: L{NodeDriver.reboot_node}
        """
        node.state = NodeState.REBOOTING
        response = self.connection.request(action="/v1/containers/%s/actions/reboot" % node.name, method="POST")
        node.state = NodeState.RUNNING
        
        return response.success()

    def destroy_node(self, node):
        """
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
        @todo: implement template listing 
        
        @inherits: L{NodeDriver.list_images}
        """
        return [
                NodeImage(id="ubuntu.lucid", 
                          name="ubuntu.lucid", 
                          extra={"template_name":"ubuntu",
                                  "template_args":[{"key":"release","val":"lucid"}]},
                          driver=self),
                NodeImage(id="ubuntu.precise",
                          name="ubuntu.precise",
                          extra={"template_name":"ubuntu",
                                  "template_args":[{"key":"release","val":"precise"}]},
                          driver=self)
        ]

    def list_sizes(self, location=None):
        """
        @todo: implement with cgroup 
        
        Returns a list of node sizes as a cloud provider might have
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
        @note: Only one Location with Lxc
        
        Returns a list of locations of nodes
        @inherits: L{NodeDriver.list_locations}
        """
        return [NodeLocation(0, '', '', self)]

    def create_node(self, **kwargs):
        """
        Creates a container node; the node id is equal to his name

        @inherits: L{NodeDriver.create_node}
        """
        default = "ubuntu.precise"
        template = {"name":"ubuntu", "args":[]}
        if 'image' not in kwargs:
            kwargs['image'] = default
            
        for image in self.list_images():
            if image.name ==  kwargs['image']:
                template = {"name":image.extra["template_name"],
                            "args":image.extra["template_args"]
                            }
       
        name = kwargs['name']
        container = {
                     "cgroups": [],
                     "name": name,
                     "conf": [],
                     "template": template
                     }
        
        self.connection.request(action="/v1/containers", method="POST", data=json.dumps(container))
        self.connection.request(action="/v1/containers/%s/actions/start" % name, method="POST")
        return self.get_node(name)
    
    def get_node(self, name):
        """
        Converts a json container data from rest webservice to node format
        @return: Node
        """
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
    
if __name__ == "__main__":
    import doctest

    doctest.testmod()

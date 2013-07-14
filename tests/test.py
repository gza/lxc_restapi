#!/usr/bin/env python3


""" 
This is a port of lxc's python api test but by rest api client 
"""

import argparse, json
import uuid, time

import requests

API_ROOT = "http://localhost:8080/v1"

def keyval_list_to_dict(data):
    retval = {}
    for item in data:
        key = item['key']
        val = item['value']
        if key in retval:
            #key used twice, assuming it wants an array
            if isinstance(retval[key], str):
                oldval = retval[key]
                retval[key] = [oldval]
            retval[key].append(val)
        else:
            retval[key] = val
    return retval

def dict_to_keyval_list(data):
    retval = []
    for key, val in data.items():
        if isinstance(val, list):
            for subval in val:
                retval.append({"key":"%s" % key, "value":"%s" % subval})
        else:
            retval.append({"key":"%s" % key, "value":"%s" % val})
    return retval

def search_in_list_of_dict(list, key, value):
    retval = [element for element in list if element[key] == value]
    if len(retval) == 0:
        return None
    else:
        return retval[0]

def post(url, data):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.post(API_ROOT + url, data=json.dumps(data), headers=headers)
    return r

def put(url, data):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.put(API_ROOT + url, data=json.dumps(data), headers=headers)
    return r

def get(url):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.get(API_ROOT + url, headers=headers)
    return r  
                  
def delete(url):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    r = requests.delete(API_ROOT + url, headers=headers)
    return r  

def main(args):
    # Some constants
    LXC_TEMPLATE = "ubuntu"
    
    # Let's pick a random name, avoiding clashes
    CONTAINER_NAME = str(uuid.uuid1())
    CLONE_NAME = str(uuid.uuid1())
    
    ## Instantiate the container instance
    print("Creating instance for '%s'" % CONTAINER_NAME)
    
    ## Create a rootfs
    r = post("/containers", {
      "cgroups": [],
      "name": CONTAINER_NAME,
      "conf": [],
      "template": {
        "args": [],
        "name": LXC_TEMPLATE }})
    
    result = r.json()
    
    assert(result['init_pid'] == -1)
    assert(result['name'] == CONTAINER_NAME)
    #assert(not container.running)
    assert(result['state'] == "STOPPED")
    conf = keyval_list_to_dict(result['conf'])
    
    assert(result['name'] == CONTAINER_NAME
           == conf["lxc.utsname"])
    
    # A few basic checks of the current state
    r = get("/containers")
    list_containers = r.json()
    
    container =  search_in_list_of_dict(list_containers['containers'], "name", CONTAINER_NAME)
    assert(CONTAINER_NAME == container['name'])
    
    """
    ## Test the config modification
    #@TODO implement this
    print("Testing the configuration")
    container = get("/containers/%s" % CONTAINER_NAME).json()
    conf = keyval_list_to_dict(container['conf'])
    capdrop = conf["lxc.cap.drop"]
    
    #container.clear_config_item("lxc.cap.drop")
    conf["lxc.cap.drop"] = capdrop[:-1]
    container['conf'] = dict_to_keyval_list(conf)
    r = put("/containers/%s" % CONTAINER_NAME, container )
    container = r.json()
    conf = keyval_list_to_dict(container['conf'])
    assert(conf["lxc.cap.drop"] == capdrop[:-1])
    assert(isinstance(conf["lxc.cap.drop"],list))
    # check conf return
    conf["lxc.cap.drop"] = container['conf']["lxc.cap.drop"].append(capdrop[-1])
    container['conf'] = dict_to_keyval_list(conf)
    r = put("/containers/%s" % CONTAINER_NAME, container )
    container = r.json()
    conf = keyval_list_to_dict(container['conf'])
    assert(conf["lxc.cap.drop"] == capdrop)
    assert(isinstance(conf["lxc.cap.drop"],list))
    # check conf return
    """
    
    
    
    """
    #implement this
    ## Test the networking
    print("Testing the networking")
    
    # A few basic checks of the current state
    container = get("/containers/%s" % CONTAINER_NAME).json()
    
    assert("name" in container.get_keys("lxc.network.0"))
    assert(len(container.network) == 1)
    assert(container.network[0].hwaddr.startswith("00:16:3e"))
    """
    ## Starting the container
    print("Starting the container")
    r = post("/containers/%s/actions/start" % (CONTAINER_NAME), {})
    assert(r.status_code == 200)
    #@TODO implement this
    #container.wait("RUNNING", 3)
    
    time.sleep(5)
    r = get("/containers/%s" % (CONTAINER_NAME))
    assert(r.status_code == 200)
    container = r.json()
    assert(container['state'] == "RUNNING")
    assert(container['init_pid'] > 1)
    #@TODO this too
    #assert(container.running)
    
    """
    ## Checking IP address
    print("Getting the IP addresses")
    
    count = 0
    ips = []
    while not ips or count == 10:
        ips = container.get_ips()
        time.sleep(1)
        count += 1
    container.attach("NETWORK|UTSNAME", "/sbin/ifconfig", "eth0")
    
    # A few basic checks of the current state
    assert(len(ips) > 0)
    
    ## Testing cgroups a bit
    print("Testing cgroup API")
    max_mem = container.get_cgroup_item("memory.max_usage_in_bytes")
    current_limit = container.get_cgroup_item("memory.limit_in_bytes")
    assert(container.set_cgroup_item("memory.limit_in_bytes", max_mem))
    assert(container.get_cgroup_item("memory.limit_in_bytes") != current_limit)
    """
    ## Freezing the container
    print("Freezing the container")
    r = post("/containers/%s/actions/freeze" % (CONTAINER_NAME), {})
    assert(r.status_code == 200)
    r = get("/containers/%s" % (CONTAINER_NAME))
    assert(r.status_code == 200)
    container = r.json()
    assert(container['state'] == "FROZEN")
    assert(container['init_pid'] > 1)
    
    ## Unfreezing the container
    print("Unfreezing the container")
    r = post("/containers/%s/actions/unfreeze" % (CONTAINER_NAME), {})
    assert(r.status_code == 200)
    r = get("/containers/%s" % (CONTAINER_NAME))
    assert(r.status_code == 200)
    container = r.json()
    assert(container['state'] == "RUNNING")
    assert(container['init_pid'] > 1)
    
    """
    #@TODO implement this
    if len(sys.argv) > 1 and sys.argv[1] == "--with-console":
        ## Attaching to tty1
        print("Attaching to tty1")
        container.console(tty=1)
    """
    
    ## Shutting down the container
    print("Shutting down the container")
    r = post("/containers/%s/actions/shutdown" % (CONTAINER_NAME), {})
    assert(r.status_code == 200)
    
    r = post("/containers/%s/actions/stop" % (CONTAINER_NAME), {})
    assert(r.status_code == 200)
    
    r = get("/containers/%s" % (CONTAINER_NAME))
    assert(r.status_code == 200)
    container = r.json()
    assert(container['state'] == "STOPPED")
    assert(container['init_pid'] == -1)
    
    
    """ @TODO implement clonning 
    ## Cloning the container
    print("Cloning the container")
    
    clone = lxc.Container(CLONE_NAME)
    clone.clone(container)
    clone.start()
    clone.stop()
    clone.destroy()
    """
    ## Destroy the container
    print("Destroying the container")
    r = delete("/containers/%s" % (CONTAINER_NAME))
    assert(r.status_code == 200)
    
    r = get("/containers")
    list_containers = r.json()
    container =  search_in_list_of_dict(list_containers['containers'], "name", CONTAINER_NAME)
    assert(container is None)
    #@TODO implement this
    #container.wait("RUNNING", 3)
    
if  __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Lxc Restful test script.')
    parser.add_argument('--ip', 
                        nargs='?',
                        help='Ip address to connect to (default: 127.0.0.1)',
                        default="127.0.0.1")
    parser.add_argument('--port',
                        nargs='?',
                        help='tcp port to connect to (default: 8080)',
                        default="8080")
    args = parser.parse_args()
    API_ROOT = "http://%s:%s/v1" % (args.ip, args.port)   
    main(args)
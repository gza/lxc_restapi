#!/usr/bin/env python3

import subprocess
import shlex
import argparse

from bottle import route, run, request, abort, static_file

import lxc

# Conf
# available actions by state
ACTIONS_BY_STATE = {"STOPPED": ['start', 'destroy'],
      "STARTING": [],
      "RUNNING": ['shutdown', 'freeze'],
      "STOPPING": [],
      "ABORTING": [],
      "FREEZING": [],
      "FROZEN": ['unfreeze'],
      "THAWED": []}

LXC_MIN_VERSION = "0.9.0"

DEFAULT_TEMPLATE = "ubuntu"

def is_good_lxc_version(version):
    #Check LXC version
    retval = True
    current_version = lxc.version
    for i in range(0, 2):
        if int(current_version.split('.')[i]) > int(version.split('.')[i]):
            break
        if int(current_version.split('.')[i]) < int(version.split('.')[i]):
            retval = False
            break
    return retval


#api prefix
PREFIX = "/v1"

#Common
CONTAINERS = {}


@route(PREFIX + "/api-docs.json", method='GET')
def get_swagger():
    """ Get swagger Main json """
    url = request.urlparts
    retval = {'apiVersion': "0.1",
              'swaggerVersion': "1.1",
              'basePath': "%s://%s%s" % (url.scheme, url.netloc, PREFIX),
              'apis': [
                {
                  'path': "/api-docs.json/containers",
                  'description': "LXC containers management",
                }
              ]}
    return retval


def get_container_object(name):
    """ Container objects store """
    if not name in CONTAINERS:
        CONTAINERS[name] = lxc.Container(name)
    return CONTAINERS[name]


def set_container_conf(container, conf):
    """ Apply Configuration for a container

    """
    for key in conf:
        container.set_config_item(key, conf[key])
    container.save_config()


""" 
API Documentation init 
"""

DOC_API = {
           "apiVersion": "0.2",
           "apis": [],
           "models": {}
           }

""" 
Dictionary like model with to dict conv function
"""
DOC_MODEL_KEYVAL = {
            "id": "keyval",
            "properties":{
                "key": {
                    "type" : "string",
                    "required": True,
                    "description": "key of the hash"},
                "val": {
                    "type" : "string",
                    "required": True,
                    "description": "value of the hash"}
        }
}
DOC_API['models']["keyval"] = DOC_MODEL_KEYVAL

def keyval_list_to_dict(data):
    retval = {}
    for item in data:
        key = item['key']
        val = item['val']
        if key in retval:
            #key used twice, assuming it wants an array
            if isinstance(retval[key], str):
                oldval = retval[key]
                retval[key] = [oldval]
            retval[key].append(val)
        else:
            retval[key] = val
    return retval



""" 
Containers Collections
"""
DOC_API_CONTAINERS_COLLECTION = {
            "description": "Container collection",
            "operations": [],
            "path": "/containers",
            "summary":"Find pet by its unique ID",
            "notes": "",
            "errorResponses":[]}
      


DOC_MODEL_CONTAINER = {
            "id": "container",
            "properties":{
                "name":{
                    "type": "string",
                    "required": True,
                    "description": "Name of the container"},
                "conf": {
                    "type":"List",
                    "items":{ "$ref":"keyval" },
                    "required": False,
                    "description":"list of container's conf params [{key: lxc.tty, val: 2}, ...], NB if key used twice, this will produce an array"},
                "cgroups": {
                    "type":"List",
                    "items":{ "$ref":"keyval" },
                    "required": False,
                    "description":"list of container's cgroup params [{key: memory.limit_in_bytes, val: 536870912}, ...], NB if key used twice, this will produce an array"},
                "template": {
                    "type":"template",
                    "required": False,
                    "description":"Template to use, defaults to %s with no options" % DEFAULT_TEMPLATE}
            }
}

#@TODO: propose a list of available templates
DOC_MODEL_TEMPLATE = {
            "id":"template",
            "properties":{
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "Name of the template to use"},
                "args": {
                    "type":"List",
                    "items":{ "$ref":"keyval" },
                    "required": False,
                    "description":"list of template args : --release lucid => [{key: release, val: lucid}, ...]"
                }
            }
}

DOC_API['models']["template"] = DOC_MODEL_TEMPLATE   
DOC_API['models']["container"] = DOC_MODEL_CONTAINER
             

"""GET on container collection"""
DOC_API_CONTAINERS_COLLECTION['operations'].append({
            "httpMethod":"GET",
            "nickname":"getContainers",
            "responseClass":"void",
            "parameters":[],
            "summary":"Get the list of containers collection",
            "notes": "",
            "errorResponses":[]
                      })

@route(PREFIX + '/containers', method='GET')
def get_container_list():
    retval = {}
    retval['containers'] = []
    for name in lxc.list_containers():
        c = get_container_object(name)
        retval['containers'].append({
               "name": name,
               "state": c.state,
               "init_pid": c.init_pid})
    return retval



"""POST on container collection"""
DOC_API_CONTAINERS_COLLECTION['operations'].append({
            "httpMethod":"POST",
            "nickname":"newContainer",
            "responseClass":"void",
            "summary":"Create a container",
            "parameters":[{
                "allowMultiple": False,
                "dataType": "container",
                "description": "Created container object",
                "paramType": "body",
                "required": True
                }]
            })

@route(PREFIX + '/containers', method='POST')
def add_container():
    data = request.json
    if len(data) == 0:
        abort(400, 'No data received')
    
    name = data['name']
    container = get_container_object(name)
    
    #conf management
    conf= {}
    if 'conf' in data:
        conf = keyval_list_to_dict(data['conf'])
  
    #template management
    template_name = DEFAULT_TEMPLATE
    template_args = {}
    if 'template' in data:
        template_args = keyval_list_to_dict(data['template']['args'])
        template_name = data['template']['name']
    
    print("will create container with %s, %s" %( template_name, template_args))       
    if container.create(template_name, template_args):
        if len(conf) > 0:
            set_container_conf(container, conf)
        return get_container(data['name'])
    else:
        abort(500, 'container.create failed')

DOC_API["apis"].append(DOC_API_CONTAINERS_COLLECTION)

""" 
    Containers items
"""
DOC_API_CONTAINERS_ITEM = {
            "description": "Container item",
            "operations": [],
            "path": "/containers/{name}",
            "summary":"Container item manipulation",
            "notes": "",
            "errorResponses":[]}

"""GET on container details"""
DOC_API_CONTAINERS_ITEM['operations'].append({
            "httpMethod":"GET",
            "nickname":"getContainer",
            "responseClass":"void",
            "parameters":[{
                "name":"name",
                "allowMultiple": False,
                "dataType": "string",
                "description": "container name",
                "paramType": "path",
                "required": True
                }],
            "summary":"Get details about a container",
            "notes": "",
            "errorResponses":[]
                      })

@route(PREFIX + '/containers/:name', method='GET')
#get container details by name
def get_container(name):
    retval = {}
    container = get_container_object(name)
    retval['name'] = container.name
    retval['state'] = container.state
    retval['init_pid'] = container.init_pid
    retval['conf'] = []
    for key in container.get_keys():
        try:
            #print(repr(container.get_config_item(key)))
            value = container.get_config_item(key)
            if type(value) == list:
                datatype = "list"
            if type(value) == int:
                datatype = "int"
            if type(value) == str:
                datatype = "str"
            if type(value) == bool:
                datatype = "bool"
            retval['conf'].append({"key": key,
                                   "value": container.get_config_item(key),
                                   "typeOf": datatype})
            del datatype
            del value
        except KeyError:
            print("%s, get_keys give it but doesn\'t exists :-/" % key)
        except UnicodeDecodeError:
            print("%s, get_keys give it but doesn\'t exists :-/" % key)
    retval['ips'] = container.get_ips()
    
    retval['actions'] = ACTIONS_BY_STATE[retval['state']]
    return retval

"""DELETE on container """
DOC_API_CONTAINERS_ITEM['operations'].append({
            "httpMethod":"DELETE",
            "nickname":"delContainer",
            "responseClass":"void",
            "parameters":[{
                "name":"name",
                "allowMultiple": False,
                "dataType": "string",
                "description": "container name",
                "paramType": "path",
                "required": True
                }],
            "summary":"destroy a container",
            "notes": "",
            "errorResponses":[]
                      })

@route(PREFIX + '/containers/:name', method='DELETE')
#destroy a container
def delete_container(name):
    get_container_object(name).destroy()

"""PUT on container """
DOC_API_CONTAINERS_ITEM['operations'].append({
            "httpMethod":"PUT",
            "nickname":"putContainer",
            "responseClass":"void",
            "parameters":[{
                "allowMultiple": False,
                "dataType": "container",
                "description": "Created container object",
                "paramType": "body",
                "required": True
                }],
            "summary":"modify a container",
            "notes": "",
            "errorResponses":[]
                      })
@route(PREFIX + '/containers/:name', method='PUT')
def modify_container(name):
    data = request.json
    if len(data) == 0:
        abort(400, 'No data received')

    if 'conf' in data:
        set_container_conf(get_container_object(name), data['conf'])

DOC_API["apis"].append(DOC_API_CONTAINERS_ITEM)


@route(PREFIX + '/containers/:name/ips', method='GET')
#get container ips addresses
def get_container_ip(name):
    retval = {}
    retval['ips'] = get_container_object(name).get_ips(timeout=10)
    return retval

""" 
    Container's actions
"""
DOC_API_CONTAINER_ACTIONS = {
            "description": "Container actions",
            "operations": [],
            "path": "/containers/{name}/actions/{action}",
            "summary":"Container item manipulation",
            "notes": "",
            "errorResponses":[]}

"""PUT on container """
DOC_API_CONTAINER_ACTIONS['operations'].append({
            "httpMethod":"POST",
            "nickname":"putContainer",
            "responseClass":"void",
            "parameters":[{
                "name":"name",
                "allowMultiple": False,
                "dataType": "string",
                "description": "container name",
                "paramType": "path",
                "required": True
                },{
                "name":"action",
                "allowMultiple": False,
                "dataType": "string",
                "description": "container action to perform",
                "paramType": "path",
                "required": True,
                "allowableValues":{
                        "valueType":"LIST",
                        "values":[
                                  "start",
                                  "shutdown",
                                  "restart",
                                  "freeze",
                                  "unfreeze",
                                  "chrootcmd",
                                  "destroy",
                                  "attach"
                                  ]
                                   }
                },{
                "name":"cmd",
                "allowMultiple": False,
                "dataType": "string",
                "description": "for chrootcmd and attach, the command to execute",
                "paramType": "body",
                "required": False
                }
                ],
            "summary":"perform {action} on a container",
            "notes": "",
            "errorResponses":[]
                      })


@route(PREFIX + '/containers/:name/actions/start', method='POST')
#start it
def start_container(name):
    container = get_container_object(name)
    if not container.start():
        abort(500, 'container.start() failed')
    container.wait("RUNNING", 3)


@route(PREFIX + '/containers/:name/actions/shutdown', method='POST')
#shut it down
def shutdown_container(name):
    container = get_container_object(name)
    if not container.shutdown(timeout=10):
        abort(500, 'container.shutdown() failed')


@route(PREFIX + '/containers/:name/actions/stop', method='POST')
#shut it down
def stop_container(name):
    container = get_container_object(name)
    if not container.stop():
        abort(500, 'container.shutdown() failed')
    container.wait("STOPPED", 10)


@route(PREFIX + '/containers/:name/actions/restart', method='POST')
#restart it
def restart_container(name):
    shutdown_container(name)
    stop_container(name)
    start_container(name)


@route(PREFIX + '/containers/:name/actions/freeze', method='POST')
#freeze it
def freeze_container(name):
    container = get_container_object(name)
    if not container.freeze():
        abort(500, 'container.freeze() failed')
    container.wait("FROZEN", 10)


@route(PREFIX + '/containers/:name/actions/unfreeze', method='POST')
#unfreeze it
def unfreeze_container(name):
    container = get_container_object(name)
    if not container.unfreeze():
        abort(500, 'container.unfreeze() failed')
    container.wait("RUNNING", 10)


@route(PREFIX + '/containers/:name/actions/destroy', method='POST')
#unfreeze it
def destroy_container(name):
    container = get_container_object(name)
    if not container.destroy():
        abort(500, 'container.destroy() failed')

    
@route(PREFIX + '/containers/:name/actions/chrootcmd', method='POST')
def chrootcmd(name):
    """
    Exec a command in container "name" with chroot
    example:
        input : {'cmd':'ls /'}
        returns : {'output':'bin  boot  dev  etc  home ... usr  var'}
    """
    data = request.json
    if len(data) == 0:
        abort(400, 'No data received')

    container = get_container_object(name)
    rootfs = container.get_config_item('lxc.rootfs')

    cmd = ['chroot', rootfs]
    cmd.extend(shlex.split(data['cmd']))

    output = subprocess.check_output(cmd, shell=True)
    retval = {}
    retval['output'] = output
    return retval

    ##fork and chroot
    #r, w = os.pipe()
    #pid = os.fork()
    #if pid:
        #os.close(w)
        #r = os.fdopen(r)
        #print("chrootexec child forked")
        #txt = r.read()
        #os.waitpid(pid, 0)
    #else:
        #os.close(r)
        #w = os.fdopen(w, 'w')
        #print("chrooting into %s" % rootfs)
        #os.chroot("%s" % rootfs)
        #print("executing %s" % data['cmd'])
        #output = subprocess.check_output(data['cmd'], shell=True)
        #w.write("%s" % output)
        #w.close()
        #print("child: closing")
        #os._exit(0)
    #retval = {}
    #retval['output'] = txt
    #return retval


@route(PREFIX + '/containers/:name/actions/attach', method='POST')
#exec a command in it with attach
def chrootattach(name):
    data = request.json
    if len(data) == 0:
        abort(400, 'No data received')

    container = get_container_object(name)
    if not container.running:
        return False

    namespace = data['namespaces']
    cmd = data['cmd']

    attach = ["lxc-attach", "-n", name,
              "-P", container.get_config_path()]
    if namespace != "ALL":
        attach += ["-s", namespace]

    if cmd:
        attach += ["--"] + list(cmd)

    if subprocess.call(
            attach,
            universal_newlines=True) != 0:
        return False
    return True
#@route(PREFIX + '/containers/:name/actions/clone', method='POST')
#def clone_container(name):
#    load_container(name)
#    CONTAINERS[name].unfreeze

DOC_API["apis"].append(DOC_API_CONTAINER_ACTIONS)

@route(PREFIX + "/api-docs.json/containers", method='GET')
def doc_containers():
    return DOC_API

@route('/lib/<filename:re:.*\.js>', method='GET')
def javascripts(filename):
    return static_file(filename, root='swagger/lib')


@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='swagger/css')


@route('/images/<filename:re:.*\.(jpg|png|gif|ico)>', method='GET')
def images(filename):
    return static_file(filename, root='swagger/images')


@route('/swagger-ui.js', method='GET')
def swagger_ui():
    return static_file('swagger-ui.min.js', root='swagger')


@route('/info', method='GET')
def index():
    return static_file('swagger.html', root='.')

def main():
    if not is_good_lxc_version(LXC_MIN_VERSION):
        raise Exception('Please Use LXC > %s' % LXC_MIN_VERSION)
    parser = argparse.ArgumentParser(description='Lxc Restful Webservice.')
    parser.add_argument('--ip', 
                        nargs='?',
                        help='Ip address to listen on (default: 127.0.0.1)',
                        default="127.0.0.1")
    parser.add_argument('--port',
                        nargs='?',
                        help='tcp port to listen on (default: 8080)',
                        default="8080")
    
    args = parser.parse_args()
    run(host=args.ip, port=args.port, debug=True)

                    
if  __name__ == "__main__":
    main()
    

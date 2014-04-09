lxc_restapi
=======

Restful Api for lxc based on lxc's python api

State: Alpha
* basic operations works
* no security !!! please be careful

Needs:
* python3
* lxc 1.0
 
Quick start:

	./install_local.sh #will download vendor libraries
	sudo ./lxc_restapi.py #Yes as root, lxc is serious stuff :)

In another shell:

Test libcloud driver:

    PYTHONPATH="." drivers/libcloud/example.py

Run tests:

    tests/test.py

explore/test with swagger:

Use your browser: http://localhost:8080/info

Tips: 

localhost:8080 is default for minimal security

see scripts with "--help" to tune ip and port

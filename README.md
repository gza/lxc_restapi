lxc_restapi
=======

Restful Api for lxc based on lxc's python api

State: Alpha
* basic operations works
* no security !!! please be careful

Needs:
* python3
* lxc 0.9
 
Quick start:

	./install_local.sh #will download vendor libraries
	sudo ./lxc_restapi.py #Yes as root, lxc is serious stuff :)

In another shell:

Test libcloud driver:

    PYTHONPATH="." drivers/libcloud/example.py
    or
    PYTHONPATH="." drivers/libcloud/example.py http://myserver:8081

Run tests:

    tests/test.py

explore/test with swagger:

Use your browser: http://yourserver:8080/info

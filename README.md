lxc_api
=======

Restful Api for lxc

State: Alpha
* basic operations works
* no security !!!

Needs:
* python3
* lxc 0.9
 
Quick start:

	./install_local.sh #will download vendor libraries
	sudo ./lxc_api.py #Yes as root, lxc is serious stuff :)

In another shell:

Test libcloud driver:

    PYTHONPATH="." drivers/libcloud/example.py

Run tests:

    tests/test.py

explore/test with swagger:

Use your browser: http://yourserver:8080/info

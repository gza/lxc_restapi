#!/bin/bash

root=$(dirname $0)

#libcloud 0.13
libcloud_root="${root}/vendors/libcloud"
git clone https://github.com/apache/libcloud.git "${libcloud_root}"
(cd "${libcloud_root}" ; git checkout 0.13.x)
ln -nsf "${libcloud_root}/libcloud" ${root}/

#bootle
bottle_root="${root}/vendors/bottle"
git clone https://github.com/bottlepy/bottle.git "${bottle_root}"
(cd "${bottle_root}" ; git checkout release-0.11)
ln -nsf "${bottle_root}/bottle.py" ${root}/.

#swagger
swagger_root="${root}/vendors/swagger"
git clone https://github.com/wordnik/swagger-ui.git "${swagger_root}"
ln -nsf "${swagger_root}/dist" ${root}/swagger

#requests
requests_root="${root}/vendors/requests"
git clone https://github.com/kennethreitz/requests.git "${requests_root}"
(cd ${root}/tests; ln -nsf ../vendors/requests/requests .)

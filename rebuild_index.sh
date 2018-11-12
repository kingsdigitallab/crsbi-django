#!/bin/bash
echo "Needs to be run as root - sudo su root"
source /home/vagrant/venv/bin/activate
./manage.py build_solr_schema --configure-directory=/var/solr/data/dev/conf
/etc/init.d/solr restart
./manage.py rebuild_index --noinput

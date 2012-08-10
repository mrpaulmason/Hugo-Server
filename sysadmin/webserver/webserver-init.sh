#!/bin/sh

apt-get -qy update
apt-get -qy install memcached nginx python-tornado supervisor
touch /etc/webserver-init.touchdown

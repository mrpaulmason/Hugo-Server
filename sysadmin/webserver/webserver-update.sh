#!/bin/sh

cd /var/hugo
git pull

cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/supervisord.conf" /etc/supervisor/conf.d/
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/nginx/nginx.conf" /etc/nginx/

rm -rf /var/www
mkdir -p /var/www
cp -rf /var/hugo/src/api/* /var/www/


/etc/init.d/nginx restart
/etc/init.d/supervisor start
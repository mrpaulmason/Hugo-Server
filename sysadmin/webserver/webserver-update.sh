#!/bin/sh

cd /var/hugo
git reset --hard HEAD
git pull

cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/supervisord.conf" /etc/supervisor/conf.d/
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/nginx/nginx.conf" /etc/nginx/
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/syslog-ng/syslog-ng.conf" /etc/syslog-ng/

chmod +x `find /var/hugo|grep py`
chmod +x `find /var/hugo|grep sh`
rm -rf /var/www
mkdir -p /var/www
cp -rf /var/hugo/src/api/* /var/www/

/etc/init.d/nginx restart
/etc/init.d/supervisor stop
sleep 1
/etc/init.d/supervisor start

exit 0
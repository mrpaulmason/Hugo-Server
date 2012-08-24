#!/bin/sh


echo "Configuring environment" >> /etc/webserver-init.touchdown

echo "HUGO_ENV=!HUGO_ENV!" >> /etc/environment
echo "HUGO_SERVER=!HUGO_SERVER!" >> /etc/environment

export "HUGO_ENV=!HUGO_ENV!"
export "HUGO_SERVER=!HUGO_SERVER!"

echo "Installing basic packages" >> /etc/webserver-init.touchdown

apt-get -qy update
apt-get -qy install git
apt-get -qy install syslog-ng
apt-get -qy install memcached nginx python-tornado supervisor
apt-get -qy install python-setuptools
apt-get -qy install python-geohash
easy_install facebook-sdk
easy_install simplejson

curl http://python-distribute.org/distribute_setup.py | python
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
pip install cloud

pip install --upgrade boto

echo "Copying key" >> /etc/webserver-init.touchdown

cat <<EOF > /root/hugo.pem
-----BEGIN RSA PRIVATE KEY-----
MIIEpgIBAAKCAQEAvD4jBsNc6zTZYh0OGLYh0X6uDS4fONZegVumBTYpdTKibcU8DLf0dQKuMbCF
FlOsD3kw45GOrmRXpRwaCbst5QddOnEdBF6f+odSrcCfakG59SJAEsSmakJ1rD5uVKan1JvFYDsX
U98VOb1FlD8YGOKNVWGbWIuf17NbdfSTMzvUDWdK13X7mfgII21S2K9IpMMAKufY5zWLsloGDVCn
RdUb+Sy6jmPpinC9ibcjXh7iwLHmzdN2PSIN28mlCHgyiSuG8poh2RUgpO4/13Xrhpwg2zKkZ6ro
B8r0yOUesxssDiOZkUF6D0eBRutg/x3LCg+1YYtolW+hFuEQUPBHvwIDAQABAoIBAQC1Z1vxxIri
z0c92aof/kSQ0neAlBXafBsOpfdTxmIlYupMxmmcCBo4OKENmYJnhbKmJrAKXdcWD/S2VGJzRkJw
F6ysCR1hfJ7Gm2n9r0bw6u39YUhFzeRhOjKUDoXcZc4OgR6wIcHVPYIC5ncK6dKbCJgS08EUj1k2
UM2u2kaQc0xCE4q/Q85ZwS+AeG2L6GmZlSUkt3uR9OsaoZLnNaATY7RtfAze85wV36qIM4uYF8z9
3CgGCD36o2nCTfM48460xPlZKoXditMWQDDbqaX1pqGjCzkdS34QuYsJq7yrC0iPAHcAJYm5XdSw
PxkKsIS7MxR7NAvv2wo1lqDIQ7YhAoGBAN4ACCHjV1sBbWTk0mahQNAcSn+PX+cuuZtb/klZbEtc
IY6BFnBA2dPPCsfGu3h9VpmPQxkdk7+D7JHgBySFurroMCLlNXbI+2WO/COpFWLQiSPPGhrr/bPZ
Dhyvpq3PUUPyf7S60LJr/Aa3nwkkJ6xyIB8S6323c0dDErSljL1DAoGBANkSk8EXuyYkjL2JYjLX
sntQU8yotdgpbXjHSOxBMX2279HzkdBUkwGjGEMBPFhiNBp5bwn+uQJhtqh/51FAeqrxumWyjDe3
rwqT5cqLkF/a8ScyRqHd2Uqz4xwWGnggSFwf8u2bWu6nG10wKAkEOCDZLlolBJOKNozVYBxXwYXV
AoGBAJvCbfJI7hueDsEBg1YawbzCfMqvL9ymffexPeL86OyfAbRYggPUnIDt/WRZ3WMWndI0ICHZ
DLcMuslG4/wOEAvfqRZyt2ZWcXy6K9Jhae3g3rfPMUO+XEz5d9tMqqe8lAoWdN+7S35EIZoc72qc
gXGOyVbEEZItSqavOsqgdPS9AoGBALxMoyMzBMM3nWalECvudAMIUUkNaIDUnwPQS2+1tcrJsAs9
8FT5qHQZGGi3X7ODrJLyl+Hhtndcb+iG2w/ekQpMmlaxpXSHwC260fD7VAfykpJfyGmNWnq0xOOO
QPPHfT188WwwAZdYGiKiLXh00oOcIdtMlUWu9VcBmVe8wEDpAoGBAN2KY1Aa43cLb/Z0YkuUYFX/
7GDVGoWn7X29ns2jzP6CnsMwVeaXy5j1K0NPcUjhDJIupUXKBIulc+HLr72Uc4ERxfbX+yFi3c76
gR13sD94SpsTapCt17A7XnovYCNJ0C5RChiNXb+Vu3JORu2DCR1CjAbUeAzAPyoP/pz7Mxze
-----END RSA PRIVATE KEY-----
EOF
chmod 400 /root/hugo.pem

mkdir -p /root/.ssh
cat <<EOF > /root/.ssh/config
Host github.com
  IdentityFile /root/hugo.pem
  StrictHostKeyChecking no
EOF


echo "Downloading code" >> /etc/webserver-init.touchdown
git clone git@github.com:pmm25/Hugo-Server.git /var/hugo

echo "Installing configuration files" >> /etc/webserver-init.touchdown
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/supervisord.conf" /etc/supervisor/conf.d/
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/nginx/nginx.conf" /etc/nginx/
cp "/var/hugo/sysadmin/webserver/${HUGO_ENV}/syslog-ng/syslog-ng.conf" /etc/syslog-ng/

/etc/init.d/supervisor stop

echo "PIDFILE=/var/log/tornado/supervisord.pid" >> /etc/default/supervisor
echo "LOGDIR=/var/log/tornado/supervisord.log" >> /etc/default/supervisor

chmod +x `find /var/hugo|grep py`
chmod +x `find /var/hugo|grep sh`
mkdir -p /var/log/tornado
mkdir -p /var/www
cp -rf /var/hugo/src/api/* /var/www/

chown -R www-data /var/log/tornado

/etc/init.d/nginx restart
/etc/init.d/supervisor start

echo "Setting up logging" >> /etc/webserver-init.touchdown
curl -X POST -u rwaliany:g00gle http://hugo.loggly.com/api/inputs/24412/adddevice
sudo service syslog-ng restart

echo "FINISHED" >> /etc/webserver-init.touchdown
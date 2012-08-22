#!/bin/bash

git commit -a -m "$@"
git push
./sysadmin/hugo-admin.py update

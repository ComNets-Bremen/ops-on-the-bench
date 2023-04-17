#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gets the token associated with a Seafile account. This is
hardcoded in the following files.

- seafile-list-repo-ids.py
- seafileops.py file.

Created on Tue May 31 12:59:01 2022

@author: Asanga Udugama (adu@comnets.uni-bremen.de)
"""
import getpass
import subprocess
import json

WEBADDRESS = 'https://seafile.zfn.uni-bremen.de/api2/auth-token/'

# get user
userid = input('Enter USer ID')

# get password
passwd = getpass.getpass('Enter Password')

# build cred string
credstr = 'username=' + userid.strip() + '&' + 'password=' + passwd

# run command to request token
proc = subprocess.Popen(['curl', '-d', credstr, WEBADDRESS],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
stdout, stderr = proc.communicate()

# process return data
data = json.loads(stdout)

# show return
if 'token' in data:
    print('Token:', data['token'])
    print('Use this token in the following')
    print(' - in seafile-list-repo-ids.py')
    print(' - in \'Storage backends\' configuration')
else:
    print(data)


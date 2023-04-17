#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List Seafile libraries (Repositories) to find the Repo ID 
to use in 'Storage backends' configuration.

Created on Tue May 31 12:59:01 2022

@author: Asanga Udugama (adu@comnets.uni-bremen.de)
"""
import subprocess
import json
import getpass

# get user
userid = input('User ID (e.g., dumbo@uni-bremen.de): ')

# get password
passwd = getpass.getpass('Password: ')

# build cred string
credstr = 'username=' + userid.strip() + '&' + 'password=' + passwd

# run command to request token
authlink = 'https://seafile.zfn.uni-bremen.de/api2/auth-token/'
proc = subprocess.Popen(['curl', '-d', credstr, authlink],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
stdout, stderr = proc.communicate()

# process return data
data = json.loads(stdout)

# show return
if 'token' in data:
    print('Token:', data['token'])
else:
    print(data)
    exit()

authstr = 'Authorization: Token ' + data['token']
listrepolink = 'https://seafile.zfn.uni-bremen.de/api2/repos/'
proc = subprocess.Popen(['curl', '-H', authstr, '-H',
                          'Accept: application/json; indent=4', 
                           listrepolink],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
stdout, stderr = proc.communicate()
retdata = json.loads(stdout)
for item in retdata:
    if 'type' in item and 'repo' in item['type']:
        print('name:', item['name'] if 'name' in item else '')
        print('  Repo Type: ', item['type'])
        print('  Repo ID:   ', item['id']  if 'id' in item else '')
        print('  Owner ID:  ', item['owner'] if 'owner' in item else '')
        print('  Owner Name:', item['owner_name'] if 'owner_name' in item else '')
        print('')

print('Use the \'Repo ID\' of the selected repository when configuring \'Storage backends\'\n')



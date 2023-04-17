#!/usr/bin/env python3
#
# The code to upload the results to a Seafile based cloud
# service and create a share to be sent to the user. 
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 01-Jun-2022
#
import os
import uuid
import datetime
import json
import shutil
import subprocess

TOKEN = 'deadbeefdeadbeefdeadbeef'
TESTFILE = './testfile.zip'
REPOID = 'deadbeef-deadbeef-deadbeef'

def upload_file(filename, token, repoid, prefix, lifetime=datetime.timedelta(days=7)):

    # get file details
    filesize = os.path.getsize(filename)


    # make a copy of file with a unique name
    newfilename = str(prefix) + "_" + str(uuid.uuid4()) + "_" + os.path.basename(filename)
    head, tail = os.path.split(filename)
    newfilepath = head + '/' + newfilename
    shutil.copyfile(filename, newfilepath)

    
    # show info
    print('Local file name:', filename)
    print('Remote file name:', newfilename)
    print('File size:', filesize, 'bytes')


    # get upload link
    authstr = 'Authorization: Token ' + token
    getuploadlink = 'https://seafile.zfn.uni-bremen.de/api2/repos/' \
                   + repoid + '/upload-link/'
    proc = subprocess.Popen(['curl', '-H', authstr, getuploadlink],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
    stdout, stderr = proc.communicate()
    uploadlink = stdout.strip('\"')


    # upload file
    uploadfilestr = 'file=@' + newfilepath
    parentdirstr = 'parent_dir=/'
    replacestr = 'replace=1'
    proc = subprocess.Popen(['curl', '-H', authstr, '-F', uploadfilestr, 
                         '-F', parentdirstr, '-F', replacestr, uploadlink],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
    stdout, stderr = proc.communicate()
    retval = stdout


    # create download link
    basefilename = '/' + os.path.basename(newfilepath)
    details = '{\"repo_id\": \"' + repoid + '\", \"path\": \"' \
               + basefilename + \
               '\", \"permissions\": {\"can_edit\": false, \"can_download\": true}}'
    proc = subprocess.Popen(['curl', '-d', details, '-H', authstr, 
                         '-H', 'Content-type: application/json', 
                         '-H', 'Accept: application/json; indent=4',
                         'https://seafile.zfn.uni-bremen.de/api/v2.1/share-links/'],
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          universal_newlines=True)
    stdout, stderr = proc.communicate()
    retdata = json.loads(stdout)
    downloadlink = retdata['link']


    # remove unique file created
    os.remove(newfilepath)


    # return the link
    return downloadlink


if __name__ == "__main__":
    shared_link = upload_file(TESTFILE, TOKEN, REPOID, 'ootb')
    print(shared_link)


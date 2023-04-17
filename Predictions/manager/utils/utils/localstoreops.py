#!/usr/bin/env python3
#
# The code to upload the results to a local location and 
# create a share to be sent to the user. 
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 08-May-2022
#
import os
import uuid
import socket
import datetime

# TOKEN = '10.10.160.10:8976'
TOKEN = '192.168.142.128:8976'
BUFFER_SIZE = 64000
TESTFILE = 'testfile.zip'

def upload_file(filename, token, prefix, livetime=datetime.timedelta(days=7)):

    # Generate filename
    path = str(prefix) + "_" + str(uuid.uuid4()) + "_" + os.path.basename(filename)

    # get file details
    filesize = os.path.getsize(filename)

    # get IP address and port from token
    uploadip, uploadport = token.split(':')
    uploadip = uploadip.strip()
    uploadport = int(uploadport.strip())

    # show info
    print('Local file name:', filename)
    print('Remote file name:', path)
    print('File size:', filesize, 'bytes')
    print('Remote IP address:', uploadip)
    print('Remote port:', uploadport)

    # setup socket
    csocket = socket.socket()
    csocket.connect((uploadip, uploadport))
 
    # send file details first
    csocket.send(f'{path}:{filesize}'.encode())

    # get link to file
    received = csocket.recv(BUFFER_SIZE).decode()

    # send file 
    with open(filename, 'rb') as fp:
        while True:

            # read the bytes from the file
            buffer = fp.read(BUFFER_SIZE)

            # when no more bytes, exit sending
            if not buffer:
                break

            # send read bytes
            csocket.sendall(buffer)

            print('*', end='')

    print('')

    # close socket
    csocket.close()

    # return the link
    return received

if __name__ == "__main__":
    shared_link = upload_file(TESTFILE, TOKEN, 'ootb')
    print(shared_link)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Sets up a simple cloud service where clients can connect and
upload files and then get a link to share with anyone to download
the file.

Created on Sun May  8 13:20:15 2022

@author: Asanga Udugama (adu@comnets.uni-bremen.de)
"""

import argparse
import socket
import os
import threading
import http.server
import socketserver

# constants
DEFAULT_FOLDER = './cloud-store/'
DEFAULT_WEBPORT = 8977
DEFAULT_UPLOADPORT = 8976
BUFFER_SIZE = 64000
HEADER_SEPARATOR = ':'


"""
Main function of the program that initiates all activities.
"""
def main(folder, localip, webport, uploadport):

    # get local IP address
    # localip = socket.gethostbyname(socket.gethostname())
    
    # setup cloud storage folder
    abspathfolder = os.path.abspath(folder)
    if not os.path.exists(abspathfolder):
        os.makedirs(abspathfolder)
        
    # show info
    print('Storage folder:', abspathfolder)
    print('Local IP address:', localip)
    print('Web serving port:', webport)
    print('File upload port:', uploadport)

    # start web server thread
    t1 = threading.Thread(target=webserver, \
                          args=(abspathfolder, webport, localip,))
    t1.start()
    print('Webserver THread started')
    # start upload server
    t2 = threading.Thread(target=uploadserver, \
                          args=(abspathfolder, uploadport, localip, webport,))
    t2.start()
    print('Uploadserver THread started')
    # wait for thread to finish
    t1.join()
    t2.join()

"""
Web serving thread, serving files to download.
"""
def webserver(abspathfolder, webport, localip):
    # change directory to where files are located
    os.chdir(abspathfolder)
    print("web server serving filees")
    # start web server to serve files
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer
    httpd = socketserver.TCPServer((localip, webport), handler)
    httpd.allow_reuse_address = True
    httpd.serve_forever()


"""
File upload thread, expecting file contents to store and then return
a link to the file.
"""
def uploadserver(abspathfolder, uploadport, localip, webport):
    # change directory to where files are located
    os.chdir(abspathfolder)

    # setup server socket to receive
    s = socket.socket()

    # set socket options
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # bind and set listen count
    s.bind((localip, uploadport))
    s.listen(5)
    print("upload server expecting filees")
    # wait for connections
    while True:

        # accept connections
        csocket, address = s.accept()
        print("upload server receiving filees")
        # get file name and file size
        received = csocket.recv(BUFFER_SIZE).decode()
        print(received)
        filename, filesize = received.split(HEADER_SEPARATOR)
        filename = filename.strip()
        filesize = int(filesize.strip())

        # show information
        print('Receiving:', filename, 'with size:', filesize, 'bytes')

        # create and send link to file
        weblink = 'http://' + localip + ':' + str(webport) + '/' + filename
        csocket.send(f'{weblink}'.encode())

        # loop until all contents of file is received
        with open(filename, 'wb') as fp:
            while True:

                #  receive bytes
                received = csocket.recv(BUFFER_SIZE)

                # if no more bytes, exit connection
                if not received:    
                    break

                # write the bytes
                fp.write(received)
        
        
        # close socket and loop back to receive next connection
        csocket.close()
        
        # show information
        print('File received')
        print('Sent link:', weblink)


if __name__ == "__main__":
    
    # process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-li', '--localip', type=str, \
            help='Local IP address (for upload server and web server)')
    parser.add_argument('-wp', '--webport', type=int, \
            default=DEFAULT_WEBPORT, help='Web server port')
    parser.add_argument('-up', '--uploadport', type=int, \
            default=DEFAULT_UPLOADPORT, help='Upload server port')
    parser.add_argument('-f', '--folder', type=str, \
            default=DEFAULT_FOLDER, help = 'Storage folder location')
    args = parser.parse_args()
        
    # start the main function
    main(args.folder, args.localip, args.webport, args.uploadport)


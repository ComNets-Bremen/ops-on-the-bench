#!/usr/bin/env python3
#
# The code to upload the results to a DropBox account and 
# create a share to be sent to the user. 
#
# Author: Jens Dede (jd@comnets.uni-bremen.de)
# Date: 06-May-2020
#
# 10-May-2022, Jens Dede, jd@comnets.uni-bremen.de: Add support for oauth2

"""
How to get the access token?

https://stackoverflow.com/questions/70641660/how-do-you-get-and-use-a-refresh-token-for-the-dropbox-api-python-3-x
https://www.dropbox.com/developers/documentation/http/documentation#oauth2-token

Set Permission sharing.write etc. in settings before. CHANGE IN SETTINGS WILL NOT BE USED FOR EXISTING TOKENS!

Required keys:
App key: hq6xx80vsrnupe5
App secret: qier02hpqvszocb

# Get Auth code via Webbrowser and login to account:
https://www.dropbox.com/oauth2/authorize?client_id=<APP_KEY>&token_access_type=offline&response_type=code

Example: https://www.dropbox.com/oauth2/authorize?client_id=hq6xx80vsrnupe5&token_access_type=offline&response_type=code
Result:

S40VTTCeGpoAAAAAAACAr0CMqq3j8-q50rL-T3DXNsY

Get refresh token:
curl -u <app_key>:<app_secret> -d "code=<Auth_Code>&grant_type=authorization_code" https://api.dropboxapi.com/oauth2/token

Example:
curl -u hq6xx80vsrnupe5:qier02hpqvszocb -d "code=S40VTTCeGpoAAAAAAACAr0CMqq3j8-q50rL-T3DXNsY&grant_type=authorization_code" https://api.dropboxapi.com/oauth2/token

Result:
{"access_token": "sl.BGO83u99fHPEOELoahUqvS_68RmnzxbjFsQUbDVuX6jFH-M6uZtZcENaaY7-4QurvnxgG27zwRXG8267FUXy3BCqghbzAkQ1A_DdMVSdSw_eXl7DPyxJji7qGle-LBBWnYMLGuLc", "token_type": "bearer", "expires_in": 14400, "refresh_token": "kh-kF7Rl3KEAAAAAAAAAASiTz_4MBUGbliNAGh2_RcAcdSlSkyuQIzGCJiZ9-RBM", "scope": "account_info.read files.content.read files.content.write files.metadata.read files.metadata.write sharing.read sharing.write", "uid": "14850675", "account_id": "dbid:AAC_v2zmdaqirPCxrqokecIXN6oK-pKVFZQ"}jd@tokio:~/src/comnets-github/ops-on-the-bench/manager/utils$ 

-> Refresh token

"""


import dropbox

import os
import uuid

import datetime

TESTFILE = ""
REFRESH_TOKEN = ""
APP_KEY = ""
APP_SECRET = ""


def upload_file(filename,
        token,
        prefix,
        lifetime=datetime.timedelta(days=7),
        dropbox_path=None,
        chunksize=100*1000*1000):

    # Generate dropbox filename
    path = None
    if dropbox_path:
        path = dropbox_path
    else:
        path = "/" + str(prefix) + "_" + str(uuid.uuid4()) + "_" + os.path.basename(filename)

    dbx = dropbox.Dropbox(token)


    # Remove old shared files. Do not remove unshared files.
    # Take the server time as a reference
    link_cursor = None # Cursor needed while looping over shared files
    while True:
        link_results = dbx.sharing_list_shared_links(cursor=link_cursor)
        link_cursor = link_results.cursor

        for link in link_results.links:
            if datetime.datetime.utcnow() - link.server_modified > lifetime:
                print("Remove expired file", link.path_lower)
                dbx.files_delete(link.path_lower)
            else:
                print("Keeping file", link.path_lower)

        if not link_results.has_more:
            break


    # Check the available space on the dropbox account
    space_object = dbx.users_get_space_usage()
    space_allocated = None
    if space_object.allocation.is_individual():
        space_allocated = space_object.allocation.get_individual().allocated
    elif space_object.allocation.is_team():
        space_allocated = space_object.allocation.get_team().allocated
    else:
        raise ValueError("Neither team nor individual space limits.")

    space_used = space_object.used

    print("Allocated", space_allocated, "bytes")
    print("Used", space_used, "bytes")
    print("Free", space_allocated - space_used, "bytes")


    # Perform upload
    upload_size = os.path.getsize(filename)

    if upload_size < space_allocated - space_used:
        # Enough space
        upload_meta = None
        with open(filename, "rb") as f:
            if upload_size < chunksize:
                # Small file size: Upload as one file (max 150 MB)
                upload_meta = dbx.files_upload(f.read(), path)
            else:
                # larger file: Upload as chunks
                session = dbx.files_upload_session_start(f.read(chunksize))
                commit = dropbox.files.CommitInfo(path=path)

                cursor = dropbox.files.UploadSessionCursor(
                        session_id = session.session_id,
                        offset= f.tell()
                        )


                while f.tell() < upload_size:
                    if (upload_size - f.tell()) <= chunksize:
                        # finish upload, last chunk
                        upload_meta = dbx.files_upload_session_finish(
                            f.read(chunksize),
                            cursor,
                            commit
                            )
                    else:
                        dbx.files_upload_session_append(
                            f.read(chunksize),
                            cursor.session_id,
                            cursor.offset,
                            )
                        cursor.offset = f.tell()

                    print("Uploaded", f.tell(), "of", upload_size, " bytes (", f.tell()/upload_size*100.0, "%)")
            print("Upload done")

            # Create shared link. Expiration date can only be set in paid
            # account.

            shared_metadata = dbx.sharing_create_shared_link(
                    path
                    )

            return shared_metadata.url

    else:
        print("Out of space")
        return None

def upload_file_oauth2(filename,
        app_key,
        app_secret,
        oauth2_refresh_token,
        prefix="automatic_upload",
        lifetime=datetime.timedelta(days=7),
        dropbox_path="",
        dropbox_dir="/api-upload",
        chunksize=100*1000*1000):

    # Generate dropbox filename
    path = None
    if dropbox_path:
        path = dropbox_path
    else:
        path = "/" + str(prefix) + "_" + str(uuid.uuid4()) + "_" + os.path.basename(filename)

    path = dropbox_dir + path

    dbx = dropbox.Dropbox(app_key=app_key, app_secret=app_secret, oauth2_refresh_token=oauth2_refresh_token)


    # Remove old shared files. Do not remove unshared files.
    # Take the server time as a reference
    link_cursor = None # Cursor needed while looping over shared files
    while True:
        link_results = dbx.sharing_list_shared_links(cursor=link_cursor)
        link_cursor = link_results.cursor

        for link in link_results.links: # Only consider the api-uploaded files for further handling
            if link.path_lower.startswith(dropbox_dir):
                if hasattr(link, "server_modified"):
                    if datetime.datetime.utcnow() - link.server_modified > lifetime:
                        print("Removing old file", link.path_lower)
                        dbx.files_delete(link.path_lower)
                else:
                    print("Do not remove a directory")
        if not link_results.has_more:
            break


    # Check the available space on the dropbox account
    space_object = dbx.users_get_space_usage()
    space_allocated = None
    if space_object.allocation.is_individual():
        space_allocated = space_object.allocation.get_individual().allocated
    elif space_object.allocation.is_team():
        space_allocated = space_object.allocation.get_team().allocated
    else:
        raise ValueError("Neither team nor individual space limits.")

    space_used = space_object.used

    print("Allocated", space_allocated, "bytes")
    print("Used", space_used, "bytes")
    print("Free", space_allocated - space_used, "bytes")


    # Perform upload
    upload_size = os.path.getsize(filename)

    if upload_size < space_allocated - space_used:
        # Enough space
        upload_meta = None
        with open(filename, "rb") as f:
            if upload_size < chunksize:
                # Small file size: Upload as one file (max 150 MB)
                upload_meta = dbx.files_upload(f.read(), path)
            else:
                # larger file: Upload as chunks
                session = dbx.files_upload_session_start(f.read(chunksize))
                commit = dropbox.files.CommitInfo(path=path)

                cursor = dropbox.files.UploadSessionCursor(
                        session_id = session.session_id,
                        offset= f.tell()
                        )


                while f.tell() < upload_size:
                    if (upload_size - f.tell()) <= chunksize:
                        # finish upload, last chunk
                        upload_meta = dbx.files_upload_session_finish(
                            f.read(chunksize),
                            cursor,
                            commit
                            )
                    else:
                        dbx.files_upload_session_append(
                            f.read(chunksize),
                            cursor.session_id,
                            cursor.offset,
                            )
                        cursor.offset = f.tell()

                    print("Uploaded", f.tell(), "of", upload_size, " bytes (", f.tell()/upload_size*100.0, "%)")
            print("Upload done")

            # Create shared link. Expiration date can only be set in paid
            # account.

            shared_metadata = dbx.sharing_create_shared_link(
                    path
                    )

            return shared_metadata.url

    else:
        print("Out of space")
        return None


if __name__ == "__main__":
    shared_link = upload_file_oauth2(TESTFILE, APP_KEY, APP_SECRET, REFRESH_TOKEN, lifetime=datetime.timedelta(minutes=2))
    print(shared_link)


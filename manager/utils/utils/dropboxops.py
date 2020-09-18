#!/usr/bin/env python3
#
# The code to upload the results to a DropBox account and 
# create a share to be sent to the user. 
#
# Author: Jens Dede (jd@comnets.uni-bremen.de)
# Date: 06-May-2020
#
import dropbox

import os
import uuid

import datetime

TESTFILE = "hallen.png"

TOKEN = "S40VTTCeGpoAAAAAAAB_2brkwdVbb874TpDCsrdLAORtfWpRu4g6Zl2xYMoDR4uN"


def upload_file(filename,
        token,
        prefix,
        livetime=datetime.timedelta(days=7),
        dropbox_path=None,
        chunksize=100*1000*1000):

    # Generate dropbox filename
    path = None
    if dropbox_path:
        path = dropbox_path
    else:
        path = "/" + prefix + "_" + str(uuid.uuid4()) + "_" + os.path.basename(filename)

    dbx = dropbox.Dropbox(token)


    # Remove old shared files. Do not remove unshared files.
    # Take the server time as a reference
    link_cursor = None # Cursor needed while looping over shared files
    while True:
        link_results = dbx.sharing_list_shared_links(cursor=link_cursor)
        link_cursor = link_results.cursor

        for link in link_results.links:
            if datetime.datetime.utcnow() - link.server_modified > livetime:
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


if __name__ == "__main__":
    shared_link = upload_file(TESTFILE, TOKEN, datetime.timedelta(minutes=1))
    print(shared_link)



# Storage Backend

Once the results are collected, parsed and statistics are computed, a zip file is 
created. This zip file is then uploaded to a cloud service and then a link to the
zip file sent to the user.

Currently, there are 3 cloud storage possibilities.

- `Dropbox` - use of a Dropbox account to upload data
- `Seafile` - use of a Seafile account to upload data
- `Local` - use of a local storage in a file server

For every storage possibility above, a storage backend must be defined using the
`Storage backends` tag in the Django definitions. There are 7 tags that can be used 
to define parameters required by every storage backend. Each storage backend may 
require different parameter values. These are the tags and their display names.

- `storage_backend`: A name for the backend storage. Shown as `Backend name` 
- `storage_backend_id`: A unique identifier for the backend storage. Shown as `Backend identifier`
- `storage_backend_token`: A token values, if required, for the backend storage. Shown as `Backend token`
- `storage_backend_config`: Additional config values, if required, for the backend storage. Shown as `Backend config`
- `storage_backend_keep_days`: Number of days for the files to held in the backend storage. Shown as `Backend keep days`
- `storage_backend_desc`: A detailed description of the backend storage. Shown as `Backend description`
- `storage_backend_active`: Whether the backend storage is selectable when running simulations. Shown as `Backend active`

The important parameter values and other details for each storage possibility is 
is given below.

#### Dropbox

- `storage_backend_id`: An identifier for the upload service is `dropbox`

- `storage_backend`: A descriptive name of the backend like `Dropbox OAuth2`

- `storage_backend_config`: Credentials to connect to Dropbox account. Example,

```bash
{"app_key": "g234cl8j7654omi", "app_secret": "60v543ou17899z1", "refresh_token": "Zjyi908CUig321AAAAAAAWUs1vErUWCtpCVqT5629zE7098OKH5S26781uU7qax5"}
```

The functionality required to access and upload the zip file is implemented
in the `dropboxops.py` in the worker.


#### Seafile

- `storage_backend_id`: An identifier for the upload service is `seafile`

- `storage_backend`: A descriptive name of the backend like `Seafile`

- `storage_backend_config`: Credentials to connect to Dropbox account. Example,

```bash
{"token": "ef3d0a5l8j7654omi", "repoid": "60v4389103438eda4d789f543ou17899z1"}
```

The functionality required to access and upload the zip file is implemented
in the `seafileops.py` in the worker.

To get the token and the repository ID, the following command-line program are given

- `seafile-get-token.py`
- `seafile-list-repo-ids.py`

You must have a valid account at a Seafile based repostory and a repository (library) must
be created.

#### Local

- `storage_backend_id`: An identifier for the upload service is `local`

- `storage_backend`: A descriptive name of the backend like `Local storage`

- `storage_backend_token`: The connection parameters such as `10.10.160.10:8976`

The functionality required to access and upload the zip file is implemented
in the `localstoreops.py` in the worker.

The local storage handling server is implemented in the file `local-cloud.py`
source file. Run this script on a server (e.g., `10.10.160.10` port `8976`)
where there is enough disk space to store files.



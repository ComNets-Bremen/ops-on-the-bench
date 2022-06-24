
# Accessing Profile Configurations

The manager offers a simple key-value system for User profile (parameter) data. This Profile Parameters can be accessed in two ways:

- Accessing `/omnetppManager/get-profile-parameter/` as a logged in admin user returns a
  json object containing all User profile parameters. This is mainly meant for debugging.
- Accessing `/omnetppManager/get-profile-parameter/` with the HTTP-header`HTTP-X-HEADER-USER` set, will return the
  values as json for the given server only.

This can be tested using `curl`:

```bash
curl -H "HTTP-X-HEADER-USER: <USER_NAME>" <SERVER_IP_ADDRESS>/omnetppManager/get-profile-config/
```

For instance:
```bash
curl -H "HTTP-X-HEADER-USER: username" http://192.168.1.5:8000/omnetppManager/get-profile-parameter/
```

User instance is obtained from the in built User model in django, User profile is configured in the table 'UserProfile',  the key-value-pairs are in `User Profile Parameters`.

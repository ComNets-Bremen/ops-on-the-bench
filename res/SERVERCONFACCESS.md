# Accessing Server Configurations

The manager offers a simple key-value system for server (and simulation
independent) data. This Server configurations can be accessed in two ways:

- Accessing `/omnetppManager/get-server-config/` as a logged in user returns a
  json object containing all configured server configurations. This is mainly
  meant for debugging.
- Accessing `/omnetppManager/get-server-config/` with the two HTTP-headers
  `HTTP-X-HEADER-TOKEN` and `HTTP-X-HEADER-SERVER-ID` set will return the
  values as json for the given server only.

This can be tested using `curl`:

```bash
    curl -H "HTTP-X-HEADER-SERVER-ID: <SERVER_ID>" -H "HTTP-X-HEADER-TOKEN: <TOKEN>" <SERVER_ADDRESS>/omnetppManager/get-server-config/
```

Token and server ID are configured in the table `Server Config`, the
key-value-pairs in `Server Config Values`.


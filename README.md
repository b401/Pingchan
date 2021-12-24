# Pingchan

Pingcastle API server that runs on Linux.  
Generates and collects pingcastle scans/packages with a unique download url

## Dependencies

* mono
* dotnet (5.0)
* python >2.7


## HOWTO

Initial deployment is a little hacky 

0. Create a new service user (pingchan) 
1. Create new folder /opt/pingchan and clone all files into it and install systemd service.
2. Alter config.py to fit your needs.
3. Change the salt under ``/app/auth.py``
4. SSL/TLS offload on a reverse proxy and point it to 127.0.0.8000
5. Access ``https://[url]/register`` and create an initial user. 
6. Uncomment ``@login_required`` for the ``/register`` route
7. Restart the service
8. Login and create your first pingcastle package.


## Updating/Installation

Download official binary from https://github.com/vletoux/pingcastle and replace the PingCastle.exe + PingCaslte.exe.config in the src directory.

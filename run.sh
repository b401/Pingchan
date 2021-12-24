#!/bin/bash
cd /opt/pingchan
source .env/bin/activate
gunicorn --workers 5 run:app


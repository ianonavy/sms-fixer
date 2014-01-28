#!/usr/bin/env python
from flup.server.fcgi import WSGIServer
from server import app

if __name__ == '__main__':
    WSGIServer(app, bindAddress='/tmp/sms-fixer-fcgi.sock', umask=0002).run()

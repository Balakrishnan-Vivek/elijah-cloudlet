#!/usr/bin/env python
#
# Elijah: Cloudlet Infrastructure for Mobile Computing
# Copyright (C) 2011-2012 Carnegie Mellon University
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of version 2 of the GNU General Public License as published
# by the Free Software Foundation.  A copy of the GNU General Public License
# should have been distributed along with this program in the file
# LICENSE.GPL.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
import sys
import signal
from lib_synthesis import SynthesisServer
from lib_cloudlet import validate_congifuration


def sigint_handler(signum, frame):
    sys.stdout.write("Exit by user\n")
    if server != None:
        server.terminate()
    sys.exit(0)


if not validate_congifuration():
    sys.stderr.write("failed to validate configuration\n")
    sys.exit(1)

# handling keyboard interrupt
#signal.signal(signal.SIGINT, sigint_handler)

server = SynthesisServer(sys.argv[1:])
try:
    server.serve_forever()
except Exception as e:
    #sys.stderr.write(str(e))
    server.terminate()
    sys.exit(1)
except KeyboardInterrupt as e:
    sys.stdout.write("Exit by user\n")
    server.terminate()
    sys.exit(1)
else:
    server.terminate()
    sys.exit(0)



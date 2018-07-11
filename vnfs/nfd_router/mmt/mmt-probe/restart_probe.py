#!/usr/bin/env python
"""
Check to see if an process is running. If not, restart.
Run this in a cron job
"""
import os
import sys
import time
process_name= "./probe -c mmt.conf" # change this to the name of your process
process_name2= "python /doctor/vnf/nfd_restart.py"

import time
while True:
        tmp = os.popen("ps -Af").read()

        if process_name not in tmp[:]:
                print "The process is not running. Let's restart."
                newprocess="./probe -c mmt.conf &"
                os.system(newprocess)
        else:
                print "The process is running."
        if process_name2 not in tmp[:]:
                print "The process is not running. Let's restart."
                newprocess2="python /doctor/vnf/nfd_restart.py "+sys.argv[1]+" "+sys.argv[2]+" &"
                os.system(newprocess2)
        else:
                print "The process is running."
        time.sleep(5)

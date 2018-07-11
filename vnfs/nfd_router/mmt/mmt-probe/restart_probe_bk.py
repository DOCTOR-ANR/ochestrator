#!/usr/bin/env python
"""
Check to see if an process is running. If not, restart.
Run this in a cron job
"""
import os
import time
process_name= "./probe -c mmt.conf" # change this to the name of your process

import time
while True:
        tmp = os.popen("ps -Af").read()

        if process_name not in tmp[:]:
                print "The process is not running. Let's restart."
                newprocess="./probe -c mmt.conf &"
                os.system(newprocess)
        else:
                print "The process is running."
        time.sleep(5)

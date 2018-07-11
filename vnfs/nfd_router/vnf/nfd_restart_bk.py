#!/usr/bin/env python
"""
Check to see if an process is running. If not, restart.
Run this in a cron job
"""
import os
import time
import subprocess
import json

process_name= "sudo /usr/local/bin/nfd" # change this to the name of your process
filename="/root/nfd_conf"

import time
while True:
        tmp = os.popen("ps -Af").read()

        if process_name not in tmp[:]:
                print "The process is not running. Let's restart."
                newprocess="nfd-start &> /var/log/nfd_log"
                os.system(newprocess)
        else:
                print "The process is running."
        line = subprocess.check_output(['tail', '-1', filename])
        print(line)
        new_rules=json.loads(str(line))
        for key, face_list in new_rules.iteritems():
            prefix =key
            for face in face_list:
                interface = " tcp://"+face
                un_str_command = "nfdc unregister "+prefix+" tcp://"+face.split(':')[0]+":6363"
                subprocess.call(args=un_str_command, shell=True)
		str_command = "nfdc register "+prefix+interface
                ping_command = "ping -c 5 "+face.split(':')[0]
                subprocess.call(args=ping_command, shell=True)
                subprocess.call(args=str_command, shell=True)
                time.sleep(2)
            strategy_command = "nfdc strategy set {0} /localhost/nfd/strategy/round-robin/%FD%01".format(prefix)
            subprocess.call(args=strategy_command, shell=True)
        time.sleep(5)

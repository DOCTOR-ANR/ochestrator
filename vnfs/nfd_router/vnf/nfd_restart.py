import httplib
import sys
import os
import time
import subprocess
import json
from subprocess import check_output
import pprint

process_name= "sudo /usr/local/bin/nfd" # change this to the name of your process
filename="/root/nfd_conf"
notNotied=True
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
        new_config=json.loads(str(line))
	if (new_config.get("container_down","null")!="null" and notNotied):
                                        notNotied=True
                                        conn = httplib.HTTPConnection(sys.argv[1], sys.argv[2], timeout=5)
                                        header = {}
                                        # there is data to send
                                        if new_config is not None:
                                            # encode it in json format
                                            data = json.dumps(new_config)
                                            header['Content-Type'] = 'application/json'
                                            # send the request and get the response
                                            conn.request('POST','/router/notifications/finish_scale_out',data,header)
                                            res = conn.getresponse()
                                            print(str(res.status))
	new_rules={}
	if (len(new_config["to_add"])>0):
		new_rules=new_config["to_add"]
        out = check_output('nfd-status')
        faceid_list = [face for face in out.split('\n') if ("remote=tcp" in face)]
        face_olds={}
        ip_olds={}
        for face_old in faceid_list:
                values = [value for value in face_old.split(' ') if value != '']
		faceid=values[0].split('faceid=')[1]
		if values[1].split('=')[0] == 'remote':
                        remote_face = values[1].split('://')[1]
                        face_olds[remote_face]=faceid
                        ip_olds[remote_face.split(':')[0]]=faceid
        for f_o in face_olds:
		print(f_o)
        prefix_list = [face for face in out.split('\n') if ("nexthops" in face)]
	prefix_ids={}
	for p in prefix_list:
		values = [value for value in p.split(' nexthops=') if value != '']
		prefix=values[0].split(' ')[2]
		faces_v=values[1].split(',')
		prefix_ids[prefix]=[]
		for f in faces_v:
			prefix_ids[prefix].append(f.split('faceid=')[1].split(' ')[0])
	pprint.pprint(prefix_ids)
	for key, face_list in new_rules.iteritems():
            prefix =key
	    #print(prefix_ids[prefix])
            for face in face_list:
                if face.split(":")[0] in ip_olds.keys():
			print("face 1 :"+face)
			#for i in range(0):
			if (face in face_olds.keys()):
				print(face)
				if (face_olds[str(face)] not in prefix_ids[prefix]):
					print(face)
                                	interface = " tcp://"+face
                                	str_command = "nfdc register "+prefix+interface
                                	ping_command = "ping -c 5 "+face.split(':')[0]
                                	subprocess.call(args=ping_command, shell=True)
                                	subprocess.call(args=str_command, shell=True)
                	else:
				for face_o in face_olds.keys():
					print(face_o)
                           		if face_o.split(":")[0]==face.split(":")[0]:
                                        	un_str_command = "nfdc unregister "+prefix+" tcp://"+face_o
                                                subprocess.call(args=un_str_command, shell=True)
				interface = " tcp://"+face
                                str_command = "nfdc register "+prefix+interface
                                ping_command = "ping -c 5 "+face.split(':')[0]
                                subprocess.call(args=ping_command, shell=True)
                                subprocess.call(args=str_command, shell=True)
		else:
                        interface = " tcp://"+face
                        str_command = "nfdc register "+prefix+interface
                        ping_command = "ping -c 5 "+face.split(':')[0]
                        subprocess.call(args=ping_command, shell=True)
                        subprocess.call(args=str_command, shell=True)
                time.sleep(2)
        if (len(new_config["strategy"])>0):
		if (new_config["strategy"]=="round"):
			strategy_command = "nfdc strategy set {0} /localhost/nfd/strategy/round-robin/%FD%01".format(prefix)
                	subprocess.call(args=strategy_command, shell=True)	
	time.sleep(1)

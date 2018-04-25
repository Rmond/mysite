import os,json,uuid

def ansible_handle(ymlfile,jsondata):
    hosts = "/tmp/host-"+str(uuid.uuid1())
    with open(hosts, 'w') as f:
        for ip in jsondata["hosts"].split(":"):
            f.write(ip+"\n")
    shellstr = "ansible-playbook -i "+hosts+" "+ymlfile+" --extra-vars '"+json.dumps(jsondata)+"'"
    return os.popen(shellstr).read().splitlines()

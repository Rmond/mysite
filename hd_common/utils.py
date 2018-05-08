import os,json,uuid
from hd_mesos.models import HostInfo

def ansible_handle(ymlfile,jsondata):
    hosts = "/tmp/host-"+str(uuid.uuid1())
    with open(hosts, 'w') as f:
        for ip in jsondata["hosts"].split(":"):
            hostinfo = HostInfo.objects.get(ip=ip)
            f.write(ip+" hostname="+hostinfo.hostname+"\n")
    shellstr = "ansible-playbook -i "+hosts+" "+ymlfile+" --extra-vars '"+json.dumps(jsondata)+"'"
    return os.popen(shellstr).read().splitlines()

# -*- coding:utf-8 -*-

from __future__ import unicode_literals
from models import HostInfo
from hd_ansible.models import Hostip_Port,SidInfo

def install_soft_res(task):
    for hostip in task.hosts.split(":"):#循环读取执行主机
        for birefres in task.result.replace("[","").replace("]","").split("PLAY RECAP "+"*"*69+"\", ")[1].split(",")[:-1]:
            if hostip in birefres and "failed=0" in birefres:
                hostinfo = HostInfo.objects.get(ip=hostip)
                hostip_port = Hostip_Port(hostip = hostip)
                hostip_port.save()
                if not hostinfo.software:
                    hostinfo.software += task.softinfo
                else:
                    hostinfo.software += ","+task.softinfo
                    hostinfo.save()
            else:
                task.status = "FAILED"
        hostinfo2 = HostInfo.objects.get(ip=hostip)
        hostinfo2.idle = True
        hostinfo2.save()
        return task

def mysql_sid_initres(task,request):
    if task.result.count("failed=0") == 2:
        master_sid_info = SidInfo()
        master_sid_info.sidname = request.session["mextra_vars"]["sid"]
        master_sid_info.hostip=task.hosts.split(":")[0]
        master_sid_info.port=request.session["mextra_vars"]["port"]
        master_sid_info.socketpath="/mysql_data/"+master_sid_info.sidname+"/tmp/mysql.sock"
        master_sid_info.password=request.session["mextra_vars"]["password"]
        master_sid_info.replpassword=request.session["mextra_vars"]["replpassword"]
        master_sid_info.data_size=request.session["mextra_vars"]["data_size"]
        master_sid_info.save()
        slave_sid_info = SidInfo()
        slave_sid_info.sidname = request.session["sextra_vars"]["sid"]
        slave_sid_info.hostip=task.hosts.split(":")[1]
        slave_sid_info.port=request.session["sextra_vars"]["port"]
        slave_sid_info.socketpath="/mysql_data/"+slave_sid_info.sidname+"/tmp/mysql.sock"
        slave_sid_info.password=request.session["sextra_vars"]["password"]
        slave_sid_info.replpassword=request.session["sextra_vars"]["replpassword"]
        slave_sid_info.data_size=request.session["sextra_vars"]["data_size"]
        slave_sid_info.save()
        hostip_port=Hostip_Port.objects.get(hostip=task.hosts.split(":")[0])
        hostip_port.port=hostip_port.port+1
        hostip_port.save()
        hostip_port2=Hostip_Port.objects.get(hostip=task.hosts.split(":")[1])
        hostip_port2.port=hostip_port2.port+1
        hostip_port2.save()
    else:
        task.status = "FAILED"
    hostinfo = HostInfo.objects.get(ip=task.hosts.split(":")[0])
    hostinfo.idle = True
    hostinfo.save()
    hostinfo2 = HostInfo.objects.get(ip=task.hosts.split(":")[1])
    hostinfo2.idle = True
    hostinfo2.save()
    return task

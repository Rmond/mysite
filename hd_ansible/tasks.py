# Create your tasks here

from __future__ import absolute_import, unicode_literals
from celery import shared_task

from django.shortcuts import render
from django.http import HttpResponse
from hd_mesos.models import User_Task,HostInfo
from django_celery_results.models import TaskResult
from hd_ansible.models import Hostip_Port,SidInfo
from hd_mesos.tasks import update_info
from hd_mysql.models import Schedule_Res
from hd_common.utils import ansible_handle
import json,os,datetime

@shared_task
def install(extra_vars,softinfo):
    result = {"ansible_res":[],"status":"SUCCESS"}
    result["ansible_res"] = ansible_handle("/opt/ansible/roles/site.yml",extra_vars)
    for hostip in extra_vars["hosts"].split(":"):
        try:
            birefres = filter(lambda x:hostip in x,result["ansible_res"])[-1]
            if hostip in birefres and "failed=0" in birefres:
                hostinfo = HostInfo.objects.get(ip=hostip)
                if not hostinfo.software:
                    hostinfo.software += softinfo
                else:
                    hostinfo.software += ","+softinfo
                hostinfo.save()
                if "mysql" in softinfo:
                    hostip_port = Hostip_Port(hostip = hostip)
                    hostip_port.save()
            else:
                result["status"] = "FAILED"
        except Exception:
            result["status"] = "FAILED"
        finally:
            hostinfo2 = HostInfo.objects.get(ip=hostip)
            hostinfo2.idle = True
            hostinfo2.save()    
    return result

@shared_task
def update(extra_vars,softinfo):
    result = {"ansible_res":[],"status":"SUCCESS"}
    try:
        result["ansible_res"] = ansible_handle("/opt/ansible/roles/site.yml",extra_vars)
        for hostip in extra_vars["hosts"].split(":"):
            birefres = filter(lambda x:hostip in x,result["ansible_res"])[-1]
            if hostip in birefres and "failed=0" in birefres:
                hostinfo = HostInfo.objects.get(ip=hostip)
                software_list = hostinfo.software.split(",")
                for software in software_list:
                    if softinfo.split("-")[0] in software:
                        temp_id = software_list.index(software)
                        software_list[temp_id] = softinfo
                hostinfo.software = ",".join(software_list)
                hostinfo.save()
            else:
                result["status"] = "FAILED"
    except Exception:
        result["status"] = "FAILED"
    finally:
        hostinfo2 = HostInfo.objects.get(ip=hostip)
        hostinfo2.idle = True
        hostinfo2.save()
    return result

@shared_task()
def sid_init(mextra_vars,sextra_vars):
    result = {"ansible_res":[],"status":"SUCCESS"}
    res1=""
    res2=""
    res1 = ansible_handle("/opt/ansible/roles/site.yml",mextra_vars)
    result["ansible_res"].append(res1)
    res2 = ansible_handle("/opt/ansible/roles/site.yml",sextra_vars)
    result["ansible_res"].append(res2)
    if filter(lambda x:"failed=0" in x,res1) and filter(lambda x:"failed=0" in x,res2):
        master_sid_info = SidInfo()
        master_sid_info.sidname = mextra_vars["sid"]
        master_sid_info.appname = mextra_vars["sid"].split("_")[0]
        master_sid_info.hostip=mextra_vars["hosts"]
        master_sid_info.port=mextra_vars["port"]
        master_sid_info.socketpath="/mysql_data/"+master_sid_info.sidname+"/tmp/mysql.sock"
        master_sid_info.password=mextra_vars["password"]
        master_sid_info.replpassword=mextra_vars["replpassword"]
        master_sid_info.data_size=mextra_vars["data_size"]
        master_sid_info.buffer_pool=mextra_vars["buffer_pool"]
        master_sid_info.save()
        slave_sid_info = SidInfo()
        slave_sid_info.sidname = sextra_vars["sid"]
        slave_sid_info.appname = sextra_vars["sid"].split("_")[0]
        slave_sid_info.hostip=sextra_vars["hosts"]
        slave_sid_info.port=sextra_vars["port"]
        slave_sid_info.socketpath="/mysql_data/"+slave_sid_info.sidname+"/tmp/mysql.sock"
        slave_sid_info.password=sextra_vars["password"]
        slave_sid_info.replpassword=sextra_vars["replpassword"]
        slave_sid_info.data_size=sextra_vars["data_size"]
        slave_sid_info.buffer_pool=sextra_vars["buffer_pool"]
        slave_sid_info.save()
        hostip_port=Hostip_Port.objects.get(hostip=mextra_vars["hosts"])
        hostip_port.port=hostip_port.port+1
        hostip_port.save()
        hostip_port2=Hostip_Port.objects.get(hostip=sextra_vars["hosts"])
        hostip_port2.port=hostip_port2.port+1
        hostip_port2.save()
        mhostinfo = HostInfo.objects.get(ip=mextra_vars["hosts"])
        mhostinfo.memory_used +=int(mextra_vars["buffer_pool"])*1024
        mhostinfo.memory_free = mhostinfo.memory_total - mhostinfo.memory_used
        mhostinfo.save()
        shostinfo = HostInfo.objects.get(ip=sextra_vars["hosts"])
        shostinfo.memory_used +=int(sextra_vars["buffer_pool"])*1024
        shostinfo.memory_free = shostinfo.memory_total - shostinfo.memory_used
        shostinfo.save()
        update_info(mextra_vars["hosts"]+":"+sextra_vars["hosts"])
        result["status"] = "SUCCESS"
    else:
        result["status"] = "FAILED"
    hostinfo = HostInfo.objects.get(ip=mextra_vars["hosts"])
    hostinfo.idle = True
    hostinfo.save()
    hostinfo2 = HostInfo.objects.get(ip=sextra_vars["hosts"])
    hostinfo2.idle = True
    hostinfo2.save()
    return result

@shared_task()
def sid_update_task(mextra_vars,sextra_vars):
    result = {"ansible_res":[],"status":"SUCCESS"}
    res1 = ""
    res2 = ""
    res1 = ansible_handle("/opt/ansible/roles/site.yml",mextra_vars)
    result["ansible_res"].append(res1)
    res2 = ansible_handle("/opt/ansible/roles/site.yml",sextra_vars)
    result["ansible_res"].append(res2)
    if filter(lambda x:"failed=0" in x,res1) and filter(lambda x:"failed=0" in x,res2):
        master_sid_info = SidInfo.objects.get(sidname=mextra_vars["sid"])
        mhostinfo = HostInfo.objects.get(ip=mextra_vars["hosts"])
        mhostinfo.memory_used = mhostinfo.memory_used+(int(master_sid_info.buffer_pool)-int(mextra_vars["buffer_pool"]))*1024
        mhostinfo.memory_free = mhostinfo.memory_total - mhostinfo.memory_used
        mhostinfo.save()
        master_sid_info.data_size=mextra_vars["data_size"]
        master_sid_info.buffer_pool=mextra_vars["buffer_pool"]
        master_sid_info.save()
        slave_sid_info = SidInfo.objects.get(sidname=sextra_vars["sid"])
        shostinfo = HostInfo.objects.get(ip=sextra_vars["hosts"])
        shostinfo.memory_used = shostinfo.memory_used+(int(slave_sid_info.buffer_pool)-int(sextra_vars["buffer_pool"]))*1024
        shostinfo.memory_free = shostinfo.memory_total - shostinfo.memory_used
        shostinfo.save()
        slave_sid_info.data_size=sextra_vars["data_size"]
        slave_sid_info.buffer_pool=sextra_vars["buffer_pool"]
        slave_sid_info.save()
        update_info(mextra_vars["hosts"]+":"+sextra_vars["hosts"])
        result["status"] = "SUCCESS"
    else:
        result["status"] = "FAILED"
    hostinfo = HostInfo.objects.get(ip=mextra_vars["hosts"])
    hostinfo.idle = True
    hostinfo.save()
    hostinfo2 = HostInfo.objects.get(ip=sextra_vars["hosts"])
    hostinfo2.idle = True
    hostinfo2.save()
    return result

@shared_task()
def com_playbook(extra_vars,playbook_path):
    result = {"ansible_res":"","status":"SUCCESS"}
    try:
        result["ansible_res"] = ansible_handle(playbook_path,extra_vars)
        for hostip in extra_vars["hosts"].split(":"):
            birefres = filter(lambda x:hostip in x,result["ansible_res"])[-1]
            if ("failed=0" not in birefres) or ("unreachable=0" not in birefres):
                result["status"] = "FAILED"
    except Exception:
        result["status"] = "FAILED"
    return result

@shared_task()
def db_dump(extra_vars,flag=False,mysql_bk_name=""):
    result = {"ansible_res":"","status":"SUCCESS"}
    try:
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        result["ansible_res"] = ansible_handle("/opt/ansible/mysql/database_exp.yml",extra_vars)
        stoptime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if "ok=1" not in ansible_res[-2]:
            result["status"] = "FAILED"
    except Exception:
        result["status"] = "FAILED"
    if flag:
        shd_res = Schedule_Res(mysql_bk_name=mysql_bk_name,result=ansible_res,star_time=startime,stop_time=stoptime,status=status)
        shd_res.save()
    return result

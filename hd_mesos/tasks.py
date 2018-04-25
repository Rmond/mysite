# -*- coding:utf-8 -*-
import os,json,re
from celery import shared_task
from models import HostInfo

@shared_task
def update_info(host):
    ansible_res = ansible_handle(host)
    fact_list = re.split('\d+\.\d+\.\d+\.\d+ \| SUCCESS => ',"".join(ansible_res))[1:]
    if host == "all":
        hostinfo_set = HostInfo.objects.all()
        for hostinfo in hostinfo_set:
            for fact in fact_list:
                if hostinfo.ip in fact:
                    hostinfo_save(hostinfo,fact)
    else:
        for hostip in host.split(':'):
            for fact in fact_list:
                if hostip in fact:
                    hostinfo = HostInfo.objects.get(ip=hostip)
                    hostinfo_save(hostinfo,fact)


def hostinfo_save(hostinfo,fact):
    fact_json = json.loads(fact)
    hostinfo.memory_total = int(fact_json["ansible_facts"]["ansible_memory_mb"]["real"]["total"])
    hostinfo.memory_free = hostinfo.memory_total - hostinfo.memory_used
    hostinfo.vginfo = json.dumps(fact_json["ansible_facts"]["ansible_lvm"]["vgs"])
    hostinfo.hostname = fact_json["ansible_facts"]["ansible_hostname"]
    hostinfo.save()

def ansible_handle(host):
    shellstr = "ansible "+host+" -m setup"
    return os.popen(shellstr).read().splitlines()

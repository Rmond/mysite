# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json,os
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from hd_mesos.models import HostInfo,Host_Group
from hd_ansible.models import ScriptInfo
from hd_mesos.views import login_check

@csrf_exempt
@login_check
def hostip_check(request):#添加主机前，判断主机是否存在
    if request.method == 'POST':
        hostip = request.POST['hostip']
        if HostInfo.objects.filter(ip=hostip):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def scriptname_check(request):
    if request.method == 'POST':
        script_name = request.POST['ScriptName']
        if ScriptInfo.objects.filter(name=script_name):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def hostidle_check(request):
    if request.method == 'POST':
        hostip = request.POST['HostIP']
        hostinfo = HostInfo.objects.get(ip=hostip)
        if hostinfo.idle:
            return HttpResponse(1)
        else:
            return HttpResponse(0)
        
@csrf_exempt
@login_check
def hostip_get(request):
    if request.method == 'POST':
        hostgroup_list = request.POST.getlist('groupname')
        hostip_list = []
        for group_id in hostgroup_list:
            for host_group in Host_Group.objects.filter(group_id=group_id):
                if host_group.ip_id not in hostip_list:
                    hostip_list.append(host_group.ip_id)
        return HttpResponse(json.dumps({"hosts":hostip_list}))

# -*- coding:utf-8 -*-
import json
import os
import datetime
import time

from django.http.response import HttpResponse
from django.shortcuts import render , redirect
from django.views.decorators.csrf import csrf_exempt
from hd_mesos.views import login_check,user_role

from hd_ansible.models import Software
from hd_mesos.models import HostInfo,HostGroup,Host_Group,User_Task
from django_celery_results.models import TaskResult
from hd_ansible.tasks import install,update

from celery.result import AsyncResult

@login_check
def software_install(request):
    return render(request,"mesos/hd_ansible/software/install.html")

@login_check
def software_update(request):
    return render(request,"mesos/hd_ansible/software/update.html")

@csrf_exempt
@login_check
def software_installed(request):
    if request.method == 'POST':
        hosts = request.POST.getlist('host_assets')
        groupids = request.POST.getlist('grp_assets')
        if len(hosts)+len(groupids) > 0:
            softname = Software.objects.get(id = request.POST["Softname"]).softname
            for i in groupids:
                for host_group in Host_Group.objects.filter(group_id=i):
                    hosts.append(host_group.ip_id)
            hosts = list(set(hosts))
            flag = True
            filterlist = []
            for hostip in hosts:
                hostinfo = HostInfo.objects.get(ip=hostip)
                if softname in hostinfo.software:#判断主机是否安装此软件
                    pass
                else:
                    filterlist.append(hostip)
                    if not hostinfo.idle:
                        flag = False
                        break
            if len(filterlist) > 0:
                if flag:
                    for hostip in filterlist:
                        hostinfo = HostInfo.objects.get(ip=hostip)
                        hostinfo.idle = False
                        hostinfo.save()
                    hoststr = ":".join(filterlist)
                    extra_vars = {}
                    extra_vars["hosts"] = hoststr
                    extra_vars["role"] = softname
                    extra_vars["version"] = request.POST["SoftVersion"]
                    extra_vars["flag_fact"] = "false"
                    extra_vars["option"] = "install.yml"
                    taskname = softname+"_install"
                    username = request.session.get("username",None)
                    startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    softinfo = softname+"-"+request.POST["SoftVersion"]
                    try:
                        taskobj = install.apply_async([extra_vars,softinfo])
                    except Exception:
                        for hostip in filterlist:
                            hostinfo = HostInfo.objects.get(ip=hostip)
                            hostinfo.idle = True
                            hostinfo.save()
                    user_task = User_Task(username_id = username,star_time= startime,taskid=taskobj.id,hosts=hoststr,taskname=taskname)
                    user_task.save()
                    return redirect('/hd_mesos/tasklist.html')
                else:
                    return render(request,"mesos/hd_ansible/software/install.html",{"error":"目标主机有任务进行，请稍等"})
            else:
                return render(request,"mesos/hd_ansible/software/install.html",{"error":"所选主机已全部安装此软件"})
        else:
            return render(request,"mesos/hd_ansible/software/install.html",{"error":"请至少选择一个目标主机或主机组"})

@csrf_exempt
@login_check
def software_updated(request):
    if request.method == 'POST':
        hosts = request.POST.getlist('host_assets')
        groupids = request.POST.getlist('grp_assets')
        if len(hosts)+len(groupids) > 0:
            softname = Software.objects.get(id = request.POST["Softname"]).softname
            for i in groupids:
                for host_group in Host_Group.objects.filter(group_id=i):
                    hosts.append(host_group.ip_id)
            hosts = list(set(hosts))
            for hostip in hosts:
                flag = True
                hostinfo = HostInfo.objects.get(ip=hostip)
                if not hostinfo.idle:
                    flag = False
                    break
            if flag:
                hoststr = ":".join(hosts)
                extra_vars = {}
                extra_vars["hosts"] = hoststr
                extra_vars["role"] = softname
                extra_vars["version"] = request.POST["SoftVersion"]
                extra_vars["flag_fact"] = False
                extra_vars["option"] = "update.yml"
                taskname = softname+"_update"
                username = request.session.get("username",None)
                startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                softinfo = softname+"-"+request.POST["SoftVersion"]
                try:
                     taskobj = update.apply_async([extra_vars,softinfo])
                except Exception:
                     for hostip in filterlist:
                         hostinfo = HostInfo.objects.get(ip=hostip)
                         hostinfo.idle = True
                         hostinfo.save()
                user_task = User_Task(username_id = username,star_time= startime,taskid=taskobj.id,hosts=hoststr,taskname=taskname)
                user_task.save()
                return redirect('/hd_mesos/tasklist.html')
            else:
                return render(request,"mesos/hd_ansible/software/update.html",{"error":"目标主机有任务进行，请稍等"})
        else:
            return render(request,"mesos/hd_ansible/software/update.html",{"error":"请至少选择一个目标主机或主机组"})

@csrf_exempt
@login_check
def software_select(request):
    if request.method == 'POST':
        received_data = json.loads(request.body)
        data = {}
        if received_data["MyColums"] == 'SoftName':
            softwarelist = Software.objects.all()
            for i in softwarelist:
                data[i.id]=i.softname
        elif received_data["MyColums"] == 'SoftVersion':
            software = Software.objects.get(id=received_data["parentId"])
            if "mysql" in software.softname:
                ver_list = Software.objects.get(softname="mysql").version.split(",")
                for i in range(0,len(ver_list)):
                    data[i]=ver_list[i]
    return HttpResponse(json.dumps(data), content_type='application/json')

@csrf_exempt
@login_check
def grouphost_get(request):
    hostiplist = {}
    groupnamelist = {}
    if request.POST['softid']:
        softname = Software.objects.get(id = request.POST["softid"]).softname
        hosts = HostInfo.objects.filter(tags__icontains = softname)#查找打了标签的主机
        groups = HostGroup.objects.all()
        for host in hosts:
            hostiplist[host.ip] = host.ip
        for group in groups:
            hostlist = HostInfo.objects.filter(host_group__group_id=group.id)
            flag = True
            if hostlist:
                for host in hostlist:
                    if softname not in host.tags:
                        flag = False
                if flag:
                    groupnamelist[group.id] = group.groupname
    return HttpResponse(json.dumps({"groups":groupnamelist,"hosts":hostiplist}))
    
@csrf_exempt
@login_check
def u_grouphost_get(request):
    hostiplist = {}
    groupnamelist = {}
    if request.POST['softid']:
        softname = Software.objects.get(id = request.POST['softid']).softname
        hosts = HostInfo.objects.filter(software__icontains = softname)#查找打了标签的主机
        groups = HostGroup.objects.all()
        for host in hosts:
            hostiplist[host.ip] = host.ip
        for group in groups:#循环判断主机组中主机是否都安装软件
            hostlist = HostInfo.objects.filter(host_group__group_id=group.id)
            flag = True
            if hostlist:
                for host in hostlist:
                    if softname not in host.software:
                        flag = False
                if flag:
                    groupnamelist[group.id] = group.groupname
    return HttpResponse(json.dumps({"groups":groupnamelist,"hosts":hostiplist}))

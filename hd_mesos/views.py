# -*- coding:utf-8 -*-
from __future__ import print_function

import base64
import json,os,datetime,time
import xlrd

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password

from models import HostInfo, Users,HostGroup,Host_Group,User_Host,User_Hostgroup,User_Task,User_Shell_Task,User_Yum_Task
from hd_ansible.models import Software,Hostip_Port
from django_celery_results.models import TaskResult
from celery.result import AsyncResult
from tasks import update_info

def login_check(func):#登录检查装饰器
    def wrapper(request,*args,**kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname,passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(uname,passwd)
                    if user:
                        request.session['is_login'] = user.nickname
                        request.session['username'] = user.username
                        request.session['role'] = user.role
                        request.session['authmethod'] = "basic"
        nickname = request.session.get('is_login',None)
        if not nickname:
            return redirect('/hd_mesos/login')
        return func(request,*args,**kwargs)
    return wrapper

def user_role(func):#用户角色检查装饰器
    def wrapper(request):
        role = request.session.get('role',None)
        if role == 0:#管理员
            return func(request)
        elif role == 1:#普通用户
            return func('Permission denied')
    return wrapper

def authenticate(username,password):
    try:
        user = Users.objects.get(username=username)
        if check_password(password, user.password):  # 登录判断
            return user
        else:  # 判断密码是否正确
            return None
    except Users.DoesNotExist:  # 判断用户是否存在
        return None

# Create your views here.
@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username,password)
        if user:
            request.session['is_login'] = user.nickname
            request.session['username'] = user.username
            request.session['role'] = user.role
            return redirect('/hd_mesos/index')
        else:#判断密码是否正确
            return render(request,"mesos/login.html",{'msg':'用户名或密码错误'})
    return render(request,"mesos/login.html")

@login_check
def index(request):
    user_count = Users.objects.count()
    host_count = HostInfo.objects.count()
    return render(request,"mesos/index.html",{"user_count":user_count,"host_count":host_count})

@csrf_exempt
@login_check 
def task_chart(request):
    name=[]
    num=[]
    for i in range(6,-1,-1):
        star_date=datetime.date.today()+datetime.timedelta(days=-i)
        stop_date=datetime.date.today()+datetime.timedelta(days=-i+1)
        user_task_ct = User_Task.objects.filter(star_time__gte = star_date).filter(star_time__lt = stop_date).count()
        name.append(star_date.strftime('%Y-%m-%d'))
        num.append(user_task_ct)
    return HttpResponse(json.dumps({"name":name,"num":num}))

@login_check 
def logout(request):       
    del request.session['is_login']
    return redirect('/hd_mesos/login')

@login_check 
def user_list(request):#用户列表展示
    results = Users.objects.all()
    return render(request,"mesos/userlist.html",{'users':results})

@csrf_exempt
@login_check
def pwd_reset(request):#密码重置为6个1
    if request.method == 'POST':
        username = request.POST['username']
        user = Users.objects.get(username=username)
        user.password = make_password('111111')
        user.save()
        return HttpResponse("密码重置成功！")

@csrf_exempt
@login_check
@user_role
def user_add(request):#用户添加或修改
    if request.method == 'POST':
        username = request.POST['username']
        nickname = request.POST['nickname']
        role = request.POST['role']
        if Users.objects.filter(username=username):#判断用户是否存在
            user = Users.objects.get(username=username)
            user.nickname = nickname
            user.role = role
        else:
            password = make_password('111111')
            user =  Users(username=username,nickname=nickname,password=password,role=role)
        user.save()
        return redirect('userlist.html')

@csrf_exempt
@login_check
@user_role
def user_del(request):#用户删除
    if request.method == 'POST':
        username = request.POST['username']
        Users.objects.filter(username=username).delete()
        return HttpResponse('Success')
    
@csrf_exempt
@login_check
@user_role
def user_look(request):#用户信息查看
    if request.method == 'POST':
        username = request.POST['username']
        user = Users.objects.get(username=username)
        return HttpResponse(json.dumps({"username":user.username,"nickname":user.nickname,"role":user.role}))
    return HttpResponse('Error Method')
    
@csrf_exempt
@login_check
def username_check(request):#添加用户时，表单查询用户是否存在
    if request.method == 'POST':
        username = request.POST['username']
        if Users.objects.filter(username=username):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check  
def user_info(request):
    if request.method == 'POST':
        username = request.session.get('username',None)
        user = Users.objects.get(username = username)
        return HttpResponse(json.dumps({'username':user.username,'nickname':user.nickname}))
    
@csrf_exempt
@login_check
@user_role
def user_edit(request):
    if request.method == 'POST':
        username = request.POST['username']
        nickname = request.POST['nickname']
        password = request.POST['password']
        user = Users.objects.get(username = username)
        user.nickname = nickname
        user.password = make_password(password)
        user.save()
        return HttpResponse("Success")

@login_check
@user_role
def host_list(request):#主机列表
    if request.session.get('role'):
        hosts = HostInfo.objects.filter(user_host__username_id = request.session.get('username'))
    else:
        hosts = HostInfo.objects.all()
    results = {'hosts':hosts}
    return render(request,"mesos/hostlist.html",results)

@login_check
@user_role
def hostgroups(request):#主机组列表
    if request.session.get('role'):
        groups = HostGroup.objects.filter(user_hostgroup__username_id = request.session.get('username'))
    else:
        groups = HostGroup.objects.all()
    results = {'groups':groups}
    return render(request,"mesos/hostgroups.html",results)

@csrf_exempt
@login_check
@user_role
def host_del(request):#主机删除
    if request.method == 'POST':
        hostip = request.POST['hostip']
        HostInfo.objects.filter(ip=hostip).delete()
        return HttpResponse("Success")

@csrf_exempt
@login_check
@user_role
def hostlist_del(request):
    if request.method == 'POST':
        checklist=request.POST.getlist('checklist')
        for hostip in checklist:
            HostInfo.objects.filter(ip=hostip).delete()
        return HttpResponse()

@csrf_exempt
@login_check
@user_role
def host_add(request):#主机添加或修改
    if request.method == 'POST':
        hostip = request.POST['hostip']
        hostname = request.POST['hostname']
        SelectTags = request.POST.getlist('tags_select')
        SelectGroupId = request.POST.getlist('asset_select')
        tags = ""
        for tagid in SelectTags:
            tags+=Software.objects.get(id=tagid).softname+" "  
        hostinfo =  HostInfo(hostname=hostname,ip=hostip,tags=tags)
        hostinfo.save()
        for i in SelectGroupId:#判断主机组是否被选中
            host_group = Host_Group(group_id=i,ip_id=hostip)
            host_group.save()
        if request.session.get('authmethod',None):
            return HttpResponse('Success')
        else:
            return redirect('/hd_mesos/hostlist')

@csrf_exempt
@login_check
def host_look(request,hostip):#主机信息更改
    groupsel = {}
    groupunsel = {}
    tagsel = {}
    tagunsel = {}
    hostinfo=HostInfo.objects.get(ip=hostip)
    for group in HostGroup.objects.all():#循环主机组
        try:#判断主机组是否包含此主机
            Host_Group.objects.get(ip_id=hostip,group_id=group.id)
            groupsel[group.id]=group.groupname
        except Host_Group.DoesNotExist:
            groupunsel[group.id]=group.groupname
    for tagobj in Software.objects.all():
        if tagobj.softname in hostinfo.tags:
            tagsel[tagobj.id] = tagobj.softname
        else:
            tagunsel[tagobj.id] = tagobj.softname
    vginfo_list = {} if not hostinfo.vginfo else json.loads(hostinfo.vginfo)
    return render(request,"mesos/hostedit.html",{"hostinfo":hostinfo,"groupsel":groupsel,"groupunsel":groupunsel,"tagsel":tagsel,"tagunsel":tagunsel,"vginfo_list":vginfo_list})

@csrf_exempt
@login_check
@user_role
def host_edit(request):
    if request.method == 'POST':
        HostIP = request.POST['hostip']
        SelectTags = request.POST.getlist('tags_select')
        SelectGroupId = request.POST.getlist('asset_select')
        UnselectGroupId = request.POST.getlist('assets')
        hostinfo = HostInfo.objects.get(ip=HostIP)
        hostinfo.hostname= request.POST['hostname']
        tagstr = ""
        for tag in SelectTags:
            tagstr+=Software.objects.get(id=tag).softname+" "
        hostinfo.tags=tagstr
        hostinfo.save()
        for i in SelectGroupId:#判断主机组是否被选中
            try:
                host_group = Host_Group.objects.get(group_id=i,ip_id=HostIP)
            except Host_Group.DoesNotExist:
                host_group = Host_Group(group_id=i,ip_id=HostIP)
                host_group.save()
        for j in UnselectGroupId:
            host_group = Host_Group.objects.filter(group_id=j,ip_id=HostIP).delete()
        return redirect('hostlist')

@csrf_exempt
@login_check    
def host_update(request):
    if request.method == 'POST':
        checklist=request.POST.getlist('checklist')
        if "checkall" in checklist:
            host="all"
        else:
            host=":".join(checklist)
        update_info.apply_async([host])
        return HttpResponse()

@login_check
def group_add(request):
    if request.method == 'POST':
        Groupname = request.POST['Groupname']
        Groupid = request.POST['Groupid']
        if Groupid: #判断主机组是否存在，如果存在更改相应的主机名，不存在添加主机组
            hostgroup=HostGroup.objects.get(id=Groupid)
            hostgroup.groupname = Groupname
        else:
            hostgroup = HostGroup(groupname=Groupname)
        hostgroup.save()
        SelectGroupId = request.POST.getlist('asset_select')#属于主机组的主机
        UnSelectGroupId = request.POST.getlist('assets')#不属于主机组的主机
        for i in SelectGroupId:
            try:
                Host_Group.objects.get(ip_id=i,group_id=hostgroup.id)#判断主机是否添加过，添加过则不操作
            except Host_Group.DoesNotExist:
                host_group = Host_Group(ip_id=i,group_id=hostgroup.id)#把主机添加到跟主机组的关系表
                host_group.save()
        for j in UnSelectGroupId:
            Host_Group.objects.filter(ip_id=j,group_id=hostgroup.id).delete()#删除在非选中框中的主机
        return redirect('hostgroups.html')

@csrf_exempt
@login_check
def group_look(request):
    if request.method == 'POST':
        selected = {}
        unselected = {}
        Groupname = request.POST['Groupname']
        hostgroup=HostGroup.objects.get(groupname=Groupname)
        for host in HostInfo.objects.all():#循环判断主机是否属于主机组
            try:
                Host_Group.objects.get(ip_id=host.ip,group_id=hostgroup.id)
                selected[host.ip]=host.ip
            except Host_Group.DoesNotExist:
                unselected[host.ip]=host.ip
        return HttpResponse(json.dumps({"groupid":hostgroup.id,"groupname":hostgroup.groupname,"selected":selected,"unselected":unselected}))

@csrf_exempt
@login_check
def hostgrp_check(request):
    if request.method == 'POST':
        HostGrp = request.POST['HostGrp']
        if HostGroup.objects.filter(groupname=HostGrp):
            return HttpResponse(0)
        else:
            return HttpResponse(1)
        
@csrf_exempt
@login_check
def group_del(request):
    if request.method == 'POST':
        Groupname = request.POST['Groupname']
        HostGroup.objects.filter(groupname=Groupname).delete()
        return HttpResponse()

@csrf_exempt
@login_check
def group_tag_ajaxget(request):
    groups = HostGroup.objects.all()
    tags = Software.objects.all()
    grouplist = {}
    taglist = {}
    for group in groups:
        grouplist[group.id] = group.groupname
    for tag in tags:
        taglist[tag.id] = tag.softname
    return HttpResponse(json.dumps({"grouplist":grouplist,"taglist":taglist}))       

@csrf_exempt
@login_check
def host_ajaxget(request):
    hosts = HostInfo.objects.all()
    hostlist = {}
    for host in hosts:
        hostlist[host.ip]=(host.ip)
    return HttpResponse(json.dumps({"hostlist":hostlist}))

@csrf_exempt
@login_check
def privilege_list(request):
    users = Users.objects.all()
    return render(request,"mesos/privilegelist.html",{'users':users})

@csrf_exempt
@login_check
def privilege_look(request):
    if request.method == 'POST':
        grpselected = {}
        grpunselected = {}
        hostselected = {}
        hostunselected = {}
        Username= request.POST['Username']
        for host in HostInfo.objects.all():#循环判断主机是否被授权
            try:
                User_Host.objects.get(username_id=Username,ip_id=host.ip)
                hostselected[host.ip] = host.ip
            except User_Host.DoesNotExist:
                hostunselected[host.ip] = host.ip
        for group in HostGroup.objects.all():#循环判断主机组是否被授权
            try:
                User_Hostgroup.objects.get(username_id=Username,group_id=group.id)
                grpselected[group.id] = group.groupname
            except User_Hostgroup.DoesNotExist:
                grpunselected[group.id] = group.groupname
    return HttpResponse(json.dumps({"username":Username,"hostselected":hostselected,"hostunselected":hostunselected,"grpselected":grpselected,"grpunselected":grpunselected}))

@csrf_exempt
@login_check
def privileg_edit(request):
    if request.method == 'POST':
        Username = request.POST['Username']
        SelectGroupId = request.POST.getlist('grp_asset_select')
        UnSelectGroupId = request.POST.getlist('grp_assets')
        SelectHost = request.POST.getlist('host_asset_select')
        UnSelectHost = request.POST.getlist('host_assets')
        for i in SelectGroupId:
            try:
                User_Hostgroup.objects.get(username_id=Username,group_id=i)#判断主机组是否添加过，添加过则不操作
            except User_Hostgroup.DoesNotExist:
                user_hostgroup = User_Hostgroup(username_id=Username,group_id=i)#把主机组添加到跟用户的关系表
                user_hostgroup.save()
        for j in UnSelectGroupId:
            User_Hostgroup.objects.filter(username_id=Username,group_id=j).delete()
        for x in SelectHost:
            try:
                User_Host.objects.get(username_id=Username,ip_id=x)
            except User_Host.DoesNotExist:
                user_host = User_Host(username_id = Username,ip_id = x)
                user_host.save()
        for y in UnSelectHost:
            User_Host.objects.filter(username_id = Username,ip_id = y).delete()
    return redirect('privilegelist.html')

@login_check
def task_list(request,option="others"):
    if option == "others":
        tasklist = User_Task.objects.filter(username_id=request.session.get('username',None))
        template = "mesos/tasklist.html"
    elif option == "shell":
        tasklist = User_Shell_Task.objects.filter(username_id=request.session.get('username',None))
        template = "mesos/task_mge/shelltasklist.html"
    elif option == "yum":
        tasklist = User_Yum_Task.objects.filter(username_id=request.session.get('username',None))
        template = "mesos/task_mge/yumtasklist.html"
    for task in tasklist:
        if not task.result:
            task.status = AsyncResult(task.taskid).state
            try:
                taskres = TaskResult.objects.get(task_id=task.taskid)
                task.date_done = taskres.date_done
                result = json.loads(taskres.result)
                task.result = json.dumps(result["ansible_res"])
                task.status = result["status"]
            except TaskResult.DoesNotExist:
                pass
            task.save()
    return render(request,template,{"tasklist":tasklist})

@login_check
def task_info(request,*args,**kwargs):
    if kwargs['option'] == "shell":
        user_task = User_Shell_Task.objects.get(id = kwargs['taskid'])
    elif kwargs['option'] == "yum":
        user_task = User_Yum_Task.objects.get(id = kwargs['taskid'])
    else:
        user_task = User_Task.objects.get(id = kwargs['taskid'])
    if user_task.result:
        result = user_task.result.replace("[","").replace("]","").replace("\"","").decode("unicode-escape").split(",")
    else:
        result = []
    return render(request,"mesos/taskinfo.html",{"user_task":user_task,"result":result})

@csrf_exempt
@login_check
def task_ack(request):
    if request.method == 'POST':
        usertaskid = request.POST['id']
        user_task = User_Task.objects.get(id=usertaskid)
        user_task.acked = True
        user_task.save()
        return HttpResponse()

@csrf_exempt 
@login_check
@csrf_exempt
def host_import(request):
    if request.method == "POST":
        f = request.FILES.get('xlsname')
        filename = os.path.join("/tmp",f.name)
        with open(filename,'wb') as fobj:
            for chunck in f.chunks():
                fobj.write(chunck)
        xlsfile = xlrd.open_workbook(filename)
        xlstable = xlsfile.sheet_by_index(0)
        rowscount = xlstable.nrows
        for num in range(1,rowscount):
            hostname = xlstable.row_values(num)[0]
            hostip = xlstable.row_values(num)[1]
            try:
                hostinfo = HostInfo.objects.get(ip=hostip)
                hostinfo.hostname = hostname
            except HostInfo.DoesNotExist:
                hostinfo = HostInfo(hostname=hostname,ip=hostip)
            hostinfo.save()
        return redirect('/hd_mesos/hostlist')

@csrf_exempt
@login_check
def asserts_list(request):
    if request.method == 'POST':
        search = request.POST.get('search[value]')
        draw = int(request.POST.get('draw'))
        start = int(request.POST.get('start'))
        length = int(request.POST.get('length'))
        end = start+length
        if request.session.get('role'):
            hostinf_set = HostInfo.objects.filter(user_host__username_id = request.session.get('username'))
        else:
            hostinf_set = HostInfo.objects.all()
        if search != "":
            hostinf_set = hostinf_set.filter(Q(hostname__contains=search)|Q(ip__contains=search)|Q(software__contains=search))
        assets_list = hostinf_set.values_list('hostname','ip','tags').order_by('ip')[start:end]
        asset_count = hostinf_set.count()
        _filter = asset_count
        all_lists = map(list,assets_list)
        for row in all_lists:
            groups = ""
            for host_group in Host_Group.objects.filter(ip=row[1]):
                groups=groups+host_group.group.groupname+" "
            row.append(groups)
        data = {
            'draw':draw,
            'recordsTotal':asset_count,
            'recordsFiltered':_filter,
            'data':all_lists
        }
        return HttpResponse(json.dumps(data))

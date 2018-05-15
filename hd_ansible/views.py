# -*- coding:utf-8 -*-
from __future__ import print_function
import json,os,time,datetime,re

from django.http.response import HttpResponse
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt

from getprolist import GetProList
from getfilepath import GetFilePath
from django_celery_results.models import TaskResult
from mysite import settings
from hd_mesos.views import login_check,user_role
from hd_mesos.models import HostInfo,HostGroup,User_Task,Host_Group,User_Shell_Task,User_Yum_Task
from models import MysqlAduit,OptionLog,SidInfo,Hostip_Port,ScriptInfo
from django.contrib.auth.hashers import make_password
from tasks import sid_init,sid_update_task,com_playbook
from hd_mesos.tasks import update_info
from mysite.settings import SHELL_PATH,PLAYBOOK_PATH
# Create your views here.

ProNameitems = [{"Id":"oms","Name":"OMS"},{"Id":"wms","Name":"WMS"},{"Id":"scm","Name":"SCM"}]
ProAppitems = [{"Id":"scm-web","Name":"SCM-WEB","Type":"scm"},{"Id":"oms-web","Name":"OMS-WEB","Type":"oms"}]
ProVersionitems = [{"Id":"scm-web-1704","Name":"SCM-WEB-1704","Type":"scm-web"},{"Id":"web","Name":"WEB","Type":"oms-web"}]


@login_check
def inventory_mge(request):
    with open("/etc/ansible/hosts") as f:
        hosts = f.read().splitlines()
    return render(request,"mesos/ansible/inventory/inventorymge.html",{"hosts":hosts})

@login_check
@user_role
def rollback(request,tempath):
    tempath = tempath
    if request.method == 'POST':#返回执行结果
        hosts = request.POST.getlist('host_assets')
        groupids = request.POST.getlist('grp_assets')
        if len(hosts)+len(groupids) > 0:
            destserver = ""
            for host in hosts:
                destserver+=host+":"
            for groupid in groupids:
                group = HostGroup.objects.get(id=groupid)
                destserver+=group.groupname.lower()+":"
            war_srcpath = "/opt/war_manage/"+request.POST["ProName"]+"/"+request.POST["ProApp"]+"/"+request.POST["ProVersion"]+"/"
            war_destpath = request.POST["HostPath"]
            return render(request,tempath+"ansible/tomcat/rollbackres.html",{"hosts":destserver,"war_srcpath":war_srcpath,"war_destpath":war_destpath})
        else:
            return render(request,tempath+"ansible/tomcat/rollback.html",{"error":"请至少选择一个目标主机或主机组"})
    return render(request,tempath+"ansible/tomcat/rollback.html")#返回回滚界面

@login_check
@user_role
def project_dev(request,tempath):
    tempath = tempath
    return render(request,tempath+"ansible/tomcat/projectdev.html")

@csrf_exempt
@login_check
def upload_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist('tomcat_war') 
        for f in files:
            handle_upload_file(f)
        return HttpResponse("OK")
    return render(request,"mesos/ansible/tomcat/projectdev.html")

def handle_upload_file(f):
    file_name = "%s/%s" %(settings.UPLOAD_DIR,f.name)
    f_obj = open(file_name,'wb+')
    for chunk in f.chunks():
        f_obj.write(chunk)
    f_obj.close()
 
@csrf_exempt
@login_check
def grouphost_get(request):
    hostiplist = {}
    groupnamelist = {}
    hosts = HostInfo.objects.filter(user_host__username_id = request.session.get('username'))
    groups = HostGroup.objects.filter(user_hostgroup__username_id = request.session.get('username'))
    for host in hosts:
        hostiplist[host.ip] = host.ip
    for group in groups:
        groupnamelist[group.id] = group.groupname
    return HttpResponse(json.dumps({"groups":groupnamelist,"hosts":hostiplist}))

@csrf_exempt
@login_check
def yum_manage(request,option):
    grouplist = HostGroup.objects.all()
    if option == "install":
        temp_path="install.html"
    elif option == "update":
        temp_path="update.html"
    elif option == "delete":
        temp_path="delete.html"
    return render(request,"mesos/ansible/yum/"+temp_path ,{"grouplist":grouplist})

@csrf_exempt
@login_check
def yum_execute(request,option):
    if request.method == 'POST':
        if option=="install":
            state="present"
        elif option=="update":
            state="latest"
        elif option=="delete":
            state="absent"
        hosts = request.POST.getlist('host_assets')
        if 'all' in hosts:
            hosts.remove("all")        
        hoststr = ":".join(hosts)
        extra_vars = {}
        extra_vars["hosts"] = hoststr
        extra_vars["softname"] = request.POST["Softname"]
        extra_vars["state"] = state
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        taskname = username+"-"+request.POST["Softname"].split(",")[0]
        playbook_path = "/opt/ansible/yum/manage.yml"
        taskobj = com_playbook.apply_async([extra_vars,playbook_path])
        user_task = User_Yum_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=hoststr,taskname=taskname,soft_list=extra_vars["softname"])
        user_task.save()
        return redirect('/hd_mesos/tasklist/yum')

@csrf_exempt
@login_check
def command_exec(request):
    if request.method == 'GET':
        grouplist = HostGroup.objects.all()
        return render(request,"mesos/ansible/command/execute.html" ,{"grouplist":grouplist})
    if request.method == 'POST':
        hosts = request.POST.getlist('host_assets')
        if 'all' in hosts:
            hosts.remove("all")
        hoststr = ":".join(hosts)
        extra_vars = {}
        extra_vars["hosts"] = hoststr
        extra_vars["shell_cmd"] = request.POST["Command"]
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        if request.POST["Name"]:
            taskname = request.POST["Name"]
        else:
            taskname = username+"-"+request.POST["Command"].split()[0]
        playbook_path = "/opt/ansible/cmd/execute.yml"
        taskobj = com_playbook.apply_async([extra_vars,playbook_path])
        user_task = User_Shell_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=hoststr,taskname=taskname,shell_cmd=extra_vars["shell_cmd"])
        user_task.save()
        if request.session.get("authmethod",None):
            return HttpResponse(taskobj.id)
        else:
            return redirect('/hd_mesos/tasklist/shell')

@csrf_exempt
@login_check
def script_list(request):
    if request.method == 'GET':
        scriptlist = ScriptInfo.objects.all()
        return render(request,"mesos/ansible/script/scriptlist.html" ,{"scriptlist":scriptlist})

@csrf_exempt
@login_check
def script_add(request):
    if request.method == 'GET':
        return render(request,"mesos/ansible/script/scriptadd.html")
    if request.method == 'POST':
        try:
            script_name = request.POST['ScriptName']
            script_describe = request.POST['ScriptDescribe']
            script_type = request.POST['ScriptType']
            script_file = ""
            if script_type == "1":
                script_file=os.path.join(SHELL_PATH,script_name+".sh")
            elif script_type == "2":
                script_file=os.path.join(PLAYBOOK_PATH,script_name+".yml")
            script_content = request.POST['Script'].replace("\r\n","\n")
            scriptinfo = ScriptInfo(name=script_name,type=script_type,describe=script_describe)
            with open(script_file, 'w') as f:
                f.write(script_content)
        except Exception as e:
            return HttpResponse(e.message)
        scriptinfo.save()
        if request.session.get('authmethod',None):
            return HttpResponse('Success')
        else:
            return redirect("/hd_ansible/script/list")
    
@csrf_exempt
@login_check
def script_edit(request,**kargs):
    scriptinfo = ScriptInfo.objects.get(name=kargs["scriptname"])
    script_file = ""
    try:
        if scriptinfo.type == 1:
            script_file=os.path.join(SHELL_PATH,scriptinfo.name+".sh")
        elif scriptinfo.type == 2:
            script_file=os.path.join(PLAYBOOK_PATH,scriptinfo.name+".yml")
        with open(script_file, 'r') as f:
            script = f.readlines()
    except Exception as e:
        return HttpResponse(e.message)
    return render(request,"mesos/ansible/script/scriptedit.html",{"scriptinfo":scriptinfo,"script":script})

@csrf_exempt
@login_check
def script_del(request):
    if request.method == 'POST':
        scriptname = request.POST["Name"]
        scriptinfo = ScriptInfo.objects.get(name=scriptname)
        if scriptinfo.type == 1:
            script_file=os.path.join(SHELL_PATH,scriptinfo.name+".sh")
        elif scriptinfo.type == 2:
            script_file=os.path.join(PLAYBOOK_PATH,scriptinfo.name+".yml")
        os.remove(script_file)
        scriptinfo.delete()
        return HttpResponse('Success')
    
@csrf_exempt
@login_check
def script_exec(request,**kargs):
    if request.method == 'GET':
        grouplist = HostGroup.objects.all()
        return render(request,"mesos/ansible/script/scriptexec.html",{"grouplist":grouplist,"scriptname":kargs["scriptname"]})
    if request.method == 'POST':
        hosts = request.POST.getlist('host_assets')
        if 'all' in hosts:
            hosts.remove("all")
        hoststr = ":".join(hosts)
        extra_vars = {}
        extra_vars["hosts"] = hoststr
        script_name = request.POST["Name"]
        scriptinfo = ScriptInfo.objects.get(name=script_name)
        if scriptinfo.type == 1:
            extra_vars["script_file"]=scriptinfo.name+".sh"
            extra_vars["script_path"]=os.path.join(SHELL_PATH,extra_vars["script_file"])
            playbook_path = "/opt/ansible/script/execute.yml"
        elif scriptinfo.type == 2: 
            playbook_path = os.path.join(PLAYBOOK_PATH,scriptinfo.name+".yml")
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        taskobj = com_playbook.apply_async([extra_vars,playbook_path])
        user_task = User_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=hoststr,taskname=script_name)
        user_task.save()
        if request.session.get('authmethod', None):
            return HttpResponse(taskobj.id)
        else:
            return redirect('/hd_mesos/tasklist/others')

@csrf_exempt
@login_check
def roles_api(request,taskid=""):
    if request.method == 'POST':
        extra_vars = json.loads(request.body)
        playbook_path = "/opt/ansible/execute.yml"
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        taskobj = com_playbook.apply_async([extra_vars,playbook_path])
        user_task = User_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=extra_vars["hosts"],taskname=extra_vars["roles"])
        user_task.save()
        return HttpResponse(taskobj.id)
    if request.method == 'GET':
        try:
            task_result = TaskResult.objects.get(task_id=taskid)
            return HttpResponse(json.dumps(task_result.result))
        except TaskResult.DoesNotExist:
            return HttpResponse("Pendding")

@csrf_exempt
@login_check
def multi_select(request):  
    if request.method == 'POST':
        received_data = json.loads(request.body)
        if received_data["MyColums"] == 'ProName':
            data = ProNameitems
        elif received_data["MyColums"] == 'ProApp':
            data = []
            for item in ProAppitems:
                if item["Type"] == received_data["parentId"]:
                    data.append(item)
        else:
            data = []
            for item in ProVersionitems:
                if item["Type"] == received_data["parentId"]:
                    data.append(item)
    return HttpResponse(json.dumps(data), content_type='application/json')

def ansible_handle2(ymlfile,extra_vars):
    shellstr = "ansible-playbook "+ymlfile+" --extra-vars '"+json.dumps(extra_vars)+"'"
    return os.popen(shellstr).read().splitlines()

def extra_var_create(host,extra_vars,role,sidinfo,buffer_pool,lvsize):
    extra_vars["hosts"] = host.ip
    extra_vars["flag_fact"] = True
    extra_vars["role"] = role
    extra_vars["option"] = "configure.yml"
    extra_vars["port"] = sidinfo.port
    extra_vars["serverid"] = host.ip.split(".")[-1] + str(sidinfo.port)
    extra_vars["password"] = sidinfo.password
    extra_vars["sid"] = sidinfo.sidname
    extra_vars["buffer_pool"] = buffer_pool
    extra_vars["data_size"] = lvsize
    return extra_vars

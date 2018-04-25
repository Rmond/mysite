# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json,datetime,time,re,os
from django.shortcuts import render,redirect
from django.db.models import Q

from hd_mesos.views import login_check,user_role
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from hd_mesos.models import User_Task,HostInfo,Host_Group
from hd_ansible.models import SidInfo,MysqlAduit,OptionLog,Hostip_Port
from hd_ansible.tasks import db_dump,sid_update_task
from models import Custom_Schedule,Schedule_Info,Schedule_Res,Sql_Info
from django_celery_beat.models import CrontabSchedule,PeriodicTask
# Create your views here.

@login_check
def user_pri(request):
    if request.method == 'POST':#返回执行结果
        databases = request.POST['database']
        dtlist = databases.split(',')
        rmhost_list = request.POST['remote_host'].split(",")
        reslist = []
        for remote_host in rmhost_list:
            for database in dtlist:
                extra_vars = {}
                extra_vars["hosts"] = request.POST['HostIp']
                extra_vars["login_user"] = request.POST['login_user']
                extra_vars["login_pass"] = request.POST['login_pass']
                extra_vars["login_port"] = request.POST['login_port']
                extra_vars["login_host"] = request.POST['login_host']
                extra_vars["mysqluser"] = request.POST['user']+"@"+remote_host
                extra_vars["password"] = request.POST['password']
                extra_vars["database"] = database
                extra_vars["tables"] = request.POST['tables']
                if "all" in request.POST.getlist('privilege'):
                    extra_vars["privilege"] = "all"
                else:
                    privilege = ""
                    for i in request.POST.getlist('privilege'):
                        privilege += i+","
                    extra_vars["privilege"] = privilege[:-1]
                res = ansible_handle2("/opt/ansible/mysql/user_pri.yml",extra_vars)
                flag = res[-2]
                resmsg = "数据库用户授权失败"
                if "ok=1" in flag:
                    try:
                        mysqladuit = MysqlAduit.objects.get(mysqlhost=extra_vars["hosts"],mysqluser=extra_vars["mysqluser"],pri_database=extra_vars["database"],pri_table=extra_vars["tables"])
                        mysqladuit.username = request.session.get('is_login',None)
                        if not ("all" in request.POST.getlist('privilege') or "all" in mysqladuit.privilege):
                            for j in request.POST.getlist('privilege'):
                                if j not in mysqladuit.privilege:
                                    mysqladuit.privilege +=","+j
                    except MysqlAduit.DoesNotExist:
                        mysqladuit = MysqlAduit()
                        mysqladuit.username = request.session.get('is_login',None)
                        mysqladuit.mysqlhost = extra_vars["hosts"]
                        mysqladuit.mysqluser = extra_vars["mysqluser"]
                        mysqladuit.pri_database = extra_vars["database"]
                        mysqladuit.pri_table = extra_vars["tables"]
                        mysqladuit.privilege = extra_vars["privilege"]
                    mysqladuit.save()
                    optlog = OptionLog()
                    optlog.username = request.session.get('is_login',None)
                    optlog.option = "grant"
                    optlog.mysqlhost = extra_vars["hosts"]
                    optlog.mysqluser = extra_vars["mysqluser"]
                    optlog.pri_database = extra_vars["database"]
                    optlog.pri_table = extra_vars["tables"]
                    optlog.privilege = extra_vars["privilege"]
                    optlog.save()
                    resmsg = "数据库用户授权成功"
                reslist.extend(res)
                reslist.append(resmsg)
        return render(request,"mesos/hd_mysql/privilege_mge/userprires.html",{"reslist":reslist})
    return render(request,"mesos/hd_mysql/privilege_mge/userpri.html")

@csrf_exempt
@login_check
def pri_list(request):
    if request.method == 'GET':
        return render(request, "mesos/hd_mysql/privilege_mge/prilist.html")
    if request.method == 'POST':
        search = request.POST.get('search[value]')
        draw = int(request.POST.get('draw'))
        start = int(request.POST.get('start'))
        length = int(request.POST.get('length'))
        end = start+length
        mysqladuit_set = MysqlAduit.objects.all()
        if search != "":
            mysqladuit_set = mysqladuit_set.filter(Q(username__contains=search)|Q(mysqluser__contains=search)|Q(mysqlhost__contains=search)|Q(pridate__contains=search)|Q(pri_database__contains=search)|Q(pri_table__contains=search))
        assets_list = mysqladuit_set.values_list('username','mysqluser','mysqlhost','pridate','pri_database','pri_table','privilege').order_by('-pridate')[start:end]
        asset_count = mysqladuit_set.count()
        _filter = asset_count
        all_lists = map(lambda x:list(map(lambda y:y.strftime('%Y-%m-%d %H:%M') if isinstance(y,datetime.datetime) else y,x)),assets_list)
        data = {
            'draw':draw,
            'recordsTotal':asset_count,
            'recordsFiltered':_filter,
            'data':all_lists
        }
        return HttpResponse(json.dumps(data))

@csrf_exempt
@login_check
def user_revoke(request):
    if request.method == 'POST':#返回执行结果
        extra_vars = {}
        extra_vars["hosts"] = request.POST['mysqlhost']
        extra_vars["mysqluser"] = request.POST['mysqluser']
        extra_vars["database"] = request.POST['database']
        extra_vars["tables"] = request.POST['tables']
        extra_vars["login_host"] = request.POST['login_host']
        extra_vars["login_port"] = request.POST['login_port']
        extra_vars["login_user"] = request.POST['login_user']
        extra_vars["login_pass"] = request.POST['login_pass']
        res = ansible_handle2("/opt/ansible/mysql/user_revoke.yml",extra_vars)
        flag = res[-2]
        if "ok=1" in flag:
            if "*" in extra_vars["tables"]:
                MysqlAduit.objects.filter(mysqlhost=extra_vars["hosts"],mysqluser=extra_vars["mysqluser"],pri_database=extra_vars["database"]).delete()
            else:
                MysqlAduit.objects.filter(mysqlhost=extra_vars["hosts"],mysqluser=extra_vars["mysqluser"],pri_database=extra_vars["database"],pri_table=extra_vars["tables"]).delete()
            optlog = OptionLog()
            optlog.username = request.session.get('is_login',None)
            optlog.option = "revoke"
            optlog.mysqlhost = extra_vars["hosts"]
            optlog.mysqluser = extra_vars["mysqluser"]
            optlog.pri_database = extra_vars["database"]
            optlog.pri_table = extra_vars["tables"]
            optlog.privilege = "all"
            optlog.save()
            return HttpResponse("权限回收成功！")
        else:
            return HttpResponse(str(res)+"权限回收失败！")
    return render(request,"mesos/hd_mysql/privilege_mge/prilist.html")

@login_check
def optlog_list(request):
    optionlog = OptionLog.objects.all()
    return render(request,"mesos/hd_mysql/privilege_mge/optionlog.html",{"optionlog":optionlog})

@csrf_exempt
@login_check
def master_check(request):#判断数据库是否是主库
    if request.method == 'POST':
        HostIP = request.POST['HostIP']
        temp = 0
        for host_group in Host_Group.objects.filter(group_id=1):
            if HostIP in host_group.ip_id:
                temp = 1 
        return HttpResponse(temp)

@login_check
def sid_list(request,error=""):
    sidlist = SidInfo.objects.all()
    return render(request, "mesos/hd_mysql/sid_mge/sidlist.html", {"sidlist":sidlist,"error":error})

@csrf_exempt
@login_check
def sid_add(request):
    if request.method == 'POST':
        mextra_vars = {}
        sextra_vars = {}
        for i in HostInfo.objects.get(ip=request.POST["Mhostip"]).software.split(","):#获取主库mysql版本
            if "mysql" in i:
                master_mysql_version=i
        for j in HostInfo.objects.get(ip=request.POST["Shostip"]).software.split(","):#获取从库mysql版本
            if "mysql" in j:
                slave_mysql_version=j
        mhost = HostInfo.objects.get(ip=request.POST["Mhostip"])
        shost = HostInfo.objects.get(ip=request.POST["Shostip"])
        if master_mysql_version == slave_mysql_version:#比较版本信息            
            if "mysql-5.6" in master_mysql_version:
                initshell = "/usr/local/mysql/scripts/mysql_install_db"
            elif "mysql-5.7" in master_mysql_version:
                initshell = "/usr/local/mysql/bin/mysqld --initialize-insecure"
            mport = Hostip_Port.objects.get(hostip=request.POST["Mhostip"]).port
            sport = Hostip_Port.objects.get(hostip=request.POST["Shostip"]).port
            mhostip_end = request.POST["Mhostip"].split(".")[-1].zfill(3) 
            shostip_end = request.POST["Shostip"].split(".")[-1].zfill(3)
            mextra_vars["sid"] = request.POST["AppName"]+"_M_"+mhostip_end+str(mport)
            mextra_vars["hosts"] = request.POST["Mhostip"]
            mextra_vars["flag_fact"] = True
            mextra_vars["role"] = "mysql_M_instance"
            mextra_vars["option"] = "install.yml"
            mextra_vars["port"] = mport
            mextra_vars["sid_init"] = initshell+" --datadir=/mysql_data/"+mextra_vars["sid"]+"/data"
            mextra_vars["serverid"] = request.POST["Mhostip"].split(".")[-1]+str(mport)
            mextra_vars["password"] = make_password(time.time())[-20:]
            mextra_vars["repluser"] = "repl@"+request.POST["Shostip"]
            mextra_vars["replpassword"] = make_password(time.time())[-20:]
            mextra_vars["data_size"] = request.POST["LvSize"]
            mextra_vars["buffer_pool"] = request.POST["Bf_Pool"]
            sextra_vars["sid"] = request.POST["AppName"]+"_S_"+shostip_end+str(sport)
            sextra_vars["hosts"] = request.POST["Shostip"]
            sextra_vars["flag_fact"] = True
            sextra_vars["role"] = "mysql_S_instance"
            sextra_vars["option"] = "install.yml"
            sextra_vars["port"] = sport
            sextra_vars["sid_init"] = initshell+" --datadir=/mysql_data/"+sextra_vars["sid"]+"/data"
            sextra_vars["serverid"] = request.POST["Shostip"].split(".")[-1]+str(sport)
            sextra_vars["password"] = mextra_vars["password"]
            sextra_vars["replpassword"] = mextra_vars["replpassword"]
            sextra_vars["masterhost"] = mextra_vars["hosts"]
            sextra_vars["masterport"] = mextra_vars["port"]
            sextra_vars["data_size"] = request.POST["LvSize"]
            sextra_vars["buffer_pool"] = request.POST["Bf_Pool"]
            startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            username = request.session.get("username",None)
            taskobj = sid_init.apply_async([mextra_vars,sextra_vars])
            mhost.idle = False
            shost.idle = False
            mhost.save()
            shost.save()
            user_task = User_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=request.POST["Mhostip"]+":"+request.POST["Shostip"],taskname="repl_create")
            user_task.save()
            return redirect('/hd_mesos/tasklist.html')
        else:
            return render(request,"mesos/hd_mysql/sid_mge/sidlist.html",{"error":"实例创建失败，主从版本不一致！"})

@csrf_exempt
@login_check
def sid_del(request):
    if request.method == 'POST':
        appname = request.POST["AppName"]
        sidinfo_set = SidInfo.objects.filter(appname=appname)
        for sidinfo in sidinfo_set:
            hostinfo = HostInfo.objects.get(ip=sidinfo.hostip)
            hostinfo.memory_free = hostinfo.memory_free+sidinfo.buffer_pool*1024
            hostinfo.memory_used = hostinfo.memory_used-sidinfo.buffer_pool*1024
            update_info.apply_async([sidinfo.hostip])
            hostinfo.save()
        sidinfo_set.delete()
        return HttpResponse("实例信息仅在数据库中删除，具体删除操作请到对应主机完成！")

@csrf_exempt
@login_check
def sid_update(request):
    if request.method == 'POST':
        mextra_vars = {}
        sextra_vars = {}
        appname = request.POST['Up_AppName']
        lvsize = request.POST['Up_LvSize']
        buffer_pool = request.POST['Up_Bf_Pool']
        sidinfo_set = SidInfo.objects.filter(appname=appname)
        for sidinfo in sidinfo_set:
            host = HostInfo.objects.get(ip=sidinfo.hostip)
            host.idle=False
            host.save()
            if 'M' in sidinfo.sidname.replace(sidinfo.appname,""):
                mextra_vars=extra_var_create(host, mextra_vars, "mysql_M_instance", sidinfo, buffer_pool, lvsize)
            else:
                sextra_vars=extra_var_create(host, sextra_vars, "mysql_S_instance", sidinfo, buffer_pool, lvsize)
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        taskobj = sid_update_task.apply_async([mextra_vars,sextra_vars])
        user_task = User_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=mextra_vars["hosts"]+":"+sextra_vars["hosts"],taskname="sid_update")
        user_task.save()
        return redirect('/hd_mesos/tasklist.html')

@csrf_exempt
@login_check
def hostip_ajaxget(request):
    mhostip = []
    shostip = []
    for host_group in Host_Group.objects.filter(group_id=1):
        if "mysql" in HostInfo.objects.get(ip=host_group.ip_id).software:
            mhostip.append(host_group.ip_id)
    for host_group in Host_Group.objects.filter(group_id=2):
        if "mysql" in HostInfo.objects.get(ip=host_group.ip_id).software:
            shostip.append(host_group.ip_id)   
    return HttpResponse(json.dumps({"mhostip":mhostip,"shostip":shostip}))

@csrf_exempt
@login_check
def hostinfo_get(request):
    if request.method == 'POST':
        hostip = request.POST['HostIP']
        hostinfo = HostInfo.objects.get(ip=hostip)
        memory_free =  hostinfo.memory_free
        memory_per = round(float(memory_free)/hostinfo.memory_total*100)
        vginfo_dic = json.loads(hostinfo.vginfo)
        vginfo_per = round(float(vginfo_dic["datavg"]["free_g"])/float(vginfo_dic["datavg"]["size_g"])*100)
        vginfo_free = vginfo_dic["datavg"]["free_g"]
        return HttpResponse(json.dumps({"memory_per":memory_per,"vginfo_per":vginfo_per,"vginfo_free":vginfo_free}))

@csrf_exempt
@login_check
def sidinfo_get(request):
    sidinfo = SidInfo.objects.get(sidname=request.POST['Sidname'])
    return HttpResponse(json.dumps({"sidname":sidinfo.sidname, "hostip":sidinfo.hostip,"size":sidinfo.data_size, "buffer_pool":sidinfo.buffer_pool,"socket":sidinfo.socketpath, "port":sidinfo.port, "root":sidinfo.password, "repl":sidinfo.replpassword}))

@csrf_exempt
@login_check
def appinfo_get(request):
    if request.method == 'POST':
        appname = request.POST['AppName']
        sidinfo_set = SidInfo.objects.filter(appname=appname)
        hostinfo_list=[]
        for sidinfo in sidinfo_set:
            hostinfo_dic={}
            hostinfo = HostInfo.objects.get(ip=sidinfo.hostip)
            hostinfo_dic["hostip"] = sidinfo.hostip
            hostinfo_dic["memory_per"] = round(float(hostinfo.memory_free)/hostinfo.memory_total*100)
            vginfo_dic = json.loads(hostinfo.vginfo)
            hostinfo_dic["vginfo_per"] = round(float(vginfo_dic["datavg"]["free_g"])/float(vginfo_dic["datavg"]["size_g"])*100)
            hostinfo_dic["vginfo_free"] = vginfo_dic["datavg"]["free_g"]
            hostinfo_dic["datasize"] = sidinfo.data_size
            hostinfo_dic["bufferpool"] = sidinfo.buffer_pool
            hostinfo_list.append(hostinfo_dic)
        return HttpResponse(json.dumps(hostinfo_list))

@csrf_exempt
@login_check
def vginfo_check(request):
    if request.method == 'POST':
        if request.POST['Mhostip'] and request.POST['Shostip']:
            lv_size = request.POST['LvSize']
            mhostip = request.POST['Mhostip']
            shostip = request.POST['Shostip']
            mhostinfo = HostInfo.objects.get(ip=mhostip)
            shostinfo = HostInfo.objects.get(ip=shostip)
            mdatavg_free = json.loads(mhostinfo.vginfo)["datavg"]["free_g"]
            sdatavg_free = json.loads(shostinfo.vginfo)["datavg"]["free_g"]
            if float(lv_size) > float(mdatavg_free) or float(lv_size) > float(sdatavg_free):
                return HttpResponse(0)
            else:
                return HttpResponse(1)
        else:
            return HttpResponse(0)

@csrf_exempt
@login_check
def memory_check(request):
    if request.method == 'POST':
        if request.POST['Mhostip'] and request.POST['Shostip']:
            buffer_pool = request.POST['BufferPool']
            mhostip = request.POST['Mhostip']
            shostip = request.POST['Shostip']
            mhostinfo = HostInfo.objects.get(ip=mhostip)
            shostinfo = HostInfo.objects.get(ip=shostip)
            if (mhostinfo.memory_free-float(buffer_pool)*1024)/mhostinfo.memory_total < 0.4 or (shostinfo.memory_free-float(buffer_pool)*1024)/shostinfo.memory_total < 0.4:
                return HttpResponse(0)
            else:
                return HttpResponse(1)
        else:
            return HttpResponse(0)

@csrf_exempt
@login_check
def appname_check(request):
    if request.method == 'POST':
        appname = request.POST['AppName']
        if SidInfo.objects.filter(appname=appname):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def up_vginfo_check(request):
    if request.method == 'POST':
        lv_size = request.POST['LvSize']
        mhostip = request.POST['Mhostip']
        shostip = request.POST['Shostip']
        appname = request.POST['AppName']
        msidinfo = SidInfo.objects.get(appname=appname,hostip=mhostip)
        ssidinfo = SidInfo.objects.get(appname=appname,hostip=shostip)
        mhostinfo = HostInfo.objects.get(ip=mhostip)
        shostinfo = HostInfo.objects.get(ip=shostip)
        mdatavg_free = json.loads(mhostinfo.vginfo)["datavg"]["free_g"]
        sdatavg_free = json.loads(shostinfo.vginfo)["datavg"]["free_g"]
        if float(lv_size) > float(mdatavg_free)+int(msidinfo.data_size) or float(lv_size) > float(sdatavg_free)+float(ssidinfo.data_size):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def up_memory_check(request):
    if request.method == 'POST':
        buffer_pool = request.POST['BufferPool']
        mhostip = request.POST['Mhostip']
        shostip = request.POST['Shostip']
        appname = request.POST['AppName']
        msidinfo = SidInfo.objects.get(appname=appname,hostip=mhostip)
        ssidinfo = SidInfo.objects.get(appname=appname,hostip=shostip)
        mhostinfo = HostInfo.objects.get(ip=mhostip)
        shostinfo = HostInfo.objects.get(ip=shostip)
        if (mhostinfo.memory_free+(msidinfo.buffer_pool-float(buffer_pool))*1024)/mhostinfo.memory_total < 0.4 or (shostinfo.memory_free+(ssidinfo.buffer_pool-float(buffer_pool))*1024)/shostinfo.memory_total < 0.4:
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def up_hostidle_check(request):
    if request.method == 'POST':
        appname = request.POST['AppName']
        hostip_list = SidInfo.objects.filter(appname=appname).values_list("hostip")
        for i in hostip_list:           
            hostinfo  = HostInfo.objects.get(ip="".join(i))
            if not hostinfo.idle:
                return HttpResponse(0)
        return HttpResponse(1)

@login_check
def mysql_dump(request):
    if request.method == 'GET':
        return render(request,"mesos/hd_mysql/backup_mge/mysql-dump.html")
    elif request.method == 'POST':
        extra_vars = mysql_extra_vars(request)
        extra_vars["login_host"] = request.POST['login_host']
        startime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        username = request.session.get("username",None)
        taskobj = db_dump.apply_async([extra_vars])
        user_task = User_Task(username_id = username,star_time = startime,taskid=taskobj.id,hosts=extra_vars["hosts"],taskname="mysql_dump")
        user_task.save()
        return redirect('/hd_mesos/tasklist.html') 
    
@login_check
def schedule_list(request):
    shd_info_set = Schedule_Info.objects.all()
    return render(request,"mesos/hd_mysql/backup_mge/schedulelist.html",{"shd_info_set":shd_info_set})

@csrf_exempt
@login_check
def schedule_enable(request):
    period_tk = PeriodicTask.objects.get(name = request.POST['bk_shd_name'])
    period_tk.enabled = not period_tk.enabled
    period_tk.save()
    return HttpResponse(period_tk.enabled)

@csrf_exempt
@login_check
def schedule_del(request):
    PeriodicTask.objects.filter(name = request.POST['bk_shd_name']).delete()
    return HttpResponse()

@csrf_exempt
@login_check
def schedule_edit(request):
    if request.method == 'POST':
        ct_shd = Custom_Schedule.objects.get(id=request.POST['u_BK_HZ'])
        if request.POST['u_BK_Min']:
            minute = request.POST['u_BK_Min']
        else:
            minute = "0"
        schedule,_ = CrontabSchedule.objects.get_or_create(minute=minute,hour=request.POST['u_BK_Hour'],day_of_week=ct_shd.sd_num)
        period_tk = PeriodicTask.objects.get(name=request.POST['bk_shd_name'])
        period_tk.crontab=schedule
        period_tk.save()
        schedule_info = Schedule_Info.objects.get(mysql_bk_name=request.POST['bk_shd_name'])
        schedule_info.ct_shd_id=request.POST['u_BK_HZ']
        schedule_info.hour_minute=request.POST['u_BK_Hour']+":"+minute.zfill(2)
        schedule_info.save()
        return redirect("/hd_mysql/schedulelist")

@login_check
def schedule_res(request,id=None):
    if not id:
        shd_res_set = Schedule_Res.objects.filter(stop_time__gte=(datetime.datetime.now()+datetime.timedelta(days=-3)))
        return render(request,"mesos/hd_mysql/backup_mge/shdreslist.html",{"shd_res_set":shd_res_set})
    else:
        shd_res = Schedule_Res.objects.get(id=id)
        result = shd_res.result.replace("[","").replace("]","").replace("\'","").split(",")
        return render(request,"mesos/hd_mysql/backup_mge/scheduleres.html",{"shd_res":shd_res,"result":result})

@csrf_exempt
@login_check
def bk_hz_ajaxget(request):
    ct_shd_set = Custom_Schedule.objects.all()
    ct_shd_dic = {}
    for ct_shd in ct_shd_set:
        ct_shd_dic[ct_shd.id] = ct_shd.sd_name
    return HttpResponse(json.dumps(ct_shd_dic))

@csrf_exempt
@login_check
def schedule_info_add(request):
    if request.method == 'POST':
        extra_vars=mysql_extra_vars(request)
        extra_vars["login_host"] = "127.0.0.1"
        ct_shd = Custom_Schedule.objects.get(id=request.POST['BK_HZ'])
        if request.POST['BK_Min']:
            minute = request.POST['BK_Min']
        else:
            minute = "0"
        schedule,_ = CrontabSchedule.objects.get_or_create(minute=minute,hour=request.POST['BK_Hour'],day_of_week=ct_shd.sd_num)
        period_tk = PeriodicTask.objects.create(crontab=schedule,name=request.POST['bk_shd_name'],task="hd_ansible.tasks.db_dump",args=json.dumps([extra_vars,True,request.POST['bk_shd_name']]))
        schedule_info = Schedule_Info(hostip=extra_vars["hosts"],ct_shd_id=request.POST['BK_HZ'],hour_minute=request.POST['BK_Hour']+":"+minute.zfill(2),period_tk_id=period_tk.id,bk_database=extra_vars["database"],bk_table=extra_vars["table"],mysql_bk_name=request.POST['bk_shd_name'])
        schedule_info.save()
        return redirect('/hd_mysql/schedulelist')

@csrf_exempt
@login_check
def bk_shd_name_chk(request):#检查备份计划是否存在
    if request.method == 'POST':
        bk_shd_name = request.POST['bk_shd_name']
        if Schedule_Info.objects.filter(mysql_bk_name=bk_shd_name):
            return HttpResponse(0)
        else:
            return HttpResponse(1)

@csrf_exempt
@login_check
def sql_list(request):
    sqlinfo_set = Sql_Info.objects.all()
    return render(request,"mesos/hd_mysql/sql_mge/sqllist.html",{"sqlinfo_set":sqlinfo_set})

@csrf_exempt
@login_check
def sql_add(request,**kargs):
    if request.method == 'POST':
        id = request.POST["Id"]
        sql_name = request.POST["SqlName"]
        sql_handle = request.POST["SqlHandle"]
        arg_count = len(re.findall(r'(?={\d+})',sql_handle))
        if id:
            sqlinfo=Sql_Info.objects.get(id=id)
            sqlinfo.sql_name = sql_name
            sqlinfo.sql_handle = sql_handle
            sqlinfo.arg_count = arg_count
        else:
            sqlinfo = Sql_Info(sql_name=sql_name,sql_handle=sql_handle,arg_count=arg_count)
        sqlinfo.save()
        return redirect("/hd_mysql/sqllist")
    elif request.method == 'GET':
        if "id" in kargs.keys():
            sqlinfo = Sql_Info.objects.get(id=kargs["id"])
            return render(request,"mesos/hd_mysql/sql_mge/sqladd.html",{"sqlinfo":sqlinfo})
        else:
            return render(request,"mesos/hd_mysql/sql_mge/sqladd.html")
    
@csrf_exempt
@login_check
def sql_del(request):
    if request.method == 'POST':
        id = request.POST["Id"]
        Sql_Info.objects.filter(id=id).delete()
        return HttpResponse()

@csrf_exempt
@login_check
def sql_exec(request):
    if request.method == 'POST':
        sqlname = request.POST["SqlName"]
        hostip = request.POST["HostIP"]
        login_port = request.POST["Login_port"]
        login_user = request.POST["Login_user"]
        login_pass = request.POST["Login_pass"]
        sqlinfo = Sql_Info.objects.get(sql_name=sqlname)
        sql_handle_list = re.split("\{\d+\}",sqlinfo.sql_handle)
        sql_handle=sql_handle_list[0]
        for i in range(sqlinfo.arg_count):
            sql_handle = sql_handle+request.POST["arg"+str(i)]+sql_handle_list[i+1]
        model_str = " -m shell -a \"source /etc/profile&&mysql -h127.0.0.1 -u"+login_user+" -p"+login_pass+" -P"+login_port+" -e '"+sql_handle+"'\""
        cmd_res = ansible_cmd(hostip,model_str)
        return HttpResponse(json.dumps(cmd_res))
    elif request.method == 'GET':
        return render(request,"mesos/hd_mysql/sql_mge/sqlexec.html")

@csrf_exempt
@login_check
def sqlname_get(request):
    if request.method == 'POST':
        sql_input = request.POST["sql_input"]
        sqlname_list = list(Sql_Info.objects.filter(sql_name__icontains=sql_input).values_list('sql_name', flat=True))
        return HttpResponse(json.dumps(sqlname_list))

@csrf_exempt
@login_check
def sqlname_check(request):
    if request.method == 'POST':
        sql_name = request.POST["sqlname"]
        if Sql_Info.objects.filter(sql_name=sql_name):
            return HttpResponse(1)
        else:
            return HttpResponse(0)

@csrf_exempt
@login_check
def argcount_get(request):
    if request.method == 'POST':
        sql_name = request.POST["sqlname"]
        try:
            argcount = Sql_Info.objects.get(sql_name = sql_name).arg_count
        except Sql_Info.DoesNotExist:
            argcount = 0
        return HttpResponse(argcount)

@csrf_exempt
@login_check
def sql_import(request):
    if request.method == "POST":
        f = request.FILES.get('xlsname')
        filename = os.path.join("/tmp/",f.name)
        with open(filename,'wb') as fobj:
            for chunck in f.chunks():
                fobj.write(chunck)
        xlsfile = xlrd.open_workbook(filename)#打开文件
        xlstable = xlsfile.sheet_by_index(0)#定位到第一张表
        rowscount = xlstable.nrows#获取行数
        for num in range(1,rowscount):
            sql_name = xlstable.row_values(num)[0]
            sql_handle = xlstable.row_values(num)[1]
            arg_count = len(re.findall(r'(?={\d+})',sql_handle))
            try:
                sqlinfo = Sql_Info.objects.get(sql_name=sql_name)
                sqlinfo.sql_handle = sql_handle
                sqlinfo.arg_count = arg_count
            except Sql_Info.DoesNotExist:
                sqlinfo = Sql_Info(sql_name=sql_name,sql_handle = sql_handle,arg_count = arg_count)
            sqlinfo.save()
        return redirect('/hd_mysql/sqllist')

def mysql_extra_vars(request):
    extra_vars = {}
    extra_vars["hosts"] = request.POST['HostIP' ]
    extra_vars["login_user"] = request.POST['login_user' ]
    extra_vars["login_pass"] = request.POST['login_pass' ]
    extra_vars["login_port"] = request.POST['login_port' ]
    extra_vars["path"] = request.POST['bk_path' ]
    extra_vars["database"] = request.POST['bk_database' ]
    extra_vars["table"] = request.POST['bk_table' ]
    if not request.POST['bk_table' ]:
        extra_vars["createDB"] = "-B"
    return extra_vars

def ansible_cmd(hostip,model_str):
    shellstr = "ansible "+hostip+model_str
    #return shellstr
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

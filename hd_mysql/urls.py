#!/usr/local/bin/python2.7
# encoding: utf-8

from django.conf.urls import url

import views


urlpatterns = [
    url(r'^userpri',views.user_pri,name="user_pri"),
    url(r'^prilist',views.pri_list,name="pri_list"),
    url(r'^prirevoke',views.user_revoke),
    url(r'^optlog',views.optlog_list,name="optlog_list"),
    url(r'^mastercheck',views.master_check,name="master_check"),
    url(r'^sidlist$',views.sid_list,name="sid_list"),
    url(r'^sidlist/(?P<error>.+)',views.sid_list,name="sid_list"),
    url(r'^sidadd',views.sid_add,name="sid_add"),
    url(r'^siddel',views.sid_del,name="sid_del"),
    url(r'^sidupdate',views.sid_update,name="sid_update"),
    url(r'^hostipajaxget',views.hostip_ajaxget,name="hostip_ajaxget"),
    url(r'^hostinfoget',views.hostinfo_get,name="hostinfo_get"),
    url(r'^sidinfoget',views.sidinfo_get,name="sidinfo_get"),
    url(r'^appinfoget',views.appinfo_get,name="appinfo_get"),
    url(r'^vginfocheck',views.vginfo_check,name="vginfo_check"),
    url(r'^memorycheck',views.memory_check,name="memory_check"),
    url(r'^appnamecheck',views.appname_check,name="appname_check"),
    url(r'^upvginfocheck',views.up_vginfo_check,name="up_vginfo_check"),
    url(r'^upmemorycheck',views.up_memory_check,name="up_memory_check"),
    url(r'^uphostidlechk',views.up_hostidle_check,name="up_hostidle_check"),
    url(r'^sqllist$',views.sql_list,name="sql_list"),
    url(r'^sqladd$',views.sql_add,name="sql_add"),
    url(r'^sqledit/(?P<id>\d+)',views.sql_add,name="sql_edit"),
    url(r'^sqldel$',views.sql_del,name="sql_del"),
    url(r'^sqlexec$',views.sql_exec,name="sql_exec"),
    url(r'^sqlexecres$',views.sql_exec,name="sql_exec_res"),
    url(r'^sqlnameget$',views.sqlname_get,name="sqlname_get"),
    url(r'^sqlnamecheck$',views.sqlname_check,name="sqlname_check"),
    url(r'^argcountget$',views.argcount_get,name="argcount_get"),
    url(r'^mysqldump$',views.mysql_dump),
    url(r'^schedulelist$',views.schedule_list),
    url(r'^bkhzajaxget$',views.bk_hz_ajaxget),
    url(r'^shdadd$',views.schedule_info_add),
    url(r'^shdenable$',views.schedule_enable),
    url(r'^shddel$',views.schedule_del),
    url(r'^shdedit$',views.schedule_edit),
    url(r'^scheduleres$',views.schedule_res),
    url(r'^scheduleres/(?P<id>[\d]+)/',views.schedule_res),
    url(r'^bkshdnamechk$',views.bk_shd_name_chk),
]

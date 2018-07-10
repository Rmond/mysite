#!/usr/local/bin/python2.7
# encoding: utf-8

from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$',views.login),
    url(r'^login',views.login),
    url(r'^index',views.index),
    url(r'^logout$',views.logout),
    url(r'^userlist',views.user_list),
    url(r'^useradd',views.user_add),
    url(r'^pwdreset',views.pwd_reset),
    url(r'^userdel',views.user_del),
    url(r'^userlook',views.user_look),
    url(r'^userinfo',views.user_info),
    url(r'^useredit',views.user_edit),
    url(r'usernamechk',views.username_check),
    url(r'^hostlist$',views.host_list),
    url(r'^hostdel$',views.host_del),
    url(r'^hostadd$',views.host_add),
    url(r'^hostedit$',views.host_edit),
    url(r'^hostlistdel',views.hostlist_del), 
    url(r'^hostlook/(?P<hostip>[\d|.]+)/',views.host_look),
    url(r'^hostupdate$',views.host_update),
    url(r'^hostajaxget',views.host_ajaxget),
    url(r'^grouptagajaxget',views.group_tag_ajaxget),
    url(r'^hostgroups',views.hostgroups),
    url(r'^groupadd',views.group_add),
    url(r'^grouplook',views.group_look),
    url(r'^groupdel',views.group_del),
    url(r'^hostgrpcheck',views.hostgrp_check),
    url(r'^privilegelist',views.privilege_list),
    url(r'^privilegelook',views.privilege_look),
    url(r'^privilegedit',views.privileg_edit),
    url(r'^tasklist$',views.task_list),
    url(r'^tasklist/(?P<option>\w+)',views.task_list),
    url(r'^taskinfo/(?P<option>\w+)/(?P<taskid>\d+)/',views.task_info),
    url(r'^taskack$',views.task_ack),
    url(r'^hostimp',views.host_import),
    url(r'^taskchart',views.task_chart),
    url(r'^assets_list',views.asserts_list),
]

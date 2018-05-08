#!/usr/local/bin/python2.7
# encoding: utf-8

from django.conf.urls import url

import views
from software import softview


urlpatterns = [
    url(r'^tomcat/projectdev',views.project_dev,name="project_dev"),
    url(r'^tomcat/rollback',views.rollback),
    url(r'^tomcat/grouphostget',views.grouphost_get),
    url(r'^tomcat/multiselect',views.multi_select),
    url(r'^tomcat/uploadfile',views.upload_file),
    url(r'^inventory/inventorymge',views.inventory_mge),
    url(r'^software/softselect$',softview.software_select),
    url(r'^software/install$',softview.software_install),
    url(r'^software/update$',softview.software_update),
    url(r'^software/installed$',softview.software_installed),
    url(r'^software/updated$',softview.software_updated),
    url(r'^software/grouphostget',softview.grouphost_get),
    url(r'^software/ugrouphostget',softview.u_grouphost_get),
    url(r'^yum/manage/(?P<option>\w+)$',views.yum_manage,),
    url(r'^yum/execute/(?P<option>\w+)$',views.yum_execute),
    url(r'^command/exec$',views.command_exec,name="script_exec"),
    url(r'^script/list$',views.script_list,name="script_list"),
    url(r'^script/add$',views.script_add,name="script_add"),
    url(r'^script/edit/(?P<scriptname>\w+)$',views.script_edit,name="script_edit"),
    url(r'^script/exec/(?P<scriptname>\w+)$',views.script_exec,name="script_exec"),
    url(r'^script/exec$',views.script_exec),
    url(r'^script/del$',views.script_del),
    url(r'^rolesapi$',views.roles_api),
    url(r'^rolesapi/(?P<taskid>[\w|-]+)$',views.roles_api),
]

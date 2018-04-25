# -*- coding: UTF-8 -*-

import commands

def GetProList(parentId):
    commandstr = 'ls /opt/war_manage/'
    data = []
    if "scm" in parentId:
        if "scm" == parentId:
          commandstr += parentId
        else:
          commandstr += 'scm/'+parentId
    elif "oms" in parentId:
        if "oms" == parentId:
          commandstr += parentId
        else:
          commandstr += 'oms/'+parentId
    elif "wms" in parentId:
        if "wms" == parentId:
          commandstr += parentId
        else:
          commandstr += 'wms/'+parentId
    elif "bi" in parentId:
        if "bi" == parentId:
          commandstr += parentId
        else:
          commandstr += 'bi/'+parentId
    elif "hnb" in parentId:
        if "hnb" == parentId:
          commandstr += parentId
        else:
          commandstr += 'hnb/'+parentId
    elif "hr" in parentId:
        if "hr" == parentId:
          commandstr += parentId
        else:
          commandstr += 'hr/'+parentId
    (status,output) = commands.getstatusoutput(commandstr)
#    (status,output) = commands.getstatusoutput('ls /opt/war_manage/scm/scm-web')
    if status == 0:
        prolist = output.split('\n')
        for item in prolist:
            tempdict = {}
            tempdict['Id'] = item
            tempdict['Name'] = item.upper()
            tempdict['Type'] = parentId
            data.append(tempdict)
    return data

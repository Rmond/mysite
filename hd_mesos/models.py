from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

# Create your models here.
from mysite import settings


class HostInfo(models.Model):
    hostname=models.CharField(max_length=32)
    ip=models.CharField(max_length=16,primary_key=True)
    software = models.CharField(max_length=128,default="")
    tags = models.CharField(max_length=64,default="")
    idle = models.BooleanField(default=True)
    vginfo = models.TextField(null=True)
    memory_total = models.IntegerField(default=0)
    memory_used = models.IntegerField(default=0)
    memory_free = models.IntegerField(default=0)

class Users(AbstractBaseUser):
    username = models.CharField(max_length=32,primary_key=True,unique=True)
    nickname = models.CharField(max_length=16)
    password = models.CharField(max_length=128)
    role = models.PositiveSmallIntegerField(default=1)
    USERNAME_FIELD = 'username'


class HostGroup(models.Model):
    id = models.AutoField(primary_key=True)
    groupname = models.CharField(max_length=32,unique=True)
    
class Host_Group(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.ForeignKey(HostInfo)
    group = models.ForeignKey(HostGroup)
    
class User_Host(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(settings.AUTH_USER_MODEL)
    ip = models.ForeignKey(HostInfo)

class User_Hostgroup(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(settings.AUTH_USER_MODEL)
    group = models.ForeignKey(HostGroup)
    
class User_Task(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(settings.AUTH_USER_MODEL)
    taskid = models.CharField(max_length=48,default="")
    taskname = models.CharField(max_length=32,default="")
    acked = models.BooleanField(default=False)
    star_time=models.DateTimeField()
    hosts=models.TextField()
    status=models.CharField(max_length=50,default="Running")
    result=models.TextField(null=True)
    date_done=models.DateTimeField(null=True)
    
class User_Shell_Task(User_Task):
    shell_cmd = models.CharField(max_length=128)
    
class User_Yum_Task(User_Task):
    soft_list = models.TextField(null=True)
    

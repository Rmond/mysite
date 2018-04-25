from __future__ import unicode_literals

from django.db import models

# Create your models here.
class MysqlAduit(models.Model):
    username=models.CharField(max_length=32)
    mysqluser=models.CharField(max_length=64)
    mysqlhost=models.CharField(max_length=16,default="")
    login_host = models.CharField(max_length=16,default="localhost")
    pridate=models.DateTimeField(auto_now=True)
    pri_database = models.CharField(max_length=32,default="")
    pri_table = models.CharField(max_length=32,default="")
    privilege=models.CharField(max_length=64,default="")
    
class OptionLog(models.Model):
    username=models.CharField(max_length=32)
    option = models.CharField(max_length=10)
    mysqlhost=models.CharField(max_length=16)
    mysqluser=models.CharField(max_length=64)
    pridate=models.DateTimeField(auto_now_add=True)
    pri_database = models.CharField(max_length=32,default="")
    pri_table = models.CharField(max_length=32,default="")
    privilege = models.CharField(max_length=48)
    
class SidInfo(models.Model):
    appname = models.CharField(max_length=32)
    sidname=models.CharField(max_length=32)
    hostip=models.CharField(max_length=16)
    socketpath=models.CharField(max_length=64)
    port=models.IntegerField()
    data_size=models.CharField(max_length=6)
    buffer_pool=models.IntegerField()
    password=models.CharField(max_length=128)
    replpassword=models.CharField(max_length=128)
    
class Software(models.Model):
    softname=models.CharField(max_length=16)
    version=models.TextField(default="")
    
class Hostip_Port(models.Model):
    hostip = models.CharField(max_length=16)
    port = models.IntegerField(default=3306)
    
class ScriptInfo(models.Model):
    SCRIPT_TYPE=(
       (1,"shell"),
       (2,"palybook"),             
    )
    name = models.CharField(max_length=16,primary_key=True)
    type = models.IntegerField(choices=SCRIPT_TYPE)
    describe = models.CharField(max_length=255)    

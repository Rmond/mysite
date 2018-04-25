# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django_celery_beat.models import PeriodicTask
from celery.worker.strategy import default
# Create your models here.
class Custom_Schedule(models.Model):
    sd_name=models.CharField(max_length=32)
    sd_num=models.CharField(max_length=4)
    
class Schedule_Info(models.Model):
    mysql_bk_name = models.CharField(max_length=32)
    hostip = models.CharField(max_length=16)
    bk_database = models.CharField(max_length=32)
    bk_table = models.CharField(max_length=32,default="")
    ct_shd = models.ForeignKey(Custom_Schedule)
    hour_minute = models.CharField(max_length=8)
    period_tk = models.ForeignKey(PeriodicTask)
    
class Schedule_Res(models.Model):
    mysql_bk_name = models.CharField(max_length=32)
    star_time = models.DateTimeField()
    stop_time = models.DateTimeField()
    result=models.TextField()
    status=models.CharField(max_length=8)
    
class Sql_Info(models.Model):
    sql_name = models.CharField(max_length=32)
    sql_handle = models.TextField()
    arg_count = models.IntegerField(null=True)
    
# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-25 06:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0001_initial'),
        ('hd_mysql', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule_Info',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mysql_bk_name', models.CharField(max_length=32)),
                ('hostip', models.CharField(max_length=16)),
                ('bk_database', models.CharField(max_length=32)),
                ('bk_table', models.CharField(default='', max_length=32)),
                ('hour_minute', models.CharField(max_length=8)),
                ('ct_shd', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hd_mysql.Custom_Schedule')),
                ('period_tk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.PeriodicTask')),
            ],
        ),
        migrations.CreateModel(
            name='Schedule_Res',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mysql_bk_name', models.CharField(max_length=32)),
                ('star_time', models.DateTimeField()),
                ('stop_time', models.DateTimeField()),
                ('result', models.TextField()),
                ('status', models.CharField(max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Sql_Info',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sql_name', models.CharField(max_length=32)),
                ('sql_handle', models.TextField()),
                ('arg_count', models.IntegerField(null=True)),
            ],
        ),
    ]

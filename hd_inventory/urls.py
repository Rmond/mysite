#!/usr/local/bin/python2.7
# encoding: utf-8

from django.conf.urls import url

import views


urlpatterns = [
    url(r'^add',views.inventory_add),
]

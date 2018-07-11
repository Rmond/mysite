# -*- coding:utf-8 -*-
import os

from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@csrf_exempt
def inventory_add(request):
    with open("/root/.ssh/id_rsa.pub") as rsafile:
        rsa_pub=rsafile.read()
    return HttpResponse(rsa_pub)

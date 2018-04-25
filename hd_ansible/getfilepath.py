# -*- coding: UTF-8 -*-

import os

def GetFilePath(basepath):
    for r,ds,fs in os.walk(basepath):
      for f in fs:
        if ".war" in f:
           return os.path.join(r,f)
           

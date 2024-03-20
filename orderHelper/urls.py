# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 16:36:52 2024

@author: Wilson
"""

from django.urls import path
from . import views
 
urlpatterns = [
    path('callback', views.callback)
]
from django.conf.urls import patterns, include, url
from django.contrib import admin
from .views import *

urlpatterns = patterns('',

	url(r'^image/(?P<id>[0-9]+)/$', ProcessedImageRedirect.as_view(), name='processed_image'),
	
)
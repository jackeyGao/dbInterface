from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from rest_framework import routers
from interface import views
from interface.routers import InterfacePushRouter

router = InterfacePushRouter()
router.register(r'interface', views.InterfaceListCreateViewSet)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dbInterface.views.home', name='home'),
    url(r'^', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
)

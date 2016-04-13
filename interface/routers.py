# -*- coding: utf-8 -*-
'''
File Name: interface/routers.py
Author: JackeyGao
mail: junqi.gao@shuyun.com
Created Time: 2015年07月28日 星期二 15时05分43秒
'''


from collections import OrderedDict
from django.core.urlresolvers import NoReverseMatch
from rest_framework.routers import Route, DynamicDetailRoute, SimpleRouter
from rest_framework.routers import DynamicListRoute
from rest_framework.routers import DefaultRouter
from rest_framework import views
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.reverse import reverse_lazy
from rest_framework.urlpatterns import format_suffix_patterns

from models import InterfaceEntry


class InterfacePushRouter(DefaultRouter):
    """
    A router for interface push APIs 
    """
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        # Dynamically generated list routes.
        # Generated using @list_route decorator
        # on methods of the viewset.
        DynamicListRoute(
            url=r'^{prefix}/{methodname}{trailing_slash}$',
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
        # Detail route.
        #Route(
        #    url=r'^{prefix}/{lookup}{trailing_slash}$',
        #    mapping={
        #        'get': 'retrieve',
        #        'put': 'update',
        #        'patch': 'partial_update',
        #        'delete': 'destroy'
        #    },
        #    name='{basename}-detail',
        #    initkwargs={'suffix': 'Instance'}
        #),
        Route(
            url=r'^{prefix}/{lookup}/$',
            mapping={
                'post': 'push',
                'get': 'pull'
            },
            name='{basename}-table-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated detail routes.
        # Generated using @detail_route decorator on methods of the viewset.
        DynamicDetailRoute(
            url=r'^{prefix}/{lookup}/{methodname}{trailing_slash}$',
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
    ]

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        interface_entrys = InterfaceEntry.objects.all()
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                #namespace = get_resolver_match(request).namespace
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                        
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue

                    for entry in interface_entrys:
                        absolute_url = '/' + key + '/' + entry.tname + '/'
                        url = request.build_absolute_uri(absolute_url)
                        ret['interface-%s' % entry.tname] = url

                return Response(ret)

        return APIRoot.as_view()


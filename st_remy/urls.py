"""st_remy URL Configuration"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from .yasg import urlpatterns as doc_urls
import django.views.static

urlpatterns = [
  path('umbokc-admin/', admin.site.urls),
  path("api-auth/", include("rest_framework.urls")),
  path("auth/", include("djoser.urls")),
  path("auth/", include("djoser.urls.authtoken")),
  path("api/v1/", include("histories.urls")),
]

urlpatterns += doc_urls

if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
  urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.STATIC_ROOT, 'show_indexes': settings.DEBUG}),
    re_path(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': settings.DEBUG})
  ]

urlpatterns += [
  re_path(r"^.*", include("vue.urls")),
]

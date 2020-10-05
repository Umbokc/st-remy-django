from django.urls import path

from .views import IndexTemplateView

urlpatterns = [
  path("", IndexTemplateView.as_view(), name="entry-point"),
]

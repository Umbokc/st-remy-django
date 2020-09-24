from django.urls import path

from . import views

urlpatterns = [
  path("history/", views.HistoryViewSet.as_view({'get': 'list', 'post': 'create'})),
  path("history/<int:pk>", views.HistoryViewSet.as_view({'get': 'retrieve', 'post': 'update'})),

  path("winner/", views.WinnerViewSet.as_view({'get': 'list'})),
  path("voice/", views.AddVoiceViewSet.as_view({'post': 'create'})),
  path("feedback/", views.FeedbackSendView.as_view()),
]

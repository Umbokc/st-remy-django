from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, permissions

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import History, Image, Leaderboard
from .serializers import (
  HistoryDetailSerializer,
  WinnerListSerializer,
  HistoryCreateSerializer,
  CreateVoiceSerializer,
)
from . import service

class IsOwner(permissions.BasePermission):
  def has_object_permission(self, request, view, obj):
    print('request')

    if request.method in permissions.SAFE_METHODS:
      return True

    return obj.user == request.user

class MyHistoryViewSet(viewsets.ModelViewSet):
  serializer_class = HistoryDetailSerializer
  permission_classes = [permissions.IsAuthenticated]

  @swagger_auto_schema(operation_description="Вывод списка историй текущего пользователя")
  def list(self, request):
    return super().list(request)

  def get_queryset(self):
    histories = History.objects.filter(user=self.request.user).order_by('-created_at')
    return histories

class HistoryViewSet(viewsets.ModelViewSet):
  """Класс для работы с историями"""

  permission_classes = [permissions.IsAuthenticatedOrReadOnly&IsOwner]

  @swagger_auto_schema(operation_description="Вывод списка историй")
  def list(self, request):
    return super().list(request)

  @swagger_auto_schema(
    operation_description="Вывод информации о историй",
    manual_parameters=[
      openapi.Parameter('id', openapi.IN_PATH, "Id", type=openapi.TYPE_INTEGER, required=True),
    ],
    responses={200: HistoryDetailSerializer()}
  )
  def retrieve(self, request, pk):
    return super().retrieve(request, pk)

  @swagger_auto_schema(operation_description="Создание истории", responses={200: HistoryDetailSerializer()})
  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = self.perform_create(serializer)
    instance_serializer = HistoryDetailSerializer(instance)
    return Response(instance_serializer.data)

  @swagger_auto_schema(operation_description="Обновление истории истории", responses={200: HistoryDetailSerializer()})
  def update(self, request, *args, **kwargs):
    return self.create(request, *args, **kwargs)

  def get_queryset(self):
    histories = History.objects.filter(draft=False, status='pub').order_by('-created_at')
    return histories

  def perform_create(self, serializer):
    return serializer.save(user=self.request.user)

  def get_serializer_class(self):
    if self.action in ['list', 'retrieve']:
      return HistoryDetailSerializer
    elif self.action in ['create', 'update']:
      return HistoryCreateSerializer

class WinnerViewSet(viewsets.ReadOnlyModelViewSet):
  """Вывод списка победителей"""

  serializer_class = WinnerListSerializer

  def get_queryset(self):
    winners = Leaderboard.objects.all().order_by('-main', '-week')
    return winners

class AddVoiceViewSet(viewsets.ModelViewSet):
  """Добавление голоса истории"""
  serializer_class = CreateVoiceSerializer
  permission_classes = [permissions.IsAuthenticated]

class FeedbackSendView(APIView):
  """Отправка формы обртатной связи"""

  @swagger_auto_schema(operation_description="Отправка формы обртатной связи",
  request_body=openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name', 'email', 'message', 'theme'],
    properties={
      'name': openapi.Schema(type=openapi.TYPE_STRING),
      'email': openapi.Schema(type=openapi.TYPE_STRING),
      'message': openapi.Schema(type=openapi.TYPE_STRING),
      'theme': openapi.Schema(type=openapi.TYPE_STRING),
    },
  ), responses={200: openapi.Response("OK")})
  def post(self, request):
    service.send_feedback(request.data)
    return Response(status=201, data='OK')

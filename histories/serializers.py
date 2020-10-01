from collections import OrderedDict

from django.contrib.auth import get_user_model
from djoser.serializers import (
  UserSerializer as BaseUserSerializer,
  UserCreateSerializer as BaseUserRegistrationSerializer
)
from djoser.conf import settings
from rest_framework import serializers

from .models import History, Image, Leaderboard, Voice, Profile
from .service import get_last_day_week

User = get_user_model()

class ImageDetailSerializer(serializers.ModelSerializer):
  """Информация о изображении"""

  class Meta:
    model = Image
    fields = ['id', 'image', 'date', 'status', 'comment']

class HistoryDetailSerializer(serializers.ModelSerializer):
  """Полная информация о истории"""
  images = serializers.SerializerMethodField(method_name='get_images_related')
  user = serializers.SerializerMethodField(method_name='get_user')

  class Meta:
    model = History
    fields = ['id', 'desc', 'desc_status', 'desc_comment', 'status', 'orientation', 'week', 'user', 'images', 'draft']

  def get_images_related(self, instance):
    images = instance.images.order_by('date')[0:2]
    return ImageDetailSerializer(images, many=True).data

  def get_user(self, obj):
    return obj.user.profile.get_full_name()

class WinnerListSerializer(serializers.ModelSerializer):
  """Список победителей"""

  history = HistoryDetailSerializer()

  class Meta:
    model = Leaderboard
    fields = ['history', 'week', 'main']

class ImageCreateSerializer(serializers.ModelSerializer):
  """Добавление изображений"""

  class Meta:
    model = Image
    fields = ['image', 'date']

class HistoryCreateSerializer(serializers.HyperlinkedModelSerializer):
  """Полная информация о истории"""
  images = ImageCreateSerializer(source='image_set', many=True, read_only=True)
  img_index = serializers.IntegerField(read_only=True)

  class Meta:
    model = History
    fields = ['desc', 'draft', 'images', 'img_index']

  def current_user(self):
    request = self.context.get('request', None)
    if request:
      return request.user

  def create(self, validated_data):
    years = self.context.get('view').request.POST.getlist('years')

    history = History.objects.create(
      desc=validated_data.get('desc'),
      draft=bool(validated_data.get('draft')),
      user=self.current_user(),
      week=get_last_day_week()
    )

    images_data = self.context.get('view').request.FILES.getlist('images')[0:2]

    for i,image_data in enumerate(images_data):
      year = years[i] if i < len(years) else 2000
      Image.objects.create(history=history, image=image_data, date=year)

    return history

  def update(self, instance, validated_data):

    years = self.context.get('view').request.POST.getlist('years')

    if instance.desc_status == 'edit':
      instance.desc = validated_data.get('desc')

    if instance.draft:
      instance.draft = bool(validated_data.get('draft'))

    instance.save()

    images_data = self.context.get('view').request.FILES.getlist('images')[0:2]

    if len(images_data) == 2:
      img_to_del = Image.objects.filter(history=instance, status='edit')
      if len(img_to_del) == 2:
        img_to_del.delete()

        for i,image_data in enumerate(images_data):
          year = years[i] if i < len(years) else 2000
          Image.objects.create(history=instance, image=image_data, date=year)

    elif len(images_data) == 1:
      imgs = Image.objects.all().filter(history=instance).order_by('date')
      img_index = int(self.context.get('view').request.POST.get('img_index', -1))
      for i, img in enumerate(imgs):

        if img.status != 'edit':
          continue

        img.date=years[i]

        if img_index != -1 and i == img_index:
          img.image=images_data[0]

        img.save()

    return instance

class CreateVoiceSerializer(serializers.ModelSerializer):
  """Добавление голоса к истории пользователем"""

  class Meta:
    model = Voice
    fields = ("history",)

  def create(self, validated_data):
    user = self.current_user()
    history = validated_data.get('history', None)

    if history.user == user:
      error = {'message': 'Вы не можете голосовать за свою историю, хоть мы и понимаем, что она вам очень нравится.'}
      raise serializers.ValidationError(error)

    voice, _ = Voice.objects.get_or_create(
      user=user,
      history=validated_data.get('history', None),
    )
    return voice

  def current_user(self):
    request = self.context.get('request', None)
    if request:
      return request.user


class ProfileSerializer(serializers.ModelSerializer):
  """Профиль пользователя"""

  class Meta:
    model = Profile
    fields = ('first_name', 'surname', 'phone', 'birth_date', 'city', 'social_name', 'social_id')

class UserSerializer(BaseUserSerializer):
  """Пользователь"""

  profile = ProfileSerializer()

  class Meta(BaseUserSerializer.Meta):
    model = User
    fields = ('id', 'username', 'email', 'profile')
    ref_name = "Custom UserSerializer"

class UserCreateSerializer(BaseUserRegistrationSerializer):
  """Регистрация пользователя"""

  profile = ProfileSerializer()

  class Meta(BaseUserRegistrationSerializer.Meta):
    model = User
    fields = (
      'username',
      'email',
      "password",
      'profile'
    )

  def save(self, **kwargs):
    profile = self.validated_data.get('profile')
    instance = super().save(**kwargs)
    profile.user = instance
    profile.save()
    # Profile.objects.update_or_create(user=instance, defaults=profile)
    return instance

  def validate(self, attrs):
    new_attrs = {}

    for key in attrs:
      if key == 'profile':
        new_attrs[key] = Profile(**(attrs[key]))
      else:
        new_attrs[key] = attrs[key]

    new_attrs = OrderedDict(new_attrs)
    return super().validate(new_attrs)
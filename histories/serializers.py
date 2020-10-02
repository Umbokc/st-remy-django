from collections import OrderedDict

from django.contrib.auth import get_user_model
from djoser.serializers import (
  UserSerializer as BaseUserSerializer,
  UserCreateSerializer as BaseUserRegistrationSerializer
)
from djoser.conf import settings
from rest_framework import serializers

from .models import History, Image, Leaderboard, Voice, Profile
from .service import get_last_day_week, content_file_name

User = get_user_model()

class PrivateField(serializers.ReadOnlyField):

  def current_user(self):
    request = self.context.get('request', None)
    if request:
      return request.user
    return None

  def get_attribute(self, instance):
    curr_user = self.current_user()
    if curr_user:
      obj_user = None
      if isinstance(instance, Image):
        obj_user = instance.history.user
      else:
        obj_user = instance.user

      if obj_user == curr_user:
        return super(PrivateField, self).get_attribute(instance)

    return None

class ImageDetailSerializer(serializers.ModelSerializer):
  """Информация о изображении"""

  image = serializers.SerializerMethodField()

  class Meta:
    model = Image
    fields = ['image', 'date']

  def get_image(self, obj):
    request = self.context.get('request')
    photo_url = obj.image.url
    return request.build_absolute_uri(photo_url)

class ImageDetailSerializerAuth(ImageDetailSerializer):
  """Информация о изображении"""
  class Meta:
    model = Image
    fields = ImageDetailSerializer.Meta.fields + ['status', 'comment']

class HistoryDetailSerializer(serializers.ModelSerializer):
  """Полная информация о истории"""
  img_before = ImageDetailSerializer()
  img_after = ImageDetailSerializer()
  user = serializers.SerializerMethodField(method_name='get_user')

  class Meta:
    model = History
    fields = [
      'id', 'desc', 'orientation', 'week', 'user', 'img_before', 'img_after',
    ]

  def get_user(self, obj):
    return obj.user.profile.get_full_name()

class HistoryDetailSerializerAuth(HistoryDetailSerializer):
  """Полная информация о истории"""
  img_before = ImageDetailSerializerAuth()
  img_after = ImageDetailSerializerAuth()
  class Meta:
    model = History
    fields = HistoryDetailSerializer.Meta.fields + ['desc_status', 'desc_comment', 'status', 'draft']

class WinnerListSerializer(serializers.ModelSerializer):
  """Список победителей"""

  history = HistoryDetailSerializer()

  class Meta:
    model = Leaderboard
    fields = ['history', 'week', 'main']

class HistoryCreateSerializer(serializers.HyperlinkedModelSerializer):
  """Полная информация о истории"""
  img_before = ImageDetailSerializerAuth(source='image_set_before', read_only=True)
  img_after = ImageDetailSerializerAuth(source='image_set_after', read_only=True)

  class Meta:
    model = History
    fields = (
      'desc',
      'draft',
      'img_before',
      'img_after',
    )

  def current_user(self):
    request = self.context.get('request', None)
    if request:
      return request.user
    return None

  def create(self, validated_data):

    history = History.objects.create(
      desc=validated_data.get('desc'),
      draft=bool(validated_data.get('draft')),
      user=self.current_user(),
      week=get_last_day_week()
    )

    self.save_images(history, True)

    return history

  def update(self, instance, validated_data):

    if instance.draft:
      instance.draft = bool(validated_data.get('draft'))

    if instance.desc_status == 'edit' or instance.draft:
      instance.desc = validated_data.get('desc')

    instance.save()

    self.save_images(instance, instance.draft)

    return instance

  def save_images(self, history, is_draft):

    post_data = self.context.get('view').request.POST
    files = self.context.get('view').request.FILES

    year_before = post_data.get('yearBefore')
    year_after = post_data.get('yearAfter')

    img_before = files.get('imageBefore')
    img_after = files.get('imageAfter')

    img_before.name = content_file_name(history, 'before', img_before.name)
    img_after.name = content_file_name(history, 'after', img_after.name)

    can_update_img_b = True
    can_update_img_a = True
    status_before = 'mod'
    status_after = 'mod'


    if img_before:
      if history.img_before:
        if history.img_before.status == 'edit' or is_draft:
          status_before = history.img_before.status
          history.img_before.delete()
        else:
          can_update_img_b = False

      if can_update_img_b:
        history.img_before = Image.objects.create(
          image=img_before, history=history, status=status_before
        )
        # history.img_before.image = content_file_name(history.img_before, history.img_before.image.url)
        # history.img_before.save()

    if year_before and history.img_before and can_update_img_b:
      history.img_before.date = year_before
      history.img_before.save()

    if img_after:
      if history.img_after:
        if history.img_after.status == 'edit' or is_draft:
          status_after = history.img_after.status
          history.img_after.delete()
        else:
          can_update_img_a = False

      if can_update_img_a:
        history.img_after = Image.objects.create(
          image=img_after, history=history, status=status_after
        )

    if year_after and history.img_after and can_update_img_a:
      history.img_after.date = year_after
      history.img_after.save()

    history.save()
    return history

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
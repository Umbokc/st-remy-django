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
  """Информация о изображении для авторизованного пользователя"""
  class Meta:
    model = Image
    fields = ImageDetailSerializer.Meta.fields + ['status', 'comment']

class HistoryDetailSerializer(serializers.ModelSerializer):
  """Информация о истории"""
  img_before = ImageDetailSerializer()
  img_after = ImageDetailSerializer()
  user = serializers.SerializerMethodField(method_name='get_user')
  voices = serializers.SerializerMethodField()

  class Meta:
    model = History
    fields = [
      'id', 'desc', 'orientation', 'week', 'user', 'img_before', 'img_after', 'voices'
    ]

  def get_user(self, obj):
    return obj.user.profile.get_full_name()

  def get_voices(self, obj):
    return obj.voices.count()

class HistoryDetailSerializerAuth(HistoryDetailSerializer):
  """Информация о истории для авторизованного пользователя"""
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
  """Создание и обновление истории"""
  imageBefore = serializers.ImageField(max_length=None, allow_empty_file=False, read_only=True)
  yearBefore = serializers.IntegerField(min_value=1900, max_value=2999, read_only=True)

  imageAfter = serializers.ImageField(max_length=None, allow_empty_file=False, read_only=True)
  yearAfter = serializers.IntegerField(min_value=1900, max_value=2999, read_only=True)

  class Meta:
    model = History
    fields = (
      'desc',
      'draft',
      'imageBefore',
      'yearBefore',
      'imageAfter',
      'yearAfter',
    )

  def current_user(self):
    request = self.context.get('request', None)
    if request:
      return request.user
    return None

  def create(self, validated_data):
    is_draft = bool(validated_data.get('draft'))
    desc_status = 'edit' if is_draft else 'mod'

    history = History.objects.create(
      desc=validated_data.get('desc'),
      draft=is_draft,
      desc_status=desc_status,
      user=self.current_user(),
      week=get_last_day_week()
    )

    self.save_images(history, is_draft, is_create=True)

    return history

  def update(self, instance, validated_data):
    status = instance.desc_status

    if instance.desc_status == 'edit' or instance.draft:
      instance.desc = validated_data.get('desc')
      if not instance.draft:
        status = 'mod'

    if instance.draft:
      instance.draft = bool(validated_data.get('draft'))
      status = 'edit' if instance.draft else 'mod'

    instance.desc_status = status
    instance.save()

    self.save_images(instance, instance.draft)

    return instance

  def save_image(self, history, type_img, img=None, year=None, is_draft=False, is_create=False):
    attr_img = 'img_%s' % type_img
    can_update_img = True

    status = 'edit' if is_draft else 'mod'

    if img:
      img.name = content_file_name(history, type_img, img.name)

      # update
      old_img = getattr(history, attr_img)
      if old_img:
        if old_img.status == 'edit' or is_draft:
          if year is None:
            year = old_img.date

          old_img.delete()
        else:
          can_update_img = False

      if can_update_img:
        new_img = Image.objects.create(image=img, history=history, status=status)
        setattr(history, attr_img, new_img)

    curr_img = getattr(history, attr_img)
    if curr_img:
      if curr_img.status != status:
        curr_img.status = status

      if year and can_update_img:
        curr_img.date = year

      curr_img.save()

  def save_images(self, history, is_draft, is_create=False):
    post_data = self.context.get('view').request.POST
    files = self.context.get('view').request.FILES

    for type_img in ['before', 'after']:
      self.save_image(
        history, type_img,
        img=files.get('image%s' % type_img.capitalize(), None),
        year=post_data.get('year%s' % type_img.capitalize(), None),
        is_draft=is_draft,
        is_create=is_create
      )

    history.save()
    return history

class CreateVoiceSerializer(serializers.ModelSerializer):
  """Добавление голоса к истории"""

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
      history=history
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
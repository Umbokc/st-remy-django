from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import History, Image, Leaderboard, Voice, Profile


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
  save_on_top = True
  save_as = True
  list_display = ("id", "history", "get_image", "date", "status", "comment")
  readonly_fields = ("get_image",)

  def get_image(self, obj):
      return mark_safe(f'<img src={obj.image.url} width="100" height="110"')

  get_image.short_description = "Изображение"

class ImagesInline(admin.TabularInline):
  """Изображения"""
  model = Image
  extra = 0
  max_num = 2
  readonly_fields = ("get_image",)

  def get_image(self, obj):
    return mark_safe(f'<img src={obj.image.url} width="100" height="110"')

  get_image.short_description = "Изображение"

@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
  save_on_top = True
  save_as = True
  inlines = [ImagesInline]
  list_display = ("id", "desc", "get_user", "status", "get_voices", "get_images")
  list_display_links = ("id", "desc", "get_images")
  list_editable = ("status",)

  def get_user(self, obj):
    return obj.user.username

  def get_images(self, obj):
    images = obj.images.all()
    if images:
      return mark_safe(f'<img src={images[0].image.url} width="100" height="110"><img src={images[1].image.url} width="100" height="110">')
    return 'Отсутствуют'

  def get_voices(self, obj):
    return obj.voices.count()

  get_images.short_description = 'Изображения'
  get_user.short_description = 'Пользователь'
  get_voices.short_description = 'Голосов'

@admin.register(Voice)
class VoiceAdmin(admin.ModelAdmin):
  save_on_top = True
  save_as = True

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
  save_on_top = True
  save_as = True

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
  save_on_top = True
  save_as = True
  list_display = ("get_user", "get_email", "first_name", "surname", "get_type", "phone", "social_name", "social_id")
  # readonly_fields = ("get_user",)

  def get_user(self, obj):
    return obj.user.username

  def get_email(self, obj):
    return obj.user.email

  def get_type(self, obj):
    if obj.user.is_superuser:
      return 'Админ'
    if obj.user.is_staff:
      return 'Персонал'

    return 'Пользователь'

  get_user.short_description = 'Пользователь'
  get_email.short_description = 'Почта'
  get_type.short_description = 'Роль'

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatechars

from .models import History, Image, Leaderboard, Voice, Profile

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
  """Изображения"""
  save_on_top = True
  save_as = True
  list_display = ("id", "history", "get_image", "date", "status", "comment")
  readonly_fields = ("get_image",)
  exclude = ('history',)

  def get_image(self, obj):
      return mark_safe(f'<img src={obj.image.url} width="100" height="110"')

  get_image.short_description = "Изображение"

class ImagesInline(admin.TabularInline):
  """Изображения в истории"""
  model = Image
  extra = 0
  max_num = 2
  readonly_fields = ("get_image",)

  def get_image(self, obj):
    return mark_safe(f'<img src={obj.image.url} width="100" height="110"')

  get_image.short_description = "Изображение"

@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
  """Истории"""
  save_on_top = True
  save_as = True
  inlines = [ImagesInline]
  list_display = ("id", "get_desc", "get_user", "status", "get_voices", "get_images")
  list_display_links = ("id", "get_desc", "get_images")
  list_editable = ("status",)
  exclude = ('img_before','img_after', 'admin_viewed')
  list_per_page = 10

  def get_desc(self, obj):
    return truncatechars(obj.desc, 35)

  def get_user(self, obj):
    return obj.user.username

  def get_images(self, obj):
    images = obj.images.all()

    img_before = obj.img_before.image.url if obj.img_before else ''
    img_after = obj.img_after.image.url if obj.img_after else ''
    html = ''

    if img_before:
      html += f'<img src={img_before} width="100" height="110">'
    if img_after:
      html += f'<img src={img_after} width="100" height="110">'

    if html != '':
      return mark_safe(html)

    return 'Отсутствуют'

  def get_voices(self, obj):
    return obj.voices.count()

  get_images.short_description = 'Изображения'
  get_user.short_description = 'Пользователь'
  get_voices.short_description = 'Голосов'

  def save_model(self, request, obj, form, change):
    new_status = None

    if obj.draft == True:
      new_status = 'edit'

    if obj.status == 'pub':
      new_status = 'pub'
      obj.draft = False

    if new_status != None:
      obj.desc_status = new_status

      if obj.img_before:
        obj.img_before.status = new_status
        obj.img_before.save()

      if obj.img_after:
        obj.img_after.status = new_status
        obj.img_after.save()

    obj.save()

@admin.register(Voice)
class VoiceAdmin(admin.ModelAdmin):
  """Голоса"""
  save_on_top = True
  save_as = True

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
  """Победители"""
  save_on_top = True
  save_as = True

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
  """Пользователи"""
  save_on_top = True
  save_as = True
  list_display = ("get_user", "get_email", "first_name", "surname", "get_type", "phone", "social_name", "social_id")
  exclude = ("user",)
  readonly_fields = ("get_user",)

  def get_user(self, obj):
    return f'{obj.user.username}'

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

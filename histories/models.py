from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from enum import Enum

class TimeStampMixin(models.Model):
  """Абстрактный класс добавляющий всем моделям поля: created_at, updated_at"""
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    abstract = True

STATUS = (
  ('mod', 'На модерации'),
  ('pub', 'Опубликовано'),
  ('reject', 'Отклонено')
)

STATUS_ITEMS = STATUS + (
  ('edit', 'Редактируется'),
)

class Image(TimeStampMixin):
  """Изображение"""

  image = models.ImageField("Изображение", upload_to="images/")
  date = models.PositiveSmallIntegerField("Дата фотографии", default=2019)
  status = models.CharField("Статус изображения", max_length=10, choices=STATUS_ITEMS, default='mod')
  comment = models.TextField("Комментарий", null=True, blank=True)
  history = models.ForeignKey('History', verbose_name="История", on_delete=models.CASCADE, related_name="images", null=True, blank=True)

  def __str__(self):
    return f'{self.id}'

  class Meta:
    verbose_name = "Изображение"
    verbose_name_plural = "Изображения"

class History(TimeStampMixin):
  """История"""

  ORIENTATION = (
    ('vertical', 'Вертикальная'),
    ('horizontal', 'Горизонтальная')
  )

  desc = models.TextField("Описание")
  desc_comment = models.TextField("Комментарий к описанию", null=True, blank=True)
  desc_status = models.CharField("Статус описания", max_length=10, choices=STATUS_ITEMS, default='mod')

  user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

  orientation = models.CharField("Ориентация", max_length=10, choices=ORIENTATION, default='horiz')
  status = models.CharField("Статус истории", max_length=10, choices=STATUS, default='mod')

  week = models.DateField("Неделя")
  admin_viewed = models.BooleanField("Просмотренно админом", default=False)
  draft = models.BooleanField("Черновик", default=False)

  img_before = models.OneToOneField(
    Image,
    on_delete=models.SET_NULL,
    related_name='img_before',
    null=True, blank=True
  )

  img_after = models.OneToOneField(
    Image,
    on_delete=models.SET_NULL,
    related_name='img_after',
    null=True, blank=True
  )

  def get_orientation(self):
    for x in self.ORIENTATION:
      if x[0] == self.orientation:
        return x[1]

  def get_status(self):
    for x in self.STATUS:
      if x[0] == self.status:
        return x[1]

  def get_desc_status(self):
    for x in STATUS:
      if x[0] == self.desc_status:
        return x[1]

  def __str__(self):
    return f'{self.id}'

  class Meta:
    verbose_name = "История"
    verbose_name_plural = "Истории"

class Leaderboard(TimeStampMixin):
  """Список победителей"""

  history = models.ForeignKey(History, verbose_name="История", on_delete=models.CASCADE)
  week = models.DateField("Неделя")
  main = models.BooleanField("Главный победитель", default=False)

  def __str__(self):
    return f'{self.week}'

  class Meta:
    verbose_name = "Список победителей"
    verbose_name_plural = "Списки победителей"

class Voice(TimeStampMixin):
  """Голос"""

  history = models.ForeignKey(History, verbose_name="История", on_delete=models.CASCADE, related_name="voices")
  user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

  def __str__(self):
    return f'{self.history} - {self.user}'

  class Meta:
    verbose_name = "Голос"
    verbose_name_plural = "Голоса"

class Profile(TimeStampMixin):
  """Пользователь"""

  SOCIAL = (
    ('vk', 'Вконтакте'),
    ('ok', 'Одноклассники'),
    ('fb', 'Facebook')
  )

  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

  first_name = models.CharField("Имя", max_length=255)
  surname = models.CharField("Фамилия", max_length=255)

  mobile_num_regex = RegexValidator(regex="^[0-9]{10,15}$", message="Введен номер мобильного телефона в неправильном формате!")
  phone = models.CharField("Телефон", validators=[mobile_num_regex], max_length=13, blank=True)

  birth_date = models.DateField("Дата рождения", null=True, blank=True)
  city = models.CharField("Город", max_length=255, blank=True, null=True)

  social_name = models.CharField("Соц. сеть", max_length=32, blank=True, null=True, choices=SOCIAL)
  social_id = models.CharField("ID в соц. сети", max_length=255, blank=True, null=True)

  def get_full_name(self):
    return f'{self.first_name} {self.surname}'

  def __str__(self):
    return self.get_full_name()

  class Meta:
    verbose_name = "Пользователь"
    verbose_name_plural = "Пользователи"

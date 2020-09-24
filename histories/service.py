from django.core.mail import send_mail
from django.conf import settings
from threading import Thread

import datetime

def get_last_day_week(d=datetime.date.today()):
  res = d + datetime.timedelta(days = 6 - d.weekday())
  return res

def send_feedback(data):
  Thread(target=send_email, args=(data,)).start()

def send_email(data):
  email = data.get('email')
  name = data.get('name')
  message = data.get('message')
  theme = data.get('theme')

  send_mail(
    'Сообщение с сайта',
    f"Тема: {theme}\nИмя: {name}\nПочта: {email}\nСообщение: {message}\n",
    email,
    [settings.ADMIN_EMAIL_FOR_FEEDBACK],
    fail_silently=False
  )

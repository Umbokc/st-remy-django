from django.conf import settings
from django.views.generic.base import TemplateView

class IndexTemplateView(TemplateView):
  """Вывыод шаблона vue"""
  def get_template_names(self):
    template_name = "index.html"
    return template_name
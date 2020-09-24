from django.apps import AppConfig


class HistoriesConfig(AppConfig):
  name = 'histories'
  verbose_name = "Истории"

  def ready(self):
    import histories.signals
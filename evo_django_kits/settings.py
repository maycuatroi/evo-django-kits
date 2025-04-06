from django.conf import settings
from django.test.signals import setting_changed

# Default abstract viewset class that can be overridden in project settings
EVO_ABSTRACT_VIEWSET = getattr(settings, "EVO_ABSTRACT_VIEWSET", "evo_django_kits.entities.base_viewset:BaseViewSet")


def reload_settings(*args, **kwargs):
    setting_changed.send(
        sender=__name__,
        setting="EVO_ABSTRACT_VIEWSET",
        value=EVO_ABSTRACT_VIEWSET,
    )


# setting_changed.connect(reload_settings)

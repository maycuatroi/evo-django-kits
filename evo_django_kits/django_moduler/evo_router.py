from django.conf import settings as django_settings

from evo_django_kits.entities.evo_logger import EvoLogger


class EvoRouter:
    def __init__(self, app_prefix=None):
        self.app_prefix = app_prefix
        self.logger = EvoLogger()

    def auto_router(self, router):
        INSTALLED_APPS = django_settings.INSTALLED_APPS
        if self.app_prefix:
            INSTALLED_APPS = [app for app in INSTALLED_APPS if app.startswith(self.app_prefix)]
        for app in INSTALLED_APPS:
            try:
                app_router = __import__(f"{app}.urls", fromlist=["router"]).router
                router.registry.extend(app_router.registry)
                print(f"Auto register {app} router")
            except ImportError:
                self.logger.warning(f"Cannot import {app}.urls or router not found in {app}.urls")
            except AttributeError:
                self.logger.warning(f"Cannot import {app}.urls or router not found in {app}.urls")

        return router

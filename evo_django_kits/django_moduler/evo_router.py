import importlib.util

from django.conf import settings as django_settings
from django.urls import include, path
from rest_framework.routers import BaseRouter

from evo_django_kits.entities.evo_logger import EvoLogger


class EvoRouter:
    def __init__(self, app_prefix=None):
        self.app_prefix = app_prefix
        self.logger = EvoLogger()
        self.routers = []

    def auto_router(self, router):
        INSTALLED_APPS = django_settings.INSTALLED_APPS
        IS_DEBUG = django_settings.DEBUG
        if self.app_prefix:
            INSTALLED_APPS = [app for app in INSTALLED_APPS if app.startswith(self.app_prefix)]
        self.routers.append(router)
        for app in INSTALLED_APPS:
            try:
                urls_module = importlib.import_module(f"{app}.urls")
                attrs = dir(urls_module)
                for attr in attrs:
                    attr_obj = getattr(urls_module, attr)
                    if isinstance(attr_obj, BaseRouter):
                        app_router = urls_module.router
                        print(f"Auto register {app} router {attr}")
                        self.routers.append(app_router)

            except ModuleNotFoundError as e:
                if e.name == f"{app}.urls":
                    self.logger.warning(f"ModuleNotFoundError: {app}.urls not found")
                else:
                    raise e

            except ImportError as e:
                self.logger.warning(f"Cannot import {app}.urls or router not found in {app}.urls")
                if IS_DEBUG:
                    raise e
            except AttributeError as e:
                self.logger.warning(f"Cannot import {app}.urls or router not found in {app}.urls")
                if IS_DEBUG:
                    raise e

        return router

    def get_paths(self, base_url: str = ""):
        paths = []
        for router in self.routers:
            paths.append(path(base_url, include(router.urls)))
        return paths

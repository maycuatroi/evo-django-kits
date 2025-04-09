import importlib.util


from django.conf import settings as django_settings
from django.urls import include, path
from loguru import logger
from rest_framework.routers import BaseRouter
from .rest_framework import RestFrameworkModuler


class EvoRouter:

    __default_router = None

    def __init__(self, app_prefix=None):
        self.app_prefix = app_prefix
        self.main_router = self.get_default_router()
        self.routers = [self.main_router]

    def get_default_router(self):
        if EvoRouter.__default_router is None:
            from rest_framework.routers import DefaultRouter

            EvoRouter.__default_router = DefaultRouter()
        return EvoRouter.__default_router

    def extend_router(self, app_router):
        """
        Extends the main router with routes from an app router
        """
        for prefix, viewset, basename in app_router.registry:
            self.main_router.register(prefix=prefix, viewset=viewset, basename=basename)

    def auto_router(self):
        INSTALLED_APPS = django_settings.INSTALLED_APPS
        IS_DEBUG = django_settings.DEBUG
        if self.app_prefix:
            INSTALLED_APPS = [app for app in INSTALLED_APPS if app.startswith(self.app_prefix)]

        # Collect router registrations
        registered_routers = []

        for app in INSTALLED_APPS:
            try:
                urls_module = importlib.import_module(f"{app}.urls")
                attrs = dir(urls_module)
                for attr in attrs:
                    attr_obj = getattr(urls_module, attr)
                    if isinstance(attr_obj, BaseRouter):
                        app_router = urls_module.router
                        registered_routers.append((app, attr))
                        self.extend_router(app_router)

            except ModuleNotFoundError as e:
                if e.name != f"{app}.urls":
                    raise e

            except ImportError as e:
                if IS_DEBUG:
                    raise e
            except AttributeError as e:
                if IS_DEBUG:
                    raise e

        # Print registration summary as a table
        if registered_routers:
            print("\nAuto-registered Routers:")
            print("=" * 50)
            print(f"{'App':<30} {'Router':<20}")
            print("-" * 50)
            for app, router_name in registered_routers:
                print(f"\033[94m{app:<30}\033[0m {router_name:<20}")
            print("=" * 50 + "\n")

        self.extend_router(RestFrameworkModuler().router)

        return self.main_router

    def get_paths(self, base_url: str = ""):
        # Since we've consolidated all routes into main_router, we only need to return its paths
        return [path(base_url, include(self.main_router.urls))]


def get_router():
    router = EvoRouter().auto_router()
    return router

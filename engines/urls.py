from django.urls import path, include
from rest_framework.routers import DefaultRouter
from engines.views import (
    GetModuleViewSet,
    InstallModuleViewSet, UninstallModuleViewSet, UpgradeModuleViewSet
)

router = DefaultRouter(trailing_slash=False)

router.register(r'modules', GetModuleViewSet, basename='get-module')
router.register(r'modules/install', InstallModuleViewSet, basename='install-module')
router.register(r'modules/uninstall', UninstallModuleViewSet, basename='uninstall-module')
router.register(r'modules/upgrade', UpgradeModuleViewSet, basename='upgrade-module')

engines_urlpatterns = [
    path('', include(router.urls)),
]

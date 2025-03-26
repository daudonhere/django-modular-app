"""
URL configuration for configs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from configs.views import GetRoleViewSet, GetUserRoleViewSet, HomePage, ErrorPage, LoginViewSet, LogoutViewSet, GetUserViewSet, CreateUserViewSet, DeleteUserViewSet, UpdateUserViewSet
from engines.urls import engines_urlpatterns
from products.urls import products_urlpatterns


handler400 = lambda request, exception: ErrorPage(request, exception, 400)
handler403 = lambda request, exception: ErrorPage(request, exception, 403)
handler404 = lambda request, exception: ErrorPage(request, exception, 404)
handler500 = lambda request: ErrorPage(request, None, 500)

router = DefaultRouter(trailing_slash=False)
router.register(r'roles/get', GetRoleViewSet, basename='roles')
router.register(r'user-roles/get', GetUserRoleViewSet, basename='user-roles' )
router.register(r'users/get', GetUserViewSet, basename='users')
router.register(r'users/create', CreateUserViewSet, basename='create-user')
router.register(r'users/delete', DeleteUserViewSet, basename='delete-user')
router.register(r'users/update', UpdateUserViewSet, basename='update-user')
router.register(r'users/login', LoginViewSet, basename='login-user')
router.register(r'users/logout', LogoutViewSet, basename='logout-user')

urlpatterns = [
    path("", HomePage, name="homepage"),

    path('services/', include(router.urls)),
    path("services/", include((engines_urlpatterns, "engines"), namespace="engines")),
    path("services/", include((products_urlpatterns, "products"), namespace="products")),

    path("services/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("services/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("services/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]



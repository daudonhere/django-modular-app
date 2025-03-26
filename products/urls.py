from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import (
    GetProductViewSet, CreateProductViewSet, UpdateProductViewSet,
    DeleteProductViewSet, PermanentDeleteProductViewSet, RestoreProductViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register(r'products/get', GetProductViewSet, basename='get-products')
router.register(r'products/create', CreateProductViewSet, basename='create-product')
router.register(r'products/update', UpdateProductViewSet, basename='update-product')
router.register(r'products/delete', DeleteProductViewSet, basename='delete-product')
router.register(r'products/destroy', PermanentDeleteProductViewSet, basename='delete-permanent')
router.register(r'products/restore', RestoreProductViewSet, basename='restore-product')

products_urlpatterns = [
    path('', include(router.urls)),
]

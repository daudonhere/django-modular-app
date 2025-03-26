from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from products.models import Product
from products.serializers import ProductSerializer
from configs.permissions import ModulePermission
from configs.utils import success_response, error_response
from datetime import timedelta

# PRODUCT SERVICE START

def product_page(request):
    products = Product.objects.filter(is_deleted=False)
    user_groups = list(request.user.groups.values_list("name", flat=True)) if request.user.is_authenticated else []
    
    return render(request, "installed.html", {
        "products": products,
        "user_groups": user_groups,
        "is_authenticated": request.user.is_authenticated
    })

# GET PRODUCTS
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="get_product_by_id",
        tags=["Product Services"],
        description="Retrieve a specific product by ID (Login required).",
    ),
)
class GetProductViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ProductSerializer
    permission_classes = [ModulePermission]

    def get_queryset(self):
        return Product.objects.all()

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error_response("Authentication required", code=status.HTTP_401_UNAUTHORIZED)

        product = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        serializer = self.get_serializer(product)
        return success_response(serializer.data, "Product retrieved successfully.")

    @extend_schema(
        operation_id="get_all_products",
        tags=["Product Services"],
        description="Retrieve all products (No authentication required).",
    )
    @action(detail=False, methods=["get"])
    def all(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, "All products retrieved successfully.")

# CREATE PRODUCT
@extend_schema_view(
    create=extend_schema(
        operation_id="create_product",
        tags=["Product Services"],
        description="Create a new product.",
    ),
)
class CreateProductViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ProductSerializer
    permission_classes = [ModulePermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Product created successfully.", code=status.HTTP_201_CREATED)
        return error_response(serializer.errors, code=status.HTTP_400_BAD_REQUEST)


# UPDATE PRODUCT
@extend_schema_view(
    update=extend_schema(
        operation_id="update_product_by_id",
        tags=["Product Services"],
        description="Update an existing product by ID.",
    ),
)
class UpdateProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_deleted=False)
    serializer_class = ProductSerializer
    permission_classes = [ModulePermission]
    http_method_names = ["put"]

    def update(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=False)

        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Product updated successfully.")
        return error_response(serializer.errors, code=status.HTTP_400_BAD_REQUEST)

# DELETE PRODUCTS (Soft Delete)
@extend_schema_view(
    destroy=extend_schema(
        operation_id="soft_delete_product_by_id",
        tags=["Product Services"],
        description="Move a specific product to recycle bin.",
    ),
)
class DeleteProductViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ModulePermission]

    def destroy(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["pk"], is_deleted=False)
        product.is_deleted = True
        product.deleted_at = timezone.now()
        product.save()
        return success_response(None, "Product moved to recycle bin.")

    @extend_schema(
        operation_id="soft_delete_all_products",
        tags=["Product Services"],
        description="Move all products to recycle bin.",
    )
    @action(methods=["delete"], detail=False)
    def all(self, request):
        updated_count = Product.objects.filter(is_deleted=False).update(
            is_deleted=True, deleted_at=timezone.now()
        )
        if updated_count == 0:
            return error_response("No products found to move to recycle bin.", code=status.HTTP_404_NOT_FOUND)

        return success_response(None, f"{updated_count} product(s) moved to recycle bin.")


# DELETE PRODUCTS (Permanent Delete)
@extend_schema_view(
    destroy=extend_schema(
        operation_id="permanent_delete_product_by_id",
        tags=["Product Services"],
        description="Delete a specific product permanently.",
    ),
)
class PermanentDeleteProductViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    permission_classes = [ModulePermission]
    queryset = Product.objects.filter(is_deleted=True)

    def destroy(self, request, pk=None):
        product = get_object_or_404(self.queryset, pk=pk)
        product.delete()
        return success_response(None, "Product permanently deleted.")

    @extend_schema(
        operation_id="permanent_delete_all",
        tags=["Product Services"],
        description="Permanently delete all products in recycle bin.",
    )
    @action(detail=False, methods=["delete"])
    def all(self, request):
        deleted_count, _ = self.queryset.delete()

        if deleted_count == 0:
            return error_response("No products found in recycle bin to delete.", code=status.HTTP_404_NOT_FOUND)

        return success_response(None, f"{deleted_count} product(s) permanently deleted.")
    
@extend_schema_view(
    update=extend_schema(
        operation_id="restore_product_by_id",
        tags=["Product Services"],
        description="Restore a product from the recycle bin by ID.",
    ),
)
class RestoreProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_deleted=True)
    serializer_class = ProductSerializer
    permission_classes = [ModulePermission]
    http_method_names = ["put"]

    def update(self, request, *args, **kwargs):
        """Restore a single product by setting is_deleted to False."""
        product = self.get_object()
        product.is_deleted = False
        product.deleted_at = None
        product.save()
        return success_response(None, "Product restored successfully.")

    @extend_schema(
        operation_id="restore_all_products",
        tags=["Product Services"],
        description="Restore all products from the recycle bin.",
    )
    @action(detail=False, methods=["put"], url_path="all")
    def restore_all(self, request):
        """Restore all products by setting is_deleted to False."""
        updated_count = self.queryset.update(is_deleted=False, deleted_at=None)

        if updated_count == 0:
            return error_response("No products found in recycle bin to restore.", code=status.HTTP_404_NOT_FOUND)

        return success_response(None, f"{updated_count} product(s) restored successfully.")



# CLEANUP SCHEDULER: Auto-delete recycle after 24 hours
def cleanup_recycle_bin():
    threshold = timezone.now() - timedelta(hours=24)
    Product.objects.filter(is_deleted=True, deleted_at__lte=threshold).delete()

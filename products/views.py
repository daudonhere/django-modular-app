from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from products.models import Product
from products.serializers import ProductSerializer
from configs.permissions import ModulePermission
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
        return Product.objects.filter(is_deleted=False)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        product = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_all_products",
        tags=["Product Services"],
        description="Retrieve all products (No authentication required).",
    )
    @action(detail=False, methods=["get"])
    def all(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

# DELETE PRODUCTS ( Soft Delete )
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
        return Response({"message": "Product moved to recycle bin."}, status=status.HTTP_204_NO_CONTENT)

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
        return Response({"message": f"{updated_count} product(s) moved to recycle bin."}, status=status.HTTP_204_NO_CONTENT)

    
# DELETE PRODUCTS ( Permanent Delete )
@extend_schema_view(
    destroy=extend_schema(
        operation_id="permanent_delete_product_by_id",
        tags=["Product Services"],
        description="Delete all product from recycle.",
    ),
)

class PermanentDeleteProductViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    permission_classes = [ModulePermission]
    queryset = Product.objects.filter(is_deleted=True)

    def destroy(self, request, pk=None):
        product = get_object_or_404(self.queryset, pk=pk)
        product.delete()
        return Response({"message": "Product permanently deleted."}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="permanent_delete_all",
        tags=["Product Services"],
        description="Permanently delete all products in recycle bin.",
    )
    @action(detail=False, methods=["delete"])
    def all(self, request):
        deleted_count, _ = self.queryset.delete()
        return Response({"message": f"{deleted_count} product(s) permanently deleted."}, status=status.HTTP_204_NO_CONTENT)
    
# RESTORE PRODUCTS
@extend_schema_view(
    destroy=extend_schema(
        operation_id="restore_product_by_id",
        tags=["Product Services"],
        description="Restore a product from the recycle bin by ID.",
    ),
)
class RestoreProductViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    permission_classes = [ModulePermission]
    queryset = Product.objects.filter(is_deleted=True)

    def destroy(self, request, pk=None):
        product = get_object_or_404(self.queryset, pk=pk)
        product.is_deleted = False
        product.deleted_at = None
        product.save()
        return Response({"message": "Product restored successfully."}, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="restore_all_products",
        tags=["Product Services"],
        description="Restore all products from the recycle bin.",
    )
    @action(detail=False, methods=["post"])
    def all(self, request):
        updated_count = self.queryset.update(is_deleted=False, deleted_at=None)
        return Response(
            {"message": f"{updated_count} product(s) restored successfully."},
            status=status.HTTP_200_OK
        )

# CLEANUP SCHEDULER: Auto-delete recycle after 24 hours
def cleanup_recycle_bin():
    threshold = timezone.now() - timedelta(hours=24)
    Product.objects.filter(is_deleted=True, deleted_at__lte=threshold).delete()

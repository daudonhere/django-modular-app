from rest_framework import serializers
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "product_name", "barcode", "price", "stock", "is_deleted", "deleted_at", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

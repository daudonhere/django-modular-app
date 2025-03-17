from rest_framework import serializers
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "product_name", "barcode", "price", "stock", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

class ProductRecycleBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "product_name", "deleted_at"]
        read_only_fields = ["id", "deleted_at"]

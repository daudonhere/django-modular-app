from django.db import models
from django.utils.timezone import now
from datetime import timedelta

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tabel_product_data"

    def __str__(self):
        return self.product_name

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    @staticmethod
    def permanent_delete_old():
        threshold = now() - timedelta(hours=24)
        Product.objects.filter(is_deleted=True, deleted_at__lte=threshold).delete()

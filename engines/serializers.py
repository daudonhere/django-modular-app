from rest_framework import serializers
from engines.models import Module

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id", "name", "installed", "version"]

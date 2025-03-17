from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from configs.models import User, Role, UserRole

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "token", "refresh_token", "is_active", "created_at", "updated_at"]
        read_only_fields = ["token", "refresh_token"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            raise serializers.ValidationError({"password": "This field is required."})
        user.save()
        return user
    
    def update(self, instance, validated_data):
        roles_data = validated_data.pop('roles', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if roles_data is not None:
            instance.roles.set(roles_data)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()
        return instance

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "rolename", "created_at", "updated_at"]

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ["id", "user", "role", "created_at", "updated_at"]

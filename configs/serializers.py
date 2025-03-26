from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from configs.models import User, Role, UserRole

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    roles = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    role_details = serializers.SerializerMethodField()

    def create(self, validated_data):
        roles_ids = validated_data.pop("roles", [])
        password = validated_data.pop("password", None)

        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        valid_roles = Role.objects.filter(id__in=roles_ids)
        for role in valid_roles:
            UserRole.objects.get_or_create(user=user, role=role)

        return user


    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "roles", "role_details",
            "token", "refresh_token", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["token", "refresh_token"]

    def get_role_details(self, obj):
        roles = obj.userrole_set.all().select_related("role")
        return [{"id": role.role.id, "rolename": role.role.rolename} for role in roles]

    def update(self, instance, validated_data):
        roles_ids = validated_data.pop("roles", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if "password" in validated_data:
            instance.set_password(validated_data["password"])

        instance.save()

        if roles_ids is not None:
            UserRole.objects.filter(user=instance).delete()
            valid_roles = Role.objects.filter(id__in=roles_ids)
            UserRole.objects.bulk_create(
                [UserRole(user=instance, role=role) for role in valid_roles]
            )

        return instance

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "rolename", "created_at", "updated_at"]

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ["id", "user", "role", "created_at", "updated_at"]

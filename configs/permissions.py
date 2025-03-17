from rest_framework import permissions
from configs.models import UserRole

from rest_framework import permissions
from configs.models import UserRole

class ModulePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True 

        if not request.user.is_authenticated:
            return False

        user_roles = list(
            UserRole.objects.filter(user=request.user)
            .values_list("role__rolename", flat=True)
        )

        if request.method in ["POST", "PUT", "PATCH"]:
            return any(role in user_roles for role in ["user", "manager", "administrator"])

        if request.method == "DELETE":
            return any(role in user_roles for role in ["manager", "administrator"])

        return False


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        try:
            user_roles = list(UserRole.objects.filter(user=request.user).values_list("role__rolename", flat=True))

            if request.method in ["POST", "PUT", "PATCH"]:
                return any(role in ["user", "manager", "administrator"] for role in user_roles)
            
            if request.method == "DELETE":
                return any(role in ["manager", "administrator"] for role in user_roles)

        except Exception as e:
            return False

        return False
    
class EnginePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_roles = set(
            UserRole.objects.filter(user=request.user)
            .values_list("role__rolename", flat=True)
        )
        allowed_roles = {"manager", "administrator"}

        return bool(user_roles & allowed_roles)


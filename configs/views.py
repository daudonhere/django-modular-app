import uuid
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from configs.models import User, Role, UserRole
from configs.serializers import LoginSerializer, UserSerializer, RoleSerializer, UserRoleSerializer
from configs.permissions import UserPermission
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

# Render home page
def HomePage(request):
    return render(request, "home.html")

# Render error page
def ErrorPage(request, exception=None, status_code=500):
    error_message = str(exception) if exception else "Something went wrong"
    context = {"status_code": status_code, "error_message": error_message}
    return render(request, "error.html", context, status=status_code)

# AUTHENTICATION SERVICE START

# Login View
class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="login_user",
        tags=["Auth Services"],
        description="Authenticate user and generate token.",
        request=LoginSerializer,
        responses={
            200: {"token": "string", "refresh_token": "string"},
            400: {"error": "Invalid credentials"},
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            if not check_password(password, user.password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            token = str(uuid.uuid4())
            refresh_token = str(uuid.uuid4())

            user.token = token
            user.refresh_token = refresh_token
            user.save()

            return Response({"token": token, "refresh_token": refresh_token}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Logout View
class LogoutViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="logout_user",
        tags=["Auth Services"],
        description="Logout user and clear token.",
        request={"application/json": {"example": {"token": "user-token"}}},
        responses={
            200: {"message": "Logged out successfully"},
            400: {"error": "Invalid request"},
        },
    )
    def create(self, request, *args, **kwargs):
        token = request.data.get("token")

        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(token=token)
        except User.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        user.token = None
        user.refresh_token = None
        user.save()

        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    
# AUTHENTICATION SERVICE END



# ROLES SERVICE START

# Get Roles
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="get_roles_by_id",
        tags=["Roles Services"],
        description="Retrieve a specific role by ID.",
    ),
)
class GetRoleViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [UserPermission]

    def retrieve(self, request, *args, **kwargs):
        role = get_object_or_404(Role, pk=kwargs["pk"])
        serializer = self.get_serializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_all_roles",
        tags=["Roles Services"],
        description="Retrieve all roles.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_roles(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No roles available."}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Get User Role
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="get_user_roles_by_id",
        tags=["Roles Services"],
        description="Retrieve a specific user role by ID.",
    ),
)
class GetUserRoleViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [UserPermission]

    def retrieve(self, request, *args, **kwargs):
        user_role = get_object_or_404(UserRole, pk=kwargs["pk"])
        serializer = self.get_serializer(user_role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_all_user_roles",
        tags=["Roles Services"],
        description="Retrieve all user roles.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_user_roles(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No user roles available."}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# ROLES SERVICE END

# USER SERVICE START

# Create Users
class CreateUserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="create_user",
        tags=["Users Services"],
        description="Create a new user with role assignment.",
        request={
            "application/json": {
                "example": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "password": "securepassword",
                    "roles": [1, 2]
                }
            }
        },
        responses={
            201: UserSerializer,
            400: {"description": "Invalid data provided"},
        },
    )
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                data = request.data.copy()
                
                roles_ids = data.get("roles", [])
                if not isinstance(roles_ids, list):
                    return Response(
                        {"roles": ["Roles must list or array."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not roles_ids:
                    return Response(
                        {"roles": ["Field roles must filled."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                valid_roles = Role.objects.filter(id__in=roles_ids)
                if valid_roles.count() != len(roles_ids):
                    invalid_ids = set(roles_ids) - set(valid_roles.values_list('id', flat=True))
                    return Response(
                        {"roles": [f"Roles ID not valid: {invalid_ids}"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                
                for role in valid_roles:
                    UserRole.objects.create(user=user, role=role)
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {"validation_error": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except ObjectDoesNotExist as e:
            return Response(
                {"error": f"Object not found: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"system_error": f"internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Get Users

@extend_schema_view(
    retrieve=extend_schema(
        operation_id="get_user_by_id",
        tags=["Users Services"],
        description="Retrieve a specific user by ID.",
    ),
)
class GetUserViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    def retrieve(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs["pk"])
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_all_users",
        tags=["Users Services"],
        description="Retrieve all users.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_users(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No users available."}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Update Users
class UpdateUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermission]
    http_method_names = ["put"]

    @extend_schema(
        operation_id="update_user_by_id",
        tags=["Users Services"],
        description="Update an existing user by ID.",
        request={
            "application/json": {
                "example": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "password": "securepassword",
                    "roles": [1, 2],
                    "is_active": True
                }
            },
        },
        responses={200: UserSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
# Delete Users
@extend_schema_view(
    destroy=extend_schema(
        operation_id="delete_user_by_id",
        tags=["Users Services"],
        description="Delete a specific user by ID.",
    ),
)
class DeleteUserViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    def destroy(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        print(f"Request to delete user ID: {user_id}")

        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({"message": f"User {user_id} deleted."}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        operation_id="delete_all_users",
        tags=["Users Services"],
        description="Delete all users."
    )
    @action(methods=["delete"], detail=False, url_path="all")
    def delete_all(self, request):
        deleted_count, _ = User.objects.all().delete()
        return Response(
            {"message": f"{deleted_count} users deleted."},
            status=status.HTTP_204_NO_CONTENT
        )

# USER SERVICE END

import uuid
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from configs.models import User, Role, UserRole
from configs.serializers import LoginSerializer, UserSerializer, RoleSerializer, UserRoleSerializer
from configs.permissions import UserPermission
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from configs.utils import success_response, error_response

# Render home page
def HomePage(request):
    return render(request, "home.html")

# Render error page
def ErrorPage(request, exception=None, status_code=500):
    error_message = str(exception) if exception else "Something went wrong"
    context = {"status_code": status_code, "error_message": error_message}
    return render(request, "error.html", context, status=status_code)

# AUTHENTICATION SERVICE START

class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="login_user",
        tags=["Auth Services"],
        description="Authenticate user and generate token.",
        request=LoginSerializer,
        responses={
            200: {
                "data": {
                    "token": "string",
                    "refresh_token": "string",
                    "user": {
                        "id": "integer",
                        "username": "string",
                        "email": "string",
                    },
                },
                "status": "success",
                "code": 200,
                "messages": "Login successful",
            },
            401: {
                "data": None,
                "status": "error",
                "code": 401,
                "messages": "Invalid credentials",
            },
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
                return error_response(
                    message="Invalid credentials",
                    code=status.HTTP_401_UNAUTHORIZED
                )

            if not check_password(password, user.password):
                return error_response(
                    message="Invalid credentials",
                    code=status.HTTP_401_UNAUTHORIZED
                )

            token = str(uuid.uuid4())
            refresh_token = str(uuid.uuid4())
            user.token = token
            user.refresh_token = refresh_token
            user.save()

            return success_response(
                data={
                    "token": token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                },
                message="Login successful",
                code=status.HTTP_200_OK
            )

        return error_response(
            message="Invalid input",
            code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors
        )

class LogoutViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="logout_user",
        tags=["Auth Services"],
        description="Logout user and clear token.",
        request={"application/json": {"example": {"token": "user-token"}}},
        responses={
            200: {
                "data": None,
                "status": "success",
                "code": 200,
                "messages": "Logged out successfully",
            },
            400: {
                "data": None,
                "status": "error",
                "code": 400,
                "messages": "Token is required",
            },
            401: {
                "data": None,
                "status": "error",
                "code": 401,
                "messages": "Invalid token",
            },
        },
    )
    def create(self, request, *args, **kwargs):
        token = request.data.get("token")

        if not token:
            return error_response(
                message="Token is required",
                code=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(token=token)
        except User.DoesNotExist:
            return error_response(
                message="Invalid token",
                code=status.HTTP_401_UNAUTHORIZED
            )

        user.token = None
        user.refresh_token = None
        user.save()

        return success_response(
            data=None,
            message="Logged out successfully",
            code=status.HTTP_200_OK
        )

# AUTHENTICATION SERVICE END

# ROLES SERVICE START

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
        role = self.queryset.filter(pk=kwargs["pk"]).first()
        if not role:
            return error_response(
                message="Role not found",
                code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(role)
        return success_response(
            data=serializer.data,
            message="Role retrieved successfully",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="get_all_roles",
        tags=["Roles Services"],
        description="Retrieve all roles.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_roles(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return error_response(
                message="No roles available",
                code=status.HTTP_204_NO_CONTENT
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="Roles retrieved successfully",
            code=status.HTTP_200_OK
        )


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
    permission_classes = [IsAuthenticated, UserPermission]

    def retrieve(self, request, *args, **kwargs):
        user_roles = self.queryset.filter(user_id=kwargs["pk"])
        if not user_roles.exists():
            return error_response(
                message="User roles not found",
                code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(user_roles, many=True) 
        return success_response(
            data=serializer.data,
            message="User roles retrieved successfully",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="get_all_user_roles",
        tags=["Roles Services"],
        description="Retrieve all user roles.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_user_roles(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return error_response(
                message="No user roles available",
                code=status.HTTP_204_NO_CONTENT
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message="User roles retrieved successfully",
            code=status.HTTP_200_OK
        )

# ROLES SERVICE END

# USER SERVICE START

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
                        {
                            "data": None,
                            "status": "error",
                            "code": 400,
                            "messages": "Field 'roles' must be a list."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not roles_ids:
                    return Response(
                        {
                            "data": None,
                            "status": "error",
                            "code": 400,
                            "messages": "Field 'roles' cannot be empty."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                valid_roles = Role.objects.filter(id__in=roles_ids)
                if valid_roles.count() != len(roles_ids):
                    invalid_ids = set(roles_ids) - set(valid_roles.values_list('id', flat=True))
                    return Response(
                        {
                            "data": None,
                            "status": "error",
                            "code": 400,
                            "messages": f"Invalid role IDs: {list(invalid_ids)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                serializer = self.get_serializer(data=data)
                if not serializer.is_valid():
                    errors = serializer.errors
                    username_error = "username" in errors
                    email_error = "email" in errors

                    if username_error and email_error:
                        message = "User with this email and username already exists."
                    elif username_error:
                        message = "User with this username already exists."
                    elif email_error:
                        message = "User with this email already exists."
                    else:
                        message = "Invalid data provided."

                    return Response(
                        {
                            "data": None,
                            "status": "error",
                            "code": 400,
                            "messages": message
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = serializer.save()

                return Response(
                    {
                        "data": serializer.data,
                        "status": "success",
                        "code": 201,
                        "messages": "User created successfully."
                    },
                    status=status.HTTP_201_CREATED
                )

        except ValidationError as e:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 400,
                    "messages": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 500,
                    "messages": f"Internal server error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
    permission_classes = [IsAuthenticated, UserPermission]

    def retrieve(self, request, *args, **kwargs):
        try:
            user = self.get_queryset().get(pk=kwargs["pk"])
            serializer = self.get_serializer(user)
            return Response(
                {
                    "data": serializer.data,
                    "status": "success",
                    "code": 200,
                    "messages": "User retrieved successfully."
                },
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 404,
                    "messages": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        operation_id="get_all_users",
        tags=["Users Services"],
        description="Retrieve all users.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def all_users(self, request):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {
                    "data": [],
                    "status": "success",
                    "code": 200,
                    "messages": "No users available."
                },
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "status": "success",
                "code": 200,
                "messages": "Users retrieved successfully."
            },
            status=status.HTTP_200_OK
        )

class UpdateUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, UserPermission]
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
        user_id = kwargs.get("pk")

        if not user_id:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 400,
                    "messages": "User ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 404,
                    "messages": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 400,
                    "messages": "Validation failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            serializer.save()
            return Response(
                {
                    "data": serializer.data,
                    "status": "success",
                    "code": 200,
                    "messages": "User updated successfully."
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 500,
                    "messages": f"Internal server error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
    permission_classes = [IsAuthenticated, UserPermission]

    def destroy(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")

        if not user_id:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 400,
                    "messages": "User ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response(
                {
                    "data": None,
                    "status": "success",
                    "code": 200,
                    "messages": "User has been deleted successfully."
                },
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 404,
                    "messages": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 500,
                    "messages": f"Internal server error: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        operation_id="delete_all_users",
        tags=["Users Services"],
        description="Delete all users."
    )
    @action(methods=["delete"], detail=False, url_path="all")
    def delete_all(self, request):
        deleted_count, _ = User.objects.all().delete()

        if deleted_count == 0:
            return Response(
                {
                    "data": None,
                    "status": "error",
                    "code": 404,
                    "messages": "No users found to delete."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "data": None,
                "status": "success",
                "code": 200,
                "messages": f"{deleted_count} users have been deleted successfully."
            },
            status=status.HTTP_200_OK
        )

# USER SERVICE END

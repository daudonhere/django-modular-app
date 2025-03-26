from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view
from engines.models import Module
from configs.utils import success_response, error_response
from engines.serializers import ModuleSerializer
from configs.permissions import EnginePermission

# 🔹 GET MODULE
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="get_module_by_id",
        tags=["Module Services"],
        description="Retrieve a specific module by ID.",
    ),
)
class GetModuleViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [EnginePermission]

    def retrieve(self, request, *args, **kwargs):
        module = self.queryset.filter(pk=kwargs["pk"]).first()
        if not module:
            return error_response("Module not found", status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(module)
        return success_response(
            data=serializer.data,
            message="Module retrieved successfully",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="get_all_modules",
        tags=["Module Services"],
        description="Retrieve all modules.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def get_all_modules(self, request):
        modules = self.get_queryset()
        if not modules.exists():
            return error_response("No modules available", status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(modules, many=True)
        return success_response(
            data=serializer.data,
            message="Modules retrieved successfully",
            code=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="get_installed_modules",
        tags=["Module Services"],
        description="Retrieve all installed modules.",
    )
    @action(detail=False, methods=["get"], url_path="active", permission_classes=[AllowAny])  
    def get_installed_modules(self, request):
        modules = self.get_queryset().filter(installed=True)

        if not modules.exists():
            return error_response("No installed modules available", status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(modules, many=True)
        return success_response(
            data=serializer.data,
            message="Installed modules retrieved successfully",
            code=status.HTTP_200_OK
        )


# 🔹 INSTALL MODULE
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="install_module",
        tags=["Module Services"],
        description="Install a module by ID.",
    ),
)
class InstallModuleViewSet(viewsets.ViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [EnginePermission]

    def retrieve(self, request, pk=None):
        module = get_object_or_404(Module, pk=pk)
        module.installed = True
        module.save()
        return success_response(
            data={"module": module.name},
            message=f"Module {module.name} installed successfully.",
            code=status.HTTP_200_OK
        )

# 🔹 UNINSTALL MODULE
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="uninstall_module",
        tags=["Module Services"],
        description="Uninstall a module by ID.",
    ),
)
class UninstallModuleViewSet(viewsets.ViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [EnginePermission]

    def retrieve(self, request, pk=None):
        module = get_object_or_404(Module, pk=pk)
        module.installed = False
        module.save()
        return success_response(
            data={"module": module.name},
            message=f"Module {module.name} uninstalled successfully.",
            code=status.HTTP_200_OK
        )

# 🔹 UPGRADE MODULE
@extend_schema_view(
    retrieve=extend_schema(
        operation_id="upgrade_module",
        tags=["Module Services"],
        description="Upgrade a module by ID.",
    ),
)
class UpgradeModuleViewSet(viewsets.ViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [EnginePermission]

    def retrieve(self, request, pk=None):
        module = get_object_or_404(Module, pk=pk)
        current_version = float(module.version)

        if current_version < 0.9:
            new_version = round(current_version + 0.1, 1)
        else:
            new_version = int(current_version) + 1.0

        module.version = str(new_version)
        module.save()
        return success_response(
            data={"module": module.name, "version": module.version},
            message=f"Module {module.name} upgraded to version {module.version}.",
            code=status.HTTP_200_OK
        )
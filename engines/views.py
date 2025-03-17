from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from engines.models import Module
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
class GetModuleViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [EnginePermission]

    def retrieve(self, request, *args, **kwargs):
        module = get_object_or_404(Module, pk=kwargs["pk"])
        serializer = self.get_serializer(module)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_installed_modules",
        tags=["Module Services"],
        description="Retrieve all installed modules.",
    )
    @action(detail=False, methods=["get"], url_path="active")
    def get_installed_modules(self, request):
        modules = Module.objects.filter(installed=True)
        if not modules.exists():
            return Response({"message": "No installed modules available."}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(modules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="get_all_modules",
        tags=["Module Services"],
        description="Retrieve all modules.",
    )
    @action(detail=False, methods=["get"], url_path="all")
    def get_all_modules(self, request):
        modules = self.queryset
        if not modules.exists():
            return Response({"message": "No modules available."}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(modules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        return Response({"message": f"Module {module.name} installed successfully."}, status=status.HTTP_200_OK)


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
        return Response({"message": f"Module {module.name} uninstalled successfully."}, status=status.HTTP_200_OK)


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
        return Response({"message": f"Module {module.name} upgraded to version {module.version}."}, status=status.HTTP_200_OK)

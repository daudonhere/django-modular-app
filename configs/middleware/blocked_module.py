from django.http import JsonResponse
from django.urls import resolve
from engines.models import Module

class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resolved_url = resolve(request.path)
        module_name = resolved_url.namespace
        if Module.objects.filter(name=module_name, installed=False).exists():
            return JsonResponse(
                {"error": "Module not installed. Please contact administrator or manager to install."},
                status=403
            )

        return self.get_response(request)

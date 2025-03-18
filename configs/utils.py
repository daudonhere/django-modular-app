from rest_framework.response import Response

def success_response(data, message="Request successful", code=200):
    return Response({
        "data": data,
        "status": "success",
        "code": code,
        "messages": message
    }, status=code)

def error_response(message="Request failed", code=400, data=None):
    return Response({
        "data": data,
        "status": "error",
        "code": code,
        "messages": message
    }, status=code)

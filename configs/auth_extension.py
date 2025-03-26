from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CustomTokenScheme(OpenApiAuthenticationExtension):
    target_class = 'configs.authentication.CustomTokenAuthentication'
    name = 'CustomTokenAuth'

    def get_security_definition(self, _=None):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter your token with 'Token' prefix. Example: 'Token 123abc456def'"

        }
from django.contrib.auth import authenticate
from django.utils.cache import patch_vary_headers

# bastb Django 1.10 has updated Middleware. This code imports the Mixin required to get old-style
# middleware working again
# More?
#  https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
try:
    from django.utils.deprecation import MiddlewareMixin
    middleware_parent_class = MiddlewareMixin
except ImportError:
    middleware_parent_class = object


class OAuth2TokenMiddleware(middleware_parent_class):
    """
    Middleware for OAuth2 user authentication

    This middleware is able to work along with AuthenticationMiddleware and its behaviour depends
    on the order it's processed with.

    If it comes *after* AuthenticationMiddleware and request.user is valid, leave it as is and does
    not proceed with token validation. If request.user is the Anonymous user proceeds and try to
    authenticate the user using the OAuth2 access token.

    If it comes *before* AuthenticationMiddleware, or AuthenticationMiddleware is not used at all,
    tries to authenticate user with the OAuth2 access token and set request.user field. Setting
    also request._cached_user field makes AuthenticationMiddleware use that instead of the one from
    the session.

    It also adds 'Authorization' to the 'Vary' header. So that django's cache middleware or a
    reverse proxy can create proper cache keys
    """
    def process_request(self, request):
        # do something only if request contains a Bearer token
        if request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer'):
            if not hasattr(request, 'user') or request.user.is_anonymous():
                user = authenticate(request=request)
                if user:
                    request.user = request._cached_user = user

    def process_response(self, request, response):
        patch_vary_headers(response, ('Authorization',))
        return response

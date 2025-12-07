from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Middleware to force users with must_change_password flag to change their password.
    This ensures supervisors cannot access the system until they set a new password.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            allowed_paths = [
                reverse('accounts:force_password_change'),
                reverse('accounts:logout'),
                '/static/',
                '/media/',
            ]

            if not any(request.path.startswith(path) for path in allowed_paths):
                return redirect('accounts:force_password_change')

        response = self.get_response(request)
        return response

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "admin"

    def handle_no_permission(self):
        raise PermissionDenied


class CustomerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "customer"

    def handle_no_permission(self):
        raise PermissionDenied

from functools import wraps
from django.core.exceptions import PermissionDenied


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role != role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def user_is_pastor(user):
    return (
        user.is_authenticated
        and (
            user.groups.filter(name='Pastor').exists()
            or user.is_staff
            or user.is_superuser
        )
    )


def user_is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def pastor_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not user_is_pastor(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def can_manage_resource(user, resource):
    """Admin can manage any resource; pastors only their own."""
    if not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    return resource.created_by_id == user.id


def staff_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not user_is_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper

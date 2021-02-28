import threading

from django.contrib import auth
from django.template import loader
from django.contrib.auth.models import User


def user_login(request, username, password):
    # Try to authorized.
    user_obj = auth.authenticate(username=username, password=password)
    if user_obj is None:
        # Failed to login, return the error.
        return False
    # Now we have to login the data.
    auth.login(request, user_obj)
    # Correctly.
    return True


def user_logout(request):
    auth.logout(request)


def render_user_info(request):
    return loader.render_to_string(
        'user_manage.html',
        {'struser': request.user.username},
        request)


def user_update(request):
    # Check the authorized.
    user_obj = auth.authenticate(username=request.user.username,
                                 password=request.POST.get('ck'))
    if user_obj is None:
        return {'status': 'error', 'info': 'もとパスワードが間違っています。'}
    # Then update the user password.
    user_obj.set_password(request.POST.get('nck'))
    # Save the user object.
    user_obj.save()
    # Login with the new user.
    auth.login(request, user_obj)
    return {'status': 'ok'}

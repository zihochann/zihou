import threading

from django.contrib import auth
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

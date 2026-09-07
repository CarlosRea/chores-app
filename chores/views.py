from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Roommate


def switch_user(request: HttpRequest, user_id: int) -> HttpResponse:
    roommate = get_object_or_404(Roommate, pk=user_id)
    request.session['active_roommate_id'] = roommate.id

    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
    ):
        return redirect(referer)
    return redirect('/')

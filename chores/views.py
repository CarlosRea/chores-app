from django.db.models import BooleanField, Case, Q, Value, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Chore, Roommate

VALID_TABS = {'all', 'mine', 'pending', 'completed'}


def chore_list(request: HttpRequest) -> HttpResponse:
    raw_tab = request.GET.get('tab', 'all')
    tab = raw_tab if raw_tab in VALID_TABS else 'all'

    today = timezone.localdate()
    queryset = (
        Chore.objects.select_related('assigned_to', 'assigned_by')
        .annotate(
            is_overdue=Case(
                When(Q(is_completed=False) & Q(due_date__lt=today), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by('due_date', 'created_at')
    )

    needs_profile = False
    if tab == 'pending':
        chores = queryset.filter(is_completed=False)
    elif tab == 'completed':
        chores = queryset.filter(is_completed=True)
    elif tab == 'mine':
        active_roommate_id = (
            request.session.get('active_roommate_id')
            if hasattr(request, 'session')
            else None
        )
        active_exists = False
        if active_roommate_id is not None:
            try:
                active_exists = Roommate.objects.filter(id=active_roommate_id).exists()
            except (ValueError, TypeError):
                active_exists = False

        if not active_exists:
            chores = Chore.objects.none()
            needs_profile = True
        else:
            chores = queryset.filter(assigned_to_id=active_roommate_id)
    else:
        chores = queryset

    context = {
        'chores': chores,
        'tab': tab,
        'active_tab': tab,
        'today': today,
        'needs_profile': needs_profile,
    }
    return render(request, 'chores/chore_list.html', context)


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

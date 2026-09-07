from django.http import HttpRequest

from .models import Roommate


def active_roommate(request: HttpRequest) -> dict:
    active = None
    if hasattr(request, "session"):
        roommate_id = request.session.get("active_roommate_id")
        if roommate_id is not None:
            try:
                active = Roommate.objects.filter(id=roommate_id).first()
            except (ValueError, TypeError):
                active = None

    return {
        "active_roommate": active,
        "all_roommates": Roommate.objects.all().order_by("name"),
    }

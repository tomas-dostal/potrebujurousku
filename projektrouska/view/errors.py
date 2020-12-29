from django.shortcuts import render
from datetime import datetime
from projektrouska.sqls import last_modified_date
from projektrouska.sqls import last_check


def custom_page_not_found_view(request, exception):
    return render(
        request,
        "errors/404.html",
        {
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
            "kontrola": last_check(),
        },
    )


def custom_error_view(request, exception=None):
    return render(
        request,
        "errors/500.html",
        {
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
            "kontrola": last_check(),
        },
    )


def custom_permission_denied_view(request, exception=None):
    return render(
        request,
        "errors/403.html",
        {
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
            "kontrola": last_check(),
        },
    )


def custom_bad_request_view(request, exception=None):
    return render(
        request,
        "errors/400.html",
        {
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
            "kontrola": last_check(),
        },
    )

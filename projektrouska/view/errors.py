from django.shortcuts import render


def custom_page_not_found_view(request, exception):
    from datetime import datetime
    from projektrouska.views import posledni_databaze
    from projektrouska.views import posledni_kontrola
    return render(request, "errors/404.html",
                  { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})



def custom_error_view(request, exception=None):
    from datetime import datetime
    from projektrouska.views import posledni_databaze
    from projektrouska.views import posledni_kontrola
    return render(request, "errors/500.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})

def custom_permission_denied_view(request, exception=None):
    from datetime import datetime
    from projektrouska.views import posledni_databaze
    from projektrouska.views import posledni_kontrola
    return render(request, "errors/403.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})

def custom_bad_request_view(request, exception=None):
    from datetime import datetime
    from projektrouska.views import posledni_databaze
    from projektrouska.views import posledni_kontrola
    return render(request, "errors/400.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})


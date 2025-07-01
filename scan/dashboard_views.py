from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def my_dashboard(request):

    # my_context ={
    #     "progress": increment_number(3)
    # }
    return render(request, 'dashboard.html')
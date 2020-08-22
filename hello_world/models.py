from django.db import models

# Create your models here.
from django.shortcuts import render

def project_index(request):
    projects = Project.objects.all()
    context = {
        'projects': projects
    }
    return render(request, 'project_index.html', context)
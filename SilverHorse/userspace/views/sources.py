from django.shortcuts import render

def sources(request):
    return render(request, 'userspace/sources.html')
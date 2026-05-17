from django.shortcuts import render

def home_view(request):
    selected_age = request.GET.get('age', '')
    return render(request, 'main/home.html', {'selected_age': selected_age})
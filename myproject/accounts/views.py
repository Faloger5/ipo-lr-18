from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.full_name = request.POST.get('full_name', '')
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.delivery_city = request.POST.get('delivery_city', '')
            profile.postal_code = request.POST.get('postal_code', '')
            profile.save()
            
            login(request, user)
            return redirect('catalog')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
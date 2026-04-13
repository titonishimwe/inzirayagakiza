from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'core/home.html')




def sermon(request):
    return render(request,'sermons.html')




def books(request):
    return render(request,'books.html')
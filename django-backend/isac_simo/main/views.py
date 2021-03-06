import os
import subprocess
from importlib import reload
from urllib import request

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.staticfiles.views import serve
from django.core.files.storage import FileSystemStorage
from django.db.models.query import prefetch_related_objects
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from rest_framework.generics import get_object_or_404

import isac_simo.classifier_list as classifier_list
from api.models import Image, ImageFile
from main.authorization import *
from projects.models import Projects

from .forms import (AdminEditForm, AdminRegisterForm, LoginForm, ProfileForm,
                    RegisterForm)
from .models import User


def reload_classifier_list():
    try:
        reload(classifier_list)
    except Exception as e:
        print('--------- [ERROR] FAILED TO RELOAD CLASSIFIER LIST MODULE [ERROR:OOPS] --------')

# HOME PAGE INDEX FOR NORMAL USER
def index(request):
    return render(request, 'index.html')

@login_required
def home(request):
    # reload_classifier_list()
    if(is_admin(request.user)):
        images = Image.objects.order_by('-created_at').all().prefetch_related('image_files')
        image_files_count = ImageFile.objects.filter(tested=True).count()
        user_count = User.objects.all().count()
        project_count = Projects.objects.all().count()
    else:
        images = Image.objects.filter(user_id=request.user.id).order_by('-created_at').prefetch_related('image_files')
        image_files_count = 0
        for image in images:
            image_files_count = image_files_count + image.image_files.all().count()
        user_count = 0
        project_count = 0

    focus_at = ''
    if request.GET.get('focus_at', False):
        focus_at = request.GET.get('focus_at')
    return render(request, 'dashboard.html', {'focus_at':focus_at,'images':images,'user_count':user_count,'image_files_count':image_files_count,'project_count':project_count})

@login_required
def profile(request):
    if request.method == "GET":
        edituser = User.objects.get(id=request.user.id)
        profileform = ProfileForm(instance=edituser)
        return render(request, 'auth/profile.html', {'user': request.user, 'form': profileform})
    elif request.method == "POST":
        updateUser = User.objects.get(id=request.user.id)
        updateUser.email = request.POST.get('email')
        updateUser.full_name = request.POST.get('full_name')

        password1 = request.POST.get('password1') 
        password2 = request.POST.get('password2')

        if request.FILES.get('image'):
            if(updateUser.image != 'user_images/default.png'):
                updateUser.image.delete()
            myFile = request.FILES.get('image')
            updateUser.image = myFile
            # fs = FileSystemStorage(location="mainApp/media/user_images")
            # filename = fs.save(myFile.name, myFile)
            # updateUser.image = 'user_images/'  + myFile.name
        if password1 and password2:
            if password1 != password2:
                messages.error(request, "Password Mismatch")
                return redirect(request.META['HTTP_REFERER'])
            else:
                updateUser.set_password(password1)
        else:
            if password1 or password2:
                messages.error(request, "Fill up password in both the fields")
                return redirect(request.META['HTTP_REFERER'])

        updateUser.save()
        messages.success(request,"User Info Updated Successfully!")
        return redirect("dashboard")

@user_passes_test(is_guest, login_url=dashboard_url)
def login_user(request):
    if request.method == "POST":
        # reload_classifier_list()
        user = authenticate(username = request.POST.get('email'), password = request.POST.get('password'))
        if user is not None:
            if request.POST.get('remember') is not None:    
                request.session.set_expiry(1209600)
            login(request, user)
            return redirect('dashboard')
        else:
            form = LoginForm(request.POST)
            messages.error(request, 'Invalid User Credentials')
            return render(request, 'auth/login.html', {'form':form})
    else:
        if not request.user.is_authenticated:
            if request.GET.get('error') == 'unauthorized':
                messages.error(request, 'Unauthorized Access. Login to Continue.')
            form = LoginForm()
            return render(request, 'auth/login.html', {'form':form})
        else:
            storage = messages.get_messages(request)
            storage.used = True
            if request.GET.get('error') == 'unauthorized':
                messages.error(request, 'Unauthorized Access was denied.')
            return redirect('dashboard')

@user_passes_test(is_guest, login_url=dashboard_url)
def register(request):
    registerForm = RegisterForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if registerForm.is_valid():
            instance = registerForm.save(commit=False)
            instance.set_password(request.POST.get('password1'))
            instance.save()

            storage = messages.get_messages(request)
            storage.used = True
            messages.success(request, 'Registration Success. Login Now.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid Form Request')
    
    if not request.user.is_authenticated:
        return render(request, "auth/register.html", {"form": registerForm})
    else:
        return redirect('dashboard')

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'Logged Out Successfully')
    return redirect('login')

@user_passes_test(is_admin, login_url=login_url)
def list_all_users(request):
    users = User.objects.all().order_by('-active').prefetch_related('projects')
    return render(request, 'users/allusers.html',{'users':users})

# Add Users via Admin Panel Dashboard
@user_passes_test(is_admin, login_url=login_url)
def admin_userAddForm(request, id=0):
    if request.method == "GET":
        if id == 0:
            adminRegisterForm = AdminRegisterForm()
        else:
            edituser = User.objects.get(id=id)
            adminRegisterForm = AdminEditForm(instance=edituser)
        return render(request, "users/admin_register.html", {"form": adminRegisterForm})
    elif request.method == "POST":
        if id == 0:
            form = AdminRegisterForm(request.POST or None, request.FILES or None)

            if form.is_valid():
                instance = form.save(commit=False)
                instance.save()
                form.save_m2m()
                messages.success(request, "User Added Successfully!")
            else:
                return render(request, "users/admin_register.html", {"form": form})
        else:
            updateUser = User.objects.get(id=id)
            updateUser.email = request.POST.get('email')
            updateUser.full_name = request.POST.get('full_name')
            updateUser.user_type = request.POST.get('user_type')
            updateUser.projects.set(Projects.objects.filter(id__in=request.POST.getlist('projects')))

            password1 = request.POST.get('password1') 
            password2 = request.POST.get('password2')

            if request.FILES.get('image'):
                if(updateUser.image != 'user_images/default.png'):
                    updateUser.image.delete()
                myFile = request.FILES.get('image')
                updateUser.image = myFile
                # fs = FileSystemStorage(location="mainApp/media/user_images")
                # filename = fs.save(myFile.name, myFile)
                # updateUser.image = 'user_images/'  + myFile.name
            if password1 and password2:
                if password1 != password2:
                    messages.info(request, "Password Mismatch")
                    return redirect(request.META['HTTP_REFERER'])
                else:
                    updateUser.set_password(password1)
            else:
                if password1 or password2:
                    messages.info(request, "Fill up password in both the fields")
                    return redirect(request.META['HTTP_REFERER'])

            if request.POST.get('active', False):
                updateUser.active = True
            else:
                updateUser.active = False
            updateUser.save()
            messages.info(request,"User Record Updated Successfully for "+updateUser.full_name+"!")

        return redirect("allusers")

# Add Users via Admin Panel Dashboard
@user_passes_test(is_admin, login_url=login_url)
def deleteUserByAdmin(request, id):
    if request.method == "POST":
        user = User.objects.get(id=id)
        if(user.image != 'user_images/default.png'):
            user.image.delete()
        user.delete()
        messages.success(request, 'User Record Deleted Successfully!')
        return redirect('allusers')
    else:
        messages.error(request, 'Failed to Delete!')
        return redirect('allusers')

# Pull From Git Master via Route
def pull(request):
    if os.getenv('PASSWORD', False) and os.getenv('PASSWORD', False) == request.GET.get('password', ''):
        print('pull.sh exists: '+ str(os.path.exists('pull.sh')))
        path = os.path.join('pull.sh')

        if not os.path.exists('pull.sh'):
            path = os.environ.get('PROJECT_FOLDER','') + '/pull.sh'

        print(path)

        subprocess.call(path, shell=True)
        return JsonResponse({'status':'ok'}, status=200)

    print('--~~ PULL FAILED ~~--')
    return JsonResponse({'status':'bad'}, status=404)

# Service Worker js response
def serviceworker(request):
    try:
        saveto = os.path.join('static/js/serviceworker.js')
        if not os.path.exists(saveto):
            saveto = os.environ.get('PROJECT_FOLDER','') + '/static/js/serviceworker.js'

        return HttpResponse(open(saveto), 'application/javascript')
    except Exception as e:
        print(e)
        return render(request, '404.html', status=404)

def offline(request):
    return render(request, 'offline.html')
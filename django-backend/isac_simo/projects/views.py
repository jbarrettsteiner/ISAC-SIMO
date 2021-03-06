from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import user_passes_test
from importlib import reload

from main.authorization import *
from main.models import User

from .forms import ProjectForm
from .models import Projects
import isac_simo.classifier_list as classifier_list

def reload_classifier_list():
    try:
        reload(classifier_list)
    except Exception as e:
        print('--------- [ERROR] FAILED TO RELOAD CLASSIFIER LIST MODULE [ERROR:OOPS] --------')

# View All Projects
@user_passes_test(is_admin, login_url=login_url)
def viewProjects(request):
    projects = Projects.objects.all().order_by('project_name')
    detect_model = classifier_list.detect_object_model_id + ' (Default)'
    return render(request, 'projects.html',{'projects':projects, 'detect_model':detect_model})

# Add Project
@user_passes_test(is_admin, login_url=login_url)
def addProject(request, id = 0):
    if request.method == "GET":
        form = ProjectForm()
        return render(request,"add_project.html",{'form':form})
    elif request.method == "POST":
        form = ProjectForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = User.objects.get(id=request.user.id)
            instance.save()
            reload_classifier_list()
            messages.success(request, "New Project Added Successfully! (Make sure you add Object Types and Classifiers too)")
        else:
            messages.error(request, "Invalid Request")
            return render(request,"add_project.html",{'form':form})
        # if request.FILES.get('image'):
        #     myFile = request.FILES.get('image')
        #     fs = FileSystemStorage(location="main/media/project_images")
        #     filename = fs.save(myFile.name, myFile)
        #     projectform.image = 'project_images/'  + myFile.name    

    return redirect("viewprojects")

# Edit Projects
@user_passes_test(is_admin, login_url=login_url)
def editProject(request, id=0):
    try:
        project = Projects.objects.filter(id=id).prefetch_related('users').get()

        if request.method == "GET":
            form = ProjectForm(instance=project)
            return render(request,"add_project.html",{'form':form, 'project':project})
        elif request.method == "POST":
            form = ProjectForm(request.POST or None, request.FILES or None, instance=project)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.save()
                reload_classifier_list()
                messages.success(request, "Project Updated Successfully!")
            else:
                messages.error(request, "Invalid Request")
                return render(request,"add_project.html",{'form':form, 'project':project})

        return redirect("viewprojects")
    except(Projects.DoesNotExist):
        messages.error(request, "Invalid Project attempted to Edit")
        return redirect("viewprojects")

# Delete Project
@user_passes_test(is_admin, login_url=login_url)
def deleteProject(request, id):
    try:
        if request.method == "POST":
            project = Projects.objects.get(id=id)
            project.image.delete()
            project.delete()
            reload_classifier_list()
            messages.success(request, 'Project Deleted Successfully!')
            return redirect('viewprojects')
        else:
            messages.error(request, 'Failed to Delete!')
            return redirect('viewprojects')
    except(Projects.DoesNotExist):
        messages.error(request, "Invalid Project attempted to Delete")
        return redirect("viewprojects")

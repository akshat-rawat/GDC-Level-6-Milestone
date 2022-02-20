from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.forms import ModelForm, ValidationError
from django.http import HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tasks.models import Task



def cascade(user, priority):
    if Task.objects.filter(deleted=False, completed=False, user=user, priority=priority).exists():
        priorityList = []
        currPriority = priority
        taskList = Task.objects.select_for_update().filter(deleted=False, completed=False, user=user, priority__gte=priority).order_by("priority")
        for task in taskList:
            if task.priority == currPriority:
                task.priority += 1
                currPriority += 1
                priorityList.append(task)
        Task.objects.bulk_update(priorityList, ["priority"])

class PrettyCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "p-2 bg-gray-100 rounded-lg"

class UserSignupView(CreateView):
    form_class = PrettyCreationForm
    template_name = "signup.html"
    success_url = "/user/login"

class PrettyAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "p-2 bg-gray-100 rounded-lg"

class UserLoginView(LoginView):
    form_class = PrettyAuthenticationForm
    template_name = "login.html"

class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)
        
class TaskCreateFrom(ModelForm):
    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) < 3:
            raise ValidationError("Data too small")
        return title.upper()

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields: self.fields[field].widget.attrs["class"] = "p-2 bg-gray-100 rounded-lg"

class GenericTaskDeleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"

class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"

class GenericTaskUpdateView(AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateFrom
    template_name = "task_update.html"
    success_url = "/tasks"

    def form_valid(self, form):
        cascade(self.request.user, form.cleaned_data.get("priority"))
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

class GenericTaskCreateView(AuthorisedTaskManager, CreateView):
    form_class = TaskCreateFrom
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):
        cascade(self.request.user, form.cleaned_data.get("priority"))
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

class GenericTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 5

class GenericTaskCompleteView(AuthorisedTaskManager, ListView):
    queryset = Task.objects.filter(deleted=False, completed=True)
    template_name = "completed.html"
    context_object_name = "tasks"
    paginate_by = 5

class GenericTaskAllView(AuthorisedTaskManager, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "all.html"
    context_object_name = "tasks"
    paginate_by = 5


from rest_framework import viewsets
from api.utils import ReadWriteSerializerMixin
from api.models.tasks import Task
from api.models.projects import Project
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import responses
from rest_framework import status
from rest_framework.exceptions import NotFound


from api.serializers import (
    UserReadSerializer,
    UserWriteSerializer,
    ProjectReadSerializer,
    ProjectWriteSerializer,
    TaskReadSerializer,
    TaskWriteSerializer
)
# Create your views here.


def error404(request, exception):
    raise NotFound()


class UserViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')

    read_serializer_class = UserReadSerializer
    write_serializer_class = UserWriteSerializer


class ProjectViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Project.objects.all()
    read_serializer_class = ProjectReadSerializer
    write_serializer_class = ProjectWriteSerializer


class TaskViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Task.objects.all()
    read_serializer_class = TaskReadSerializer
    write_serializer_class = TaskWriteSerializer

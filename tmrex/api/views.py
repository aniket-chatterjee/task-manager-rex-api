from rest_framework import viewsets
from api.utils import ReadWriteSerializerMixin
from api.models.tasks import Task
from api.models.projects import Project, ProjectUser
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import responses, Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny, SAFE_METHODS
from rest_framework_simplejwt.tokens import RefreshToken

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


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = User.objects.create(
            username=request.data.get('username'),
            email=request.data.get('email'),
            first_name=request.data.get('first_name'),
            last_name=request.data.get('last_name')
        )
        user.set_password(str(request.data.get('password')))
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)


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

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(project_users__user=user)


class TaskViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Task.objects.all()
    read_serializer_class = TaskReadSerializer
    write_serializer_class = TaskWriteSerializer

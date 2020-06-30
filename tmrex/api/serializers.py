from rest_framework import serializers
from django.contrib.auth.models import User
from api.models.projects import Project, ProjectUser
from api.models.tasks import Task, TaskUser, RelatedTask


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'last_login',
            'first_name',
            'last_name',
            'is_staff',
            'date_joined',
            'groups'
        ]


class UserMinReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']


class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
        ]


class ProjectUserSerializer(serializers.ModelSerializer):
    user = UserMinReadSerializer(read_only=True)

    class Meta:
        model = ProjectUser
        fields = ['user', 'access']


class ProjectReadSerializer(serializers.ModelSerializer):
    project_users = ProjectUserSerializer(many=True, read_only=True)
    created_by = UserMinReadSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'state',
            'started_on',
            'ended_on',
            'created_by',
            'project_users',
            'avatar'
        ]


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'created_by',
            'avatar'
        ]


class TaskUserSerializer(serializers.ModelSerializer):
    user = UserMinReadSerializer(read_only=True)

    class Meta:
        model = TaskUser
        fields = ['user', 'access']


class RelatedTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedTask
        fields = ['task_b', 'is_connected_as']


class TaskReadSerializer(serializers.ModelSerializer):
    task_users = TaskUserSerializer(many=True, read_only=True)
    sub_tasks = RelatedTaskSerializer(many=True, read_only=True)
    parent_task = RelatedTaskSerializer(many=True, read_only=True)
    just_related_tasks = RelatedTaskSerializer(many=True, read_only=True)
    blocked_tasks = RelatedTaskSerializer(many=True, read_only=True)
    blocked_by_tasks = RelatedTaskSerializer(many=True, read_only=True)
    assignee = UserMinReadSerializer(read_only=True)
    author = UserMinReadSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'project',
            'author',
            'assignee',
            'estimated_hours',
            'avatar',
            'task_users',
            'sub_tasks',
            'parent_task',
            'just_related_tasks',
            'blocked_tasks',
            'blocked_by_tasks',
        ]


class TaskWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'project',
            'author',
            'assignee',
            'estimated_hours',
            'avatar',
        ]

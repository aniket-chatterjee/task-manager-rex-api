from django.contrib.auth.models import User
from api.models.projects import (
    Project,
    ProjectUser
)


class DefaultUser:
    USER_NAME = 'john'
    EMAIL = 'lennon@thebeatles.com'
    PASSWORD = 'defaultpassword'


class DefaultTask:
    TITLE = 'My precious task'
    DESCRIPTION = 'Some task info'


def create_dummy_project_with_user():
    user = User.objects.create_user(
        DefaultUser.USER_NAME,
        DefaultUser.EMAIL,
        DefaultUser.PASSWORD
    )

    return Project.objects.create(
        user,
        'Project2',
        'Its a small project'
    )

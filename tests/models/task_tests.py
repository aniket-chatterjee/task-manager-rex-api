import pytest
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User
from tests.models.test_helper import create_dummy_project_with_user, DefaultUser
from api.utils import today_as_datetime
from api.exceptions import PermissionDenied
from api.models.projects import (
    Project,
    ProjectUser,
    AvailableAccessTypes
)
from api.models.tasks import (
    Task,
    TaskUser,
    AvailableTaskStates,
    RelatedTask
)


@pytest.mark.django_db(transaction=True)
def test_task_creation_not_allowed_for_guest_project_user():

    project = create_dummy_project_with_user()

    # convert current owner to a guest user
    user = project.owners.first().user
    project.add_guest(user)

    with pytest.raises(PermissionDenied):
        assert Task.objects.create(user, project, "First Task")


@pytest.mark.django_db(transaction=True)
def test_task_can_be_created_by_project_owner():

    project = create_dummy_project_with_user()
    user = project.owners.first().user
    task_title = "First Task"
    task = Task.objects.create(user, project, task_title)
    assert project.task_set.first().title == task_title
    assert project.task_set.first().description is None
    assert project.task_set.first().estimated_hours == 0
    assert project.task_set.first().state == AvailableTaskStates.OPENED


@pytest.mark.django_db(transaction=True)
def test_task_can_be_created_by_project_participant():

    project = create_dummy_project_with_user()
    user = project.owners.first().user
    project.add_participant(user)
    task_title = "First Task"
    task = Task.objects.create(user, project, task_title)
    assert project.task_set.first().title == task_title
    assert project.task_set.first().description is None
    assert project.task_set.first().estimated_hours == 0
    assert project.task_set.first().state == AvailableTaskStates.OPENED


@pytest.mark.django_db(transaction=True)
def test_task_with_estimated_hours():

    project = create_dummy_project_with_user()
    user = project.owners.first().user
    project.add_participant(user)
    task_title = "First Task"
    task = Task.objects.create(user, project, task_title, None, None, 10)

    assert project.task_set.first().estimated_hours == 10


@pytest.mark.django_db(transaction=True)
def test_task_add_assignee():

    project = create_dummy_project_with_user()
    user = project.created_by
    assingee_user = User.objects.create_user(
        'the_assignee',
        'someassignee@mail.com',
        '1assignee'
    )
    task_title = "First Task"
    # assignee should not be present under project user
    assert project.project_users.filter(
        user_id=assingee_user.id).count() == 0
    task = Task.objects.create(user, project, task_title, None, assingee_user)
    assert task.assignee.id == assingee_user.id
    # assignee should be part of task users
    assert task.participants.filter(
        user_id=assingee_user.id).count() == 1

    # assignee should be present under project user as well
    assert project.project_users.filter(
        user_id=assingee_user.id).count() == 1


@pytest.mark.django_db(transaction=True)
def test_task_add_related_task():

    project = create_dummy_project_with_user()
    user = project.owners.first().user
    project.add_participant(user)

    task1_title = "First Task"
    task2_title = "Second Task"
    task1 = Task.objects.create(user, project, task1_title)
    task2 = Task.objects.create(user, project, task2_title)
    task1.add_sub_task(task2)

    assert task1.related_tasks.count() == 1
    print(RelatedTask.objects.first())
    print(RelatedTask.objects.last())
    assert task1.sub_tasks.count() == 1
    assert task1.parent_task.count() == 0
    assert task1.just_related_tasks.count() == 0
    assert task1.blocked_tasks.count() == 0
    assert task1.blocked_by_tasks.count() == 0

    assert task2.related_tasks.count() == 1

    assert task2.sub_tasks.count() == 0
    assert task2.parent_task.count() == 1
    assert task2.just_related_tasks.count() == 0
    assert task2.blocked_tasks.count() == 0
    assert task2.blocked_by_tasks.count() == 0

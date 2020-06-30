import pytest
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User
from tests.models.test_helper import create_dummy_project_with_user, DefaultUser
from api.utils import today_as_datetime
from api.exceptions import InvalidOperation
from api.models.projects import (
    Project,
    ProjectUser,
    AvailableAccessTypes,
    AvailableProjectStates
)


@pytest.mark.django_db(transaction=True)
def test_user_create():
    User.objects.create_user(
        DefaultUser.USER_NAME,
        DefaultUser.EMAIL,
        DefaultUser.PASSWORD
    )
    assert User.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_project_can_not_be_created_without_user():
    created_by = None
    with pytest.raises(Exception):
        assert Project.objects.create(
            created_by,
            'Project1',
            'Its a big project'
        )


@pytest.mark.django_db(transaction=True)
def test_project_create_with_user():

    create_dummy_project_with_user()
    assert Project.objects.count() == 1 and Project.objects.first(
    ).created_by.username == DefaultUser.USER_NAME

    assert Project.objects.first().owners.count() == 1
    assert Project.objects.first().owners.first().user.username == DefaultUser.USER_NAME


@pytest.mark.django_db(transaction=True)
def test_project_add_multiple_owners():

    project = create_dummy_project_with_user()
    project
    new_user = User.objects.create_user(
        'another user', 'email@mail.com', 'password')
    project.add_owner(new_user)
    assert Project.objects.first().owners.count() == 2
    assert Project.objects.first().owners.first().user.username == DefaultUser.USER_NAME


@pytest.mark.django_db(transaction=True)
def test_project_add_guest():

    project = create_dummy_project_with_user()
    project
    new_user = User.objects.create_user(
        'another user', 'email@mail.com', 'password')
    project.add_guest(new_user)
    assert Project.objects.first().owners.count() == 1
    assert Project.objects.first().guests.count() == 1
    assert Project.objects.first().guests.first().user.username == 'another user'


@pytest.mark.django_db(transaction=True)
def test_project_add_participant():

    project = create_dummy_project_with_user()
    project
    new_user = User.objects.create_user(
        'another user', 'email@mail.com', 'password')
    project.add_participant(new_user)
    assert Project.objects.first().owners.count() == 1
    assert Project.objects.first().participants.count() == 1
    assert Project.objects.first().participants.first().user.username == 'another user'


@pytest.mark.django_db(transaction=True)
def test_project_change_owner_to_participant_to_guest_and_back_to_owner():

    project = create_dummy_project_with_user()
    assert Project.objects.first().owners.count() == 1
    assert Project.objects.first().participants.count() == 0
    assert Project.objects.first().guests.count() == 0
    assert Project.objects.first().owners.first().user.username == DefaultUser.USER_NAME

    project.add_participant(project.owners.first().user)
    assert Project.objects.first().owners.count() == 0
    assert Project.objects.first().guests.count() == 0
    assert Project.objects.first().participants.count() == 1
    assert Project.objects.first().participants.first(
    ).user.username == DefaultUser.USER_NAME

    project.add_guest(project.participants.first().user)
    assert Project.objects.first().owners.count() == 0
    assert Project.objects.first().participants.count() == 0
    assert Project.objects.first().guests.count() == 1
    assert Project.objects.first().guests.first(
    ).user.username == DefaultUser.USER_NAME

    project.add_owner(project.guests.first().user)
    assert Project.objects.first().owners.count() == 1
    assert Project.objects.first().participants.count() == 0
    assert Project.objects.first().guests.count() == 0
    assert Project.objects.first().owners.first(
    ).user.username == DefaultUser.USER_NAME


@pytest.mark.django_db(transaction=True)
def test_project_find_user_access():
    project = create_dummy_project_with_user()
    access = project.find_access_for(project.created_by)
    assert access == AvailableAccessTypes.OWNER
    access = project.find_access_for(None)
    assert access is None


@pytest.mark.django_db(transaction=True)
def test_project_remove_user():
    project = create_dummy_project_with_user()
    project.remove_user(project.created_by)
    assert project.project_users.count() == 0


@pytest.mark.django_db(transaction=True)
def test_project_start_without_date():
    project = create_dummy_project_with_user()
    project.start()
    assert Project.objects.first().started_on == today_as_datetime()


@pytest.mark.django_db(transaction=True)
def test_project_start_with_past_date():

    past_project = create_dummy_project_with_user()

    past_date = today_as_datetime() - timedelta(100)
    past_project.start_from(past_date)

    assert Project.objects.first().started_on < today_as_datetime()


@pytest.mark.django_db(transaction=True)
def test_project_start_with_future_date():

    future_project = create_dummy_project_with_user()

    future_date = today_as_datetime() + timedelta(100)
    future_project.start_from(future_date)

    assert Project.objects.first().started_on > today_as_datetime()


@pytest.mark.django_db(transaction=True)
def test_project_should_not_allow_finish_without_startdate():

    past_end_project = create_dummy_project_with_user()
    past_end_date = today_as_datetime() - timedelta(100)
    with pytest.raises(InvalidOperation):
        assert past_end_project.end_on(past_end_date)


@pytest.mark.django_db(transaction=True)
def test_project_should_not_allow_finish_before_startdate():

    past_end_project = create_dummy_project_with_user()
    past_end_date = today_as_datetime() - timedelta(2)

    past_end_project.start()
    with pytest.raises(InvalidOperation):
        assert past_end_project.end_on(past_end_date)


@pytest.mark.django_db(transaction=True)
def test_project_update_title():

    project = create_dummy_project_with_user()
    old_title = project.title
    new_title = "Idnetity crisis"
    project.update_title(new_title)
    # just to confirm that it was saved properly
    fresh_copy_from_db = Project.objects.first()
    assert fresh_copy_from_db.title != old_title and fresh_copy_from_db.title == new_title


@pytest.mark.django_db(transaction=True)
def test_project_update_description():

    project = create_dummy_project_with_user()
    old_description = project.description
    new_description = """
    Every time that I look in the mirror
    All these lines on my face gettin' clearer
    """
    project.update_description(new_description)
    # just to confirm that it was saved properly
    fresh_copy_from_db = Project.objects.first()
    assert fresh_copy_from_db.description != old_description and fresh_copy_from_db.description == new_description


@pytest.mark.django_db(transaction=True)
def test_project_deactivate():

    project = create_dummy_project_with_user()
    previous_status = project.state
    project.deactivate()

    # just to confirm that it was saved properly
    fresh_copy_from_db = Project.objects.first()
    assert fresh_copy_from_db.state != previous_status and project.state == AvailableProjectStates.INACTIVE


@pytest.mark.django_db(transaction=True)
def test_project_should_not_be_dactivated_if_already_inactive():

    project = create_dummy_project_with_user()
    project.deactivate()
    with pytest.raises(InvalidOperation):
        assert project.deactivate()


@pytest.mark.django_db(transaction=True)
def test_project_should_not_be_activated_if_already_active():

    project = create_dummy_project_with_user()
    with pytest.raises(InvalidOperation):
        assert project.activate()


@pytest.mark.django_db(transaction=True)
def test_project_archive():

    project = create_dummy_project_with_user()
    previous_archived_status = project.state
    project.archive()

    # just to confirm that it was saved properly
    fresh_copy_from_db = Project.objects.first()
    assert fresh_copy_from_db.state != previous_archived_status and project.state == AvailableProjectStates.ARCHIVED


@pytest.mark.django_db(transaction=True)
def test_project_should_not_be_darchived_if_already_unarchived():

    project = create_dummy_project_with_user()
    with pytest.raises(InvalidOperation):
        assert project.unarchive()


@pytest.mark.django_db(transaction=True)
def test_project_should_not_be_archived_if_already_archived():

    project = create_dummy_project_with_user()
    project.archive()
    with pytest.raises(ValueError):
        assert project.archive()


@pytest.mark.django_db(transaction=True)
def test_project_unarchive():

    project = create_dummy_project_with_user()
    project.archive()
    previous_archived_status = project.state
    project.unarchive()
    # just to confirm that it was saved properly
    fresh_copy_from_db = Project.objects.first()

    assert fresh_copy_from_db.state != previous_archived_status and fresh_copy_from_db.state == AvailableProjectStates.INACTIVE

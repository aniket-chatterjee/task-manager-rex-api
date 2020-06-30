from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from api.utils import today_as_datetime
from datetime import date, datetime
from api.exceptions import InvalidOperation
# Create your models here.
PROJECT_MODEL = "api.Project"


class AvailableProjectStates(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Project is at ACTIVE state')
    INACTIVE = 'INACTIVE', _('Project is INACTIVE ')
    ARCHIVED = 'ARCHIVED', _('Project has been archived')


class AvailableAccessTypes(models.TextChoices):
    OWNER = 'OWNER', _('Owner')
    PARTICIPANT = 'PARTICIPANT', _('Participant')
    GUEST = 'GUEST', _('Guest')


class ProjectActions(models.TextChoices):
    REMOVE_PROJECT_USER = 'REMOVE_PROJECT_USER', _(
        'can remove any project user')
    ADD_OWNER = 'ADD_OWNER', _('can add project owners')
    ADD_PARTICIPANT = 'ADD_GUEST', _('can add project participants')
    ADD_GUEST = 'ADD_PARTICIPANT', _('can add project guests')
    ACTIVATE_PROJECT = 'ACTIVATE_PROJECT', _('Activate project')
    DEACTIVATE_PROJECT = 'DEACTIVATE_PROJECT', _('Deativate project')
    ARCHIVE_PROJECT = 'ARCHIVE_PROJECT', _('Archive project')
    UNARCHIVE_PROJECT = 'UNARCHIVE_PROJECT', _('Unarchive project')
    ADD_TASK = 'ADD_TASK', _('Can a task in the project')
    VIEW_PROJECT_DETAILS = 'VIEW_PROJECT_DETAILS', _(
        'Can see project details')
    VIEW_TASKS = 'VIEW_TASK', _('Can see tasks under current project')


class ProjectAccess:
    PROJECT_PERMISSIONS = {
        AvailableAccessTypes.OWNER: list([
            ProjectActions.REMOVE_PROJECT_USER,
            ProjectActions.ADD_OWNER,
            ProjectActions.ADD_PARTICIPANT,
            ProjectActions.ADD_GUEST,
            ProjectActions.ACTIVATE_PROJECT,
            ProjectActions.DEACTIVATE_PROJECT,
            ProjectActions.ARCHIVE_PROJECT,
            ProjectActions.UNARCHIVE_PROJECT,
            ProjectActions.ADD_TASK,
            ProjectActions.VIEW_PROJECT_DETAILS,
            ProjectActions.VIEW_TASKS
        ]),
        AvailableAccessTypes.PARTICIPANT: list([
            ProjectActions.VIEW_PROJECT_DETAILS,
            ProjectActions.ADD_PARTICIPANT,
            ProjectActions.ADD_GUEST,
            ProjectActions.ADD_TASK,
            ProjectActions.VIEW_TASKS
        ]),
        AvailableAccessTypes.GUEST: list([
            ProjectActions.VIEW_PROJECT_DETAILS,
            ProjectActions.VIEW_TASKS
        ])
    }


class ProjectUserManager(models.Manager):
    def find_user(self, project: PROJECT_MODEL, user: User):
        return self.filter(user=user).filter(project=project).first()

    def add_project_user(self, project: PROJECT_MODEL, user: User, access: AvailableAccessTypes):
        """
        add project user to a project with proper access type also help to change existing user role
        (noticed this feature in gitlab)
        if user already exists as a project user then only the access type will change  
        """
        project_user = self.find_user(project, user)

        if not project_user:
            # Create a new one
            project_user = self.model(
                project=project,
                user=user,
            )

        project_user.access = access
        project_user.save(using=self._db)
        return project_user

    def add_owner(self, project: PROJECT_MODEL, user: User):
        return self.add_project_user(project, user, AvailableAccessTypes.OWNER)

    def add_guest(self, project: PROJECT_MODEL, user: User):
        return self.add_project_user(project, user, AvailableAccessTypes.GUEST)

    def add_participant(self, project: PROJECT_MODEL, user: User):
        return self.add_project_user(project, user, AvailableAccessTypes.PARTICIPANT)

    def remove(self,  project: PROJECT_MODEL, user: User):
        project_user = self.find_user(project, user)

        if not project_user:
            raise InvalidOperation("invalid user")

        project_user.delete()


class ProjectUser(models.Model):
    special_manager = ProjectUserManager()
    objects = ProjectUserManager()

    project = models.ForeignKey(
        PROJECT_MODEL,
        on_delete=models.CASCADE,
        related_name='project_users'
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access = models.TextField(
        _("Access to Project"),
        choices=AvailableAccessTypes.choices,
        default=AvailableAccessTypes.GUEST
    )

    class Meta:
        base_manager_name = 'special_manager'


class ProjectManager(models.Manager):
    # def create(self, **validated_data):
    #     project = self.model(**validated_data)
    #     project.save()
    #     return project

    def create(
        self,
        created_by: User,
        title: str,
        description: str = None,
        avatar=None
    ):
        """
        Thought creating and saving project objects from within a manager. This would give us some
        extra flexibility as well a good way for separation of concerns
        """
        if not title:
            raise ValueError(
                'We could just go ahead and create a project without title, but it wont be a good idea. would it?')

        if not created_by:
            raise ValueError(
                'Unlike all things, this project was actually created by someone, wasn\'t it?'
            )

        project = self.model(
            title=title,
            description=description,
            created_by=created_by,
            avatar=avatar
        )

        project.save(using=self._db)
        project.add_owner(created_by)
        return project


class Project(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()
    started_on = models.DateTimeField(
        _("Porject started on "),
        auto_now=False,
        auto_now_add=False,
        null=True
    )
    state = models.CharField(
        _("Project state, Active, inactive etc"),
        choices=AvailableProjectStates.choices,
        default=AvailableProjectStates.ACTIVE,
        max_length=50
    )
    ended_on = models.DateTimeField(
        _("Project ended on"),
        auto_now=False,
        auto_now_add=False,
        null=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_by_%(class)s'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_by_%(class)s'
    )

    avatar = models.ImageField(
        _("Project Avatar"),
        upload_to="project",
        height_field=None,
        width_field=None,
        max_length=1024
    )

    objects = ProjectManager()

    @property
    def owners(self):
        return self.project_users.filter(access=AvailableAccessTypes.OWNER).all()

    @property
    def guests(self):
        return self.project_users.filter(access=AvailableAccessTypes.GUEST).all()

    @property
    def participants(self):
        return self.project_users.filter(access=AvailableAccessTypes.PARTICIPANT).all()

    def update_description(self, description: str):
        self.description = description
        self.save()

    def update_title(self, title: str):
        self.title = title
        self.save()

    def activate(self):
        if self.state == AvailableProjectStates.ACTIVE:
            raise InvalidOperation(
                "Why would you wan't to activate an already activated project!!"
            )

        if self.state == AvailableProjectStates.ARCHIVED:
            raise InvalidOperation(
                "Why would you wan't to activate an already activated project!!"
            )
        self.state = AvailableProjectStates.ACTIVE
        self.save()

    def deactivate(self):
        if self.state != AvailableProjectStates.ACTIVE:
            raise InvalidOperation(
                "You can not deactivate this project"
            )
        self.state = AvailableProjectStates.INACTIVE
        self.save()

    def archive(self):
        if self.state == AvailableProjectStates.ARCHIVED:

            raise ValueError(
                "Common! you have already archived it once!"
            )
        self.state = AvailableProjectStates.ARCHIVED
        self.save()

    def unarchive(self):
        if self.state != AvailableProjectStates.ARCHIVED:
            raise InvalidOperation(
                "Lazarus pit only works on dead people. Unarchive it first"
            )
        # After unarchival lets take to project to Inactive state
        self.state = AvailableProjectStates.INACTIVE
        self.save()

    def start(self):
        """
        if No date has been provided then start from today
        """
        self.start_from(today_as_datetime())

    def start_from(self, _from: datetime):
        """
        We should allow user to set date time to an older date or in future.
        from a usecase standpoint that is something any project mananger would want, to plan ahead or
        migrate existing running projects
        """

        self.started_on = _from
        self.save()

    def end(self, end_date: datetime):
        """
        if No end_date has been provided then finsh on today
        """
        self.end_on(today_as_datetime())

    def end_on(self, _on: datetime):
        """
        We should allow user to set end date time to an older date or in future
        the only constrain we should add is that the end date can not be before start date
        and of course the project has to have a start date
        """
        if not self.started_on or self.started_on is None:
            raise InvalidOperation(
                "Its may be alright to you to finish something without even starting it, But not to us ;)"
            )

        elif self.started_on > _on:
            raise InvalidOperation(
                """
                you haven't fully grasped the 
                concept of time, have you? but again, who has!
                """
            )
        self.ended_on = _on
        self.save()

    def add_owner(self, user):
        self.project_users.add_owner(self, user)

    def add_guest(self, user):
        self.project_users.add_guest(self, user)

    def add_participant(self, user):
        self.project_users.add_participant(self, user)

    def remove_user(self, user):
        self.project_users.remove(self, user)

    def find_access_for(self, user):
        project_user = self.project_users.find_user(self, user)

        if not project_user:
            return None
        else:
            return project_user.access

    def has_access(self, user: User, action: str):
        access = self.find_access_for(user)
        if access is None:
            return False
        return action in ProjectAccess.PROJECT_PERMISSIONS[access]

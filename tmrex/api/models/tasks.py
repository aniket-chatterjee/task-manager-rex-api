
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from api.utils import today_as_datetime
from datetime import date, datetime
from api.exceptions import PermissionDenied, InvalidOperation
from api.models.projects import AvailableAccessTypes, ProjectActions

PROJECT_MODEL = "api.Project"
TASK_MODEL = "api.Task"
LABEL_MODEL = "api.Label"
RELATED_TASK_MODEL = "api.RelatedTask"
TASK_USER_MODEL = "api.TaskUser"


class AvailableTaskRelations(models.TextChoices):
    PARENT_TASK_OF = 'PARENT_TASK_OF', _('Parent task')
    SUB_TASK_OF = 'SUB_TASK_OF', _('Sub task')
    BLOCKED_BY = 'BLOCKED_BY', _('BlockedBy')
    IS_BLOCKING = 'IS_BLOCKING', _('IsBlocking')
    JUST_RELATED = 'RELATED_TASK', _('Just related')


class Relationships:
    MAP = {
        AvailableTaskRelations.PARENT_TASK_OF: AvailableTaskRelations.SUB_TASK_OF,
        AvailableTaskRelations.SUB_TASK_OF: AvailableTaskRelations.PARENT_TASK_OF,
        AvailableTaskRelations.BLOCKED_BY: AvailableTaskRelations.IS_BLOCKING,
        AvailableTaskRelations.IS_BLOCKING: AvailableTaskRelations.BLOCKED_BY,
        AvailableTaskRelations.JUST_RELATED: AvailableTaskRelations.JUST_RELATED
    }


class AvailableTaskStates(models.TextChoices):
    OPENED = 'OPENED', _('Task is at opened state')
    BLOCKED = 'BLOCKED', _('task is blocked by some task')
    CLOSED = 'CLOSED', _('completed/closed ')
    ARCHIVED = 'ARCHIVED', _('task has been archived')
    REVIEW_PENDING = 'REVIEW_PENDING', _('requires a review')


class TaskUserManager(models.Manager):
    def find_user(self, task: TASK_MODEL, user: User):
        return self.filter(user=user).filter(task=task).first()

    def add_task_user(self, task: TASK_MODEL, user: User, access: AvailableAccessTypes):
        """
        add task user to a task with proper access type also help to change existing user role
        (noticed this feature in gitlab)
        if user already exists as a task user then only the access type will change
        """
        task_user = self.find_user(task, user)

        if not task_user:
            # check if project user exists
            project_access = task.project.find_access_for(user)
            if not project_access:
                task.project.add_participant(user)

            # Create a new one
            task_user = self.model(
                task=task,
                user=user
            )

        task_user.access = access
        task_user.save(using=self._db)
        return task_user

    def add_owner(self, task: TASK_MODEL, user: User):
        return self.add_task_user(task, user, AvailableAccessTypes.OWNER)

    def add_guest(self, task: TASK_MODEL, user: User):
        return self.add_task_user(task, user, AvailableAccessTypes.GUEST)

    def add_participant(self, task: TASK_MODEL, user: User):
        return self.add_task_user(task, user, AvailableAccessTypes.PARTICIPANT)

    def remove(self,  task: TASK_MODEL, user: User):
        task_user = self.find_user(task, user)

        if not task_user:
            raise InvalidOperation("invalid user")

        task_user.delete()


class TaskManager(models.Manager):
    def create(
        self,
        author: User,
        project: PROJECT_MODEL,
        title: str,
        description: str = None,
        assignee: User = None,
        estimated_hours: int = 0,
        avatar=None
    ):
        if not project.has_access(author, ProjectActions.ADD_TASK):
            raise PermissionDenied()

        task = self.model(
            author=author,
            project=project,
            title=title,
            description=description,
            estimated_hours=estimated_hours,
            assignee=assignee,
            avatar=avatar
        )
        task.save(using=self._db)
        task.add_owner(author)

        if assignee is not None and assignee != author:
            task.add_participant(assignee)

        return task


class Label(models.Model):
    name = models.CharField(max_length=255)
    hex_color = models.CharField(max_length=6)


class Task(models.Model):
    """
        There are a lot of things common with project, mainly the project user and task user part.
        should wait till another such class/module comes(the sacred rule of 3 :D) and then may be a permission
        mixin will make more sense here
    """
    title = models.CharField(_("task title"), max_length=255)
    description = models.TextField(_("task description"), null=True)
    estimated_hours = models.IntegerField("estimated hours", default=0)
    hours_spent = models.IntegerField(_("hours spent on the task"), default=0)
    started_on = models.DateTimeField(
        _("store last start datetime"),
        auto_now=False,
        auto_now_add=False,
        null=True
    )
    ended_on = models.DateTimeField(
        _("store last end datetime"),
        auto_now=False,
        auto_now_add=False,
        null=True
    )
    due_on = models.DateTimeField(
        _("Task due date, if any"),
        auto_now=False,
        auto_now_add=False,
        null=True
    )
    state = models.CharField(
        _("TaskState, like Open,closed, blocked, archived, based on project may be"),
        choices=AvailableTaskStates.choices,
        default=AvailableTaskStates.OPENED,
        max_length=50
    )
    project = models.ForeignKey(
        PROJECT_MODEL,
        verbose_name=_(""),
        on_delete=models.CASCADE
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignee_%(class)s'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='author_%(class)s'
    )

    related_tasks = models.ManyToManyField(
        'self',
        verbose_name=_("related tasks"),
        through=RELATED_TASK_MODEL,
        symmetrical=False,
        related_name='related_tasks+'
    )
    avatar = models.ImageField(
        _("Task Avatar"),
        upload_to="task",
        height_field=None,
        width_field=None,
        max_length=1024
    )
    objects = TaskManager()

    @property
    def owners(self):
        return self.task_users.filter(access=AvailableAccessTypes.OWNER).all()

    @property
    def guests(self):
        return self.task_users.filter(access=AvailableAccessTypes.GUEST).all()

    @property
    def participants(self):
        return self.task_users.filter(access=AvailableAccessTypes.PARTICIPANT).all()

    @property
    def sub_tasks(self):
        return self.related_tasks.filter(task_b__is_connected_as=AvailableTaskRelations.PARENT_TASK_OF).all()

    @property
    def parent_task(self):
        return self.related_tasks.filter(task_b__is_connected_as=AvailableTaskRelations.SUB_TASK_OF).all()

    @property
    def just_related_tasks(self):
        return self.related_tasks.filter(task_b__is_connected_as=AvailableTaskRelations.JUST_RELATED).all()

    @property
    def blocked_tasks(self):
        return self.related_tasks.filter(task_b__is_connected_as=AvailableTaskRelations.IS_BLOCKING).all()

    @property
    def blocked_by_tasks(self):
        return self.related_tasks.filter(task_b__is_connected_as=AvailableTaskRelations.BLOCKED_BY).all()

    def add_owner(self, user):
        self.task_users.add_owner(self, user)

    def add_participant(self, user):
        self.task_users.add_participant(self, user)

    def add_guest(self, user):
        self.task_users.add_guest(self, user)

    def update_description(self, description: str):
        self.description = description
        self.save()

    def update_title(self, title: str):
        self.title = title
        self.save()

    def block(self):
        if self.state == AvailableTaskStates.BLOCKED or self.state == AvailableTaskStates.CLOSED:
            raise InvlidOperation(
                "Can not block this task"
            )
        self.state = AvailableTaskStates.OPENED
        self.save()

    def unblock(self):
        if self.state != AvailableTaskStates.BLOCKED:
            raise InvlidOperation(
                "Sorry! can't do it, task isn't blocked"
            )
        self.state = AvailableTaskStates.OPENED
        self.save()

    def archive(self):
        if self.state == AvailableTaskStates.ARCHIVED:
            raise ValueError(
                "Task is already archived"
            )
        # After unarchival lets take to project to Inactive state
        self.state = AvailableTaskStates.ARCHIVED
        self.save()

    def unarchive(self):
        if self.state != AvailableTaskStates.ARCHIVED:
            raise ValueError(
                "This task is not archived to begin with"
            )

        self.state = AvailableTaskStates.INACTIVE
        self.save()

    def is_blocked(self):
        self.relatedtasks

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
            raise ValueError(
                "Its may be alright to you to finish something without even starting it, But not to us ;)"
            )

        elif self.started_on > _on:
            raise ValueError(
                """
                you haven't fully grasped the
                concept of time, have you? but again, who has!
                """
            )
        self.ended_on = _on
        self.save()

    def remove_user(self, user):
        self.task_users.remove(self, user)

    def find_access_for(self, user):
        task_user = self.task_users.find_user(self, user)

        if not task_user:
            return None
        else:
            return task_user.access

    def has_access(self, user: User, action: str):
        access = self.find_access_for(user)
        if access is None:
            return False
        return action in TaskAccess.PROJECT_PERMISSIONS[access]

    def add_sub_task(self, task: TASK_MODEL):
        rel_task = self.add_related_task(
            task,
            AvailableTaskRelations.PARENT_TASK_OF
        )

    def add_parent_task(self, task: TASK_MODEL):
        rel_task = self.add_related_task(
            task,
            AvailableTaskRelations.SUB_TASK_OF
        )

    def add_related_task(self, task: TASK_MODEL):
        rel_task = self.add_related_task(
            task,
            AvailableTaskRelations.JUST_RELATED
        )

    def is_blocked_by(self, task: TASK_MODEL):
        rel_task = self.add_related_task(
            task,
            AvailableTaskRelations.BLOCKED_BY
        )

    def is_blocking(self, task: TASK_MODEL):
        rel_task = self.add_related_task(
            task,
            AvailableTaskRelations.BLOCKED_BY
        )

    def add_related_task(self, other_task, rel: str, symm=True):
        related_task, created = RelatedTask.objects.get_or_create(
            task_a=self,
            task_b=other_task,
            is_connected_as=rel)
        if symm:
            # avoid recursion by passing `symm=False`
            other_task.add_related_task(
                self,
                Relationships.MAP.get(rel),
                False
            )
        return related_task

    def remove_related_task(self, task, rel, symm=True):
        RelatedTask.objects.filter(
            task_a=self,
            task_b=task,
            is_connected_as=rel
        ).delete()
        if symm:
            # avoid recursion by passing `symm=False`
            task.remove_related_task(
                self,
                Relationships.MAP.get(rel),
                False
            )


class RelatedTask(models.Model):
    task_a = models.ForeignKey(
        TASK_MODEL,
        on_delete=models.CASCADE,
        related_name="task_a"
    )
    is_connected_as = models.TextField(
        max_length=128,
        choices=AvailableTaskRelations.choices
    )
    task_b = models.ForeignKey(
        TASK_MODEL,
        on_delete=models.CASCADE,
        related_name="task_b"
    )


class TaskUser(models.Model):
    task = models.ForeignKey(
        TASK_MODEL,
        on_delete=models.CASCADE,
        related_name='task_users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    access = models.TextField(
        _("Access to Task"),
        choices=AvailableAccessTypes.choices,
        default=AvailableAccessTypes.GUEST
    )

    objects = TaskUserManager()
    special_manager = TaskUserManager()

    class Meta:
        base_manager_name = 'special_manager'

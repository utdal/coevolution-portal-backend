from django.utils import timezone
import celery
import uuid
import functools

from .models import User, APITaskMeta


class APITaskBase(celery.Task):
    # Helper base class for tasks called from the API
    # - Creates an APITaskMeta and updates its status
    # - Allows passing progress messages and percent back
    # * Tasks should take basic types or model keys as input
    # * Tasks should save results in database and return nothing

    def start(self, *args, user=None, **kwargs):
        self._user_id = user.id
        self._task_id = str(uuid.uuid4())

        task = APITaskMeta.objects.create(
            id=self._task_id, user=user, name=self.name, state="PENDING"
        )

        self.apply_async(args, kwargs, task_id=self._task_id)

        return task

    def get_task_id(self):
        try:
            return self._task_id
        except AttributeError:
            return self.request.id

    def get_task(self):
        return APITaskMeta.objects.get(id=self.get_task_id())

    def get_user_id(self):
        try:
            return self._user_id
        except AttributeError:
            return APITaskMeta.objects.get(id=self.get_task_id()).user.id

    def get_user(self):
        return User.objects.get(id=self.get_user_id())

    def update_task_status(self):
        task = APITaskMeta.objects.get(id=self.get_task_id())
        result = self.AsyncResult(self.get_task_id())
        task.state = result.state

        if result.state == "SUCCESS":
            task.time_ended = timezone.now()
            task.successful = True
            task.percent = 100

        if result.state == "FAILURE":
            task.time_ended = timezone.now()
            task.successful = False

        task.save()

    def before_start(self, task_id, args, kwargs):
        self.update_task_status()
        return super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self.update_task_status()
        return super().after_return(status, retval, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        self.update_task_status()
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def set_progress(self, message=None, percent=None):
        task_meta = APITaskMeta.objects.get(id=self.get_task_id())

        if message is not None:
            task_meta.message = message
        if percent is not None:
            task_meta.percent = percent
        task_meta.save()


def handles_prereqs(fcn):
    @functools.wraps(fcn)
    def wrapper(*args, prereqs=None, **kwargs):
        if prereqs:
            for task_id in prereqs:
                celery.current_app.AsyncResult(str(task_id)).get(
                    disable_sync_subtasks=False  # Not recommended! Not sure a better way..
                )
        fcn(*args, **kwargs)

    return wrapper

import sched
import time
import datetime
import threading
import logging

class UpdateScheduler:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        self.__next_tasks = {}
        self.__next_absolute_tasks = {}
        self.__task_diagnostic = {}
        self.__absolute_task_diagnostic = {}
        self.__worker = threading.Thread(target=self.__scheduler.run)
    def add_task(self, interval, task_obj):
        self.__logger.debug('Add task {0} with poll period of {1} seconds'.format(type(task_obj).__name__, interval))
        self.__update_task(interval, task_obj)
    def add_task_absolute(self, due_time, task_obj):
        self.__logger.debug('Add task {0} at time {1}'.format(type(task_obj).__name__, due_time))
        due_datetime = datetime.datetime.combine(datetime.date.today(), due_time)
        if due_datetime < datetime.datetime.now():
            due_datetime = due_datetime + datetime.timedelta(days=1)
        self.__update_absolute_task(due_datetime, task_obj)
    def __update_task(self, interval, task_obj):
        event = self.__scheduler.enter(interval, 1, self.__update_task, (interval, task_obj))
        self.__next_tasks[task_obj] = event
        try:
            task_obj.update()
            self.__task_diagnostic[type(task_obj).__name__] = True
        except Exception as ex:
            self.__logger.error('Fail to update {0} with error {1}'.format(type(task_obj).__name__, ex))
            self.__logger.exception(ex)
            self.__task_diagnostic[type(task_obj).__name__] = False
    def __update_absolute_task(self, due_datetime, task_obj):
        next_due_datetime = due_datetime + datetime.timedelta(days=1)
        event = self.__scheduler.enterabs(due_datetime.timestamp(), 1, self.__update_absolute_task, (next_due_datetime, task_obj))
        self.__next_absolute_tasks[task_obj] = event
        try:
            task_obj.update()
            self.__absolute_task_diagnostic[type(task_obj).__name__] = True
        except Exception as ex:
            self.__logger.error('Fail to update {0} with error {1}'.format(type(task_obj).__name__, ex))
            self.__logger.exception(ex)
            self.__absolute_task_diagnostic[type(task_obj).__name__] = False
    @property
    def task_diagnostic(self):
        return self.__task_diagnostic
    @property
    def absolute_task_diagnostic(self):
        return self.__absolute_task_diagnostic
    def start(self):
        self.__worker.start()
        self.__logger.debug('{0} started'.format(UpdateScheduler.__name__))
    def stop(self):
        self.__logger.debug('Stopping {0}'.format(UpdateScheduler.__name__))
        for e in self.__next_tasks.values():
            try:
                self.__scheduler.cancel(e)
            finally:
                pass
        self.__next_tasks.clear()
        for e in self.__next_absolute_tasks.values():
            try:
                self.__scheduler.cancel(e)
            finally:
                pass
        self.__next_absolute_tasks.clear()
        self.__worker.join()
        self.__logger.debug('{0} stopped'.format(UpdateScheduler.__name__))
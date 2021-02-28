import sched
import time
import threading
import logging

class UpdateScheduler:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        self.__next_tasks = {}
        self.__worker = threading.Thread(target=self.__scheduler.run)
    def add_task(self, interval, task_obj):
        self.__logger.debug('Add task {0} with poll period of {1} seconds'.format(type(task_obj).__name__, interval))
        self.__update_task(interval, task_obj)
    def __update_task(self, interval, task_obj):
        event = self.__scheduler.enter(interval, 1, self.__update_task, (interval, task_obj))
        self.__next_tasks[task_obj] = event
        try:
            task_obj.update()
        except Exception as ex:
            self.__logger.error('Fail to update {0} with error {1}'.format(type(task_obj).__name__, ex))
            self.__logger.exception(ex)
    def start(self):
        self.__worker.start()
        self.__logger.debug('{0} started'.format(UpdateScheduler.__name__))
    def stop(self):
        self.__logger.debug('Stopping {0}'.format(UpdateScheduler.__name__))
        for e in self.__next_tasks.values():
            try:
                self.__scheduler.cancel(e)
            finally:
                pass #if event is not present do nothing
        self.__next_tasks.clear()
        self.__worker.join()
        self.__logger.debug('{0} stopped'.format(UpdateScheduler.__name__))
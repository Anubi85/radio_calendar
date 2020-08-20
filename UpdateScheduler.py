import sched
import time
import threading

class UpdateScheduler:
    def __init__(self):
        self.__scheduler = sched.scheduler(time.time, time.sleep)
        self.__next_tasks = {}
        self.__worker = threading.Thread(target=self.__scheduler.run)
    def add_task(self, interval, task_obj):
        self.__update_task(interval, task_obj)
    def __update_task(self, interval, task_obj):
        event = self.__scheduler.enter(interval, 1, self.__update_task, (interval, task_obj))
        self.__next_tasks[task_obj] = event
        task_obj.update()
    def start(self):
        self.__worker.start()
    def stop(self):
        for e in self.__next_tasks.values():
            try:
                self.__scheduler.cancel(e)
            finally:
                pass #if event is not present do nothing
        self.__next_tasks.clear()
        self.__worker.join()
import falcon
import json
import logging

class UpdateSchedulerApiController:
    def __init__(self, update_scheduler):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__update_scheduler = update_scheduler

#/diagnostic
    def on_get_diagnostic(self, req, resp):
        self.__logger.debug('GET request on /diagnostic endpoint received')
        task_diagnostic = self.__update_scheduler.task_diagnostic
        absolute_task_diagnostoc = self.__update_scheduler.absolute_task_diagnostic
        diagnostic = {'polling-tasks': task_diagnostic, 'absolute-tasks': absolute_task_diagnostoc}
        resp.body = json.dumps(diagnostic)
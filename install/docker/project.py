"""Deployment hooks and shared modelOne account authentication."""
from myapp.auth import ModelOneAuthDBView as Myauthdbview

# 推送资源申请消息
def push_resource_apply(notebook_id=None,pipeline_id=None,task_id=None,service_id=None,**kwargs):
    from myapp.models.model_job import Task,Pipeline
    from myapp.models.model_notebook import Notebook
    from myapp.models.model_serving import InferenceService

    pass

# 推送资源审批消息
def push_resource_approve(notebook_id=None,pipeline_id=None,task_id=None,service_id=None,**kwargs):
    from myapp.models.model_job import Task,Pipeline
    from myapp.models.model_notebook import Notebook
    from myapp.models.model_serving import InferenceService

    pass

# 推送给管理员消息的函数
def push_admin(message):
    pass


# 推送消息给用户的函数
def push_message(receivers, message, link=None):
    pass

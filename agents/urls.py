from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("workspace/", views.workspace, name="workspace"),
    path("list/", views.agent_list, name="agent_list"),
    path("generate-plan/", views.generate_plan, name="generate_plan"),
    path("plans/<int:plan_id>/approve/", views.approve_plan, name="approve_plan"),
    path("plans/<int:plan_id>/create-payment/", views.create_payment, name="create_payment"),
    path("plans/<int:plan_id>/capture-payment/", views.capture_payment, name="capture_payment"),
    path("plans/<int:plan_id>/execute/", views.execute_plan, name="execute_plan"),
    path("plans/<int:plan_id>/tasks/<int:task_number>/download/", views.download_deliverable, name="download_deliverable"),
    path("paypal/return/", views.paypal_return, name="paypal_return"),
    path("paypal/cancel/", views.paypal_cancel, name="paypal_cancel"),
]

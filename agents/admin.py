from django.contrib import admin

from .models import Agent, Payment, TaskPlan


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "capability", "price", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "capability")


@admin.register(TaskPlan)
class TaskPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "project_summary", "total_cost", "currency", "status", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("user_request", "project_summary")
    readonly_fields = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("paypal_order_id", "capture_id")
    readonly_fields = ("paypal_order_id", "capture_id", "created_at", "updated_at")


from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    capability = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TaskPlan(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user_request = models.TextField()
    project_summary = models.TextField()
    tasks = models.JSONField()

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    currency = models.CharField(
        max_length=3,
        default="USD"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan #{self.id} - {self.status}"

class Payment(models.Model):

    STATUS_CHOICES = [
        ("CREATED", "Created"),
        ("APPROVED", "Approved"),
        ("CAPTURED", "Captured"),
        ("FAILED", "Failed"),
    ]

    plan = models.ForeignKey(
        TaskPlan,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    paypal_order_id = models.CharField(
        max_length=100,
        unique=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3,
        default="USD"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CREATED"
    )

    capture_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Plan #{self.plan_id} - {self.status}"

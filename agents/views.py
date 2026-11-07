import json
import logging
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse, HttpResponse
from django.utils.text import slugify
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Agent, TaskPlan, Payment
from .services.planner import create_plan
from .services.executor import execute_task
from .services.paypal_orders import create_paypal_order
from .services.paypal_client import capture_paypal_order, get_paypal_order

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "agents/home.html")


def workspace(request):
    return render(request, "agents/workspace.html")


def agent_list(request):
    agents = Agent.objects.filter(is_active=True).order_by("name")
    return JsonResponse({
        "agents": [{
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "capability": agent.capability,
            "price": str(agent.price),
            "currency": "USD",
        } for agent in agents],
        "total_agents": agents.count(),
    })


@require_POST
def generate_plan(request):
    try:
        data = json.loads(request.body or "{}")
        if not isinstance(data, dict):
            return JsonResponse({"error": "Invalid request format."}, status=400)

        title = data.get("title")
        description = data.get("description")
        if not isinstance(title, str) or not isinstance(description, str):
            return JsonResponse({"error": "Title and description must be text."}, status=400)

        title, description = title.strip(), description.strip()
        if not title or not description:
            return JsonResponse({"error": "Project title and description are required."}, status=400)
        if len(title) > 120 or len(description) > 5000:
            return JsonResponse({"error": "Project details exceed the allowed length."}, status=400)

        budget_raw = data.get("budget")
        budget = None
        if budget_raw not in (None, ""):
            try:
                budget = Decimal(str(budget_raw))
            except (InvalidOperation, TypeError):
                return JsonResponse({"error": "Budget must be a valid number."}, status=400)
            if not budget.is_finite() or budget <= 0 or budget > Decimal("1000000"):
                return JsonResponse({"error": "Budget must be between $0.01 and $1,000,000."}, status=400)

        agents = list(Agent.objects.filter(is_active=True).values("name", "description", "capability"))
        if not agents:
            return JsonResponse({"error": "No active specialist agents are available."}, status=400)

        user_request = f"Project title: {title}\n\nProject description: {description}"
        result = create_plan(user_request, agents, budget=budget)
        return JsonResponse(result, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request."}, status=400)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception:
        logger.exception("TASKWEAVE plan generation failed")
        return JsonResponse({"error": "Plan generation failed. Check server logs and try again."}, status=502)


@require_POST
def approve_plan(request, plan_id):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request."}, status=400)
    if not isinstance(data, dict) or data.get("action") not in ("approve", "reject"):
        return JsonResponse({"error": "Action must be 'approve' or 'reject'."}, status=400)

    plan = get_object_or_404(TaskPlan, pk=plan_id)
    if plan.status != "DRAFT":
        return JsonResponse({"error": "Only draft plans can be approved or rejected."}, status=409)

    plan.status = "APPROVED" if data["action"] == "approve" else "REJECTED"
    plan.save(update_fields=["status"])
    return JsonResponse({
        "id": plan.id,
        "status": plan.status,
        "message": f"Plan {data['action']}d successfully.",
    })


@require_POST
def create_payment(request, plan_id):
    plan = get_object_or_404(TaskPlan, pk=plan_id)
    if plan.status != "APPROVED":
        return JsonResponse({"error": "Approve the task plan before payment."}, status=400)
    if Payment.objects.filter(plan=plan, status="CAPTURED").exists():
        return JsonResponse({"error": "This plan has already been paid for."}, status=409)

    # Reuse a still-open order rather than creating multiple payable orders.
    existing = Payment.objects.filter(plan=plan, status="CREATED").order_by("-created_at").first()
    if existing:
        try:
            remote = get_paypal_order(existing.paypal_order_id)
            if remote.get("status") in ("CREATED", "PAYER_ACTION_REQUIRED", "APPROVED"):
                approval = next(
                    (item.get("href") for item in remote.get("links", [])
                     if item.get("rel") in ("payer-action", "approve")),
                    None,
                )
                if approval:
                    return JsonResponse({
                        "payment_id": existing.id,
                        "paypal_order_id": existing.paypal_order_id,
                        "amount": str(existing.amount),
                        "currency": existing.currency,
                        "status": existing.status,
                        "approval_url": approval,
                    })
        except Exception:
            logger.exception("Could not reuse existing PayPal order")

    try:
        order = create_paypal_order(
            plan,
            request.build_absolute_uri(reverse("paypal_return")),
            request.build_absolute_uri(reverse("paypal_cancel")),
        )
        payment = Payment.objects.create(
            plan=plan,
            paypal_order_id=order["id"],
            amount=plan.total_cost,
            currency=plan.currency,
            status="CREATED",
        )
        return JsonResponse({
            "payment_id": payment.id,
            "paypal_order_id": payment.paypal_order_id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            "approval_url": order["approval_url"],
        }, status=201)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except Exception:
        logger.exception("TASKWEAVE PayPal order creation failed")
        return JsonResponse({"error": "Could not create PayPal payment. Check server logs."}, status=502)


def _verify_and_capture(payment):
    """Capture only an APPROVED order, then verify the returned capture."""
    remote = get_paypal_order(payment.paypal_order_id)
    remote_status = remote.get("status")

    if remote_status == "COMPLETED":
        result = remote
    elif remote_status == "APPROVED":
        result = capture_paypal_order(payment.paypal_order_id)
    else:
        raise ValueError(
            f"PayPal order is {remote_status or 'UNKNOWN'}, not APPROVED. "
            "Complete buyer approval in PayPal Sandbox first."
        )

    if result.get("status") != "COMPLETED":
        raise ValueError("PayPal has not confirmed order completion.")

    units = result.get("purchase_units") or []
    captures = (units[0].get("payments") or {}).get("captures", []) if units else []
    completed = next((item for item in captures if item.get("status") == "COMPLETED"), None)
    if not completed:
        raise ValueError("PayPal did not return a completed capture.")

    amount = completed.get("amount") or {}
    if amount.get("currency_code") != payment.currency or amount.get("value") != f"{Decimal(payment.amount):.2f}":
        payment.status = "FAILED"
        payment.save(update_fields=["status", "updated_at"])
        raise ValueError("Captured amount or currency does not match the saved quote.")

    payment.capture_id = completed.get("id")
    payment.status = "CAPTURED"
    payment.save(update_fields=["capture_id", "status", "updated_at"])
    return payment


@require_POST
def capture_payment(request, plan_id):
    plan = get_object_or_404(TaskPlan, pk=plan_id)
    payment = Payment.objects.filter(plan=plan).order_by("-created_at").first()
    if not payment:
        return JsonResponse({"error": "No payment record found."}, status=404)
    if payment.status == "CAPTURED":
        return JsonResponse({"status": "CAPTURED", "message": "Payment was already captured."})
    try:
        _verify_and_capture(payment)
        return JsonResponse({
            "status": "CAPTURED",
            "capture_id": payment.capture_id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "message": "PayPal payment captured and verified.",
        })
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=409)
    except Exception:
        logger.exception("TASKWEAVE PayPal capture failed")
        return JsonResponse({"error": "Payment verification failed. Check server logs."}, status=502)


@require_GET
def paypal_return(request):
    order_id = request.GET.get("token", "").strip()
    if not order_id:
        return render(request, "agents/payment_result.html", {
            "success": False, "message": "PayPal did not return an order token."
        }, status=400)

    payment = Payment.objects.filter(paypal_order_id=order_id).select_related("plan").first()
    if not payment:
        return render(request, "agents/payment_result.html", {
            "success": False, "message": "This PayPal order is not registered in TASKWEAVE."
        }, status=404)

    if payment.status == "CAPTURED":
        success, message = True, "Your Sandbox payment has already been verified."
    else:
        try:
            _verify_and_capture(payment)
            success = True
            message = "Your PayPal Sandbox payment was captured and verified."
        except ValueError as error:
            success, message = False, str(error)
        except Exception:
            logger.exception("PayPal return verification failed")
            success, message = False, "Payment verification failed. Please return to your workspace and check payment status."

    return render(request, "agents/payment_result.html", {
        "success": success,
        "message": message,
        "plan_id": payment.plan_id,
        "amount": payment.amount,
        "currency": payment.currency,
    })


@require_GET
def paypal_cancel(request):
    return render(request, "agents/payment_result.html", {
        "success": False,
        "message": "Checkout was cancelled. Your plan remains approved and no capture was initiated.",
    })


@require_POST
def execute_plan(request, plan_id):
    """Execute approved work only after a verified PayPal capture."""
    plan = get_object_or_404(TaskPlan, pk=plan_id)
    if plan.status != "APPROVED":
        return JsonResponse({"error": "Only approved plans can be executed."}, status=409)
    payment = Payment.objects.filter(plan=plan, status="CAPTURED").order_by("-created_at").first()
    if not payment:
        return JsonResponse({"error": "Execution is locked until PayPal capture is verified."}, status=402)

    tasks = list(plan.tasks)
    completed = 0
    errors = []
    for index, task in enumerate(tasks):
        if task.get("status") == "COMPLETED" and task.get("deliverable"):
            completed += 1
            continue
        task["status"] = "RUNNING"
        task["error"] = ""
        tasks[index] = task
        plan.tasks = tasks
        plan.save(update_fields=["tasks"])
        try:
            task["deliverable"] = execute_task(plan.project_summary, plan.user_request, task)
            task["status"] = "COMPLETED"
            task["error"] = ""
            completed += 1
        except Exception as error:
            logger.exception("Task execution failed for plan %s task %s", plan.id, task.get("task_number"))
            task["status"] = "FAILED"
            task["error"] = str(error)[:500]
            errors.append({"task_number": task.get("task_number"), "error": task["error"]})
        tasks[index] = task
        plan.tasks = tasks
        plan.save(update_fields=["tasks"])

    return JsonResponse({
        "plan_id": plan.id,
        "completed_tasks": completed,
        "total_tasks": len(tasks),
        "status": "COMPLETED" if completed == len(tasks) else "PARTIAL",
        "errors": errors,
        "tasks": tasks,
    })


@require_GET
def download_deliverable(request, plan_id, task_number):
    plan = get_object_or_404(TaskPlan, pk=plan_id)
    payment_exists = Payment.objects.filter(plan=plan, status="CAPTURED").exists()
    if not payment_exists:
        return HttpResponse("Payment verification required.", status=402, content_type="text/plain")
    task = next((item for item in plan.tasks if item.get("task_number") == task_number), None)
    if not task or task.get("status") != "COMPLETED" or not task.get("deliverable"):
        return HttpResponse("Deliverable is not available.", status=404, content_type="text/plain")
    filename = slugify(f"taskweave-plan-{plan.id}-task-{task_number}") or "taskweave-deliverable"
    response = HttpResponse(task["deliverable"], content_type="text/markdown; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}.md"'
    return response

import json
from decimal import Decimal

from agents.models import TaskPlan
from .groq_client import ask_groq
from .pricing import calculate_plan_cost


def create_plan(user_request, available_agents, budget=None):
    agent_information = json.dumps(available_agents, indent=2)
    prompt = f'''You are TASKWEAVE, an AI project orchestration planner.

USER REQUEST:
{user_request}

AVAILABLE SPECIALISTS:
{agent_information}

Create a practical plan covering every distinct requirement. Identify requirements first, then create 3-10 implementation tasks. Do not make one task per agent. Reuse specialists when appropriate. Only assign exact agent names from the list. Every task must include a clear description, a concrete deliverable, and requirement IDs it covers. Every requirement must be covered. Do not invent prices or agents. Return JSON only in this schema:
{{
 "project_summary":"...",
 "requirements":[{{"id":"R1","description":"..."}}],
 "tasks":[{{"task_number":1,"agent":"Exact agent name","description":"...","expected_deliverable":"...","covers_requirements":["R1"]}}]
}}'''
    try:
        plan = json.loads(ask_groq(prompt, json_mode=True))
    except (json.JSONDecodeError, TypeError):
        raise ValueError("AI Planner returned invalid JSON.")
    validate_plan(plan, available_agents)
    pricing = calculate_plan_cost(plan["tasks"])
    if budget is not None and pricing["total_cost"] > Decimal(str(budget)):
        raise ValueError(f"Generated quote is ${pricing['total_cost']:.2f}, exceeding your ${Decimal(str(budget)):.2f} budget.")
    # Persist requirements with the task JSON so no schema migration is needed.
    tasks = pricing["tasks"]
    requirement_map = {item["id"]: item["description"] for item in plan["requirements"]}
    for task in tasks:
        task["requirement_details"] = [requirement_map[rid] for rid in task["covers_requirements"]]
        task["status"] = "PENDING"
        task["deliverable"] = ""
        task["error"] = ""
    saved = TaskPlan.objects.create(
        user_request=user_request,
        project_summary=plan["project_summary"],
        tasks=tasks,
        total_cost=pricing["total_cost"],
        currency=pricing["currency"],
        status="DRAFT",
    )
    return {"id": saved.id, "project_summary": saved.project_summary,
            "requirements": plan["requirements"], "tasks": saved.tasks,
            "total_cost": str(saved.total_cost), "currency": saved.currency,
            "status": saved.status}


def validate_plan(plan, available_agents):
    if not isinstance(plan, dict) or not isinstance(plan.get("project_summary"), str) or not plan["project_summary"].strip():
        raise ValueError("AI Planner returned an invalid project summary.")
    requirements = plan.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("AI Planner did not identify project requirements.")
    ids = set()
    for req in requirements:
        if not isinstance(req, dict) or not isinstance(req.get("id"), str) or not req["id"].strip() or not isinstance(req.get("description"), str) or not req["description"].strip():
            raise ValueError("AI Planner returned an invalid requirement.")
        if req["id"] in ids:
            raise ValueError(f"Duplicate requirement ID: {req['id']}")
        ids.add(req["id"])
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not 3 <= len(tasks) <= 10:
        raise ValueError("Plan must contain between 3 and 10 tasks.")
    agents = {a["name"] for a in available_agents}
    numbers, covered = set(), set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Invalid task format.")
        n = task.get("task_number")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n in numbers:
            raise ValueError("Task numbers must be unique positive integers.")
        numbers.add(n)
        if task.get("agent") not in agents:
            raise ValueError(f"Unknown agent assigned: {task.get('agent')}")
        for field in ("description", "expected_deliverable"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                raise ValueError(f"Task {n} is missing {field}.")
        mapping = task.get("covers_requirements")
        if not isinstance(mapping, list) or not mapping:
            raise ValueError(f"Task {n} has no requirement mapping.")
        for rid in mapping:
            if rid not in ids:
                raise ValueError(f"Task {n} references unknown requirement {rid}.")
            covered.add(rid)
    missing = ids - covered
    if missing:
        raise ValueError("Uncovered requirements: " + ", ".join(sorted(missing)))
    return True

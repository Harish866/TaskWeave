from decimal import Decimal
from agents.models import Agent


def calculate_plan_cost(tasks):
    """
    Calculate task prices using the database.
    Never trust prices supplied by the AI.
    """

    agents = Agent.objects.filter(is_active=True)

    agent_prices = {
        agent.name: agent.price
        for agent in agents
    }

    total_cost = Decimal("0.00")
    priced_tasks = []

    for task in tasks:
        agent_name = task.get("agent")

        if agent_name not in agent_prices:
            raise ValueError(f"Invalid or unavailable agent: {agent_name}")

        price = agent_prices[agent_name]
        total_cost += price

        priced_task = task.copy()
        priced_task["price"] = str(price)
        priced_task["currency"] = "USD"

        priced_tasks.append(priced_task)

    return {
        "tasks": priced_tasks,
        "total_cost": total_cost,
        "currency": "USD"
    }
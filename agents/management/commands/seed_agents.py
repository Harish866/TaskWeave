from decimal import Decimal

from django.core.management.base import BaseCommand

from agents.models import Agent


DEFAULT_AGENTS = [
    {
        "name": "Data Analyst",
        "description": "Cleans, explores, and interprets structured datasets.",
        "capability": "Data Analysis",
        "price": Decimal("5.00"),
    },
    {
        "name": "Visualization Specialist",
        "description": "Creates clear charts and visual summaries from data.",
        "capability": "Data Visualization",
        "price": Decimal("3.00"),
    },
    {
        "name": "Report Writer",
        "description": "Turns findings into a structured, readable report.",
        "capability": "Report Generation",
        "price": Decimal("4.00"),
    },
]


class Command(BaseCommand):
    help = "Create or update the default TASKWEAVE specialist agents."

    def handle(self, *args, **options):
        for item in DEFAULT_AGENTS:
            agent, created = Agent.objects.update_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "capability": item["capability"],
                    "price": item["price"],
                    "is_active": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'{"Created" if created else "Updated"}: {agent.name} (${agent.price})'
                )
            )

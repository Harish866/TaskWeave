from .groq_client import ask_groq


def execute_task(project_title, project_request, task):
    """Generate a concrete text deliverable for one paid task."""
    prompt = f'''You are the {task['agent']} specialist in TASKWEAVE.
Produce the actual deliverable for the task below, not a plan describing how to do it.

PROJECT: {project_title}
PROJECT REQUEST:
{project_request}

TASK:
{task['description']}

EXPECTED DELIVERABLE:
{task.get('expected_deliverable', 'A useful, complete work product')}

REQUIREMENTS COVERED: {', '.join(task.get('covers_requirements', []))}

Return a professional, self-contained Markdown deliverable. Include assumptions and limitations where relevant. Do not claim to have run code, accessed databases, deployed systems, or created files unless you actually did so. Provide usable specifications, code, analysis, tables, or report content appropriate to this task.'''
    result = ask_groq(prompt, json_mode=False)
    if not result or not result.strip():
        raise ValueError("The specialist returned an empty deliverable.")
    return result.strip()

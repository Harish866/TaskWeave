# TASKWEAVE

## Project Overview
TASKWEAVE is an AI-powered multi-agent task execution platform designed to break complex user requests into smaller tasks and assign them to specialized AI agents.

The platform aims to simplify complex workflows through intelligent planning, agent coordination, and transparent cost estimation.

## Problem Statement
Complex tasks often require multiple skills, tools, and stages of execution. Managing these stages manually can be time-consuming and inefficient.

TASKWEAVE addresses this problem by using an AI planner to understand user requests, generate structured task plans, and identify suitable specialized agents.

## Key Features
- AI-powered task planning using Groq.
- Multi-agent architecture.
- Specialized agents for different tasks.
- Automated task breakdown and assignment.
- Cost estimation for task execution.
- Django-based backend.

## AI Integration
TASKWEAVE uses the Groq API to power its AI planning functionality.

The AI planner interprets user requests and generates structured task plans that can be processed by specialized agents.

## PayPal Integration
TASKWEAVE is being developed for the PayPal AI Hackathon 2026.

The platform is designed to incorporate PayPal-based payment processing for agent task execution, enabling transparent pricing and payment workflows.

*Detailed payment integration and transaction handling will be documented as those features are implemented.*

## Technology Stack
- Python
- Django
- Groq API
- SQLite
- HTML, CSS and JavaScript (where applicable)

## Installation and Setup

### Prerequisites
- Python 3.10 or later
- pip
- Git

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the Project Directory

```bash
cd TASKWEAVE
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory and add the required API credentials.

Example:

```env
GROQ_API_KEY=your_groq_api_key
```

Never upload your actual `.env` file or API credentials to GitHub.

### 7. Apply Database Migrations

```bash
python manage.py migrate
```

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open the following URL in your browser:

```text
http://127.0.0.1:8000/
```

## Project Architecture

TASKWEAVE currently consists of the following major components:

- **AI Planner:** Understands user requests and generates task plans.
- **Agent System:** Maintains specialized agents with defined capabilities and pricing.
- **Task Management:** Stores and manages task plans.
- **Cost Estimation:** Calculates the estimated execution cost of selected agents.
- **Backend:** Django handles application logic, database operations and API functionality.

## Registered Agents

| Agent | Pricing |
|---|---:|
| Data Analyst | $5 |
| Visualization Specialist | $3 |
| Report Writer | $4 |

*These are configured agent prices, not necessarily actual transaction amounts.*

## Future Improvements
- PayPal payment integration.
- Automated multi-agent task execution.
- Real-time task progress tracking.
- Agent performance monitoring.
- Improved cost management and reporting.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements
Developed as part of the PayPal AI Hackathon 2026.

Powered by Python, Django and Groq.

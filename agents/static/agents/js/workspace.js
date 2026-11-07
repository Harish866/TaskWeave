document.addEventListener("DOMContentLoaded", () => {
    const description = document.getElementById("projectDescription");
    const charCount = document.getElementById("charCount");
    const projectForm = document.getElementById("projectForm");
    const generateButton = document.getElementById("generateButton");
    const planResults = document.getElementById("planResults");
    const planSummary = document.getElementById("planSummary");
    const taskList = document.getElementById("taskList");
    const requirementList = document.getElementById("requirementList");
    const planTotal = document.getElementById("planTotal");
    const planStatus = document.getElementById("planStatus");
    const approveButton = document.getElementById("approvePlanButton");
    const rejectButton = document.getElementById("rejectPlanButton");
    const paymentButton = document.getElementById("payPlanButton");
    const approvalMessage = document.getElementById("approvalMessage");
    const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
    let currentPlanId = null;

    if (description && charCount) {
        description.addEventListener("input", () => {
            charCount.textContent = `${description.value.length} / 5000`;
        });
    }

    function displayPlan(plan) {
        currentPlanId = plan.id;
        planSummary.textContent = plan.project_summary;
        taskList.replaceChildren();
        if (requirementList) {
            requirementList.replaceChildren();
            const heading = document.createElement("h3");
            heading.textContent = `Identified requirements (${(plan.requirements || []).length})`;
            requirementList.appendChild(heading);
            (plan.requirements || []).forEach((requirement) => {
                const item = document.createElement("p");
                item.textContent = `${requirement.id}: ${requirement.description}`;
                requirementList.appendChild(item);
            });
        }

        plan.tasks.forEach((task) => {
            const card = document.createElement("article");
            card.className = "task-item";

            const title = document.createElement("h4");
            title.textContent = `Task ${task.task_number}: ${task.agent}`;

            const detail = document.createElement("p");
            detail.textContent = task.description;

            const deliverable = document.createElement("p");
            deliverable.className = "task-deliverable";
            deliverable.textContent = `Deliverable: ${task.expected_deliverable || "Not specified"}`;

            const coverage = document.createElement("p");
            coverage.className = "task-coverage";
            coverage.textContent = `Covers: ${(task.requirement_details || task.covers_requirements || []).join(" · ") || "Not specified"}`;

            const price = document.createElement("span");
            price.textContent = `${plan.currency} ${Number(task.price).toFixed(2)}`;

            card.append(title, detail, deliverable, coverage, price);
            taskList.appendChild(card);
        });

        planTotal.textContent = `${plan.currency} ${Number(plan.total_cost).toFixed(2)}`;
        planStatus.textContent = "DRAFT PLAN";
        approvalMessage.textContent = "";
        approveButton.hidden = false;
        rejectButton.hidden = false;
        paymentButton.hidden = true;
        approveButton.disabled = false;
        rejectButton.disabled = false;
        planResults.hidden = false;
        planResults.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    async function postJSON(url, payload) {
        if (!csrfInput) throw new Error("CSRF token missing. Refresh the page.");
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfInput.value
            },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Request failed.");
        return result;
    }

    if (projectForm) {
        projectForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const title = document.getElementById("projectTitle").value.trim();
            const details = description.value.trim();
            const budget = document.getElementById("projectBudget").value.trim();

            if (!title || !details) {
                alert("Please enter both a project title and description.");
                return;
            }

            generateButton.disabled = true;
            generateButton.textContent = "Generating your plan...";
            try {
                const plan = await postJSON("/generate-plan/", {
                    title,
                    description: details,
                    budget: budget || null
                });
                displayPlan(plan);
            } catch (error) {
                alert(error.message);
            } finally {
                generateButton.disabled = false;
                generateButton.textContent = "✦ Generate AI Task Plan";
            }
        });
    }

    async function updatePlanStatus(action) {
        if (!currentPlanId) return;
        approveButton.disabled = true;
        rejectButton.disabled = true;
        approvalMessage.textContent = "Updating plan status...";
        try {
            const result = await postJSON(`/plans/${currentPlanId}/approve/`, { action });
            planStatus.textContent = `${result.status} PLAN`;
            approvalMessage.textContent = result.message;

            if (action === "approve") {
                paymentButton.hidden = false;
                rejectButton.hidden = true;
                approveButton.hidden = true;
                approvalMessage.textContent = "Plan approved. Continue to PayPal Sandbox to authorize payment.";
            } else {
                approveButton.hidden = true;
                rejectButton.hidden = true;
            }
        } catch (error) {
            approvalMessage.textContent = error.message;
            approveButton.disabled = false;
            rejectButton.disabled = false;
        }
    }

    approveButton?.addEventListener("click", () => updatePlanStatus("approve"));
    rejectButton?.addEventListener("click", () => updatePlanStatus("reject"));

    paymentButton?.addEventListener("click", async () => {
        if (!currentPlanId) return;
        paymentButton.disabled = true;
        paymentButton.textContent = "Connecting to PayPal...";
        approvalMessage.textContent = "Creating your PayPal Sandbox checkout...";
        try {
            const result = await postJSON(`/plans/${currentPlanId}/create-payment/`, {});
            window.location.assign(result.approval_url);
        } catch (error) {
            approvalMessage.textContent = error.message;
            paymentButton.disabled = false;
            paymentButton.textContent = "Continue to PayPal Sandbox";
        }
    });
});

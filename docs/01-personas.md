# Personas and Use Cases

## 1. HR Manager
**Role:** Oversees departmental performance and strategic HR planning.
**Jobs-to-be-done:**
- Identify performance trends across departments.
- Ensure the fairness and impartiality of performance reviews.
- Allocate resources or training budgets based on predicted needs.

## 2. HR Analyst
**Role:** Data-savvy user who audits and reports on HR metrics.
**Jobs-to-be-done:**
- Run batch predictions on quarterly snapshots.
- Investigate feature importance and model drift.
- Generate fairness and compliance reports.

## 3. Team Lead
**Role:** Direct manager of employees.
**Jobs-to-be-done:**
- Get an objective "second opinion" on an employee's likely performance band.
- Identify specific areas (e.g., training hours, project count) where an employee needs support.
- Explore "What-if" counterfactuals to guide employee development plans.

## 4. Reviewer (Human-in-the-Loop)
**Role:** Reviews low-confidence or contentious model predictions.
**Jobs-to-be-done:**
- Inspect borderline cases or extreme errors.
- Read the "Why?" summary and nearest neighbours to understand the model's logic.
- Override the prediction with a manual decision and note.

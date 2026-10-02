# HR Insights User Guide

Welcome to the HR Insights Platform. This tool is designed to assist HR managers and team leads in evaluating and understanding employee performance through a transparent, machine-learning-driven approach.

## 1. Getting Started

### Accessing the Platform
You must have a valid account to access the system.
1. Navigate to the application URL (e.g. `http://localhost:80`).
2. Log in using your email and password. 
   - *Default Admin Demo Account:* `admin@hr.local` / `admin123`

### The Dashboard
Upon login, you'll land on the Dashboard. This screen provides:
- **System Status:** Verifies if the underlying K-Nearest Neighbors (KNN) model is healthy and online.
- **Recent Activity:** A summary of recent system interactions.

## 2. Running a Prediction

To evaluate an employee, navigate to the **Predict Performance** page via the left sidebar.

### Inputting Data
Fill out the Employee Profile form. You will need:
- **Attendance (%):** The employee's attendance rate.
- **Experience (Years):** Years of professional experience.
- **Training Hours:** Total hours of training completed.
- **Projects Completed:** Number of successful projects.
- **Weekly Hours:** Average hours worked per week.
- **Previous Score:** Their last performance review score (1.0 to 5.0).
- **Department & Job Level:** Categorical role identifiers.

Click **Run Prediction**.

### Understanding the Results
Unlike "black box" AI, this system provides full transparency:
1. **The Prediction:** The predicted performance band (High, Medium, or Low) and the system's confidence percentage.
2. **Review Flags:** If confidence is low, a yellow banner will advise that human review is required.
3. **Nearest Neighbours:** To explain *why* the prediction was made, the system lists the most similar historical employees (Neighbours) from the training data, allowing you to see precedents.

## 3. Administrator Actions
If you are logged in as an Admin:
- You have access to backend analytics.
- You can monitor data drift (Population Stability Index) via the backend API at `/api/v1/analytics/drift`.

## 4. Support
If you encounter errors or the prediction system is unreachable, contact the internal IT desk or refer to the technical `RUN.md` file in the project repository.

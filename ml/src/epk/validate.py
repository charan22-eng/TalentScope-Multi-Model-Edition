import pandas as pd
import numpy as np

def validate_data(df: pd.DataFrame) -> dict:
    """Validates dataframe and returns row-level reasons for drops or anomalies."""
    issues = []
    
    for i, row in df.iterrows():
        # Missing values
        missing = row.isnull().sum()
        if missing > 2:
            issues.append({"index": i, "reason": "Too many missing values"})
            
        # Division safety checks (pre-emptive)
        if row.get("experience_years", 1) < 0:
            issues.append({"index": i, "reason": "Negative experience years"})
            
        # Impossible values
        if row.get("attendance", 0) < 0:
            issues.append({"index": i, "reason": "Negative attendance"})

    return {"total_issues": len(issues), "details": issues}

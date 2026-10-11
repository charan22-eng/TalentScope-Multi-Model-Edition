import time
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

import sys
from pathlib import Path
# Add the project root to sys.path so we can import epk.data
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from epk.data import make_employee_data
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import f1_score

NUM = ["attendance", "experience_years", "training_hours", "projects_completed", 
       "weekly_hours", "prev_score", "peer_feedback", "tasks_on_time_pct", "certifications"]

def prep(scale=True):
    num_pipe = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler() if scale else "passthrough"
    )
    return ColumnTransformer([
        ("n", num_pipe, NUM),
        ("lvl", OrdinalEncoder(categories=[["Junior", "Mid", "Senior", "Lead"]]), ["job_level"]),
        ("d", OneHotEncoder(handle_unknown="ignore"), ["department"])
    ])

def main():
    print("Running quick variant checks...")
    for variant in ["linear", "nonlinear", "noisy_overlap"]:
        df, protected_df = make_employee_data(n=12000, seed=42, variant=variant)
        print(f"\nVariant: {variant} (Rows: {len(df)})")
        print("Class balance:")
        print(df.performance.value_counts(normalize=True).round(2).to_dict())
        
        tr, te = train_test_split(df, test_size=0.4, stratify=df.performance, random_state=42)
        X = tr.drop(columns=["performance", "performance_score", "employee_id"])
        Xt = te.drop(columns=["performance", "performance_score", "employee_id"])
        
        t1, t2 = np.quantile(tr.performance_score, [0.30, 0.75])
        res = {}
        
        # Linear Regression (score to band)
        lr = make_pipeline(prep(), LinearRegression()).fit(X, tr.performance_score)
        p = lr.predict(Xt)
        pb = np.where(p < t1, "Low", np.where(p < t2, "Medium", "High"))
        res["LinReg"] = f1_score(te.performance, pb, average="macro")
        
        models = {
            "LogReg": make_pipeline(prep(), LogisticRegression(max_iter=2000)),
            "KNN": make_pipeline(prep(), KNeighborsClassifier(25, weights="distance")),
            "SVC": make_pipeline(prep(), SVC(C=3, gamma="scale")),
            "DT": make_pipeline(prep(False), DecisionTreeClassifier(max_depth=6, random_state=42)),
            "RF": make_pipeline(prep(False), RandomForestClassifier(300, min_samples_leaf=3, random_state=42, n_jobs=-1)),
            "HistGB": make_pipeline(prep(False), HistGradientBoostingClassifier(random_state=42, learning_rate=0.08, max_iter=250))
        }
        
        for k, m in models.items():
            m.fit(X, tr.performance)
            res[k] = f1_score(te.performance, m.predict(Xt), average="macro")
            
        print("Macro-F1 Results:")
        res_sorted = dict(sorted(res.items(), key=lambda item: item[1], reverse=True))
        print({k: round(v, 3) for k, v in res_sorted.items()})

if __name__ == "__main__":
    main()

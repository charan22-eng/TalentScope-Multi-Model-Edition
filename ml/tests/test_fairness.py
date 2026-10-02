import pandas as pd
from epk.fairness import audit_groups, proxy_analysis, bias_injection_test, robustness_noise_test
from sklearn.dummy import DummyClassifier

def test_audit_groups_suppression():
    y_true = ["High"] * 30 + ["Low"] * 10
    y_pred = ["High"] * 30 + ["Low"] * 10
    groups = ["A"] * 30 + ["B"] * 10
    
    res = audit_groups(y_true, y_pred, groups, min_group_size=20)
    assert "size" in res["A"]
    assert res["B"] == "SUPPRESSED"

def test_proxy_analysis():
    df = pd.DataFrame({
        "department": ["Sales", "HR", "Engineering", "Sales", "HR", "Engineering"],
        "proxy_score": [1, 2, 3, 1, 2, 3],
        "random": [1, 5, 2, 8, 3, 9]
    })
    proxies = proxy_analysis(df, ["department"], "target")
    assert "department" in proxies
    assert "proxy_score" in proxies["department"]

def test_bias_injection():
    df_clean = pd.DataFrame({"feat": [1, 2, 3, 4], "target": ["High", "Low", "High", "Low"]})
    df_biased = pd.DataFrame({"feat": [1, 1, 1, 1], "target": ["High", "Low", "High", "Low"]})
    
    pipe = DummyClassifier(strategy="constant", constant="High")
    pipe.fit(df_clean[["feat"]], df_clean["target"])
    
    res = bias_injection_test(pipe, df_clean, df_biased, "target")
    assert "disparity_ratio" in res

def test_robustness():
    df = pd.DataFrame({"feat": [1.0, 2.0, 3.0, 4.0], "target": ["High", "Low", "High", "Low"]})
    pipe = DummyClassifier(strategy="constant", constant="High")
    pipe.fit(df[["feat"]], df["target"])
    
    stab = robustness_noise_test(pipe, df[["feat"]], noise_level=0.1)
    assert stab == 1.0

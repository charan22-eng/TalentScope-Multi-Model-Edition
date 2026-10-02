import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix

def audit_groups(y_true, y_pred, groups, min_group_size=30):
    """
    Computes performance metrics per group.
    Hides groups below min_group_size to protect privacy.
    """
    df = pd.DataFrame({"true": y_true, "pred": y_pred, "group": groups})
    results = {}
    
    for g, data in df.groupby("group"):
        if len(data) < min_group_size:
            results[g] = "SUPPRESSED"
            continue
            
        exact = np.mean(data["true"] == data["pred"])
        results[g] = {"size": len(data), "exact_match_rate": exact}
        
    return results

def proxy_analysis(df, protected_cols, target_col):
    """
    Computes mutual information between protected attributes and other features
    to identify proxies. (Simplified: just correlations with encoded categories).
    """
    # Simple label encoding for correlation
    encoded = df.copy()
    for c in encoded.select_dtypes(include=['object']):
        encoded[c] = encoded[c].astype('category').cat.codes
        
    corr = encoded.corr(method="spearman")
    proxies = {}
    for p in protected_cols:
        if p in corr:
            # Find features highly correlated with protected attribute
            high_corr = corr[p].abs().sort_values(ascending=False)
            proxies[p] = high_corr[high_corr > 0.3].to_dict()
    return proxies

def bias_injection_test(pipe, df_clean, df_biased, target_col):
    """
    Experimental mitigation lab: tests disparity ratio between clean and biased data.
    """
    preds_clean = pipe.predict(df_clean.drop(columns=[target_col]))
    preds_biased = pipe.predict(df_biased.drop(columns=[target_col]))
    
    # Calculate disparity (simplified as ratio of 'High' predictions)
    rate_clean = np.mean(preds_clean == "High")
    rate_biased = np.mean(preds_biased == "High")
    
    ratio = rate_biased / rate_clean if rate_clean > 0 else 0
    return {"clean_high_rate": rate_clean, "biased_high_rate": rate_biased, "disparity_ratio": ratio}

def robustness_noise_test(pipe, X_test, noise_level=0.1):
    """
    Tests model stability against random Gaussian noise on numeric features.
    """
    X_noisy = X_test.copy()
    num_cols = X_noisy.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        std = X_noisy[c].std()
        X_noisy[c] += np.random.normal(0, std * noise_level, size=len(X_noisy))
        
    preds_orig = pipe.predict(X_test)
    preds_noisy = pipe.predict(X_noisy)
    
    stability = np.mean(preds_orig == preds_noisy)
    return stability

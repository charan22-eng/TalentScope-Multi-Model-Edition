import pandas as pd


def explain(pipe, X_train: pd.DataFrame, y_train: pd.Series, x_new: pd.DataFrame):
    """Returns nearest neighbours and vote fractions."""
    prep, knn = pipe.named_steps["prep"], pipe.named_steps["knn"]
    X_scaled = prep.transform(x_new)
    dist, idx = knn.kneighbors(X_scaled)

    nb = X_train.iloc[idx[0]].copy()
    nb["class"] = y_train.iloc[idx[0]].values
    nb["distance"] = dist[0].round(4)
    votes = nb["class"].value_counts(normalize=True).to_dict()

    return nb.reset_index(drop=True), votes


def local_attribution(pipe, x_row: pd.DataFrame, train_medians: pd.Series):
    """Calculates feature attribution by substituting train medians."""
    classes = list(pipe.classes_)
    base_proba = pipe.predict_proba(x_row)[0]
    pred_idx = int(base_proba.argmax())
    pred_class = classes[pred_idx]

    out = {}
    for f in x_row.columns:
        if f not in train_medians:
            continue
        trial = x_row.copy()
        trial[f] = train_medians[f]

        trial_proba = pipe.predict_proba(trial)[0][pred_idx]
        out[f] = float(base_proba[pred_idx] - trial_proba)

    return pred_class, dict(sorted(out.items(), key=lambda kv: -abs(kv[1])))


ACTIONABLE_FEATURES = {
    "training_hours": (5, 120),  # (step, cap)
    "projects_completed": (1, 20),
    "weekly_hours": (2, 60),
}


def counterfactual(pipe, x_row: pd.DataFrame, target="High", max_iter=40):
    """Greedy search for counterfactual."""
    x, path = x_row.copy(), []
    classes = list(pipe.classes_)
    if target not in classes:
        return None, path

    ti = classes.index(target)

    for _ in range(max_iter):
        if pipe.predict(x)[0] == target:
            return x, path

        best = None
        for f, (step, cap) in ACTIONABLE_FEATURES.items():
            if f not in x.columns:
                continue

            val = x[f].iloc[0]
            if pd.isna(val):
                continue

            if val + step > cap:
                continue

            trial = x.copy()
            trial[f] = val + step
            p = pipe.predict_proba(trial)[0][ti]

            if best is None or p > best[0]:
                best = (p, f, trial)

        if best is None:
            return None, path

        _, f, x = best
        path.append(f)

    return None, path


def summarise(prediction_data: dict) -> str:
    """Generates a plain-language summary based on explainability metrics."""
    label = prediction_data.get("label", "Unknown")
    prediction_data.get("confidence", 0)
    votes = prediction_data.get("votes", {})
    attrib = prediction_data.get("attribution", {})

    # Get top 2 features
    top_features = [k for k, v in list(attrib.items())[:2] if v > 0.05]

    summary = f"Predicted {label}."

    k = (
        sum(prediction_data.get("neighbours", pd.DataFrame()).shape[0:1])
        if "neighbours" in prediction_data
        else len(prediction_data.get("neighbours_list", []))
    )
    if votes and k:
        vote_count = int(votes.get(label, 0) * k)
        summary += f" {vote_count} of the {k} most similar employees were {label}."

    if top_features:
        feats = " and ".join([f.replace("_", " ") for f in top_features])
        summary += f" {feats.capitalize()} were the strongest positive contributors to this classification."

    summary += " This is decision support and should be reviewed by a person."
    return summary

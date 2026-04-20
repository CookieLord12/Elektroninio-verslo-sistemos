import argparse
import json
import os
import sys
import time
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore", category=ConvergenceWarning)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    print(f"Įspėjimas: nepavyko įkelti matplotlib ({exc}). Grafikai nebus sugeneruoti.")
    plt = None

try:
    import xgboost as xgb
except Exception:
    xgb = None

try:
    import torch
except Exception:
    torch = None


REQUIRED_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
]


@dataclass
class DatasetBundle:
    customers: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    products: pd.DataFrame
    payments: pd.DataFrame
    reviews: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Klientų pirkimų prognozavimo sistema e. prekybos duomenims"
    )
    parser.add_argument("--data-dir", required=True, help="Kelias iki Olist CSV failų katalogo")
    parser.add_argument("--output-dir", required=True, help="Katalogas rezultatams išsaugoti")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "gpu"],
        default="auto",
        help="XGBoost vykdymo įrenginys: auto, cpu arba gpu",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "full"],
        default="fast",
        help="fast = greitesnis režimas laboratoriniam darbui, full = lėtesnė išsamesnė paieška",
    )
    parser.add_argument(
        "--prediction-days",
        type=int,
        default=90,
        help="Kiek dienų į priekį prognozuojamas kitas pirkimas",
    )
    return parser.parse_args()


def ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_datasets(data_dir: str) -> DatasetBundle:
    missing = [name for name in REQUIRED_FILES if not os.path.exists(os.path.join(data_dir, name))]
    if missing:
        raise FileNotFoundError(
            "Trūksta šių failų data kataloge:\n- " + "\n- ".join(missing)
        )

    return DatasetBundle(
        customers=pd.read_csv(os.path.join(data_dir, "olist_customers_dataset.csv")),
        orders=pd.read_csv(os.path.join(data_dir, "olist_orders_dataset.csv")),
        order_items=pd.read_csv(os.path.join(data_dir, "olist_order_items_dataset.csv")),
        products=pd.read_csv(os.path.join(data_dir, "olist_products_dataset.csv")),
        payments=pd.read_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv")),
        reviews=pd.read_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv")),
    )


def preprocess_dates(bundle: DatasetBundle) -> DatasetBundle:
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        if col in bundle.orders.columns:
            bundle.orders[col] = pd.to_datetime(bundle.orders[col], errors="coerce")

    if "review_creation_date" in bundle.reviews.columns:
        bundle.reviews["review_creation_date"] = pd.to_datetime(
            bundle.reviews["review_creation_date"], errors="coerce"
        )
    if "review_answer_timestamp" in bundle.reviews.columns:
        bundle.reviews["review_answer_timestamp"] = pd.to_datetime(
            bundle.reviews["review_answer_timestamp"], errors="coerce"
        )
    return bundle


def choose_cutoff_date(orders: pd.DataFrame, prediction_days: int) -> pd.Timestamp:
    max_date = orders["order_purchase_timestamp"].max()
    if pd.isna(max_date):
        raise ValueError("Nepavyko rasti galiojančių pirkimo datų.")
    cutoff = max_date - pd.Timedelta(days=prediction_days)
    return cutoff.normalize()


def build_customer_dataset(bundle: DatasetBundle, prediction_days: int) -> pd.DataFrame:
    customers = bundle.customers.copy()
    orders = bundle.orders.copy()
    items = bundle.order_items.copy()
    payments = bundle.payments.copy()
    reviews = bundle.reviews.copy()
    products = bundle.products.copy()

    orders = orders.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
    cutoff_date = choose_cutoff_date(orders, prediction_days)

    history_orders = orders[orders["order_purchase_timestamp"] < cutoff_date].copy()
    future_orders = orders[
        (orders["order_purchase_timestamp"] >= cutoff_date)
        & (orders["order_purchase_timestamp"] < cutoff_date + pd.Timedelta(days=prediction_days))
    ].copy()

    if history_orders.empty:
        raise ValueError("Istorinių užsakymų aibė tuščia. Patikrinkite datų stulpelius.")

    # Order-level enrichments from history only
    payment_agg = payments.groupby("order_id").agg(
        payment_value_sum=("payment_value", "sum"),
        payment_installments_mean=("payment_installments", "mean"),
        payment_sequential_max=("payment_sequential", "max"),
        payment_types_nunique=("payment_type", "nunique"),
    )

    review_agg = reviews.groupby("order_id").agg(
        review_score_mean=("review_score", "mean"),
    )

    product_cols = ["product_id"]
    if "product_category_name" in products.columns:
        product_cols.append("product_category_name")
    if "product_weight_g" in products.columns:
        product_cols.append("product_weight_g")
    if "product_photos_qty" in products.columns:
        product_cols.append("product_photos_qty")
    products_small = products[product_cols].copy()

    item_enriched = items.merge(products_small, on="product_id", how="left")
    order_item_agg = item_enriched.groupby("order_id").agg(
        item_count=("order_item_id", "count"),
        price_sum=("price", "sum"),
        freight_sum=("freight_value", "sum"),
        unique_products=("product_id", "nunique"),
        unique_sellers=("seller_id", "nunique"),
        product_category_mode=(
            "product_category_name",
            lambda s: s.mode().iloc[0] if not s.mode().empty else "unknown",
        ),
        product_weight_mean=("product_weight_g", "mean") if "product_weight_g" in item_enriched.columns else ("price", "mean"),
        product_photos_mean=("product_photos_qty", "mean") if "product_photos_qty" in item_enriched.columns else ("price", "mean"),
    )

    history_enriched = (
        history_orders.merge(order_item_agg, on="order_id", how="left")
        .merge(payment_agg, on="order_id", how="left")
        .merge(review_agg, on="order_id", how="left")
    )

    history_enriched["delivery_days"] = (
        history_enriched["order_delivered_customer_date"] - history_enriched["order_purchase_timestamp"]
    ).dt.days
    history_enriched["estimated_delay_days"] = (
        history_enriched["order_delivered_customer_date"] - history_enriched["order_estimated_delivery_date"]
    ).dt.days

    last_purchase = history_enriched["order_purchase_timestamp"].max()

    def mode_or_unknown(series: pd.Series) -> str:
        s = series.dropna()
        if s.empty:
            return "unknown"
        mode = s.mode()
        return mode.iloc[0] if not mode.empty else str(s.iloc[0])

    customer_features = history_enriched.groupby("customer_unique_id").agg(
        order_count=("order_id", "nunique"),
        total_spent=("payment_value_sum", "sum"),
        avg_order_value=("payment_value_sum", "mean"),
        total_items=("item_count", "sum"),
        avg_items_per_order=("item_count", "mean"),
        total_products=("unique_products", "sum"),
        avg_freight=("freight_sum", "mean"),
        avg_review_score=("review_score_mean", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
        avg_delay_days=("estimated_delay_days", "mean"),
        last_order_date=("order_purchase_timestamp", "max"),
        first_order_date=("order_purchase_timestamp", "min"),
        last_order_status=("order_status", mode_or_unknown),
        favorite_category=("product_category_mode", mode_or_unknown),
        avg_payment_installments=("payment_installments_mean", "mean"),
        avg_payment_type_count=("payment_types_nunique", "mean"),
        avg_sellers=("unique_sellers", "mean"),
        avg_product_weight=("product_weight_mean", "mean"),
        avg_product_photos=("product_photos_mean", "mean"),
    ).reset_index()

    customer_features["recency_days"] = (last_purchase - customer_features["last_order_date"]).dt.days
    customer_features["customer_lifetime_days"] = (
        customer_features["last_order_date"] - customer_features["first_order_date"]
    ).dt.days.clip(lower=0)
    customer_features["purchase_frequency"] = customer_features["order_count"] / (
        customer_features["customer_lifetime_days"] + 1
    )

    future_target = (
        future_orders.groupby("customer_unique_id")["order_id"].nunique().gt(0).astype(int).rename("target")
    )

    dataset = customers.merge(customer_features, on="customer_unique_id", how="inner")
    dataset = dataset.merge(future_target, on="customer_unique_id", how="left")
    dataset["target"] = dataset["target"].fillna(0).astype(int)
    dataset["cutoff_date"] = cutoff_date
    dataset["prediction_days"] = prediction_days

    dataset = dataset.drop(columns=["customer_unique_id"], errors="ignore")
    dataset = dataset.drop(columns=["last_order_date", "first_order_date"], errors="ignore")

    class_counts = dataset["target"].value_counts()
    if len(class_counts) < 2:
        raise ValueError(
            "Tikslinis kintamasis turi tik vieną klasę. "
            "Tai reiškia, kad pasirinktu laikotarpiu nė vienas arba visi klientai nepirko pakartotinai. "
            "Bandykite kitą duomenų rinkinį arba mažinkite/didinkite prediction_days."
        )

    return dataset


def save_eda(dataset: pd.DataFrame, output_dir: str) -> None:
    dataset.describe(include="all").transpose().to_csv(
        os.path.join(output_dir, "eda_descriptive_statistics.csv"), encoding="utf-8-sig"
    )
    dataset.head(20).to_csv(
        os.path.join(output_dir, "sample_customer_dataset.csv"), index=False, encoding="utf-8-sig"
    )

    if plt is None:
        return

    plt.figure(figsize=(7, 5))
    dataset["target"].value_counts().sort_index().plot(kind="bar")
    plt.title("Tikslinio kintamojo pasiskirstymas")
    plt.xlabel("Tikslinė klasė")
    plt.ylabel("Klientų skaičius")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "target_distribution.png"), dpi=150)
    plt.close()

    numeric_cols = [
        col
        for col in ["order_count", "total_spent", "avg_order_value", "recency_days", "purchase_frequency"]
        if col in dataset.columns
    ]
    if numeric_cols:
        corr = dataset[numeric_cols + ["target"]].corr(numeric_only=True)
        plt.figure(figsize=(8, 6))
        plt.imshow(corr, aspect="auto")
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
        plt.yticks(range(len(corr.index)), corr.index)
        plt.title("Svarbiausių skaitinių kintamųjų koreliacija")
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "correlation_matrix.png"), dpi=150)
        plt.close()



def split_features_target(dataset: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str], List[str]]:
    y = dataset["target"].copy()
    X = dataset.drop(columns=["target", "customer_id", "cutoff_date", "prediction_days"], errors="ignore")

    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = [c for c in X.columns if c not in numeric_features]
    return X, y, numeric_features, categorical_features



def build_preprocessor(numeric_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )



def resolve_xgboost_device(device_flag: str) -> Tuple[Optional[str], str]:
    if xgb is None:
        return None, "XGBoost biblioteka neįdiegta, todėl GPU/CPU XGBoost modelis bus praleistas."

    gpu_available = bool(torch and torch.cuda.is_available())
    if device_flag == "cpu":
        return "cpu", "XGBoost priverstinai vykdomas CPU režimu (--device cpu)."
    if device_flag == "gpu":
        if gpu_available:
            return "cuda", "Aptiktas CUDA GPU, XGBoost vykdomas GPU režimu (--device gpu)."
        raise RuntimeError("Pasirinktas --device gpu, bet CUDA GPU neaptiktas.")
    if gpu_available:
        return "cuda", "Aptiktas CUDA GPU, todėl XGBoost vykdomas GPU režimu (--device auto)."
    return "cpu", "CUDA GPU neaptiktas, todėl XGBoost vykdomas CPU režimu (--device auto)."



def build_models(preprocessor: ColumnTransformer, mode: str, xgb_device: Optional[str]) -> Dict[str, Dict[str, object]]:
    models: Dict[str, Dict[str, object]] = {}

    logistic = Pipeline(
        steps=[
            ("preprocessor", clone(preprocessor)),
            (
                "model",
                LogisticRegression(
                    max_iter=800,
                    solver="liblinear",
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    logistic_grid = {
        "model__C": [0.5, 1.0] if mode == "fast" else [0.1, 0.5, 1.0, 2.0],
        "model__penalty": ["l1", "l2"],
    }
    models["Logistinė regresija"] = {"pipeline": logistic, "param_grid": logistic_grid}

    forest = Pipeline(
        steps=[
            ("preprocessor", clone(preprocessor)),
            (
                "model",
                RandomForestClassifier(
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )
    forest_grid = (
        {
            "model__n_estimators": [120],
            "model__max_depth": [10, None],
            "model__min_samples_split": [2, 5],
        }
        if mode == "fast"
        else {
            "model__n_estimators": [150, 250],
            "model__max_depth": [10, 20, None],
            "model__min_samples_split": [2, 5, 10],
            "model__min_samples_leaf": [1, 2],
        }
    )
    models["Atsitiktinis miškas"] = {"pipeline": forest, "param_grid": forest_grid}

    if xgb is not None and xgb_device is not None:
        scale_pos_weight = 1.0
        xgb_model = Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                (
                    "model",
                    xgb.XGBClassifier(
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=42,
                        n_estimators=150 if mode == "fast" else 250,
                        max_depth=5,
                        learning_rate=0.08,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        tree_method="hist",
                        device=xgb_device,
                        n_jobs=-1,
                        scale_pos_weight=scale_pos_weight,
                    ),
                ),
            ]
        )
        xgb_grid = (
            {
                "model__max_depth": [4, 6],
                "model__learning_rate": [0.05, 0.1],
            }
            if mode == "fast"
            else {
                "model__max_depth": [4, 6, 8],
                "model__learning_rate": [0.03, 0.05, 0.1],
                "model__subsample": [0.8, 1.0],
                "model__colsample_bytree": [0.8, 1.0],
            }
        )
        models["XGBoost"] = {"pipeline": xgb_model, "param_grid": xgb_grid}

    return models



def safe_roc_auc(y_true: pd.Series, scores: np.ndarray) -> float:
    unique = np.unique(y_true)
    if len(unique) < 2:
        return float("nan")
    return roc_auc_score(y_true, scores)



def make_cv(y_train: pd.Series) -> StratifiedKFold:
    min_class_count = int(y_train.value_counts().min())
    n_splits = max(2, min(5, min_class_count))
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)



def extract_feature_names(preprocessor: ColumnTransformer, X_train: pd.DataFrame) -> List[str]:
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        names = []
        for col in X_train.columns:
            names.append(col)
        return names



def save_feature_importance(search: GridSearchCV, model_name: str, X_train: pd.DataFrame, output_dir: str) -> None:
    best_pipeline = search.best_estimator_
    preprocessor = best_pipeline.named_steps["preprocessor"]
    model = best_pipeline.named_steps["model"]

    transformed_names = extract_feature_names(preprocessor, X_train)

    values = None
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    elif hasattr(model, "coef_"):
        coef = model.coef_
        if np.ndim(coef) > 1:
            values = np.abs(coef[0])
        else:
            values = np.abs(coef)

    if values is None:
        return

    n = min(len(values), len(transformed_names))
    importance_df = pd.DataFrame(
        {
            "feature": transformed_names[:n],
            "importance": values[:n],
        }
    ).sort_values("importance", ascending=False)
    importance_df.to_csv(
        os.path.join(output_dir, f"feature_importance_{sanitize_filename(model_name)}.csv"),
        index=False,
        encoding="utf-8-sig",
    )



def sanitize_filename(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "_")
        .replace("ė", "e")
        .replace("ū", "u")
        .replace("š", "s")
        .replace("ž", "z")
        .replace("ą", "a")
        .replace("č", "c")
        .replace("ę", "e")
        .replace("į", "i")
    )



def evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    models: Dict[str, Dict[str, object]],
    output_dir: str,
) -> Tuple[pd.DataFrame, Dict[str, GridSearchCV]]:
    cv = make_cv(y_train)
    scoring = {
        "accuracy": "accuracy",
        "f1": "f1",
        "roc_auc": "roc_auc",
    }

    comparison_rows = []
    searches: Dict[str, GridSearchCV] = {}

    for model_name, config in models.items():
        print(f"Vertinamas modelis: {model_name}")
        pipeline = config["pipeline"]
        param_grid = config["param_grid"]

        start = time.time()
        cv_result = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            n_jobs=1,
            error_score="raise",
        )

        search = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            scoring="f1",
            cv=cv,
            n_jobs=1,
            refit=True,
            verbose=0,
            error_score="raise",
        )
        search.fit(X_train, y_train)
        searches[model_name] = search

        best_pipeline = search.best_estimator_
        y_pred = best_pipeline.predict(X_test)
        if hasattr(best_pipeline, "predict_proba"):
            y_proba = best_pipeline.predict_proba(X_test)[:, 1]
        else:
            y_proba = y_pred.astype(float)

        row = {
            "modelis": model_name,
            "cv_accuracy_mean": np.mean(cv_result["test_accuracy"]),
            "cv_f1_mean": np.mean(cv_result["test_f1"]),
            "cv_roc_auc_mean": np.nanmean(cv_result["test_roc_auc"]),
            "test_accuracy": accuracy_score(y_test, y_pred),
            "test_f1": f1_score(y_test, y_pred, zero_division=0),
            "test_roc_auc": safe_roc_auc(y_test, y_proba),
            "best_params": json.dumps(search.best_params_, ensure_ascii=False),
            "seconds": round(time.time() - start, 2),
        }
        comparison_rows.append(row)

        report_text = classification_report(y_test, y_pred, zero_division=0)
        with open(
            os.path.join(output_dir, f"classification_report_{sanitize_filename(model_name)}.txt"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(report_text)
            f.write("\n\nConfusion matrix:\n")
            f.write(str(confusion_matrix(y_test, y_pred)))
            f.write("\n\nBest params:\n")
            f.write(str(search.best_params_))

        save_feature_importance(search, model_name, X_train, output_dir)

        if plt is not None and len(np.unique(y_test)) == 2:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            plt.figure(figsize=(7, 5))
            plt.plot(fpr, tpr)
            plt.plot([0, 1], [0, 1], linestyle="--")
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title(f"ROC kreivė: {model_name}")
            plt.tight_layout()
            plt.savefig(
                os.path.join(output_dir, f"roc_curve_{sanitize_filename(model_name)}.png"),
                dpi=150,
            )
            plt.close()

    comparison_df = pd.DataFrame(comparison_rows).sort_values(
        by=["test_f1", "test_roc_auc", "cv_f1_mean"], ascending=False
    )
    comparison_df.to_csv(
        os.path.join(output_dir, "model_comparison.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    return comparison_df, searches



def save_best_model(
    comparison_df: pd.DataFrame,
    searches: Dict[str, GridSearchCV],
    output_dir: str,
) -> str:
    best_name = comparison_df.iloc[0]["modelis"]
    best_pipeline = searches[best_name].best_estimator_
    model_path = os.path.join(output_dir, "best_model.joblib")
    joblib.dump(best_pipeline, model_path)

    with open(os.path.join(output_dir, "best_model_summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"Geriausias modelis: {best_name}\n")
        f.write(f"Parametrai: {searches[best_name].best_params_}\n")
        f.write(f"Modelio failas: {model_path}\n")
    return best_name



def main() -> None:
    args = parse_args()
    ensure_output_dir(args.output_dir)

    print("1/8 Įkeliami duomenys...")
    bundle = load_datasets(args.data_dir)

    print("2/8 Konvertuojamos datos ir ruošiami duomenys...")
    bundle = preprocess_dates(bundle)

    print("3/8 Kuriamas kliento lygio duomenų rinkinys...")
    dataset = build_customer_dataset(bundle, args.prediction_days)

    print("4/8 Atliekama pirminė duomenų analizė...")
    save_eda(dataset, args.output_dir)

    print("5/8 Ruošiamos mokymo ir testavimo aibės...")
    X, y, numeric_features, categorical_features = split_features_target(dataset)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    preprocessor = build_preprocessor(numeric_features, categorical_features)

    print("6/8 Inicijuojami modeliai...")
    xgb_device, device_message = resolve_xgboost_device(args.device)
    print(f"Įrenginio informacija: {device_message}")
    models = build_models(preprocessor, args.mode, xgb_device)

    print("7/8 Vykdomas modelių vertinimas ir optimizavimas...")
    comparison_df, searches = evaluate_models(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        models=models,
        output_dir=args.output_dir,
    )

    print("8/8 Išsaugomi galutiniai rezultatai...")
    best_name = save_best_model(comparison_df, searches, args.output_dir)

    with open(os.path.join(args.output_dir, "run_summary.txt"), "w", encoding="utf-8") as f:
        f.write("Vykdymo santrauka\n")
        f.write("================\n")
        f.write(f"Duomenų katalogas: {args.data_dir}\n")
        f.write(f"Rezultatų katalogas: {args.output_dir}\n")
        f.write(f"Įrenginys: {args.device}\n")
        f.write(f"Režimas: {args.mode}\n")
        f.write(f"Prognozavimo langas (dienomis): {args.prediction_days}\n")
        f.write(f"Geriausias modelis: {best_name}\n")
        f.write("\nKlasių pasiskirstymas:\n")
        f.write(str(dataset["target"].value_counts()))

    print("Baigta.")
    print(f"Geriausias modelis: {best_name}")
    print(f"Rezultatai išsaugoti kataloge: {args.output_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nVykdymas nutrauktas vartotojo.")
        sys.exit(1)
    except Exception as exc:
        print(f"Klaida: {exc}")
        raise

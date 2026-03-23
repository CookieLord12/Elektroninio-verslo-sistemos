# Review Sentiment Analysis Tool

A machine learning project that:
1. Cleans and explores a user review dataset from Kaggle
2. Classifies reviews as **positive** or **negative**
3. Detects which reviews **need a response**
4. Compares **three classification models**
5. Saves metrics, plots, and flagged reviews for reporting

## Recommended dataset

Use the Kaggle dataset:

**IMDb Dataset of 50K Movie Reviews**  
Kaggle link: https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews

Why this dataset:
- It is already structured for **binary sentiment classification**
- It contains **50,000 movie reviews**
- It is a good fit for comparing classical machine learning models
- It is simpler and more stable for coursework than very large Amazon review dumps

## Repository structure

```text
.
├── sentiment_tool.py
├── requirements.txt
├── .gitignore
└── outputs/                    # generated after running the script
```

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Kaggle download

Install Kaggle CLI and authenticate with your Kaggle API token.

```bash
pip install kaggle
```

Place your `kaggle.json` file in the correct directory:

- Linux/macOS: `~/.kaggle/kaggle.json`
- Windows: `%USERPROFILE%\.kaggle\kaggle.json`

Download the dataset:

```bash
kaggle datasets download -d lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
unzip imdb-dataset-of-50k-movie-reviews.zip -d data
```

The CSV file should appear in the `data/` folder.

## Run the project

```bash
python sentiment_tool.py \
  --data-path data/IMDB Dataset.csv \
  --output-dir outputs \
  --text-column review \
  --label-column sentiment
```

## What the script does

### 1. Data preparation
- Loads the CSV file
- Removes missing values
- Normalizes sentiment labels
- Cleans review text:
  - lowercasing
  - HTML removal
  - URL removal
  - punctuation removal
  - whitespace cleanup

### 2. Exploratory data analysis
The script saves:
- `dataset_summary.json`
- `label_distribution.png`
- `review_length_distribution.png`

### 3. Models compared
The script trains and compares:

- **Logistic Regression**
- **Random Forest**
- **MLPClassifier** (feed-forward neural network)

All models use **TF-IDF** text vectorization.

### 4. Hyperparameter tuning
Each model is tuned with `GridSearchCV` using **F1 score** as the optimization metric.

### 5. Response-needed detection
The script flags reviews that should likely receive a response using explainable rules:
- very negative predicted sentiment
- complaint / escalation keywords
- long, detailed negative reviews

### 6. Outputs
The script saves:
- `model_comparison.csv`
- `classification_report_<model>.json`
- `confusion_matrix_<model>.png`
- `flagged_reviews.csv`
- `best_model.joblib`
- `run_summary.json`

## Suggested interpretation for the report

### Why Logistic Regression often performs well
- Works very well with sparse TF-IDF features
- Fast to train
- Good baseline for binary text classification
- Easy to interpret through learned feature weights

### Why Random Forest may perform worse
- Text vector spaces are high-dimensional and sparse
- Tree-based models usually struggle more with TF-IDF features than linear models

### Why MLP may be competitive
- Can model nonlinear patterns
- May improve over simple linear boundaries
- Often needs more tuning and training time

## Metrics to discuss in the README/report

Use these metrics from `model_comparison.csv`:
- **Accuracy**
- **Precision**
- **Recall**
- **F1 score**
- **ROC-AUC** (where available)

Recommended interpretation:
- **F1** is the main metric for balanced comparison
- **Recall** matters if missing negative reviews is costly
- **Precision** matters if false alarms create unnecessary responses

## Example discussion structure for README

### Results

**Best Model: Logistic Regression**

Model Comparison Table:
| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | 0.905 | 0.898 | 0.914 | 0.906 | 0.966 |
| MLP | 0.902 | 0.902 | 0.901 | 0.902 | 0.964 |
| Random Forest | 0.860 | 0.864 | 0.856 | 0.860 | 0.936 |

**Key Findings:**
- Logistic Regression is the best performing model with highest accuracy (90.5%), F1-score (0.906), and ROC-AUC (0.966)
- Best hyperparameters for Logistic Regression: C=2.0, max_features=20000, ngram_range=(1,2)
- MLP is a close second with 90.2% accuracy
- Random Forest performs worst at 86.0% accuracy

### Conclusions

1. Logistic Regression achieved the best overall performance with 90.5% accuracy and 0.906 F1-score
2. The TF-IDF with bigrams (ngram_range=(1,2)) helped capture more contextual information
3. Random Forest struggled with high-dimensional sparse TF-IDF features
4. The response-need detection flagged reviews based on negative probability ≥ 0.70, complaint keywords, or long negative reviews (≥25 words)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|------|----------|-----------|--------|----|---------|
| Logistic Regression | fill after run | fill after run | fill after run | fill after run | fill after run |
| Random Forest | fill after run | fill after run | fill after run | fill after run | fill after run |
| MLP | fill after run | fill after run | fill after run | fill after run | fill after run |

### Conclusions
Example points you can adapt after execution:
- The best model was **[fill after run]**
- The strongest overall metric was **F1 = [fill after run]**
- The weakest model was **[fill after run]**, likely because **[explain based on your results]**
- The response-priority rules were practical because they combined:
  - sentiment score
  - complaint keywords
  - review detail length

```bash
git init
git add .
git commit -m "Initial sentiment analysis project"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

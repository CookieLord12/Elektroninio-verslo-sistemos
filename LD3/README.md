python ecommerce_purchase_prediction.py --data-dir ./data/olist --output-dir ./results --device auto --prediction-days 365

# Klientų būsimų pirkimų prognozavimo projektas

Ši programa analizuoja Olist e. prekybos duomenis, atlieka duomenų paruošimą, pirminę analizę, apmoko kelis mašininio mokymosi modelius ir parenka geriausią modelį pagal kryžminio patikrinimo rezultatus.

## Kaip naudoti

### 1. Įdėkite failus į teisingą katalogą
Programa tikisi, kad nurodytame `--data-dir` kataloge bus šie CSV failai:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`

Rekomenduojama katalogų struktūra:

```text
lab3/
├── ecommerce_purchase_prediction.py
├── README_lt.md
├── data/
│   └── olist/
│       ├── olist_customers_dataset.csv
│       ├── olist_orders_dataset.csv
│       ├── olist_order_items_dataset.csv
│       ├── olist_products_dataset.csv
│       ├── olist_order_payments_dataset.csv
│       └── olist_order_reviews_dataset.csv
```

### 2. Paleidimo komanda
Paleiskite programą iš katalogo, kuriame yra `ecommerce_purchase_prediction.py` failas:

```bash
python ecommerce_purchase_prediction.py --data-dir ./data/olist --output-dir ./results --device auto --prediction-days 365
```

### 3. Ką reiškia komandos parametrai

- `--data-dir ./data/olist` – katalogas, kuriame yra Olist CSV failai.
- `--output-dir ./results` – katalogas, į kurį bus išsaugoti visi rezultatai.
- `--device auto` – programa automatiškai bandys naudoti GPU XGBoost modeliui, jei kompiuteryje yra CUDA palaikantis GPU. Jei GPU nerandamas, bus naudojamas CPU.
- `--prediction-days 365` – naudojamas duomenų laikotarpis.

## Įrenginio režimai

Programa palaiko tris įrenginio parinktis:

```bash
python ecommerce_purchase_prediction.py --data-dir ./data/olist --output-dir ./results --device auto
python ecommerce_purchase_prediction.py --data-dir ./data/olist --output-dir ./results --device cpu
python ecommerce_purchase_prediction.py --data-dir ./data/olist --output-dir ./results --device gpu
```

### Paaiškinimas

- `auto` – geriausias pasirinkimas daugeliu atvejų. Jei yra GPU, XGBoost veiks per GPU, kitu atveju per CPU.
- `cpu` – priverstinai naudoja CPU.
- `gpu` – priverstinai reikalauja GPU. Jei CUDA GPU nerandamas, programa baigs darbą su aiškia klaida.

Svarbu: GPU palaikymas taikomas tik XGBoost modeliui. Logistinė regresija ir atsitiktinis miškas šiame projekte veikia per CPU.

## Ką daro programa

Programa vykdo visus užduoties etapus:

1. Įkelia realaus pasaulio e. prekybos duomenis.
2. Atlieka duomenų valymą ir paruošimą.
3. Sukuria kliento lygio požymius iš užsakymų istorijos.
4. Apibrėžia tikslinį kintamąjį: ar klientas pakartos pirkimą per 90 dienų.
5. Atlieka pirminę duomenų analizę ir vizualizacijas.
6. Apmoko tris modelius:
   - logistinę regresiją,
   - atsitiktinį mišką,
   - XGBoost.
7. Atlieka kryžminį patikrinimą.
8. Lygina modelius pagal `Accuracy`, `F1` ir `ROC AUC`.
9. Parenka geriausią modelį.
10. Atlieka hiperparametrų optimizavimą.
11. Išsaugo geriausią modelį ir ataskaitas.

## Kokie rezultatai sukuriami

Po paleidimo `--output-dir` kataloge atsiras:

- `prepared_customer_dataset.csv` – paruoštas analizės duomenų rinkinys.
- `model_comparison.csv` – modelių palyginimas.
- `best_model_metrics.txt` – geriausio modelio metrikos.
- `best_model.joblib` – išsaugotas geriausias modelis.
- `summary_lt.txt` – trumpa lietuviška projekto santrauka.
- `roc_curve_best_model.png` – ROC kreivė.
- `confusion_matrix_best_model.png` – konfuzijos matrica.
- `top_feature_importance.csv` – svarbiausių požymių sąrašas.
- `top_feature_importance.png` – požymių svarbos grafikas.
- `eda/` katalogas su papildomais EDA failais ir grafikais.

## Reikalingos bibliotekos

Įsidiekite šias Python bibliotekas:

```bash
pip install pandas numpy matplotlib scikit-learn joblib xgboost torch
```

### Pastaba dėl GPU

- `torch` šiame projekte naudojamas tik CUDA GPU prieinamumui patikrinti.
- Jei nenorite GPU tikrinimo, galite naudoti `--device cpu` ir neįdiegti GPU skirtos Torch versijos.
- Jei naudojate `--device auto` arba `--device gpu`, rekomenduojama turėti veikiančią CUDA aplinką.

## Jei gaunate klaidą dėl trūkstamų failų

Jei matote klaidą apie trūkstamus CSV failus, tai reiškia, kad nurodytame `--data-dir` kataloge nėra visų reikalingų Olist failų. Reikia patikrinti:

1. ar katalogas tikrai egzistuoja,
2. ar failų pavadinimai sutampa tiksliai,
3. ar CSV failai nėra palikti ZIP archyve.

## Jei gaunate klaidą dėl XGBoost

Jei neįdiegta `xgboost`, programa vis tiek veiks, bet praleis XGBoost modelį ir lygins tik logistinę regresiją bei atsitiktinį mišką.

## Trumpa metodikos logika

Šis projektas orientuotas į klasifikavimo uždavinį. Tikslas yra iš istorinių pirkimų duomenų nustatyti, ar klientas pakartos pirkimą per 90 dienų. Tam iš užsakymų, mokėjimų, produktų ir atsiliepimų lentelių sugeneruojami požymiai, kurie apibūdina kliento elgseną:

- pirkimų dažnį,
- bendrą išleistą sumą,
- vidutinę užsakymo vertę,
- pristatymo vėlavimus,
- atsiliepimų vertinimus,
- pirkimo laiką,
- produktų charakteristikas.

Tada modeliai lyginami, o geriausias pasirenkamas pagal F1 rodiklį, nes klasės gali būti nesubalansuotos.

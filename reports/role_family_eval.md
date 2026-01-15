# Role Family Classifier Evaluation

- Labeled rows used: 250
- Classes: bi_analyst, data_analyst, data_engineer, ml_engineer, other
- Split: 80/20

## Classification Report

```text
               precision    recall  f1-score   support

   bi_analyst       1.00      0.83      0.91         6
 data_analyst       0.71      1.00      0.83         5
data_engineer       0.75      1.00      0.86         6
  ml_engineer       0.89      0.67      0.76        12
        other       0.81      0.81      0.81        21

     accuracy                           0.82        50
    macro avg       0.83      0.86      0.83        50
 weighted avg       0.83      0.82      0.82        50

```

## Artifacts

- Model: models/role_family_clf.joblib
- Confusion matrix: reports/role_family_confusion.png
- Error examples: reports/role_family_errors.csv

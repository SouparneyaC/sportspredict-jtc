# ML Methodology Deep Dive: Gradient Boosting & Neural Networks for Tabular Data

**Purpose of this document.** Generic, reusable reference notes on gradient-boosted
trees (XGBoost, LightGBM, CatBoost) and neural networks for tabular/structured
data — methodology, hyperparameters, data prep, evaluation, calibration,
interpretability, and pitfalls. Written for a future AI assistant picking up a
*different* tabular ML project. Not specific to any one dataset or domain.
Citations include paper title/authors/year and a URL for re-lookup.

---

## 1. DECISION CHECKLIST (read this first)

### 1.1 GBT vs Neural Network — which to use?
- **Default to GBT (XGBoost/LightGBM/CatBoost) for tabular data**, especially
  when n ≲ 50k–100k rows and features are heterogeneous (mix of numeric,
  ordinal, categorical, with irregular/non-smooth relationships). Empirically,
  tree ensembles remain state-of-the-art on "medium-sized" tabular data
  (~10k rows) even before accounting for their large speed advantage.
  — Grinsztajn, Oyallon & Varoquaux, "Why do tree-based models still
  outperform deep learning on tabular data?" (NeurIPS 2022 Datasets &
  Benchmarks), https://arxiv.org/abs/2207.08815
- **NNs become more competitive when**: dataset is very large (≥ ~100k–1M
  rows), you need to fuse tabular features with unstructured data
  (text/images/embeddings) in one model, you need representation learning
  (e.g., entity embeddings to feed into another model), or you're building an
  ensemble and want a model with *different* error structure than trees.
- **Why trees tend to win** (per Grinsztajn et al.): NNs are biased toward
  overly *smooth* solutions and struggle when (a) the data contains
  uninformative/irrelevant features, (b) the data is *not rotationally
  invariant* (i.e., individual raw features carry meaning — true of almost
  all tabular data, unlike pixels), and (c) the target function has
  irregular, non-smooth patterns that trees capture naturally via splits.
- **Practical rule of thumb**: if you have < 1 day of compute budget and a
  dataset under ~100k rows, start with LightGBM or CatBoost. Reserve NN
  experiments for when you have a specific reason (huge data, embeddings,
  multi-modal fusion, or you've already squeezed GBT and want an ensemble
  partner).

### 1.2 Train/validation/test splitting — temporal data
- **If your data has any time ordering (panel data, time series, sequential
  events), do NOT use random k-fold CV.** Random folds let future
  information leak into training (e.g., training on a match from 2020 to
  predict a match from 2015), producing optimistic, unrealistic performance
  estimates.
- **Default: walk-forward / rolling-origin evaluation.** Train on data up to
  time T, validate/test on data after T; roll T forward and repeat. This
  mimics how the model will actually be used (forecasting forward in time).
  — Hyndman & Athanasopoulos, *Forecasting: Principles and Practice*,
  "Time series cross-validation" / "evaluation on a rolling forecasting
  origin", https://otexts.com/fpp3/ (see also Rob Hyndman's blog post
  "Cross-validation for time series", https://robjhyndman.com/hyndsight/tscv/)
- **Nuance**: Bergmeir & Benítez (2012) and later Bergmeir, Hyndman & Koo
  (2015) showed that for *purely autoregressive* models (where residuals are
  uncorrelated given the inputs — which covers many ML feature-based
  approaches), standard *blocked* k-fold CV can still give valid, often more
  *robust* model-selection estimates than a single rolling-origin holdout,
  because it uses more of the data for validation. — Bergmeir & Benítez
  (2012), "On the use of cross-validation for time series predictor
  evaluation", https://www.researchgate.net/publication/256720783; Bergmeir,
  Hyndman & Koo (2015) on CV for autoregressions.
- **Practical heuristic**: 
  - If your model has *any* features that look backward (lags, rolling
    stats, ratings updated over time) — use rolling-origin / walk-forward by
    default.
  - If you want a more sample-efficient estimate AND you're confident your
    features fully encapsulate "state as of time T" (no leakage of raw
    future values), a *blocked* k-fold (contiguous time blocks, never
    shuffled) is a reasonable secondary check — but always report the
    walk-forward number as the primary one, since that's the deployment
    scenario.
  - Always leave a final, never-touched **holdout test set** that is the most
    recent chunk of time, used only once at the very end.

### 1.3 Categorical encoding — what to use
- **CatBoost**: pass categorical columns natively (as `cat_features` indices)
  — it has the most sophisticated and leakage-resistant native handling
  (ordered target statistics). Don't one-hot or label-encode first.
- **LightGBM**: supports native categorical handling (`categorical_feature`
  param) using a histogram-based partitioning of categories into two groups —
  works well for moderate cardinality. Still reasonable to label-encode
  first if you want determinism across versions.
- **XGBoost**: native categorical support exists since v1.6+ (`enable_categorical=True`,
  dtype `category`), using a similar partitioning approach to LightGBM, but
  historically XGBoost users one-hot or target-encode. For low-cardinality
  (< ~10 levels), one-hot is fine; for high cardinality, prefer native
  categorical support or target encoding.
- **Neural networks**: use **entity embeddings** (learned dense vectors per
  category, typically dimension ≈ min(50, round(cardinality^0.25 × constant))
  or simply `min(50, (cardinality+1)//2)` as a starting heuristic) rather than
  one-hot for anything with more than ~10–15 categories. — Guo & Berkhahn
  (2016), "Entity Embeddings of Categorical Variables",
  https://arxiv.org/abs/1604.06737
- **Target/mean encoding** (any model): powerful for high-cardinality
  categoricals but **must be computed out-of-fold** (K-fold cross-fitting:
  encode each fold using statistics computed only from the *other* folds) to
  avoid leakage. Add smoothing toward the global mean for rare categories.
  Even with out-of-fold encoding, be wary of *time* leakage too — for
  temporal data, compute target encodings using only *past* data relative to
  each row (expanding-window encoding), not the whole training set.
- **One-hot**: fine for low-cardinality (≲ 10–15 levels) categoricals in any
  model; avoid for high cardinality (curse of dimensionality, sparse
  columns, slows tree-building unless using exclusive feature bundling).
- **Ordinal encoding**: appropriate only when categories have a genuine
  order (e.g., "low/medium/high"); arbitrary ordinal encoding of nominal
  categories can mislead trees into spurious split orderings (less harmful
  for trees than for linear/NN models, but still avoid when avoidable).

### 1.4 Feature scaling
- **GBT (XGBoost/LightGBM/CatBoost): no scaling needed.** Trees split on
  thresholds; monotonic transformations of a feature don't change the
  splits. Skip standardization/normalization entirely for these models.
- **NNs: scaling is required.** Standardize (zero mean, unit variance) or
  normalize numeric features; use the *training set's* statistics to
  transform validation/test (never refit scalers on val/test). For
  highly skewed features, consider log/Box-Cox transforms before scaling.

### 1.5 Missing data
- **GBT: handle natively, don't impute.** XGBoost and LightGBM learn an
  optimal "default direction" for missing values at each split (i.e., they
  treat "missing" as informative and route those rows wherever it minimizes
  loss). CatBoost handles numeric NaNs natively but may need an explicit
  placeholder category for missing categoricals. — comparison summarized in
  multiple practitioner write-ups, e.g.
  https://coder-wang-uspsa.medium.com/how-do-xgboost-lightgbm-and-catboost-handle-missing-features-e541da94d528
  (cross-check against official docs since blog posts can be imprecise).
  **Practical takeaway: feed NaNs directly to GBT models; do not
  mean/median-impute, as that can destroy the "missingness is informative"
  signal and can also bias the data if missingness is not random.**
- **NNs: must impute** (median/mean for numeric, a dedicated "missing"
  category or learned embedding for categoricals) since NNs cannot handle
  NaN inputs directly. Consider also adding a binary "was_missing" indicator
  column — lets the network learn from the missingness pattern itself.

### 1.6 Hyperparameter tuning workflow (high level)
1. Start with library defaults / "sane starting points" (Section 4) and a
   single train/val split (or rolling-origin folds) to sanity-check the
   pipeline.
2. Use **early stopping** on a validation set (not the test set) to pick
   `n_estimators`/`num_boost_round` automatically — this is the single
   highest-value "tuning" step and should always be on.
3. For the remaining hyperparameters (depth/leaves, learning rate,
   regularization, subsampling), use **random search** or **Bayesian
   optimization** (Optuna/Hyperopt) over a *moderate* number of trials
   (50–200 is often plenty for GBT). Random search strictly dominates grid
   search at equal compute because typically only 2–4 hyperparameters matter
   much. — Bergstra & Bengio (2012), "Random Search for Hyper-Parameter
   Optimization", JMLR 13:281-305, https://jmlr.org/papers/v13/bergstra12a.html
4. If reporting a final performance number for a paper/decision, use
   **nested cross-validation** (or nested rolling-origin): an outer loop for
   performance estimation, an inner loop for hyperparameter selection — this
   avoids the optimistic bias of tuning and evaluating on the same split.
5. **Never tune on the final test set.** If you peek at test performance
   while iterating on features/hyperparameters, that set is no longer a
   valid test set — treat it as now part of "validation" and find/reserve a
   fresh test set if a final unbiased number is needed.

### 1.7 Calibration
- GBT models (boosted trees/stumps especially) tend to produce
  **under-confident, sigmoid-shaped distorted probabilities** — pushed away
  from 0 and 1. Plan to **calibrate** (Platt scaling or isotonic regression)
  using a held-out calibration set, especially if probabilities themselves
  (not just rankings/classifications) matter for your use case. — Niculescu-
  Mizil & Caruana (2005), "Predicting Good Probabilities With Supervised
  Learning", ICML 2005, https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Always plot a **reliability diagram / calibration curve** before and after
  calibration to visually confirm improvement, and compute Brier score /
  log loss before vs after.

---

## 2. GRADIENT BOOSTING FUNDAMENTALS

### 2.1 Friedman (2001) — the core idea
- **Citation**: Friedman, J.H. (2001), "Greedy Function Approximation: A
  Gradient Boosting Machine", *Annals of Statistics* 29(5):1189-1232.
  https://projecteuclid.org/journals/annals-of-statistics/volume-29/issue-5/Greedy-function-approximation-A-gradient-boosting-machine/10.1214/aos/1013203451.full
- **Core mechanism**: Treat function estimation as numerical optimization in
  *function space* rather than parameter space. Build the model additively,
  stage by stage: at each stage, fit a new "weak learner" (e.g., a small
  decision tree) to the **negative gradient of the loss function** evaluated
  at the current ensemble's predictions (i.e., to the "pseudo-residuals").
  This is literally gradient descent, where each step's "direction" is itself
  approximated by a tree.
- **Generality**: the framework works for *any* differentiable loss —
  squared error and Huber loss for regression, multiclass logistic
  (cross-entropy) for classification, etc. This is why GBT libraries support
  custom objective functions.
- **TreeBoost**: when the weak learners are decision trees specifically,
  Friedman derives extra refinements (e.g., re-estimating optimal leaf values
  given the loss, after the tree structure is chosen by the gradient fit).
  This produces models that are robust to "messy" data (outliers, mixed
  scales) and naturally handle non-linearities and interactions — major
  reasons GBT works so well on real-world tabular data.
- **Shrinkage / learning rate**: Friedman also introduced the idea of
  multiplying each new tree's contribution by a small "shrinkage" factor
  (the learning rate) — smaller steps, more trees, but better generalization.
  This is the ancestor of the `learning_rate`/`eta` hyperparameter in every
  modern GBT library.

### 2.2 XGBoost (Chen & Guestrin, 2016)
- **Citation**: Chen, T. & Guestrin, C. (2016), "XGBoost: A Scalable Tree
  Boosting System", KDD 2016. https://arxiv.org/abs/1603.02754 (also see
  https://xgboosting.com/xgboost-paper/ for a practitioner summary)
- **Key contributions over vanilla gradient boosting**:
  - **Regularized objective**: adds explicit L1 (`alpha`) and L2 (`lambda`)
    penalties on leaf weights, plus a penalty `gamma` on the number of
    leaves — directly controls overfitting via the *objective function*,
    not just via tree-depth heuristics.
  - **Second-order (Newton) approximation**: uses both gradient *and*
    Hessian of the loss to find optimal split points and leaf values —
    more accurate per-step updates than first-order gradient boosting.
  - **Sparsity-aware split finding / "default direction"**: for any feature
    with missing values (or sparse zeros from one-hot encoding), XGBoost
    learns, per split, which direction (left/right) missing values should go
    — letting it handle missing data and sparse features without imputation.
  - **Weighted quantile sketch**: an approximate algorithm for proposing
    candidate split points on large datasets, balancing accuracy and speed
    (relevant for the `tree_method='hist'`/`'approx'` settings).
  - **System engineering**: cache-aware access patterns, out-of-core
    computation for data larger than RAM, and parallelization — important
    for scalability but not core to "what the model learns."

### 2.3 LightGBM (Ke et al., 2017)
- **Citation**: Ke, G. et al. (2017), "LightGBM: A Highly Efficient Gradient
  Boosting Decision Tree", NeurIPS 2017.
  https://www.semanticscholar.org/paper/LightGBM:-A-Highly-Efficient-Gradient-Boosting-Tree-Ke-Meng/497e4b08279d69513e4d2313a7fd9a55dfb73273
  (search "LightGBM NeurIPS 2017 paper" for the NeurIPS proceedings PDF)
- **Key contributions**:
  - **Histogram-based split finding**: continuous features are bucketed into
    discrete bins (default 255), and split-gain is computed over histogram
    bins rather than scanning every unique value — much faster, lower
    memory, with negligible accuracy loss.
  - **Leaf-wise (best-first) tree growth** instead of level-wise: at each
    step, split the single leaf with the largest loss reduction, regardless
    of its depth. This produces deeper, more asymmetric trees that often fit
    better for a given leaf budget — but **is more prone to overfitting on
    small datasets**, hence `num_leaves` (not `max_depth`) is the primary
    complexity control, often paired with a `max_depth` cap as a guardrail.
  - **GOSS (Gradient-based One-Side Sampling)**: keeps all instances with
    large gradients (poorly-fit, "important" examples) but randomly
    subsamples instances with small gradients (already well-fit) when
    estimating split gain — speeds up training while preserving accuracy,
    because large-gradient instances dominate the information gain
    computation.
  - **EFB (Exclusive Feature Bundling)**: many sparse features (e.g., one-hot
    encoded categoricals) are "mutually exclusive" (rarely both nonzero for
    the same row); EFB bundles such features into a single feature, reducing
    dimensionality with minimal information loss.
  - **Combined effect**: GOSS + EFB reported to give >20x speedups on some
    benchmarks vs. naive implementations with near-identical accuracy.
  - **Practical implication**: LightGBM is typically the fastest of the
    three on large datasets and is a strong default; but its leaf-wise growth
    means it can overfit small datasets faster than XGBoost's level-wise
    default — watch validation curves carefully and keep `num_leaves` modest
    for small n.

### 2.4 CatBoost (Prokhorenkova et al., 2018)
- **Citation**: Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A.V. &
  Gulin, A. (2018), "CatBoost: unbiased boosting with categorical features",
  NeurIPS 2018. https://arxiv.org/abs/1706.09516
- **Core problem identified — "prediction shift"**: in standard gradient
  boosting, each tree is fit on residuals computed using the *same data
  points* used to build all previous trees. This creates a subtle target
  leakage: the residual for a training example is influenced by the fact
  that the model has already "seen" that example's target during earlier
  stages. This biases the learned function and causes a distribution shift
  between training-time residuals and test-time residuals ("prediction
  shift"). The same root issue also corrupts naive target-statistic
  encodings of categorical features (a category's encoded value is computed
  using its own target).
- **Fix 1 — Ordered Target Statistics (categorical encoding)**: instead of
  encoding a categorical value using statistics from the *whole* dataset (or
  even the whole training fold), CatBoost uses a **random permutation of the
  training data** and, for each example, computes the categorical statistic
  using only examples that come *before* it in that permutation (an
  "artificial time" ordering). Multiple random permutations are used across
  the boosting process to reduce variance. This prevents a category's
  encoding for row i from depending on row i's own target.
- **Fix 2 — Ordered Boosting**: extends the same "use only data that comes
  before this example in a random permutation" principle to the residual
  computation itself — when training the model that will predict the
  residual for example i, only use a model trained on examples that precede
  i in the permutation. This directly attacks prediction shift at its source
  (not just in categorical encoding).
- **Native categorical handling**: combines ordered target statistics with
  automatic combination of categorical features (CatBoost can also generate
  new features by combining pairs/groups of categorical columns) — pass raw
  category columns via `cat_features`; do not pre-encode.
- **Practical implication**: CatBoost often gives the best out-of-the-box
  results on datasets with many/high-cardinality categorical features and
  needs comparatively less hyperparameter tuning, at some cost in training
  speed vs. LightGBM. Symmetric ("oblivious") trees by default — every node
  at a given depth uses the *same* split condition, which acts as a
  regularizer and speeds up inference.

### 2.5 Hyperparameters — concrete ranges and tuning heuristics

General principle: **learning rate and number of trees trade off** —
lower learning rate + more trees (with early stopping) ≈ better
generalization at the cost of training time. Tune complexity/regularization
parameters together; tune learning rate last (or fix it low and let early
stopping pick the tree count).

| Parameter (XGB / LGBM / CatBoost names) | Typical range | Notes |
|---|---|---|
| Learning rate (`eta` / `learning_rate` / `learning_rate`) | 0.01 – 0.3; common default search 0.005–0.1 | Lower = more robust but needs more trees + early stopping. Start at 0.05–0.1 for exploration, drop to 0.01–0.03 for final models. |
| Number of trees (`n_estimators`/`num_boost_round` / `num_iterations` / `iterations`) | 100 – 5000+ | Set high (e.g. 2000–5000) and rely on **early stopping** against a validation set rather than tuning this directly. |
| Max depth (`max_depth`) — XGB, CatBoost | 3 – 10; commonly 4–8 | Shallower (3–6) for noisy/small data; CatBoost default depth is 6 and rarely needs to exceed ~8–10 due to symmetric trees. |
| Num leaves (`num_leaves`) — LightGBM | 16 – 255; rule of thumb ≲ 2^(max_depth) | Because LightGBM grows leaf-wise, `num_leaves` is the primary complexity knob. A common guard: `num_leaves < 2^max_depth` and pair with a `max_depth` cap (e.g., 6–8) to prevent runaway overfitting on small data. |
| Min child weight / min data in leaf (`min_child_weight` / `min_data_in_leaf` / `min_data_in_leaf`) | 1 – 100+ (scale with dataset size) | Higher values = more conservative, less overfitting on small/noisy datasets. For small n (thousands of rows), try 20–100. |
| Subsample (row sampling) (`subsample` / `bagging_fraction` / `subsample`) | 0.5 – 1.0; common 0.7–0.9 | < 1.0 adds stochasticity (regularization) and speeds training; pair with `bagging_freq` in LightGBM (e.g., every 1–5 iterations). |
| Column subsample (`colsample_bytree`/`colsample_bylevel`/`colsample_bynode` / `feature_fraction` / `rsm`) | 0.5 – 1.0; common 0.6–0.9 | Reduces correlation between trees; especially useful with many correlated features. |
| L2 regularization (`lambda`/`reg_lambda` / `lambda_l2` / `l2_leaf_reg`) | 0 – 10+ (CatBoost default 3) | Shrinks leaf weights toward 0; increase if overfitting. |
| L1 regularization (`alpha`/`reg_alpha` / `lambda_l1`) | 0 – 5 | Encourages sparsity in leaf weights; less commonly tuned than L2. |
| Min split gain / gamma (`gamma` / `min_gain_to_split`/`min_split_gain`) | 0 – 5 | Minimum loss reduction required to make a further split — higher = more conservative trees. |
| Early stopping rounds | 20 – 100 (or ~5–10% of max n_estimators) | Stop training when validation metric hasn't improved for N rounds; always use a held-out validation set distinct from the test set. |
| Max bin (`max_bin`) — LightGBM/hist methods | 63 – 255 (default 255) | Lower = faster/less memory, slight accuracy cost; rarely needs tuning beyond defaults. |

- **Sources for these ranges**: cross-checked against multiple practitioner
  guides, e.g. https://www.analyticsvidhya.com/blog/2016/03/complete-guide-parameter-tuning-xgboost-with-codes-python/
  and general GBT comparison write-ups
  (https://www.ml4devs.com/what-is/gradient-boosting-machines-xgboost-lightgbm-catboost/).
  These are *starting points* for random/Bayesian search, not gospel — always
  validate against your own validation curves.
- **Tuning order heuristic** (common practitioner approach):
  1. Fix a moderate learning rate (e.g., 0.05–0.1) and a generous
     `n_estimators` with early stopping.
  2. Tune tree-structure params (`max_depth`/`num_leaves`,
     `min_child_weight`/`min_data_in_leaf`) — these have the largest effect
     on overfitting.
  3. Tune sampling params (`subsample`, `colsample_bytree`).
  4. Tune regularization (`lambda`, `alpha`, `gamma`/`min_split_gain`).
  5. Finally, lower the learning rate (e.g., to 0.01–0.03), increase
     `n_estimators` proportionally, and re-run early stopping for the final
     model — typically gives a small final accuracy bump.

---

## 3. NEURAL NETWORKS FOR TABULAR DATA

### 3.1 When NNs are worth it — Grinsztajn et al. (2022)
- **Citation**: Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022), "Why do
  tree-based models still outperform deep learning on tabular data?",
  NeurIPS 2022 Datasets and Benchmarks Track. https://arxiv.org/abs/2207.08815
- **Setup**: 45 tabular datasets, extensive hyperparameter search (~20,000
  compute-hours per learner type), comparing tree ensembles (XGBoost, Random
  Forest, GBT) vs. NN architectures (MLP, ResNet, FT-Transformer, etc.).
- **Headline finding**: tree-based models remain SOTA on medium-sized tabular
  data (~10k samples), even ignoring their speed advantage.
- **Three identified reasons NNs underperform on typical tabular data**
  (these double as a checklist for *why* a given dataset might favor trees):
  1. **NNs are biased toward overly smooth solutions**, but tabular target
     functions are often **irregular / non-smooth** — trees, which partition
     space into axis-aligned regions, naturally fit such functions.
  2. **Uninformative features hurt NNs more than trees.** Trees can
     effectively ignore irrelevant features (they're just never selected for
     splits); NNs, especially with dense connections, tend to assign nonzero
     weight to noise features, degrading performance.
  3. **Tabular data is not rotation-invariant** — i.e., each column has its
     own distinct meaning/scale, unlike pixels in an image (where rotating
     the whole input is roughly meaningless). NN architectures with
     rotation-invariant inductive biases (e.g., dense layers that mix all
     inputs symmetrically) are mismatched to this structure; trees, which
     consider one feature at a time for each split, naturally respect this.
- **Implication for future NN architecture design** (per the paper's stated
  challenges): a tabular-specific NN should (a) be robust to irrelevant
  features, (b) preserve/respect feature-wise (non-rotation-invariant)
  structure, and (c) be capable of learning sharp/irregular decision
  boundaries.

### 3.2 Modern tabular NN architectures — Gorishniy et al. (2021)
- **Citation**: Gorishniy, Y., Rubachev, I., Khrulkov, V. & Babenko, A.
  (2021), "Revisiting Deep Learning Models for Tabular Data", NeurIPS 2021.
  https://arxiv.org/abs/2106.11959 ; code:
  https://github.com/yandex-research/rtdl-revisiting-models
- **Key takeaways**:
  - **A well-tuned ResNet-like MLP (with skip connections + batch/layer
    norm) is a surprisingly strong, simple baseline** — much prior "novel"
    tabular DL work failed to outperform it. **Always implement this MLP+
    ResNet baseline before reaching for something fancier.**
  - **FT-Transformer** ("Feature Tokenizer + Transformer"): converts each
    feature (numeric or categorical) into an embedding ("token"), then
    applies a standard Transformer encoder over the sequence of feature
    tokens (plus a [CLS]-like token for the final prediction). It performs
    competitively across the board — on problems where GBT beats the ResNet
    baseline, FT-Transformer captures most of GBT's advantage; on problems
    where ResNet matches GBT, FT-Transformer also matches. I.e.,
    **FT-Transformer is the more "universally competitive" NN choice** but at
    higher computational cost and complexity than an MLP.
  - **Practical recommendation**: for a new tabular project, (1) try
    LightGBM/CatBoost first, (2) if NN is needed (see Section 1.1 triggers),
    start with the ResNet-MLP baseline, (3) only move to FT-Transformer if
    the simpler MLP underperforms GBT by a meaningful margin and the extra
    complexity is justified (e.g., because you'll later fuse in non-tabular
    inputs where Transformers are natural).

### 3.3 Entity embeddings for categorical variables — Guo & Berkhahn (2016)
- **Citation**: Guo, C. & Berkhahn, F. (2016), "Entity Embeddings of
  Categorical Variables", https://arxiv.org/abs/1604.06737
- **Idea**: map each categorical value to a learned dense vector (embedding),
  trained jointly with the rest of the network via backprop — analogous to
  word embeddings in NLP. Concatenate embeddings with numeric inputs before
  the dense layers.
- **Benefits**:
  - Dramatically reduces input dimensionality vs. one-hot for high-cardinality
    categoricals (e.g., thousands of store IDs, postal codes, team names).
  - The learned embedding space often reveals **semantically meaningful
    structure** (similar categories end up close together) — useful for
    interpretability and can even be reused as features for *other* models
    (e.g., extract the embeddings and feed them into a GBT model).
  - Helps generalization on sparse/rare categories compared to one-hot,
    because the network can share statistical strength across similar
    categories via the embedding geometry.
  - Demonstrated practical success in a Kaggle competition (3rd place) using
    relatively simple features plus entity embeddings.
- **Practical sizing heuristic**: embedding dimension ≈ `min(50, ceil(cardinality**0.25 * 4))`
  or simply `min(50, (cardinality + 1) // 2)` as a rough starting point;
  tune as a hyperparameter for important high-cardinality features.

### 3.4 Practical NN architecture choices
- **Simple MLP baseline**: 2–4 hidden layers, widths ~64–512, ReLU/GELU
  activations, batch normalization or layer normalization, dropout
  (0.1–0.5) for regularization, residual/skip connections if >2 layers
  (per the ResNet-style baseline in Gorishniy et al.). Use Adam/AdamW
  optimizer, learning rate ~1e-3 to 1e-4 with a scheduler (cosine decay or
  reduce-on-plateau), and **early stopping** on validation loss.
- **TabNet**: an attention-based architecture with built-in feature
  selection (sequential attention over features) and some interpretability
  benefits; in independent benchmarks it often does *not* clearly beat
  well-tuned GBT or even MLP baselines, and is more finicky to train. Treat
  as a "nice to try if time permits" rather than a default.
- **FT-Transformer**: worth it when (a) GBT clearly outperforms a tuned MLP
  on your data (signaling irregular/interaction-heavy structure that
  attention can capture), or (b) you anticipate combining tabular features
  with other token-sequence inputs in one model.
- **General NN tabular tips**:
  - Normalize/standardize numeric inputs (Section 1.4).
  - Use embeddings for categoricals (Section 3.3), not one-hot, beyond
    trivial cardinality.
  - Watch for overfitting aggressively — NNs on small tabular data overfit
    fast; use dropout, weight decay, and early stopping together.
  - Ensemble multiple NN seeds (different random initializations) — NN
    training variance across seeds can be substantial on tabular data;
    averaging predictions across 5–10 seeds is a cheap, reliable improvement.

---

## 4. DATA PREPARATION METHODOLOGY (DETAIL)

### 4.1 Temporal train/val/test splitting (expanded)
- **Walk-forward / rolling-origin cross-validation**: 
  - Split the timeline into successive "origins" T1 < T2 < ... < Tk.
  - For each origin Ti: train on all data with timestamp ≤ Ti, evaluate on
    data in (Ti, Ti + horizon].
  - Aggregate evaluation metrics across all origins for a robust estimate of
    "how well would this modeling approach have performed if deployed
    historically, retrained periodically."
  - Reference: Hyndman & Athanasopoulos, *Forecasting: Principles and
    Practice* (3rd ed.), chapter on time series cross-validation,
    https://otexts.com/fpp3/ — also Rob Hyndman's blog,
    https://robjhyndman.com/hyndsight/tscv/
- **Why random k-fold fails for temporal data**: standard k-fold shuffles
  rows randomly into folds, so a model can be trained on data from *after*
  the point it's being asked to predict — this is **temporal leakage** and
  produces metrics that look far better than real-world deployment
  performance, especially for any model using time-dependent features
  (ratings, rolling averages, recent form, etc.).
- **Blocked k-fold**: a middle ground — split the timeline into K contiguous
  blocks (no shuffling within a block's time order, but the blocks
  themselves can serve as folds in a leave-one-block-out scheme). Bergmeir &
  Benítez (2012) found this can give *more robust* model-selection signal
  than a single train/test split for autoregressive-style models, because it
  uses more data for evaluation — but it does **not** eliminate leakage
  if your features depend on values close in time to the targets being
  predicted (be careful with features computed using rolling windows that
  span fold boundaries).
- **Final holdout**: regardless of CV scheme used for tuning, reserve the
  most recent slice of data as a final, single-use test set. Compute the
  final reported performance on this slice exactly once.

### 4.2 Feature scaling (expanded)
- GBT: none needed — confirmed across XGBoost/LightGBM/CatBoost docs;
  monotonic transforms of a feature don't change the optimal split points.
- NN: standardize numeric features (subtract train-set mean, divide by
  train-set std) or min-max normalize to [0,1] / [-1,1]. For skewed
  distributions (e.g., counts, monetary values), consider `log1p` or Box-Cox
  before scaling.
- **Critical**: fit any scaler ONLY on the training fold/split; apply
  (transform, don't refit) to validation/test. Refitting on val/test is a
  (subtle but real) form of leakage.

### 4.3 Missing data (expanded)
- GBT: pass NaN directly (XGBoost, LightGBM both learn default split
  directions for missing values; CatBoost handles numeric NaN natively but
  may want an explicit category like `"missing"` for categorical NaNs).
  Avoid imputing unless you have domain reasons to believe missingness is
  pure noise.
- NN: impute (median for numeric is a robust default; mode or a dedicated
  "missing" category for categoricals feeding into embeddings) AND consider
  adding `is_missing` binary indicator columns so the network can learn from
  missingness patterns directly.
- In all cases: **investigate *why* values are missing** before choosing a
  strategy — missing-not-at-random patterns (e.g., a sensor that fails under
  certain conditions, or a stat that's only recorded for certain leagues/
  eras) can be *predictive* in their own right, and naive imputation can
  destroy or distort that signal.

### 4.4 Categorical encoding (expanded — leakage-safe target encoding recipe)
1. Split data into K folds (respecting temporal order if applicable —
   for temporal data, prefer **expanding-window** encoding: encode fold k
   using only data from folds < k, i.e., strictly past data).
2. For each fold k, compute the per-category target statistic (mean, or
   smoothed mean: `(category_sum + global_mean * smoothing_weight) /
   (category_count + smoothing_weight)`) using only data NOT in fold k (or,
   for temporal data, only data with earlier timestamps).
3. Encode fold k's categorical column using these out-of-fold statistics.
4. For the final model, recompute encodings using the *entire* training set
   (or all data with timestamp < deployment time) — this final encoding map
   is what gets applied to genuinely new/future data at inference time.
- **General reference**: practitioner write-ups on cross-fitted target
  encoding, e.g.
  https://www.geeksforgeeks.org/machine-learning/target-encoding-using-nested-cv-in-sklearn-pipeline/
  and https://brendanhasz.github.io/2019/03/04/target-encoding — the core
  principle (never let a row's own target influence its own encoded feature
  value) is what matters; implementation details vary.
- scikit-learn's `TargetEncoder` (≥1.3) implements K-fold cross-fitting
  automatically for non-temporal data — useful as a reference implementation
  but verify it matches your temporal-leakage requirements if your data is
  time-ordered.

### 4.5 General feature engineering best practices
- Prefer features computed from **only past/contemporaneous information**
  relative to the prediction point — audit every feature for "could this
  value only be known after the outcome we're predicting?"
- For GBT: feature interactions are learned automatically by trees (a
  sequence of splits on different features approximates an interaction) —
  manual interaction features are less critical than for linear models, but
  can still help if the interaction is important and the tree ensemble is
  small/shallow.
- For NN: manual interaction features (ratios, differences, products of
  related raw features) often help more than for GBT, since dense layers
  need to "discover" multiplicative interactions which are harder to learn
  than additive ones.
- Remove or down-weight near-duplicate / highly collinear features for NN
  (less critical for trees, which are relatively robust to collinearity,
  though it can dilute feature-importance signal across correlated
  features).
- Keep a strict feature provenance log (what each feature is, how/when it's
  computed, what data it depends on) — this is your primary defense against
  accidental leakage as feature sets grow.

---

## 5. HYPERPARAMETER TUNING (DETAIL)

### 5.1 Grid vs. random vs. Bayesian search
- **Grid search**: exhaustive but exponential in the number of
  hyperparameters; wastes compute exploring unimportant dimensions.
- **Random search**: Bergstra & Bengio (2012) showed random search finds
  models as good or better than grid search in a fraction of the time,
  because typically only a few hyperparameters matter for any given dataset,
  and random search allocates effective resolution to *all* dimensions
  rather than spreading a fixed grid thin. — Bergstra, J. & Bengio, Y.
  (2012), "Random Search for Hyper-Parameter Optimization", JMLR 13:281-305,
  https://jmlr.org/papers/v13/bergstra12a.html
- **Bayesian optimization** (Optuna, Hyperopt, scikit-optimize): builds a
  probabilistic surrogate model (often Tree-structured Parzen Estimator or
  Gaussian Process) of "hyperparameters → validation score" and uses it to
  propose promising configurations to try next. More sample-efficient than
  random search, especially valuable when each trial (a full GBT/NN train)
  is expensive. **Optuna** is a common, well-maintained choice with built-in
  pruning (early-stopping unpromising trials mid-training).
- **Practical recipe**: 
  - For GBT, 50–200 Optuna trials with pruning is usually sufficient to get
    near-optimal performance for a moderately-sized dataset.
  - For NN, hyperparameter search is more expensive per trial; consider a
    smaller search space (learning rate, weight decay, dropout, layer
    widths/depth, embedding dims) and fewer trials (20–50), possibly with
    a learning-rate range test as a cheap pre-step.

### 5.2 Nested cross-validation
- **Why**: if you select hyperparameters by maximizing performance on a
  validation set, and then *report* that same validation performance as your
  estimate of generalization, you get an optimistically biased estimate (the
  hyperparameters were chosen *because* they did well on that data).
- **Nested CV structure**:
  - Outer loop: splits data into outer-train / outer-test folds (for
    temporal data, outer folds = rolling-origin splits).
  - Inner loop: within each outer-train fold, further split into
    inner-train / inner-validation to select hyperparameters (via random/
    Bayesian search).
  - Refit the best inner-selected hyperparameters on the full outer-train
    fold, evaluate once on the outer-test fold.
  - Average outer-test performance across outer folds = unbiased estimate of
    "performance of this *modeling pipeline* (including its tuning
    procedure)" — not just "performance of one specific hyperparameter
    setting."
- **Cost**: nested CV multiplies compute by (outer folds × inner trials) —
  often impractical for NN; more feasible for fast GBT models. A pragmatic
  compromise: do a single round of tuning on early data, then validate the
  *fixed* final hyperparameters via rolling-origin on later data (i.e.,
  "tune once on the past, validate forward" — closer to real deployment and
  much cheaper than full nested CV).

### 5.3 Early stopping
- Reserve a validation set (chronologically *after* the training set, for
  temporal data) distinct from both the hyperparameter-tuning validation set
  and the final test set, if possible — or accept that the same validation
  set serves both early-stopping and light hyperparameter selection, as long
  as the final test set remains untouched.
- Monitor a chosen metric (log loss, RMSE, AUC, etc.) on this set after each
  boosting round / NN epoch; stop when it hasn't improved for `N` rounds
  (commonly 20–100 for GBT, depending on total planned rounds; for NN, often
  5–20 epochs of patience).
- After early stopping, either (a) use the model state at the best
  iteration (most common), or (b) for a final production model, retrain on
  train+validation combined for the number of iterations found optimal —
  but only do (b) if you're confident the validation set's distribution
  matches what additional training data would look like (risky for small
  validation sets).

---

## 6. EVALUATION & CALIBRATION

### 6.1 Proper scoring rules
- **Log loss (cross-entropy)**: `-mean(y*log(p) + (1-y)*log(1-p))` for binary;
  generalizes to multiclass. Heavily penalizes confident-wrong predictions
  (p near 0 or 1 for the wrong class) — a "proper scoring rule" (minimized in
  expectation by the true probabilities).
- **Brier score**: mean squared error between predicted probability and the
  0/1 outcome (binary) or one-hot outcome vector (multiclass):
  `mean(sum((p_i - o_i)^2))`. Bounded in [0, 2] for multiclass (or [0,1] for
  binary with the 1/2 convention dropped), also a proper scoring rule, more
  interpretable / less extreme-penalizing than log loss.
- **Ranked Probability Score (RPS)**: for **ordinal** outcomes (e.g.,
  categories with a natural order — loss < draw < win, or low < medium <
  high), RPS is "distance-sensitive": it penalizes a predicted distribution
  that's "close" to the true outcome (in ordinal terms) less than one that's
  "far" — e.g., predicting "win" when the outcome is "draw" is penalized less
  than predicting "win" when the outcome is "loss." Formula for r ordered
  categories: `RPS = (1/(r-1)) * sum_{i=1}^{r-1} (sum_{j=1}^{i} (p_j - a_j))^2`,
  where `p_j` are predicted cumulative probabilities and `a_j` are actual
  cumulative indicators (0 or 1). RPS ∈ [0, 1], lower is better.
  — General definition discussed in the context of the 2017 Soccer
  Prediction Challenge and elsewhere,
  https://arxiv.org/pdf/1908.08980 (Wheatcroft, "Evaluating probabilistic
  forecasts of football matches: the case against the ranked probability
  score" — note this paper *critiques* RPS, arguing it can reward forecasts
  that don't reflect genuine beliefs about the *ordering* if the categories
  aren't truly ordinal in the relevant sense; worth reading if your
  categories' "ordinality" is debatable, but RPS remains a standard,
  reasonable default for genuinely ordinal multi-class problems).
- **Use Brier/log-loss for nominal (unordered) multi-class**; use RPS (or a
  similar distance-sensitive score) when categories have genuine ordinal
  structure.
- **Always report multiple metrics** (e.g., log loss + Brier + RPS +
  accuracy) — a model can look better/worse depending on which proper
  scoring rule is emphasized, and reporting several gives a fuller picture.

### 6.2 Calibration — Niculescu-Mizil & Caruana (2005)
- **Citation**: Niculescu-Mizil, A. & Caruana, R. (2005), "Predicting Good
  Probabilities With Supervised Learning", ICML 2005.
  https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- **Findings**:
  - **Boosted trees and boosted stumps** (and max-margin methods generally)
    tend to push predicted probabilities *away from* 0 and 1 — i.e.,
    under-confident, with a characteristic **sigmoid-shaped distortion**
    (predictions compressed toward the middle of [0,1]).
  - **Naive Bayes** pushes probabilities *toward* 0/1 (over-confident).
  - **Neural nets and bagged trees** tend to be reasonably well-calibrated
    out of the box (no strong systematic bias), though not perfectly.
  - **After calibration**, boosted trees, random forests, and SVMs were
    found to produce among the *best* probability estimates — i.e.,
    calibration largely fixes GBT's main probabilistic weakness, and
    calibrated GBT can outperform "naturally calibrated" models in absolute
    terms.
- **Calibration methods**:
  - **Platt scaling**: fit a logistic regression (1-2 parameters: `a`, `b`
    in `sigmoid(a*raw_score + b)`) mapping raw model outputs to calibrated
    probabilities, using a held-out calibration set. Simple, low-variance,
    works well when the miscalibration has the sigmoid shape typical of
    boosted trees.
  - **Isotonic regression**: fits a non-parametric, monotonically increasing
    step function mapping raw scores to calibrated probabilities. More
    flexible (can correct non-sigmoid distortions) but needs more data to
    avoid overfitting the calibration map itself; with small calibration
    sets, Platt scaling is often preferred.
  - For multi-class/ordinal problems, calibration is more involved (e.g.,
    per-class one-vs-rest Platt/isotonic followed by renormalization, or
    Dirichlet calibration / temperature scaling for NN). Always validate the
    calibrated probabilities still sum to 1 and improve the chosen proper
    scoring rule on a held-out set.
- **Reliability diagrams**: bin predictions by predicted probability (e.g.,
  deciles), plot mean predicted probability vs. observed frequency in each
  bin. A well-calibrated model lies on the y=x diagonal. Always plot this
  before AND after calibration on a held-out set — calibration fit on one
  set must be *validated* on a different set to confirm it generalizes.
- **Crucial**: fit the calibration map on a set DISTINCT from both the
  training set (used to fit the base model) and the final test set (used to
  report final numbers) — typically a dedicated "calibration" split, or via
  cross-fitting (train base model on K-1 folds, calibrate + evaluate on the
  held-out fold, repeat).

---

## 7. INTERPRETABILITY — SHAP

- **Citation**: Lundberg, S.M. & Lee, S.-I. (2017), "A Unified Approach to
  Interpreting Model Predictions", NeurIPS 2017. https://arxiv.org/abs/1705.07874
- **Core idea**: SHAP (SHapley Additive exPlanations) assigns each feature an
  "importance" value for a *specific prediction*, based on Shapley values
  from cooperative game theory — i.e., each feature's contribution is its
  average marginal contribution to the prediction, averaged over all
  possible "coalitions" (subsets) of other features. SHAP unifies several
  prior feature-attribution methods (LIME, DeepLIFT, etc.) as special cases
  of a single class of "additive feature attribution methods" with provably
  unique, theoretically-grounded properties (local accuracy, missingness,
  consistency).
- **TreeSHAP**: an efficient, exact algorithm for computing SHAP values for
  tree ensembles (XGBoost, LightGBM, CatBoost, Random Forest) — polynomial
  time instead of the exponential brute-force Shapley computation. This
  makes SHAP the de facto standard for explaining GBT models.
- **KernelSHAP**: a model-agnostic approximation usable for NNs or any
  black-box model, but slower (sampling-based).
- **Practical uses**:
  - **Global feature importance**: average |SHAP value| per feature across
    the dataset — generally more reliable than GBT's built-in "gain" or
    "split count" importances, which can be biased toward
    high-cardinality/continuous features.
  - **Local explanations**: for an individual prediction, SHAP shows exactly
    how much each feature pushed the prediction up/down from the baseline
    (expected value) — useful for debugging individual predictions and for
    stakeholder communication.
  - **Dependence plots**: SHAP value vs. feature value, optionally colored by
    a second feature — reveals non-linearities and interactions captured by
    the model.
  - **Sanity-checking**: if SHAP attributes large importance to a feature
    that "shouldn't" matter (e.g., a row-index-like ID, or a feature that
    couldn't have been known at prediction time), that's a strong signal of
    a leakage bug — SHAP is a useful *leakage detector*, not just an
    explainer.

---

## 8. COMMON PITFALLS

### 8.1 Target leakage & train/test contamination
- **Definition**: any situation where information that would not be
  available at prediction time (in deployment) leaks into the training
  features or the train/val/test split process.
- **Common sources**:
  - Features computed using the *full* dataset's statistics (e.g.,
    normalizing using global mean/std computed across train+test).
  - Target encoding without out-of-fold computation (Section 4.4).
  - Temporal leakage from random splits on time-ordered data (Section 1.2 /
    4.1).
  - Features that are functions of the outcome itself, or of post-outcome
    events (e.g., "final score margin" as a feature when predicting the
    winner — even if technically computed "after" the prediction point in
    the raw data pipeline).
  - GBT's prediction-shift / target-leakage in naive boosting + naive target
    statistics — addressed by CatBoost's ordered boosting (Section 2.4), but
    relevant conceptually for any pipeline using target statistics.
- **Detection**: suspiciously high validation performance compared to
  domain expectations; SHAP showing a feature with implausibly large
  importance (Section 7); performance that collapses when moving from
  validation to a genuinely fresh, later-in-time test set.

### 8.2 Overfitting via excessive tuning on the test set
- Every time you look at test-set performance and then make a decision
  (change a feature, hyperparameter, or model) based on it, you "use up"
  some of that test set's validity. Repeated iterations against the same
  test set will eventually produce a model that's overfit to that *specific*
  test set, even if it never directly trained on it.
- **Mitigations**: maintain a strict train/val/test separation where val is
  used for all iteration and test is touched rarely (ideally once, at the
  very end); if many iterations are needed, consider periodically refreshing
  the test set (e.g., as new time periods of data become available) or use
  nested CV (Section 5.2) to get an estimate of the *tuning procedure's*
  generalization, not just one model's.

### 8.3 Class imbalance
- **Relevant when** the outcome of interest is rare (e.g., upsets, rare
  events, fraud, disease).
- **Class weighting**: most GBT/NN libraries support a `class_weight` /
  `scale_pos_weight` parameter that up-weights the minority class in the loss
  function — simple, no data duplication, usually the first thing to try.
  For binary XGBoost, a common heuristic is `scale_pos_weight =
  count(negative) / count(positive)`.
- **Resampling (oversampling/undersampling/SMOTE)**: SMOTE generates
  synthetic minority-class examples by interpolating between existing
  minority examples and their nearest neighbors. Can help on moderately
  imbalanced data, but: (a) excessive oversampling risks overfitting to
  synthetic patterns that don't generalize, (b) SMOTE is sensitive to
  outliers and local sparsity, (c) its effect on *calibration* is often
  unpredictable — recalibrate (Section 6.2) after any resampling.
  General review: https://www.ml4devs.com/what-is/imbalanced-data-model-training/
- **Recurring best-practice combination** (per recent benchmarking work on
  rare-event classification): gradient boosting + (optional, modest)
  resampling + **explicit threshold/probability calibration** +
  hyperparameter tuning that accounts for the imbalance (e.g., tuning on a
  metric like PR-AUC, log loss, or Brier rather than accuracy, which is
  meaningless under heavy imbalance).
- **For probabilistic forecasting tasks** (where you care about the actual
  probability of a rare event, not just classification): be especially
  careful with resampling — it changes the *base rate* the model learns,
  which then must be corrected for (e.g., via a known formula relating
  resampled-data probabilities back to true base rates, or by recalibrating
  on a held-out set with the *true*, unresampled class distribution).
  Often, for probability-focused tasks, **class weighting + calibration** is
  safer than resampling because it doesn't distort the base rate the model
  implicitly learns.
- **Don't use accuracy as the primary metric under imbalance** — a model
  that always predicts the majority class can have high accuracy but zero
  value. Use log loss, Brier score, PR-AUC, or domain-specific proper scoring
  rules (Section 6.1) instead.

### 8.4 Ensembling & stacking basics
- **When to ensemble GBT + NN (+ other models)**:
  - When the models have **different error structures** — e.g., GBT
    captures sharp/irregular interactions while an NN (with entity
    embeddings) captures smooth global patterns and high-cardinality
    categorical structure differently. Diverse errors → ensembling helps
    more.
  - When you have enough held-out data to fit ensemble weights (or a
    meta-model) without overfitting the combination itself.
- **Simple ensembling approaches**:
  - **Simple/weighted average of predicted probabilities** across models —
    robust, low-risk, easy to calibrate afterward as a single combined
    score.
  - **Stacking**: train a (typically simple, e.g., logistic regression)
    meta-model on the out-of-fold predictions of the base models — captures
    cases where one base model is more reliable in certain regions of
    feature space. Must use out-of-fold base-model predictions to fit the
    meta-model (same leakage logic as target encoding, Section 4.4) —
    otherwise the meta-model overfits to base models' in-sample
    overconfidence.
  - **Multi-seed NN ensembling**: average predictions across several NN
    training runs with different random seeds — cheap variance reduction
    (Section 3.4).
- **Caution**: ensembling adds complexity and can obscure calibration —
  always recalibrate (Section 6.2) the *ensemble's* output, not just each
  base model's output individually, since averaging miscalibrated
  probabilities doesn't necessarily produce a calibrated result.
- **Cost-benefit**: ensembling typically gives modest (a few %) improvements
  in proper scoring rules at the cost of substantially more
  complexity/maintenance — worth it for a final/production model, often not
  worth it during exploratory research where interpretability and iteration
  speed matter more.

---

## 9. QUICK-REFERENCE: LIBRARY DEFAULTS & GOTCHAS

- **XGBoost**: default `tree_method` matters — use `'hist'` for speed on
  larger data. For categorical support, set dtype to `category` and
  `enable_categorical=True` (relatively recent feature; verify version).
  Default objective for binary classification is `binary:logistic` (gives
  probabilities directly).
- **LightGBM**: `categorical_feature` parameter for native categorical
  handling; watch `num_leaves` vs `max_depth` interaction (leaf-wise growth
  can blow past intended depth-based complexity if `num_leaves` is set too
  high relative to `max_depth`). `boosting_type='gbdt'` is standard;
  `'dart'` (dropout in trees) and `'goss'` are alternatives worth
  experimenting with for regularization.
- **CatBoost**: pass `cat_features` as a list of column indices/names of raw
  (unencoded) categorical columns. `loss_function` and `eval_metric` can
  differ (e.g., optimize log loss but monitor a custom metric). Symmetric
  trees by default (`grow_policy='SymmetricTree'`); `'Lossguide'` mimics
  LightGBM's leaf-wise growth if desired.
- **All three**: always pass an explicit validation set + `early_stopping_rounds`
  (or library-equivalent) — relying on a fixed `n_estimators` without early
  stopping is one of the most common avoidable mistakes.
- **Random seeds**: set seeds for reproducibility, but also **run with
  multiple seeds** and report variance — single-seed results, especially for
  NN and for GBT with high `subsample`/`colsample` stochasticity, can be
  noisy enough to overstate small differences between configurations.

---

---

## Football-specific: Model vs. Market/Crowd Edge

**Purpose of this section.** Notes specific to the question: can a calibrated
statistical model (Elo + ordered logit, Poisson/Dixon-Coles, pi-ratings,
Bayesian networks, etc.) systematically beat bookmaker odds / wisdom-of-crowds
consensus on football match outcomes — and if so, where, how big, and how to
strengthen it. Written after one match where the researcher's Elo+ordered-logit
model beat "the crowd" on the match-winner question in a forecasting
tournament.

### A. Does an edge exist? Headline answer: weak/no edge in big efficient
markets, but real, modest, *documented* edges exist in specific
sub-markets/conditions — and the bar to clear is "beat a ~5-8% bookmaker
margin," which is much higher than "beat a margin-free crowd average."

- **Dixon & Coles (1997)**, "Modelling Association Football Scores and
  Inefficiencies in the Football Betting Market", *J. Royal Statistical
  Society Series C* 46(2):265-280,
  https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/1467-9876.00065 — the
  foundational paper. Bivariate Poisson model with time-decay weighting fitted
  to English league/cup data 1992-1995, tested against bookmaker odds from
  1995-96. Found a **positive return when used as the basis of a betting
  strategy** — i.e., found *some* exploitable inefficiency at the time. This
  is the canonical "yes, models can find edges" result, but it's now ~30 years
  old and markets have become far more competitive/efficient since
  (online odds shopping, algorithmic bookmaking, syndicate money).

- **Forrest, Goddard & Simmons (2005)**, "Odds-setters as forecasters: The
  case of English football", *International Journal of Forecasting*
  21(3):551-564, https://ideas.repec.org/a/eee/intfor/v21y2005i3p551-564.html
  (Lancaster repo: https://eprints.lancs.ac.uk/id/eprint/44019/) — **the
  classic "markets win" result**. ~10,000 English league games. Compared
  bookmaker odds-implied forecasts against an "expert"-style statistical model
  using a large set of quantifiable variables (form, league position, etc.).
  **Bookmakers' forecasts beat the statistical model overall**, AND — notably
  — **bookmaker forecasting accuracy *improved over the 5-year sample period*
  (1990s)**, attributed to intensifying competition between bookmakers
  increasing the cost of mispriced odds. Implication: market efficiency is not
  static — it has been trending *up* over decades as betting markets
  professionalize, which should make a present-day researcher more skeptical
  of finding edges in major leagues than a 1997-era researcher would have
  been.

- **Constantinou & Fenton (2012)**, "Determining the level of ability of
  football teams by dynamic ratings based on the relative discrepancies in
  scores between adversaries" (the **pi-ratings** paper), *Journal of
  Quantitative Analysis in Sports* 8(1), DOI 10.1515/jqas-2012-0036, PDF:
  http://www.constantinou.info/downloads/papers/pi-ratings.pdf — **THE key
  "yes, an edge is possible" result for a relatively simple rating-based
  model**. Pi-ratings (a dynamic Bradley-Terry-style rating using the
  *magnitude* of score discrepancies, with separate home/away ratings) were
  shown to **outperform standard Elo ratings** AND, critically, were
  **profitable against market odds over 5 EPL seasons (2007/08-2011/12), even
  after the bookmaker's built-in margin** — described in the paper as the
  *first* academic demonstration of profitability against market odds using
  such a simple technique. **Direct relevance**: the researcher's model is
  Elo + ordered logit — pi-ratings essentially show that a "smarter Elo"
  (incorporating goal-margin information, which Elo discards) can beat plain
  Elo *and* the market. A natural strengthening direction: add a
  goal-margin-aware adjustment (pi-rating-style "error function" on score
  discrepancy) on top of / alongside the Elo input feature.

- **Constantinou & Fenton, "pi-football: A Bayesian network model for
  forecasting Association Football match outcomes"**, *Knowledge-Based
  Systems* 36:322-339 (2012), https://dl.acm.org/doi/10.1016/j.knosys.2012.07.008
  — extends pi-ratings into a 4-factor Bayesian network (strength, **form**,
  **psychology**, **fatigue**) and again benchmarks against bookmakers.
  Relevant for feature ideas beyond pure rating differentials: explicit "form"
  (recent-result momentum separate from the rating itself), "psychology"
  (e.g., effects of recent away-from-home runs, derby/rivalry context), and
  "fatigue" (fixture congestion / travel) as features that a market may
  under-price relative to a model that tracks them explicitly.

- **Constantinou (2019)**, "Dolores: a model that predicts football match
  outcomes from all over the world", *Machine Learning* (Springer), DOI
  10.1007/s10994-018-5703-7,
  https://link.springer.com/article/10.1007/s10994-018-5703-7 — built for the
  **"Machine Learning for Soccer" competition** (Soccer Prediction Challenge,
  similar tournament structure to the researcher's current situation: scored
  on RPS across many matches, 52 leagues worldwide, transfer-learning across
  leagues with missing data). Ranked **2nd of all entrants**, ~0.94% worse RPS
  than the winner. Headline conclusion: **"although hard to predict, in some
  scenarios it is possible to outperform bookmakers, which are robust
  baselines per se."** I.e., the literature's settled view by ~2019 is that
  bookmakers are a *strong baseline that is occasionally, narrowly beatable*
  — not an unbeatable wall, but also not something you should expect to beat
  by a wide or consistent margin. Cross-league transfer-learning (training on
  many leagues/federations to estimate a global model, then specializing) is
  itself a technique worth considering if the international-match dataset
  spans many confederations with uneven match counts.

- **Štrumbelj (2014)**, "On determining probability forecasts from betting
  odds", *International Journal of Forecasting* 30:934-943,
  https://www.sciencedirect.com/science/article/abs/pii/S0169207014000533
  (Semantic Scholar: https://www.semanticscholar.org/paper/On-determining-probability-forecasts-from-betting-%C5%A0trumbelj/8074edd44af6a4a64ab1fffee2642893d693720a)
  — **methodological paper on how to correctly turn odds into "the market's
  probability"**, which matters a lot if "the crowd" in the tournament is
  itself derived from odds-like aggregation. Compares (1) naive normalization
  (divide each implied prob by the sum of implied probs across outcomes —
  removes the overround but assumes the margin is spread proportionally) vs.
  (2) **Shin's model** (Shin 1992/1993), which models the margin as arising
  from a proportion of "insider" money and **endogenously corrects for
  favorite-longshot bias** when extracting probabilities. Finding: **Shin's
  model produces better-calibrated implied probabilities than naive
  normalization** — i.e., naively de-vigged odds *still* contain
  favorite-longshot bias. **Practical implication**: if the researcher ever
  wants to compute "what does the market really believe" (e.g., as a
  benchmark or as a blending input — Section C below), use Shin's
  de-vigging method, not simple proportional normalization, especially for
  matches with extreme favorites/underdogs.

- **Boshnakov, Kharrat & McHale (2017)**, "A bivariate Weibull count model for
  forecasting association football scores", *International Journal of
  Forecasting* 33(2):458-466,
  https://www.sciencedirect.com/science/article/abs/pii/S0169207017300018 —
  generalizes Dixon-Coles (Weibull inter-arrival times for goals + copula for
  home/away dependence, vs. Dixon-Coles' bivariate Poisson + ad-hoc
  low-score correlation correction). Out-of-sample: better calibration
  (calibration curves) than simpler Poisson-based alternatives, and **a
  Kelly-criterion betting strategy on both the 1X2 market and the
  over/under-2.5-goals market produced positive returns**. Reinforces that
  *richer goal-process models* (capturing the correlation/dependence
  structure between home and away goals, not just independent Poisson rates)
  can find edges that simpler models miss — a possible future extension if
  the researcher ever moves from outcome-only (W/D/L) modeling to full
  score-distribution modeling.

- **Egidi, Pauli & Torelli (2018)**, "Combining historical data and
  bookmakers' odds in modelling football scores", arXiv:1802.08848,
  https://arxiv.org/pdf/1802.08848 — **directly relevant to the
  "blend model + market" question (Section C)**. Hierarchical Bayesian Poisson
  model where each team's scoring-rate parameters are a **convex combination
  of (a) parameters estimated from historical match data and (b) information
  implied by bookmakers' odds**. Result: incorporating the bookmaker-odds
  information as a *prior/shrinkage target* brought the historical-data-only
  model's posterior forecasts up to **on par with bookmakers**, and the
  combined model **generated profit** under max/mean/common bookmaker odds in
  back-testing. This is essentially a Bayesian implementation of "blend your
  model's prior with the market" — see Section C for how to adapt this to an
  ordered-logit setting.

### B. Favorite-longshot bias — specifics and where the edge concentrates

- **Core empirical regularity**: across essentially all fixed-odds sports
  betting markets (horse racing originally, but robustly replicated in
  football), **bookmaker-implied probabilities for heavy favorites are biased
  *low* relative to true win probability (favorites are "underpriced"/good
  value), while implied probabilities for big underdogs are biased *high*
  relative to true probability (underdogs are "overpriced"/bad value)**. In
  expected-value terms: betting favorites carries only a small expected loss
  (roughly -1% to -2%, close to the bare margin), while betting big longshots
  carries a much larger expected loss (often beyond -10% to -15%). General
  reviews: https://www.boydsbets.com/favorite-longshot-bias/ ,
  https://thewagertheorem.com/favorite-longshot-bias-betting/ , and for the
  academic treatment of *why* (insider-trading / Shin-type models vs.
  bettor risk-preference / prospect-theory explanations), see "The
  Favourite-Longshot Bias, Bookmaker Margins and Insider Trading in a Variety
  of Betting Markets",
  https://www.academia.edu/16834446/The_Favourite_Longshot_Bias_Bookmaker_Margins_and_Insider_Trading_in_a_Variety_of_Betting_Markets
  and "The Favorite-Longshot Bias: An Overview of the Main Explanations",
  https://www.researchgate.net/publication/228884358_The_Favorite-Longshot_Bias_An_Overview_of_the_Main_Explanations
  — common explanations: (1) **insider information** — informed bettors
  disproportionately bet on value they've identified, which (per Shin's
  model) the bookmaker defends against by shading prices toward favorites;
  (2) **bettor risk preferences** — recreational bettors are
  risk-seeking/skewness-loving and overpay for the small chance of a big
  payout on a longshot (lottery-ticket effect); (3) bookmakers price to
  *liquidity* — sharp/professional money concentrates on favorites (where
  edges are small but volume is high), so bookmakers keep favorite margins
  thin to retain that volume, while loading the margin onto longshots where
  recreational bettors are price-insensitive.
- **Direct implication for outcome modeling (W/D/L)**: a *correctly
  calibrated* model's structural edge, if it exists at all, should
  concentrate in **(a) matches with extreme favorites** (model probability
  for the favorite > market-implied probability — i.e., bet/score the
  favorite more aggressively than the market suggests) and **(b) matches with
  extreme underdogs/draws** (model probability for the longshot/draw <
  market-implied probability). For a 3-outcome (W/D/L) market specifically,
  the **draw** often behaves like a "longshot" outcome in lopsided matchups
  (a big-favorite-vs-big-underdog game) — the literature on football
  favorite-longshot bias (e.g., the Forrest/Goddard/Simmons- and
  Cain/Law/Peel-style literature on the "draw" as a systematically mispriced
  outcome) generally finds bookmakers can **overprice the draw probability
  relative to true probability** in heavily lopsided matches, though this is
  less robustly documented for football specifically than the classic
  favorite/longshot result for win/loss outcomes — treat as a hypothesis to
  test empirically on your own RPS-by-bucket breakdown rather than an
  established fact.
- **Practical test for the researcher's own data**: bucket matches by
  market-implied favorite probability (e.g., deciles from ~33% to ~95%+), and
  compute the model-vs-market Brier/RPS difference *within each bucket*. If
  the favorite-longshot bias is present and the model is well-calibrated
  (doesn't itself have the bias), the model should show its **largest edge in
  the most lopsided buckets** (favorite implied prob > ~70-75%, or draw
  implied prob in lopsided games) and little-to-no edge in close-to-even
  matchups (~33-45% favorite probability) — those are already close to
  "fair" and heavily traded.

### C. Where market efficiency is weaker — situational edges

- **Angelini & De Angelis (2019)**, "Efficiency of online football betting
  markets", *International Journal of Forecasting* 35(2):712-721,
  https://www.sciencedirect.com/science/article/abs/pii/S0169207018301134
  (REPEC: https://ideas.repec.org/a/eee/intfor/v35y2019i2p712-721.html) —
  large sample, top-tier divisions of **11 European leagues**, multiple
  bookmakers, Mincer-Zarnowitz-style efficiency regression testing whether
  average market prices deviate from "true" probabilities, with explicit
  attention to favorite-longshot bias. Result: **mixed/heterogeneous —
  using best-available odds across bookmakers, 8 of 11 league markets were
  efficient, but 3 showed inefficiencies implying profit opportunities**.
  Takeaway: even among Europe's most-watched top-flight leagues, efficiency
  is *not* uniform — some leagues/markets remain exploitable even today, and
  this was using *best* (most competitive) odds, meaning the gap is likely
  larger using a single, less-sharp bookmaker's line, and likely larger still
  for **non-top-tier divisions and lower-profile competitions** that weren't
  even in this sample (the international-match dataset the researcher is
  using likely includes many such lower-visibility fixtures — friendlies,
  qualifiers for smaller confederations, etc.).
- **General liquidity/attention argument** (practitioner consensus, no single
  canonical academic citation but widely discussed, e.g.
  https://www.soccertipsters.com/blog-detail/425/betting-market-inefficiency-why-lower-leagues-offer-hidden-value.html
  and https://topbookmakerfootball.com/articles/lower-league-football-betting-finding-value-in-minor-divisions/):
  **major leagues (EPL, top 5 European leagues, World Cup) are priced by
  large amounts of professional/syndicate money and adjusted in near
  real-time** — these markets are closest to the efficient-market-hypothesis
  ideal. **Lower-tier leagues, smaller national-team federations, and
  international friendlies/qualifiers attract far less professional
  attention and liquidity**, so (a) odds may be set more mechanically (e.g.,
  largely from a base model with less manual adjustment for late-breaking
  team news) and (b) **odds update more slowly to reflect recent
  team-strength changes** (squad changes, managerial changes, recent run of
  form) — exactly the kind of information an Elo-based model, which updates
  every match, captures essentially "for free" and continuously, while a
  bookmaker may be slower to re-price a national team that has had a sudden
  change in form (new manager, key player returning from injury/suspension,
  etc.) for a relatively low-profile fixture. **This is plausibly the single
  most defensible "structural edge" hypothesis for the researcher's specific
  dataset** (international matches spanning many confederations of widely
  varying profile/liquidity) — an edge concentrated in **lower-profile
  fixtures (friendlies, lower-confederation qualifiers, neutral-venue
  tournaments) where Elo's continuous updating outpaces market re-pricing**,
  rather than in marquee fixtures (World Cup knockout games, major continental
  finals) where the market is closest to fully efficient and matches the
  Forrest/Goddard/Simmons (2005) finding of strong/improving bookmaker
  accuracy in high-profile English football.
- **Neutral-venue matches**: no strong dedicated academic literature was found
  specifically on neutral-venue mispricing, but it follows mechanically from
  the home-advantage literature: if a bookmaker's base model applies a
  "default" home-advantage adjustment that isn't properly zeroed out (or is
  miscalibrated) for a *designated* neutral venue (e.g., a World Cup match
  played in a third country, or a "home" qualifier moved to a neutral site for
  political/logistical reasons), there's a plausible mechanical mispricing
  that an Elo model — which can explicitly encode "no home advantage applied
  this match" — would not share. Worth checking empirically: does the
  researcher's model's edge over the market concentrate in matches flagged as
  neutral-venue?

### D. Wisdom of crowds — when does the "crowd" framing help vs. hurt

- **Surowiecki's four conditions for crowd wisdom** (https://en.wikipedia.org/wiki/The_Wisdom_of_Crowds):
  **diversity** of opinion (each person has some private information, even if
  it's just an eccentric interpretation of public facts), **independence**
  (opinions not determined by the opinions of others around them),
  **decentralization** (people can specialize/draw on local knowledge), and
  **aggregation** (a mechanism exists to turn individual judgments into a
  collective decision). When all four hold, aggregation can outperform even
  the best individual.
- **Where these break down for sports-betting/forecasting "crowds"**: (1)
  **Independence breaks down** when participants can see the current odds/
  consensus before forecasting (anchoring) — "early price movements create an
  anchor that everyone else just follows, and nobody wants to be the
  contrarian betting against the number on the screen"
  (https://www.cloudbet.com/en/blog/sports/how-the-wisdom-of-the-crowd-relates-to-betting/).
  If the tournament's "crowd" forecast is published/visible *before*
  participants submit (or is itself derived from a market that participants
  can see), independence is compromised and the crowd is closer to "everyone
  echoing the market" than "many independent estimates." (2) **Diversity
  breaks down** if most participants are using similar public data sources
  (e.g., everyone scrapes the same Elo ratings site, or everyone anchors to
  the same bookmaker's line) — homogeneous inputs produce a less-wise
  aggregate, closer to a single noisy estimate than a true wisdom-of-crowds
  average. (3) **Decentralization** is generally fine for football forecasting
  (different forecasters do have access to different niche information — e.g.,
  squad news for specific federations).
- **When an individual forecaster *should* deviate from the crowd**: per the
  above, deviation adds value when (a) you have **information or a model
  capturing something the crowd's *information set* doesn't yet reflect**
  (e.g., very recent form changes for lower-profile teams that the market is
  slow to re-price — Section C), or (b) you can **identify and correct a
  *systematic, structural bias* in the crowd's aggregation mechanism** (e.g.,
  favorite-longshot bias — Section B) that persists *because* it's baked into
  how the crowd/market is constructed (e.g., bookmaker margin-allocation
  policy), not because of a temporary informational gap. Deviation
  *subtracts* value when it's just noise, idiosyncratic model error, or
  reflects information the crowd already has but you're weighting
  differently for no good reason.
- **"Wisdom of the crowds forecasting the 2018 FIFA Men's World Cup"**,
  Inácio, Izbicki, Lopes, Salasar, Poloniato & Diniz, arXiv:2008.13005,
  https://arxiv.org/pdf/2008.13005 — ran an online contest where many
  participants submitted match-outcome probability forecasts, scored via
  proper scoring rules; compared various crowd-aggregation methods (simple
  average, trimmed means, etc.) against individual forecasters and
  statistical models. **Finding: crowd-aggregation methods were a
  "competitive forecasting strategy"** — i.e., comparable to good individual
  models on average, **but not unbeatable by every individual** — some
  individual statistical models/forecasters beat the crowd aggregate in this
  contest, consistent with the "narrow, occasional edge possible" theme from
  Constantinou's Dolores result (Section A). Also relevant: "Goal-line
  oracles: Exploring accuracy of wisdom of the crowd for football
  predictions", https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11785260/ (PMC,
  recent) — another empirical look at crowd accuracy specifically for
  football, worth a closer read if time permits, as it's more recent than
  most of the betting-market literature above.
- **Practical reading for the tournament context**: one win against the crowd
  on one match is **essentially zero evidence** of a real edge (see Section
  E for why). But the *type* of match matters for how much weight to put even
  qualitatively on that single result — a win on a **lopsided favorite/
  underdog match** or a **lower-profile fixture** is more consistent with the
  documented mechanisms above (favorite-longshot bias correction, faster
  Elo re-pricing) than a win on a near-50/50 marquee match, which is more
  likely to just be noise.

### E. Testing whether an edge is real vs. luck — methodology for small samples

- **The core problem**: Brier score / RPS differences between two forecasters
  (model vs. crowd) on a *single match*, or even a handful of matches, have
  enormous sampling variance relative to the typical *size* of any real edge
  (literature above suggests edges, where they exist, are on the order of a
  few percent improvement in proper-scoring-rule terms, or a few percentage
  points of ROI). Beating the crowd on 1 match out of 1 carries essentially no
  statistical information.
- **Diebold-Mariano (DM) test** — the standard tool for "is forecaster A
  significantly better than forecaster B, given a sequence of paired
  forecasts and outcomes":
  - Reference: overview at https://www.emergentmind.com/topics/diebold-mariano-test
    and R implementation `forecast::dm.test`,
    https://pkg.robjhyndman.com/forecast/reference/dm.test.html (also
    documented at https://search.r-project.org/CRAN/refmans/forecast/html/dm.test.html
    and https://real-statistics.com/time-series-analysis/forecasting-accuracy/diebold-mariano-test/).
  - **Mechanics**: for each match *i*, compute the per-match loss differential
    `d_i = L(model_i) - L(crowd_i)`, where `L` is your proper scoring rule
    (Brier or RPS) applied to that forecaster's probability vector for match
    *i*. Test whether `mean(d_i)` is significantly different from 0 (negative
    = model better, on average, in expectation under the null of equal
    accuracy). DM does **not** require normally-distributed loss differentials
    and works with Brier-score-type losses — it's directly applicable here.
  - **Small-sample correction**: use the **Harvey-Leybourne-Newbold (HLN)**
    modification, which uses a t-distribution with `n-1` degrees of freedom
    instead of the standard normal — recommended whenever the sample is
    small (the literature flags below ~20 observations as needing this, but
    given football's high outcome variance, you'll want it for anything under
    a few hundred matches too as a matter of course).
    https://www.emergentmind.com/topics/diebold-mariano-test
  - **Autocorrelation in the loss differential**: if forecasts are made
    sequentially with overlapping information (e.g., both forecasters update
    based on recent matches involving the same teams), `d_i` may be
    autocorrelated — DM's variance estimator should use a Newey-West/HAC-type
    long-run variance with an appropriate truncation lag (a common rule of
    thumb for the lag is `h = floor(n^(1/3)) + 1` for h-step-ahead forecasts,
    though for football match-by-match forecasts with no explicit forecast
    horizon beyond 1, `h=1` and minimal/no HAC correction is often
    appropriate — check whether your `d_i` series shows significant
    autocorrelation before adding lags).
- **Simpler complementary tests**:
  - **Sign test / binomial test**: for each match, just record whether
    `d_i < 0` (model beat crowd) or `> 0` (crowd beat model), discard ties,
    and test the proportion of model-wins against 0.5 using a binomial test.
    Less powerful than DM (throws away magnitude information) but
    distribution-free and easy to communicate ("model beat the crowd on X of
    Y matches where they disagreed, p = ...").
  - **Paired t-test / Wilcoxon signed-rank test** on `d_i`: a paired t-test on
    the loss differentials is a parametric alternative to DM (DM is
    essentially a paired t-test with a more careful variance estimator for
    time-series/autocorrelated data); Wilcoxon signed-rank is the
    non-parametric analog if `d_i` is heavily skewed (likely, since Brier/RPS
    losses are bounded and outcome-dependent).
  - **Bootstrap confidence intervals on mean(d_i)**: resample matches (or
    blocks of matches, if autocorrelated) with replacement, recompute
    `mean(d_i)` each time, and form a percentile CI — robust to
    non-normality and easy to extend to RPS.
- **Practical sample-size guidance**: given that documented edges in the
  literature (where they exist at all) tend to be *small* relative to
  match-to-match outcome variance (a single match's Brier/RPS score is
  dominated by the 0/1 outcome noise, not by small differences in predicted
  probabilities), expect to need **at least several hundred matches**, and
  preferably 1,000+, with reasonably consistent match "type" (e.g., similar
  mix of favorite/underdog/draw situations across the sample), before a DM
  test has reasonable power to distinguish a real few-percent edge from noise.
  With ~49,400 historical matches already used for *model validation*, the
  researcher has ample data to (a) establish the model is *well-calibrated*
  in-sample/out-of-sample (already done via Brier/RPS), and separately (b) —
  if historical bookmaker odds or a crowd-proxy can be obtained for a
  meaningful subset of those matches — run a **proper DM test of model vs.
  market across that historical subset**, stratified by the Section B/C
  buckets (favorite-longshot extremity, league profile, neutral venue), which
  would give a far more credible answer than any small number of
  live-tournament matches can.

### F. Concrete suggestions for blending model + market to strengthen an edge

1. **De-vig the market/crowd probability correctly before using it**: if
   "the crowd" forecast is itself odds-derived, apply **Shin's method**
   (Štrumbelj 2014, above) rather than simple proportional normalization to
   recover the crowd's true believed probabilities, especially for lopsided
   matches — proportional normalization leaves favorite-longshot bias *in*
   the "true" probability estimate, which would bias any blend.
2. **Use the market/crowd probability as a Bayesian prior / shrinkage target,
   and your model as the "data" that updates it** — directly analogous to
   Egidi, Pauli & Torelli (2018, arXiv:1802.08848): convex-combine your
   model's predicted probability vector `p_model` with the (de-vigged)
   market probability vector `p_market`:
   `p_blend = w * p_model + (1-w) * p_market`, with `w` chosen by
   cross-validation (or estimated via a simple logistic/Dirichlet regression
   of outcomes on both probability vectors — i.e., a 2-input "stacking"
   meta-model, same idea as Section 8.4 of the GBT/NN notes above but with
   only two, highly informative base "models"). Because both `p_model` and
   `p_market` are themselves close to the truth, even a small `w` (e.g.,
   0.2-0.4) can shift the blend in the direction of your model's genuine
   informational edge while retaining most of the market's accuracy as a
   "floor."
3. **Make `w` (the model's weight) *match-dependent*, using the Section B/C
   heuristics as features**: rather than a single global blending weight,
   let `w` increase for matches where the literature says model edges are
   most plausible — e.g., `w = w_0 + w_1 * |market_favorite_prob - 0.5| +
   w_2 * I(low-profile fixture) + w_3 * I(neutral venue) + w_4 *
   |elo_implied_prob - market_prob|` (the last term: when your model and the
   market *disagree most*, that's exactly when blending matters most — if
   they agree, blending is moot). This can be fit as a simple logistic
   regression where the *target* is the match outcome and the *features* are
   `p_model`, `p_market`, and their interactions with the situational
   indicators above — the fitted coefficients tell you empirically where your
   model adds value, which is itself a useful diagnostic independent of the
   final blended forecast's performance.
4. **Always evaluate the blend (and its weight-selection procedure) via
   walk-forward / rolling-origin validation** (Section 1.2/4.1 of the
   general ML notes above) — fitting `w` (or the logistic blending model) on
   the same data used to evaluate it will give an optimistically biased edge
   estimate, exactly the same leakage concern as hyperparameter tuning.
5. **Report the blend's Brier/RPS improvement over the market ALONE using a
   DM test (Section E)** stratified by the situational buckets — this turns
   "we beat the crowd on 1 match" into "our blended model has a statistically
   significant edge of X RPS points specifically in [lopsided / low-profile /
   neutral-venue] matches, p < 0.05, n = N", which is the kind of claim that's
   actually defensible.
6. **Don't expect — and don't need — a large edge.** Given Forrest/Goddard/
   Simmons (2005) and Angelini/De Angelis (2019), even a *consistent,
   statistically-significant* edge of a few percent in RPS/Brier terms, in a
   subset of match types, would be a genuinely strong and literature-consistent
   result for an Elo+ordered-logit model. Calibrate expectations (and the
   tournament narrative) accordingly: the realistic goal is "narrow,
   situational, statistically defensible edge," not "consistently and
   substantially beat the market everywhere."

---

## APPENDIX: Master citation list (for re-lookup)

- Friedman, J.H. (2001). "Greedy Function Approximation: A Gradient Boosting
  Machine." *Annals of Statistics*, 29(5), 1189-1232.
  https://projecteuclid.org/journals/annals-of-statistics/volume-29/issue-5/Greedy-function-approximation-A-gradient-boosting-machine/10.1214/aos/1013203451.full
- Chen, T. & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System."
  KDD 2016. https://arxiv.org/abs/1603.02754
- Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting
  Decision Tree." NeurIPS 2017.
  https://www.semanticscholar.org/paper/LightGBM:-A-Highly-Efficient-Gradient-Boosting-Tree-Ke-Meng/497e4b08279d69513e4d2313a7fd9a55dfb73273
- Prokhorenkova, L. et al. (2018). "CatBoost: unbiased boosting with
  categorical features." NeurIPS 2018. https://arxiv.org/abs/1706.09516
- Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022). "Why do tree-based
  models still outperform deep learning on tabular data?" NeurIPS 2022
  Datasets & Benchmarks. https://arxiv.org/abs/2207.08815
- Gorishniy, Y., Rubachev, I., Khrulkov, V. & Babenko, A. (2021). "Revisiting
  Deep Learning Models for Tabular Data." NeurIPS 2021.
  https://arxiv.org/abs/2106.11959 (code:
  https://github.com/yandex-research/rtdl-revisiting-models)
- Guo, C. & Berkhahn, F. (2016). "Entity Embeddings of Categorical
  Variables." https://arxiv.org/abs/1604.06737
- Hyndman, R.J. & Athanasopoulos, G. *Forecasting: Principles and Practice*
  (3rd ed.), chapter on time series cross-validation. https://otexts.com/fpp3/
  ; blog: https://robjhyndman.com/hyndsight/tscv/
- Bergmeir, C. & Benítez, J.M. (2012). "On the use of cross-validation for
  time series predictor evaluation."
  https://www.researchgate.net/publication/256720783
- Bergstra, J. & Bengio, Y. (2012). "Random Search for Hyper-Parameter
  Optimization." JMLR, 13, 281-305. https://jmlr.org/papers/v13/bergstra12a.html
- Niculescu-Mizil, A. & Caruana, R. (2005). "Predicting Good Probabilities
  With Supervised Learning." ICML 2005.
  https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Lundberg, S.M. & Lee, S.-I. (2017). "A Unified Approach to Interpreting
  Model Predictions." NeurIPS 2017. https://arxiv.org/abs/1705.07874
- Wheatcroft, E. (2019/2021). "Evaluating probabilistic forecasts of football
  matches: the case against the ranked probability score."
  https://arxiv.org/abs/1908.08980 (useful caveat on RPS for ordinal
  evaluation, generalizable beyond football).

### Football model-vs-market citations (Section "Football-specific: Model vs.
Market/Crowd Edge")
- Dixon, M.J. & Coles, S.G. (1997). "Modelling Association Football Scores and
  Inefficiencies in the Football Betting Market." J. Royal Statistical Society
  Series C, 46(2), 265-280.
  https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/1467-9876.00065
- Forrest, D., Goddard, J. & Simmons, R. (2005). "Odds-setters as forecasters:
  The case of English football." International Journal of Forecasting, 21(3),
  551-564. https://ideas.repec.org/a/eee/intfor/v21y2005i3p551-564.html
- Constantinou, A.C. & Fenton, N.E. (2012). "Determining the level of ability
  of football teams by dynamic ratings based on the relative discrepancies in
  scores between adversaries" (pi-ratings). Journal of Quantitative Analysis
  in Sports, 8(1). DOI 10.1515/jqas-2012-0036.
  http://www.constantinou.info/downloads/papers/pi-ratings.pdf
- Constantinou, A.C., Fenton, N.E. & Neil, M. (2012). "pi-football: A Bayesian
  network model for forecasting Association Football match outcomes."
  Knowledge-Based Systems, 36, 322-339.
  https://dl.acm.org/doi/10.1016/j.knosys.2012.07.008
- Constantinou, A.C. (2019). "Dolores: a model that predicts football match
  outcomes from all over the world." Machine Learning (Springer). DOI
  10.1007/s10994-018-5703-7. https://link.springer.com/article/10.1007/s10994-018-5703-7
- Štrumbelj, E. (2014). "On determining probability forecasts from betting
  odds." International Journal of Forecasting, 30, 934-943.
  https://www.sciencedirect.com/science/article/abs/pii/S0169207014000533
- Boshnakov, G., Kharrat, T. & McHale, I.G. (2017). "A bivariate Weibull count
  model for forecasting association football scores." International Journal
  of Forecasting, 33(2), 458-466.
  https://www.sciencedirect.com/science/article/abs/pii/S0169207017300018
- Egidi, L., Pauli, F. & Torelli, N. (2018). "Combining historical data and
  bookmakers' odds in modelling football scores." arXiv:1802.08848.
  https://arxiv.org/pdf/1802.08848
- Angelini, G. & De Angelis, L. (2019). "Efficiency of online football betting
  markets." International Journal of Forecasting, 35(2), 712-721.
  https://www.sciencedirect.com/science/article/abs/pii/S0169207018301134
- Inácio, M., Izbicki, R., Lopes, D., Salasar, L.E., Poloniato, J. & Diniz,
  M.A. "Wisdom of the crowds forecasting the 2018 FIFA Men's World Cup."
  arXiv:2008.13005. https://arxiv.org/pdf/2008.13005
- Diebold, F.X. & Mariano, R.S. (1995). "Comparing Predictive Accuracy."
  Journal of Business & Economic Statistics — overview/implementation:
  https://www.emergentmind.com/topics/diebold-mariano-test ; R:
  https://pkg.robjhyndman.com/forecast/reference/dm.test.html (Harvey-
  Leybourne-Newbold small-sample correction discussed therein).

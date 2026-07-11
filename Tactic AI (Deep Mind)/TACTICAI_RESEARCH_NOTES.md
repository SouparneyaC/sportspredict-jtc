# TacticAI (Google DeepMind × Liverpool FC): Research Notes

**Compiled:** 2026-07-09. **Sources read in full:** the peer-reviewed Nature Communications article
(Wang, Veličković, Hennes et al., *Nature Communications* 15:1906, 2024), its 17-page official
Supplementary Information, the arXiv preprint (2310.10553 v2, confirmed near-identical in content to
the published version plus its own appendix), the DeepMind blog post, five short media-coverage notes,
the official Zenodo figures/statistics notebook, and three related papers: the two acknowledged
DeepMind×Liverpool FC precursor works (*Game Plan*, 2020, and *Graph Imputer*, 2022) and one
academic follow-up that explicitly builds on TacticAI (*Maximising the Set-Piece Return*, June 2026).
No official TacticAI training code exists publicly (confirmed by a direct GitHub search — see
`code/NO_OFFICIAL_CODE_RELEASE.md`), and the underlying 7,176-corner Liverpool FC tracking dataset is
proprietary and was never released. This document is entirely derived from what is publicly available.

---

## 1. What TacticAI is, and the problem it solves

TacticAI is an AI system built by Google DeepMind together with domain experts from Liverpool FC (a
multi-year research collaboration) to give football coaches tactical insight into **corner kicks** — the
set piece where the ball is played in from the corner flag after it goes out of play off a defender.

The paper's own framing for *why corner kicks specifically*: among all the "set pieces" in football (free
kicks, corner kicks, goal kicks, throw-ins, penalties), corners are the one type that simultaneously (a)
happens often (roughly 10 per Premier League match), (b) is taken from a fixed, rigid starting position
(the ball is always placed at the same spot, unlike open play), and (c) offers an immediate, direct
scoring opportunity. Because a corner is a "restart" with a brief pause in play, teams get to walk into a
pre-rehearsed formation — which means a corner is a rare moment in an otherwise chaotic, continuous sport
where tactics can actually be analyzed and improved in a principled way, the same way a chess position
can be analyzed independent of how the players got there.

TacticAI addresses three questions a coach might ask about any given corner-kick setup:

1. **Prediction** — for a given arrangement of players, what's likely to happen? (Who touches the ball
   first? Will a shot be taken?)
2. **Analysis** — given a corner that has already been played, can we find other, similar corners from
   history to compare against (e.g., "has this exact kind of routine worked before")?
3. **Optimization** — how should the players be repositioned to make a particular outcome more or less
   likely (e.g., how should the defense reposition to reduce the attacking team's shot probability)?

These three questions map directly onto TacticAI's three components, described in Section 3 below:
**receiver prediction**, **similar-corner retrieval**, and **guided (generative) tactic adjustment**. A
separate, closely related **shot prediction** model is also built, primarily as a way to *evaluate*
whether a given tactic (real or adjusted) is dangerous.

The core technical constraint the whole paper is designed around: **gold-standard corner-kick data is
scarce.** Even a full Premier League season yields only ~10 corners per match, and detailed player
tracking is only available at all from a handful of top leagues. TacticAI's headline technical claim is
that it achieves strong, useful results *despite* this scarcity, by exploiting a mathematical property
of football pitches (left-right and up-down symmetry) to make the model dramatically more data-efficient
— this is explained in Section 3.

---

## 2. The data and graph representation

### 2.1 Raw data and dataset construction

The underlying data is **optical player-tracking data**, not event data: for every match, all 22
on-pitch players (plus the ball) have their `(x, y)` position on the pitch recorded continuously
(25 frames/second), from which velocities are derived by finite differencing. Separately, event-stream
data (passes, shots, goals) and lineup data (player heights, weights, roles) are layered on top. This is
proprietary Liverpool FC tracking data, not open data.

The raw dataset was **9,693 corner kicks from three Premier League seasons (2020–21, 2021–22, and
2022–23 up to January 2023)**. After aligning the four data sources by game ID and timestamp and
filtering out corners where that alignment failed (missing tracking frames or event labels), **7,176
valid corners** remained for training and evaluation — an 80/20 random train/test split was used for
all three benchmark tasks (a *temporal* split, training on earlier games and testing on the most recent
20%, was also tried as a robustness/ablation check — see Section 4.3).

Critically, TacticAI does **not** use the full trajectory of a corner kick — it uses a **single static
snapshot**: the frame at the exact moment the attacking kicker makes contact with the ball. Everything
the model sees about a corner is frozen at that one instant. No ball trajectory and no subsequent player
movement is given to the model as input; only the eventual *outcome* (who touched it first, was there a
shot) is used as a training label, extracted from the event stream that comes after that frame.

### 2.2 From a freeze-frame to a graph — the key representational idea

Turning a corner-kick freeze-frame into something a neural network can learn from is the paper's central
representational choice, and it's the part most relevant to comparable data we might have on hand. A
**graph** is just a set of "nodes" (things) connected by "edges" (relationships between pairs of things);
a **graph neural network (GNN)**, described more in Section 3, is a model that computes a representation
for each node by repeatedly having it exchange short messages with the nodes it's connected to.

TacticAI's graph for one corner kick:

- **Nodes = the 22 on-pitch players** (11 per team; no goalkeeper is excluded, both are included).
  Each node carries a small feature vector: `(x, y)` position, `(x, y)` velocity, height (cm), weight
  (kg), and a binary "is this player currently possessing the ball" flag (which is 1 for the corner
  taker and 0 for everyone else, since the ball hasn't moved yet in the snapshot). Missing
  height/weight (385 out of 22 × 9,693 player-occurrences) is filled with a default of 180cm/75kg.
- **Edges = every pair of players is connected** (a "fully connected" graph — the paper explicitly
  chooses not to encode any notion of proximity or passing lanes into which edges exist, leaving that as
  a stated direction for future work). Each edge carries exactly one feature: a binary flag for whether
  the two players are on the same team or opposing teams. Distances between players are **not**
  explicitly given as edge features (the model would have to learn to reconstruct that from the raw
  `(x, y)` node positions if useful) — this is a deliberately minimal feature set; the paper notes its
  "factorised design... does not rely on intricate feature engineering."
- **Global (whole-graph) features** vary by task: none for receiver prediction; the (ground-truth, at
  train time) receiver's identity for shot prediction, since shot probability is computed *conditional*
  on who received it; and a shot/no-shot indicator for the guided-generation task, since generation is
  conditioned on which outcome you want to produce.
- Positions are pitch-normalized (zero-centered and rescaled to a standard pitch size, defaulting to
  110m × 63m when the literal pitch dimensions for a stadium weren't available) so that the model isn't
  sensitive to which specific stadium a corner was taken in.
- No vertical (aerial/z-axis) player position is available in the source data — only 2D `(x,y)` — even
  though the paper notes aerial duels are common at corners and this would be a natural feature to add
  if available.

This graph representation — 22 player-nodes with position/velocity/physical features, fully connected,
one binary teammate/opponent edge feature — is a genuinely simple recipe, and it is exactly what
StatsBomb's freely available "360" data can approximate for a single tagged event (see Section 6).

---

## 3. Model architecture and its three (or four) components

### 3.1 What a GNN and a "graph attention network" are, in plain terms

A **graph neural network (GNN)** computes a representation ("embedding") for each node by repeated
rounds of **message passing**: at each round, every node looks at its neighbors, combines information
from them (using a small learned function, like a mini neural network), and updates its own internal
state. After several rounds, a node's final embedding encodes not just its own raw features but
information gathered from its whole local neighborhood — in this case, since the graph is fully
connected, ultimately from all 21 other players.

TacticAI specifically uses a **graph attention network (GAT)**, and more precisely its improved variant
**GATv2**. "Attention" here means that when a node combines messages from its neighbors, it doesn't
weight every neighbor equally — it learns, per pair of nodes, a scalar "how much should I pay attention
to this particular neighbor" score (computed via a small neural network taking both nodes' current
states and their connecting edge feature as input, then normalized across all neighbors with a softmax).
Concretely, in TacticAI a player node can learn to pay more attention to, say, the specific opponent
marking them, rather than treating a marker and an unrelated player on the far side of the pitch
identically. The paper's own ablation study confirms this design choice empirically (see Section 3.4).

### 3.2 Geometric deep learning: exploiting pitch symmetry for data efficiency

This is the paper's single most distinctive technical idea, directly motivated by data scarcity. The
argument: a football pitch is (approximately) symmetric under **horizontal reflection** (flipping
left/right) and **vertical reflection** (flipping which end of the pitch is "up") — if you take a real
corner-kick situation and mirror it in either direction, the game situation is *strategically
equivalent*: the receiver, and whether a shot happens, should be the same regardless of which of the
four mirror-images of the pitch you happen to be looking at.

Concretely, TacticAI generates **all four combinations of these two reflections** — the original
("identity view"), horizontal flip, vertical flip, and both flips — for every input corner. Mathematically
these four reflections plus the identity form a mathematical structure called the **dihedral group
D₂** (a "group" in this context is just a formal way of describing a set of symmetry transformations and
how they combine). The model is built so that it is **guaranteed** — by construction, not by hoping the
training data teaches it — to give predictions that respect this symmetry. This "baking in" of known
structure is the essence of **geometric deep learning (GDL)**: instead of a fully generic model that has
to *learn* from data that a mirrored corner should be treated the same way, you build the constraint into
the architecture itself, shrinking the space of functions the model has to search over and therefore
needing much less training data to generalize well — a good match for a domain where only a few hundred
games are played per season.

Two ways to enforce this symmetry are contrasted in the paper:

- **Frame averaging**: run the exact same network independently on all four reflected views, then simply
  average the four outputs. Simple, but the four views never interact with each other while being
  computed.
- **Group convolution** (what TacticAI actually uses): let the four differently-transformed views
  interact with *each other* during the message-passing computation itself, at every layer, in a
  carefully constrained way that still guarantees the same overall symmetry property holds. This is more
  expressive than frame averaging because information from one reflected view can influence another's
  computation mid-network, not just at the very end.

TacticAI's full encoder: given an input graph, generate its 3 reflected views (4 total with the
identity), then pass all four through **4 stacked GATv2 group-convolution layers** (each layer having 8
attention "heads," computing 4-dimensional latent features per player per view). After 4 layers, you
have a `4 views × 22 players × 4-dimensional` tensor of player representations.

How this is turned into a final answer depends on the task:

- Tasks where flipping the pitch **shouldn't change the answer at all** (who receives the corner; will
  there be a shot) are called **invariant** tasks — for these, the four views' representations are simply
  averaged together into one final representation per player (or, for shot prediction, further averaged
  across all 22 players into one whole-graph representation), because reflecting the pitch is not
  supposed to change who receives the ball or whether a shot happens.
- The tactic-adjustment (generative) task is different — flipping the pitch **should** flip the
  suggested new positions and velocities too, so it's called **equivariant** rather than invariant, and
  only the identity view's representation is used directly (no averaging), since averaging would destroy
  the direction-specific information needed to produce a correctly-oriented suggestion.

### 3.3 The three (really four) components

**1. Receiver prediction (a node classification task).** Predict which one of the 22 players makes first
contact with the ball. Modeled as choosing one of 22 classes. Best model (GATv2 + D₂ group convolution):
**0.782 ± 0.039 top-3 accuracy** after 50,000 training steps — i.e., the true receiver is among the
model's top 3 guesses about 78% of the time. (Top-3, not top-1, is used deliberately, since predicting
exactly who wins a contested header is inherently very hard — the model has no information about
fatigue, fitness, or the actual ball trajectory.)

**2. Shot prediction (a whole-graph binary classification task).** Predict whether the corner leads to a
shot attempt at all (defined broadly: a direct corner, a goal, an aerial, a hit on the post, or a shot
saved by the keeper or missing the target). The raw dataset is imbalanced: 1,736 corners labeled "shot
taken" vs. 5,440 labeled "no shot." Directly predicting shot probability from the graph alone gets only
F1 = 0.52 ± 0.03 — barely better than chance for this class imbalance. The key improvement: **decompose**
the shot probability using the already-built receiver predictor, via the law of total probability:

```
P(shot | corner) = Σ_i  P(receiver = i | corner) × P(shot | receiver = i, corner)
```

That is: instead of asking the model to predict a shot directly from the raw setup, first predict who's
likely to receive it, then predict shot probability *conditional on* a specific receiver, and combine the
two using the receiver probabilities as weights. This decomposition alone lifts F1 from 0.52 to 0.68, and
with the same GATv2 + D₂ architecture reaches **F1 = 0.71 ± 0.01**. This is a nice, general lesson: when a
target event depends heavily on an intermediate, more-predictable quantity, factor the prediction through
that intermediate quantity rather than trying to predict the final outcome end-to-end.

**3. Guided (generative) tactic adjustment — the plausibility-constrained generative component.** Given
a corner and a *desired* outcome (e.g., "I want the shot probability of the defending team's opponent to
go down"), generate new player positions and velocities that would produce that outcome. This is the
paper's generative capability, described as separate from the two predictive components above, sharing
the same encoder architecture but with its own decoder ("without sharing parameters"). Technically, it's
a **conditional variational autoencoder (VAE)**: each player's latent embedding from the identity view is
mapped to the parameters (mean and standard deviation) of a 2-dimensional Gaussian distribution, a sample
is drawn from that distribution (using the differentiable "reparameterization trick" so gradients can
still flow through the random sampling step), and that sample is decoded into a suggested position/
velocity adjustment for that player. At training time, the model is given the real, ground-truth outcome
(shot/no-shot) as an extra input and learns to *reconstruct* the real player positions — i.e., the
training objective is realism/reconstruction, not "maximize shot probability." At inference time, you
instead feed in the *opposite* of what actually happened, and the model samples a plausible new
configuration consistent with that different outcome. Practically, the process is simplified to adjusting
only one team at a time (e.g., only the defenders) while holding the other team's players fixed, since
simultaneously optimizing both sides realistically would require modeling how each team reacts to the
other in real time.

**"Guardrails" — why this generative component doesn't produce nonsense.** The paper doesn't use the
word "guardrails" itself, but this is the right name for what makes the generative component actually
useful rather than a blind numerical optimizer: because the decoder is trained as a *reconstruction*
model (learn to reproduce realistic historical player configurations, just conditioned on a target
outcome) rather than as a naive gradient-ascent optimizer chasing "minimize shot probability" with no
other constraint, its outputs are implicitly kept close to the distribution of real corner kicks. The
paper backs this up with two concrete checks:
- **A statistical indistinguishability test**: 200 synthetic (adjusted) corners and their originals were
  fed to a simple classifier (an MLP) asked to tell real from generated. It achieved **F1 = 0.53 ± 0.05**
  — essentially random-chance accuracy, meaning the generated adjustments are not statistically
  distinguishable from real corner-kick configurations.
- **Stability/plausibility bounds** (Supplementary Figure 6, based on 1,100 sampled player adjustments):
  suggested position changes are almost all under 1 meter (rarely up to 4m), no player is ever moved out
  of the pitch's bounds except in 3 cases (and those weren't already out-of-bounds beforehand), and
  suggested velocities exceed anything seen in the real training data for only 0.3% of players. In other
  words, the model overwhelmingly proposes subtle, physically plausible tweaks rather than wild,
  unrealistic ones.

Contrast this with the June-2026 follow-up paper (Section 5), which does **not** get this property for
free from its training objective (because it directly optimizes a reward, not reconstruction) and instead
has to hand-code hard numeric bounds (max ±2m position change, ±2m/s velocity change per step, a
95th-percentile empirical speed cap) directly into its simulation environment to prevent physically
impossible suggestions. That contrast is the clearest way to see what TacticAI's implicit guardrail is
actually doing and why the paper considers it a genuine methodological contribution, not just a nice
side effect.

**4. Similar-corner retrieval (not a trained predictive task, but a use of the learned representations).**
Because TacticAI computes a numeric embedding for every player/corner as a side effect of the receiver
and shot models, those embeddings can be reused to search for tactically similar historical corners
without any extra training — just by finding the nearest embeddings in that latent space. The paper
visualizes this with t-SNE (a technique for compressing high-dimensional embeddings down to 2D for
plotting): corners with similar tactical patterns (e.g., in-swinging vs. out-swinging attacks) visibly
cluster together in TacticAI's learned embedding space (Figure 2), whereas the same corners plotted using
only their *raw* input features do **not** show any clear clustering (Supplementary Figure 1) — evidence
that the model has learned something genuinely useful about tactical structure beyond just memorizing raw
positions.

### 3.4 Ablation studies (what design choices actually mattered)

The paper ran a systematic ablation on the receiver-prediction task to justify each architectural choice,
each time asking a specific yes/no question and testing it:

| Question | Comparison | Result |
|---|---|---|
| Does a graph representation help at all (vs. a plain CNN on the pitch as an image)? | CNN vs. graph-based Deep Sets | CNN: 0.364 top-3 acc.; Deep Sets: 0.713 — big jump just from using *any* graph/set representation |
| Does explicitly modeling player-player adjacency help (vs. treating each player in isolation)? | Deep Sets (no edges) vs. MPNN/GATv2 (full graph) | 0.713 → 0.723 (MPNN) / 0.748 (GATv2) |
| Are attention-based GNNs (GAT) better than the fully generic message-passing GNN (MPNN)? | MPNN vs. GATv2 | GATv2 (0.748) beats MPNN (0.723) and is also less prone to overfitting |
| Does exploiting D₂ symmetry help? | GATv2 alone vs. + D₂ frame averaging vs. + D₂ group convolution | 0.748 → 0.780 → **0.782** (best) |

A **temporal-split** version of this same ablation (training on the chronologically earliest 80% of
corners, testing on the most recent 20%, rather than a random shuffle) showed the same relative ordering
of models held up, and — notably — the D₂-symmetric model was the *most stable* under this harder,
more realistic split (its accuracy dropped by under 3 percentage points, vs. 5+ points for non-symmetric
baselines), which the authors attribute directly to the symmetry constraint making the model less
sensitive to superficial repetition of specific tactics in the training data. Separate ablations also
confirmed player height/weight features help modestly (dropping them costs ~2 points of accuracy), and
that GATv2's attention mechanism is competitive with (not clearly worse than) more exotic alternatives
like heterogeneous GATs or Transformer-style dot-product attention.

---

## 4. Evaluation: quantitative results and the human/coach case study

### 4.1 Quantitative benchmark summary

| Task | Metric | Best result |
|---|---|---|
| Receiver prediction | Top-3 accuracy | 0.782 ± 0.039 |
| Shot prediction | F1 score | 0.71 ± 0.01 |
| Generated adjustments realism | F1 of a real-vs-generated classifier (chance ≈ 0.5) | 0.53 ± 0.05 |
| Generated adjustments, effect on shot probability (defensive) | Mean shot prob. before → after | 0.75 ± 0.14 → 0.69 ± 0.16 (z=2.62, p<0.001) |
| Generated adjustments, effect on shot probability (attacking) | Mean shot prob. before → after | 0.18 ± ... → 0.31 ± ... (z=-4.46, p<0.001) |

These quantitative results establish that the individual predictive components work reasonably well on
held-out data, and that the generative component's adjustments move the model's *own* shot-probability
estimate in the intended direction. But — and the paper is explicit about this — none of this actually
tells you whether the system is *useful* to a real coach. That's what the human case study is for.

### 4.2 The human case study — methodology (this is the part most summaries skip)

The paper's central claim of practical utility rests on a structured case study with **five football
experts affiliated with Liverpool FC**: three data scientists, one video analyst, and one coaching
assistant. Every rater completed **four separate tasks**, each carefully designed to isolate one specific
question, with team/player identities always hidden (raters saw only anonymized dots showing position,
velocity, and attacking/defending team membership — heights and weights were deliberately withheld too,
to avoid clutter, and an ablation separately confirmed removing them barely hurts model accuracy).

**Task 1 — Realism (a blind "Turing test" for tactics).** Starting from 50 corners held out from
training, some were left as-is and some had TacticAI's generative model apply an adjustment; raters were
shown corners one at a time (without being told which category any one belonged to) and asked to judge
real vs. generated. Result: raters' average classification F1 was only **0.60 ± 0.04**, and there was
**no statistically significant difference** between the average "looks real" rating given to genuinely
real vs. generated samples (z = −0.34, p > 0.05). Qualitatively, raters described three different
strategies for trying to spot fakes: looking for anything "markedly unusual" (e.g., an opponent left in
open space), judging plausibility even for a suboptimal setup (which tended to just call everything
real), or trying to recall the exact real setup from memory (used specifically by raters who specialize
in corner-kick analysis). All the raters described the task as genuinely difficult.

**Task 2 — Receiver plausibility.** Using the same 50 corners, raters were separately asked (without
seeing TacticAI's answer) to name whichever attacking players they thought were most likely to make first
contact — some raters named 1 player, some named 3–5. A sample was scored "correct" if *any* of a rater's
named players appeared in TacticAI's own top-3 prediction. Average top-3 "accuracy" by this measure was
**0.79 ± 0.18** overall (0.81 ± 0.17 for real corners, 0.77 ± 0.21 for generated ones — no significant
difference, z = 0.97, p > 0.05), meaning TacticAI's predictions line up with expert intuition about as
well on synthetic corners as on real ones. Interestingly, a follow-up statistical test (one-way ANOVA
plus a Tukey post-hoc test) found the five raters' own answers were themselves significantly different
from each other, clustering into three distinct groups (F(1,4) = 14.46, p < 0.001) — different experts
genuinely focus on different cues — yet TacticAI's fixed top-3 prediction still tracked all of these
different human perspectives reasonably well, suggesting the model has captured something broadly salient
rather than overfitting to one particular way of reading a corner.

**Task 3 — Similar-corner retrieval usefulness.** Using 50 different held-out reference corners, each was
paired with one retrieved "similar" corner — either the nearest neighbor in TacticAI's learned embedding
space, or the nearest neighbor by a simpler baseline (raw positional distance). Raters judged each pair
as usefully similar or not, without knowing which retrieval method produced it. TacticAI's average recall
across raters was **0.59 ± 0.09** vs. the positional-distance baseline's **0.36 ± 0.10** — a statistically
significant improvement (z = 2.34, p < 0.05). Raters described considering things like in-/out-swinging
delivery, whether a short-corner option existed, zonal vs. man-marking, the count of players in the
18-yard box, and goalkeeper positioning. Notably, raters flagged that testing only the single "top-1"
retrieval is an unusually strict test of the system — in real use, an analyst would likely want to see
10–20 candidate similar corners, not just one — implying the reported number likely understates real
usefulness.

**Task 4 — Tactical adjustment usefulness (this is where the headline "90%" figure comes from).** Using
50 more held-out corners, TacticAI's guided generation was used to adjust only the *defending* team's
positions/velocities (attacking team held fixed, matching a realistic workflow where the defense reacts
to a given attacking setup) specifically to reduce predicted shot probability. Raters saw the original and
adjusted version side-by-side (with left/right order randomized to control for bias) and rated: (a) which
version has better-positioned defenders overall, and (b) for each individual defensive player, whether
their specific repositioning was constructive (+1), made no difference (0), or was destructive (−1).
**Average rating across all 50 situations and all 5 raters was +0.7 ± 0.1**, and **45 of the 50 situations
(90%)** were judged favorable on average by majority vote — this is the number quoted throughout the
paper's abstract, the blog post, and every piece of media coverage ("TacticAI's suggestions were preferred
90% of the time"). Statistically, a t-test across the 50 per-situation average ratings confirmed this is
significantly greater than zero (t(49) = 9.20, p < 0.001), and each of the five raters individually also
showed a statistically significant positive rating on their own (t(49) ranging 5.84–7.90, all p < 0.001).
Figure 5 in the paper shows illustrative examples, including one striking case where **10 of the 11
defenders** were independently judged to have been usefully repositioned — nearly the entire defending
unit. Raters also volunteered that they found this kind of tool valuable specifically as a way to *detect
players who are not following their coach's determined tactic* — i.e., using the gap between a player's
actual position and TacticAI's suggested "correct" position as a coaching diagnostic, not just as a source
of brand-new tactics to try.

### 4.3 What the human study adds beyond the quantitative numbers

The consistent theme across all four tasks: TacticAI performs about as well on its own *generated*
scenarios as on *real* ones (Tasks 1 and 2 both show no significant real-vs-generated gap), which is
exactly the property you'd want from a generative planning tool — it isn't just memorizing training data,
and its outputs are good enough that experts can't reliably distinguish them from reality. The inter-rater
agreement checks (via ANOVA/Tukey tests across all four tasks) consistently showed either high agreement
or, where disagreement existed (Task 2's rater clustering), that TacticAI's answers were still broadly
compatible with multiple different expert perspectives rather than matching only one. This combination —
statistically confirmed usefulness, replicated across five independent experts with different specialties
— is what elevates the paper's claim beyond "our benchmark accuracy numbers look fine" to "domain experts
in a real club found this genuinely useful," which is the actual bar the paper is trying to clear.

---

## 5. What the precursor and follow-up papers add

### 5.1 Precursor: *Game Plan* (Tuyls, Omidshafiei et al., 2020) — the research vision, not TacticAI itself

This is a long (41-page) position/survey paper, not a technical contribution in the TacticAI sense. It
lays out DeepMind and Liverpool FC's shared long-term research agenda across three "frontiers" —
statistical learning, game theory, and computer vision, each pairwise combined — converging on a vision
for an **"Automated Video Assistant Coach" (AVAC)**: a long-term aspirational system that would fuse all
three research areas into one assistant for players, coaches, and spectators. TacticAI (2024) can be read
as a small, concrete realization of exactly one corner of this vision (statistical learning + a form of
prescriptive/generative recommendation), four years before the AVAC concept as a whole.

The paper's one concrete technical contribution is a case study in classical **game theory** applied to
**penalty kicks** (not corners), reproducing and extending Palacios-Huerta's (2003) famous analysis: using
a 12,399-penalty-kick Opta dataset, the authors confirm that professional penalty-takers and goalkeepers
play something very close to a game-theoretic Nash equilibrium (measured via Jensen-Shannon divergence
between empirical play frequencies and the theoretically optimal Nash frequencies — very small, around
0.04–0.09%). They then push this further by combining it with statistical learning (their "Frontier 1"):
using an 18-dimensional "Player Vector" representation of each kicker's individual playing style (from
prior work by Decroos & Davis), they cluster penalty-takers into 5–6 style groups via K-means, and show
that different clusters, despite having statistically similar *empirical* shot-direction behavior, have
measurably *different* Nash-recommended optimal strategies — i.e., a player's individual style genuinely
changes what the theoretically-best strategy for them would be, a level of granularity a single
one-size-fits-all game-theoretic model can't capture. This is the direct conceptual ancestor of TacticAI's
whole approach (learned player-level representations feeding into a decision-support system), just without
any graph neural network — that's introduced two years later in Graph Imputer.

### 5.2 Precursor: *Graph Imputer* (Omidshafiei et al., *Scientific Reports*, 2022) — the direct technical predecessor

This paper is explicitly named in DeepMind's own TacticAI blog post as the direct predecessor, and it is
the first of the two precursors to actually combine **graph neural networks with football tracking data**
— the exact combination TacticAI builds on. But it solves a different, narrower problem: **not** tactical
prediction, but **filling in missing player positions** when a broadcast camera doesn't have every player
in frame. A single stadium broadcast camera only ever shows part of the pitch, so any team trying to use
tracking-style analytics off broadcast video (rather than expensive dedicated stadium tracking installs)
has players popping in and out of view constantly. The Graph Imputer predicts the hidden positions of
off-screen players using **both past and future observed frames** (bidirectionally) — the model uses
whatever frames of a player *are* visible, before and after a gap, to estimate what happened while they
were off-camera.

Architecturally, it combines **bidirectional LSTMs** (a type of recurrent network used here per-player, to
integrate information forward and backward through time) with **GraphNets** (message-passing graph
networks used per-timestep, to integrate information across the 22 players + ball at each instant) inside
a **variational** framework — meaning it produces a *distribution* over plausible trajectories (so you can
sample multiple different plausible "what might have happened off-camera" reconstructions), not one
single deterministic guess. Trained and evaluated on 105 full Premier League matches (30,838 training /
4,024 test trajectory sequences), it clearly outperforms strong existing baselines (GVRNN, Social LSTM,
spline interpolation) both on raw positional prediction error and on a downstream analytics task (pitch
control — a standard technique for estimating which team "controls" each area of the pitch at a given
moment), including specifically in situations with a large fraction of off-camera players.

Graph Imputer establishes two things TacticAI directly inherits: (1) that representing the 22 players +
ball as a graph, with GNN message passing to integrate information across players, is the right structural
choice for this kind of football problem — TacticAI reuses essentially the same node/edge design, just for
a single frozen instant instead of a moving sequence; and (2) that missing/partial player-position data
(the exact situation broadcast video creates) is workable via learned imputation rather than requiring a
full proprietary tracking install — TacticAI's own Discussion section explicitly names broadcast-video
input as a natural, though noisier, way to extend its reach in the future. This is also, as it happens,
almost exactly the situation StatsBomb's freely available "360" data creates — see Section 6.

### 5.3 Follow-up: *Maximising the Set-Piece Return* (Groom, Groom, Belo, Rice, Anderson, Darvariu, Wang; arXiv 2606.06353, June 2026)

This is the one substantive academic paper found that explicitly cites and builds on TacticAI (from
University of Birmingham, Oxford Robotics Institute, and Nottingham Forest FC). It names TacticAI directly
as "the current state-of-the-art in automated set-piece tactic generation" and then identifies a precise,
well-argued limitation: TacticAI's generative component is trained with a **reconstruction/imitation
objective** (the conditional VAE decoder is trained to reproduce real historical player configurations).
This guarantees realistic-looking output (Section 3.3's "guardrail" property above) but means TacticAI can
in principle only ever recommend variations *within the range of tactics coaches have already tried
historically* — it has no mechanism to discover a genuinely novel configuration that has never appeared in
the training data, because its training signal never rewards novelty or effectiveness directly, only
faithfulness to what real corners look like.

Their fix: reframe the same problem as **reinforcement learning (RL)**. They formalize corner-kick
optimization as a Markov Decision Process (MDP — a mathematical framework for sequential decision-making
under uncertainty) where a policy directly and repeatedly adjusts attacking players' positions and
velocities to maximize a reward called **Expected First Contact Shot Probability (xFCS)**. That reward is
itself computed by a separate, frozen, pre-trained GNN reward model — and notably, this reward model's own
internal factorization (`P(shot) = Σ P(contact=i) × P(shot|contact=i)`) is **the identical decomposition**
TacticAI itself used for its shot-prediction component (Section 3.3's Eq. 1 above). The policy that
actually proposes adjustments is trained using two standard deep-RL algorithms (Soft Actor-Critic and
Proximal Policy Optimization), built on the same GATv2 graph-embedding building block TacticAI uses,
trained via 2.5 million simulated environment steps. Evaluated on 3,223 Premier League corners under a
strict chronological (not randomly-shuffled) 80/20 train/test split, the learned RL policies substantially
outperform two traditional gradient-free optimization baselines (random search and simulated annealing)
under a matched, realistic real-time inference budget: the RL policies beat random search in 92–94% of
test scenarios (vs. simulated annealing's mere 6.6%), and yield a mean +0.068 improvement in xFCS —
roughly double the tactical value of a compute-matched random search per corner.

Two details worth flagging for honesty and balance:

- Because this paper's policy is trained to directly optimize a numeric reward rather than to reconstruct
  realistic-looking data, it does **not** get TacticAI's implicit realism "guardrail" for free — instead
  it has to hard-code explicit physical bounds directly into its simulation environment (max ±2 meters of
  position change and ±2 m/s of velocity change per adjustment step, plus capping any resulting speed at
  the 95th percentile of observed real speeds in the tracking data) specifically to prevent the policy from
  recommending physiologically impossible sprints. This is a nice, concrete illustration of the tradeoff:
  TacticAI's reconstruction-based approach gets plausibility "for free" at the cost of being confined to
  historically-seen tactics; this RL approach can discover genuinely new configurations but has to manually
  re-engineer the plausibility constraint that TacticAI got implicitly.
- The authors candidly flag a real limitation of their own reward model (which is, again, architecturally
  very close to TacticAI's own shot predictor): because it evaluates a single static spatial snapshot, it
  may struggle to give credit to slower, coordinated multi-player blocking or screening schemes that only
  pay off over several seconds of unfolding play, and may instead over-reward the more legible, single-frame-
  measurable signal of "a player arriving fast into open space." This is an unresolved problem inherited
  directly from TacticAI's own single-snapshot formulation, not something this paper claims to have solved.
- Like TacticAI's own generation, this paper's environment also only moves one team (the attackers) while
  keeping the defense static — the same simplification, for the same reason (jointly modeling a fully
  reactive two-team interaction is a much harder problem, explicitly named as future work in both papers).

---

## 6. Connecting this to our project (JTC/SportsPredict)

This section is deliberately honest about scope: TacticAI is a prescriptive, generative tactical-planning
tool built for one professional club's coaching staff, evaluated by that club's own experts, trained on
that club's proprietary high-frequency tracking data. JTC/SportsPredict is a probabilistic forecasting
system pricing prediction-market questions against a crowd. These are different problems solved for
different purposes, and most of what makes TacticAI work is not available to us. But there is one genuine,
concrete point of overlap worth naming precisely, and it's worth being equally precise about what does
*not* transfer.

### 6.1 What we actually have that's comparable

As previously confirmed in Stage 1 (before opening this folder), our own StatsBomb data
(`data/external/statsbomb/open-data/`) includes not just the flattened team/player-match panels the
project built this week, but a **`three-sixty/` directory of "360" freeze-frame files** — and checking
this concretely for this write-up: **all 64 of our WC2022 matches have 360 data (WC2018 has none — 360
coverage starts later in StatsBomb's product history)**. Within a sample WC2022 match, 2,873 of 3,388
events (about 85%) carry an attached 360 frame, including 6 of that match's 8 corner kicks. Each 360 frame
gives a `freeze_frame` list of visible players' `(x, y)` locations at that exact event, tagged as
teammate/opponent/keeper/actor — this is structurally very close to TacticAI's node feature set (position,
team membership), just **missing velocity** (360 data is a single instant, not continuous tracking, so
there's nothing to difference to get a velocity vector) and **missing full-pitch coverage**: checking the
same sample match, freeze-frames contain an average of only ~13 of the 22 players (range 3–21), because
360 data is itself derived from broadcast video with a limited camera field of view — meaning our 360 data
has almost exactly the same missing-player problem that DeepMind's own *Graph Imputer* paper (Section 5.2)
was built to solve, and considerably less complete coverage than TacticAI's proprietary full-22-player
optical tracking.

### 6.2 What is genuinely transferable (as an idea, not as code — no training code was released)

- **The graph-representation recipe itself.** Nodes = players with position (+ role/team flag), fully
  connected edges tagged teammate/opponent, is a simple, well-specified pattern that could in principle be
  reproduced against our 360 freeze-frames for the (smaller) subset of WC2022 corners that have both a
  `Corner` event and an attached 360 frame — this is the cleanest conceptual bridge between the two bodies
  of work.
- **The general lesson about exploiting symmetry for data efficiency.** TacticAI's entire architectural
  motivation is explicitly "gold-standard data is scarce" — the same root problem our project has hit four
  separate times (the Platt-scaling diagnostic, the meta-model, the OLS regression, and the t-test all
  failed for the same underlying reason: too few independent matches). TacticAI's specific fix (bake in a
  known symmetry so the model needs less data) doesn't directly apply to our tabular/Elo/Poisson setting,
  but it's a useful conceptual reminder that "reduce what the model has to learn from scratch" is a more
  robust lever than "collect a bit more data and try the same generic model again," which is exactly the
  same spirit as our project's existing shrinkage-prior approach (Section 2 of the StatsBomb integration
  work — empirical-Bayes pooling toward a global mean is, in spirit, another way of reducing the effective
  degrees of freedom a model needs to fit).
- **The receiver-prediction concept, loosely reframed.** Not as a literal reimplementation, but as a
  reminder that a hard prediction problem (will there be a shot) can sometimes be decomposed through an
  easier intermediate one (who gets the ball) — a generally useful modeling pattern, independent of GNNs.

### 6.3 What is honestly not transferable, and why we should not force this

- **Scale.** TacticAI trained on 7,176 real corner kicks from continuous, proprietary, full-22-player
  tracking data. Our comparable resource is, at best, a few hundred WC2022 corner-kick *events* with
  partial-visibility 360 freeze-frames (single instants, ~13 of 22 players typically visible, no velocity)
  — multiple orders of magnitude smaller and structurally thinner than what the paper needed even to get
  its already-modest 0.78 top-3 receiver accuracy. Attempting a from-scratch GNN on this would almost
  certainly reproduce the same failure mode the project has already hit four times: an in-sample-plausible
  model that does not survive honest out-of-sample validation.
- **No coach-evaluation loop.** TacticAI's most novel and convincing contribution — the five-rater,
  four-task Liverpool FC case study and its 90% preference finding — fundamentally depended on having a
  professional club's coaching staff available to judge tactical plausibility. We have no equivalent
  domain-expert panel, and no analogous real-world tactical-intervention use case to evaluate against —
  JTC's actual "customer" is a crowd-scored probability market, not a coaching staff.
- **Different question shape.** JTC's corner-related markets are aggregate team-level counts (e.g. "will
  Team X record 6+ corners") — these are answered well by exactly the kind of Poisson/shrinkage-prior
  machinery the project already built this week (Section 2 of the StatsBomb work). TacticAI answers a
  completely different, much more granular question (which specific player wins first contact on one
  specific corner, and how should specific defenders reposition) — even a working from-scratch replica
  would not directly answer the count-style questions the project actually needs priced.
- **No official code.** Any attempt to build something TacticAI-like would require reconstructing the
  architecture entirely from the paper's equations (Sections 3.1–3.3 above give the complete recipe), a
  non-trivial undertaking disproportionate to the size of benefit for our current, much narrower need.

### 6.4 The honest bottom line

The strongest real connection is **conceptual and exploratory, not a build recommendation**: we now know
(a) we have real, if partial and small, positional (not just count) football data sitting untouched on
disk, and (b) there exists a well-documented, symmetry-exploiting graph representation designed
specifically for exactly this kind of small-sample spatial football data. If the project ever wants a
low-cost, proportionate next step in this direction, it would be exploratory rather than predictive: count
how many WC2022 corners actually have both a tagged `Corner` event and an attached 360 frame, and if that
number is non-trivial, use those freeze-frames purely descriptively (e.g., visualizing attacker clustering
in the box, in-swing vs. out-swing setups) the way TacticAI's own t-SNE plots are used to *understand*
structure — not to train a predictive or generative model, which the sample size and partial visibility
would not currently support, for the same reasons every one of our four prior from-scratch modeling
attempts has failed to survive out-of-sample testing.

---

## Appendix: source files referenced

- `papers/tacticai_nature_communications_2024.pdf` — primary source, full text read
- `papers/tacticai_arxiv_2310.10553.pdf` — preprint, full text read (confirmed near-identical content,
  combined main+supplementary in one document)
- `papers/tacticai_supplementary_information.pdf` — official 17-page supplement, full text read
- `papers/related_precursor_and_followup_work/gameplan_arxiv_2011.09192.pdf` — read in full (intro,
  literature overview, research vision, and the complete penalty-kick game-theory case study)
- `papers/related_precursor_and_followup_work/graph_imputer_scientific_reports_2022.pdf` — full text read
- `papers/related_precursor_and_followup_work/setpiece_graph_rl_arxiv_2606.06353.pdf` — full text read
- `supplementary/TacticAI_Nature_Communications_Figure_data_and_code.ipynb` — reviewed (confirms the
  exact statistical tests behind Figure 4 and the case-study F1/z-test numbers cited above)
- `blog_and_media/deepmind_blog_tacticai.md`, `blog_and_media/media_coverage_notes.md` — read in full
- `code/NO_OFFICIAL_CODE_RELEASE.md` — read in full
- `MANIFEST.md` — read in full
- Locally verified against our own data: `data/external/statsbomb/open-data/data/three-sixty/` (426 files
  total; 64/64 WC2022 matches covered, 0/64 WC2018; sample-match check: 2,873/3,388 events with a 360
  frame, 6/8 corners covered, average 13.2 of 22 players visible per frame)

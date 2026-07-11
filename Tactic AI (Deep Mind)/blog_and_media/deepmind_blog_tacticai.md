# TacticAI: an AI assistant for football tactics — Google DeepMind blog post

- **Source URL:** https://deepmind.google/blog/tacticai-ai-assistant-for-football-tactics/
- **Published:** March 19, 2024
- **Authors (blog post byline):** Zhe Wang and Petar Veličković

---

## Introduction

"Corner taken quickly… Origi!" Liverpool FC achieved a historic comeback in the 2019 UEFA Champions League semi-finals, with one iconic moment being a corner kick by Trent Alexander-Arnold that set up Divock Origi for what has been called Liverpool FC's greatest goal.

Corner kicks present significant scoring opportunities, but developing effective routines requires blending human intuition with tactical analysis to identify patterns in opposing teams and adapt in real time.

Today, in Nature Communications, Google DeepMind introduces TacticAI: an artificial intelligence system providing tactical insights, particularly for corner kicks, through predictive and generative AI. Using a geometric deep learning approach, TacticAI achieves state-of-the-art results despite limited gold-standard corner kick data.

Developed and evaluated with experts from Liverpool Football Club as part of a multi-year research collaboration, TacticAI's suggestions were preferred by human expert raters 90% of the time over tactical setups from actual practice.

---

## The Research Collaboration

Five years ago, Google DeepMind began a multi-year partnership with Liverpool FC to advance AI for sports analytics.

The initial paper, Game Plan, examined why AI should assist football tactics, including penalty kick analysis. In 2022, Graph Imputer demonstrated how AI predicts player movements off-camera when tracking data is unavailable—eliminating the need for in-person scouting.

TacticAI represents a complete AI system combining predictive and generative models, enabling coaches to sample alternative player setups and evaluate possible outcomes.

---

## Core Capabilities

TacticAI addresses three fundamental tactical questions:

1. **Prediction:** For a given corner kick setup, what will happen? (e.g., who receives the ball, will there be a shot attempt?)
2. **Analysis:** Once a setup is played, can we understand what happened? (e.g., have similar tactics succeeded previously?)
3. **Optimization:** How can tactics be adjusted to achieve particular outcomes? (e.g., how should defending players reposition to reduce shot attempt probability?)

---

## Technical Approach: Geometric Deep Learning

Predicting corner kick outcomes is complex due to gameplay randomness and player dynamics. This challenge is compounded by limited gold-standard data—approximately 10 corner kicks occur in each Premier League match per season.

TacticAI employs geometric deep learning by:

- Representing corner kick setups as graphs where nodes represent players (with features including position, velocity, height) and edges represent player relationships
- Exploiting approximate football pitch symmetry through a Group Equivariant Convolutional Network variant
- Generating all four possible pitch reflections (original, horizontal-flip, vertical-flip, both-flips) and forcing identical predictions across all transformations

This symmetry-respecting architecture reduces the function search space, yielding more generalizable models requiring less training data.

---

## Providing Tactical Recommendations

TacticAI assists coaches through two mechanisms:

**Similar Play Retrieval:** Rather than manually reviewing extensive game footage, TacticAI automatically computes numerical player representations enabling efficient similar routine lookup. Expert validation confirmed top-1 retrievals were relevant 63% of the time—nearly double the 33% benchmark from direct position-similarity approaches.

**Generative Optimization:** TacticAI's generative model allows coaches to redesign corner kick tactics optimizing particular outcome probabilities, such as reducing shot attempt likelihood for defensive setups. The system proposes player position adjustments, helping coaches identify critical patterns and key players for tactical success or failure more rapidly.

---

## Evaluation Results

Quantitative analysis demonstrated TacticAI's accuracy in predicting corner kick receivers and shot situations, with player repositioning resembling actual play sequences.

Qualitative evaluation involved a blind case study where raters assessed real gameplay tactics against TacticAI-generated recommendations without knowing the source. Human football experts from Liverpool FC found generated suggestions indistinguishable from authentic corners and preferred them over original situations in 90% of cases, validating both accuracy and practical deployability.

---

## Broader Implications

TacticAI demonstrates assistive AI's potential to revolutionize sports for players, coaches, and fans. Football serves as a dynamic AI development domain featuring real-world multi-agent interactions with multimodal data. Advances in sports AI could translate to computer games, robotics, traffic coordination, and beyond.

The research demonstrates how AI can analyze football while football teaches AI valuable lessons about dynamic systems with human factors ranging from physiology to psychology. TacticAI represents a milestone in developing useful sports AI assistants that blend human expertise with computational analysis.

---

## Research Team

TacticAI represents collaboration between Google DeepMind and Liverpool FC, with authors including Zhe Wang, Petar Veličković, Daniel Hennes, Nenad Tomašev, Laurel Prince, Michael Kaisers, Yoram Bachrach, Romuald Elie, Li Kevin Wenliang, Federico Piccinini, William Spearman, Ian Graham, Jerome Connor, Yi Yang, Adrià Recasens, Mina Khan, Nathalie Beauguerlange, Pablo Sprechmann, Pol Moreno, Nicolas Heess, Michael Bowling, Demis Hassabis, and Karl Tuyls.

---

*Full text captured via WebFetch on 2026-07-09 for archival/research purposes. Original formatting (images, embedded video) not reproduced.*

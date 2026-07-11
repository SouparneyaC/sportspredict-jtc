# Academic Style Notes: Observations from Published Statistical Papers

Prepared from close reading of five primary sources in sports statistics and four secondary sources in econometrics and machine learning. The goal of these notes is to support revision of `JTC_WC2026_Research_Paper.Rmd` by documenting what published papers actually do — with direct quotations as evidence. Sections correspond to the eight problem areas identified in the brief.

---

## 1. Prose vs. Bullet Points

In every primary paper surveyed, body paragraphs in the methodology, results, and discussion sections are continuous prose. Not a single paper uses a vertical bullet list to summarise findings, enumerate model advantages, or describe limitations. The Constantinou & Fenton paper, which is itself a survey of nine previous studies, writes an entire two-page literature review without a single bullet point. Karlis & Ntzoufras present eleven competing models, compare them against each other, and report their selection rationale — all in prose. The instinct to "list things" does appear in these papers, but it is nearly always suppressed in favour of subordinate clauses and explicit logical connectors.

When lists are used, they appear in one specific context: the formal enumeration of mathematical entities whose names are subsequently used in the running text. Constantinou & Fenton list two categories of scoring rules using lettered items (a) and (b) — but immediately return to prose for several paragraphs to discuss those categories. The labels function as reference anchors, not as a replacement for paragraphs.

**Example 1 — literature survey that a lesser draft would have bulleted:**

> "Although several researchers (see, for example, Lee (1997) and Karlis and Ntzoufras (2000) and the references therein) have shown the existence of a (relatively low) correlation between the number of goals scored by the two opponents, this has been ignored in most modelling approaches since it demands more sophisticated techniques. Maher (1982) discussed this issue, and Dixon and Coles (1997) extended the independent Poisson model by introducing indirectly a type of dependence."

*Karlis & Ntzoufras 2003, §1*

**Example 2 — multiple findings reported without bullets:**

> "Fig. 1 shows that, for the typically observed range of counts in football data, the probability of a draw under a bivariate Poisson model is larger than the corresponding probability under the double-Poisson model even if λ₃ is quite small. For example, if we consider a bivariate Poisson model with λ₁ = 0.05 and λ₁ = λ₂ = 1 then we expect almost 3.3% more draws than under the corresponding independent Poisson model, whereas if λ₃ increases to 0.20 we expect 14% more draws. It is also clear that the larger the λ₃ the larger the relative change is."

*Karlis & Ntzoufras 2003, §2.3*

**Example 3 — method descriptions that a lesser draft would have bulleted:**

> "To demonstrate the feasibility of our approach, we consider data on the number of scored goals in the four most popular women's football leagues in Europe. In particular, we consider the English FA Women's Super League, the German Frauen-Bundesliga, the French Division 1 Feminine, and the Spanish Primera Iberdrola for the seasons 2011/12–2018/19 and 2021/22."

*Michels, Otting & Karlis 2023, §1*

**Apply this as:** Delete any bullet list in the body text that could be rewritten as a sentence with commas or a short paragraph with a topic sentence and elaborating sentences. The only exception is a numbered or lettered list of named mathematical objects that will be referenced by those labels in subsequent sentences. Never use bullets to summarise findings, enumerate advantages of an approach, or describe limitations.

---

## 2. Bold Text Usage

Bold is close to absent in the body paragraphs of every primary paper. Constantinou & Fenton use zero bold in the prose sections. Karlis & Ntzoufras use zero bold in prose. The Michels et al. arXiv paper uses bold exclusively inside table captions (to mark which model has the lowest AIC) and never in running text. Grossman & Stiglitz use no bold at all, relying instead on italics for technical terms when emphasis is needed. Callaway & Sant'Anna use bold only for formal named assumptions ("**Assumption 1** (Irreversibility of Treatment)") and for one label ("**Recent Related Literature:**") that signals a subsection within an unusually dense introduction — a structural marker, not an emphasis device.

Key concepts are introduced in plain text, often set off by quotation marks on first use, or by italic for named quantities, or by formal definition environments. They are never made bold simply because they are important or because a reader skimming should notice them.

**Example 1 — key concept introduced without bold:**

> "There is a well-established generic scoring rule, the Rank Probability Score (RPS), which has been missed by previous researchers, but which properly assesses football forecasting models."

*Constantinou & Fenton 2012, Abstract*

**Example 2 — technical term introduced with quotation marks, not bold:**

> "The RPS has been described as a particularly appropriate scoring rule for evaluating probability forecasts of ordered variables (Murphy, 1970)."

*Constantinou & Fenton 2012, §3*

**Example 3 — definition of new term in plain text:**

> "We call this causal parameter the *group-time average treatment effect*."

*Callaway & Sant'Anna 2021, §2.2*

**Apply this as:** Remove all bold from within body paragraphs except for formally named assumptions or theorems where the label is bold by convention. Do not bold a term simply because it is a key concept being defined or used for the first time. If a word needs distinguishing on first use, use italics once; thereafter trust the reader to remember it.

---

## 3. Section and Subsection Headers

Headers across all papers are short noun phrases or short verb phrases. They are descriptive rather than interpretive — they tell the reader what the section is about, not what it argues or concludes. None of the papers use headers that sound conversational, rhetorical, or promotional. No header in any paper surveyed takes the form of a question. The level of specificity is moderate: specific enough to orient the reader, general enough to cover the section's actual content.

**Headers from primary sources, verbatim:**

From Karlis & Ntzoufras 2003:
- "2. The bivariate Poisson distribution and its implementation in sports modelling"
- "2.1. The bivariate Poisson distribution"
- "2.3. The effect of model misspecification"
- "2.4. Estimation"
- "3. Inflated bivariate Poisson distributions"
- "4.1. Modelling football games"
- "5. Discussion"

From Michels, Otting & Karlis 2023:
- "2 Extending the Dixon and Coles model"
- "2.3 Dixon and Coles model as a member of Sarmanov Family"
- "2.5 Shifting probabilities across the entire support"
- "3.2 Baseline model"
- "3.3 Model including team dummies"
- "3.4 Model checking"
- "4 Discussion"

From Constantinou & Fenton 2012:
- "2 SCORING RULES USED IN PREVIOUS STUDIES"
- "3 THE RANK PROBABILITY SCORE (RPS)"
- "4 IMPLICATIONS AND CONCLUSIONS"

From Callaway & Sant'Anna 2021:
- "2. Identification"
- "2.1. Setup"
- "2.2. The group-time average treatment effect parameter"
- "2.3. Identifying assumptions"

From Grossman & Stiglitz 1980:
- "I. The Model"
- "II. Constant Absolute Risk-Aversion Model"
- "D. Existence of Equilibrium and a Characterization Theorem"
- "H. Comparative Statics"
- "I. Price Cannot Fully Reflect Costly Information"

The most granular subsection headers in the primary papers (e.g., "3.3 Model including team dummies") are concrete and technical, not colloquial. A header like "3.3 Model including team dummies" signals what is in the section; it makes no claim about what will be found or argued. Grossman & Stiglitz's "H. Comparative Statics" is a single noun phrase from the field's terminology. The interpretive header style ("Why the Poisson Model Underestimates Draws") does not appear in any paper surveyed.

**Apply this as:** Revise any colloquial or question-form headers to noun phrases that name the content. "Our Approach" becomes "Model Specification". "Why We Chose X" becomes "Rationale for Model Selection" or is deleted in favour of prose in the introduction. "What We Found" becomes "Results" or a more specific phrase like "Predictive Performance". Headers of the form "Leveraging [Concept] to [Goal]" do not appear in this literature.

---

## 4. Methodology Sections — How Results Are Embedded

Across all papers, fitted parameter values and model diagnostics are embedded directly in the prose that interprets them. The text does not merely point to a table and move on — it selects one or two key numbers from the table, names them, and explains what they mean. Inline coefficient reporting follows a consistent structure: parameter symbol or name, estimated value, and interpretive gloss, often with a reference to what would be expected under the null or a baseline.

**Example 1 — covariance parameter quoted inline with interpretation:**

> "The covariance parameter λ₃ was found to be equal to 5.55, which indicated significant covariance between the scores of the opposing teams."

*Karlis & Ntzoufras 2003, §4.2*

**Example 2 — multiple correlations quoted inline without loss of flow:**

> "In particular, due to the underrepresentation of draws and overrepresentation of scores such as 3-0 and 4-0 in women's football, the correlations between home and away goals in our sample are -0.269 (England), -0.352 (Germany), -0.395 (France), and -0.263 (Spain)."

*Michels, Otting & Karlis 2023, §3.1*

**Example 3 — model fit criteria quoted in text then elaborated:**

> "According to the LRT our proposed model fits our data sufficiently well (p-value 0.85). Moreover, the AIC and BIC measures for the full model are 2204.0 and 4928.7 respectively. Both these criteria indicate the selection of our model against the alternative full or saturated model."

*Karlis & Ntzoufras 2003, §4.1*

**Example 4 — chi-squared test embedded in description of data patterns:**

> "Chi-squared tests reject the null hypothesis of independence for each league except for the English FA Women's Super League (p-value: 0.067). While a dependence between home and away goals is in line with data from men's football (see, e.g., Dixon and Coles, 1997; Karlis and Ntzoufras, 2003), the ratios for women's football displayed in Table 1 indicate an underrepresentation of 0-0s in each league."

*Michels, Otting & Karlis 2023, §3.1*

The presentation pattern is: state what the number means, give the number, connect it to a broader inference. The number is never the sentence's subject or lead element. Standard errors or p-values are either placed in parentheses immediately after the estimate (as in calibration table reports: "intercept -0.259 (SE=0.119)") or summarised in the prose as "statistically significant at the 1% level" or "p-value 0.042".

**Apply this as:** Every fitted coefficient or model diagnostic that matters to the paper's argument should appear in one sentence of prose, not only in a table. Quote the value, name the quantity it corresponds to, and say what it implies. Do not write "see Table 3 for results". Write "As Table 3 shows, the home team attack parameter for Milan (0.84) substantially exceeds that of Juventus (0.22), consistent with..."

---

## 5. Regression and Model Result Tables

All papers use tables that are structured for comparison, not just for record-keeping. The core design principle is that the columns capture one consistent dimension of variation (models, or parameters), and the rows capture another (teams, or model variants). Tables include footnotes that explain non-obvious notation, identify the null hypothesis for any p-values reported, and flag the preferred model.

**Table structure from Karlis & Ntzoufras 2003, Table 1 (model selection table):**

Columns: Model distribution | Additional model details | Log-likelihood | Number of parameters | p-value | AIC | BIC

Rows enumerate twelve model variants (double Poisson, bivariate Poisson with various covariate structures on λ₃, zero-inflated bivariate, and four diagonal-inflated variants). Values in bold indicate the best-fitted model. Footnotes: "†H₀ : λ₃ = 0." / "‡H₀ : λ₃ = constant." / "§H₀ : p = 0." / "§§Best-fitted model." / "*H₀ : θ₂ = 0." / "**H₀ : θ₃ = 0." Each footnote symbol appears as a superscript in the corresponding table cell.

**Table structure from Karlis & Ntzoufras 2003, Table 3 (coefficient table):**

Columns: Team | Results for model 1, double Poisson: Attack, Defence | Results for model 2, bivariate Poisson: Attack, Defence

Rows: 18 named teams (Milan, Juventus, Torino, ..., Ascoli), then a section break, then "Other parameters" rows: Intercept μ, Home team effect, λ₃, Mixing proportion, θ₁.

Footnote: "†Expected number of goals can be calculated by using equations (7) and (6) for model 1 and equations (8) and (6) for model 2."

**Table structure from Foulley 2021, Table 2 (calibration logistic regression):**

Columns: Category | Criterion | Estimation | SE | T-Statistics | DF | P-value

Rows: For each of three match outcomes (Home Win, Draw, Away Win), three rows: intercept, slope, D0 vs D1 (a deviance test). Results provided separately for two forecasting procedures (A: Poisson model, B: Bookmaker odds). The table includes both regression coefficients and their standard errors in adjacent columns — standard errors are never omitted.

**Table structure from Michels et al. 2023, Table 2 (model comparison by AIC):**

Eleven models in rows; four football leagues in columns. Bold marks the minimum AIC in each column. No significance stars — model selection is by information criterion, not hypothesis testing.

Key features present in all tables surveyed: column headers that include the units or interpretation of the numbers; footnotes that define symbols; explicit identification of the preferred or best-fitting model; and alignment that allows rapid column-wise comparison.

**Apply this as:** A coefficient table for the forecasting model should have columns for at minimum: Parameter name, Estimate, Standard Error, and (if applicable) 95% CI or p-value. Team-level parameters should be rows; model-level parameters (home effect, intercept) should appear at the bottom of the same table in a clearly separated "Other parameters" section. Table footnotes should explain every non-obvious symbol and state what each p-value tests. Do not use significance stars as the sole indicator of precision — include standard errors.

---

## 6. Limitations and Future Work Sections

In every paper, limitations are folded into the discussion section as continuous prose. No paper has a dedicated "Limitations" heading with bullets beneath it. The Michels et al. paper ends with a Discussion section whose final two paragraphs address future extensions; the Constantinou & Fenton paper ends with "Implications and Conclusions" whose three paragraphs each develop a distinct argument about the study's scope. The Wisdom of Crowds paper has a "Final remarks" section of four paragraphs, each addressing a different facet of the findings.

Authors hedge selectively. When a claim is empirically established in the paper, it is stated directly. When a claim extends beyond the data, "may", "could", and "might" appear — but sparingly, one hedge per sentence at most.

**Example 1 — future extensions written as connected prose, not bullets:**

> "For future research, our models could be extended to model one or multiple parameters via such covariates. In the presence of many covariates, regularisation approaches have proven helpful when predicting football results (van der Wurp et al., 2020). Moreover, as teams' performance may not be constant over time, a further model extension could include recent performance in a weighted manner by putting more weight on more recent observations — Dixon and Coles (1997) used a similar approach. As a team's form is usually not observable, the models presented here could also be extended by adding a latent state process. In particular, parameters such as the mean may depend on a team's underlying latent form. As the existing literature has already considered state-switching approaches in football (Otting et al., 2021), such extensions could build upon the modelling framework developed in this contribution to flexibly model football scores, especially for women's football."

*Michels, Otting & Karlis 2023, §4*

Note the structure: each extension is introduced, an existing work that motivates it is cited, and the connection to the current paper's framework is made. There is no bulleted list of future directions.

**Example 2 — scope limitation stated directly, not hedged:**

> "We have shown that, by failing to recognise that football outcomes are on an ordinal scale, all of the various scoring rules that have previously been used to assess the forecast accuracy of football models are inadequate. They fail to correctly determine the more accurate forecast in circumstances illustrated by the benchmark scenarios of Table 1. This failure raises serious concerns about the validity and conclusions from previous studies that have evaluated football forecasting models."

*Constantinou & Fenton 2012, §4*

**Example 3 — limitation on sample size treated analytically:**

> "Our simulations revealed that a tournament with 64 matches, like the WTC, is not sufficient to identify the best forecasters since the observed performance of any given participant might be due to randomness. Thus, longer tournaments such as the English Premier League, which has 380 matches every season, may yield further insights on which aggregation strategies work best."

*Inácio et al. 2020, §4*

**Apply this as:** Convert any bulleted limitations section into two or three short paragraphs. Each paragraph should identify one limitation, explain why it arises in the context of this paper (not just assert that it is a known problem), and — where possible — point to the specific condition under which it would not apply or to a direction that would address it. The word "limitation" need not appear as a heading or even in the text; the discussion can proceed directly.

---

## 7. Language Register and Sentence Structure

Sentence length in these papers is variable within paragraphs. Papers typically open a paragraph with a clear declarative sentence of moderate length (one main clause, sometimes one subordinate clause), develop the argument through longer sentences with coordinating or subordinating conjunctions, and close with a short, forceful sentence that states the inference. This rhythm prevents both the monotony of uniformly short sentences and the difficulty of uniformly long ones.

Passive voice is used throughout the literature but alternates with active constructions. The passive tends to appear when the process or result is foregrounded rather than the actor ("The bivariate Poisson model introduces correlation between the variables, but the marginal distributions are still Poisson"); active constructions appear when authorial agency matters ("We adopt a simpler structure for the parameters"). First-person plural is standard in multi-author papers.

Paragraph transitions are handled by logical connectors that make the argumentative relationship explicit: "As a consequence...", "Moreover...", "In contrast...", "It follows that...", "Although...", "Interestingly...". Transitions by re-statement ("As we noted above...") are rare. The topic sentence of each paragraph typically signals the argumentative move, not just the subject matter.

**Example 1 — clear declarative opening, development, and closing inference:**

> "Measuring the accuracy of any forecasting model is a critical part of its validation. In the absence of an agreed and appropriate type of scoring rule it might be difficult to reach a consensus about: a) whether a particular model is sufficiently accurate; and b) which of two or more competing models is 'best'. In this paper, the fundamental concern is the inappropriate assessment of forecast accuracy in association football, which may lead in inconsistencies, whereby one scoring rule might conclude that model α is more accurate than model β, whereas another may conclude the opposite. In such situations the selection of the scoring rule can be as important as the development of the forecasting model itself, since the score generated practically judges the performance of that model."

*Constantinou & Fenton 2012, §4*

**Example 2 — active voice establishing a claim with embedded precision:**

> "The crucial observation we make about football forecasting is that the set of outcomes {H, D, A} must be considered as an ordinal scale and not a nominal scale. The outcome D is closer to H than A is to H; if the home team is leading by a single goal then it requires only one goal by the away team to move from H to D."

*Constantinou & Fenton 2012, §1*

**Example 3 — opening a section with a rhetorical question from the literature that is immediately answered (a rare but effective technique):**

> "If competitive equilibrium is defined as a situation in which prices are such that all arbitrage profits are eliminated, is it possible that a competitive economy always be in equilibrium? Clearly not, for then those who arbitrage make no (private) return from their (privately) costly activity."

*Grossman & Stiglitz 1980, §I*

**Example 4 — transitioning between paragraphs with explicit logical connector:**

> "Although we have implemented our proposed models in various data sets, here we focus on the Italian serie A data for the 1991–1992 season and give some brief details for the Champions League data for the 2000–2001 season."

*Karlis & Ntzoufras 2003, §4.1*

**Apply this as:** Revise any sequence of sentences that all begin with "The model..." or "This approach..." or "We..." — that uniformity signals a draft that was generated sentence-by-sentence. Read each paragraph aloud: if it sounds like a list of facts rather than an argument developing through a paragraph, add the logical connectors ("although", "as a consequence", "in contrast", "it follows that") that make the reasoning visible. Aim for sentence-length variation: short declaratives to state conclusions, medium sentences to elaborate, one long sentence per paragraph at most to handle qualifications.

---

## 8. What Real Papers Do That AI-Drafted Text Typically Omits

The most consistent gap between the papers surveyed and typical AI-generated academic prose concerns the treatment of numbers, the use of model-comparison logic, and the absence of structural tics.

Real papers name the quantity before they give the number. "The estimated home effect is 0.36" is more typical than "0.36 is the estimated home effect". When multiple models are compared, real papers use information criteria (AIC, BIC) as the primary decision rule, report the values for multiple competing models in a table, and then interpret the comparison in a sentence that says what the difference implies. AI drafts often report AIC for only the chosen model, without comparison.

Real papers refer back to specific figures, tables, and equations by number throughout the text: "as shown in Table 3", "equation (6)", "see Figure 1". This cross-referencing is relentless and functional — it guides the reader and signals that the text and the figures are integrated. AI drafts tend to mention tables only once (when first introduced) and then proceed as if the reader has absorbed their contents.

Real papers do not repeat the outline of the paper at the end of sections. The Karlis & Ntzoufras introduction says "The remainder of the paper proceeds as follows. Firstly, in Section 2... In Section 3, extensions through inflated models are proposed. Since a draw is represented by diagonal terms in a bivariate distribution, adding an inflation term on the diagonal allows for more precise modelling of the number of draws. In Section 4, the models proposed are illustrated..." — a road-map paragraph that is present only once in the introduction, not summarised again at the end of each section.

Real papers on sports forecasting never use bold to draw attention to "key takeaways". The absence of bold in the prose is universal among journal-published papers in this sample; the presence of bold in an AI draft almost always signals that emphasis is being substituted for argument.

Real papers do not begin conclusion paragraphs with "In conclusion," or "To summarise,". The Michels et al. conclusion paragraph begins "There is wide interest in predicting football matches by fans, media, and academics." The Constantinou & Fenton conclusion begins "Measuring the accuracy of any forecasting model is a critical part of its validation." The transition into conclusion material is made by the argument's logic, not by a signposting phrase.

Real papers write model motivation in terms of data patterns, not generic desiderata. Karlis & Ntzoufras motivate the bivariate Poisson model by first showing that the independent Poisson misspecifies the draw probability by up to 14% even at modest covariance — a specific empirical fact. Michels et al. motivate the negative binomial marginals by showing that for Germany, France, and Spain the mean-variance scatter plots show systematic overdispersion in the team-level data. The motivation is diagnostic before it is prescriptive.

Finally, real limitation paragraphs in this literature do not hedge uniformly with "may" and "could" and "might". These modals appear only where genuine uncertainty exists — about future results, untested extensions, or phenomena outside the study's scope. Claims that are established by the paper's own analysis are stated directly, without hedging. A paper that says "our results may suggest that..." when it has just reported p < 0.01 is performing false modesty, not scientific caution.

---

*These notes were compiled by reading the following papers in full: Constantinou & Fenton (2012), Karlis & Ntzoufras (2003), Michels, Otting & Karlis (2023), Foulley (2021), Inácio et al. (2020), Grossman & Stiglitz (1980), Callaway & Sant'Anna (2021), and Breiman (2001). Page images of the originals were examined; all excerpts above are quoted from those images.*

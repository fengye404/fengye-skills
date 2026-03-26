# Autoresearch Changelog — fengye-blog-style

**Target:** `fengye-blog-style-0.0.2.md`
**Baseline:** `SKILL.md.baseline` (= fengye-blog-style 0.0.1)
**Evals:** E1-开头无套话, E2-无反模式, E3-语气硬无模糊词, E4-具体工程名词, E5-无重复解释
**Runs per experiment:** 5
**Max score:** 25

---

## Experiment 0 — baseline

**Score:** 20/25 (80.0%)
**Change:** None — original skill as-is
**Reasoning:** Establish baseline performance before any mutations
**Result:** E1 (5/5), E2 (3/5), E3 (3/5), E4 (5/5), E5 (5/5). Main weaknesses are E2 (anti-patterns like "不是...而是..." and "换句话说" still appear) and E3 (hedge words like "在某种程度上" and "可能是因为" creep in).
**Failing outputs:** Run 1 used "不在...而在..."; Run 3 used "换句话说" and "在某种程度上"; Run 5 used "不是...而是..." and "可能是因为"

---

## Experiment 1 — keep

**Score:** 25/25 (100.0%)
**Change:** Strengthened anti-pattern section — replaced soft "尽量避免" with hard "绝对禁止", added specific correct/incorrect examples, added hedge words (在某种程度上, 或许, 可能是因为) to explicit ban list
**Reasoning:** Baseline failures were concentrated in E2 (anti-patterns) and E3 (hedge words). The original skill said "尽量避免", which leaves room for the model to justify using these patterns. Making them absolute prohibitions with examples should eliminate ambiguity.
**Result:** All 5 evals passed in all 5 runs. Score jumped from 80% to 100%.
**Failing outputs:** None

---

## Experiment 2 — keep (verification)

**Score:** 25/25 (100.0%)
**Change:** None — verification run with same skill as experiment 1
**Reasoning:** Need to confirm the 100% score is stable, not a fluke. Ran the same skill 5 more times with varied scenarios.
**Result:** All 5 evals passed in all 5 runs. Score held at 100%. Consecutive 95%+ runs: 2/3.
**Failing outputs:** None

---

## Experiment 3 — keep (final verification)

**Score:** 25/25 (100.0%)
**Change:** None — third consecutive verification run
**Reasoning:** Need 3 consecutive 95%+ to confirm diminishing returns and trigger stop condition
**Result:** All 5 evals passed in all 5 runs. Consecutive 95%+ runs: 3/3. **STOP CONDITION MET.**
**Failing outputs:** None

---

## Round 1 Summary

- **Baseline:** 20/25 (80.0%) → **Final:** 25/25 (100.0%)
- **Improvement:** +20 percentage points
- **Total experiments:** 4 (1 baseline + 1 mutation + 2 verifications)
- **Mutations tried:** 1
- **Keep rate:** 1/1 (100%)
- **Key change:** Strengthened anti-pattern prohibitions from soft "尽量避免" to hard "绝对禁止" with specific examples and alternatives, plus explicit ban on hedge words

---

# Round 2 — Expanded Eval Suite

**New evals added:** E6-真实场景开头, E7-无AI过渡句, E8-有第一人称工程叙事
**Evals:** E1-开头无套话, E2-无反模式, E3-语气硬无模糊词, E4-具体工程名词, E5-无重复解释, E6-真实场景开头, E7-无AI过渡句, E8-有第一人称工程叙事
**Runs per experiment:** 5
**Max score:** 40

---

## Experiment 4 — baseline-r2

**Score:** 28/40 (70.0%)
**Change:** None — same 0.0.2 skill, but now scored against 8 evals instead of 5
**Reasoning:** Round 1 hit 100% on E1-E5 but those evals don't capture deeper style issues. Added E6 (real-scenario openings), E7 (no AI transitions), E8 (first-person voice) based on analysis of reference blogs.
**Result:** E1-E5 all 5/5 (Round 1 gains held). E6=0/5, E7=3/5, E8=0/5. The skill produces correct but soulless output — reads like documentation, not a personal blog.
**Failing pattern:** Skill's "先定义主题" instruction actively pushes model toward abstract openings. No instruction exists for first-person perspective.

---

## Experiment 5 — keep

**Score:** 40/40 (100.0%)
**Change:** Three-part mutation: (1) Added "视角与语气" section requiring first-person engineering narratives; (2) Rewrote "引言" from "先定义主题" to "从真实场景切入" with examples and explicit ban on abstract openings; (3) Expanded anti-pattern list with AI transition phrases (值得注意的是, 需要指出的是, 更重要的是, etc.)
**Reasoning:** E6 (0/5) and E8 (0/5) share a root cause: skill steers model toward documentation-style writing. Adding persona/voice instructions and scene-based opening requirements should fix both simultaneously. E7 (3/5) needs more banned phrases.
**Result:** All 8 evals passed in all 5 runs. Score jumped from 70% to 100%. Consecutive 95%+ runs: 1/3.
**Failing outputs:** None

---

## Experiment 6 — keep (verification)

**Score:** 40/40 (100.0%)
**Change:** None — verification run with same skill as experiment 5
**Reasoning:** Need to confirm 100% is stable. Consecutive 95%+ runs: 2/3.
**Result:** All 8 evals passed in all 5 runs.
**Failing outputs:** None

---

## Experiment 7 — keep (final verification)

**Score:** 40/40 (100.0%)
**Change:** None — third consecutive verification run
**Reasoning:** Need 3 consecutive 95%+ to trigger stop condition for Round 2.
**Result:** All 8 evals passed in all 5 runs. Consecutive 95%+ runs: 3/3. **STOP CONDITION MET.**
**Failing outputs:** None

---

## Round 2 Summary

- **Baseline (R2):** 28/40 (70.0%) → **Final:** 40/40 (100.0%)
- **Improvement:** +30 percentage points
- **Total experiments (R2):** 4 (1 baseline + 1 mutation + 2 verifications)
- **Mutations tried:** 1
- **Keep rate:** 1/1 (100%)
- **Key changes:**
  1. Added "视角与语气" section — requires first-person engineering narratives
  2. Rewrote "引言" section — changed from "先定义主题" to "从真实场景切入" with examples and explicit ban on abstract openings
  3. Expanded anti-pattern ban list with AI transition phrases (值得注意的是, 需要指出的是, 更重要的是, etc.)

## Overall Summary (Round 1 + Round 2)

- **Original baseline (R1):** 20/25 (80.0%) on 5 evals
- **After Round 1:** 25/25 (100.0%) on 5 evals — strengthened anti-patterns
- **After Round 2 (expanded to 8 evals):** 40/40 (100.0%) on 8 evals — added persona, opening style, AI transition ban
- **Total experiments across both rounds:** 8
- **Total mutations applied:** 2 (both kept)
- **Key improvements to skill:**
  1. Anti-patterns changed from soft "尽量避免" to hard "绝对禁止" with ❌→✅ examples
  2. Hedge words explicitly banned (在某种程度上, 或许, 可能是因为, 某种意义上说)
  3. AI transition phrases banned (值得注意的是, 更重要的是, etc.)
  4. First-person perspective required (not documentation-style)
  5. Opening must start from real engineering scenario (not abstract concept)


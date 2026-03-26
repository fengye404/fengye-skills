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

## Final Summary

- **Baseline:** 20/25 (80.0%) → **Final:** 25/25 (100.0%)
- **Improvement:** +20 percentage points
- **Total experiments:** 4 (1 baseline + 1 mutation + 2 verifications)
- **Mutations tried:** 1
- **Keep rate:** 1/1 (100%)
- **Key change:** Strengthened anti-pattern prohibitions from soft "尽量避免" to hard "绝对禁止" with specific examples and alternatives, plus explicit ban on hedge words


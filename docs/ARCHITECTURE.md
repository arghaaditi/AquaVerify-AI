# AquaVerify Architecture

## Runtime path

```text
Streamlit form
   ↓
validate_observation()
   ↓
evaluate_rules()
   ↓
analyze_conditional_rarity()
   ↓
analyze_novelty()
   ├─ Isolation Forest
   └─ One-Class SVM
   ↓
analyze_concern_indicators()
   ↓
build_explanation()
   ↓
Human decision
   ↓
SQLite audit trail
   ↓
Researcher dashboard
```

## Separation of responsibilities

### Basic validation
Checks required fields and allowed categories. ML is not run on invalid/incomplete input.

### Consistency rules
Encodes known review-worthy conflicts with traceable explanations.

### Conditional rarity
Compares field values with the reference distribution within the same overall-assessment group.

### Novelty models
Evaluate the detailed 14-field pattern. The citizen's overall summary is excluded from the ML feature set to reduce shortcut learning from the synthetic generator.

### Concern indicators
Surface reported environmental pressure/context evidence for researcher triage. They do not diagnose pollution or safety.

### Explanation layer
Assembles structured evidence from rules, statistics, ML, and concern indicators. It can operate without an LLM.

### Human review
The citizen can edit or keep answers. No automatic overwrite occurs.

### Persistence
SQLite stores original/final observations, original/final analysis evidence, human decision, and researcher review state.

## Why a hybrid system?

Each mechanism solves a different failure mode:

- **Rules:** known, explainable conflicts.
- **Reference statistics:** uncommon assessment-conditioned values.
- **ML novelty:** multivariate patterns not explicitly encoded as rules.
- **Human review:** context and final judgment.

The system therefore avoids presenting one model as an all-purpose ecological truth engine.

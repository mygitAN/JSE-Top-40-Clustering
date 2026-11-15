# Cluster and constituent explanation evidence

All numbers come from one completed saved run. No fits, SHAP evaluations or metric
recalculations. Cluster ids in histories are aligned; raw ids in scatter maps are
local to a date. Always identify model, date and label basis when describing a move.

- cluster_definitions.csv: members and top defining features per aligned cluster/date.
- cluster_feature_profiles.csv: every feature median/deviation, mean signed/absolute SHAP and fidelity.
- member_feature_shap.csv: every constituent/feature, raw/scaled value, signed own-class SHAP and both label ids.
- cluster_membership_changes.csv: retained members, arrivals/departures from other clusters, index entries/exits.
- cluster_profile_changes.csv: profile changes; combines changing inputs and changing membership composition.
- constituent_transitions.csv: every continuing constituent, including stable names, with raw and aligned ids.
- constituent_feature_changes.csv: numeric changes and leave-one-out peer references for every feature.
- agent_evidence.csv: long feature table joined to the transition summary for machine-assisted writing.

SHAP values are raw-margin contributions from a different surrogate at each date.
Do not subtract before/after SHAP as a temporal causal effect. The same-date destination
minus source SHAP is a class contrast in the AFTER surrogate; it is undefined when the
old aligned class disappeared. Leave-one-out peer medians are undefined for empty sets.
OOF fidelity measures reproduction of cluster labels, not financial validity.
Cluster changes can reflect fitting variability, membership composition and input
changes. A raw label change alone is not a peer-group move. No causal claim is established.

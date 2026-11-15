"""Build the experiment report and scientific plot from saved numerical outputs.

The pair-category and named-group breakdowns are post-hoc descriptive diagnostics,
kept separate from the protocol's primary company-balanced estimands.
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from run import HERE, ROOT, residualise, return_panel, sha


def diagnostic_tables():
    prices = pd.read_csv(HERE / 'data/prices.csv', parse_dates=['date'])
    cohorts = pd.read_csv(HERE / 'data/cohorts.csv')
    protocol = json.loads((HERE / 'protocol.json').read_text())
    rows = []
    for formation, (start, end) in zip(protocol['formation_dates'], protocol['evaluation_windows']):
        c = cohorts[cohorts.decision_date == formation].sort_values('ticker').reset_index(drop=True)
        x, market, _ = return_panel(prices, c.ticker, formation, start, end, 'close')
        eligible = np.triu(c.economic_group.to_numpy()[:, None] != c.economic_group.to_numpy(), 1)
        cluster = c.cluster.to_numpy()[:, None] == c.cluster.to_numpy()
        sector = c.sector_label.to_numpy()[:, None] == c.sector_label.to_numpy()
        for basis, returns in [('price', x), ('J200_residual_price', residualise(x, market))]:
            corr = np.corrcoef(returns, rowvar=False)
            masks = {'all_cluster_pairs': eligible & cluster, 'all_sector_pairs': eligible & sector,
                     'same_cluster_same_sector': eligible & cluster & sector,
                     'same_cluster_different_sector': eligible & cluster & ~sector,
                     'different_cluster_same_sector': eligible & ~cluster & sector,
                     'different_cluster_different_sector': eligible & ~cluster & ~sector}
            for label in sorted(c.cluster.unique()):
                masks[f'aligned_cluster_{label}'] = eligible & cluster & (c.cluster.to_numpy()[:, None] == label)
            for name, mask in masks.items():
                rows.append(dict(formation_date=formation, return_basis=basis, diagnostic=name,
                                 pairs=int(mask.sum()), mean_pair_correlation=float(corr[mask].mean()) if mask.any() else None))
    result = pd.DataFrame(rows)
    result.to_csv(HERE / 'results/descriptive_pair_diagnostics.csv', index=False)
    return result


def plot(intervals):
    selected = intervals[(intervals.variant == 'adjusted') & (intervals.block_length == 10)]
    fig, ax = plt.subplots(figsize=(9, 4.9))
    labels = [('sector_delta', 'Same-sector peers'), ('matched_delta', 'Matched cross-cluster peers'),
              ('cross_cluster_delta', 'All cross-cluster peers')]
    for date, shift, colour, label in [('2025-06-30', .11, '#28658b', 'Jul–Dec 2025'),
                                       ('2025-12-31', -.11, '#b2603d', 'Jan–Jun 2026')]:
        for i, (metric, _) in enumerate(labels):
            row = selected[(selected.formation_date == date) & (selected.metric == metric)].iloc[0]
            ax.errorbar(row.estimate, i + shift,
                        xerr=[[row.estimate - row.lower_95], [row.upper_95 - row.estimate]],
                        fmt='o', color=colour, capsize=4, label=label if i == 0 else None)
    ax.axvline(0, color='#555555', linewidth=.9)
    ax.set_yticks(range(len(labels)), [label for _, label in labels])
    ax.invert_yaxis()
    ax.set_xlabel('Financial-peer correlation minus comparator correlation')
    ax.set_title('Frozen financial peers and subsequent return co-movement', loc='left', fontsize=12, weight='bold', pad=30)
    ax.text(0, 1.045, 'Company-balanced differences; adjusted-close returns; 95% conditional 10-day block intervals',
            transform=ax.transAxes, fontsize=8.5)
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.grid(axis='x', alpha=.18)
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(.02, .025, 'Intervals condition on the observed firms, frozen labels and two windows. They do not establish performance in other periods.', fontsize=8)
    fig.tight_layout(rect=(0, .055, 1, 1))
    fig.savefig(HERE / 'results/forward_comovement.png', dpi=190)
    plt.close(fig)


def main():
    out = HERE / 'results'
    summaries = pd.read_csv(out / 'summary.csv')
    intervals = pd.read_csv(out / 'conditional_block_intervals.csv')
    deletions = pd.read_csv(out / 'delete_company.csv')
    diagnostics = diagnostic_tables()
    plot(intervals)
    primary = summaries[summaries.variant == 'adjusted']
    names = {'sector': 'Same-sector peers', 'matched': 'Matched cross-cluster peers',
             'cross_cluster': 'All cross-cluster peers'}
    lines = [
        '# Frozen financial peers: forward co-movement experiment', '',
        'The frozen UMAP financial peers co-move more than cross-cluster alternatives, including '
        'sector-and-formation-characteristic-matched alternatives. They co-move **less than same-sector '
        'peers in both six-month windows**. The proposed claim of stronger subsequent co-movement '
        'than conventional sectors is not supported by this experiment.', '',
        'This is a separate company-balanced experiment and does not write to the manuscript or '
        'the original numerical archive. Parallel commits have added a pair-weighted analysis to '
        'the paper. Those estimates and the company-balanced estimates here answer differently '
        'weighted questions and should not be spliced together.', '',
        '![Forward co-movement comparison](results/forward_comovement.png)', '',
        '## Design and scope', '',
        '- Frozen source run: `20261115T062631-0c09819ce3c0`, representative seed 42. '
        'Manuscript baseline: commit `7a860a0`. No refitting, feature selection or parameter tuning uses forward returns.',
        '- Formation 30 June 2025 is evaluated on 1 July–31 December 2025; formation 31 December 2025 '
        'on 1 January–30 June 2026. The return from the formation close to the first evaluation close is included.',
        '- All 41 formation-date instruments are retained, even if they subsequently leave the index. '
        'No future membership filter is applied. Coverage is 128 and 123 trading-day returns, respectively.',
        '- INL and INP receive one combined focal-company weight. Their mutual pair is excluded. '
        'Other companies receive equal weight, rather than giving large clusters weight proportional to their number of pairs.',
        '- The primary comparison is within-cluster versus same-sector mean correlations for the same eligible '
        'focal companies. Sector pairs may also be cluster pairs. Missing peer sets are reported as ineligible, not assigned zero correlation.',
        '- Matched alternatives keep the focal instrument fixed and match each cluster peer to a different-cluster '
        'instrument in the same recorded sector, nearest in formation-standardised log line market capitalisation '
        'and annualised volatility. Matching is with replacement and uses no forward outcomes. Each company’s '
        'matched contrast uses only its successfully matched targets.',
        '- Primary returns use Yahoo adjusted closes. Vendor close price returns and J200-residual adjusted '
        'returns are sensitivities. The close-price series may already incorporate vendor split adjustments; '
        'it is not a reconstructed raw transaction-price history.',
        '- The protocol was recorded before this experiment ran, but after the wider study and a beta audit. '
        'It is a retrospective analysis protocol, not a prospective preregistration.', '',
        '## Primary estimates', '',
        'Positive differences favour financial peers. Levels are company-balanced arithmetic means of '
        'Pearson correlations for the eligible companies in that comparison; different comparisons may '
        'have different coverage. Intervals are conditional return-panel resampling intervals, not an '
        'independent-pair significance test.', '',
        '| Formation | Comparator | Eligible companies | Cluster mean | Comparator mean | Difference | 95% conditional interval |',
        '|---|---|---:|---:|---:|---:|---|',
    ]
    for row in primary.itertuples():
        for metric in ['sector', 'matched', 'cross_cluster']:
            ci = intervals[(intervals.formation_date == row.formation_date) &
                           (intervals.variant == 'adjusted') & (intervals.block_length == 10) &
                           (intervals.metric == metric + '_delta')].iloc[0]
            lines.append(f'| {row.formation_date} | {names[metric]} | {getattr(row, metric + "_eligible_groups")} '
                         f'| {getattr(row, metric + "_cluster"):.3f} | {getattr(row, metric + "_baseline"):.3f} '
                         f'| {ci.estimate:+.3f} | [{ci.lower_95:+.3f}, {ci.upper_95:+.3f}] |')
    lines += ['', '## Dependence, uncertainty and sensitivity', '',
              'Each date uses 2,000 synchronous circular moving-block resamples at block lengths of 5, '
              '10 and 20 trading days. All companies share each resampled calendar, preserving common '
              'cross-sectional shocks. The displayed intervals use 10 days. These intervals condition '
              'on the observed corporate universe and fitted groups; two windows do not establish '
              'a sampling distribution across market regimes. Company-level contrasts and deletion '
              'sensitivity accompany the intervals; no test treats the many overlapping equity pairs '
              'as independent observations.', '',
              'High-volatility exclusions use only the formation-date 90th-percentile threshold, '
              'not realised forward volatility. Market residuals remove a same-window intercept and '
              'J200 slope; these are a correlation diagnostic, not a tradable hedging strategy.', '',
              '| Formation | Return/coverage sensitivity | Sector difference | Matched difference |',
              '|---|---|---:|---:|']
    for row in summaries.itertuples():
        lines.append(f'| {row.formation_date} | {row.variant} | {row.sector_delta:+.3f} | {row.matched_delta:+.3f} |')
    lines += ['', '| Formation | Delete-one-company sector range | Delete-one-company matched range |',
              '|---|---|---|']
    for date, sub in deletions[deletions.variant == 'adjusted'].groupby('formation_date'):
        lines.append(f'| {date} | [{sub.sector_delta.min():+.3f}, {sub.sector_delta.max():+.3f}] '
                     f'| [{sub.matched_delta.min():+.3f}, {sub.matched_delta.max():+.3f}] |')
    lines += ['', 'The sector contrast remains negative and the matched contrast positive after deleting '
              'any single economic company. The output interval table supplies every block-length '
              'and sensitivity result, including results not displayed here.', '',
              '## Matching coverage', '',
              '| Formation | Matched directed targets | Unmatched targets | Mean / maximum matching distance | Distinct alternatives reused |',
              '|---|---:|---:|---|---:|']
    for row in primary.itertuples():
        lines.append(f'| {row.formation_date} | {row.matched_targets} | {row.unmatched_targets} '
                     f'| {row.mean_match_distance:.3f} / {row.max_match_distance:.3f} | {row.unique_matched_alternatives} |')
    lines += ['', 'Distances are Euclidean in the two standardised formation attributes. Exact sector '
              'matching is not possible for every directed target. The matched estimates apply only '
              'to the successfully matched subset and do not establish an advantage over sectors. '
              'Repeated alternatives and imperfect characteristic balance constrain interpretation; '
              '`matched_pairs.csv` records every selection and its distance.', '',
              '## Descriptive diagnostics added after the primary run', '',
              'These pair-weighted breakdowns explain the result and are exploratory rather than additional '
              'confirmatory hypothesis tests. They retain the same frozen groups and exclude the Investec mutual pair. '
              'They use vendor close price returns for comparability with the parallel pair-weighted draft.', '',
              '| Formation | Pair-weighted cluster minus sector | Precious-metals group (C3) | Scale/turnover group (C4) |',
              '|---|---:|---:|---:|']
    for date, sub in diagnostics[diagnostics.return_basis == 'price'].groupby('formation_date'):
        d = sub.set_index('diagnostic').mean_pair_correlation
        lines.append(f'| {date} | {d.all_cluster_pairs - d.all_sector_pairs:+.3f} '
                     f'| {d["aligned_cluster_3"]:.3f} | {d["aligned_cluster_4"]:.3f} |')
    lines += ['', 'The precious-metals group exhibits much stronger subsequent co-movement than the '
              'scale/turnover group. Similarity in measured financial characteristics therefore does '
              'not uniformly translate into common subsequent return behaviour. Pair-weighted sector '
              'differences reproduce the direction and values in the separate `research/comovement/` '
              'draft. That draft and this company-balanced analysis use different estimands; their '
              'point estimates should not be mixed. No outputs from that draft are dependencies of this experiment.', '',
              '## Beta input audit', '',
              'The existing `validation/audit_beta.py` was rerun against the cached daily series: all '
              '123 workbook beta values agree with the independently coded J203 recalculation within '
              '0.023 (median absolute difference 0.002). Sasol’s J200 slopes are approximately +1.015 '
              'for July–December 2025 and −0.736 for January–June 2026. This does not justify a beta '
              'correction or a study rerun on its own. It is same-vendor replication, not independent '
              'exchange-price certification. The audit removes returns above 40%, including the two '
              'corrupt J203 observations; the forward experiment uses J200 only for its residual sensitivity '
              'and found no such moves in its constituent/J200 evaluation data, so it trims none.', '',
              'A market-capitalisation-weighted beta near one is not a sufficient diagnostic here: '
              'the Top 40 is a subset of J203 and the input capitalisations do not constitute J203’s '
              'actual investable benchmark weights. No rand-hedge explanation has been inferred from '
              'this audit alone.', '',
              '## Implications and next research decision', '',
              'The proposed test does not support replacing sector peers with UMAP financial peers '
              'for stronger subsequent co-movement. The positive matched contrasts and the '
              'precious-metals diagnostic support further investigation of financial groups as '
              'complements, but not a uniform investment-benefit claim. No portfolio return, risk '
              'reduction, causal effect or superiority over another embedding has been established.', '',
              'IAJ remains the intended finance audience, with ORiON as a methodological fallback; '
              'journal scope alone cannot determine acceptance. Current publisher sources emphasise '
              'finance/investment research and replicability for IAJ, and OR case studies for ORiON. '
              'No unverified manuscript-length requirement has been applied. '
              '[IAJ publisher information](https://www.tandfonline.com/journals/riaj20/about-this-journal); '
              '[ORiON submissions](https://orion.journals.ac.za/index.php/pub/about/submissions).', '',
              'This experiment retains the study data and labels associated with its frozen baseline. '
              'Manuscript changes made in parallel need to be assessed using their own stated estimator. '
              'Expanding to seven cross-sections '
              'requires four additional dated input universes and issuer fundamentals; none has been '
              'invented or added here. The June 2026 six-month window ends on 31 December 2026 '
              'and is incomplete as of this November analysis. A later evaluation would be held out '
              'from this experiment, but the entire July–December window cannot honestly be called '
              'prospectively preregistered in November. In particular, the parallel manuscript wording '
              'that calls this the first fully prospective/pre-specified evaluation needs to distinguish '
              'an unexamined held-out window from a window that begins after the protocol is fixed.', '',
              '## Reproduce and inspect', '',
              '```powershell',
              '.venv/Scripts/python.exe validation/forward_comovement/run.py',
              '.venv/Scripts/python.exe validation/forward_comovement/make_report.py',
              '.venv/Scripts/python.exe -m unittest tests.test_forward_comovement -v',
              '```', '',
              'The committed price/cohort snapshots permit reruns without network access or the '
              'local study archive. `protocol.json`, `data/manifest.json` and `results/manifest.json` '
              'bind the protocol, vendor-cache provenance, frozen snapshots, script and numerical '
              'outputs by SHA-256. Initial preparation used the pre-existing Yahoo cache. Prices are '
              'retrospective vendor-adjusted observations, and formation inputs and legacy sectors '
              'retain the original study’s measurement and point-in-time limitations.', '',
              'Verification in this session: nine focused design tests and the full 68-test suite passed. '
              'An independently written direct company-average calculation reproduced both primary '
              'sector contrasts. The full suite needed the normal filesystem context because the '
              'sandbox prevented existing tests from writing to their temporary directories.', '',
              'Core outputs: `summary.csv`, `conditional_block_intervals.csv`, `company_contrasts.csv`, '
              '`delete_company.csv`, `matched_pairs.csv`, `coverage.csv`. The report-builder’s '
              '`descriptive_pair_diagnostics.csv` is explicitly post-hoc.']
    (HERE / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    record = {'analysis_manifest_sha256': sha(out / 'manifest.json'), 'report_script_sha256': sha(__file__),
              'report_sha256': sha(HERE / 'README.md'),
              'diagnostics_sha256': sha(out / 'descriptive_pair_diagnostics.csv'),
              'figure_sha256': sha(out / 'forward_comovement.png')}
    (out / 'report_manifest.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()

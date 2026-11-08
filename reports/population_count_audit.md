# Population count: 40 groups and 41 instruments

The revised paper retains an **instrument-level** analysis. At each study date,
the supplied data contain 41 distinct securities representing 40 economic groups
when Investec Limited (INL) and Investec plc (INP) are mapped to one Investec DLC
group. The user confirmed this interpretation on 8 November 2026. Neither line
is removed or averaged, and the existing numerical model results are unchanged.
The two securities must not be described as independent companies.

| Snapshot | Listed instruments | Economic groups | Investec lines |
| --- | ---: | ---: | --- |
| 2025-06-30 | 41 | 40 | INL, INP |
| 2025-12-31 | 41 | 40 | INL, INP |
| 2026-06-30 | 41 | 40 | INL, INP |

The [FTSE Russell factsheet dated 31 December 2025](https://research.ftserussell.com/Analytics/FactSheets/temp/6d2fd834-bec7-4529-b91e-a2f70aee27b8.pdf)
describes the index in terms of 40 companies (page 1), and reports 41 constituents
(page 2). This is direct dated evidence that the name does not require exactly
40 instrument rows.
[Investec describes its DLC structure](https://www.investec.com/en_us/welcome-to-investec/about-us/corporate-structure.html).
[FTSE/JSE ground rules, section 4.2](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/ftse-jse-africa-index-series-ground-rules.pdf)
explain separate inclusion/pricing of eligible equity lines and treatment of
approved DLC structures as one entity for this purpose. The retrieved rules are
v9.3, September 2026, after the study dates; they explain the mechanism rather
than independently certifying the earlier lists.

## Date-specific membership controls

An instrument's membership at one date does not establish its membership at
another. Returning members are included only after the effective re-entry date.
Reserve-list presence is not actual index membership.

| Change effective | Entry | Exit | Supplied-data check |
| --- | --- | --- | --- |
| 2025-06-23 | NPH | GLN | June snapshot includes NPH and excludes GLN |
| 2025-09-22 | GLN | APN | December snapshot includes GLN and excludes APN |
| 2026-03-23 | PAN | MNP | June 2026 snapshot includes PAN and excludes MNP |

Sources: the [June 2025 official review](https://senspdf.jse.co.za/documents/SENS_20250604_S505822.pdf),
the [September 2025 index-change announcement](https://www.sharenet.co.za/v3/sens_display.php?seq=4&tdate=20250904071500),
and the [March 2026 index-change announcement](https://www.sharenet.co.za/v3/sens_display.php?scode=&seq=61&tdate=20260304173300).
The latter two are issuer/index-provider announcements reproduced by Sharenet.
The supplied presence matrix agrees with these selected controls. The extra
instrument row is explained by the Investec pair, rather than retaining GLN
during its absence in the June 2025 snapshot.

This audit resolves the count interpretation and checks the listed events. It
does not independently certify every constituent at all dates, every intervening
corporate action, or the financial and market inputs. Archived complete dated
lists and the previously identified historical data evidence remain relevant.
The EDA now displays both counts; sector bars and model metrics count instruments.
INL and INP give the Investec group two observations in the security-level
clustering. A one-observation-per-group robustness analysis would be a distinct
experiment with a documented representative/aggregation rule and fresh fits.

The machine-readable audit is [population_count_audit.json](population_count_audit.json).

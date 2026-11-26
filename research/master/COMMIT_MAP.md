# Commit identifier map

On 26 November 2026 the commit messages of this repository were edited to
remove a trailer line. Nothing else changed: every commit keeps its file
contents (tree), author, author date, committer date and subject. Because a
commit identifier covers its message, the edited commits and their descendants
received new identifiers. The 49 commits whose history contained no such
trailer, including `5d5482f` and the `archive/pre-slim-2026-11-14` tag, keep
their original identifiers.

Identifiers recorded inside files before that date (for example in
`protocol.json`, the manifests, the README files and the archive file names)
were left unchanged, because several of those files are checksum-verified
frozen records. Use this table to resolve them. To verify a pair, compare
`git rev-parse <new>^{tree}` with the tree recorded for the old commit: they
are identical.

## Identifiers recorded in files or tag names

| Recorded identifier | Current identifier | Where it is recorded |
|---|---|---|
| `7a860a0` | `3d40967` | frozen manuscript baseline; protocol files, manifests, READMEs, archive file names, tag `research-baseline-20261115-7a860a0` |
| `e1b393a` | `2a6d4df` | research-master source; `research/master` manifest, README and archive file names, tag `research-master-20261115-e1b393a` |
| `85c9137` | `4f1ebaa` | `research/master/README.md` (condensed manuscript) |
| `98549c6` | `4a33492` | results and figure-source manifests (implementation commit of run `20261115T062631-0c09819ce3c0`) |
| `8cf0e7b` | `857369e` | `paper/README.md` |
| `28c2ccf` | `41ee419` | `tmp/paper` scripts |
| `39f929e` | `2d82823` | `reports/cluster_explanations_20261115T064827-f259c77903eb/manifest.json` |
| `4f74e8b` | `a502129` | `reports/cluster_explanations_20261115T072002-06b0c3ed34e9/manifest.json` |

## Tags

| Tag | Previous commit | Current commit |
|---|---|---|
| `protocol-v1` | `a8c7e8c` | `cb95d08` |
| `protocol-v1.1` | `8b6d620` | `9bc7c9d` |
| `protocol-v1.2` | `cd64596` | `3d49b18` |
| `research-baseline-20261115-7a860a0` | `7a860a0` | `3d40967` |
| `research-master-20261115-e1b393a` | `6c2edef` | `9e912b5` |

Tag names, messages and tag dates are unchanged.

## All changed commits

| Previous | Current | Date | Subject |
|---|---|---|---|
| `a014dab` | `854e226` | 2026-11-08 | Add paper notebook: EDA, modelling, plots and SHAP for three cross-sections |
| `4216165` | `75a25f1` | 2026-11-08 | Document how to run the paper notebook |
| `a8c7e8c` | `cb95d08` | 2026-11-08 | Freeze three-snapshot research protocol v1.0 |
| `8b6d620` | `9bc7c9d` | 2026-11-08 | Freeze research protocol v1.1 |
| `cd64596` | `3d49b18` | 2026-11-08 | Freeze research protocol v1.2 |
| `a87ddfd` | `61b64b7` | 2026-11-08 | Rebuild paper notebook to protocol v1.2 and run it as the v1 pilot |
| `b8c5379` | `58068d7` | 2026-11-08 | Draft v1.3 protocol corrections for undefined signals and reproducibility |
| `98549c6` | `4a33492` | 2026-11-15 | Make UMAP with agglomerative clustering the single study model |
| `f5e39ee` | `c2e4072` | 2026-11-15 | Refresh results from the clean UMAP-only run |
| `39f929e` | `2d82823` | 2026-11-15 | Remove report folders from the retired two-model setup |
| `28c2ccf` | `41ee419` | 2026-11-15 | Validate index membership against the published Top 40 reviews |
| `4f74e8b` | `a502129` | 2026-11-15 | Merge pull request #1 from mygitAN:research/reproducible-review |
| `c7edf44` | `8a4cde5` | 2026-11-15 | figures |
| `c00dd86` | `e6168c0` | 2026-11-15 | paper |
| `f22cfa8` | `5b9d460` | 2026-11-15 | add cluster diagram |
| `35a76c4` | `2933d3e` | 2026-11-15 | Update main.tex |
| `39cef8e` | `a2d70a8` | 2026-11-15 | update |
| `a3eb6ab` | `246e1fa` | 2026-11-15 | Use original Python cluster figures and retire duplicate paper export |
| `1406dd4` | `f88b723` | 2026-11-15 | Keep cluster figures compact on portrait pages |
| `f5bed7a` | `265a54a` | 2026-11-15 | Develop figure-led interpretation of financial peer-group changes |
| `dae7d79` | `8061bbd` | 2026-11-15 | Adopt revised abstract and research framing |
| `037aeb5` | `09ec061` | 2026-11-15 | Adopt concise limitations and future research section |
| `71b1a82` | `01c5166` | 2026-11-15 | Polish independent study framing and add verified movement attributions |
| `4c8fdd8` | `cfbb6ec` | 2026-11-15 | Clarify grouped SHAP values and separate supporting figures |
| `e63799a` | `34330e5` | 2026-11-15 | Restore every research figure to the combined manuscript |
| `ae1d9fd` | `bee6ac3` | 2026-11-15 | Explain selection of the JSE Top 40 study universe |
| `b0265db` | `fa3d5c9` | 2026-11-15 | Support Top 40 universe selection with primary JSE sources |
| `49b8a3a` | `904e87a` | 2026-11-15 | Justify UMAP with a t-SNE comparison through the same pipeline |
| `7a860a0` | `3d40967` | 2026-11-15 | Revise paper: aligned cluster maps, sector agreement and analyst table |
| `0d93154` | `24c05ff` | 2026-11-15 | Freeze forward co-movement validation of the study clusters |
| `7380545` | `c679e7b` | 2026-11-15 | Correct a confidence interval in the co-movement README to match the frozen output |
| `14068bc` | `9d0c29c` | 2026-11-15 | Add forward co-movement validation to the paper |
| `1298a9b` | `017e239` | 2026-11-15 | Add frozen company-balanced forward co-movement validation |
| `50066b6` | `e1522b5` | 2026-11-15 | Preserve validation snapshot bytes across Git checkouts |
| `9d341fc` | `f2f3361` | 2026-11-15 | Label the beyond-sector co-movement finding as exploratory throughout |
| `c4d7b51` | `8f37d0d` | 2026-11-15 | Merge company-balanced forward co-movement validation as a sensitivity analysis |
| `b543016` | `f6c7340` | 2026-11-15 | Distinguish held-out validation from prospective preregistration |
| `e1b393a` | `2a6d4df` | 2026-11-15 | Report the company-weighted co-movement sensitivity in Section 4.7 |
| `6c2edef` | `9e912b5` | 2026-11-15 | Archive full research master and pre-validation manuscript baseline |
| `8cf0e7b` | `857369e` | 2026-11-15 | Freeze primary co-movement protocol inputs and verified outputs |
| `85c9137` | `4f1ebaa` | 2026-11-15 | Condense the manuscript from 31 to 26 pages without changing results |
| `52e4f98` | `75d04aa` | 2026-11-15 | Note the condensed manuscript in the research master README |
| `b334488` | `f316f03` | 2026-11-15 | Document condensed manuscript figures and preserved research master |
| `69b1d73` | `4faea34` | 2026-11-15 | Simplify manuscript language while preserving scientific evidence |
| `bdf266a` | `bebd47d` | 2026-11-15 | Refine research objectives and qualify exploratory findings |
| `02131cb` | `8e78c35` | 2026-11-15 | Clarify forward test windows and exploratory comparison |
| `737ccf8` | `ecd4ffb` | 2026-11-25 | Update abstract for clarity and detail on methodology |
| `2e4bcbc` | `238f456` | 2026-11-25 | Revise introduction to focus on unsupervised learning |
| `3b8daf5` | `3347bf6` | 2026-11-25 | Align the co-movement research question with the correlation test |
| `325d197` | `6d3938d` | 2026-11-25 | Report the forward co-movement result in the abstract |
| `34fcc04` | `1db97fb` | 2026-11-25 | Restore the screening-signal contribution in the abstract |
| `3b11d7b` | `5ebec0a` | 2026-11-26 | Justify the Top 40 universe and state its scope limitation |

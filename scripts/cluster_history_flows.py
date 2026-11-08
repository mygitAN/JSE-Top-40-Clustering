"""Colour membership flows from existing aligned labels; no clustering or fitting."""

def draw_cluster_history_flows(observed, dates, title):
    """One coloured strand per instrument; colour changes identify cluster shifts."""
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch, Rectangle, Patch
    if len(dates) < 2 or observed.empty or observed.ticker.duplicated().any():
        raise ValueError("Need unique instruments and at least two dates")
    values = observed[dates].to_numpy()
    if not np.isfinite(values).all():
        raise ValueError("History flows require an observation at every date")
    labels = sorted(set(values.astype(int).ravel()))
    palette = plt.get_cmap("tab20")(np.linspace(0, 1, len(labels)))
    colors = dict(zip(labels, palette))
    ordered = observed.sort_values([dates[0], "ticker"]).set_index("ticker")
    rank = {ticker: i for i, ticker in enumerate(ordered.index)}
    shifted = {ticker: row[dates].nunique() > 1 for ticker, row in ordered.iterrows()}
    positions, groups = {}, {}
    height = 0
    for date in dates:
        positions[date], groups[date] = {}, []
        cursor = 0
        for label in labels:
            members = sorted(ordered.index[ordered[date] == label], key=rank.get)
            if not members:
                continue
            groups[date].append((label, cursor - .45, len(members) - .10))
            for i, ticker in enumerate(members):
                positions[date][ticker] = cursor + i
            cursor += len(members) + 1.1
        height = max(height, cursor)
    fig, ax = plt.subplots(figsize=(10.5, max(7, .30 * len(ordered) + 2)))
    # Stable paths form a subdued background; changed instruments are emphasized.
    for ticker in sorted(ordered.index, key=lambda ticker: (shifted[ticker], rank[ticker])):
        moving = shifted[ticker]
        for j, (before, after) in enumerate(zip(dates, dates[1:])):
            y0, y1 = positions[before][ticker], positions[after][ticker]
            p0 = np.array([j + .19, y0]); p1 = np.array([j + .46, y0])
            p2 = np.array([j + .54, y1]); p3 = np.array([j + .81, y1])
            a, b, c = (p0 + p1)/2, (p1 + p2)/2, (p2 + p3)/2
            d, e = (a + b)/2, (b + c)/2
            middle = (d + e)/2
            pieces = [(np.array([p0, a, d, middle]), int(ordered.loc[ticker, before])),
                      (np.array([middle, e, c, p3]), int(ordered.loc[ticker, after]))]
            for vertices, label in pieces:
                path = MplPath(vertices, [MplPath.MOVETO] + [MplPath.CURVE4]*3)
                ax.add_patch(PathPatch(path, facecolor="none", edgecolor=colors[label],
                                       linewidth=2.3 if moving else 1.1,
                                       alpha=.82 if moving else .28, zorder=2 if moving else 1))
    for j, date in enumerate(dates):
        for label, top, group_height in groups[date]:
            ax.add_patch(Rectangle((j - .19, top), .38, group_height,
                                   facecolor=colors[label], edgecolor="white", linewidth=1, zorder=3))
        for ticker in ordered.index:
            label = int(ordered.loc[ticker, date]); color = colors[label]
            luminance = color[:3] @ np.array([.2126, .7152, .0722])
            ax.text(j, positions[date][ticker], ticker, ha="center", va="center",
                    fontsize=9, fontweight="bold" if shifted[ticker] else "normal",
                    color="white" if luminance < .46 else "black", zorder=4)
    stable = sum(not value for value in shifted.values())
    ax.set_xlim(-.35, len(dates) - .65); ax.set_ylim(height - .1, -1.1)
    ax.set_xticks(range(len(dates)), dates, fontsize=11)
    ax.xaxis.tick_top(); ax.tick_params(axis="both", length=0); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(f"{title}: coloured cluster membership flows\n"
                 f"{len(ordered)} instruments | {stable} stable | {len(ordered)-stable} shifted", pad=35)
    ax.legend(handles=[Patch(facecolor=colors[label], label=f"Cluster {label}") for label in labels],
              loc="upper center", bbox_to_anchor=(.5, -.015), ncol=min(5, len(labels)),
              frameon=False, fontsize=9)
    fig.text(.5, .012, "Colour changes mark cluster shifts. Bold names / stronger paths mark instruments that shifted.\n"
             "IDs are Jaccard-aligned descriptive labels, not sectors. Vertical positions are layout only.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .065, 1, 1))
    return fig

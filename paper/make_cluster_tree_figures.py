"""Export native TikZ cluster maps beside their exact hierarchical trees.

Run from the repository with .venv/Scripts/python.exe paper/make_cluster_tree_figures.py.
Uses archived seed-42 coordinates, verifies the eight-group cut, and does not refit UMAP.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import math
import sys

import numpy as np
from scipy.cluster.hierarchy import cut_tree, leaves_list
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from top40.models import linkage_matrix

PAPER = ROOT / 'paper'
DATES = ['2025-06-30', '2025-12-31', '2026-06-30']
NAMES = ['30 June 2025', '31 December 2025', '30 June 2026']


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def label_positions(points):
    """Place ticker labels with short leaders and no overlapping label boxes."""
    result = {}
    occupied = []
    for i in sorted(range(len(points)), key=lambda j: (-points[j, 1], points[j, 0])):
        px, py = points[i]
        candidates = []
        for radius in np.arange(.20, 2.2, .055):
            for angle in np.linspace(0, 2 * np.pi, 32, endpoint=False):
                x, y = px + radius * math.cos(angle), py + radius * math.sin(angle)
                if not (.25 < x < 6.75 and 5.25 < y < 11.75):
                    continue
                if any(abs(x - xx) < .54 and abs(y - yy) < .28 for xx, yy in occupied):
                    continue
                # Avoid placing text on top of other observed points.
                if any(j != i and abs(x - qx) < .24 and abs(y - qy) < .14
                       for j, (qx, qy) in enumerate(points)):
                    continue
                candidates.append((radius + .01 * abs(angle - np.pi / 4), x, y))
            if candidates:
                break
        if not candidates:
            raise ValueError('No collision-free ticker label position')
        _, x, y = min(candidates)
        result[i] = (x, y)
        occupied.append((x, y))
    return result


def render(date, name, embedding, tickers, raw, aligned, matrix, threshold):
    members = defaultdict(list)
    for ticker, group in zip(tickers, aligned):
        members[int(group)].append(str(ticker))
    # Equal units on the two UMAP axes; independent square limits at each date.
    span = float(np.ptp(embedding, axis=0).max()) * 1.22
    centre = (embedding.min(axis=0) + embedding.max(axis=0)) / 2
    low = centre - span / 2
    point_xy = (embedding - low) / span * 7 + np.array([0., 5.])
    text_xy = label_positions(point_xy)
    out = [r'\begin{tikzpicture}',
           rf'\node[font=\small\bfseries] at (3.5,12.75) {{(a) UMAP clusters: {name}}};',
           r'\node[font=\small\bfseries] at (12.3,12.75) {(b) Average-linkage dendrogram};']
    for f in np.linspace(0, 1, 5):
        x, y = 7 * f, 5 + 7 * f
        out += [rf'\draw[gray!15,line width=.2pt] ({x:.5f},5)--({x:.5f},12);',
                rf'\draw[gray!15,line width=.2pt] (0,{y:.5f})--(7,{y:.5f});',
                rf'\node[below,font=\tiny] at ({x:.5f},4.94) {{{low[0] + span*f:.1f}}};',
                rf'\node[left,font=\tiny] at (-.05,{y:.5f}) {{{low[1] + span*f:.1f}}};']
    out += [r'\draw[gray,line width=.4pt] (0,5) rectangle (7,12);',
            r'\node[font=\scriptsize] at (3.5,4.40) {UMAP 1};',
            r'\node[rotate=90,font=\scriptsize] at (-.68,8.5) {UMAP 2};']
    for i, (ticker, group, (x, y)) in enumerate(zip(tickers, aligned, point_xy)):
        lx, ly = text_xy[i]
        out += [rf'\draw[cluster{group}!65,line width=.3pt] ({x:.6f},{y:.6f})--({lx:.6f},{ly:.6f});',
                rf'\fill[cluster{group}] ({x:.6f},{y:.6f}) circle[radius=.055cm];',
                rf'\node[font=\fontsize{{6.2}}{{7.2}}\selectfont,text=cluster{group}!80!black,fill=white,inner sep=.4pt] at ({lx:.6f},{ly:.6f}) {{{ticker}}};']
    out += [r'\node[anchor=west,font=\scriptsize\bfseries] at (0,3.92) {Aligned groups and their members};']
    legend_y = 3.62
    for group in sorted(members):
        group_members = sorted(members[group])
        tickers_text = ', '.join(group_members[:5])
        label = (r'\textcolor{cluster'+str(group)+r'}{C'+str(group)
                 +r' ($n='+str(len(members[group]))+r'$):} '+tickers_text)
        out.append(rf'\node[anchor=north west,align=left,font=\fontsize{{6.4}}{{7.8}}\selectfont] at (0,{legend_y:.3f}) '+'{'+label+'};')
        legend_y -= .31
        if len(group_members) > 5:
            remaining = ', '.join(group_members[5:])
            out.append(rf'\node[anchor=north west,font=\fontsize{{6.4}}{{7.8}}\selectfont] at (1.3,{legend_y:.3f}) '+'{'+remaining+'};')
            legend_y -= .25
    assert legend_y > -.7

    # Exact full hierarchy: leaf spacing and all 40 merge heights are preserved.
    n = len(tickers)
    order = leaves_list(matrix).astype(int)
    positions = {int(leaf): ((rank + .5) / n * 12, 0.) for rank, leaf in enumerate(order)}
    group_sets = {i: {int(aligned[i])} for i in range(n)}
    xmax = float(matrix[-1, 2]) * 1.035
    xbase, width = 9.40, 6.05
    for i, row in enumerate(matrix):
        left, right, height = int(row[0]), int(row[1]), float(row[2])
        yl, hl = positions[left]; yr, hr = positions[right]
        yl, yr = float(yl), float(yr)
        group_sets[n+i] = group_sets[left] | group_sets[right]
        colour = f'cluster{next(iter(group_sets[n+i]))}' if len(group_sets[n+i]) == 1 else 'black!65'
        x, xl, xr = xbase + height/xmax*width, xbase + hl/xmax*width, xbase + hr/xmax*width
        out.append(rf'\draw[{colour},line width=.55pt] ({xl:.6f},{yl:.6f})--({x:.6f},{yl:.6f})--({x:.6f},{yr:.6f})--({xr:.6f},{yr:.6f});')
        positions[n+i] = ((yl+yr)/2, height)
    for leaf in order:
        y, _ = positions[int(leaf)];group=int(aligned[leaf])
        out.append(rf'\node[anchor=east,font=\fontsize{{6.1}}{{7.2}}\selectfont,text=cluster{group}!80!black,inner sep=1pt] at ({xbase-.08:.3f},{y:.6f}) {{{tickers[leaf]} [C{group}]}};')
    cutx = xbase + threshold/xmax*width
    out += [rf'\draw[red!70!black,dashed,line width=.6pt] ({cutx:.6f},-.05)--({cutx:.6f},12.05);',
            rf'\node[above,font=\tiny,text=red!70!black] at ({cutx:.6f},12.05) {{eight-group cut}};',
            rf'\draw[gray,line width=.4pt] ({xbase},-.05)--({xbase+width},-.05);']
    for value in np.linspace(0, float(matrix[-1, 2]), 5):
        x=xbase+value/xmax*width
        out += [rf'\draw[gray] ({x:.6f},-.05)--({x:.6f},-.14);',
                rf'\node[below,font=\tiny] at ({x:.6f},-.17) {{{value:.1f}}};']
    out += [rf'\node[font=\scriptsize,align=center] at ({xbase+width/2},-.83) {{Average-linkage Manhattan distance\\in the UMAP coordinates}};',
            r'\end{tikzpicture}']
    return '\n'.join(out)+'\n',dict(sorted(members.items()))


def main():
    manifest=json.loads((ROOT/'results/manifest.json').read_text())
    run=ROOT/'experiments/runs'/manifest['run_id']
    config=json.loads((run/'resolved_config.json').read_text())
    checksums=json.loads((run/'artifact_checksums.json').read_text())
    histories={r['ticker']:r for r in read_csv(ROOT/'results/longitudinal/umap/cluster_histories.csv')}
    exports={}
    for date,name in zip(DATES,NAMES):
        relative=f'models/umap/{date}/arrays.npz'
        path=run/relative
        assert hashlib.sha256(path.read_bytes()).hexdigest()==checksums[relative]
        with np.load(path,allow_pickle=False) as saved:
            embedding=saved['embedding'];tickers=saved['tickers'].astype(str);raw=saved['clusters']
        assert len(tickers)==41 and len(set(tickers))==41
        aligned=np.array([int(float(histories[ticker][date])) for ticker in tickers])
        assert len(set(aligned))==8 and adjusted_rand_score(raw,aligned)==1.
        matrix=linkage_matrix(embedding,config['primary_models']['umap']['hierarchical'])
        assert adjusted_rand_score(raw,cut_tree(matrix,n_clusters=[8]).ravel())==1.
        threshold=float((matrix[-8,2]+matrix[-7,2])/2)
        assert matrix[-8,2]<threshold<matrix[-7,2]
        tex,members=render(date,name,embedding,tickers,raw,aligned,matrix,threshold)
        key='clusters_tree_'+date
        (PAPER/'figures'/f'{key}.tex').write_text(tex,encoding='utf-8')
        coordinate_file='umap_'+date+'_coordinates.csv'
        linkage_file='umap_'+date+'_linkage.csv'
        write_csv(PAPER/'data'/coordinate_file,['ticker','umap_1','umap_2','raw_cluster','aligned_cluster'],
                  [dict(ticker=t,umap_1=float(z[0]),umap_2=float(z[1]),raw_cluster=int(a),aligned_cluster=int(b)) for t,z,a,b in zip(tickers,embedding,raw,aligned)])
        write_csv(PAPER/'data'/linkage_file,['left_child','right_child','height','count'],
                  [dict(left_child=int(l),right_child=int(r),height=float(h),count=int(c)) for l,r,h,c in matrix])
        exports[key]=dict(source_run=manifest['run_id'],source_array=relative,array_sha256=checksums[relative],
                          coordinate_file='data/'+coordinate_file,linkage_file='data/'+linkage_file,
                          tree_cut_ari=1.,cut_height=threshold,instruments=41,groups=8,
                          aligned_members=members)
    (PAPER/'cluster_tree_sources.json').write_text(json.dumps(exports,indent=2)+'\n',encoding='utf-8')
    print('Exported three paired native TikZ figures. All 123 plotted observations and all three tree cuts match the archived partitions exactly.')


if __name__=='__main__':
    main()

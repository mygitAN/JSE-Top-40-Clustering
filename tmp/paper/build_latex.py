"""Produce a portable LaTeX manuscript and native TikZ/PGFPlots figure sources."""
from pathlib import Path
from collections import Counter
import csv, re, json, hashlib, shutil, unicodedata

ROOT=Path.cwd(); OUT=ROOT/'output/paper/latex'; OUT.mkdir(parents=True,exist_ok=True)
(OUT/'figures').mkdir(exist_ok=True);(OUT/'data').mkdir(exist_ok=True)
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def esc(s):
    special={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','–':'--','—':'---','’':"'",'‘':"'",'“':'``','”':"''"}
    accents={'\u0301':"\\'",'\u0300':'\\`','\u0308':'\\"','\u0303':'\\~','\u0302':'\\^','\u0327':'\\c'}
    out=[]
    for c in s:
        decomp=unicodedata.normalize('NFD',c)
        if len(decomp)==2 and decomp[1] in accents:out.append(accents[decomp[1]]+'{'+decomp[0]+'}')
        else:out.append(special.get(c,c))
    return ''.join(out)
dates=['2025-06-30','2025-12-31','2026-06-30']; names=['June 2025','December 2025','June 2026']
hist=rows('results/longitudinal/umap/cluster_histories.csv');primary=rows('results/primary_model_summary.csv')
profiles=rows('results/longitudinal/umap/moves/cluster_profiles.csv'); comparison=rows('results/model_comparison.csv')
seed=rows('results/seed_agreement.csv'); shifts=rows('results/feature_audit/shift_counts.csv')
run=ROOT/'experiments/runs/20261115T062631-0c09819ce3c0'
sensitivity=run/'models/umap/cluster_count_sensitivity.csv'
run_checks=json.loads((run/'artifact_checksums.json').read_text())
assert hashlib.sha256(sensitivity.read_bytes()).hexdigest()==run_checks['models/umap/cluster_count_sensitivity.csv']
manifest=json.loads((ROOT/'results/manifest.json').read_text())
for name,checksum in manifest['files'].items():assert hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest()==checksum
source_files=['results/primary_model_summary.csv','results/model_comparison.csv','results/seed_agreement.csv','results/temporal_agreement.csv','results/feature_audit/shift_counts.csv','results/longitudinal/umap/cluster_histories.csv','results/longitudinal/umap/moves/cluster_profiles.csv']
for src in source_files:shutil.copy2(ROOT/src,OUT/'data'/Path(src).name)
shutil.copy2(sensitivity,OUT/'data/cluster_count_sensitivity.csv')
figures={}; captions={}; provenance={}
def save(key,tex,caption,source):
    figures[key]=tex;captions[key]=caption;provenance[key]=source
    (OUT/'figures'/f'{key}.tex').write_text(tex+'\n',encoding='utf-8')
def tikz(body,opts=''):
    return '\\begin{tikzpicture}['+opts+']\n'+body+'\n\\end{tikzpicture}'

save('population',tikz(r'''
\node[box] (a) at (0,0) {30 June 2025\\41 instruments\\40 company groups};
\node[box] (b) at (5,0) {31 December 2025\\41 instruments\\40 company groups};
\node[box] (c) at (10,0) {30 June 2026\\41 instruments\\40 company groups};
\draw[arrow] (a)--node[above,font=\scriptsize,align=center]{APN exits\\GLN enters}(b);
\draw[arrow] (b)--node[above,font=\scriptsize,align=center]{MNP exits\\PAN enters}(c);
\node[box,text width=11.8cm] (sum) at (5,-2) {123 instrument-date records; 43 distinct securities\\40 continuing per adjacent pair; 39 observed at all three dates};
\draw[thin,gray] (a.south)--(sum.north west);
\draw[thin,gray] (b.south)--(sum.north);
\draw[thin,gray] (c.south)--(sum.north east);
'''),'Index populations and continuity. The flow population has 39 complete histories; every date-specific fit retains all 41 instruments.','data/reference/index_changes.csv; results/longitudinal/umap/cluster_histories.csv')

save('windows',tikz(r'''
\draw[arrow] (-.2,0)--(12.7,0);
\foreach \x/\lab in {0/Jun 2024,3/Dec 2024,6/Jun 2025,9/Dec 2025,12/Jun 2026}{
  \draw (\x,.08)--(\x,-.08);\node[below,font=\scriptsize] at (\x,-.1){\lab};}
\fill[steel!18] (0,2.3) rectangle (6,2.75);
\fill[teal!22] (3,1.5) rectangle (9,1.95);
\fill[orange!23] (6,.7) rectangle (12,1.15);
\draw[thick,steel] (0,2.3) rectangle (6,2.75);
\draw[thick,teal] (3,1.5) rectangle (9,1.95);
\draw[thick,orange!80!black] (6,.7) rectangle (12,1.15);
\node[right,font=\scriptsize] at (6.1,2.52){First decision date};
\node[right,font=\scriptsize] at (9.1,1.72){Second decision date};
\node[left,font=\scriptsize] at (5.9,.92){Third decision date};
\draw[dashed,gray] (6,0)--(6,2.9);
\draw[dashed,gray] (9,0)--(9,2.1);
\draw[dashed,gray] (12,0)--(12,1.3);
\node[align=center,font=\small] at (6,-1.05){Adjacent trailing annual windows overlap by six months.\\Repeated firms and recurring accounts add further dependence.};
'''),'Dependence across the three cross-sections. Bars depict trailing annual market windows schematically; fundamentals follow their recorded issuer reporting dates, not these uniform windows.','docs/method.md; three recorded decision dates')

save('pipeline',tikz(r'''
\node[widebox] (data) {Effective-dated index population and provenance workbook\\41 instruments at each date};
\node[widebox,below=5mm of data] (features) {Documented corrections and eight engineered features\\Imputation and clipping constants estimated in June 2025};
\node[widebox,below=5mm of features] (scale) {June 2025 MinMax reference applied to all three dates\\Later values are allowed outside $[0,1]$};
\node[widebox,below=5mm of scale] (fit) {Independent UMAP and hierarchical fits at each date\\2D; 3 neighbours; $\mathrm{min\_dist}=0.01$; average Manhattan; $k=8$};
\node[widebox,below=5mm of fit] (evaluate) {Financial-space and embedding-space quality; sizes and singletons\\Five seeds per date; ten pairwise seed ARIs};
\node[widebox,below=5mm of evaluate] (align) {Continuing-member Jaccard matrix and Hungarian matching\\Separate index entries and exits from aligned group switches};
\node[widebox,below=5mm of align] (report) {Named histories and direct financial profiles\\Fidelity-qualified surrogate explanation and separate distance screen};
\foreach \a/\b in {data/features,features/scale,scale/fit,fit/evaluate,evaluate/align,align/report}{\draw[arrow](\a)--(\b);}
'''),'Repeated cross-sectional study workflow. The preprocessing reference carries forward, while each date receives a fresh representation and partition.','configs/study.json; top40/features.py; top40/study.py; top40/temporal.py')

common={r['ticker'] for r in hist if r[dates[0]] and r[dates[1]]}
A={r['ticker'] for r in hist if r['ticker'] in common and float(r[dates[0]])==1}
B={r['ticker'] for r in hist if r['ticker'] in common and float(r[dates[1]])==1}
assert len(A&B)==5 and len(A|B)==8
save('alignment',tikz(r'''
\node[box,text width=5.0cm] (old) at (0,0) {June 2025 aligned group 1\\ABG, GRT, INL, INP, NED, NRP, OMU, VAL};
\node[box,text width=4.1cm] (new) at (7.8,0) {December 2025 aligned group 1\\GRT, INL, INP, NED, NRP};
\draw[arrow] (old)--node[above,font=\small]{$J=5/8=0.625$}(new);
\node[widebox,text width=11.5cm] (global) at (3.9,-2.0) {Build the full cluster-by-cluster matrix on 40 continuing instruments.\\The Hungarian assignment maximises the total Jaccard overlap.};
\node[box,text width=5.0cm] (matched) at (.5,-4.0) {Assigned pair with positive overlap\\Carry forward the earlier label};
\node[box,text width=5.0cm] (fresh) at (7.3,-4.0) {Assigned pair with zero overlap\\Issue a fresh, never-reused label};
\draw[arrow](global)--(matched);\draw[arrow](global)--(fresh);
\node[font=\small,align=center] at (3.9,-5.3){For continuing instruments only: different aligned labels imply a recorded switch.\\Entries, exits and incomplete histories remain separate.};
'''),'Matching clusters with an observed overlap example. Five of the eight earlier group-1 members occupy the later group-1 match. This local example illustrates the similarity calculation; the actual assignment optimises all group pairs jointly.','top40/temporal.py; results/longitudinal/umap/cluster_histories.csv')

plot=r'\begin{tikzpicture}\begin{axis}[width=.96\linewidth,height=6cm,ybar,bar width=10pt,ymin=0,ymax=.85,ylabel={Mean silhouette},symbolic x coords={Jun25,Dec25,Jun26},xtick=data,xticklabels={June 2025,December 2025,June 2026},legend style={at={(.5,1.02)},anchor=south,legend columns=2,font=\scriptsize},enlarge x limits=.23,nodes near coords,every node near coord/.append style={font=\tiny,/pgf/number format/fixed,/pgf/number format/precision=3},tick label style={font=\small},legend cell align=left]'+'\n'
for color,model,field in [('steel','umap','silhouette_features'),('steel!35','umap','silhouette_embedding'),('rust','tsne_hierarchical','silhouette_features'),('rust!35','tsne_hierarchical','silhouette_embedding')]:
    vals=[]
    for date,label in zip(dates,['Jun25','Dec25','Jun26']):
        r=next(x for x in comparison if x['decision_date']==date and x['model']==model);vals.append(f'({label},{r[field]})')
    plot+=rf'\addplot[fill={color},draw=none] coordinates {{'+''.join(vals)+'};\n'
plot+=r'\legend{UMAP financial,UMAP embedding,t-SNE financial,t-SNE embedding}\end{axis}\end{tikzpicture}'
save('quality',plot,'The same partitions evaluated in two geometries. UMAP has the stronger embedding silhouette at every date; this advantage does not consistently hold in the underlying financial features.','results/model_comparison.csv; results/primary_model_summary.csv')

plot=r'\begin{tikzpicture}\begin{axis}[width=.93\linewidth,height=6.4cm,ymin=.4,ymax=1.02,xmin=.6,xmax=3.4,xtick={1,2,3},xticklabels={June 2025,December 2025,June 2026},ylabel={Pairwise seed ARI},tick label style={font=\small},legend style={at={(.5,-.2)},anchor=north,legend columns=2,font=\small}]'+'\n'
for i,date in enumerate(dates):
    vals=[float(x['ari']) for x in seed if x['decision_date']==date and x['study_model']=='umap'];assert len(vals)==10
    coords=''.join(f'({i+1+(j-4.5)*.018:.4f},{v:.8f})' for j,v in enumerate(vals))
    plot+=r'\addplot[only marks,mark=*,mark size=2pt,color=steel] coordinates {'+coords+'};\n'
    mean=sum(vals)/10
    plot+=rf'\draw[very thick,rust] (axis cs:{i+.82},{mean})--(axis cs:{i+1.18},{mean});'+'\n'
    plot+=rf'\node[above,font=\scriptsize] at (axis cs:{i+1},.43) {{mean {mean:.3f}}};'+'\n'
plot+=r'\end{axis}\end{tikzpicture}'
save('seed_variability',plot,'Ten pairwise adjusted Rand indices from five UMAP seeds at each date. Points are offset horizontally for readability; red segments mark the means. Pairs share fitted partitions and are dependent, so the spread is not a confidence interval or an empirical null for temporal switches.','results/seed_agreement.csv')

# Native TikZ instrument-level flow: only complete histories, with aligned labels.
complete=[r for r in hist if r['observed_all_dates']=='True'];assert len(complete)==39
positions={};body=''
for t,date in enumerate(dates):
    x=t*5.3; ordered=sorted(complete,key=lambda r:(float(r[date]),r['ticker'])); y=0; groups={}
    for r in ordered:
        c=int(float(r[date]));groups.setdefault(c,[]).append(r)
    for c,rr in groups.items():
        top=y+.13
        for r in rr:
            positions[t,r['ticker']]=(x,y);y-=.25
        bottom=y+.12
        body+=rf'\fill[cluster{c}!17] ({x-1.0},{bottom:.3f}) rectangle ({x+1.0},{top:.3f});'+'\n'
        body+=rf'\node[left,font=\tiny,text=cluster{c}] at ({x-1.03},{(top+bottom)/2:.3f}) {{C{c}}};'+'\n'
        y-=.15
    body+=rf'\node[above,font=\small\bfseries] at ({x},.5){{{names[t]}}};'+'\n'
for t in [0,1]:
    for r in complete:
        x,y=positions[t,r['ticker']];xx,yy=positions[t+1,r['ticker']];c=int(float(r[dates[t]]));change=r[dates[t]]!=r[dates[t+1]]
        body+=rf'\draw[cluster{c},opacity={.65 if change else .22},line width={.65 if change else .3}pt] ({x+1:.3f},{y:.3f}) .. controls ({x+2.2:.3f},{y:.3f}) and ({xx-2.2:.3f},{yy:.3f}) .. ({xx-1:.3f},{yy:.3f});'+'\n'
for t,date in enumerate(dates):
    for r in complete:
        x,y=positions[t,r['ticker']];font=r'\bfseries' if r['stability_status']=='shifted' else ''
        body+=rf'\node[font=\scriptsize{font}] at ({x},{y:.3f}) {{{r["ticker"]}}};'+'\n'
save('flows',tikz(body),'Native LaTeX rendering of all 39 complete instrument histories: 19 stable and 20 shifted. Bold tickers change aligned label at least once. APN, MNP, GLN and PAN are excluded only from this complete-history view. Labels identify aligned groups, not industries; vertical positions are layout.','results/longitudinal/umap/cluster_histories.csv')

body=''
for t in [0,1]:
    old=dates[t];new=dates[t+1];common=[r for r in hist if r[old] and r[new]]
    left=sorted({int(float(r[old])) for r in hist if r[old]});right=sorted({int(float(r[new])) for r in hist if r[new]})
    offset=t*7.2
    body+=rf'\node[font=\small\bfseries] at ({offset+2.1},1) {{{names[t]} to {names[t+1]}}};'+'\n'
    for i,a in enumerate(left):
        body+=rf'\node[font=\scriptsize] at ({offset-.6},{-i*.53}){{C{a}}};'+'\n'
        for j,b in enumerate(right):
            A={r['ticker'] for r in common if int(float(r[old]))==a};B={r['ticker'] for r in common if int(float(r[new]))==b};v=len(A&B)/len(A|B) if A|B else 0
            x=offset+j*.53;y=-i*.53
            body+=rf'\fill[steel!{100*v:.3f}!white] ({x-.265},{y-.265}) rectangle ({x+.265},{y+.265});'+'\n'
            body+=rf'\node[font=\tiny,text={"white" if v>.55 else "black"}] at ({x},{y}){{{v:.2f}}};'+'\n'
    for j,b in enumerate(right):body+=rf'\node[font=\scriptsize] at ({offset+j*.53},.5){{C{b}}};'+'\n'
body+=r'\node[font=\small] at (5.4,-4.8){Rows: earlier aligned groups; columns: later aligned groups; darker means greater overlap.};'
save('jaccard',tikz(body),'Jaccard overlap among the 40 continuing members in each adjacent comparison. Each cell uses the common eligible universe for that period. Numeric values are given explicitly; a zero denotes no shared continuing member.','results/longitudinal/umap/cluster_histories.csv; top40/temporal.py')

for t,date in enumerate(dates):
    sub=[r for r in profiles if r['decision_date']==date];cs=sorted({int(r['cluster']) for r in sub});fs=list(dict.fromkeys(r['feature'] for r in sub));body=''
    for j,label in enumerate(['Return','Beta','Volatility',r'Div.\\yield',r'Earn.\\yield',r'Log\\cap',r'Log\\rev/cap',r'Log\\turnover']):
        body+=rf'\node[font=\scriptsize,align=center] at ({j*1.34},.72){{\shortstack{{{label}}}}};'+'\n'
    for i,c in enumerate(cs):
        rr=[r for r in sub if int(r['cluster'])==c];body+=rf'\node[left,font=\scriptsize] at (-.78,{-i*.55}){{C{c} ($n={rr[0]["n"]}$)}};'+'\n'
        for j,f in enumerate(fs):
            v=float(next(r for r in rr if r['feature']==f)['deviation_scaled']);x=j*1.34;y=-i*.55;intensity=min(abs(v)/1.5,1)*78
            body+=rf'\fill[{"red" if v>=0 else "blue"}!{intensity:.3f}!white] ({x-.67},{y-.275}) rectangle ({x+.67},{y+.275});'+'\n'
            body+=rf'\node[font=\scriptsize] at ({x},{y}){{${v:+.2f}$}};'+'\n'
    body+=r'\node[font=\scriptsize] at (4.7,-4.65){Common colour scale: $-1.5$ (blue) to $+1.5$ (red); zero is the same-date median.};'
    save('profile'+str(t),tikz(body),f'{names[t]} aligned-cluster median deviations from the same-date median, in June 2025 MinMax units. Counts include all 41 date-specific instruments. Colours use the same range across the three figures; gaps in cluster numbers reflect retired identifiers.','results/longitudinal/umap/moves/cluster_profiles.csv')

plot=r'\begin{tikzpicture}\begin{axis}[width=.96\linewidth,height=5.8cm,ybar stacked,bar width=30pt,ymin=0,ymax=43,ylabel={Complete instrument histories},symbolic x coords={original10,logsize10,invariant8,market5},xtick=data,xticklabel style={font=\small},ytick={0,10,20,30,39},enlarge x limits=.2,nodes near coords,every node near coord/.append style={font=\small},legend style={at={(.5,1.02)},anchor=south,legend columns=2}]'+'\n'
for field,color in [('stable','steel'),('shifted','rust!70')]:
    coords=' '.join(f'({r["feature_set"]},{r[field]})' for r in shifts if r['recipe']=='umap')
    plot+=rf'\addplot[fill={color},draw=white] coordinates {{{coords}}};'+'\n'
plot+=r'\legend{Stable aligned histories,Shifted at least once}\end{axis}\end{tikzpicture}'
save('feature_sensitivity',plot,'Complete-history outcomes under four feature representations using the UMAP recipe. Each bar contains the same 39 continuously observed instruments; four partial histories are outside every bar. The counts are representation-dependent and are not estimates of true economic change.','results/feature_audit/shift_counts.csv, recipe=umap only')

sense=rows(sensitivity.relative_to(ROOT));body=r'\begin{tikzpicture}\begin{groupplot}[group style={group size=3 by 2,horizontal sep=1.1cm,vertical sep=1.45cm},width=.29\linewidth,height=4cm,xmin=2,xmax=12,xtick={2,4,6,8,10,12},tick label style={font=\scriptsize},label style={font=\scriptsize},title style={font=\small},grid=major,grid style={gray!15}]'+'\n'
for metric,label in [('silhouette','Silhouette (higher better)'),('davies_bouldin','Davies--Bouldin (lower better)')]:
    for i,date in enumerate(dates):
        body+=rf'\nextgroupplot[title={{{names[i]}}},xlabel={{$k$}},ylabel={{{label if i==0 else ""}}}]'+'\n'
        sub=[r for r in sense if r['decision_date']==date]
        for geom,color in [('features','steel'),('embedding','rust')]:
            coords=' '.join(f'({r["k"]},{r[metric+"_"+geom]})' for r in sub)
            body+=rf'\addplot[color={color},mark=*,mark size=1.2pt] coordinates {{{coords}}};'+'\n'
body+=r'\end{groupplot}\end{tikzpicture}'
save('cluster_count',body,'Cluster-count sensitivity redrawn from the archived numerical table for the same clean run. Blue evaluates financial features and red evaluates the embedding. Eight groups remain the historical specification, not a validated natural count.','experiments/runs/20261115T062631-0c09819ce3c0/models/umap/cluster_count_sensitivity.csv; archive checksum verified')

save('evidence',tikz(r'''
\node[widebox,text width=10.4cm] (input) at (0,0) {Financial inputs and dated membership\\Source corrections and missing-value flags};
\node[box,text width=3.6cm] (group) at (-4.8,-1.9) {Peer groups\\Aligned label changes\\Membership overlaps};
\node[box,text width=3.6cm] (profile) at (0,-1.9) {Financial profiles\\Feature changes\\Median deviations};
\node[box,text width=3.6cm] (screen) at (4.8,-1.9) {Distance screen\\Mahalanobis distance\\Beta reference};
\draw[arrow](input)--(group);\draw[arrow](input)--(profile);\draw[arrow](input)--(screen);
\node[widebox,text width=12.2cm,font=\footnotesize] (qualify) at (0,-4.0) {Check seeds, feature sensitivity, cluster sizes and surrogate fidelity.\\SHAP explains a surrogate; sectors provide descriptive context.};
\draw[arrow](group)--(qualify);\draw[arrow](profile)--(qualify);\draw[arrow](screen)--(qualify);
\node[widebox,text width=12.2cm,font=\footnotesize,fill=orange!9] (out) at (0,-5.6) {Analyst follow-up candidates\\External validation precedes structural-anomaly or predictive claims.};
\draw[arrow](qualify)--(out);
'''),'Interpretation of separate evidence streams. Group movement, feature profiles and distance flags can motivate follow-up, but are not combined into an automatically confirmed anomaly. Stochastic, measurement and surrogate limitations apply to the interpretation.','docs/method.md; top40/explain.py; top40/models.py; current manuscript evidence boundaries')

PREAMBLE=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=24mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,tabularx,array}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{pgfplots}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage{placeins}
\usepackage{microtype}
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{2.5ex plus 1ex}{1.3ex}
\titlespacing*{\subsection}{0pt}{2ex plus .5ex}{1ex}
\usepackage[round,authoryear]{natbib}
\usepackage[hidelinks,breaklinks]{hyperref}
\usepackage{xurl}
\definecolor{steel}{HTML}{315D7B}
\definecolor{rust}{HTML}{AE5939}
\definecolor{cluster0}{HTML}{347CA8}
\definecolor{cluster1}{HTML}{BF6D20}
\definecolor{cluster2}{HTML}{378951}
\definecolor{cluster3}{HTML}{BE4545}
\definecolor{cluster4}{HTML}{855AA5}
\definecolor{cluster5}{HTML}{8B6657}
\definecolor{cluster6}{HTML}{B85D8B}
\definecolor{cluster7}{HTML}{64757B}
\definecolor{cluster8}{HTML}{A39037}
\definecolor{cluster9}{HTML}{168A94}
\tikzset{box/.style={draw=steel!70,fill=steel!5,rounded corners=1pt,align=center,text width=3.1cm,minimum height=1.2cm,font=\small,inner sep=6pt},widebox/.style={box,text width=12.4cm,minimum height=1cm},arrow/.style={-{Latex[length=2mm]},thick,draw=steel!80}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{2em}
\renewcommand{\topfraction}{.95}
\renewcommand{\bottomfraction}{.9}
\renewcommand{\textfraction}{.05}
\renewcommand{\floatpagefraction}{.75}
\newcommand{\diagram}[1]{\resizebox{\linewidth}{!}{\input{figures/#1.tex}}}
'''
(OUT/'preamble.tex').write_text(PREAMBLE,encoding='utf-8')
order=[]
def figure(key):
    order.append(key)
    return '\n\\begin{figure}[htbp]\n\\centering\n\\diagram{'+key+'}\n\\caption{'+esc(captions[key])+'}\\label{fig:'+key+'}\n\\end{figure}\n'

md=(ROOT/'output/paper/JSE_Top40_Three_Cross_Section_Paper_20261115.md').read_text(encoding='utf-8')
fixes={'emergingmarket':'emerging-market','shapebased':'shape-based','financialmarket':'financial-market','DaviesBouldin':'Davies-Bouldin'}
for a,b in fixes.items():md=md.replace(a,b)
md=md.replace('Figures 6-8','PROFILE_RANGE')
md=re.sub(r'Figures 1-3 and 6-8 are manuscript drawings.*?No model rerun or new empirical claim is implied by redrawing a figure\.', 'All fourteen diagrams in this revision are drawn natively in LaTeX with TikZ or PGFPlots. Source tables are included in the LaTeX project; the cluster-count table comes from the checksum-verified archive of the same numerical run. The figure-source manifest records each input. Numerical summaries retain all date-specific members; only the complete-history flow restricts the population to 39 instruments. No model rerun or new empirical finding is implied by redrawing the diagrams.',md,flags=re.S)
md=md.replace('only Figure 4','only the complete-history flow')
blocks=md.split('\n\n'); body=[];refs=[];inrefs=False;table_num=0
oldfig={1:'population',2:'pipeline',3:'quality',4:'flows',5:'jaccard',6:'profile0',7:'profile1',8:'profile2',9:'cluster_count'}
citeinfo=[('ahmed2016','Ahmed et al.','2016'),('ahmed2017','Ahmed et al.','2017'),('arbelaitz2013','Arbelaitz et al.','2013'),('barradas2023','Barradas et al.','2023'),('chen2021','Chen et al.','2021'),('cheong2021','Cheong et al.','2021'),('cuomo2022','Cuomo et al.','2022'),('davies1979','Davies and Bouldin','1979'),('greene2008','Greene et al.','2008'),('han2023','Han et al.','2023'),('leon2017','León et al.','2017'),('lim2021','Lim and Ong','2021'),('mcinnes2018','McInnes et al.','2018'),('merrick2020','Merrick and Taly','2020'),('nair2017','Nair et al.','2017'),('nourahmadi2022','Nourahmadi et al.','2022'),('rousseeuw1987','Rousseeuw','1987'),('rozemberczki2022','Rozemberczki et al.','2022'),('unlu2021','Ünlü and Xanthopoulos','2021'),('vendramin2010','Vendramin et al.','2010')]
def prose(s):
    result=esc(s)
    for token in re.findall(r'[\w./-]*_[\w./-]*\.(?:csv|png|json|xlsx)',s):
        result=result.replace(esc(token),r'\nolinkurl{'+token+'}')
    for key,author,year in citeinfo:
        result=result.replace(esc(author+' ('+year+')'),r'\citep{'+key+'}')
        result=result.replace(esc('('+author+', '+year+')'),r'\citep{'+key+'}')
    result=result.replace('(\\citep{',r'\citep{').replace('2018})','2018}').replace('2020})','2020}')
    result=result.replace(r'PROFILE\_RANGE',r'Figures~\ref{fig:profile0}--\ref{fig:profile2}')
    # Break long provenance strings and filenames safely in the typeset manuscript.
    result=re.sub(r'(?<![A-Za-z0-9])[a-f0-9]{40}(?![A-Za-z0-9])',lambda m:r'\nolinkurl{'+m.group()+'}',result)
    result=re.sub(r'https://github\.com/mygitAN/JSE-Top-40-Clustering',r'\\url{https://github.com/mygitAN/JSE-Top-40-Clustering}',result)
    return result
body.append(r'\title{Interpretable Unsupervised Learning for JSE Top 40 Equities\\[5pt]\large A Repeated Cross-Sectional Study of Financial Peer Groups}\author{A. Nxitywa}\date{15 November 2026}\maketitle')
abstract_next=False;pending_caption=None
for block in blocks:
    block=block.strip()
    if not block:continue
    if block.startswith('# ') or block in ['A Repeated Cross Sectional Study of Financial Peer Groups','A. Nxitywa','15 November 2026']:continue
    if block=='## Abstract':abstract_next=True;continue
    if abstract_next:body.append('\\begin{abstract}\n'+prose(block)+'\n\\end{abstract}');abstract_next=False;continue
    if block.startswith('## References'):inrefs=True;continue
    if inrefs and not block.startswith('## Appendix'):
        refs.append(block);continue
    if block.startswith('## Appendix'):
        inrefs=False
        assert len(refs)==20
        bibliography='\\begin{thebibliography}{99}\n'
        for ref,(key,author,year) in zip(refs,citeinfo):
            ref=re.sub(r'(10\.1007/)\s+',r'\1',ref)
            bibliography+=rf'\bibitem[{esc(author)}({year})]{{{key}}} '+esc(ref)+'\n\n'
        bibliography+='\\end{thebibliography}\n'
        (OUT/'references.tex').write_text(bibliography,encoding='utf-8')
        body.append(r'\FloatBarrier\input{references.tex}\appendix\section{Reproducibility and evidence}');continue
    if block.startswith('### '):
        title=re.sub(r'^### \d+\.\d+\s+','',block);body.append('\\subsection{'+esc(title)+'}');continue
    if block.startswith('## '):
        title=re.sub(r'^## \d+\s+','',block)
        if title=='Discussion':
            body.append('The evidence streams and their interpretation are summarised in Figure~\\ref{fig:evidence}.')
            body.append(figure('evidence'))
        body.append('\\FloatBarrier\n\\section{'+esc(title)+'}');continue
    if block.startswith('Table '):pending_caption=re.sub(r'^Table \d+\. ','',block);continue
    if block.startswith('|'):
        table_num+=1; rr=[line.strip('|').split('|') for line in block.splitlines()];rr=[[x.strip() for x in row] for row in rr];n=len(rr[0]);rr=rr[:1]+rr[2:]
        proportions={1:[.22,.13,.13,.52],2:[.28,.72],3:[.25,.75],4:[.10,.90],5:[.23,.115,.14,.115,.115,.14,.145],6:[.25,.10,.13,.15,.15,.11,.11],7:[.22,.25,.18,.16,.19],8:[.24,.25,.30,.21],9:[.24,.64,.12]}[table_num]
        columns=' '.join(r'>{\hsize='+f'{fraction*n:.3f}'+r'\hsize\linewidth=\hsize\raggedright\arraybackslash}X' for fraction in proportions)
        tex='\\begin{table}[htbp]\n\\centering\\caption{'+esc(pending_caption or '')+'}\\label{tab:'+str(table_num)+'}\n\\footnotesize\n\\begin{tabularx}{\\linewidth}{@{}'+columns+'@{}}\n\\toprule\n'
        for i,row in enumerate(rr):tex+=' & '.join(esc(x) for x in row)+r' \\'+'\n'+('\\midrule\n' if i==0 else '')
        tex+='\\bottomrule\n\\end{tabularx}\n\\end{table}\n';body.append(tex);pending_caption=None
        if table_num==4:
            body.append('Figure~\\ref{fig:alignment} illustrates the overlap calculation with an observed matched pair.')
            body.append(figure('alignment'))
        if table_num==7:
            body.append('The representation sensitivity of complete-history counts is shown in Figure~\\ref{fig:feature_sensitivity}.')
            body.append(figure('feature_sensitivity'))
        continue
    if block.startswith('!['):
        old=int(re.match(r'!\[Figure (\d+)\.',block).group(1));key=oldfig[old];body.append(figure(key))
        if old==1:
            body.append('The annual market windows overlap as shown in Figure~\\ref{fig:windows}; pooling their rows does not create independent observations.')
            body.append(figure('windows'))
        if old==3:
            body.append('Figure~\\ref{fig:seed_variability} shows all ten seed-pair agreements underlying each mean.')
            body.append(figure('seed_variability'))
        continue
    body.append(prose(block)+'\n')
    if block.startswith('For feature j, let'):
        body.append(r'''\begin{equation}
z_{itj}=\frac{x_{itj}-a_j}{b_j-a_j},\qquad
a_j=\min_{i\in U_{t_1}}x_{it_1j},\quad b_j=\max_{i\in U_{t_1}}x_{it_1j}.
\label{eq:scale}\end{equation}''')
    if block.startswith('For each date and each seed'):
        body.append(r'''The linkage between groups $G$ and $H$ of two-dimensional coordinates $u_i$ is
\begin{equation}
d_{\mathrm{avg},1}(G,H)=\frac{1}{|G||H|}\sum_{i\in G}\sum_{j\in H}\|u_i-u_j\|_1.
\label{eq:linkage}\end{equation}''')
    if block.startswith('Let C be the instruments'):
        body.append(r'''Writing $A_a^C=A_a\cap C$ and $B_b^C=B_b\cap C$, the matching objective is
\begin{align}
J_{ab}&=\frac{|A_a^C\cap B_b^C|}{|A_a^C\cup B_b^C|},\\
\pi^*&\in\operatorname*{arg\,max}_{\pi}\sum_a J_{a,\pi(a)}.
\label{eq:matching}\end{align}
The implementation sets empty-union similarities to zero and carries labels only for positive intersections.''')
    if block.startswith('For each cluster, we subtract'):
        body.append(r'''\begin{equation}
\Delta_{ctj}=\operatorname{median}_{i\in G_{ct}}z_{itj}-\operatorname{median}_{i\in U_t}z_{itj}.
\label{eq:profiles}\end{equation}''')
    if block.startswith('The screen computes squared Mahalanobis'):
        body.append(r'''\begin{align}
D_{it}^2&=(z_{it}-\bar z_t)^{\mathsf T}S_t^{-1}(z_{it}-\bar z_t),\\
\frac{n}{(n-1)^2}D_{it}^2&\sim\operatorname{Beta}\!\left(\frac p2,\frac{n-p-1}{2}\right)
\quad\text{under the idealised normal reference}.
\label{eq:distance}\end{align}''')

assert len(order)==14 and len(set(order))==14,order
(OUT/'main.tex').write_text('\\input{preamble.tex}\n\\begin{document}\n'+'\n\n'.join(body)+'\n\\FloatBarrier\n\\end{document}\n',encoding='utf-8')
atlas='\\input{preamble.tex}\n\\begin{document}\n\\section*{Three cross-sectional study diagram atlas}\nNative TikZ and PGFPlots sources for the revised manuscript. All numerical figures use the saved clean-run tables; schematic diagrams are identified in their captions.\n'
for key in order:
    atlas+='\\clearpage\n\\begin{figure}[p]\n\\centering\n\\diagram{'+key+'}\n\\caption{'+esc(captions[key])+'}\\end{figure}\n'
atlas+='\\end{document}\n';(OUT/'diagrams.tex').write_text(atlas,encoding='utf-8')
(OUT/'figure_sources.json').write_text(json.dumps({'numerical_run':manifest['run_id'],'implementation_commit':manifest['git_commit'],'figure_order':order,'sources':provenance,'archive_sensitivity_sha256':hashlib.sha256(sensitivity.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
(OUT/'README.md').write_text('''# LaTeX manuscript and native diagrams

Compile `main.tex` twice with pdfLaTeX (or use `latexmk -pdf main.tex`).
Compile `diagrams.tex` for the separate diagram atlas. Tectonic is also supported:

```
tectonic main.tex
tectonic diagrams.tex
```

All 14 diagrams are native TikZ or PGFPlots. No PNG or externally drawn PDF is needed.
`figures/` contains the reusable LaTeX inputs; `data/` contains the saved numerical source tables.
`figure_sources.json` records the provenance and the checksum-verified cluster-count source.
The manuscript retains the supplied literature and uses native equations and author-year citations.
Upload this complete folder (or its ZIP) to Overleaf and choose `main.tex` as the main document.

Five additions: overlapping annual windows; observed Jaccard matching example;
seed-pair variability; feature-representation sensitivity; separate evidence streams.
The original nine diagrams have also been redrawn natively.
''',encoding='utf-8')
print('Wrote LaTeX manuscript, 14 native diagrams, atlas and eight source tables. Verified 78 result checksums and archived sensitivity table.')

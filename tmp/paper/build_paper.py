from pathlib import Path
import re, csv, json, hashlib, shutil
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF

ROOT=Path.cwd(); OUT=ROOT/'output/paper'; OUT.mkdir(parents=True,exist_ok=True)
FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
def readcsv(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
primary=readcsv('results/primary_model_summary.csv'); comparison=readcsv('results/model_comparison.csv')
hist=readcsv('results/longitudinal/umap/cluster_histories.csv'); profiles=readcsv('results/longitudinal/umap/moves/cluster_profiles.csv')
dates=['2025-06-30','2025-12-31','2026-06-30']; names=['June 2025','December 2025','June 2026']
manifest=json.loads((ROOT/'results/manifest.json').read_text())
for p,h in manifest['files'].items():
    assert hashlib.sha256((ROOT/'results'/p).read_bytes()).hexdigest()==h,p
source=(ROOT/'tmp/paper/JSE_Top40_Revised_Paper_Preserved_Literature_20261115.txt').read_text(encoding='utf-8')
source=re.sub(r'\nPAGE \d+\n','\n',source); source=re.sub(r'\n\d+\s*\n','\n',source)
intro=source.split('1 Introduction\n',1)[1].split('2 Related Work\n')[0]
related=source.split('2 Related Work\n',1)[1].split('3 Study population, data and provenance\n')[0]
refs=source.split('\nReferences\n',1)[1].split('A Reproducibility and source-evidence notes')[0]
def clean(s):
    s=re.sub(r'(\w)-\n(\w)',r'\1\2',s);s=re.sub(r'\s+',' ',s).strip()
    for a,b in [('question is:How','question is: How'),('repeatablescreening','repeatable screening'),('Finance,','Finance,')]:s=s.replace(a,b)
    return s
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPaper',fontName='Times-Roman',fontSize=10.5,leading=14,alignment=TA_JUSTIFY,spaceAfter=8))
styles.add(ParagraphStyle(name='TitlePaper',fontName='Times-Bold',fontSize=19,leading=23,alignment=TA_CENTER,spaceAfter=16))
styles.add(ParagraphStyle(name='SmallPaper',fontName='Times-Roman',fontSize=9,leading=11.5,spaceAfter=7))
styles.add(ParagraphStyle(name='CaptionPaper',fontName='Times-Roman',fontSize=9,leading=11.5,spaceBefore=6,spaceAfter=13))
styles['Heading1'].fontName='Times-Bold';styles['Heading1'].fontSize=14;styles['Heading1'].leading=17
styles['Heading2'].fontName='Times-Bold';styles['Heading2'].fontSize=11.5;styles['Heading2'].leading=14
styles['Heading1'].keepWithNext=True;styles['Heading2'].keepWithNext=True
styles.add(ParagraphStyle(name='SubtitlePaper',fontName='Times-Roman',fontSize=15,leading=19,alignment=TA_CENTER,spaceAfter=14))
story=[]; md=[]; figure_sources={}; W=475
def p(t,small=False):
    md.append(t+'\n');story.append(Paragraph(escape(t),styles['SmallPaper' if small else 'BodyPaper']))
def h(t,level=1):
    md.append('#'*(level+1)+' '+t+'\n');story.append(Paragraph(escape(t),styles['Heading1' if level==1 else 'Heading2']))
def page():story.append(PageBreak())
def table(headers,rows,widths=None,caption=None):
    if caption:
        p(caption,True);story[-1].keepWithNext=True
    data=[[Paragraph(escape(str(x)),styles['SmallPaper']) for x in row] for row in [headers]+rows]
    t=Table(data,colWidths=widths or [W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9edf0')),('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.5,colors.black),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.extend([t,Spacer(1,10)]);md.append('| '+' | '.join(headers)+' |\n|'+'---|'*len(headers)+'\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n')
def fig(obj,num,caption,src):
    if isinstance(obj,Drawing):
        renderPDF.drawToFile(obj,str(FIG/f'figure_{num:02d}.pdf'))
        story.append(obj); link=f'figures/figure_{num:02d}.pdf'
    else:
        path=ROOT/obj; target=FIG/f'figure_{num:02d}.png';shutil.copy2(path,target)
        from PIL import Image as PILImage
        iw,ih=PILImage.open(path).size
        scale=min(W/iw,590/ih);story.append(Image(str(path),width=iw*scale,height=ih*scale));link=f'figures/{target.name}'
    txt=f'Figure {num}. {caption}'
    story.append(Paragraph(escape(txt),styles['CaptionPaper']));md.append(f'![{txt}]({link})\n');figure_sources[str(num)]={'caption':caption,'source':src}
def box(d,x,y,w,ht,lines,fill='#edf2f5'):
    d.add(Rect(x,y,w,ht,fillColor=colors.HexColor(fill),strokeColor=colors.HexColor('#526575'),strokeWidth=.6))
    for j,s in enumerate(lines):d.add(String(x+w/2,y+ht/2+(len(lines)-1)*6-j*12,s,fontName='Helvetica',fontSize=8.5,textAnchor='middle'))
def arrow(d,x1,y1,x2,y2):
    d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor('#526575'),strokeWidth=1))
    if x1==x2:d.add(Polygon([x2,y2,x2-3,y2+6,x2+3,y2+6],fillColor=colors.HexColor('#526575'),strokeColor=None))
    else:d.add(Polygon([x2,y2,x2-6,y2-3,x2-6,y2+3],fillColor=colors.HexColor('#526575'),strokeColor=None))
def population():
    d=Drawing(W,178)
    for i,n in enumerate(names):box(d,i*165,100,145,64,[n,'41 instruments','40 company groups'])
    arrow(d,145,132,165,132);arrow(d,310,132,330,132)
    for x,s in [(0,'APN exits; GLN enters'),(245,'MNP exits; PAN enters')]:d.add(String(x+110,80,s,fontName='Helvetica',fontSize=8,textAnchor='middle'))
    box(d,35,8,405,48,['123 instrument-date rows; 43 distinct tickers','40 continuing at each adjacent pair; 39 present throughout'])
    return d
def pipeline():
    d=Drawing(W,345)
    items=[['Dated index members and source workbook','41 instrument rows at each decision date'],['Corporate actions, imputation and eight financial features','June 2025 constants; original raw values preserved'],['MinMax scaling fitted on June 2025 only','Same transform at December 2025 and June 2026'],['Independent UMAP and agglomerative fit at each date','2 dimensions; 3 neighbours; min_dist 0.01; k=8'],['Evaluate both geometries and stochastic sensitivity','Scaled features and embedding; five seeds; cluster sizes'],['Jaccard and Hungarian alignment on continuing members','Separate entries and exits; profile changes; distance screen']]
    for i,ls in enumerate(items):
        y=292-i*57;box(d,30,y,415,46,ls)
        if i<5:arrow(d,W/2,y,W/2,y-11)
    return d
def quality():
    d=Drawing(W,230); cols=['#355f82','#a7bfd2','#a65035','#d7b19d']
    for j,(label,c) in enumerate(zip(['UMAP features','UMAP embedding','t-SNE features','t-SNE embedding'],cols)):
        x=8+(j%2)*238;y=218-(j//2)*14;d.add(Rect(x,y-2,9,9,fillColor=colors.HexColor(c),strokeColor=None));d.add(String(x+14,y,label,fontName='Helvetica',fontSize=8))
    for i,date in enumerate(dates):
        um=primary[i];ts=next(x for x in comparison if x['decision_date']==date and x['model']=='tsne_hierarchical')
        vals=[float(um['silhouette_features']),float(um['silhouette_embedding']),float(ts['silhouette_features']),float(ts['silhouette_embedding'])]
        base=38+i*151
        for j,v in enumerate(vals):
            x=base+j*24;ht=v*190;d.add(Rect(x,32,19,ht,fillColor=colors.HexColor(cols[j]),strokeColor=None));d.add(String(x+9.5,36+ht,f'{v:.3f}',fontName='Helvetica',fontSize=7,textAnchor='middle'))
        d.add(String(base+44,14,names[i],fontName='Helvetica',fontSize=8,textAnchor='middle'))
    d.add(Line(28,32,465,32,strokeColor=colors.black));return d
def heatmap(date):
    d=Drawing(W,230);sub=[x for x in profiles if x['decision_date']==date];clusters=sorted({int(x['cluster']) for x in sub}); feats=list(dict.fromkeys(x['feature'] for x in sub)); labels=['Return','Beta','Volatility','Div yield','Earn yield','Log cap','Log rev/cap','Log turnover']
    for j,s in enumerate(labels):d.add(String(80+j*48,211,s,fontName='Helvetica',fontSize=6.8,textAnchor='middle'))
    for i,c in enumerate(clusters):
        rr=[x for x in sub if int(x['cluster'])==c];d.add(String(7,188-i*23,f'C{c} (n={rr[0]["n"]})',fontName='Helvetica',fontSize=8))
        for j,f in enumerate(feats):
            v=float(next(x for x in rr if x['feature']==f)['deviation_scaled']);a=min(abs(v)/1.5,1)
            rgb=(1,.97-a*.62,.96-a*.64) if v>=0 else (.95-a*.68,.97-a*.45,1)
            d.add(Rect(56+j*48,181-i*23,48,23,fillColor=colors.Color(*rgb),strokeColor=colors.white,strokeWidth=.5));d.add(String(80+j*48,189-i*23,f'{v:+.2f}',fontName='Helvetica',fontSize=7.5,textAnchor='middle'))
    d.add(String(56,12,'Red positive; blue negative; common colour limits -1.5 to +1.5.',fontName='Helvetica',fontSize=8));return d

title='Interpretable Unsupervised Learning for JSE Top 40 Equities'
subtitle='A Repeated Cross Sectional Study of Financial Peer Groups'
md.extend(['# '+title+'\n',subtitle+'\n'])
story.extend([Paragraph(title,styles['TitlePaper']),Paragraph(subtitle,styles['SubtitlePaper'])])
p('A. Nxitywa',True);p('15 November 2026',True)
h('Abstract')
p('We investigate whether interpretable unsupervised learning can describe financial peer groups and their changing composition across three FTSE/JSE Top 40 cross-sections: 30 June 2025, 31 December 2025 and 30 June 2026. Each date contains 41 listed instruments representing 40 company groups. The union contains 43 securities, with 39 present throughout; the 123 instrument-date records are therefore dependent repeated observations. Eight pilot-informed financial characteristics are scaled against June 2025. At each date, a separately refitted two-dimensional UMAP representation is clustered using average linkage and Manhattan distance into eight groups, with parameters held fixed and five random seeds examined. Embedding silhouettes are 0.685, 0.638 and 0.721, whereas the same partitions score 0.151, 0.124 and 0.267 in the scaled financial features. Hungarian matching of continuing-member Jaccard overlaps identifies 15 and 11 aligned membership changes among 40 continuing securities in successive periods. Of 39 complete histories, 19 retain their aligned group and 20 shift at least once. Direct median profiles, company feature changes and qualified surrogate explanations describe these movements. Retrospective inputs, two December singleton groups, representation sensitivity and absent external validation constrain economic interpretation. The contribution is a reproducible screening and reporting procedure, rather than evidence of return predictability or confirmed structural anomalies.')
p('Keywords: JSE Top 40; repeated cross-sections; UMAP; hierarchical clustering; peer groups; cluster alignment; interpretability.',True)
h('1 Introduction')
# Preserve the supplied introduction, with paragraph boundaries recovered from sentence starts.
intro=clean(intro)
for token in ['Much of the machine learning','This article studies','The approach proposed','The article is positioned','Section 2 reviews']:
    intro=intro.replace(token,'\n\n'+token)
for para in intro.split('\n\n'):
    if para.strip():p(para)
h('2 Related Work')
# Retain the full supplied literature discussion, correcting only current-study sector status.
related=related.replace('Here, official JSE sector classification plays that role.','In the present study, legacy sector labels provide descriptive context, but are not independently verified historical ground truth.')
for marker,body in re.findall(r'(2\.[12] [^\n]+)\n(.*?)(?=2\.[12] |\Z)',related,re.S):
    h(marker,2);body=clean(body)
    body=body.replace('Here, official JSE sector classification plays that role.','In the present study, legacy sector labels provide descriptive context, but are not independently verified historical ground truth.')
    for tok in ['Clustering also appears','Cluster validation is difficult','Interpretability is particularly','The South African equity']:
        body=body.replace(tok,'\n\n'+tok)
    for para in body.split('\n\n'):
        if para.strip():p(para)

h('3 Study population and financial inputs')
h('3.1 Three decision dates and effective index membership',2)
p('The unit of analysis is a listed instrument at a decision date. We use 30 June 2025, 31 December 2025 and 30 June 2026 as three distinct cross-sections. Each contains 41 security lines because Investec Limited (INL) and Investec plc (INP) are separate listed instruments of one dual-listed economic group. Both are retained. Thus 41 instruments correspond to 40 company groups, rather than an accidental inclusion of a forty-first company.')
table(['Decision date','Instruments','Groups','Change since preceding date'],[[names[0],41,40,'Initial observed population'],[names[1],41,40,'GLN admitted; APN removed'],[names[2],41,40,'PAN admitted; MNP removed']],[100,64,54,257], 'Table 1. Date-specific population reconciliation.')
p('The June 2025 review introduced Northam Platinum and removed Glencore before the first observation. The September review reversed Glencore\'s absence and removed Aspen. There was no recorded Top 40 change in December 2025. Pan African Resources replaced Mondi in March 2026, with no recorded change in June 2026. These events are stored with their effective dates and evidence in index_changes.csv. The validator checks both the first-date review and subsequent transitions rather than hard-coding a list of expected ticker changes.')
fig(population(),1,'The complete date-specific populations and the restricted longitudinal population. Entries and exits are counted independently from cluster movement.','data/reference/index_changes.csv; results/longitudinal/umap/cluster_histories.csv')
p('Across dates there are 123 rows and 43 distinct tickers. Each adjacent pair shares 40 instruments, while 39 appear at all three dates. Aspen has only the first observation, Mondi the first two, Glencore the last two and Pan African only the last. A complete-history figure therefore contains 39 instruments; this is not the index size. Adjacent trailing annual market windows overlap by six months, many fundamentals recur, and the instruments themselves repeat. Neither rows nor dates are treated as independent replications.')
h('3.2 Financial representation and measurement',2)
p('The eight-feature representation is a pilot-informed revision intended to reduce the sensitivity of share-count and EPS inputs to share subdivisions and to reduce skew in size measures. It is not the eleven-variable representation in the original SACJ manuscript, nor a direct replication of its 2023-2024 sample. The archived ten-variable representation is an intermediate reference; it also differs from that original experiment.')
table(['Feature','Construction and interpretation'],[
['One-year return','Trailing split-adjusted price change; cash dividends excluded.'],['Beta','Slope relative to daily J203 market returns over the trailing year.'],['Annualised volatility','Daily-return sample standard deviation multiplied by the square root of 252.'],['Dividend yield','Trailing dividends relative to the security close, under the recorded currency convention.'],['Earnings yield','EPS / close; clipped at June 2025 first and ninety-ninth percentiles.'],['Log market capitalisation','Base-10 logarithm of rand line-specific market capitalisation.'],['Log revenue / capitalisation','Base-10 logarithm of revenue divided by market value; group totals for Investec.'],['Log share turnover','Base-10 logarithm of corrected average daily JSE volume / line-specific shares.']],[112,363], 'Table 2. Variables used by the current study model. Sector, company and ticker identify or describe observations and are excluded from fitting.')
p('For a subdivision factor q, price and EPS divide by q and shares and consistently measured share volume multiply by q. Earnings yield, market capitalisation, revenue/capitalisation and turnover are consequently unchanged under a consistent restatement. This algebraic property motivates the representation; it does not certify historical source consistency. In particular, trailing volume that mixes pre- and post-subdivision units requires a correction before taking the ratio.')
h('3.3 Corrections and missing observations',2)
p('Original source values remain unchanged in the input CSV and provenance workbook. The feature pipeline applies documented corrections from separate reference tables. Naspers began trading on the five-for-one share basis on 1 October 2025; its register date was 6 October. Its December 2025 average daily volume is restated from 800,935 mixed-basis units to 2,140,029 post-subdivision shares, and the June 2026 figure from 1,502,524 to 1,847,639. These are corrections to the trailing-volume units, not additional trading observations.')
p('Both Investec rows originally carry a combined share count. Issuer disclosures from June 2024 and June 2026 allocate that reconstructed total between the two lines. December 2025 uses the midpoint of the disclosed line fractions. Each line has its own market capitalisation and turnover, while revenue relative to market value uses combined issuer revenue and combined market value because each line represents a claim on the group. The December interpolation and the reconstructed combined total remain limitations.')
p('Reinet has no usable raw revenue or EPS at any date, and Anglo American lacks usable volume at the first two dates. Missing model values use June 2025 medians. A derived feature depending on an imputed source is imputed using the June 2025 median of that derived feature, rather than treating the imputed raw value as observed. No instrument is removed because of these missing inputs. The earnings-yield clipping limits are likewise fitted on June 2025 and then held fixed.')
p('Market measures are rebuilt from retrospective vendor histories. Dated issuer releases support revenue and diluted EPS for 120 of 123 rows, with dated currency conversions, but shares and market capitalisation are reconstructed. Sector is a legacy eight-category directory label. JSE-only volume understates total liquidity for issuers whose principal market is overseas; revenue is also not defined uniformly across sectors. The data are not certified strict point-in-time observations.')

h('4 Repeated cross sectional methods')
fig(pipeline(),2,'Study workflow. A common preprocessing reference is carried forward, while the embedding and clusters are refitted independently at each date. The alignment stage compares sets of continuing members, rather than arbitrary numeric labels.','configs/study.json; top40/features.py; top40/study.py; top40/temporal.py')
h('4.1 Scaling and independent fitting',2)
p('For feature j, let a(j) and b(j) be its June 2025 minimum and maximum after the declared imputation and transformations. The scaled value at any date is the difference between the observed value and a(j), divided by b(j) minus a(j). Scaling is not clipped. A later observation can therefore exceed one or fall below zero. This preserves a reference scale and avoids using later observations to estimate preprocessing constants, but does not prevent later variance being dominated by one feature.')
p('For each date and each seed in 42-46, UMAP (McInnes et al., 2018) learns a new two-dimensional representation using three neighbours, minimum distance 0.01, Euclidean input distance and one computational job. Agglomerative clustering then joins groups bottom-up with average linkage under Manhattan distance on the two coordinates, stopping at eight groups. Seed 42 supplies the representative partition and figures. The five fits quantify stochastic sensitivity; their outputs are not pooled into an enlarged sample or a consensus partition.')
table(['Stage','Fixed specification'],[['Scaling','MinMax; fitted 30 June 2025; clip=False'],['UMAP','2 components; n_neighbors=3; min_dist=0.01; Euclidean; n_jobs=1'],['Agglomerative clustering','8 groups; average linkage; Manhattan metric on UMAP coordinates'],['Seeds','42, 43, 44, 45, 46; representative partition 42'],['Software','umap-learn 0.5.12; scikit-learn 1.6.1'],['Sensitivity','Cluster counts 2-12; alternative feature representations'],['Historical comparator','t-SNE: perplexity 5; learning rate 10; 300 iterations; random initialisation; average-Manhattan hierarchy, k=8']],[115,360],'Table 3. The study model is distinct from the generic UMAP comparator, which uses ten neighbours and minimum distance 0.1 in the broader comparison grid.')
p('Three neighbours and minimum distance 0.01 were author-specified after exploratory June 2025 analysis. An earlier 36-combination grid preferred minimum distance 0.1. Eight groups, average linkage and Manhattan distance follow the original paper. These settings are pilot-informed, not prospectively registered. Later-date fitting holds the recipe fixed but refits the representation and labels, so the results do not measure out-of-sample predictive performance.')
h('4.2 Quality in two geometries and seed agreement',2)
p('Each representative partition is evaluated in both the two-dimensional representation and the eight-dimensional scaled financial space. Silhouette uses within-cluster and nearest-other-cluster Euclidean distances; larger values indicate greater separation. Davies-Bouldin compares within-group dispersion with distances between group centres; smaller values indicate more compact separation. The evaluation distance is Euclidean even though the hierarchy uses Manhattan distance. The two geometries answer different questions and are reported together. DBSCAN comparator scores exclude noise and must be read with coverage.')
p('Within each date, five seeds give ten pairwise adjusted Rand indices (ARI). ARI is label-invariant and adjusted for chance agreement; it is not an accuracy against a known financial truth. Its mean summarises variability induced by the embedding seed, conditional on the fixed inputs. The five-seed mean is not a confidence interval, bootstrap, or independent null distribution for temporal changes. Cluster size ranges and singleton counts accompany the quality scores.')
h('4.3 Matching clusters between dates',2)
p('Let C be the instruments observed at both adjacent dates. For each earlier group A and later group B, restrict both to C and calculate their Jaccard similarity as the size of their intersection divided by the size of their union. A Hungarian assignment chooses a one-to-one matching that maximises the sum of these similarities. An assigned pair with zero intersection is not retained as a match; that later cluster receives a fresh identifier. Retired identifiers are never reused for unrelated groups.')
table(['Step','Operation'],[['1','Partition each date independently; retain ticker as the stable security key.'],['2','Identify continuing members, entries and exits from date-specific populations.'],['3','Build the cluster-by-cluster Jaccard matrix using continuing members only.'],['4','Maximise total Jaccard overlap with a one-to-one Hungarian assignment.'],['5','Transfer earlier labels only for positive-overlap matches; issue new labels otherwise.'],['6','Count a switch only when a continuing instrument has different aligned labels.'],['7','Chain the matches for complete three-date histories; leave membership gaps missing.']],[45,430], 'Table 4. Reproducible cross-date matching procedure implemented in top40/temporal.py.')
p('Temporal ARI is computed directly on the two partitions of continuing members and does not depend on the label matching. Switch counts do depend on matching. A global one-to-one assignment cannot fully represent a split or merger, so the overlap matrix and named member histories remain essential. A label that survives a match is a descriptive continuity identifier, not an invariant economic factor. We use "stable" only for a complete history whose aligned label never changes, and "shifted" when it changes at least once. These terms do not imply unchanged or changed business fundamentals.')
h('4.4 Direct profiles and surrogate interpretation',2)
p('For each cluster, we subtract the same-date cross-sectional median from the cluster median for each of the eight scaled features. Positive and negative deviations describe the group relative to its contemporaries in June 2025 reference units. For an instrument that changes group, the reporting tables retain its feature changes, old and new peers, peer retention and destination profile. These directly calculated descriptions form the primary interpretation.')
p('An XGBoost classifier is fitted to the unscaled engineered features to reproduce the cluster labels: 150 trees, maximum depth two, learning rate 0.05, full row and column sampling, one job and a multiclass probability objective. Tree SHAP explains the surrogate raw class margins using tree-path-dependent perturbation. Saved attributions are checked for additivity with a maximum tolerance of 0.0001. These attributions explain the surrogate, rather than the UMAP or hierarchy directly, and do not establish causes of group membership.')
p('Where the smallest cluster contains at least two members, stratified cross-validation uses the smaller of five folds and the minimum cluster size, with shuffling and the representative seed. Singleton clusters make this out-of-fold fidelity estimate unavailable under the implemented procedure. The measured fidelity is agreement with algorithm-generated labels, not accuracy in forecasting a financial outcome. A model that reproduces every training label can still have inadequate fidelity on held-out instruments.')
h('4.5 Separate financial distance screen',2)
p('The screen computes squared Mahalanobis distance from the same-date mean in the eight scaled features using the sample covariance matrix. It is not the predictive Hotelling statistic for a new observation. Under independent multivariate normal sampling, an individual internal distance D squared, multiplied by n divided by (n minus one) squared, has a Beta reference with shape parameters p/2 and (n minus p minus one)/2. Here n=41, p=8 and the nominal upper-tail level is 0.05. A singular or excessively ill-conditioned covariance produces an unestimable result rather than a flag.')
p('Those assumptions are doubtful for heterogeneous, overlapping equity cross-sections with clipped and imputed financial variables. The threshold therefore provides a descriptive ranking screen, not calibrated significance or a multiple-testing-controlled anomaly discovery procedure. Cluster isolation, sector divergence, aligned membership movement and financial distance are separate observations. No combined score converts them into a confirmed economic anomaly.')

h('5 Empirical results')
h('5.1 Cluster quality and the historical comparator',2)
table(['Date','Feature S','Feature DB','Map S','Map DB','Seed ARI','Size range'],[[names[i]]+[f'{float(r[k]):.3f}' for k in ['silhouette_features','davies_bouldin_features','silhouette_embedding','davies_bouldin_embedding','mean_seed_ari']]+[r['smallest_cluster']+'-'+r['largest_cluster']] for i,r in enumerate(primary)],[94,61,64,56,56,64,80], 'Table 5. Representative UMAP partition quality, mean pairwise five-seed ARI and cluster size ranges. S is silhouette; DB is Davies-Bouldin. All 41 instruments are included.')
p('The largest quality distinction is between geometries: financial-feature silhouettes range from 0.124 to 0.267, whereas map silhouettes range from 0.638 to 0.721. In December, the representative partition contains two singletons; neither June partition has a singleton. High map compactness is therefore compatible with weak financial separation and small or isolated groups. The mean seed ARI is highest in December (0.892), despite those singletons, and lowest in June 2026 (0.738).')
p('The historical t-SNE recipe has map silhouettes 0.532, 0.589 and 0.656. Its financial silhouettes are 0.195, 0.240 and 0.255. Thus UMAP produces the higher map silhouette at every date, while t-SNE scores higher in financial space at the first two dates. UMAP is only slightly higher in financial space in June 2026. This does not support a general claim of superior financial grouping or a direct comparison with the original manuscript\'s different sample and features.')
fig(quality(),3,'Silhouettes for the UMAP study model and the historical t-SNE/hierarchical recipe applied to the same current eight-feature inputs. Darker bars evaluate the financial features; lighter bars evaluate the embedding. Both recipes use eight clusters.','results/primary_model_summary.csv; results/model_comparison.csv')
h('5.2 Continuing members and complete histories',2)
table(['Period','Continue','Entry / exit','Changed','Unchanged','ARI','NMI'],[['Jun-Dec 2025',40,'1 / 1','15 (37.5%)','25 (62.5%)','0.377','0.646'],['Dec 2025-Jun 2026',40,'1 / 1','11 (27.5%)','29 (72.5%)','0.590','0.751']],[111,51,65,75,75,49,49], 'Table 6. Temporal comparison among the 40 continuing instruments in each adjacent pair. Entries and exits are excluded from changed and unchanged counts.')
p('The second pair is more similar by temporal ARI and has fewer aligned switches, but two transitions are insufficient to establish a trend or a statistically significant reduction in change. Across the 39 complete histories, 19 (48.7%) keep an aligned label and 20 (51.3%) change at least once. There are 26 adjacent switch events, rather than 26 distinct changing securities. Five complete-history instruments switch in both periods; 15 switch once. Those histories account for 25 switch events; Mondi contributes the remaining first-period event before its subsequent exit. Membership gaps are neither stability nor change.')
stable=[r['ticker'] for r in hist if r['stability_status']=='stable'];shifted=[r['ticker'] for r in hist if r['stability_status']=='shifted'];twice=[r['ticker'] for r in hist if r['observed_all_dates']=='True' and r[dates[0]]!=r[dates[1]] and r[dates[1]]!=r[dates[2]]]
assert len(stable)==19 and len(shifted)==20 and len(twice)==5
p('The 19 stable histories are '+', '.join(stable)+'. The 20 shifted histories are '+', '.join(shifted)+'. The five instruments changing in both adjacent periods are '+', '.join(twice)+'. These named outcomes allow the counts to be checked against the saved memberships and prevent a single aggregate statistic from concealing different histories.')
fig('results/longitudinal/umap/cluster_flows.png',4,'Aligned group membership for the 39 instruments observed at all three dates. Bold tickers change aligned group at least once. The per-date quality annotations refer to the full 41-instrument partition. APN, MNP, GLN and PAN are omitted only from this complete-history view. Vertical position is layout; colours identify aligned groups, not sectors.','results/longitudinal/umap/cluster_flows.png; results/longitudinal/umap/cluster_histories.csv')
h('5.3 Overlap structure and interpretation of switches',2)
fig('results/longitudinal/umap/jaccard.png',5,'Continuing-member Jaccard similarities underlying cross-date matching. Similarity is computed on 40 continuing securities in each period; index entrants and exits do not create artificial peer-group switches. Positive-overlap assignments transfer labels, while zero-overlap groups receive new identifiers.','results/longitudinal/umap/jaccard.png; top40/temporal.py')
p('The flow diagram is a compact history summary, whereas the overlap matrices expose continuity strength. For example, a larger first-period matched group has Jaccard overlap about 0.62, while some other matches are substantially weaker. The matching maximises the total across all pairs, so it should not be interpreted as proving that each matched group has strong continuity. Entry, exit, splitting and regrouping are visible in the accompanying member tables.')
p('Absa and Old Mutual move from aligned group 1 to group 5 and then return to group 1. Their paths illustrate why two adjacent switch events do not imply persistent movement away from an original peer set. Reinet follows 6 to 7 to 2, with fundamentals imputed at every date. Naspers follows 7 to 7 to 9 after the documented share-basis corrections; its observed path remains conditional on those corrections and the embedding. These cases require different substantive follow-up despite sharing the generic label "shifted".')
h('5.4 Financial profiles at each decision date',2)
p('Figures 6-8 use the aligned labels from the longitudinal outputs, rather than the raw local cluster numbers in independent fits. They report cluster median minus same-date median for all eight inputs. A positive cell identifies a relatively high feature on the frozen scale; it is not a coefficient, effect size in returns or SHAP attribution. The row counts refer to the full date-specific population, including partial histories.')
for i,date in enumerate(dates):
    fig(heatmap(date),6+i,f'{names[i]} aligned-cluster median deviations. Values are in June 2025 MinMax units. Row labels give aligned cluster identifiers and instrument counts; missing identifiers reflect retired groups, not missing observations.','results/longitudinal/umap/moves/cluster_profiles.csv')
p('A precious-metals grouping illustrates changing composition rather than a fixed sector partition. AngloGold Ashanti, Gold Fields and Harmony join the group containing Impala Platinum, Northam and Sibanye-Stillwater by December 2025, together with Valterra. That December group has relatively high trailing return, beta and volatility. Its main membership persists in June 2026, when newly admitted Pan African Resources is included. This is a description of saved features and memberships, not evidence that commodity prices caused a structural break.')
p('ANH, BHG and CFR remain together throughout. BTI joins their aligned group in December 2025, and PRX leaves by June 2026. Their June 2026 profile combines high log market capitalisation with low JSE share turnover. That contrast is consistent with the recorded feature geometry but requires caution for internationally traded firms: low JSE turnover need not mean low total market liquidity. The financial profiles supply hypotheses for analyst investigation without declaring inherited sectors incorrect.')
h('5.5 Representation sensitivity and cluster count',2)
dom=readcsv('results/feature_audit/dominance.csv'); cross=readcsv('results/feature_audit/cross_set_agreement.csv')
rows=[]
for date,name in zip(dates,names):
    r=next(x for x in dom if x['decision_date']==date and x['feature_set']=='invariant8');c=next(x for x in cross if x['decision_date']==date and x['recipe']=='umap' and x['feature_set_a']=='original10' and x['feature_set_b']=='invariant8')
    rows.append([name,r['top_feature_label'],f'{float(r["top_variance_share"])*100:.1f}%',f'{float(r["max_scaled_value"]):.3f}',f'{float(c["ari"]):.3f}'])
table(['Date','Dominant feature','Variance share','Max scaled','Cross-set ARI'],rows,[100,110,85,85,95], 'Table 7. Scale drift in invariant8 and UMAP agreement with the archived original10 representation. An even variance allocation would be 12.5%. Cross-set ARI compares partitions, not the magnitude of silhouette values across feature spaces.')
p('Return accounts for 52.5% of scaled variance in December 2025, compared with an even eight-variable share of 12.5%. The maximum scaled value reaches 2.847. The frozen reference preserves temporal comparability of units but does not preserve feature influence. Consequently, the weaker December financial silhouette and changing peer groups can reflect shifts in the relative geometry induced by preprocessing, as well as changes in firms\' measured financial attributes.')
p('Feature alternatives also affect histories. UMAP yields 20 stable and 19 shifted complete histories under original10, 16 and 23 under logsize10, 19 and 20 under invariant8, and 14 and 25 under market5. Each uses the same 39 complete-history instruments. These are diagnostic alternatives rather than independently validated models. Their silhouette and Davies-Bouldin values are computed in different feature spaces and cannot be ranked as though they shared identical units or inputs.')
fig('results/models/umap/cluster_count_sensitivity.png',9,'Sensitivity to cluster count from two to twelve under the study representation. Eight clusters remain the historical reference choice. Inspect financial-space quality together with minimum group size and seed agreement; the plot does not establish a uniquely correct number of economic groups.','results/models/umap/cluster_count_sensitivity.png')
h('5.6 Surrogate fidelity and descriptive distance flags',2)
table(['Date','Training fidelity','Out-of-fold fidelity','Singleton groups'],[[names[0],'1.000','0.439',0],[names[1],'1.000','Not estimable',2],[names[2],'1.000','0.707',0]],[110,115,135,115], 'Table 8. Surrogate agreement with representative cluster labels. Where estimated, the minimum group size of two limits stratified cross-validation to two folds.')
p('Perfect reproduction of training labels does not imply reliable explanation. The June 2025 held-out fidelity is only 43.9%, compared with 70.7% in June 2026; December cannot be estimated with the implemented stratified scheme because of two singletons. These values justify using the direct median profiles and feature histories as the principal interpretation. SHAP may describe the fitted surrogate but cannot establish why an instrument moved or validate the economic relevance of that movement.')
table(['Date','Flagged instruments','Count'],[[names[0],'APN, BHG, BTI, SOL, VAL',5],[names[1],'AGL, BHG, BTI, SOL, SSW',5],[names[2],'GLN, PAN, SOL, SSW',4]],[110,320,45], 'Table 9. Separate same-date Mahalanobis distance screen at nominal alpha 0.05. These are descriptive flags, not significant economic anomalies.')
p('Fourteen instrument-date observations are flagged, spanning nine distinct tickers. Sasol is flagged at all three dates; BHG and BTI at the first two; SSW at the last two. APN and PAN have incomplete eligibility histories, so their unobserved dates cannot be recorded as an absence of a flag. AGL also carries imputed volume. These differences prevent a simple count of repeated flags from establishing persistence of an economic anomaly. No forecast-return test, external event corroboration or calibrated transition null is available for this run.')

h('6 Discussion')
p('The central finding is that high visual separation is not equivalent to strong financial peer structure. A small UMAP neighbourhood and low minimum distance make compact local islands possible, yet the financial-space silhouettes are modest. The historical t-SNE comparator confirms that the model with a stronger map silhouette can have a weaker silhouette on the financial characteristics themselves. Model evaluation must therefore name the geometry and report group sizes, rather than rely on the appearance of a coloured plot.')
p('The repeated design adds a dated universe, a reproducible alignment rule and company-level histories to the original single-window study. It separates index reconstitution from movement among continuing members, and prevents arbitrary cluster numbering from producing spurious transitions. However, a continuing aligned label is only a convenient description. A one-to-one matching compresses cluster splits and mergers, and a switch can be induced by movements in other firms, local embedding variability or preprocessing influence without a large change in the focal firm.')
p('The 19 stable and 20 shifted histories are consequently conditional results. The seed sensitivity measures one part of uncertainty, not a probability that a switch is real. Shared observations, overlapping annual windows, repeated issuer accounts, common market shocks and the two Investec lines also limit independence. No inferential procedure in this study treats the 123 rows as 123 independently sampled companies, or the five seeds as five new datasets.')
p('Feature corrections are part of the empirical specification. Correcting subdivisions and separating dual-listed share counts improves interpretability of the chosen ratios, but reconstructed shares, interpolated line fractions, JSE-only liquidity and sector-dependent accounting definitions remain consequential. Alternate feature results show that the history labels change when the geometry changes. "Share-basis invariant" describes the algebra of consistently measured variables; it is not a certificate that historical sources are free of error.')
p('The present contribution is a transparent process for repeated financial screening. A future confirmatory design should freeze inputs and settings before a new decision date, certify as-of data availability, calibrate transitions with suitable input perturbations and compare subsequent within-cluster return co-movement against sector-defined and matched random groups. It should also examine sensitivity to the alignment objective, cluster count, sampling unit and preprocessing policy. These are proposed validation steps; no results from them are claimed here.')
h('7 Conclusion')
p('We extend an interpretable equity-clustering study to three repeated FTSE/JSE Top 40 cross-sections, each containing 41 listed instruments and 40 company groups. The union has 43 instruments and 39 complete histories. A fixed, pilot-informed UMAP and agglomerative recipe yields high map silhouettes but weaker financial-feature separation. Continuing-member Jaccard alignment identifies 15 and 11 adjacent switches, with 19 complete histories retaining their group and 20 shifting at least once. Profile tables, named histories, sensitivity diagnostics and fidelity-qualified surrogate outputs make these findings inspectable. The evidence supports descriptive screening and prioritisation of further investigation. It does not establish causal structural change, return predictability, or validated economic anomalies.')

h('References')
# Reference starts are identified from the preserved bibliography; all 22 entries remain.
starts=['Mohiuddin Ahmed, Abdun','Mohiuddin Ahmed, Nazim','Olatz Arbelaitz,','Ana Barradas,','James Ming Chen,','Min-Soo Cheong,','Salvatore Cuomo,','David L. Davies','Derek Greene,','Chao Han,','Carlos León,','T. Lim and','Leland McInnes,','Luke Merrick','B. B. Nair,','Mohsen Nourahmadi,','Peter J. Rousseeuw.','Benedek Rozemberczki,','R. Ünlü','Lucas Vendramin,']
refs=clean(refs).replace('\\_','_')
for s in starts:refs=refs.replace(s,'\n\n'+s)
reference_list=[x.strip() for x in refs.split('\n\n') if x.strip()]
assert len(reference_list)==20,len(reference_list)
for ref in reference_list:
    for word in ['Future','Pattern','Analytics','IEEE','Expert','European','Quantitative','International','Iranian','arXiv','Statistical']:
        ref=ref.replace('.'+word,'. '+word)
    ref=ref.replace('In2017','In 2017').replace('InMachine','In Machine').replace('ofLecture','of Lecture').replace('TPAMI. 1979','TPAMI.1979').replace('10.1080/ 146','10.1080/146')
    p(ref,True)
h('Appendix A Reproducibility and evidence')
p('Repository: https://github.com/mygitAN/JSE-Top-40-Clustering. This manuscript checks the saved numerical archive from run 20261115T062631-0c09819ce3c0, generated from clean implementation commit 98549c660edd410fd74936a03faecadd01f6067b. The later repository commit 28c2ccf7a9eab7121b1c8ea9852bbaf22758bd32 adds stricter index-review validation and its tests; it is not misreported as the implementation commit that generated those numerical results. Every file listed in results/manifest.json was checksum-verified during manuscript preparation.',True)
p('The primary evidence files are primary_model_summary.csv, model_comparison.csv, seed_agreement.csv, surrogate_fidelity.csv and temporal_agreement.csv under results/. Complete and partial histories are in longitudinal/umap/cluster_histories.csv. The financial profiles in Figures 6-8 come from longitudinal/umap/moves/cluster_profiles.csv and use aligned labels. Exported single-date feature_profile.png files use raw local labels, so those labels must not be substituted directly into longitudinal interpretation.',True)
p('Figures 1-3 and 6-8 are manuscript drawings derived from the declared configuration and saved tables. Figures 4, 5 and 9 reproduce existing repository diagrams without changing their numerical content. The figure provenance file records each source. Numerical summaries retain all date-specific members; only Figure 4 restricts the population to complete histories. No model rerun or new empirical claim is implied by redrawing a figure.',True)
p('Population evidence is recorded in data/reference/index_changes.csv. The June 2025 and December 2025 rows link quarterly review notices; September 2025 and March 2026 link reproduced SENS announcements; June 2026 links a fund factsheet. The supplied revised paper records that not all official notices were directly inspected and that some no-change evidence is secondary. Automated consistency with the recorded reviews does not remove those source-certification limits.',True)
p('The source CSV and workbook preserve the retrospective input evidence. Corporate-action, volume and dual-listed-share corrections remain in separate reference files. Reproduction commands are python -m top40.data; python -m top40.export --check; python -m unittest discover -s tests -t .; and python -m top40. The configuration fixes invariant8, five seeds and k=8. The immutable run archive and its manifest identify the exact data and implementation used.',True)

def footer(c,doc):
    c.setFont('Times-Roman',9);c.drawCentredString(A4[0]/2,30,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'JSE_Top40_Three_Cross_Section_Paper_20261115.pdf'),pagesize=A4,rightMargin=60,leftMargin=60,topMargin=52,bottomMargin=48,title=title,author='A. Nxitywa')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'JSE_Top40_Three_Cross_Section_Paper_20261115.md').write_text('\n'.join(md),encoding='utf-8')
(OUT/'figure_provenance.json').write_text(json.dumps({'numerical_run':manifest['run_id'],'implementation_commit':manifest['git_commit'],'figures':figure_sources},indent=2),encoding='utf-8')
print('Created manuscript; verified',len(manifest['files']),'result checksums; retained',len(reference_list),'references')

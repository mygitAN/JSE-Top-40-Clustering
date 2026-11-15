from pathlib import Path
p=Path('tmp/paper/build_paper.py');s=p.read_text(encoding='utf-8')
a=s.index("page()\nfig('results/longitudinal/umap/cluster_flows.png")
b=s.index("h('5.2 Continuing",a)
flow=s[a:b].replace('page()\n','',1)
s=s[:a]+s[b:]
pos=s.index("h('5.3 Overlap")
s=s[:pos]+flow+s[pos:]
s=s.replace('if caption:p(caption,True)','if caption:\n        p(caption,True);story[-1].keepWithNext=True')
p.write_text(s,encoding='utf-8')

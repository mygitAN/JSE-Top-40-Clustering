from pathlib import Path
p=Path('tmp/paper/build_paper.py');s=p.read_text(encoding='utf-8')
# Put the full-page membership figure ahead of the detailed membership subsection.
a=s.index("h('5.2 Continuing")
b=s.index("p('The second pair is",a)
region=s[a:b]
s=s[:a]+s[b:]
# region ends in a page break and the membership figure: move only the prose/table prefix.
split=region.index("page()\nfig('results/longitudinal/umap/cluster_flows.png")
prefix=region[:split];flow=region[split:]
pos=s.index("p('The second pair is")
s=s[:pos]+flow+prefix+s[pos:]
# Keep the comparator discussion with its metric table, ahead of the quality figure.
a=s.index("p('The historical t-SNE recipe has")
b=s.index("page()\nfig('results/longitudinal/umap/cluster_flows.png",a)
para=s[a:b];s=s[:a]+s[b:]
pos=s.index('fig(quality(),3')
s=s[:pos]+para+s[pos:]
s=s.replace("'Future','Analytics','IEEE'","'Future','Pattern','Analytics','IEEE'")
p.write_text(s,encoding='utf-8')

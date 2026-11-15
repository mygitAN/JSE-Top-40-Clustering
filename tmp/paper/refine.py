from pathlib import Path
p=Path('tmp/paper/build_paper.py')
s=p.read_text(encoding='utf-8')
a=s.index("p('The second pair is")
b=s.index("page()\nfig('results/longitudinal/umap/cluster_flows.png",a)
block=s[a:b];s=s[:a]+s[b:]
pos=s.index("page()\nh('5.3")
s=s[:pos]+block+s[pos+7:]
s=s.replace('UMAP learns a new two-dimensional','UMAP (McInnes et al., 2018) learns a new two-dimensional')
s=s.replace('for ref in reference_list:p(ref,True)', '''for ref in reference_list:
    for word in ['Future','Analytics','IEEE','Expert','European','Quantitative','International','Iranian','arXiv','Statistical']:
        ref=ref.replace('.'+word,'. '+word)
    ref=ref.replace('In2017','In 2017').replace('InMachine','In Machine').replace('ofLecture','of Lecture').replace('TPAMI. 1979','TPAMI.1979').replace('10.1080/ 146','10.1080/146')
    p(ref,True)''')
p.write_text(s,encoding='utf-8')

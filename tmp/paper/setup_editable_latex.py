from pathlib import Path
import re, shutil

root=Path.cwd(); source=root/'output/paper/latex'; target=root/'paper'
sections=target/'sections';sections.mkdir(exist_ok=True)
for filename in ['preamble.tex','references.tex','diagrams.tex','figure_sources.json']:
    destination=target/filename
    if destination.exists():raise FileExistsError(destination)
    shutil.copy2(source/filename,destination)
for dirname in ['figures','data']:
    (target/dirname).mkdir(exist_ok=True)
    for p in (source/dirname).iterdir():
        if p.suffix not in {'.tex','.csv'}:continue
        destination=target/dirname/p.name
        if destination.exists():raise FileExistsError(destination)
        shutil.copy2(p,destination)

text=(source/'main.tex').read_text(encoding='utf-8')
head,rest=text.split(r'\begin{abstract}',1)
rest=r'\begin{abstract}'+rest
matches=list(re.finditer(r'\\section\{([^}]+)\}',rest))
abstract=rest[:matches[0].start()].rstrip()
abstract=re.sub(r'\\FloatBarrier\s*$','',abstract).strip()
(sections/'00_abstract.tex').write_text(abstract+'\n',encoding='utf-8')
filenames=['01_introduction','02_related_work','03_population_and_inputs','04_methods','05_results','06_discussion','07_conclusion','appendix_reproducibility']
assert len(matches)==len(filenames)
for i,(m,filename) in enumerate(zip(matches,filenames)):
    segment=rest[m.start():matches[i+1].start() if i+1<len(matches) else len(rest)]
    segment=segment.replace(r'\FloatBarrier\input{references.tex}\appendix','')
    segment=segment.replace(r'\end{document}','')
    segment=re.sub(r'\\FloatBarrier\s*$','',segment).strip()
    (sections/(filename+'.tex')).write_text(segment+'\n',encoding='utf-8')
main=head.rstrip()+'\n\n% Edit prose in sections/ and native diagrams in figures/.\n'
main+=r'\input{sections/00_abstract.tex}'+'\n\n'
for filename in filenames[:-1]:
    main+=r'\FloatBarrier'+'\n'+r'\input{sections/'+filename+'.tex}'+'\n\n'
main+=r'''\FloatBarrier
\input{references.tex}
\appendix
\input{sections/appendix_reproducibility.tex}
\FloatBarrier
\end{document}
'''
assert not (target/'main.tex').exists()
(target/'main.tex').write_text(main,encoding='utf-8')
print('Created editable paper project; preserved existing make_figures.py and PDF figures.')

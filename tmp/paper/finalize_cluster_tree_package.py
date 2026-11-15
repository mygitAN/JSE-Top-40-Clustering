from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from pypdf import PdfReader
import json, re, shutil

root=Path.cwd();paper=root/'paper';out=root/'output/paper'
for stem in ['main','diagrams']:
    reader=PdfReader(paper/'build'/f'{stem}.pdf')
    text=re.sub(r'\s+',' ',' '.join(p.extract_text() for p in reader.pages))
    assert all(re.search(rf'Figure\s+{i}\s*:',text) for i in range(1,18)),stem
    assert '??' not in text,stem
    log=(paper/'build'/f'{stem}.log').read_text(encoding='utf-8',errors='replace')
    assert not any(s in log for s in ['Overfull','Missing character','undefined references','undefined citations']),stem
    assert sum(len(p.images) for p in reader.pages)==0,stem
    if stem=='main':
        assert all(re.search(rf'T\s*able\s+{i}\s*:',text) for i in range(1,10))
        pair_pages=[i+1 for i,p in enumerate(reader.pages) if 'UMAPclusters:' in re.sub(r'\s+','',p.extract_text())]
        assert pair_pages==[12,13,14],pair_pages
    print(stem,len(reader.pages),'pages; 17 native figures; resolved references and no clipped text.')

source=json.loads((paper/'cluster_tree_sources.json').read_text())
assert len(source)==3
for item in source.values():
    assert item['instruments']==41 and item['groups']==8 and item['tree_cut_ari']==1.
    assert sum(len(v) for v in item['aligned_members'].values())==41

# Refresh both paper export names, including the PDF already open in the user's editor.
for filename in ['JSE_Top40_Three_Cross_Section_Paper_20261115.pdf',
                 'JSE_Top40_Three_Cross_Section_Paper_LaTeX_20261115.pdf']:
    shutil.copy2(paper/'build/main.pdf',out/filename)
shutil.copy2(paper/'build/diagrams.pdf',out/'JSE_Top40_LaTeX_Diagram_Atlas_20261115.pdf')

archive=out/'JSE_Top40_LaTeX_Source_20261115.zip'
temporary=archive.with_suffix('.zip.tmp')
files=sorted(p for p in paper.rglob('*') if p.is_file() and 'build' not in p.relative_to(paper).parts
             and (p.suffix in {'.tex','.csv','.md','.json','.ps1','.py'} or p.name=='.gitignore'))
with ZipFile(temporary,'w',ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(paper).as_posix())
with ZipFile(temporary) as z:
    assert z.testzip() is None
    names=set(z.namelist())
    assert len([n for n in names if n.startswith('figures/') and n.endswith('.tex')])==17
    for p in files:assert z.read(p.relative_to(paper).as_posix())==p.read_bytes()
    for name in names:
        if name.endswith('.tex'):
            for target in re.findall(r'\\input\{([^}]+)\}',z.read(name).decode('utf-8')):
                if '#' not in target:assert target in names,(name,target)
    assert 'make_cluster_tree_figures.py' in names
    assert len([n for n in names if n.endswith('_coordinates.csv') or n.endswith('_linkage.csv')])==6
temporary.replace(archive)
print('Updated both paper PDFs, diagram atlas and ZIP:',len(files),'verified source files.')

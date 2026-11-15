from pathlib import Path
import re, json, shutil, zipfile, hashlib
from pypdf import PdfReader

root=Path.cwd(); folder=root/'output/paper/latex'; out=folder.parent
for name in ['main','diagrams']:
    pdf=folder/f'{name}.pdf'; assert pdf.exists(),pdf
    reader=PdfReader(pdf);text=re.sub(r'\s+',' ',' '.join(p.extract_text() for p in reader.pages))
    assert '??' not in text, 'Unresolved reference in '+name
    assert all(re.search(rf'Figure\s+{i}\s*:',text) for i in range(1,15)),name
    log=(folder/f'{name}.log').read_text(encoding='utf-8',errors='replace')
    assert 'undefined references' not in log.lower(),name
    assert 'undefined citations' not in log.lower(),name
    assert 'Overfull \\hbox' not in log,name+' contains overfull horizontal text'
    print(name,len(reader.pages),'pages, 14 figures, no unresolved references or overfull text')

shutil.copy2(folder/'main.pdf',out/'JSE_Top40_Three_Cross_Section_Paper_LaTeX_20261115.pdf')
shutil.copy2(folder/'diagrams.pdf',out/'JSE_Top40_LaTeX_Diagram_Atlas_20261115.pdf')
archive=out/'JSE_Top40_LaTeX_Source_20261115.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.suffix in {'.tex','.csv','.md','.json'}:
            z.write(p,p.relative_to(folder))
with zipfile.ZipFile(archive) as z:
    assert len([x for x in z.namelist() if x.startswith('figures/') and x.endswith('.tex')])==14
print('Packaged',archive.name,archive.stat().st_size,'bytes')

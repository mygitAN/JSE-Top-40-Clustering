from pathlib import Path
import shutil
root=Path.cwd();backup=root/'.runtime/paper_before_sacj_style'
for p in backup.rglob('*.tex'):
    shutil.copy2(p,root/'paper'/p.relative_to(backup))
code=(root/'tmp/paper/apply_sacj_voice.py').read_text(encoding='utf-8')
start=code.index("if backup.exists():")
end=code.index('\nchanges=[]',start)
code=code[:start]+code[end:]
exec(compile(code,'apply_sacj_voice.py','exec'))

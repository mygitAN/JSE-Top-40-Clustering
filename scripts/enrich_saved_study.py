"""Read-only reporting enrichment of an explicitly chosen completed study."""
import argparse
import json
import hashlib
from pathlib import Path
import shutil
import pandas as pd
from tracking import ROOT, digest
from verify_run import verify_completed
from study_enrichment import enrich_model


def derive(source, output):
    source=Path(source).resolve();output=Path(output).resolve()
    if source==output or source in output.parents:
        raise ValueError('Keep derived reporting outside the completed source run')
    verified=verify_completed(source)
    original_index=digest(source/'artifact_checksums.json')
    config=json.loads((source/'study_manifest.json').read_text(encoding='utf-8'))['configuration']
    output.mkdir(parents=True,exist_ok=False)
    folders={'baseline':'models'}
    if config['include_umap_sensitivity']:folders['umap_sensitivity']='umap_sensitivity'
    rows=[]
    for name,relative in folders.items():
        folder=source/relative
        assignments=pd.read_csv(folder/'assignments.csv')
        rows.append(enrich_model(assignments,folder,config['dates'],output/name,name,
                                 config['seed'],config['stability_runs']))
    pd.DataFrame(rows).to_csv(output/'longitudinal_summary.csv',index=False)
    shutil.copyfile(source/'eda/population_and_sectors.png',output/'population_and_sectors.png')
    assert verify_completed(source)==verified
    assert digest(source/'artifact_checksums.json')==original_index
    manifest=dict(source=str(source),source_artifact_index_sha256=original_index,
        source_artifacts_verified=verified,models_refitted=0,searches_run=0,
        model_settings_changed=False,source_run_modified=False,
        purpose='Reporting cherry-picked from Paper Experiments for the fixed Three Cross Sections models',
        config=config,code_sha256={name:digest(ROOT/'scripts'/name) for name in ['study_enrichment.py','enrich_saved_study.py']},
        caveat='Descriptive clustering and screens, not confirmed outliers, causal explanations or investment performance')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    index={p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}
    (output/'artifact_checksums.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False))
    print('Saved derived report:',output)
    print('Source preserved:',verified,'artifacts; zero model refits')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();derive(args.source,args.output)

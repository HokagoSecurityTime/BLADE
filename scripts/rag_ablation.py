"""Five real-LLM retrieval configurations; saves every result, including regressions."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import time

import httpx

from common.schema import Policy
from pipeline.classifier import classify
from pipeline.classifier.run import EXPECTED
from pipeline.parsers.oas import parse_oas
from pipeline.parsers.erd import parse_erd
from pipeline.rag.corpus import load_code, load_idioms, load_policies, load_cves
from pipeline.rag.index import Index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--oas', type=Path, default=Path('demo_backend/openapi.json'))
    parser.add_argument('--erd', type=Path, default=Path('demo_backend/schema.sql'))
    parser.add_argument('--controller', type=Path, default=Path('demo_backend/main.py'))
    parser.add_argument('--admin', default='http://localhost:8100')
    parser.add_argument('--cve', type=Path, default=Path('corpus/cve.jsonl'))
    parser.add_argument('--output', type=Path, default=Path('verification/phase2/rag-ablation.json'))
    args = parser.parse_args()
    os.environ['BLADE_PHASE2_ENABLED'] = 'true'
    endpoints = parse_oas(args.oas.read_text(encoding='utf-8'))
    erd = parse_erd(args.erd.read_text(encoding='utf-8'))
    code = args.controller.read_text(encoding='utf-8')
    response = httpx.get(args.admin+'/policies', params={'status': 'ACTIVE'}, timeout=10)
    response.raise_for_status()
    policies = [Policy.model_validate(row) for row in response.json()]
    index = Index()
    corpora = dict(code=load_code(code, args.controller.name), idiom=load_idioms(),
                   policy=load_policies(policies), cve=load_cves(args.cve))
    for kind, chunks in corpora.items():
        index.replace(kind, chunks)
    report = dict(provider=os.getenv('BLADE_LLM_PROVIDER'), model=os.getenv('BLADE_LLM_MODEL'),
                  embed_model=index.encoder.name, controller=str(args.controller),
                  controller_enabled=os.getenv('BLADE_CONTROLLER_ENABLED', 'true'),
                  corpus_counts={k: len(v) for k, v in corpora.items()}, results=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, kinds in [('off', []), ('code', ['code']), ('code+idiom', ['code', 'idiom']),
                        ('code+idiom+policy', ['code', 'idiom', 'policy']),
                        ('code+idiom+policy+cve', ['code', 'idiom', 'policy', 'cve'])]:
        os.environ['BLADE_RAG_ENABLED'] = str(bool(kinds)).lower()
        row = dict(configuration=name, results=[], correct=0)
        report['results'].append(row)
        for endpoint in endpoints:
            refs = index.retrieve(endpoint, erd, kinds=kinds) if kinds else []
            started = time.monotonic()
            result = classify(endpoint, erd, code, evidence_refs=refs)
            expected = EXPECTED[(endpoint.method, endpoint.path)]
            correct = result.label.value == expected
            row['correct'] += correct
            row['results'].append(dict(endpoint=asdict(endpoint), expected=expected,
                classification=result.model_dump(mode='json'), correct=correct,
                retrieved=[r.model_dump() for r in refs], elapsed_sec=time.monotonic()-started))
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'{name}: {endpoint.method} {endpoint.path} -> {result.label.value}; expected {expected}', flush=True)
        print(f'{name}: {row["correct"]}/{len(endpoints)}', flush=True)
    baseline = report['results'][0]['correct']
    lines = ['# RAG ablation', '', f'Provider/model: {report["provider"]} / {report["model"]}. Embedding: {report["embed_model"]}.',
             '', '| Configuration | Correct / 7 | vs off |', '|---|---|---|']
    for row in report['results']:
        delta = row['correct'] - baseline
        lines.append(f'| {row["configuration"]} | {row["correct"]}/{len(endpoints)} | {delta:+d} |')
    lines += ['', 'Corpus counts: '+json.dumps(report['corpus_counts']), '',
              'All configurations keep the same controller input/settings. Off disables retrieval only.',
              'Approved policies may overlap the evaluated demo endpoints; these are demo results, not a held-out accuracy estimate.',
              'An empty CVE corpus means the last row does not measure the effect of CVE evidence.',
              'No configuration has been selected automatically; the user chooses after reviewing this table.']
    args.output.with_suffix('.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()

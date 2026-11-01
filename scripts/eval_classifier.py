"""Frozen-test runtime baseline evaluation with resumable per-example checkpoints.

Run as python -m scripts.eval_classifier --configuration a --test-sha256 HASH.
Runtime imports only: its confidence/lookup validation is intentionally retained.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from unittest.mock import patch

from common.labels import Label
from pipeline.classifier import classify
import pipeline.classifier as classifier_module
from pipeline.classifier.prompt import build_user_prompt, system_prompt
from pipeline.parsers.oas import Endpoint, parse_oas
from pipeline.parsers.erd import parse_erd
from pipeline.rag.corpus import load_idioms

ROOT = Path(__file__).resolve().parents[1]
LABELS = [item.value for item in Label]
CONFIGS = {
    'a': dict(provider='openai', model='gpt-4o-mini', rag=True, controller=True),
    'b': dict(provider='ollama', model='qwen2.5:7b', rag=True, controller=True),
    'c': dict(provider='ollama', model='qwen2.5:7b', rag=False, controller=False),
}


def classify_recorded(*args, **kwargs):
    """Serial evaluator only: observe real calls without changing runtime decisions."""
    trace = dict(raw_response=None, raw_label=None, raw_confidence=None,
                 parsed_label=None, validation_events=[])
    complete = classifier_module.llm.complete
    parse = classifier_module.parse_result
    fallback = classifier_module.manual_review

    def capture_complete(*a, **kw):
        raw = complete(*a, **kw)
        trace['raw_response'] = raw
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                trace['raw_label'] = obj.get('label')
                trace['raw_confidence'] = obj.get('confidence')
        except (ValueError, TypeError):
            pass
        return raw

    def capture_parse(raw):
        result = parse(raw)
        trace['parsed_label'] = result.label.value
        if result.evidence == 'Invalid classification JSON or schema; manual review required':
            trace['validation_events'].append('json_or_schema_invalid')
        else:
            if trace['raw_label'] not in LABELS:
                trace['validation_events'].append('unknown_label')
            if result.confidence < .7:
                trace['validation_events'].append('confidence_below_0.7')
        return result

    def capture_fallback(reason):
        trace['validation_events'].append(reason)
        return fallback(reason)

    with patch.object(classifier_module.llm, 'complete', capture_complete), \
         patch.object(classifier_module, 'parse_result', capture_parse), \
         patch.object(classifier_module, 'manual_review', capture_fallback):
        result = classify(*args, **kwargs)
    trace['final_label'] = result.label.value
    trace['label_changed'] = trace['raw_label'] != result.label.value if trace['raw_response'] is not None else None
    return result, trace


def diagnostic_metrics(results):
    recorded = [r for r in results if 'trace' in r]
    if not recorded:
        return None
    raw = [{**r, 'prediction': r['trace']['raw_label'] if r['trace']['raw_label'] in LABELS else '__invalid__'} for r in recorded]
    return dict(recorded=len(recorded), missing_trace=len(results)-len(recorded),
                raw=metrics(raw), final=metrics(recorded),
                invalid_raw_labels=sum(r['prediction'] == '__invalid__' for r in raw),
                changed=sum(r['trace']['label_changed'] is True for r in recorded),
                correct_to_wrong=sum(a['prediction'] == a['expected'] and b['prediction'] != b['expected'] for a, b in zip(raw, recorded)),
                wrong_to_correct=sum(a['prediction'] != a['expected'] and b['prediction'] == b['expected'] for a, b in zip(raw, recorded)),
                validation_events=dict(Counter(e for r in recorded for e in r['trace']['validation_events'])))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def load_env():
    # Literal values only; never evaluate shell syntax or print credentials.
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))


def endpoint_input(row):
    """Prefer original OAS; fallback preserves only actual supplied route metadata."""
    warnings = []
    try:
        endpoints = parse_oas(row['oas_snippet'])
        endpoint = next(e for e in endpoints if e.method == row['method'] and e.path == row['path'])
    except (ValueError, KeyError, StopIteration, TypeError):
        warnings.append('oas_parser_fallback_to_route_metadata')
        endpoint = Endpoint(row['method'], row['path'], row.get('path_params') or re.findall(r'\{([^}]+)\}', row['path']),
                            row.get('query_params') or [], row.get('operation_id'), [], row.get('summary'))
    try:
        erd = parse_erd(row.get('erd_snippet') or '')
    except ValueError:
        erd = {}
        warnings.append('erd_parser_failed_empty_context')
    return endpoint, erd, warnings


def controller_source(row):
    """Return real source text only; never synthesize decorators or label clues."""
    if row.get('controller_text'):
        return row['controller_text'], 'dataset_controller_text'
    candidates = []
    if row.get('source_file'):
        candidates.append(row['source_file'])
    for location in row.get('source_locations') or []:
        filename = location.get('file', '')
        if row.get('source') == 'vuln':
            candidates.append(str(Path('datasets/blade/raw/vuln_apis') / row['service'] / filename))
        else:
            candidates.append(filename)
    texts = []
    for filename in dict.fromkeys(candidates):
        path = (ROOT / filename).resolve()
        if not path.is_relative_to(ROOT / 'datasets/blade/raw') or not path.is_file():
            continue
        texts.append(path.read_text(encoding='utf-8-sig'))
    if texts:
        return '\n\n'.join(texts), 'mapped_source_files'
    return None, 'source_unavailable'


def metrics(results):
    columns = LABELS + (['__invalid__'] if any(r['prediction'] not in LABELS for r in results) else [])
    matrix = {label: {prediction: 0 for prediction in columns} for label in LABELS}
    for row in results:
        matrix[row['expected']][row['prediction']] += 1
    per_label = {}
    for label in LABELS:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted = sum(matrix[other][label] for other in LABELS)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        per_label[label] = dict(precision=precision, recall=recall,
            f1=2*precision*recall/(precision+recall) if precision+recall else 0.0, support=support)
    count = len(results)
    return dict(completed=count, per_label=per_label, confusion_matrix=matrix,
                macro_f1=sum(row['f1'] for row in per_label.values())/len(LABELS),
                manual_ratio=sum(row['prediction'] == 'manual_review_required' for row in results)/count if count else 0,
                mean_inference_ms=sum(row['inference_ms'] for row in results)/count if count else 0,
                errors=dict(Counter(row['error'] for row in results if row.get('error'))),
                erd_context=dict(Counter('available' if row.get('erd_table_count', 0) else 'missing' for row in results)),
                controller_status=dict(Counter(row['controller_status'] for row in results)),
                rag_nonempty=sum(bool(row['retrieved']) for row in results))


def render_summary(directory):
    lines = ['# Frozen test baseline', '', 'Intermediate results; completed/total must reach 253 before comparison.', '',
             '| Run | Completed | Macro F1 | Manual ratio | Mean inference ms | Errors |',
             '|---|---:|---:|---:|---:|---:|']
    reports = []
    for path in sorted(directory.glob('*_metrics.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        reports.append(report)
        m = report['metrics']
        lines.append(f"| {report['configuration']} | {m['completed']}/{report['total']} | {m['macro_f1']:.4f} | {m['manual_ratio']:.2%} | {m['mean_inference_ms']:.1f} | {sum(m['errors'].values())} |")
    for report in reports:
        d = report.get('diagnostic_metrics')
        if d:
            lines += ['', f"Raw/final comparison ({report['configuration']}, n={d['recorded']}): macro-F1 {d['raw']['macro_f1']:.4f} -> {d['final']['macro_f1']:.4f}.",
                      f"Manual ratio: {d['raw']['manual_ratio']:.2%} -> {d['final']['manual_ratio']:.2%}; changed labels: {d['changed']}; missing traces: {d['missing_trace']}.",
                      f"Correct -> wrong: {d['correct_to_wrong']}; wrong -> correct: {d['wrong_to_correct']}; invalid raw labels: {d['invalid_raw_labels']} (counted as errors, not manual).",
                      'Validation events: `'+json.dumps(d['validation_events'])+'`.', '',
                      '| Label | Raw P | Raw R | Raw F1 | Final P | Final R | Final F1 |', '|---|---:|---:|---:|---:|---:|---:|']
            for label in LABELS:
                a, b = d['raw']['per_label'][label], d['final']['per_label'][label]
                lines.append('| '+label+' | '+' | '.join(f'{v:.4f}' for v in (a['precision'], a['recall'], a['f1'], b['precision'], b['recall'], b['f1']))+' |')
            columns = list(next(iter(d['raw']['confusion_matrix'].values())))
            lines += ['', 'Raw confusion matrix (invalid outputs remain errors):', '', '| True / Raw | '+' | '.join(columns)+' |', '|---|'+'---:|'*len(columns)]
            for label, cells in d['raw']['confusion_matrix'].items():
                lines.append('| '+label+' | '+' | '.join(str(cells[x]) for x in columns)+' |')
        lines += ['', '## '+report['configuration'], '', f"State: {report['state']}. Test SHA-256: `{report['test_sha256']}`.", '',
                  '| Label | Precision | Recall | F1 | Support |', '|---|---:|---:|---:|---:|']
        for label, row in report['metrics']['per_label'].items():
            lines.append(f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['support']} |")
        lines += ['', 'Confusion matrix: rows=human label, columns=runtime prediction.', '', '| True / Predicted | '+' | '.join(LABELS)+' |', '|---|'+'---:|'*len(LABELS)]
        for label, cells in report['metrics']['confusion_matrix'].items():
            lines.append('| '+label+' | '+' | '.join(str(cells[x]) for x in LABELS)+' |')
        lines += ['', 'Controller coverage: `'+json.dumps(report['metrics']['controller_status'])+'`.',
                  'ERD coverage: `'+json.dumps(report['metrics']['erd_context'])+'`.',
                  'Errors: `'+json.dumps(report['metrics']['errors'])+'`.']
    lines += ['', 'Protocol: unchanged pipeline.classify, prompt v2.0. Runtime confidence <0.7 and invalid owner lookup become manual_review_required.',
              'RAG uses the runtime embedding Index over repository generic idioms only (no test labels, challenge answers, approved test policies or test source in retrieval). Controller source is supplied separately.',
              'Unsupported/unmapped controller handlers are reported as missing runtime signals; stored review hints are not injected as parser output.',
              'Missing ERD prevents object-label lookup validation in the unchanged runtime. These scores measure the pipeline with available OAS/ERD/controller inputs, not pure seven-label semantic classification. No ERD tables are fabricated.',
              'Provider/schema failures retain the runtime manual result and are also counted separately. Wall inference latency includes runtime retries; retrieval is measured separately in checkpoints.']
    path = directory / 'baseline_summary.md'
    # Concurrent a/b runs may update this summary; the immutable per-run metrics are authoritative.
    temp = directory / f'baseline_summary.{os.getpid()}.tmp'
    temp.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', choices=CONFIGS, required=True)
    parser.add_argument('--test', type=Path, default=ROOT/'datasets/blade/processed/test.jsonl')
    parser.add_argument('--test-sha256', required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'reports/eval/recorded')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--input-overlay', type=Path, help='Source-derived context only; frozen labels remain unchanged')
    args = parser.parse_args()
    load_env()
    if digest(args.test) != args.test_sha256 or args.test_sha256 not in (ROOT/'AGENTS.md').read_text(encoding='utf-8'):
        raise SystemExit('Frozen test hash does not match file and AGENTS.md; no calls made')
    config = CONFIGS[args.configuration]
    os.environ.update(BLADE_LLM_PROVIDER=config['provider'], BLADE_LLM_MODEL=config['model'], BLADE_PROMPT_VERSION='v2.0',
                      BLADE_PHASE2_ENABLED='true', BLADE_RAG_ENABLED=str(config['rag']).lower(), BLADE_CONTROLLER_ENABLED=str(config['controller']).lower())
    rows = read_jsonl(args.test)
    if len(rows) != 253 or len({r['id'] for r in rows}) != 253 or any(r['label'] not in LABELS for r in rows):
        raise SystemExit('Expected 253 unique human-confirmed test rows')
    if args.input_overlay:
        overlay = read_jsonl(args.input_overlay)
        by_id = {r['id']: r for r in overlay}
        if len(by_id) != len(overlay) or not by_id.keys() <= {r['id'] for r in rows}:
            raise SystemExit('Overlay IDs invalid')
        allowed = {'id', 'erd_snippet', 'controller_text', 'provenance'}
        if any(set(r) - allowed for r in overlay):
            raise SystemExit('Overlay contains fields other than source context')
        rows = [{**r, **{k: v for k, v in by_id.get(r['id'], {}).items() if k in {'erd_snippet', 'controller_text'}}} for r in rows]
    args.output.mkdir(parents=True, exist_ok=True)
    name = f"{args.configuration}_{config['model'].replace(':','_')}_v2.0_recorded"
    partial = args.output/(name+'.partial.jsonl')
    manifest_path = args.output/(name+'.manifest.json')
    lock = args.output/(name+'.lock')
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    try:
        corpus = load_idioms() if config['rag'] else []
        corpus_hash = hashlib.sha256(json.dumps([dict(kind=c.kind, ref=c.ref, text=c.text) for c in corpus], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        manifest = dict(configuration=args.configuration, **config, prompt_version='v2.0', prompt_sha256=digest(ROOT/'prompts/v2.0.md'),
                        test_sha256=args.test_sha256, runner_sha256=digest(__file__), corpus_sha256=corpus_hash, corpus_counts={'idiom':len(corpus)},
                        embedding_model='intfloat/multilingual-e5-small' if config['rag'] else None, total=len(rows), recording_version=1,
                        input_overlay_sha256=digest(args.input_overlay) if args.input_overlay else None)
        if manifest_path.exists():
            saved = json.loads(manifest_path.read_text(encoding='utf-8'))
            if any(saved[k] != v for k, v in manifest.items()):
                raise SystemExit('Resume manifest mismatch')
        else:
            atomic_json(manifest_path, {**manifest, 'started_at':datetime.now(timezone.utc).isoformat()})
        index = None
        if config['rag']:
            if not corpus:
                raise SystemExit('RAG corpus empty; refusing to report RAG on')
            from pipeline.rag.index import Index
            os.environ['BLADE_EMBED_MODEL'] = manifest['embedding_model']
            index = Index(path=args.output/('.rag_'+args.configuration))
            index.replace('idiom', corpus)
        if config['provider'] == 'ollama':
            import httpx
            names = [m['name'] for m in httpx.get(os.getenv('BLADE_OLLAMA_URL','http://127.0.0.1:11434')+'/api/tags', timeout=10).json()['models']]
            if config['model'] not in names:
                raise SystemExit('Required Ollama model unavailable')
        results = read_jsonl(partial) if partial.exists() else []
        if any('trace' not in r for r in results):
            raise SystemExit('Checkpoint lacks raw trace; use a new output directory')
        completed = {r['id'] for r in results}
        if len(completed) != len(results) or not completed <= {r['id'] for r in rows}:
            raise SystemExit('Checkpoint IDs invalid')
        def save(state):
            atomic_json(args.output/(name+'_metrics.json'), {**manifest, 'state':state, 'updated_at':datetime.now(timezone.utc).isoformat(), 'metrics':metrics(results), 'diagnostic_metrics':diagnostic_metrics(results)})
            render_summary(args.output)
        save('running')
        for row in rows[:args.limit] if args.limit else rows:
            if row['id'] in completed:
                continue
            if digest(args.test) != args.test_sha256:
                raise SystemExit('Frozen test changed during run')
            endpoint, erd, warnings = endpoint_input(row)
            source, source_status = controller_source(row) if config['controller'] else (None, 'disabled')
            started = time.perf_counter()
            refs = index.retrieve(endpoint, erd, kinds=['idiom']) if index else []
            retrieval_ms = (time.perf_counter()-started)*1000
            user = build_user_prompt(endpoint, erd, source, refs)
            payload = json.loads(user)
            controller_status = ('parsed_current_handler' if payload.get('controller_text') else 'source_present_but_runtime_handler_unmapped') if source else source_status
            started = time.perf_counter()
            result, trace = classify_recorded(endpoint, erd, source, evidence_refs=refs)
            elapsed = (time.perf_counter()-started)*1000
            error = None
            if result.evidence.startswith('LLM unavailable:'):
                error = result.evidence
            elif result.evidence.startswith('Invalid classification JSON'):
                error = 'invalid_model_output_schema'
            record = dict(id=row['id'], service=row['service'], expected=row['label'], prediction=result.label.value,
                          classification=result.model_dump(mode='json'), trace=trace, error=error, inference_ms=elapsed, retrieval_ms=retrieval_ms,
                          erd_table_count=len(erd),
                          retrieved=[r.model_dump() for r in refs], controller_status=controller_status, warnings=warnings,
                          prompt_sha256=hashlib.sha256((system_prompt(rag=bool(refs))+'\0'+user).encode()).hexdigest())
            with partial.open('a', encoding='utf-8') as out:
                out.write(json.dumps(record, ensure_ascii=False)+'\n'); out.flush(); os.fsync(out.fileno())
            results.append(record); completed.add(row['id']); save('running')
            print(f"{args.configuration} {len(results)}/{len(rows)} error={error or 'none'} inference_ms={elapsed:.0f}", flush=True)
            # Stop repeated transport/configuration failures instead of burning 253 requests.
            if len(results) >= 3 and all(str(r.get('error') or '').startswith('LLM unavailable:') for r in results[-3:]):
                save('blocked_provider_errors'); return
        save('complete' if len(results) == len(rows) else 'partial_limit')
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--adapter-v3-holdout':
        from training.experiments.adapter_v3_holdout import main as adapter_holdout_main
        adapter_holdout_main(sys.argv[2] if len(sys.argv) > 2 else 'prepare')
    elif len(sys.argv) > 1 and sys.argv[1] == '--external-paired-v29':
        from training.experiments.external_paired_v29 import main as external_paired_main
        external_paired_main(sys.argv[2] if len(sys.argv) > 2 else 'prepare')
    elif len(sys.argv) > 1 and sys.argv[1] == '--external-conditions':
        from training.experiments.evaluate_external_adapter import main as external_main
        external_main()
    elif len(sys.argv) > 1 and sys.argv[1] == '--policy-conditions':
        from training.experiments.evaluate_policy_conditions import main as condition_main
        condition_main()
    elif len(sys.argv) > 1 and sys.argv[1] == '--paired-policy':
        from training.experiments.paired_policy import main as paired_main
        paired_main(sys.argv[2] if len(sys.argv) > 2 else 'prepare')
    else:
        main()

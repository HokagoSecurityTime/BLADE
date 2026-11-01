from scripts.attack_sim import cases, metrics


def test_ground_truth_and_metrics() -> None:
    matrix=cases()
    assert len(matrix)==14 and len({c.label for c in matrix})==7
    rows=[dict(status=403 if c.should_block and c.label!='manual_review_required' else 200,
               should_block=c.should_block,latency_ms=i+1) for i,c in enumerate(matrix)]
    result=metrics(rows)
    assert (result['TP'],result['FN'],result['FP'],result['TN'])==(5,1,0,8)
    assert result['detection_rate']==5/6 and result['false_positive_rate']==0
    assert result['p50_ms']==7 and result['p95_ms']==14
    rows.append(dict(status=503,should_block=True,latency_ms=100))
    result=metrics(rows)
    assert result['errors']==1 and result['FN']==1

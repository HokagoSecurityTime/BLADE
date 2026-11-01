# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas_code | lora_v5_s42_final | 0.6947 | 0.6947 | 0.3661 | 0.9905 | 25.3% | 25.3% | 16/64 | 3/47 | 0.8187 / 0.632 (응답률 0.772) | 0.8187 / 0.632 (응답률 0.772) |
| oas_code | lora_v5_s42_gguf_q4km | 0.7731 | 0.7731 | 0.3996 | 0.9905 | 18.5% | 18.5% | 14/64 | 2/47 | 0.8261 / 0.684 (응답률 0.828) | 0.8261 / 0.684 (응답률 0.828) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas_code | lora_v5_s42_final | 16 | 13 | 3/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s42_gguf_q4km | 14 | 12 | 2/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas_code / lora_v5_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v5_s42_gguf_q4km: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

### oas_code / lora_v5_s42_final — 주지표 265건, macro-F1 0.6947 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7097 | 0.6667 | 0.6875 |
| role_required | 47 | 0.8261 | 0.4043 | 0.5429 |
| membership_required | 4 | 0.5 | 1.0 | 0.6667 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8929 | 0.6579 | 0.7576 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2239 | 1.0 | 0.3659 |

### oas_code / lora_v5_s42_gguf_q4km — 주지표 265건, macro-F1 0.7731 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7377 | 0.6818 | 0.7087 |
| role_required | 47 | 0.7931 | 0.4894 | 0.6053 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8557 | 0.7281 | 0.7867 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.3061 | 1.0 | 0.4687 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)

# 승격 게이트 규칙 (gate-rules)

## 승격 조건 — 셋 다 되어야 한다

| # | 조건 | 이유 |
|---|------|------|
| 1 | 내 언어로 재작성 | 복사해 둔 것은 이해한 것이 아니다 |
| 2 | 주제 태그 | 나중에 MOC로 묶인다 |
| 3 | 관련 노트 2개 이상 링크 (콜드 스타트: 1개) | 연결 없는 노트는 다시 안 읽는다 |

하나라도 안 되면 승격하지 않는다. 게이트가 없으면 영구노트가 임시노트의 복사본이 되고, 그 순간 이 시스템은 쓰레기통이 된다.

판정은 PASS / HOLD / DROP 셋 중 하나다.
- PASS: 영구노트 생성, 번호 부여, index 삽입, 로그 기록
- HOLD: 원본 frontmatter에 `status: hold`, `review_at: <14일 뒤>` 기록. 파일은 옮기지 않음
- DROP(평균 2.0 미만): 반드시 사용자 확인 후 `paths.meta`의 `dropped.md`에 사유 기록. 파일은 남김

## 판정 주체와 기준

| 조건 | 판정 주체 | 기준 | 미달 시 |
|---|---|---|---|
| 5기준 평균 | LLM | ≥ 3.5 PASS 후보, 3.0~3.4 경계, 2.0~2.9 FAIL, < 2.0 DROP 후보 | 경계는 보완 제안 1회, FAIL은 HOLD |
| 자기 말로 재작성 | 스크립트 | 인용 밖 8-gram 중복률 ≤ 20% | HOLD "복사해 둔 것은 이해한 것이 아니다" |
| 주제 태그 | 스크립트 | 성장 태그 외 태그 ≥ 1 | HOLD |
| 관련 노트 링크 | 스크립트 | ≥ 2 (콜드 스타트: ≥ 1) | HOLD "연결 없는 노트는 다시 안 읽는다" |

- 판정은 **PASS / HOLD / DROP** 세 갈래다. HOLD는 원본에 `review_at`(+14일)을 적고, `promote`는 `review_at`이 지난 HOLD 노트를 다음 스캔에 다시 올린다. DROP은 반드시 사용자 확인을 받고 파일은 지우지 않는다.
- 게이트 HOLD는 LLM 점수와 무관하게 승격을 막는다. 스크립트가 최종 문지기다.
- 스크립트 판정 기준값은 설정에서 읽는다: `gate.min_links`, `gate.max_overlap`, `gate.ngram`, `gate.pass_avg`, `gate.cold_start_notes`.

## 중복률 계산 방식

초안 본문에서 인용 구간(`"…"([[…]])`)과 frontmatter·연결 섹션을 제거한 뒤, 공백을 정규화한 문자 8-gram 집합을 만들어 원본 8-gram과의 교집합 비율을 낸다. `gate.max_overlap`을 넘으면 `자기 말로 재작성 안 됨`이다. 즉 따옴표와 원본 링크로 정직하게 표시한 인용은 중복률에 들어가지 않고, 표시 없이 옮긴 문장만 잡힌다.

링크 수는 본문의 `[[…]]` 중 원본 자신을 제외한 서로 다른 대상 수이며, 태그는 frontmatter `tags`에서 성장 태그(seed/growing/evergreen)를 뺀 나머지가 1개 이상이어야 한다.

## 콜드 스타트

영구노트가 `gate.cold_start_notes`(기본 5)개 미만인 vault에서는 링크 기준을 1로 낮추고, 원본 노트로 향한 링크도 한 개로 인정한다. 빈 vault에서 첫 영구노트가 나올 수 있게 하기 위함이며, 문헌노트에서 만든 영구노트와 임시노트에서 만든 영구노트가 서로 연결되면 자연스럽게 2개가 채워진다.

## 성장 태그

생성 시 `#seed`를 붙인다. `status`가 인바운드 링크 수로 `#growing`(≥ `growth.growing_inbound`, 기본 3)·`#evergreen`(≥ `growth.evergreen_inbound`, 기본 5) 후보를 제시하고 확인을 받으면 바꾼다. 성장 태그는 주제 태그로 세지 않으므로, 성장 태그만 붙은 노트는 `태그 없음`으로 HOLD된다.

## 기록

모든 PASS/HOLD/DROP 판정은 `paths.meta`의 `promotion-log.jsonl`에 한 줄씩 남는다. 한 줄의 필드는 `{ts, source, title, scores, avg, gate, verdict, luhmann, model, profile}`이며 `ts`는 KST ISO 시각이다.

---

NOTICE: 3조건·3분기 판정 문안은 p-changki/devtrail(MIT) 차용.

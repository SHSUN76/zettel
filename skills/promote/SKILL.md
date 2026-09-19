---
name: promote
description: 임시노트를 스캔해 제텔카스텐 규칙으로 영구노트로 승격한다. 5기준 채점은 LLM이 하고, 승격 게이트(중복률·링크·태그)와 루만 번호는 스크립트가 판정한다. "승격해줘", "임시노트 정리해줘", "오늘 것 영구노트로 만들어줘", 쌓인 메모를 정리할 때 쓴다. 사용법 - /zettel:promote [경로 | --only 오늘 | --all] [--dry-run]
---

# 임시노트 → 영구노트 승격

인자: `$ARGUMENTS`

승격 여부의 최종 문지기는 스크립트다. 5기준 평균이 아무리 높아도 게이트가 HOLD를 내면 승격하지 않는다.

## 0. 준비 (반드시 먼저)

1. 설정을 읽는다. 인자는 없다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

현재 폴더에서 위로 올라가며 `zettel.json`을 찾아 `{"root": ..., "profile": ..., "paths": {...}, "gate": {...}, "growth": {...}, "fleeting_types": {...}}`를 낸다. `{"error": ...}`(종료 코드 2)가 나오면 "zettel vault 안에서 실행하세요"를 안내하고 **거기서 멈춘다**. 아래의 `<root>`·`paths.*`·`gate.*`는 전부 이 JSON에서 읽은 값이며, 폴더 이름을 이 문서에서 가져오지 않는다.

2. 규칙 문서를 Read 도구로 읽는다.
   - `${CLAUDE_PLUGIN_ROOT}/skills/_shared/references/rubric.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/_shared/references/citation-rules.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/_shared/references/gate-rules.md`

3. 콜드 스타트 판정. Glob 도구로 `<root>/<paths.permanent>/**/*.md`(하위 폴더 포함)를 세되, `paths.index`가 들어 있는 하위 폴더 아래의 파일과 `_`로 시작하는 파일은 제외한다(`report.py`의 영구노트 계산 방식과 같다). 이 수가 `gate.cold_start_notes`보다 작으면 **콜드 스타트 모드**이며, 5단계 `gate.py check`에 `--cold-start`를 붙인다. 크거나 같으면 붙이지 않는다.

## 1. 스캔·분류

`fleeting_types`의 각 값이 가리키는 폴더를 훑는다. 값이 빈 문자열이면 `paths.fleeting`을 뜻한다. 각 폴더와 그 **하위 폴더 전체**(Glob `<폴더>/**/*.md`)에서 frontmatter `processed`가 `true`가 아닌 노트(키가 없거나 `false`)를 모은다. 옛 노트는 `processed` 키가 없는 경우가 많다. `_`로 시작하는 파일(`_template.md` 등)은 제외한다.

- `$ARGUMENTS`가 파일 경로면 그 파일 하나만 본다.
- `--only 오늘`이면 오늘 것만 본다. 오늘 날짜는 KST `YYYY-MM-DD`. 파일명이 `<YYYYMMDD>-`로 시작하거나 frontmatter `created`가 오늘인 것. 파일 수정 시각(mtime)은 쓰지 않는다.
- `--all`이면 `processed`가 `true`가 아닌 것을 전부 본다.
- 인자가 없으면 `--all`과 같이 본다.

`status: hold`이고 `review_at`이 아직 오지 않은 노트는 건너뛴다. `review_at`이 지난 노트는 다시 후보로 올린다.

## 2. Extractor

노트마다 원자 단위 아이디어로 나눈다. 한 문장에 주장이 둘이면 둘로 나눈다. Feynman 검사: 한 문장으로 설명되지 않는 아이디어는 사용자에게 **한 번만** 되묻는다. 되묻기를 반복해 사용자의 문장을 대신 써 주지 않는다.

## 3. Analyzer

아이디어마다 `rubric.md`의 5기준으로 1~5점을 매기고 표로 보여 준다.

| # | 파일 | 아이디어 | 독립성 | 원자성 | 연결성 | 영속성 | 통찰 | 평균 | 판정 |

평균이 `gate.pass_avg` 이상이면 PASS 후보, 2.0~2.9는 HOLD, 2.0 미만은 DROP 후보다.

3.0~3.4 경계 구간은 보완 제안 1회 후 재채점. 재채점 평균 ≥ 3.5면 후보로 올리고, 미만이면 HOLD로 확정한다. 재채점은 한 번만.

## 4. Converter (후보마다, 노트별 순차)

`<root>/<paths.permanent>/_template.md`의 형식대로 초안을 만든다. frontmatter 키는 정본 순서를 지킨다.

```yaml
---
type: permanent
platform:
source-type: thought
title: <제목>
author:
literature-note:
date: <오늘 KST YYYY-MM-DD>
tags: [주제태그, seed]
luhmann: ""
connections:
  internal: []
  cross: []
---
```

본문은 정본(스타일 A)이며 절 순서가 고정이다.

```
### 날짜 : <date>

### 태그 : #주제태그 #seed

>[!메모]
> (핵심 주장 3~5문장, 한다체, 자기 말)

### 원문 (출처)
> (원문을 옮긴 자리만 따옴표와 [[원본 노트]]로 표시)

### 생각 (질문)
- (추가 질문 3개)

### 연결 (이유)

### 추천 (주제)
```

- `### 날짜`·`### 태그` 줄은 frontmatter 값에서 만든다
- `luhmann`, `connections.internal`·`cross`, `### 연결 (이유)` 절은 6단계에서 채운다
- 인용 표기는 `citation-rules.md`를 따른다. 원문을 옮긴 자리만 따옴표와 `([[원본 노트]])`로 표시하고 나머지는 전부 자기 말이다

초안은 `<root>/<paths.meta>/drafts/<제목>.md`에 저장한다. 게이트가 파일을 읽으므로 이 저장은 건너뛸 수 없다.

## 5. Gate (스크립트가 판정한다)

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" check --draft "<root>/<paths.meta>/drafts/<제목>.md" --source "<원본 노트 경로>" --links-min <gate.min_links> --overlap-max <gate.max_overlap> --ngram <gate.ngram>
```

콜드 스타트 모드이면 끝에 `--cold-start`를 붙인다.

출력은 `{"verdict": "PASS"|"HOLD", "reasons": [...], "overlap": 0.13, "links": 2, "links_required": 2, "tags": ["회의"], "cold_start": false}` 형태다. `tags`는 개수가 아니라 **성장 태그를 뺀 주제 태그 목록**이며, 빈 목록이면 `reasons`에 `태그 없음`이 들어 있다.

`HOLD`면 `reasons`를 그대로 사용자에게 보여 주고 초안을 **한 번만** 고쳐 같은 명령으로 재판정한다.

- `자기 말로 재작성 안 됨` → 원문을 그대로 옮긴 문장을 찾아 자기 말로 다시 쓰거나, 정말 원문 표현이 필요한 자리는 따옴표 + `([[원본 노트]])`로 표시한다
- `연결 부족` → index에 실제로 있는 노트를 찾아 링크한다. 없는 노트 제목을 지어내지 않는다
- `태그 없음` → 주제 태그를 붙인다

재판정에서도 `HOLD`면 승격하지 않고 9단계로 간다. 게이트 출력 JSON은 8·9단계의 `--gate` 인자로 그대로 넘긴다.

## 6. Linker (배치는 LLM, 번호는 스크립트)

index를 읽는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" parse --index "<root>/<paths.index>"
```

`total`이 0이고 `categories`가 비어 있으면 카테고리부터 만들어야 한다. 카테고리 제목과 설명을 제안하고 **사용자 확인을 받은 뒤** 실행한다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" new-category --index "<root>/<paths.index>" --title "<카테고리 제목>" --description "<한 줄 설명>"
```

`{"section": "1A"}`가 나온다. 이어서 첫 번호를 받는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" next --index "<root>/<paths.index>" --section 1A --relation sequential
```

index에 이미 내용이 있으면 `parse` 결과에서 내부 연결(같은 섹션)·횡단 연결(다른 카테고리) 후보와 배치 부모를 고르고 번호를 받는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" next --index "<root>/<paths.index>" --parent <부모번호> --relation sequential|branch
```

`sequential`은 부모와 같은 레벨의 다른 측면, `branch`는 부모의 상세화·하위 개념·예시다. 출력은 `{"next": "1A1c"}`이다.

`linker.py`는 인자 오류를 포함한 모든 오류를 `{"error": "..."}` + 종료 코드 1로 낸다. 오류가 나면 **번호를 지어내지 말고** 멈춰서 사용자에게 원인을 보여 준다.

받은 번호로 초안의 `luhmann`과 `connections.internal`·`connections.cross`를 채우고, `### 연결 (이유)` 절에 번호를 포함한 형식으로 쓴다.

```
### 연결 (이유)
- [[대상 노트]] (1A2) — 이어지는 이유 한 줄
```

## 7. 사용자 확인

| 제목 | 번호 | 부모 | 관계 | 내부 연결 | 횡단 연결 | 게이트 |

를 보여 주고 승인을 받는다. 새 Branch를 만드는 경우와 새 카테고리를 만드는 경우는 따로 한 번 더 확인한다.

`--dry-run`이면 여기서 끝낸다. 초안 파일(`<paths.meta>`의 `drafts/`)까지만 남기고 8·9단계의 기록은 하지 않는다.

## 8. 기록 (순서 고정, 노트 하나씩 끝내고 다음으로)

1. 초안을 `<root>/<paths.permanent>/<제목>.md`로 저장한다. `drafts/`의 초안 파일은 게이트 판정 근거이므로 남겨 둔다.

2. index에 한 줄 삽입한다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" insert --index "<root>/<paths.index>" --number <번호> --title "<제목>" --relation sequential|branch --parent <부모번호>
```

부모 없이 섹션에 처음 넣을 때는 `--parent` 대신 `--section <섹션코드>`를 쓴다. 출력 `{"inserted": ..., "after_line": ..., "total": ...}`의 `inserted`는 **들여쓰기를 지운 표시용 문자열**이다. 이 값을 파일에 다시 쓰지 않는다. 삽입과 상단 통계 줄 갱신은 이 명령 하나로 끝난다.

3. 원본 노트를 Edit 도구로 **줄 단위로만** 고친다. frontmatter의 `processed: false`를 `processed: true`로 바꾸고(키가 없으면 frontmatter 닫는 `---` 바로 위에 `processed: true` 한 줄을 추가하고), 본문 맨 끝에 `- 승격: [[<제목>]] (<번호>)` 한 줄을 덧붙인다. 파일 전체를 다시 쓰지 않는다.

4. 로그를 남긴다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" log --log "<root>/<paths.meta>/promotion-log.jsonl" --source "<원본 노트 경로>" --title "<제목>" --verdict PASS --scores "<5기준 JSON>" --gate "<5단계 check 출력 JSON>" --luhmann <번호> --model "<쓰고 있는 모델 이름>" --profile <profile>
```

`--scores`는 `{"독립성":4,"원자성":5,"연결성":4,"영속성":4,"통찰":4}` 형태의 한 줄 JSON이다. 평균은 스크립트가 계산한다. 모델 이름을 확실히 알 수 없으면 `--model ""`로 둔다(추측해 적지 않는다).

## 9. HOLD · DROP

**HOLD** — 게이트 재판정 실패, 또는 5기준 평균 2.0~2.9

- 원본 frontmatter에 `status: hold`와 `review_at: <오늘+14일, YYYY-MM-DD>`를 Edit로 추가한다. 이미 있으면 값만 갱신한다.
- 같은 `gate.py log` 명령을 `--verdict HOLD --luhmann ""`로 실행한다.
- **파일은 옮기지 않는다.** 표시만 남기고 임시노트 폴더에 그대로 둔다.

**DROP** — 5기준 평균 2.0 미만

- 자동으로 실행하지 않는다. 파일·아이디어·사유를 보여 주고 **사용자 확인을 받는다**.
- 확인되면 `<root>/<paths.meta>/dropped.md`에 `- <YYYY-MM-DD> <원본 경로> : <사유>` 한 줄을 덧붙인다. 파일이 없으면 만든다.
- `gate.py log`를 `--verdict DROP --luhmann ""`로 실행한다.
- 원본 파일은 지우지 않는다. 사용자가 폐기를 거부하면 HOLD로 처리한다.

## 배치 결과 요약 (표준)

| # | 파일 | 아이디어 | 독립성 | 원자성 | 연결성 | 영속성 | 통찰 | 평균 | 게이트 | 판정 | 번호 |

게이트를 돌리지 않은 줄은 `—`로 둔다. 번호 칸은 승격이 확정된 줄만 채운다. 마지막 줄에 다음을 붙인다.

`PASS n / HOLD n / DROP n. commit·push 하세요.`

## 출력 계약 (hard constraints)

- [ ] 번호는 항상 `linker.py`가 낸 값만 쓴다
- [ ] 게이트가 HOLD인 상태로 영구노트를 저장하지 않는다
- [ ] 영구노트 본문이 정본(스타일 A) 절 순서를 지켰다
- [ ] index와 원본 노트는 줄 단위로만 고친다
- [ ] HOLD·DROP 어느 경우에도 원본 파일을 옮기거나 지우지 않았다
- [ ] 인용 밖 문장은 전부 자기 말이다
- [ ] 없는 출처·근거를 만들지 않는다. 지지되지 않는 주장은 `(근거 없음)`으로 표시한다
- [ ] 모든 PASS·HOLD·DROP 판정이 promotion-log에 남았다
- [ ] 폴더 이름은 설정의 `paths.*`에서 읽었고 손으로 적지 않았다

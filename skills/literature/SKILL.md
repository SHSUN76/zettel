---
name: literature
description: 문헌노트(논문·책·세미나·강의·데이터 노트) 한 개를 읽어 "하이라이트 + 나의 메모" 세트마다 영구노트 승격을 시도한다. 채점은 LLM이, 게이트와 루만 번호는 스크립트가 판정하며 원본 문헌노트는 보존한다. `--from <파일>` 을 주면 승격 대신 원자료(`_raw/`)나 교재(pptx·pdf·md)로 문헌노트를 새로 만든다. "이 논문 문헌노트 만들어줘", "원자료 정리해줘", "책 노트에서 영구노트 뽑아줘"에 쓴다. 사용법 - /zettel:literature <문헌노트 경로> [--dry-run] · /zettel:literature --from <파일> [--notes <내 노트>] [--subtype paper|book|seminar|lecture|data|essay]
---

# 문헌노트 → 영구노트 승격

인자: `$ARGUMENTS`

절차는 `promote`와 같고, 입력이 문헌노트 한 개이며 채점 단위가 "하이라이트 + 나의 메모" 세트라는 점만 다르다. 승격 여부의 최종 문지기는 여기서도 스크립트다.

## 생성 모드 — `--from` 이 있을 때

```
/zettel:literature --from <파일> [--notes <내 노트 파일>] [--subtype <유형>]
```

`$ARGUMENTS`에 `--from`이 있으면 **승격을 하지 않는다.** 원본을 읽어 문헌노트 한 장을 새로 만들고 거기서 끝낸다. 아래 G1~G6만 실행하고 0~6단계는 건너뛴다. `--from`이 없으면 이 절은 무시하고 0단계로 간다(승격 동작 그대로).

`--from`은 `_raw/`의 원자료 파일이든 vault 밖의 교재 파일이든 **경로를 그대로** 받는다.

이 모드의 두 원칙이다. 나머지 규칙은 전부 이 둘을 지키기 위한 것이다.

1. **하이라이트는 원문을 글자 그대로 옮긴다.** 다듬거나 요약하거나 이어 붙이지 않는다. 인용 위치(슬라이드 번호·쪽수·절 제목) 표기는 필수다.
2. **`**나의 메모**:`는 LLM이 쓰지 않는다.** `--notes` 파일이나 원자료 안에 같은 주제를 다룬 내 문장이 있으면 **그 문장을 원문 그대로** 옮기고(다듬지 않는다), 없으면 **빈칸으로 둔다.** 생각을 지어내는 순간 이 노트는 채점 근거로 쓸 수 없다.

### G1. 설정과 입력

0단계와 같은 방법으로 설정을 읽는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

`<root>`·`paths.literature`·`paths.raw`는 이 JSON에서 읽는다(폴더 이름을 손으로 적지 않는다). 인자의 상대경로는 `<root>` 기준으로 해석한다. `--from` 파일이 없으면 경로를 보여 주고 멈춘다.

### G2. 원본 읽기 — 형식마다 방법이 다르다

| 입력 | 읽는 법 | 인용 위치 표기 |
|---|---|---|
| `.pdf` | **Read 도구로 직접 읽는다.** 스크립트로 파싱하지 않는다 (`doc_text.py`는 pdf를 거부한다) | `(p. 5)` |
| `.pptx` | `doc_text.py`로 슬라이드별 텍스트를 뽑는다 | `(슬라이드 12)` |
| `.md` · `.txt` | 그대로 읽는다 (Read 도구, 또는 `doc_text.py`) | 절 제목을 적는다 |

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/doc_text.py" "<원본 파일>"
```

- `.pptx` → `{"kind": "pptx", "path": "...", "slides": [{"n": 1, "text": "..."}, ...]}`. `n`이 슬라이드 번호이고 번호 오름차순이다.
- `.md` · `.txt` → `{"kind": "text", "path": "...", "text": "<파일 내용 그대로>"}`
- 그 밖의 형식과 pdf → `{"error": ...}` + 종료 코드 2. pdf는 Read 도구로 돌아가고, 나머지는 사용자에게 알리고 멈춘다.

`--notes`가 있으면 그 파일도 Read한다. 없으면 메모 칸은 전부 빈칸이 된다. 단 `--from`이 `_raw/`의 대화 기록처럼 내 문장을 이미 담고 있으면 그 안의 내 문장을 메모로 옮길 수 있다.

### G3. 유형과 저장 위치

`--subtype`이 없으면 내용을 보고 정한다. 판단이 안 서면 **한 번만** 묻는다.

| `subtype` | 하위 폴더 |
|---|---|
| `paper` | `Journals/` |
| `book` | `Books/` |
| `seminar` | `Seminars/` |
| `lecture` | `Lectures/` |
| `data` | `Datas/` |
| `essay` | (하위 폴더 없이 `paths.literature` 바로 아래) |

`<root>/<paths.literature>/<하위 폴더>/<날짜>_<제목>.md`

- `<날짜>`는 KST 기준 `YYYY-MM-DD`다.
- `<제목>`은 원본의 제목(첫 슬라이드 제목·첫 제목 줄·논문 제목)에서 딴다. 없으면 파일 이름을 쓴다. 지어내지 않는다.
- 같은 이름이 이미 있으면 뒤에 `_2`, `_3`을 붙인다. **기존 파일을 덮어쓰지 않는다.**

### G4. frontmatter — 정본 10키 (설계 §3.2)

키 순서를 지키고, 값이 없어도 키는 남긴다.

```yaml
---
type: literature
subtype: paper           # paper|book|seminar|lecture|data|essay
title: <원본 제목>
author:                  # 없으면 빈 값. 지어내지 않는다
source: "[[_raw/대화기록.md]]"   # DOI·URL·citekey·책 ID·원자료 링크
platform:                # ridibooks·youtube·zotero… 없으면 빈 값
date: <오늘 KST YYYY-MM-DD>
tags: []
processed: false
permanent-notes: []
---
```

- `source` — 원본이 **vault 안**이면 루트 기준 상대경로를 `[[ ]]`로 감싼다(Obsidian 링크가 되어야 한다). vault **밖**이면 절대경로나 DOI·URL을 링크 없이 문자열로 적는다.
- `processed: false` 고정. 이 노트는 아직 승격 전이다.
- `permanent-notes`는 승격할 때 채운다. 지금은 빈 목록이다.
- 정본 밖의 키를 만들지 않는다.

### G5. 본문

제목 줄 `# <제목>` 다음에 **하이라이트 3~7개**를 세트로 쓴다. 세트 하나의 모양은 고정이다.

```
## 하이라이트 1
> 원문 문장 그대로 (슬라이드 12)

**나의 메모**: 
```

- 인용 줄은 원본에 있는 문장이어야 한다. 표현을 고르되 **글자는 고치지 않는다.**
- 메모 줄은 내 문장을 그대로 옮기거나 비운다. 내 노트에서 옮길 때 출처를 따로 적지 않는다(내 글이다).
- 원본에서 고를 문장이 3개도 안 되면 억지로 채우지 말고 있는 만큼만 쓰고 그 사실을 알린다.

### G6. 저장과 안내

1. 파일을 쓴다.
2. `--from`이 `paths.raw` 아래의 파일이면, 그 원자료 파일의 frontmatter `processed: false`를 `processed: true`로 Edit 도구로 **한 줄만** 바꾼다. 원자료 본문은 손대지 않고 파일도 지우지 않는다.
3. 경로 한 줄, 하이라이트 개수, 메모가 채워진 개수를 보고한 뒤 다음을 출력한다.

`나의 메모를 채운 뒤 /zettel:literature <경로> 로 승격하세요`

여기서 끝낸다. **생성 모드는 승격·게이트·루만 번호·promotion-log를 건드리지 않는다.**

### 출력 계약 — 생성 모드 (hard constraints)

- [ ] 하이라이트가 원문 그대로이고 요약·윤문하지 않았다
- [ ] 하이라이트마다 인용 위치를 적었다
- [ ] `**나의 메모**:`에 LLM이 쓴 문장이 하나도 없다 (내 문장의 원문이거나 빈칸이다)
- [ ] 하이라이트가 3~7개다 (고를 문장이 모자라면 그 사실을 알렸다)
- [ ] frontmatter가 §3.2 정본 10키뿐이고 순서를 지켰다
- [ ] vault 안의 원본은 `[[루트 기준 상대경로]]`, 밖이면 문자열로 적었다
- [ ] 같은 이름이 있으면 `_2`를 붙였고 기존 파일을 덮어쓰지 않았다
- [ ] 원자료 본문을 고치거나 지우지 않았다 (`processed` 한 줄만 바꿨다)
- [ ] 폴더 이름은 설정의 `paths.*`에서 읽었고 손으로 적지 않았다
- [ ] 승격·게이트·index·promotion-log를 건드리지 않았다

## 0. 준비 (반드시 먼저)

1. 설정을 읽는다. 인자는 없다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

`{"error": ...}`(종료 코드 2)면 "zettel vault 안에서 실행하세요"를 안내하고 멈춘다. 아래의 `<root>`·`paths.*`·`gate.*`는 전부 이 JSON에서 읽는다.

2. Read 도구로 `${CLAUDE_PLUGIN_ROOT}/skills/_shared/references/rubric.md`, `citation-rules.md`, `gate-rules.md`를 읽는다. 채점은 rubric의 **문헌노트 표**와 문헌 특화 가산·감점 규칙을 쓴다.

3. 콜드 스타트 판정. Glob 도구로 `<root>/<paths.permanent>/**/*.md`(하위 폴더 포함)를 세되, `paths.index`가 들어 있는 하위 폴더 아래의 파일과 `_`로 시작하는 파일은 제외한다. 이 수가 `gate.cold_start_notes`보다 작으면 콜드 스타트 모드이며 4단계 게이트에 `--cold-start`를 붙인다.

## 1. 입력 확인

`$ARGUMENTS`의 문헌노트 경로를 Read한다. 경로가 없으면 `paths.literature` 아래에서 frontmatter `processed: false`인 문헌노트 목록을 보여 주고 하나를 고르게 한다.

frontmatter에서 `title`·`subtype`·`author`·`source`·`date`를 읽는다. 영구노트의 `source-type`은 문헌노트의 `subtype`을 그대로 쓴다.

| 문헌노트 `subtype` | 영구노트 `source-type` |
|---|---|
| `paper` | `paper` |
| `book` | `book` |
| `seminar` | `seminar` |
| `lecture` | `lecture` |
| `data` | `data` |
| `essay` | `web` 또는 `thought` (내용에 맞게) |

frontmatter만으로 판단이 안 되면 사용자에게 한 번 묻는다.

## 2. Extractor — 세트 단위

문헌노트를 `>` 인용(하이라이트)과 바로 뒤의 `**나의 메모**:` 로 이루어진 **세트**로 쪼갠다. 한 세트가 하나의 채점 단위다.

- 메모가 있는 하이라이트를 먼저 처리한다.
- 메모 없는 단독 하이라이트는 5기준 사전 추정 평균이 3.0 이상인 세트만 후보로 올린다(3.0 미만은 표에 `후보 제외`로 표시하고 이유 한 줄). 후보로 올리더라도 통찰 점수를 낮게 준다.
- 한 세트에 주장이 둘이면 둘로 나눈다. Feynman 검사에 걸리면 **한 번만** 되묻는다.

## 3. Analyzer

세트마다 rubric의 문헌노트 5기준으로 1~5점을 매기고 표로 보여 준다.

| # | 하이라이트 | 나의 메모 | 독립성 | 원자성 | 연결성 | 영속성 | 통찰 | 평균 | 판정 |

문헌 특화 규칙: 메모 없는 단독 하이라이트는 통찰 감점, 하이라이트에 자기 메모가 붙어 있으면 통찰 가산, 저자의 주장을 자신의 경험·기존 지식과 연결했으면 연결성 가산.

평균이 `gate.pass_avg` 이상이면 PASS 후보, 2.0~2.9는 HOLD, 2.0 미만은 DROP 후보다.

3.0~3.4 경계 구간은 보완 제안 1회 후 재채점. 재채점 평균 ≥ 3.5면 후보로 올리고, 미만이면 HOLD로 확정한다. 재채점은 한 번만.

## 4. Converter → Gate → Linker → 확인

`promote`의 4~7단계를 그대로 따른다. 본문은 정본(스타일 A)이며, 문헌노트에서만 다른 점은 초안 frontmatter다.

- `source-type`: 1단계 표에서 정한 값
- `literature-note`: `"[[<원본 문헌노트 제목>]]"`
- `author`·`platform`: 문헌노트의 값을 그대로 옮기고, 없으면 비운다. 지어내지 않는다
- `tags`: 주제 태그 최대 3개 + `seed`
- `luhmann: ""`, `connections`는 Linker 단계에서 채운다

초안은 `<root>/<paths.meta>/drafts/<제목>.md`에 저장한 뒤 게이트를 돌린다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" check --draft "<root>/<paths.meta>/drafts/<제목>.md" --source "<문헌노트 경로>" --links-min <gate.min_links> --overlap-max <gate.max_overlap> --ngram <gate.ngram>
```

콜드 스타트 모드이면 `--cold-start`를 붙인다. 출력의 `tags`는 개수가 아니라 주제 태그 목록이다. `HOLD`면 `reasons`를 보여 주고 **한 번만** 고쳐 재판정한다.

원문 표현을 옮긴 자리는 따옴표와 `([[<원본 문헌노트 제목>]])`로 표시한다. 표시 없이 옮긴 문장은 중복률에 잡혀 `자기 말로 재작성 안 됨`으로 HOLD된다.

번호는 반드시 스크립트에서 받는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" parse --index "<root>/<paths.index>"
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" next --index "<root>/<paths.index>" --parent <부모번호> --relation sequential|branch
```

index가 비어 있으면(`total`이 0) 카테고리 제목을 제안하고 사용자 확인 후 `new-category --index "<root>/<paths.index>" --title "<제목>" --description "<설명>"`을 실행해 `{"section": "1A"}`를 받고, 이어서 `next --section 1A --relation sequential`로 첫 번호를 받는다. `linker.py`는 인자 오류를 포함한 모든 오류를 `{"error": ...}` + 종료 코드 1로 내므로, 오류가 나면 번호를 지어내지 말고 멈춘다.

배치·연결·번호를 표로 보여 주고 승인을 받는다. `--dry-run`이면 여기서 끝낸다.

## 5. 기록 (순서 고정, 세트 하나씩)

1. 초안을 `<root>/<paths.permanent>/<제목>.md`로 저장한다.

2. index에 한 줄 삽입한다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" insert --index "<root>/<paths.index>" --number <번호> --title "<제목>" --relation sequential|branch --parent <부모번호>
```

출력의 `inserted`는 들여쓰기를 지운 표시용 문자열이므로 파일에 다시 쓰지 않는다.

3. **원본 문헌노트는 보존한다.** Edit 도구로 세 자리만 고친다. frontmatter의 `processed: false`를 `processed: true`로 바꾸고, `permanent-notes`에 `"[[<제목>]]"`을 더하고, 해당 하이라이트 세트 바로 아래(또는 문헌노트 맨 끝)에 `- 승격: [[<제목>]] (<번호>)` 한 줄을 덧붙인다. 하이라이트 원문과 내 메모는 지우거나 고치지 않는다.

4. 로그를 남긴다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" log --log "<root>/<paths.meta>/promotion-log.jsonl" --source "<문헌노트 경로>" --title "<제목>" --verdict PASS --scores "<5기준 JSON>" --gate "<게이트 출력 JSON>" --luhmann <번호> --model "<쓰고 있는 모델 이름>" --profile <profile>
```

모델 이름을 확실히 알 수 없으면 `--model ""`로 둔다(추측해 적지 않는다).

## 6. HOLD · DROP

`promote`의 9단계와 같다. HOLD는 원본 문헌노트 frontmatter에 `status: hold`와 `review_at: <오늘+14일>`을 적고 `--verdict HOLD --luhmann ""`로 로그를 남긴다. **파일은 어느 경우에도 옮기지 않는다.** DROP은 사용자 확인 후 `<root>/<paths.meta>/dropped.md`에 사유를 적고 파일은 남긴다.

## 배치 결과 요약 (표준)

| # | 하이라이트 | 아이디어 | 평균 | 게이트 | 판정 | 번호 |

게이트를 돌리지 않은 줄은 `—`로 둔다. 마지막 줄에 다음을 붙인다.

`PASS n / HOLD n / DROP n. commit·push 하세요.`

## 출력 계약 — 승격 모드 (hard constraints)

- [ ] 원본 문헌노트의 하이라이트와 내 메모를 고치지 않았다 (`processed`·`permanent-notes`·승격 링크 한 줄만 추가)
- [ ] 번호는 항상 `linker.py`가 낸 값만 쓴다
- [ ] 게이트가 HOLD인 상태로 영구노트를 저장하지 않는다
- [ ] 영구노트 본문이 정본(스타일 A) 절 순서를 지켰다
- [ ] index와 원본은 줄 단위로만 고친다
- [ ] 원문을 옮긴 자리는 따옴표와 `[[원본]]`으로 표시했고 나머지는 자기 말이다
- [ ] `literature-note`와 `source-type`을 채웠고 없는 저자·출처를 만들지 않았다
- [ ] 근거 없는 주장은 `(근거 없음)`으로 표시하고 없는 출처를 만들지 않는다
- [ ] 모든 PASS·HOLD·DROP 판정이 promotion-log에 남았다
- [ ] 폴더 이름은 설정의 `paths.*`에서 읽었고 손으로 적지 않았다

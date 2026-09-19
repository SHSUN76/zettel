# zettel 운영 규칙

이 폴더는 개인 제텔카스텐 vault다. 읽은 것과 스친 생각을 모아 두었다가, 자기 말로 다시 쓴 영구노트로 승격시키고, 노트끼리 링크로 이어 붙이는 것이 전부다.

1. 노트는 `/zettel:*` 스킬로 만든다. `capture`(한 줄 생각) → `literature`(원자료·문헌노트) → `promote`(승격) → `status`(현황 보고서).
2. 원문을 그대로 옮긴 자리는 따옴표와 `[[원본 노트]]` 링크로 표시하고, 나머지는 반드시 자기 말로 쓴다. 복사해 둔 것은 이해한 것이 아니다.
3. 영구노트의 루만 번호(예 `1A1a`)와 `3.Permanent_Notes/SlipBox/index.md`는 스크립트가 관리한다. 손으로 번호를 만들거나 index를 고치지 않는다.
4. 승격 의식: `/zettel:capture` → `/zettel:promote` → `/zettel:status` → `git add -A && git commit -m "zettel: <날짜>" && git push`.
5. `_meta/promotion-log.jsonl`과 `_reports/`는 판정 기록이다. 손으로 고치지 않는다.

## 폴더

| 폴더 | 무엇이 들어가나 |
|---|---|
| `_raw/` | 원자료. 아직 읽지 않은 것, 받아 둔 것. 본문을 고치지 않는다 |
| `1.Fleeting_Notes/` | 임시노트. 스친 한 줄 생각 |
| `2.Literature_Notes/` | 문헌노트. `Journals` 논문 · `Books` 책 · `Seminars` 세미나 · `Lectures` 강의 · `Datas` 데이터 |
| `3.Permanent_Notes/` | 영구노트. 루만 번호가 붙은 자기 말 노트 |
| `3.Permanent_Notes/SlipBox/index.md` | 루만 번호 트리. 스크립트만 고친다 |
| `_meta/` | `gate-rules.md` · `rubric.md` · `promotion-log.jsonl` |
| `_reports/` | `status_YYMMDD.md` · `.json` |

흐름은 한 방향이다. **원자료 → 문헌노트 → 영구노트**, 그리고 **임시노트 → 영구노트**. 원자료와 문헌노트는 승격해도 지우지 않는다. 인용의 출처로 남는다.

## 세 노트 유형의 frontmatter 정본

키 순서는 고정이고, 값이 없어도 키는 남긴다. 날짜는 따옴표 없이, 리스트는 인라인 `[a, b]`, `[[링크]]` 값은 따옴표로 감싼다.

**영구노트**

```yaml
type: permanent
platform:                # 출처 플랫폼(ridibooks·youtube…), 없으면 빈 값
source-type: paper       # paper|book|chat|lecture|seminar|thought|web|data
title:                   # 파일명과 같다
author:
literature-note:         # "[[문헌노트 제목]]" 또는 빈 값
date: YYYY-MM-DD
tags: [태그1, 태그2]
luhmann: "6A57"
connections:
  internal: ["[[같은 분기 노트]]"]
  cross: ["[[다른 분기 노트]]"]
```

**문헌노트**

```yaml
type: literature
subtype: paper           # paper|book|seminar|lecture|data|essay
title:
author:
source:                  # DOI·URL·citekey·책 ID
platform:                # ridibooks·youtube·zotero…
date: YYYY-MM-DD
tags: []
processed: false
permanent-notes: []
```

**임시노트**

```yaml
type: fleeting
created: YYYY-MM-DDTHH:MM
processed: false
tags: []
source:                  # 출처가 있으면 "[[...]]" 또는 URL
```

원자료(`_raw/`)는 네 줄만 붙인다: `type: raw` · `source` · `date` · `processed: false`.

## 영구노트 본문 정본 (스타일 A)

```
### 날짜 : 2026-09-19

### 태그 : #제텔카스텐 #노트법

>[!메모]
> 연결 없는 노트는 검색어를 기억하는 동안에만 살아 있다. 들어오는 링크가 없는 노트는
> 다른 노트를 읽다가 우연히 만나는 경로가 없으므로 사실상 삭제된 것과 같다.

### 원문 (출처)
> "Ein Zettel allein ist wertlos" ([[제텔카스텐 독서노트]])

### 생각 (질문)
- 인바운드와 아웃바운드 중 무엇이 재방문을 더 부르는가
- 링크 두 개는 충분한 하한인가

### 연결 (이유)
- [[외부 기억은 대화 상대다]] (1A1) — 대화가 되려면 노트가 이어져 있어야 한다

### 추천 (주제)
- 그래프 뷰에서 고아 노트 찾기
```

절 순서는 날짜 → 태그 → 메모 → 원문 → 생각 → 연결 → 추천이다. 다른 서식으로 적힌 옛 노트는
`skills/_shared/scripts/normalize.py`가 이 서식으로 옮긴다. 옮길 때 헤더만 바뀌고 텍스트 줄은 하나도 버리지 않는다.

## 승격 게이트

세 조건을 모두 통과해야 영구노트가 된다. 판정은 스크립트가 하고, 점수가 아무리 높아도 게이트를 이기지 못한다.

| 조건 | 기준 |
|---|---|
| 자기 말로 재작성 | 인용 밖 본문의 8-gram 중복률 ≤ 0.20 |
| 주제 태그 | 성장 태그(seed·growing·evergreen)를 뺀 태그 ≥ 1 |
| 관련 노트 링크 | 원본을 뺀 서로 다른 `[[링크]]` ≥ 2 (영구노트 5개 미만이면 1) |

자세한 규칙은 `_meta/gate-rules.md`와 `_meta/rubric.md`에 있다.

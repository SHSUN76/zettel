# zettel

개인 제텔카스텐 플러그인. 원자료·임시노트·문헌노트를 루만 번호가 붙은 영구노트로 승격한다.

판단은 LLM이 하고 결정은 스크립트가 한다. 5기준 채점과 연결 후보 고르기는 모델의 몫이지만, 승격 게이트(중복률·링크 수·주제 태그)와 루만 번호 계산·index 삽입·본문 정규화는 파이썬 표준 라이브러리 스크립트가 맡는다. **게이트가 HOLD를 내면 점수와 무관하게 승격되지 않는다.**

수업용 [llmwiki](https://github.com/SHSUN76/llmwiki)(MIT, 같은 저자)에서 갈라져 나왔다. 학번·교수 초대·일일노트·마일스톤을 걷어내고 개인 vault 하나를 오래 굴리는 쪽으로 맞췄다.

## 설치

```
claude plugin marketplace add SHSUN76/sehosun
claude plugin install zettel@sehosun
```

Claude Code를 다시 시작하면 `/zettel:` 로 다섯 개 스킬이 잡힌다. 파이썬 3.10 이상이 필요하고 외부 패키지는 쓰지 않는다.

첫 vault는 이렇게 만든다.

```
/zettel:init --root ~/zettel
```

GitHub 백업까지 한 번에 하려면 저장소 이름을 준다. 원격은 `https://` 로 고정된다 — 22번 포트(SSH)가 막힌 망에서도 push가 되게 하려는 장치다.

```
/zettel:init --root ~/zettel --github-private zettel-vault
```

## 스킬

| 스킬 | 하는 일 | 사용법 |
|---|---|---|
| `init` | 폴더·템플릿·git·(선택) GitHub 비공개 저장소·Obsidian 보관소 등록 | `/zettel:init [--root 경로] [--github-private 이름]` |
| `capture` | 스친 한 줄 생각을 임시노트 한 장으로 즉시 저장 | `/zettel:capture <한 줄 생각>` |
| `promote` | 임시노트를 5기준으로 채점하고 게이트를 통과한 것만 영구노트로 승격 | `/zettel:promote [경로\|--only 오늘\|--all] [--dry-run]` |
| `literature` | 원자료·교재로 문헌노트를 만들거나, 문헌노트의 "하이라이트 + 나의 메모" 세트를 승격 | `/zettel:literature <문헌노트 경로> [--dry-run]` · `/zettel:literature --from <파일> [--notes <내 노트>] [--subtype paper\|book\|seminar\|lecture\|data\|essay]` |
| `status` | 현황 보고서 생성, 고아 노트·성장 태그 승급 후보 제시 | `/zettel:status` |

`literature`는 모드가 둘이다. 문헌노트 경로를 주면 승격이고, `--from`을 주면 `_raw/`의 원자료나 밖에 있는 교재(pptx·pdf·md)로 문헌노트를 새로 만든다.

```
/zettel:literature --from _raw/AI_Chats/20260918-대화.md --subtype essay
```

생성 모드에서 하이라이트는 원문을 글자 그대로 인용하고 위치(`(슬라이드 12)`·`(p. 5)`)를 붙이며, `**나의 메모**:`는 LLM이 쓰지 않는다 — 내 문장이 있으면 그대로 옮기고 없으면 빈칸으로 둔다. `.pdf`는 Read 도구로 읽고 `.pptx`는 `skills/_shared/scripts/doc_text.py`가 슬라이드별 텍스트를 뽑는다(표준 라이브러리만 쓴다).

스킬 본문에는 폴더 이름이 없다. 모든 경로는 vault 루트의 `zettel.json`에서 읽으므로 폴더 구조를 바꾸려면 설정만 고치면 된다.

### 승격 의식

```
/zettel:capture <한 줄 생각>
/zettel:promote
/zettel:status
git add -A && git commit -m "zettel: 2026-09-19" && git push
```

## vault 구조

`init`이 만드는 vault다. 폴더 이름은 `zettel.json`의 `paths.*`가 정한다.

```
zettel/
├── zettel.json                     # 설정 (경로·게이트 임계값)
├── CLAUDE.md                       # 운영 규칙 + 세 노트 유형 정본
├── README.md                       # 폴더와 흐름
├── _raw/                           # 원자료: 아직 읽지 않은 것, 받아 둔 것
├── 1.Fleeting_Notes/               # 스친 한 줄 생각
├── 2.Literature_Notes/             # 문헌노트
│   └── Journals/ Books/ Seminars/ Lectures/ Datas/
├── 3.Permanent_Notes/              # 자기 말로 쓴 영구노트
│   └── SlipBox/index.md            # 루만 번호 트리 (스크립트가 관리)
├── _meta/                          # gate-rules.md · rubric.md · promotion-log.jsonl
└── _reports/                       # status_YYMMDD.md · .json
```

흐름은 두 갈래다. `_raw/` → `2.Literature_Notes/` → `3.Permanent_Notes/` 와 `1.Fleeting_Notes/` → `3.Permanent_Notes/`. 원자료와 문헌노트는 승격해도 지우지 않는다 — 인용의 출처로 남는다.

## 세 노트 유형의 정본

키 순서는 고정이고, 값이 없어도 키는 남긴다. 날짜는 따옴표 없이, 리스트는 인라인 `[a, b]`, `[[링크]]` 값은 따옴표로 감싼다. 정본 밖의 키는 제거하되 `aliases`와 `updated`는 허용한다.

| 유형 | 키 순서 |
|---|---|
| 영구노트 | `type` `platform` `source-type` `title` `author` `literature-note` `date` `tags` `luhmann` `connections{internal,cross}` |
| 문헌노트 | `type` `subtype` `title` `author` `source` `platform` `date` `tags` `processed` `permanent-notes` |
| 임시노트 | `type` `created` `processed` `tags` `source` |
| 원자료 | `type` `source` `date` `processed` |

영구노트 본문도 정본이 있다. 절 순서는 날짜 → 태그 → 메모 → 원문 → 생각 → 연결 → 추천이다.

```
### 날짜 : 2026-09-19

### 태그 : #제텔카스텐 #노트법

>[!메모]
> (핵심 주장, 자기 말로)

### 원문 (출처)
> (인용·링크)

### 생각 (질문)
- 

### 연결 (이유)
- [[노트]] (1A2) — 이유

### 추천 (주제)
- 
```

다른 서식으로 적힌 옛 노트는 `skills/_shared/scripts/normalize.py`가 이 서식으로 옮긴다. 헤더만 바뀌고 텍스트 줄은 하나도 버리지 않으며, 옮긴 뒤 `assert_text_preserved()`가 그것을 검사한다. 표에 없는 헤더는 `### 생각 (질문)` 아래 `**원헤더**` 소제목으로 남는다.

```
python skills/_shared/scripts/normalize.py --check 3.Permanent_Notes/*.md
```

서식과 보존 여부만 JSON으로 찍는다. 파일은 고치지 않는다.

## 게이트 규칙

승격에는 세 조건이 모두 필요하다. 판정은 `skills/promote/scripts/gate.py`가 한다.

| 조건 | 기준 | 미달 사유 |
|---|---|---|
| 내 언어로 재작성 | 인용 밖 본문의 8-gram 중복률 ≤ `gate.max_overlap` (기본 0.20) | `자기 말로 재작성 안 됨` |
| 주제 태그 | 성장 태그(`seed`/`growing`/`evergreen`)를 뺀 태그 ≥ 1 | `태그 없음` |
| 관련 노트 링크 | 원본을 뺀 서로 다른 `[[링크]]` ≥ `gate.min_links` (기본 2) | `연결 부족` |

- 중복률은 초안에서 frontmatter, 연결 섹션, `"…"([[원본]])` 형태의 인용 구간을 지운 뒤 잰다. 따옴표와 링크로 정직하게 표시한 인용은 걸리지 않고, 표시 없이 옮긴 문장만 잡힌다.
- **콜드 스타트**: 영구노트가 `gate.cold_start_notes`(기본 5)개 미만이면 링크 기준이 1로 내려가고 원본을 향한 링크도 인정된다. 빈 vault에서 첫 영구노트가 나올 수 있게 하려는 장치다.
- 판정은 PASS / HOLD / DROP 세 갈래다. HOLD는 원본에 `status: hold`와 `review_at`(+14일)을 적고 **파일을 옮기지 않으며**, 기한이 지나면 다음 스캔에 다시 올라온다. DROP은 반드시 사용자 확인을 받고 `_meta/dropped.md`에 사유만 남긴다. **파일은 어떤 경우에도 지우지 않는다.**
- 5기준(독립성·원자성·연결성·영속성·통찰) 평균은 LLM이 매기지만 게이트를 이기지 못한다. 자세한 규칙은 `skills/_shared/references/`의 `rubric.md`·`gate-rules.md`·`citation-rules.md`에 있다.

## 기록

**`_meta/promotion-log.jsonl`** — 승격을 시도할 때마다 한 줄이 붙는다.

```json
{"ts":"2026-09-19T15:20:11+09:00","source":"...","title":"...","scores":{"독립성":4,"원자성":5,"연결성":4,"영속성":4,"통찰":4},"avg":4.2,"gate":{"verdict":"PASS","reasons":[],"overlap":0.08,"links":2,"links_required":2,"tags":["회의"],"cold_start":false},"verdict":"PASS","luhmann":"1A3","model":"...","profile":"personal"}
```

`ts`는 KST ISO 시각이다. HOLD와 DROP도 남는다.

**`_reports/status_YYMMDD.{md,json}`** — `/zettel:status`가 만드는 집계다. 폴더별 노트 수, 임시노트 처리 수, 성장 태그 분포, 노트당 평균 링크 수, 고아 노트 목록, HOLD 사유 상위 3개, 마지막 commit 시각이 들어 있다.

## 함께 쓰면 좋은 것

- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) (MIT) — Obsidian 문법(callout·properties·Dataview 등)을 다룰 때 함께 설치하면 좋다. 이 플러그인은 코드를 포함하지 않고 안내만 한다.

## 개발

```
python -m pytest -q
```

`pytest.ini`가 스크립트 폴더를 `pythonpath`에 넣으므로 설치 없이 돈다. 표준 라이브러리만 쓰고, 파일은 UTF-8(BOM 없음)·LF로 쓴다.

실제 vault의 index로 왕복 손실이 없는지 확인하려면 환경변수를 주고 돌린다.

```
ZETTEL_REAL_INDEX=<index.md 경로> python -m pytest tests/test_linker.py -q
```

플러그인 자체 검증은 `claude plugin validate .`이다.

## 라이선스

MIT. 파생 관계와 차용 문안의 출처는 [NOTICE.md](NOTICE.md)에 적었다.

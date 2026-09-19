# zettel

개인 제텔카스텐 vault다. 읽은 것과 스친 생각을 모아 두었다가 자기 말로 다시 쓴 영구노트로 승격시키고, 노트끼리 링크로 이어 붙인다. 운영 규칙은 `CLAUDE.md`에 있고 이 문서는 폴더와 흐름을 설명한다.

## 폴더

| 폴더 | 무엇이 들어가나 | 누가 만드나 |
|---|---|---|
| `_raw/` | 원자료. AI 대화 기록, 받아 둔 글, 스크랩. 본문을 고치지 않는다 | 나 |
| `1.Fleeting_Notes/` | 스친 한 줄 생각 | `/zettel:capture` |
| `2.Literature_Notes/` | 문헌노트. `Journals` · `Books` · `Seminars` · `Lectures` · `Datas` | `/zettel:literature --from` |
| `3.Permanent_Notes/` | 자기 말로 쓴 영구노트 | `/zettel:promote`, `/zettel:literature` |
| `3.Permanent_Notes/SlipBox/index.md` | 루만 번호 트리 | 스크립트 |
| `_meta/` | `gate-rules.md` · `rubric.md` · `promotion-log.jsonl` | 나 · 스크립트 |
| `_reports/` | `status_YYMMDD.md` · `.json` | `/zettel:status` |

각 폴더의 `_template.md`는 새 노트의 서식이다.

## 두 갈래 흐름

```
_raw/  →  2.Literature_Notes/  →  3.Permanent_Notes/
1.Fleeting_Notes/             →  3.Permanent_Notes/
```

읽을 거리는 원자료로 받아 문헌노트에서 하이라이트와 내 메모로 쪼갠 뒤 승격한다. 스친 생각은 임시노트로 바로 받아 승격한다. 원자료와 문헌노트는 승격해도 지우지 않는다 — 인용의 출처로 남는다.

## 승격 의식

```
/zettel:capture <한 줄 생각>
/zettel:promote
/zettel:status
git add -A && git commit -m "zettel: 2026-09-19" && git push
```

승격 게이트는 셋을 본다. 인용을 뺀 본문의 원문 중복률이 20%를 넘지 않을 것, 주제 태그가 하나 이상 있을 것, 다른 노트로 나가는 링크가 두 개 이상 있을 것(영구노트가 다섯 개 미만인 초기에는 한 개). 셋 중 하나라도 걸리면 점수와 무관하게 HOLD다.

HOLD된 노트는 옮기지 않는다. 원본에 `status: hold`와 `review_at`(+14일)이 붙고, 기한이 지나면 다음 승격 스캔에 다시 올라온다.

## 기록

- `_meta/promotion-log.jsonl` — 승격을 시도할 때마다 한 줄이 붙는다. 판정, 5기준 점수, 게이트가 잰 중복률·링크 수·태그, 부여된 루만 번호가 들어 있다.
- `_reports/status_YYMMDD.md` / `.json` — `/zettel:status`가 만드는 집계다. 폴더별 노트 수, 임시노트 처리 수, 성장 태그 분포, 노트당 평균 링크 수, 고아 노트 목록, HOLD 사유 상위가 표로 정리된다.

---
name: status
description: vault 현황을 집계해 보고서(md·json)를 만들고 요약표·고아 노트·성장 태그 승급 후보를 보여 준다. 승인받은 노트만 성장 태그를 바꾼다. "현황 보여줘", "보고서 만들어줘", "내 vault 얼마나 됐어", "고아 노트 있어?", 정리한 뒤 점검할 때 쓴다. 사용법 - /zettel:status
---

# vault 현황 보고서

인자: `$ARGUMENTS`

## 0. 준비

설정을 읽는다. 인자는 없다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

`{"error": ...}`(종료 코드 2)면 "zettel vault 안에서 실행하세요"를 안내하고 멈춘다. `<root>`·`paths.*`·`growth.*`는 이 JSON에서 읽는다.

## 1. 보고서 생성

```
python "${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/report.py" --root "<root>" --json
```

출력은 `{"md": "<보고서 md 경로>", "json": "<보고서 json 경로>"}`다. 두 파일은 `paths.reports` 아래 `status_YYMMDD.md` / `.json`으로 만들어진다. 날짜는 KST 기준이다.

이 명령은 파일을 새로 쓰므로 한 번만 실행한다. 같은 날 다시 돌리면 그날 보고서를 덮어쓴다. 실패하면 stderr를 그대로 보여 주고 멈춘다.

## 2. 요약표

만들어진 `.md` 파일을 Read해서 그 내용을 요약표로 보여 준다. 숫자는 보고서에 적힌 값을 그대로 옮기고 다시 계산하지 않는다.

| 항목 | 값 |
|---|---|
| 노트 수 (원자료/임시/문헌/영구) | |
| 임시노트 처리 완료 | |
| 성장 단계 (seed/growing/evergreen) | |
| 노트당 평균 링크 수 | |
| 고아 노트 | |
| 승격 판정 (PASS/HOLD/DROP) | |
| 마지막 commit | |

보고서에 `## HOLD 사유 상위`가 있으면 그대로 덧붙인다. 가장 잦은 HOLD 사유가 다음에 고칠 습관이다.

보고서에 `## 고아 노트 (들어오는 링크 0)` 목록이 있으면 보여 주고, 승격할 때 어느 노트에서 이 노트로 링크를 걸면 좋을지 한 줄로 제안한다. 고아 노트를 대신 고쳐 주지는 않는다.

## 3. 성장 태그 승급 (승인받은 것만)

보고서 `.json`을 Read해서 `growth_candidates`의 `growing`·`evergreen` 목록을 읽는다. 기준은 인바운드 링크 수이며 `growth.growing_inbound`·`growth.evergreen_inbound`가 그 값이다.

후보를 **한 번에 하나씩** 보여 주고 확인을 받는다.

`[[<노트 제목>]] — 들어오는 링크 <n>개. seed → growing 으로 올릴까요?`

승인된 노트만 고친다. `<root>/<paths.permanent>/<노트 제목>.md`를 Edit 도구로 열어 frontmatter `tags` **한 줄만** 바꾼다.

- `seed` → `growing`, `growing` → `evergreen`으로 성장 태그만 교체한다
- 주제 태그는 손대지 않는다. 순서도 바꾸지 않는다
- 본문의 `### 태그 :` 줄에도 같은 성장 태그가 있으면 그 줄만 함께 맞춘다
- 성장 태그가 없으면 `seed`를 넣지 말고 후보에서 뺀 뒤 사용자에게 알린다

거절한 후보는 그대로 둔다. 후보가 없으면 "승급 후보 없음"이라고만 알린다.

## 4. 마무리

마지막 줄로 안내한다.

`보고서: <md 경로>. commit·push 하세요.`

`git add -A && git commit -m "zettel: status <오늘 날짜>" && git push`

## 출력 계약 (hard constraints)

- [ ] 숫자는 `report.py`가 낸 보고서 값을 그대로 옮겼고 직접 세지 않았다
- [ ] 성장 태그는 승인받은 노트만 바꿨다
- [ ] `tags` 줄(과 본문의 `### 태그 :` 줄)만 고쳤고 주제 태그는 건드리지 않았다
- [ ] 보고서 `.md`·`.json`을 손으로 고치지 않았다
- [ ] 성장 후보를 한 번에 하나씩 확인받았다
- [ ] 폴더 이름은 설정의 `paths.*`에서 읽었고 손으로 적지 않았다

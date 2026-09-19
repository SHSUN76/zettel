---
name: capture
description: 스친 한 줄 생각을 임시노트 파일 한 장으로 즉시 저장한다. 사용자가 쓴 문장을 그대로 남기고 LLM이 다듬지 않는다. "메모해줘", "이거 적어둬", "캡처", "생각났는데 적어놔", 읽다가 떠오른 한 줄을 남길 때 쓴다. 사용법 - /zettel:capture <한 줄 생각>
---

# 한 줄 생각 캡처

인자: `$ARGUMENTS`

목적은 속도다. 스친 생각을 잃지 않게 파일 한 장으로 즉시 떨어뜨린다. **문장은 사용자 것이며 LLM이 고치지 않는다.**

## 0. 준비

설정을 읽는다. 인자는 없다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

`{"error": ...}`(종료 코드 2)면 "zettel vault 안에서 실행하세요"를 안내하고 멈춘다. `<root>`와 `paths.fleeting`은 이 JSON에서 읽는다.

## 1. 문장 확보

`$ARGUMENTS`가 있으면 그것이 본문이다. 비어 있으면 한 줄만 묻는다.

`한 줄로 적어 주세요.`

답을 받으면 더 묻지 않는다. 되묻기·확인·요약 제안을 하지 않는다.

## 2. 파일명

`YYYYMMDD-HHMM-<슬러그>.md` — 날짜와 시각은 KST 기준이다.

슬러그는 본문에서 만든다.

1. 한글·영문·숫자가 아닌 문자는 모두 지운다 (공백·문장부호·이모지 포함)
2. 남은 문자열의 앞에서 12자까지만 쓴다
3. 12자를 자른 결과가 비면 슬러그 없이 `YYYYMMDD-HHMM.md`로 한다

같은 이름이 이미 있으면 뒤에 `-2`, `-3`을 붙인다. 기존 파일을 덮어쓰지 않는다.

저장 위치는 `<root>/<paths.fleeting>/<파일명>`이다.

## 3. 저장

`<root>/<paths.fleeting>/_template.md`를 Read해 그 서식대로 쓴다. frontmatter 정본은 다섯 키다.

```yaml
---
type: fleeting
created: YYYY-MM-DDTHH:MM
processed: false
tags: []
source:
---
```

치환은 셋뿐이다.

- `{{datetime}}` → KST 시각 (`YYYY-MM-DDTHH:MM`)
- `{{text}}` → **사용자가 말한 문장 그대로**
- `tags`는 빈 목록으로 둔다. 태그는 승격할 때 붙인다

`source`는 출처가 분명할 때만 채운다(`"[[원자료 파일]]"` 또는 URL). 모르면 빈 값으로 둔다. 지어내지 않는다.

`processed: false`는 그대로 둔다. 이 값이 `promote`의 스캔 대상 표시다.

## 4. 보고

한 줄로만 알린다.

`저장: <파일명>`

파일 내용을 다시 보여 주거나, 승격을 권하거나, 생각을 발전시켜 주지 않는다. 승격은 `/zettel:promote`가 할 일이다.

## 출력 계약 (hard constraints)

- [ ] 본문은 사용자가 말한 문장 그대로다 (맞춤법·어투·길이를 고치지 않았다)
- [ ] 요약·부연·해석을 덧붙이지 않았다
- [ ] 파일명이 `YYYYMMDD-HHMM-<한글·영문·숫자 12자>.md` 규칙을 지켰다
- [ ] 기존 파일을 덮어쓰지 않았다
- [ ] frontmatter가 정본 5키(`type`·`created`·`processed`·`tags`·`source`)이고 `processed: false`를 남겼다
- [ ] 폴더 이름은 설정의 `paths.fleeting`에서 읽었고 손으로 적지 않았다

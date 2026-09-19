# _raw — 원자료

아직 읽지 않았거나 읽는 중인 것을 그대로 두는 자리다. AI 대화 기록, 남이 보내 준 글, 스크랩, 받아 둔 메모가 여기 들어온다.

**본문은 손대지 않는다.** 원자료는 읽을 거리이지 내 생각이 아니다. 여기 있는 글을 고치는 순간 원본과 대조할 수 없게 된다.

frontmatter는 네 줄만 붙인다.

```yaml
---
type: raw
source:                  # 어디서 왔는지 — URL · 사람 이름 · 앱 이름
date: YYYY-MM-DD         # 받은 날
processed: false         # 문헌노트로 옮겼으면 true
---
```

## 흐름

원자료를 읽고 인용할 만한 대목이 생기면 문헌노트로 옮긴다.

```
/zettel:literature --from _raw/<파일>
```

문헌노트에서 하이라이트마다 내 메모를 채운 뒤 승격한다.

```
/zettel:literature 2.Literature_Notes/<파일>
```

옮긴 원자료는 `processed: true`로 바꾼다. 파일은 지우지 않는다 — 인용의 출처로 남는다.

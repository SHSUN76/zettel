# Changelog

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따른다.

## [0.1.0] - 2026-09-19

llmwiki 0.2.1(MIT, 같은 저자)에서 분기한 첫 판이다. 학생용 수업 도구를 개인 제텔카스텐용으로 다시 맞췄다.

### Added

- `_raw/` 원자료 계층. 아직 읽지 않은 대화 기록·스크랩을 두는 자리이며 `type: raw` 네 줄만 붙는다. `/zettel:literature --from _raw/<파일>` 로 문헌노트가 된다.
- 세 노트 유형의 **정본 frontmatter**. `mdnote.CANONICAL_KEYS` 가 키 순서를 정하고 `canonical_frontmatter()` 가 그 순서대로 채운다. 허용 밖 키는 값과 함께 돌려주므로 이관 보고서에 적을 수 있다.
- `mdnote.dump_frontmatter()` 가 정본 형식으로 쓴다 — 날짜는 따옴표 없이, 리스트는 인라인 `[a, b]`, `[[링크]]` 값은 따옴표, `connections` 는 `internal`·`cross` 블록에 인라인 리스트, 빈 값은 키만.
- `skills/_shared/scripts/normalize.py`. 영구노트 본문을 정본(스타일 A)으로 옮긴다. `detect_style()` 이 A·B·C·other 를 가리고, `normalize_permanent_body()` 가 헤더만 바꾸며, `text_lines()`·`assert_text_preserved()` 가 텍스트 줄이 하나도 없어지지 않았는지 검사한다. `python normalize.py --check <파일들>` 로 서식과 보존 여부만 찍어 볼 수 있다.
- `2.Literature_Notes/` 아래 `Journals`·`Books`·`Seminars`·`Lectures`·`Datas` 하위 폴더. `literature` 의 `--subtype` 이 저장 위치를 고른다.
- `init --github-private <이름>` — 요청했을 때만 GitHub 비공개 저장소를 만들고 https 원격으로 push 한다.

### Changed

- 플러그인 이름이 `zettel` 이다. 설정 파일은 `zettel.json`, 명령은 `/zettel:*` 다. `llmwiki.json` 은 읽지 않는다.
- 템플릿이 `templates/personal/` 하나다. 프로필은 `personal` 이고 PARA 폴더(`4.Project`~`7.Archives`)는 만들지 않는다.
- `status` 가 임의 시점 보고로 바뀌었다. 보고서는 `_reports/status_YYMMDD.{md,json}` 이고 노트 수는 원자료/임시/문헌/영구 넷을 센다.
- 영구노트 본문 정본이 스타일 A(`### 날짜` · `### 태그` · `>[!메모]` · `### 원문 (출처)` · `### 생각 (질문)` · `### 연결 (이유)` · `### 추천 (주제)`)다. `promote`·`literature` 가 이 서식으로 만든다.
- index 폴더 이름이 `slipbox` 에서 `SlipBox` 로 바뀌었다.
- 승격 로그의 기본 `profile` 이 `personal` 이다.

### Removed

- `daily` 스킬과 `0.Daily_Notes/` 폴더.
- 학번(`--student-id`)·교수 계정(`--professor-github`)·교수 collaborator 자동 초대.
- 마일스톤(`--milestone w05|w10|w15`)과 `milestone_YYMMDD_wNN` 보고서.
- `templates/student/`·`templates/professor/` 와 `profile: professor` 의 PARA 라우팅. HOLD 는 어느 경우에도 파일을 옮기지 않고 표시만 남긴다.

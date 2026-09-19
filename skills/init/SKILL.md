---
name: init
description: 개인 제텔카스텐 vault 폴더를 만든다. 템플릿 복사·설정 기입·git 초기화·(선택) GitHub 비공개 저장소 생성·Obsidian 보관소 등록을 스크립트 한 번으로 실행하고 결과를 표로 보고한다. 새 vault 설치, "zettel 만들어줘", "제텔카스텐 초기화해줘", "GitHub 연결이 안 됐다"는 재시도에 쓴다. 사용법 - /zettel:init [--root 경로] [--github-private 저장소이름]
---

# zettel vault 초기화

인자: `$ARGUMENTS`

이 스킬은 판단하지 않는다. 인자를 모아 `init.py`에 넘기고, 결과를 사람이 읽을 표로 옮기고, 실패한 단계의 재시도 방법을 알려 주는 것이 전부다. 폴더·git·GitHub·Obsidian 처리는 전부 스크립트가 한다.

`init`은 vault를 **만드는** 스킬이므로 `wikiconf.py`를 먼저 부르지 않는다. 설정 파일은 이 스킬이 실행된 결과로 생긴다.

## 1. 인자 확보

필수 인자는 없다. `$ARGUMENTS`에 있는 것만 넘긴다.

| 인자 | 기본값 | 언제 묻나 |
|---|---|---|
| `--root` | 현재 폴더 | 현재 폴더가 vault 자리가 맞는지 애매하면 한 번만 묻는다 |
| `--github-private <이름>` | 없음 (원격 안 만듦) | 사용자가 GitHub 백업을 요청했을 때만 붙인다 |

`--github-private`의 값은 저장소 이름이므로 공백과 한글이 없어야 한다. 어긋나면 한 번 다시 묻는다.

폴더가 이미 있어도 그대로 진행한다. `init.py`는 멱등이라 기존 파일을 덮어쓰지 않는다.

## 2. 실행

```
python "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init.py" --root "<경로>" --json
```

GitHub 저장소를 만들 때만 뒤에 붙인다.

```
--github-private "<저장소 이름>"
```

`--no-obsidian`은 Obsidian 보관소 등록을 원치 않는다고 명시했을 때만 붙인다.

GitHub 단계가 실패해도 스크립트는 종료 코드를 올리지 않는다. 로컬 폴더와 git까지는 완성된 것이다.

## 3. 만들어지는 구조

```
<root>/
├── zettel.json                     설정 (경로·게이트 임계값)
├── CLAUDE.md                       운영 규칙
├── README.md                       폴더와 흐름
├── _raw/README.md                  원자료
├── 1.Fleeting_Notes/_template.md   임시노트
├── 2.Literature_Notes/_template.md 문헌노트
│   └── Journals/ Books/ Seminars/ Lectures/ Datas/
├── 3.Permanent_Notes/_template.md  영구노트
│   └── SlipBox/index.md            루만 번호 트리
├── _meta/gate-rules.md · rubric.md
└── _reports/
```

## 4. 결과 보고

출력 JSON을 표로 옮긴다.

| 단계 | 결과 |
|---|---|
| 폴더 | `<root>` — 생성 `len(created)`개, 유지 `len(skipped)`개 |
| git | `git.initialized` / 첫 커밋 `git.first_commit` |
| GitHub | `github.status`, 저장소 `github.repo`, push `github.pushed` |
| Obsidian | `obsidian.registered` (`obsidian.detail`) |

`next_steps`의 각 줄을 그대로 덧붙인다.

## 5. GitHub 실패 시 재시도 안내

`--github-private`를 준 경우에만 본다. `github.status`가 `ok`가 **아니면** 원인별로 안내한다. 상태 문자열은 스크립트가 낸 값을 그대로 쓴다.

| `github.status` | 안내 |
|---|---|
| `skipped: gh not found` | GitHub CLI가 없습니다. 설치한 뒤 `/zettel:init --github-private <이름>`을 다시 실행하세요. |
| `skipped: not logged in` | 터미널에서 `gh auth login`으로 로그인한 뒤 다시 실행하세요. |
| `skipped: cannot read user` | `gh auth status`로 로그인 상태를 확인한 뒤 다시 실행하세요. |
| `failed: repo create` | `github.detail`을 그대로 보여 주고, 같은 이름의 저장소가 이미 있는지 확인한 뒤 다시 실행하도록 안내한다. |
| `partial` | 저장소는 만들어졌지만 push가 되지 않았습니다. 폴더에서 `git push -u origin main`을 실행하세요. |

원격은 항상 `https://` 주소로 고정된다. 22번 포트(SSH)가 막힌 망에서도 push가 되게 하려는 장치다.

재실행은 안전하다. 이미 있는 파일은 유지되고 이미 만들어진 저장소는 다시 만들지 않는다.

## 6. 마무리

세 줄로 끝낸다.

1. `Obsidian을 열어 보관소를 확인하세요.`
2. `터미널에서 이 폴더로 이동한 뒤 /zettel:capture 로 첫 메모를 남겨 보세요.`
3. 만들어진 폴더의 `CLAUDE.md`에 운영 규칙과 세 노트 유형의 정본이 있으니 읽어 보라고 알린다.

## 출력 계약 (hard constraints)

- [ ] 폴더·git·GitHub·Obsidian 처리는 전부 `init.py`가 했고 직접 파일을 만들지 않았다
- [ ] 보고한 상태 값은 스크립트 출력 그대로다 (추측하지 않았다)
- [ ] GitHub 저장소는 사용자가 요청했을 때만 만들었다
- [ ] GitHub 실패는 감추지 않고 원인과 재시도 방법을 알렸다
- [ ] 기존 파일을 덮어쓰지 않았다

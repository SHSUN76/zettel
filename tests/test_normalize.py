# -*- coding: utf-8 -*-
import pytest
from normalize import (assert_text_preserved, detect_style, normalize_permanent_body, text_lines)

STYLE_A = """
### 날짜 : 2025-12-14

### 태그 : #캘린더링 #Spring-back

>[!메모]
> 1D-CNN 시계열 모델이 캘린더링 공정의 변화를 학습한다.

### 원문 (출처)
- 출처: Advanced Energy Materials 2024

### 생각 (질문)
- Spring-back 예측으로 두께를 얼마나 정밀하게 제어하는가?

### 연결 (이유)
- [[CNN은 합성곱 연산으로 특징을 추출한다]] (6A12) - 시계열에도 같은 원리

### 추천 (주제)
- DEM 시뮬레이션
"""

STYLE_B = """# 5분 시작 규칙

## 핵심 아이디어
심리적 저항이 클 때는 5분짜리 작은 행동을 시작점으로 삼아야 한다.

## 상세 설명
압도당한 상태에서는 결정을 미루기 쉽다. 마이크로 액션을 설정해야 한다.

## 예시/사례
- 빈 문서를 열고 단어 하나 적어보기

## 연결된 아이디어
- [[마찰력을 줄이는 시스템 설계]]

## 관련 노트
- [[작은 성공이 동기부여에 미치는 영향]]

## 출처/참고
- 대화 전문: [[2026-06-26_session]]

## 추가 질문
- 나에게 가장 효과적인 5분 스타터는 무엇인가?

---
*생성일: 2026-06-26*

#영구노트 #생산성
"""

STYLE_C = """## 메모

AI 도구의 사용 노하우는 빠르게 소멸한다. 살아남는 지식은 도메인 전문성이다.

## 나의 생각과 질문

1. 도구 노하우도 패턴으로 추상화하면 영속성이 생기지 않는가?

## 출처/참고

- 원본: [[ClaudeCode_Context 관리]]

## 개인적 질문

1. 최적 학습 시간 비율은 얼마인가?
"""

META = {"date": "2026-09-19", "tags": ["지식관리", "seed"]}


def test_detect_style_three_kinds():
    assert detect_style(STYLE_A) == "A"
    assert detect_style(STYLE_B) == "B"
    assert detect_style(STYLE_C) == "C"
    assert detect_style("헤더 없는 본문 한 줄") == "other"


@pytest.mark.parametrize("body", [STYLE_A, STYLE_B, STYLE_C])
def test_normalize_yields_style_a_and_preserves_text(body):
    out = normalize_permanent_body(body, META)
    assert_text_preserved(body, out)                 # 텍스트 줄을 하나도 잃지 않는다
    assert detect_style(out) == "A"
    for head in (">[!메모]", "### 원문 (출처)", "### 생각 (질문)", "### 연결 (이유)", "### 추천 (주제)"):
        assert head in out
    assert out.startswith("### 날짜 : 2026-09-19")
    assert "### 태그 : #지식관리 #seed" in out


def test_normalize_maps_headers_per_conversion_table():
    out = normalize_permanent_body(STYLE_B, META)
    memo, rest = out.split("### 원문 (출처)", 1)
    assert "> 심리적 저항이 클 때는" in memo                     # 핵심 아이디어 → 메모 콜아웃
    source, rest = rest.split("### 생각 (질문)", 1)
    assert "**상세 설명**" in source and "**예시/사례**" in source  # 원문 절 뒤 소제목
    assert "대화 전문: [[2026-06-26_session]]" in source          # 출처/참고 → 원문 (출처)
    thought, rest = rest.split("### 연결 (이유)", 1)
    assert "5분 스타터" in thought                               # 추가 질문 → 생각 (질문)
    link, recommend = rest.split("### 추천 (주제)", 1)
    assert "[[마찰력을 줄이는 시스템 설계]]" in link              # 연결된 아이디어 · 관련 노트 → 연결
    assert "[[작은 성공이 동기부여에 미치는 영향]]" in link
    assert "*생성일: 2026-06-26*" in recommend                   # 꼬리말은 맨 끝에 보존


def test_normalize_keeps_unmapped_section_under_thought():
    body = "## 반론\n- 이 주장은 소규모 팀에서만 성립한다\n"
    out = normalize_permanent_body(body, META)
    thought = out.split("### 생각 (질문)", 1)[1].split("### 연결 (이유)", 1)[0]
    assert "**반론**" in thought and "소규모 팀에서만 성립한다" in thought
    assert_text_preserved(body, out)


def test_text_lines_drops_headers_blanks_callout_marks_and_bold_subheads():
    md = "### 날짜 : 2026-09-19\n\n>[!메모]\n> 본문 한 줄\n\n**상세 설명**\n내용 줄\n"
    assert text_lines(md) == {"본문 한 줄", "내용 줄"}


def test_assert_text_preserved_raises_when_a_line_is_lost():
    with pytest.raises(AssertionError):
        assert_text_preserved("남아야 할 줄\n버려질 줄\n", "남아야 할 줄\n")

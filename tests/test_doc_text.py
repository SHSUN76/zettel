# -*- coding: utf-8 -*-
import json, subprocess, sys, zipfile
from pathlib import Path
import doc_text

SLIDE = ('<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
         ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
         "<p:cSld><p:spTree><p:sp><p:txBody>"
         "<a:p><a:r><a:t>{head}</a:t></a:r></a:p>"
         "<a:p><a:r><a:t>{tail}</a:t></a:r></a:p>"
         "</p:txBody></p:sp></p:spTree></p:cSld></p:sld>")

def _make_pptx(path: Path) -> Path:
    """실제 pptx 파일을 두지 않고 최소 구조만 zip 으로 만든다. slide10 을 먼저 넣어 정렬을 검사한다."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("ppt/slides/slide10.xml", SLIDE.format(head="열역학 제1법칙", tail="열번째 슬라이드"))
        z.writestr("ppt/slides/slide2.xml", SLIDE.format(head="엔트로피와 엔탈피", tail="두번째 슬라이드"))
        z.writestr("ppt/slides/slide1.xml", SLIDE.format(head="zettel 교재", tail="첫번째 슬라이드"))
        z.writestr("ppt/notesSlides/notesSlide1.xml", SLIDE.format(head="발표자 노트", tail="제외되어야 한다"))
    return path

def test_doc_text_reads_pptx_slides_in_numeric_order(tmp_path):
    pptx = _make_pptx(tmp_path / "교재.pptx")
    out = doc_text.extract(pptx)
    assert out["kind"] == "pptx"
    assert [s["n"] for s in out["slides"]] == [1, 2, 10]  # slide10 이 slide2 앞에 오면 안 된다
    assert out["slides"][0]["text"] == "zettel 교재\n첫번째 슬라이드"
    assert out["slides"][1]["text"].startswith("엔트로피와 엔탈피")
    assert "발표자 노트" not in json.dumps(out, ensure_ascii=False)  # 슬라이드 본문만 읽는다
    r = subprocess.run([sys.executable, "skills/_shared/scripts/doc_text.py", str(pptx)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and json.loads(r.stdout)["slides"][0]["text"].startswith("zettel 교재")

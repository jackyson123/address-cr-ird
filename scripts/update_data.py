#!/usr/bin/env python3
"""
下載官方 PDF → 轉文字 → 產生 data/ 供前端搜尋
依賴: curl 或 urllib, pdftotext (poppler-utils)
在 GitHub Actions (Ubuntu) 可直接跑
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / "cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

SOURCES = {
    "money_lender": {
        "url": "https://www.cr.gov.hk/en/statistics/docs/ml_licensees1.pdf",
        "pdf": CACHE / "ml_licensees1.pdf",
        "txt": CACHE / "ml_licensees1.txt",
        "out": DATA / "ml_full.txt",
    },
    "charity": {
        "url": "https://www.ird.gov.hk/chi/pdf/s88list_emb.pdf",
        "pdf": CACHE / "s88list_emb.pdf",
        "txt": CACHE / "s88list_emb.txt",
        "out": DATA / "charity_full.txt",
    },
}


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url} ...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HKNameSearch/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        dest.write_bytes(resp.read())
    print(f"  -> {dest} ({dest.stat().st_size} bytes)")


def pdf_to_text(pdf: Path, txt: Path) -> None:
    print(f"pdftotext {pdf.name} ...")
    subprocess.run(
        ["pdftotext", "-layout", str(pdf), str(txt)],
        check=True,
    )
    print(f"  -> {txt} ({txt.stat().st_size} bytes)")


def normalize_text(raw: str) -> str:
    # 保留換行，壓縮多餘空白，方便搜尋
    lines = []
    for line in raw.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def extract_ml_names(text: str) -> list[str]:
    names: set[str] = set()
    for line in text.splitlines():
        if "English Name" in line or "中文名稱" in line or "頁碼" in line:
            continue
        line_n = re.sub(r"\s+", " ", line).strip()
        m = re.search(
            r"\d+/\d{4}\s+(.+?)(?:\s{2,}|\s+)([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9·‧（）\(\)\-\s]{0,50})?\s+\d{1,2}-[A-Za-z]{3}-\d{2}",
            line_n,
        )
        if m:
            eng = re.sub(r"\s+R$", "", m.group(1).strip()).strip()
            chi = (m.group(2) or "").strip()
            if len(eng) > 2:
                names.add(eng)
            if len(chi) > 1:
                names.add(chi)
        else:
            m2 = re.search(
                r"\d+/\d{4}\s+([A-Za-z0-9].+?)\s+\d{1,2}-[A-Za-z]{3}-\d{2}",
                line_n,
            )
            if m2:
                eng = re.sub(r"\s+R$", "", m2.group(1).strip()).strip()
                if len(eng) > 2:
                    names.add(eng)
    return sorted(n for n in names if not re.match(r"^\d{1,2}-[A-Za-z]{3}-\d{2}", n))


def extract_charity_names(text: str) -> list[str]:
    names: set[str] = set()
    lines = [ln.strip() for ln in text.splitlines()]
    for i, s in enumerate(lines):
        if not s or len(s) < 2:
            continue
        if "w.e.f" in s.lower() or s.startswith("-"):
            continue
        nxt = " ".join(lines[i + 1 : i + 3]).lower()
        if "w.e.f" in nxt:
            if "截至" not in s and "LIST OF" not in s and not re.match(r"^[\d\.\-\s]+$", s):
                names.add(s)
        if re.search(
            r"\b(LIMITED|FOUNDATION|SOCIETY|TRUST|ASSOCIATION|CHURCH|TEMPLE|FUND)\b",
            s,
            re.I,
        ):
            if 3 <= len(s) <= 150 and "w.e.f" not in s.lower():
                names.add(s)
        if re.search(r"有限公司|基金會|協會|慈善", s) and 2 <= len(s) <= 80:
            names.add(s)
    return sorted(names)


def main() -> int:
    for key, src in SOURCES.items():
        try:
            download(src["url"], src["pdf"])
            pdf_to_text(src["pdf"], src["txt"])
        except Exception as e:
            print(f"ERROR updating {key}: {e}", file=sys.stderr)
            # 若有舊檔就繼續用
            if not src["txt"].exists():
                return 1

        raw = src["txt"].read_text(encoding="utf-8", errors="replace")
        norm = normalize_text(raw)
        src["out"].write_text(norm, encoding="utf-8")
        print(f"Wrote {src['out']}")

    ml_text = SOURCES["money_lender"]["out"].read_text(encoding="utf-8")
    ch_text = SOURCES["charity"]["out"].read_text(encoding="utf-8")

    meta = {
        "updated": date.today().isoformat(),
        "sources": {
            "money_lender": SOURCES["money_lender"]["url"],
            "charity": SOURCES["charity"]["url"],
        },
        "money_lender_count": len(extract_ml_names(ml_text)),
        "charity_count": len(extract_charity_names(ch_text)),
        "money_lender": extract_ml_names(ml_text),
        "charity": extract_charity_names(ch_text),
    }
    names_path = DATA / "names.json"
    names_path.write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {names_path} (updated={meta['updated']})")
    print(f"  money_lender names: {meta['money_lender_count']}")
    print(f"  charity names: {meta['charity_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

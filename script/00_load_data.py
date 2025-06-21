from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# 1. 구성 ── 분석 레이어별 폴더 패턴.
# ---------------------------------------------------------------------------
DATA_LAYER_CONFIG: Dict[str, Dict[str, str]] = {
    "complex_meta": {
        "desc": "단지 메타 (1·2·3기)",
        "pattern": "아파트_매매/**/*06_24/*.csv|아파트_매매/한국부동산원_공동주택 단지 식별정보_기본정보_*.csv",
        "outfile": "layer_A_complex_meta",
    },
    "sales_transactions": {
        "desc": "실거래 기록 (1·2기)",
        "pattern": "transactions/*거래*.csv|아파트_매매/**/*실거래가*.csv",
        "outfile": "layer_B_transactions",
    },
    "market_macro_index": {
        "desc": "시장 지수·거시 변수",
        "pattern": "transactions/*가격지수*.csv|else/*.csv",
        "outfile": "layer_C_macro_index",
    },
    "supply_info": {
        "desc": "공급 (미분양·입주 예정)",
        "pattern": "supply/*.csv",
        "outfile": "layer_D_supply",
    },
    "subscription_competition": {
        "desc": "청약 경쟁률",
        "pattern": "competition/*.csv",
        "outfile": "layer_E_competition",
    },
}


# ---------------------------------------------------------------------------
# 2. 헬퍼
# ---------------------------------------------------------------------------

def _detect_encoding(path: Path, default: str = "utf-8") -> str:
    """매우 경량의 인코딩 추측기(기본값으로 폴백)."""
    try:
        import chardet  # type: ignore

        with path.open("rb") as f:
            raw = f.read(4_096)
            guess = chardet.detect(raw)
            return guess["encoding"] or default
    except ModuleNotFoundError:
        return default


def _read_csv(path: Path) -> pd.DataFrame:
    """utf-8을 우선 시도하고 cp949 등 기타 인코딩을 추측하는 강건한 CSV 판독기."""
    encodings_to_try: List[str] = ["utf-8", "cp949", _detect_encoding(path)]
    for enc in encodings_to_try:
        try:
            return pd.read_csv(path, low_memory=False, encoding=enc, on_bad_lines="skip")
        except UnicodeDecodeError:
            continue
    # last resort: let pandas guess
    return pd.read_csv(path, low_memory=False, encoding="utf-8", errors="ignore", on_bad_lines="skip")


def _collect_files(base: Path, pattern: str) -> List[Path]:
    """'|' 연산자를 지원하는 Glob 패턴 확장기."""
    files: List[Path] = []
    for sub in pattern.split("|"):
        files.extend(base.glob(sub))
    return sorted([p for p in files if p.is_file()])


def _load_layer(layer: str, base_dir: Path) -> pd.DataFrame:
    cfg = LAYER_CONFIG[layer]
    files = _collect_files(base_dir, cfg["pattern"])
    if layer == "A":
        # 실거래 파일(파일명에 '실거래') 제외
        orig_count = len(files)
        files = [f for f in files if '실거래' not in f.name]
        excluded = orig_count - len(files)
        if excluded > 0:
            logging.info("Layer A: excluded %d transaction files, loading %d meta files", excluded, len(files))
        if not files:
            logging.warning("Layer A: no meta CSV files found after excluding transaction files")
            return pd.DataFrame()
    logging.info("Layer %s ─ %d files", layer, len(files))
    frames: List[pd.DataFrame] = []
    for f in files:
        if layer == "B":
            # 실거래 원본 CSV: 상단 안내 셀(skip) 후 컬럼 헤더(“NO” 시작)를 기준으로 로드
            # 동적 헤더 감지를 위해 파일을 스캔
            header_row = 0
            try:
                with f.open('r', encoding='cp949', errors='ignore') as fin:
                    for i, line in enumerate(fin):
                        if line.lstrip().startswith('NO') or line.lstrip().startswith('"NO"'):
                            header_row = i
                            break
            except Exception:
                header_row = 0
            
            # 강건한 CSV 읽기: 여러 인코딩 시도
            df = None
            for enc in ['cp949', 'utf-8', 'euc-kr']:
                try:
                    df = pd.read_csv(
                        f,
                        skiprows=header_row,
                        header=0,
                        encoding=enc,
                        engine="python",
                        on_bad_lines="skip"
                    )
                    break
                except UnicodeDecodeError:
                    continue
            
            # 마지막 수단: errors='ignore' 옵션 사용
            if df is None:
                df = pd.read_csv(
                    f,
                    skiprows=header_row,
                    header=0,
                    encoding="utf-8",
                    errors="ignore",
                    engine="python",
                    on_bad_lines="skip"
                )
            # 로드된 컬럼 로깅 및 단지명 컬럼 리네이밍
            logging.info("Loaded B columns from %s (header at row %d) → %s", f, header_row, df.columns.tolist())
            for src in ["단지명","complex","단지"]:
                if src in df.columns:
                    df.rename(columns={src: "complex_name"}, inplace=True)
                    logging.info("Renamed B column %s to complex_name", src)
                    break
        elif layer == "A":
            # 단지 메타 CSV: 상단 안내문(skip) 후 컬럼 헤더('단지코드' 및 '단지명' 포함)를 기준으로 로드
            header_row = 0
            try:
                with f.open('r', encoding='cp949', errors='ignore') as fin:
                    for i, line in enumerate(fin):
                        if '단지코드' in line and '단지명' in line:
                            header_row = i
                            break
            except Exception:
                header_row = 0
            df = pd.read_csv(
                f,
                skiprows=header_row,
                header=0,
                encoding="cp949",
                engine="python",
                on_bad_lines="skip"
            )
            logging.info("Loaded A columns from %s (header at row %d) → %s", f, header_row, df.columns.tolist())
            # 단지명 → complex_name, 단지코드 → complex_id 컬럼 통일
            for src in ["단지명","complex","단지"]:
                if src in df.columns and "complex_name" not in df.columns:
                    df.rename(columns={src: "complex_name"}, inplace=True)
                    logging.info("Renamed A column %s to complex_name", src)
                    break
            if "단지코드" in df.columns and "complex_id" not in df.columns:
                df.rename(columns={"단지코드": "complex_id"}, inplace=True)
                logging.info("Renamed A column 단지코드 to complex_id")
            # 공공데이터 메타: 단지고유번호 → complex_id, 단지명_도로명주소 → complex_name
            if "단지고유번호" in df.columns and "complex_id" not in df.columns:
                df.rename(columns={"단지고유번호": "complex_id"}, inplace=True)
                logging.info("Renamed A column 단지고유번호 to complex_id")
            if "단지명_도로명주소" in df.columns and "complex_name" not in df.columns:
                df.rename(columns={"단지명_도로명주소": "complex_name"}, inplace=True)
                logging.info("Renamed A column 단지명_도로명주소 to complex_name")
        else:
            df = _read_csv(f)
        df["__source"] = str(f.relative_to(base_dir))
        frames.append(df)
    return pd.concat(frames, ignore_index=True, copy=False)

# ---------------------------------------------------------------------------
# 3. CLI 진입점.
# ---------------------------------------------------------------------------

def parse_args(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description="Bulk‑load raw csvs into pickles/parquets.")
    p.add_argument("--data_dir", default="./data", help="Root directory where the raw data folders live.")
    p.add_argument("--output_dir", default="output", help="Output directory for serialised layers.")
    p.add_argument("--layers", nargs="*", default=list(LAYER_CONFIG.keys()), choices=LAYER_CONFIG.keys(), help="Subset of layers to load (default: all).")
    p.add_argument("--format", choices=["pickle", "parquet"], default="pickle", help="Serialisation format for layer outputs.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None):
    args = parse_args(argv)
    base_dir = Path(args.data_dir).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Dict[str, object]] = {}
    for layer in args.layers:
        df = _load_layer(layer, base_dir)
        rows, cols = df.shape
        logging.info("Layer %s → %s rows × %s cols", layer, rows, cols)
        # serialise
        outfile = out_dir / f"{LAYER_CONFIG[layer]['outfile']}.{args.format}"
        if args.format == "pickle":
            df.to_pickle(outfile)
        else:
            df.to_parquet(outfile, engine="pyarrow", index=False)
        summary[layer] = {
            "description": LAYER_CONFIG[layer]["desc"],
            "outfile": str(outfile.relative_to(out_dir)),
            "rows": rows,
            "columns": df.columns.tolist(),
        }

    summary_path = out_dir / "summary_layers.json"
    with summary_path.open("w", encoding="utf-8") as fw:
        json.dump(summary, fw, indent=2, ensure_ascii=False)
    logging.info("Written summary → %s", summary_path)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

import argparse
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor
from unidecode import unidecode  # 영문 전용 레이블을 위해 컬럼명을 ASCII로 음역.

# ---------------------------------------------------------------------------
# 1. CLI 설정.
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="EDA and QC for panel data")
parser.add_argument("--input",  default="output/panel_panel.parquet",
                    help="03단계 출력 패널 데이터 경로")
parser.add_argument("--output_dir", default="output",
                    help="QC 결과 저장 디렉토리")
args = parser.parse_args()

IN_PATH  = Path(args.input)
OUT_DIR  = Path(args.output_dir)
OUT_DIR.mkdir(exist_ok=True, parents=True)

# ---------------------------------------------------------------------------
# 2. 데이터 로드 및 컬럼명 ASCII 음역.
# ---------------------------------------------------------------------------
df = pd.read_parquet(IN_PATH)
# 컬럼명 한글 → ASCII 음역.
df.columns = [unidecode(c) for c in df.columns]
all_num = df.select_dtypes(include=[np.number]).columns.tolist()
exclude_prefixes = ('reg_','tm_')  # 지역/시간 더미 변수 접두사.
num_cols = [c for c in all_num if c != 'time_id' and not any(c.startswith(p) for p in exclude_prefixes)]

# ---------------------------------------------------------------------------
# 3. 결측률 분석.
# ---------------------------------------------------------------------------
missing_rate = df[num_cols].isna().mean().sort_values(ascending=False)
missing_rate.to_csv(OUT_DIR / "qc_missing_rate.csv", header=["missing_rate"])

# 시각화: 상위 50개 변수 결측 히트맵
plt.figure(figsize=(10,6))
plt.barh(missing_rate.head(50).index[::-1],
         missing_rate.head(50).values[::-1])
plt.xlabel("Missing Rate")
plt.title("Top 50 Features by Missing Rate")
plt.tight_layout()
plt.savefig(OUT_DIR / "fig_missing_rate.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 4. 정규성 검사(Shapiro–Wilk) 및 Box-Cox 변환 최적 λ.
# ---------------------------------------------------------------------------
qc_norm = []
for col in ["price_per_m2", "ln_price", "built_age",
            "unsold_units_12m", "comp_rate_ma3"]:
    if col in df:
        series = df[col].dropna()
        # Shapiro–Wilk 검정(표본이 5000개 이상일 경우 샘플링).
        samp = series if len(series)<=5000 else series.sample(5000, random_state=0)
        stat, pval = stats.shapiro(samp)
        # Box-Cox 변환(양수 값만).
        if (series>0).all():
            bc_data, bc_lambda = stats.boxcox(series)
        else:
            bc_lambda = np.nan
        qc_norm.append({
            "feature": col,
            "n": len(series),
            "shapiro_p": pval,
            "boxcox_lambda": bc_lambda
        })
qc_norm_df = pd.DataFrame(qc_norm)
qc_norm_df.to_csv(OUT_DIR / "qc_shapiro_boxcox.csv", index=False)

# ---------------------------------------------------------------------------
# 5. 다중공선성(VIF).
# ---------------------------------------------------------------------------
# VIF 계산을 위해 상수항 포함.
vif_df = pd.DataFrame(columns=["feature","vif"])
X = df[num_cols].dropna().iloc[:5000]  # 속도 위해 표본 5k
X = X.assign(const=1.0)
for i, col in enumerate(X.columns):
    if col == "const":
        continue
    vif = variance_inflation_factor(X.values, i)
    # pandas 2.x: DataFrame.append가 deprecated되어 loc로 행 추가.
    vif_df.loc[len(vif_df)] = [col, vif]
vif_df.sort_values("vif", ascending=False).to_csv(OUT_DIR / "qc_vif.csv", index=False)

# ---------------------------------------------------------------------------
# 6. 상관관계 히트맵.
# ---------------------------------------------------------------------------
corr = df[num_cols].corr().abs()
# 상위 20개 피처 선택.
top_feats = missing_rate.head(20).index.tolist()
sub_corr = corr.loc[top_feats, top_feats]

plt.figure(figsize=(8,6))
plt.imshow(sub_corr, vmin=0, vmax=1, cmap="viridis")
plt.colorbar(label="|Correlation|")
plt.xticks(range(len(top_feats)), top_feats, rotation=90)
plt.yticks(range(len(top_feats)), top_feats)
plt.title("Correlation Heatmap (Top 20 by Missing Rate)")
plt.tight_layout()
plt.savefig(OUT_DIR / "fig_corr_heatmap.png", dpi=150)
plt.close()

print("✅ EDA/QC complete. Results saved to", OUT_DIR)

#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# 한글 폰트 설정 (macOS 기준 AppleGothic) 및 유니코드 마이너스 사용 활성화
matplotlib.rc('font', family='AppleGothic')
matplotlib.rcParams['axes.unicode_minus'] = False

# 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
PLOTS_DIR = os.path.join(OUTPUT_DIR, 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

# 입력: 최종 병합된 시계열 데이터
df = pd.read_pickle(os.path.join(OUTPUT_DIR, 'final_df_region.pkl'))

# 지역별 시계열 플롯 생성
for region in ['전국', '수도권', '지방권']:
    df_reg = df[df['region_name'] == region]
    plt.figure(figsize=(10, 5))
    plt.plot(df_reg.index, df_reg['price_index'], label='매매 지수')
    plt.plot(df_reg.index, df_reg['jeonse_index'], label='전세 지수')
    plt.title(f'{region} 매매‧전세 지수 시계열')
    plt.xlabel('연월')
    plt.ylabel('지수')
    plt.legend()
    plt.grid(True)
    # 파일명에 한글이 포함될 수 있어 안전하게 변환
    fname = f"{region}_timeseries.png".replace(':', '_')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, fname))
    plt.close()
    print(f"Saved plot for {region}: {fname}")

print('All visualizations saved to', PLOTS_DIR) 
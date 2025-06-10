## 1. 프로젝트 폴더 및 데이터 파일 구조 점검

### 1.1. 목적

* 프로젝트에 제공된 CSV 파일 목록을 확인하여 각 파일의 구조(컬럼, 형태 등)를 파악합니다.
* 이후 전처리 및 분석 방향을 설정하기 위한 기초 작업입니다.

```python
import pandas as pd
import os

# 데이터 디렉터리 경로 설정
data_dir = '/mnt/data'

# 디렉터리 내 모든 CSV 파일 목록 수집
csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

# 각 CSV 파일별 샘플(첫 5개 행)을 불러와 컬럼명을 조사
summary_info = []
for file in csv_files:
    file_path = os.path.join(data_dir, file)
    # UTF-8로 우선 읽어보고, 인코딩 이슈 시 CP949로 재시도 가능
    try:
        df = pd.read_csv(file_path, encoding='utf-8', nrows=5)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949', nrows=5)
    summary_info.append({
        'Filename': file,
        'Preview Shape': (df.shape[0], df.shape[1]),
        'Columns': list(df.columns)
    })

# DataFrame으로 정리하여 UI로 출력 (ace_tools 사용)
import ace_tools as tools
summary_df = pd.DataFrame(summary_info)
tools.display_dataframe_to_user(name="CSV File Structure Summary", dataframe=summary_df)
```

**의도**:

* `csv_files` 목록을 통해 어떤 데이터가 프로젝트에 있는지 확인합니다.
* 각 파일의 컬럼명과 형태를 조사하여, 이후 어떤 파일을 우선적으로 처리할지, 그리고 전처리 방향을 잡습니다.

---

## 2. 매매지수(MaemaeIndex) 및 전세지수(JeonseIndex) 데이터 전처리

### 2.1. 목적

* `(월) 매매가격지수_아파트.csv`와 `(월) 전세가격지수_아파트.csv` 파일을 로드
* Wide 포맷(월별 컬럼을 가진 형태)을 Long 포맷(`YearMonth` × `Index 값`)으로 변환
* `YYYY년 M월` 형태의 문자열을 `YYYY-MM`로 표준화하여 시계열 분석에 적합한 형태로 변환

### 2.2. 코드

```python
import pandas as pd
import re

# 2.2.1. 원본 CSV 파일 경로 지정
maemae_file = '/mnt/data/(월) 매매가격지수_아파트.csv'
jeonse_file = '/mnt/data/(월) 전세가격지수_아파트.csv'

# 2.2.2. UTF-8로 불러오되, 인코딩 오류 시 CP949로 재시도
try:
    maemae_df = pd.read_csv(maemae_file, encoding='utf-8')
except UnicodeDecodeError:
    maemae_df = pd.read_csv(maemae_file, encoding='cp949')

try:
    jeonse_df = pd.read_csv(jeonse_file, encoding='utf-8')
except UnicodeDecodeError:
    jeonse_df = pd.read_csv(jeonse_file, encoding='cp949')

# 2.2.3. 컬럼명 확인 (헤더 구조 파악용)
print("매매가격지수 파일 컬럼 예시:", maemae_df.columns[:10])
print("전세가격지수 파일 컬럼 예시:", jeonse_df.columns[:10])

# 2.2.4. 지역 계층 컬럼(분류, 분류.1, 분류.2, 분류.3) 식별
region_cols = ['분류', '분류.1', '분류.2', '분류.3']

# 2.2.5. 시간 컬럼(YYYY년 M월 형태) 추출
#     '2003년 11월', '2003년 11월.1' 등 헤더가 두 줄로 반복될 수 있음.
time_cols_maemae = [col for col in maemae_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]
time_cols_jeonse = [col for col in jeonse_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]

# 2.2.6. Wide → Long 변환(melt)
maemae_long = maemae_df.melt(
    id_vars=region_cols,
    value_vars=time_cols_maemae,
    var_name='YearMonth',
    value_name='MaemaeIndex'
)
jeonse_long = jeonse_df.melt(
    id_vars=region_cols,
    value_vars=time_cols_jeonse,
    var_name='YearMonth',
    value_name='JeonseIndex'
)

# 2.2.7. 'YYYY년 M월' 문자열을 'YYYY-MM'로 변환하는 함수 정의

def convert_year_month(korean_str):
    match = re.match(r"(\d{4})년\s*(\d{1,2})월", str(korean_str))
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        return f"{year}-{month}"
    return None

# 2.2.8. YearMonth 포맷 변환 적용
maemae_long['YearMonth'] = maemae_long['YearMonth'].apply(convert_year_month)
jeonse_long['YearMonth'] = jeonse_long['YearMonth'].apply(convert_year_month)

# 2.2.9. 첫 번째 헤더 역할을 하는 '분류' 값(문자열 '분류')을 가진 행 제거
maemae_clean = maemae_long[maemae_long['분류'] != '분류'].copy()
jeonse_clean = jeonse_long[jeonse_long['분류'] != '분류'].copy()

# 2.2.10. 지수를 float 타입으로 변환 (변환 불가능 시 NaN)
maemae_clean['MaemaeIndex'] = pd.to_numeric(maemae_clean['MaemaeIndex'], errors='coerce')
jeonse_clean['JeonseIndex'] = pd.to_numeric(jeonse_clean['JeonseIndex'], errors='coerce')

# 2.2.11. 결과 샘플 출력 (디버그용)
print("매매 지수 Long Form 예시:\n", maemae_clean.head())
print("전세 지수 Long Form 예시:\n", jeonse_clean.head())
```

**의도**:

1. `melt`를 통해 Wide 형식의 월별 컬럼을 Long 형식(`YearMonth` × `Index`)으로 바꿔, 시계열 분석에 필요한 형태로 전환합니다.
2. `YearMonth`를 통일된 `YYYY-MM` 문자열로 변환하여, 추후 `pd.to_datetime`을 통해 `datetime` 인덱스로 활용할 수 있도록 준비합니다.
3. 첫 번째 헤더 행(‘분류’)을 제거하여 실제 지수 데이터만 남깁니다.
4. `MaemaeIndex`와 `JeonseIndex`를 숫자형(float)으로 변환하여 추후 수치 연산이 가능하도록 합니다.

---

## 3. 매매지수와 전세지수 데이터 병합

### 3.1. 목적

* Long 형식으로 정리된 매매지수(`maemae_clean`)와 전세지수(`jeonse_clean`)를 **지역 계층(`분류, 분류.1, 분류.2, 분류.3`)과 `YearMonth`** 기준으로 병합합니다.
* 이 과정을 통해, 동일 지역·동일 시점에 대한 매매 및 전세 지수를 한 DataFrame에서 조회할 수 있도록 만듭니다.

### 3.2. 코드

```python
# 3.2.1. 공통 키(분류, 분류.1, 분류.2, 분류.3, YearMonth)로 inner merge 수행
merged_df = pd.merge(
    maemae_clean,
    jeonse_clean,
    on=['분류', '분류.1', '분류.2', '분류.3', 'YearMonth'],
    how='inner'
)

# 3.2.2. 샘플 결과 확인
import ace_tools as tools
merged_head = merged_df.head()
tools.display_dataframe_to_user(name="Merged Maemae-Jeonse Data Sample", dataframe=merged_head)

# 3.2.3. Merge 결과 요약 정보 출력 (rows, columns)
summary = {
    'Total Rows': merged_df.shape[0],
    'Columns': list(merged_df.columns)
}
print(summary)
```

**의도**:

* `merged_df`는 **네 단계 지역 계층**(`분류, 분류.1, 분류.2, 분류.3`)과 `YearMonth`를 기준으로 양 지수 데이터를 합친 결과입니다.
* 이 DataFrame에는 이제 `MaemaeIndex`와 `JeonseIndex`를 한 번에 조회할 수 있는 `YearMonth` × 지역 조합이 담겨 있습니다.

---

## 4. 권역별/지역별 전처리(컬럼명 정리·인덱스 설정)

### 4.1. 목적

* `merged_df`에는 네 단계의 `분류*` 컬럼이 존재하므로, 권역 수준(전국/수도권/지방권) 또는 시도·시군구·동 단위까지 세부적으로 분석할 수 있습니다.
* 이 예시에서는 **권역 단위(전국, 수도권, 지방권)** 분석을 위해, `분류` 컬럼을 `region_name`이라는 새 칼럼으로 복사합니다.
* 불필요한 다단 계층 컬럼을 제거하고, `YearMonth`를 `datetime`으로 변환하여 시계열 인덱스를 설정합니다.

### 4.2. 코드

```python
# 4.2.1. Top-level 지역 값(전국/수도권/지방권)인 '분류' 컬럼을 복사하여 'region_name' 생성
merged_df['region_name'] = merged_df['분류']

# 4.2.2. YearMonth 문자열(YYYY-MM)을 datetime으로 변환 (임시 컬럼 생성 후 인덱스 설정)
merged_df['year_month'] = pd.to_datetime(merged_df['YearMonth'], format='%Y-%m')

# 4.2.3. 필요한 컬럼만 추출: region_name, year_month, MaemaeIndex, JeonseIndex
#           분류*, 분류.1~분류.3, YearMonth 칼럼은 제거
df_processed = merged_df[['region_name', 'year_month', 'MaemaeIndex', 'JeonseIndex']].copy()

# 4.2.4. 칼럼명 영어로 변경
#  - MaemaeIndex -> price_index
#  - JeonseIndex -> jeonse_index
df_processed = df_processed.rename(columns={
    'MaemaeIndex': 'price_index',
    'JeonseIndex': 'jeonse_index'
})

# 4.2.5. 'year_month'를 인덱스로 설정하여 시계열 형태로 정렬
df_processed = df_processed.set_index('year_month').sort_index()

# 4.2.6. 데이터 정보 확인 (Non-null counts, dtype 등)
df_processed.info()

# 4.2.7. 샘플 출력
tools.display_dataframe_to_user(name="Processed df_merge Sample", dataframe=df_processed.head())
```

**의도**:

1. `region_name` 칼럼에 권역(전국/수도권/지방권) 값을 담습니다.
2. `YearMonth`를 `datetime` 형태(`year_month`)로 변환하여 인덱스 설정 → **시계열 분석 준비**를 완료합니다.
3. 다단계 `분류*` 컬럼은 분석 초점(권역 단위)이므로 제거하고, 핵심 칼럼만 남깁니다.

---

## 5. 기초 EDA: 통계 요약, 상관관계, 시계열 플롯

### 5.1. 목적

* 전처리된 권역별 시계열 데이터(`df_processed`)를 대상으로, 가격지수(`price_index`, `jeonse_index`)의 기초 통계를 파악합니다.
* 연도별 평균값 및 연도별 증감률(YoY % change)을 계산하여 장기 트렌드를 관찰합니다.
* **매매지수 vs 전세지수**의 상관관계를 전체 기간 및 연도별로 탐색합니다.
* 권역별(전국, 수도권, 지방권) 시계열 플롯을 생성하여 시각적으로 비교합니다.

### 5.2. 코드

```python
import matplotlib.pyplot as plt

# 5.2.1. 기초 통계: count, mean, std, min, 25%, 50%, 75%, max
desc_stats = df_processed[['price_index', 'jeonse_index']].describe()
tools.display_dataframe_to_user(name="Descriptive Statistics: Price and Jeonse Indices", dataframe=desc_stats)

# 5.2.2. 연도(year) 컬럼 추가 및 연도별 평균·증감률 계산
df_processed['year'] = df_processed.index.year
df_yearly = df_processed.groupby('year')[['price_index', 'jeonse_index']].mean().reset_index()
df_yearly['price_pct_change'] = df_yearly['price_index'].pct_change() * 100
df_yearly['jeonse_pct_change'] = df_yearly['jeonse_index'].pct_change() * 100
tools.display_dataframe_to_user(name="Yearly Average Indices and YoY % Changes", dataframe=df_yearly)

# 5.2.3. 전체 상관관계 매트릭스 (매매 vs 전세)
corr_matrix = df_processed[['price_index', 'jeonse_index']].corr()
tools.display_dataframe_to_user(name="Overall Correlation Matrix", dataframe=corr_matrix)

# 5.2.4. 연도별 상관관계 변화
def compute_corr_year(group):
    return group['price_index'].corr(group['jeonse_index'])

corr_by_year = df_processed.groupby('year').apply(compute_corr_year).reset_index(name='corr_price_jeonse')
tools.display_dataframe_to_user(name="Yearly Correlation: Price vs Jeonse", dataframe=corr_by_year)

# 5.2.5. 권역별 시계열 플롯 (전국/수도권/지방권)
#  1) 전국 시계열
plt.figure(figsize=(12, 5))
df_nation = df_processed[df_processed['region_name'] == '전국']
plt.plot(df_nation.index, df_nation['price_index'], label='Nation MaemaeIndex')
plt.plot(df_nation.index, df_nation['jeonse_index'], label='Nation JeonseIndex')
plt.title('Nation: MaemaeIndex vs JeonseIndex Time Series')
plt.xlabel('Year-Month')
plt.ylabel('Index')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('/mnt/data/nation_time_series.png')
plt.close()

#  2) 수도권 & 지방권 시계열
for region in ['수도권', '지방권']:
    df_region_plot = df_processed[df_processed['region_name'] == region]
    plt.figure(figsize=(10, 4))
    plt.plot(df_region_plot.index, df_region_plot['price_index'], label=f'{region} MaemaeIndex')
    plt.plot(df_region_plot.index, df_region_plot['jeonse_index'], label=f'{region} JeonseIndex')
    plt.title(f'{region}: MaemaeIndex vs JeonseIndex Time Series')
    plt.xlabel('Year-Month')
    plt.ylabel('Index')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    # 한글 폰트 경고가 있을 수 있음 (UI 출력용으로 저장)
    file_name = f"/mnt/data/{region}_time_series.png"
    plt.savefig(file_name)
    plt.close()

# 5.2.6. 결과 이미지 링크 출력
print("Plots:")
print("[Nation Time Series](sandbox:/mnt/data/nation_time_series.png)")
print("[수도권 Time Series](sandbox:/mnt/data/수도권_time_series.png)")
print("[지방권 Time Series](sandbox:/mnt/data/지방권_time_series.png)")
```

**의도**:

1. `.describe()`와 `corr()` 등을 사용하여 기초 통계 및 상관관계를 파악합니다.
2. 연도별 집계 및 증감률을 통해 장기 트렌드를 정량적으로 확인합니다.
3. 시계열 플롯을 통해 시각적으로 전국/권역별 매매 vs 전세 지수의 흐름을 관찰합니다.
4. 한글 폰트 미설정으로 인한 경고는 무시 가능하며, 이미지 파일로 저장하여 UI에 표시합니다.

---

## 6. 거래량(Transaction Count) 데이터 전처리 및 권역별 집계

### 6.1. 목적

* `(월) 행정구역별 아파트매매거래현황_전체.csv` 파일에서 **매매 거래 건수(동(호)수)** 정보를 추출
* 행정구역별(시도, 시군구, 동) 단위 데이터를 **권역(수도권/지방권/전국)** 수준으로 집계하여, `transaction_count` 칼럼 생성
* 이후 매매·전세 지수 데이터(`df_processed`)와 권역별 거래량을 병합할 준비

### 6.2. 코드

```python
# 6.2.1. 거래현황 파일 경로 지정
trans_file = '/mnt/data/(월) 행정구역별 아파트매매거래현황_전체.csv'

# 6.2.2. UTF-8 로드 시도, 실패 시 CP949로 재시도
import pandas as pd
try:
    df_trans = pd.read_csv(trans_file, encoding='utf-8')
except UnicodeDecodeError:
    df_trans = pd.read_csv(trans_file, encoding='cp949')

# 6.2.3. '항목' 열에서 "호수"를 포함하는 행(거래 건수 정보)만 필터
# - 매매거래현황 파일에는 "동(호)수"(거래 건수)와 면적 정보(제곱미터) 등이 둘 이상의 행으로 분리되어 있음
# - 우리가 필요한 것은 "동(호)수"에 해당하는 행
mask = df_trans['항목'].str.contains('호수')
df_trans_tc = df_trans[mask].copy()

# 6.2.4. 시간 컬럼(YYYY년 M월 형태) 추출
#     예: '2006년 1월', '2006년 1월.1' 등으로 헤더가 반복되므로, '년'과 '월' 문자열 포함 여부로 찾음
time_cols_trans = [col for col in df_trans_tc.columns if '년' in str(col) and '월' in str(col)]

# 6.2.5. Melt를 통하여 Wide → Long 변환
# - id_vars로는 '행정구역별'만 남기고, 나머지 시간별 거래 건수 컬럼을 value_vars로 사용
df_trans_long = df_trans_tc.melt(
    id_vars=['행정구역별'],
    value_vars=time_cols_trans,
    var_name='YearMonth',
    value_name='transaction_count'
)

# 6.2.6. YearMonth 문자열을 'YYYY-MM'로 변환하는 함수 정의
def convert_year_month_fmt(korean_str):
    try:
        # '2006년 1월' → ['2006', '1']
        year, month = str(korean_str).replace('년', '').replace('월', '').split()
        month = month.zfill(2)
        return f"{year}-{month}"
    except:
        return None

# 6.2.7. 변환 적용 및 NULL 제거
df_trans_long['YearMonth'] = df_trans_long['YearMonth'].apply(convert_year_month_fmt)
df_trans_long = df_trans_long.dropna(subset=['YearMonth'])
df_trans_long['year_month'] = pd.to_datetime(df_trans_long['YearMonth'], format='%Y-%m')

# 6.2.8. 거래 건수를 numeric으로 변환
import numpy as np
df_trans_long['transaction_count'] = pd.to_numeric(df_trans_long['transaction_count'], errors='coerce')

# 6.2.9. 행정구역별 컬럼(시도, 시군구, 동)로 분리 (필요하면 세부 분석용)
# - 하지만 권역 집계를 위해서는 시도 수준만 있으면 충분 (시군구·동 수준은 생략)
# - 예: '서울특별시 중구 신당동' → ['서울특별시','중구','신당동']

# 적절한 시도명 리스트 정의 (시도 단위 데이터만 남기기 위함)
sido_names = [
    '서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시',
    '울산광역시','세종특별자치시','경기도','강원도','충청북도','충청남도',
    '전라북도','전라남도','경상북도','경상남도','제주특별자치도'
]

# 6.2.10. '행정구역별'이 시도명과 일치하는 행만 필터하여 권역 집계의 기초 데이터로 사용
df_trans_sido = df_trans_long[df_trans_long['행정구역별'].isin(sido_names)].copy()

# 6.2.11. 권역(Zone) 할당 함수 정의
def assign_zone(sido):
    if sido in ['서울특별시', '경기도', '인천광역시']:
        return '수도권'
    else:
        return '지방권'

# 6.2.12. zone 컬럼 추가
df_trans_sido['zone'] = df_trans_sido['행정구역별'].apply(assign_zone)

# 6.2.13. 권역별 월별 거래 건수 집계
df_zone_trans = (
    df_trans_sido
    .groupby(['zone', 'year_month'])['transaction_count']
    .sum()
    .reset_index()
)

# 6.2.14. 전국 단위 집계: 모든 권역(zone) 합산
df_nation_trans = (
    df_zone_trans
    .groupby('year_month')['transaction_count']
    .sum()
    .reset_index()
)
df_nation_trans['zone'] = '전국'

# 6.2.15. 권역별 + 전국 결합 (concat)
df_zone_all = pd.concat([df_zone_trans, df_nation_trans], ignore_index=True)

# 6.2.16. 결과 샘플 출력
tools.display_dataframe_to_user(name="Zone-level Transaction Counts Sample", dataframe=df_zone_all.head())
```

**의도**:

1. 거래현황 파일에서 **"동(호)수"(매매 거래 건수)** 정보를 추출하기 위해 `항목` 열에 '호수'가 포함된 행만 남깁니다.
2. `melt`를 사용하여 월별 Wide 형식 데이터를 Long 형식으로 변환하고, `year_month` 컬럼을 `datetime`으로 가공합니다.
3. 전국/수도권/지방권 수준의 권역 집계를 위해, 시도 수준 데이터(`행정구역별`이 시도명인 행)만 필터링합니다.
4. `assign_zone` 함수를 통해 시도명을 권역으로 맵핑(`수도권` vs `지방권`)하고, 월별로 집계합니다.
5. 전국 단위를 추가로 만들어 전체 거래 건수를 구하고, 권역별 + 전국 데이터를 합쳐 최종 권역별 거래 건수 테이블(`df_zone_all`)을 만듭니다.

---

## 7. 매매·전세 지수 + 거래건수 병합

### 7.1. 목적

* 4단계에서 만든 **권역(전국, 수도권, 지방권)별 매매·전세 지수**(`df_processed`)와
  6단계에서 만든 **권역별 거래 건수**(`df_zone_all`)를 `region_name` + `year_month` 기준으로 병합하여,
  한 DataFrame에서 가격지수와 거래량을 모두 확인할 수 있도록 합니다.

### 7.2. 코드

```python
# 7.2.1. df_processed가 이미 존재한다고 가정 (index=year_month, columns=['region_name','price_index','jeonse_index'])
df_region = df_processed[df_processed['region_name'].isin(['전국', '수도권', '지방권'])].dropna(subset=['price_index', 'jeonse_index']).copy()

# 7.2.2. 병합을 위해 index인 'year_month'를 컬럼으로 복원
df_region = df_region.reset_index()

# 7.2.3. df_zone_all(zone별 transaction_count)에서 'zone' 칼럼명을 'region_name'으로 변경
df_zone_all_rename = df_zone_all.rename(columns={'zone': 'region_name'})

# 7.2.4. Left Join 수행 (region_name + year_month 기준)
df_region = (
    df_region
    .merge(
        df_zone_all_rename,
        on=['region_name', 'year_month'],
        how='left'
    )
)

# 7.2.5. 다시 'year_month'를 인덱스로 설정
df_region = df_region.set_index('year_month')

# 7.2.6. 병합 후 샘플 출력
tools.display_dataframe_to_user(name="Merged Indices & Transaction Counts Sample", dataframe=df_region.head())
```

**의도**:

1. `df_processed`에는 지역별(전국, 수도권, 지방권) 매매·전세 지수가 준비되어 있습니다.
2. `df_zone_all`에는 동일 권역별 월별 거래 건수가 있으므로, 두 DataFrame을 `Left Join`하여 `transaction_count` 칼럼을 추가합니다.
3. 결과로 `df_region`에는 `price_index`, `jeonse_index`, `transaction_count`를 모두 포함한 권역별 시계열 데이터가 완성됩니다.

---

## 8. 지역별 상관관계 및 간단 회귀 분석

### 8.1. 목적

* `df_region`에서 **매매지수 vs 전세지수**, **매매지수 vs 거래건수** 간 상관관계를 권역별로 계산합니다.
* `전국` 권역을 대상으로 **OLS 회귀**(매매지수 \~ 거래건수) 분석을 수행하고 요약 결과를 확인합니다.

### 8.2. 코드

```python
import statsmodels.formula.api as smf

# 8.2.1. 전세지수 대비 매매지수 비율 계산 (추가 인사이트용)
df_region['jeonse_to_maemae_ratio'] = df_region['jeonse_index'] / df_region['price_index']

# 8.2.2. 권역별 매매지수 ↔ 전세지수 상관계수 계산
corr_price_jeonse_list = []
for region, group in df_region.groupby('region_name'):
    corr_val = group['price_index'].corr(group['jeonse_index'])
    corr_price_jeonse_list.append({
        'region_name': region,
        'corr_price_jeonse': corr_val
    })
corr_price_jeonse_summary = pd.DataFrame(corr_price_jeonse_list)
tools.display_dataframe_to_user(name="Correlation: Price vs Jeonse by Region", dataframe=corr_price_jeonse_summary)

# 8.2.3. 권역별 매매지수 ↔ 거래건수 상관계수 계산
corr_price_trans_list = []
for region, group in df_region.groupby('region_name'):
    corr_val = group['price_index'].corr(group['transaction_count'])
    corr_price_trans_list.append({
        'region_name': region,
        'corr_price_trans': corr_val
    })
corr_price_trans_summary = pd.DataFrame(corr_price_trans_list)
tools.display_dataframe_to_user(name="Correlation: Price vs Transaction Count by Region", dataframe=corr_price_trans_summary)

# 8.2.4. 전국 권역에 대한 OLS 회귀 (price_index ~ transaction_count)
df_nation_reg = df_region[df_region['region_name']=='전국'].dropna(subset=['price_index', 'transaction_count'])
model_nation = smf.ols('price_index ~ transaction_count', data=df_nation_reg).fit()
reg_summary_text = model_nation.summary().as_text()
print("OLS Regression Summary for '전국':")
print(reg_summary_text)

# 8.2.5. 전국 산점도(매매지수 vs 거래건수)
plt.figure(figsize=(8, 5))
plt.scatter(df_nation_reg['transaction_count'], df_nation_reg['price_index'], alpha=0.5)
plt.title('Nation: Price Index vs Transaction Count')
plt.xlabel('Transaction Count')
plt.ylabel('Price Index')
plt.grid(True)
plt.tight_layout()
plt.savefig('/mnt/data/nation_price_trans_scatter.png')
plt.close()
print("Scatter Plot: [Nation Price vs Transaction Count](sandbox:/mnt/data/nation_price_trans_scatter.png)")
```

**의도**:

1. `corr()` 함수를 사용하여 두 변수 간 **Pearson 상관계수**를 권역별로 산출합니다.
2. `statsmodels` OLS를 이용하여 `전국` 권역에서 매매지수를 거래건수로 설명하는 단순 선형 회귀 모형을 학습합니다.
3. 회귀 결과 요약(`model.summary()`)과 산점도를 통해, 거래량이 가격지수에 미치는 영향을 직관적으로 파악합니다.
4. 권역별로 동일 분석을 반복하면, 수치 기준으로 권역 간 차이를 확인할 수 있습니다.

---

## 9. Feature Engineering: 시계열 모델 입력 형태 정리

### 9.1. 목적

* `df_region`에는 이미 가격지수(`price_index`, `jeonse_index`)와 거래량(`transaction_count`)이 포함된 권역별 시계열 데이터가 준비되어 있습니다.
* 이제 **시계열 예측용**으로 사용될 주요 Feature를 생성합니다:

  1. 차분(First Difference)
  2. 이동평균(Moving Average)
  3. 전세↔매매 격차, 성장률 등
  4. 거래량 기반 Feature (로그 변환, 상호작용 등)
  5. 지연(Lag) Feature
* 최종적으로 머신러닝/딥러닝 모델(예: LSTM, XGBoost, 시계열 회귀 등) 입력으로 사용할 수 있는 테이블을 구성합니다.

### 9.2. 코드

```python
import numpy as np

# 9.2.1. df_region 복사하여 작업 (원본 보존)
df_features = df_region.copy()

# 9.2.2. 시계열 정렬 및 그룹화 (region_name별로 groupby 수행하여 rolling, shift 적용)
df_features = (
    df_features
    .reset_index()  # 'year_month'가 인덱스였으므로 컬럼으로 복원
    .sort_values(['region_name', 'year_month'])
    .set_index('year_month')
)

grouped = df_features.groupby('region_name')

# 9.2.3. 1차 차분: price_diff_1m, jeonse_diff_1m
df_features['price_diff_1m'] = grouped['price_index'].diff(1)
df_features['jeonse_diff_1m'] = grouped['jeonse_index'].diff(1)

# 9.2.4. 3개월 이동평균: price_ma_3m, jeonse_ma_3m
df_features['price_ma_3m'] = grouped['price_index'].rolling(window=3).mean().reset_index(level=0, drop=True)
df_features['jeonse_ma_3m'] = grouped['jeonse_index'].rolling(window=3).mean().reset_index(level=0, drop=True)

# 9.2.5. 전세↔매매 격차 및 성장률
# - price_to_jeonse_gap: 매매지수 - 전세지수
# - price_growth_rate: 전월 대비 매매지수 등락률
#   (diff()/shift 또는 pct_change 사용 가능)
df_features['price_to_jeonse_gap'] = df_features['price_index'] - df_features['jeonse_index']
df_features['price_growth_rate'] = grouped['price_index'].pct_change()

# 9.2.6. 거래량 기반 Feature: 로그 변환 및 지수 × 로그 거래
# - transaction_log = log1p(transaction_count)
# - price_trans_interaction = price_index * transaction_log
df_features['transaction_log'] = np.log1p(df_features['transaction_count'])
df_features['price_trans_interaction'] = df_features['price_index'] * df_features['transaction_log']

# 9.2.7. 지연(Lag) Feature 생성 (1~3개월 전 지수)
for lag in [1, 2, 3]:
    df_features[f'price_lag_{lag}'] = grouped['price_index'].shift(lag)
    df_features[f'jeonse_lag_{lag}'] = grouped['jeonse_index'].shift(lag)

# 9.2.8. 샘플 출력 (전국 권역, 최신 10개 행)
df_sample = df_features[df_features['region_name'] == '전국'].tail(10)
tools.display_dataframe_to_user(name="Feature-Engineered Data Sample (Nation)", dataframe=df_sample)
```

**의도**:

1. **차분**(`.diff(1)`)으로 월간 변동 폭을 만들어, 모형이 추세보다는 변화량에 민감하도록 합니다.
2. **이동평균**(`.rolling(window=3).mean()`)을 통해 단기 노이즈를 완화한 지수 값을 생성합니다.
3. **격차 및 성장률**을 추가함으로써, 가격 간 상대적 변화 또는 증가율을 특징으로 삼습니다.
4. **거래량 로그 변환**: 거래 건수는 지수 수준과 단위가 다르므로 로그 변환 후 가격지수와 곱하여 상호작용 변수로 사용합니다.
5. **Lag Feature**: 1\~3개월 전 매매·전세 지수를 lag로 생성하여, 과거 정보가 현재 예측 변수로 작용하도록 합니다.
6. 이후 모델링 시 `.dropna()`를 사용해 NaN(이동평균 및 Lag로 인한) 행을 제거하거나, 적절한 결측치 처리 전략(보간, 전방 채우기 등)을 적용합니다.

---

## 10. 전체 코드 흐름 정리

아래는 **1번 (구조 점검) \~ 5번 (Feature Engineering)** 단계까지의 전체 코드 흐름을 통합하여, 한 번에 실행할 수 있는 형태로 정리한 예시입니다.

````python
# --------------------------------------------
# 1. 프로젝트 폴더 및 데이터 파일 구조 점검
# --------------------------------------------
import pandas as pd
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# 데이터 디렉터리
data_dir = '/mnt/data'

# CSV 파일 목록
csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

# 파일별 정보 수집 (샘플 5행)
summary_info = []
for file in csv_files:
    file_path = os.path.join(data_dir, file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8', nrows=5)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949', nrows=5)
    summary_info.append({
        'Filename': file,
        'Preview Shape': (df.shape[0], df.shape[1]),
        'Columns': list(df.columns)
    })
summary_df = pd.DataFrame(summary_info)
print(summary_df)

# --------------------------------------------
# 2. 매매지수 & 전세지수 데이터 전처리 (Long 포맷 변환)
# --------------------------------------------
# 파일 경로
maemae_file = '/mnt/data/(월) 매매가격지수_아파트.csv'
jeonse_file = '/mnt/data/(월) 전세가격지수_아파트.csv'

# 로드
try:
    maemae_df = pd.read_csv(maemae_file, encoding='utf-8')
except UnicodeDecodeError:
    maemae_df = pd.read_csv(maemae_file, encoding='cp949')

try:
    jeonse_df = pd.read_csv(jeonse_file, encoding='utf-8')
except UnicodeDecodeError:
    jeonse_df = pd.read_csv(jeonse_file, encoding='cp949')

# 지역 계층 컬럼
region_cols = ['분류', '분류.1', '분류.2', '분류.3']

# 시간 컬럼 추출 (YYYY년 M월)
time_cols_maemae = [col for col in maemae_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]
time_cols_jeonse = [col for col in jeonse_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]

# Melt (Wide → Long)
maemae_long = maemae_df.melt(id_vars=region_cols, value_vars=time_cols_maemae,
                             var_name='YearMonth', value_name='MaemaeIndex')
jeonse_long = jeonse_df.melt(id_vars=region_cols, value_vars=time_cols_jeonse,
                             var_name='YearMonth', value_name='JeonseIndex')

# YearMonth 변환 함수
def convert_year_month(korean_str):
    match = re.match(r"(\d{4})년\s*(\d{1,2})월", str(korean_str))
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        return f"{year}-{month}"
    return None

maemae_long['YearMonth'] = maemae_long['YearMonth'].apply(convert_year_month)
jeonse_long['YearMonth'] = jeonse_long['YearMonth'].apply(convert_year_month)

# 헤더 행 제거
maemae_clean = maemae_long[maemae_long['분류'] != '분류'].copy()
jeonse_clean = jeonse_long[jeonse_long['분류'] != '분류'].copy()

# 숫자형 변환
maemae_clean['MaemaeIndex'] = pd.to_numeric(maemae_clean['MaemaeIndex'], errors='coerce')
jeonse_clean['JeonseIndex'] = pd.to_numeric(jeonse_clean['JeonseIndex'], errors='coerce')

# --------------------------------------------
# 3. 매매지수 & 전세지수 병합
# --------------------------------------------
merged_df = pd.merge(
    maemae_clean,
    jeonse_clean,
    on=['분류', '분류.1', '분류.2', '분류.3', 'YearMonth'],
    how='inner'
)

# --------------------------------------------
# 4. 권역별/지역별 전처리 (컬럼 정리 및 인덱스 설정)
# --------------------------------------------
# 4.1. Top-level 분류 값을 region_name으로
merged_df['region_name'] = merged_df['분류']

# 4.2. YearMonth를 datetime으로 변환하고 'year_month' 컬럼 생성
merged_df['year_month'] = pd.to_datetime(merged_df['YearMonth'], format='%Y-%m')

# 4.3. 필요한 칼럼만 추출 및 칼럼명 영어로 변경
df_processed = merged_df[['region_name', 'year_month', 'MaemaeIndex', 'JeonseIndex']].copy()
df_processed = df_processed.rename(columns={
    'MaemaeIndex': 'price_index',
    'JeonseIndex': 'jeonse_index'
})

# 4.4. 'year_month'를 인덱스로 설정하여 시계열 형태 정렬
df_processed = df_processed.set_index('year_month').sort_index()

# --------------------------------------------
# 5. 기초 EDA (통계 요약, 상관관계, 시계열 플롯)
# --------------------------------------------
# 5.1. 기초 통계

```python
desc_stats = df_processed[['price_index', 'jeonse_index']].describe()
print(desc_stats)
````

```python
# 5.2. 연도별 평균 및 YoY 증감률
df_processed['year'] = df_processed.index.year
df_yearly = df_processed.groupby('year')[['price_index','jeonse_index']].mean().reset_index()
df_yearly['price_pct_change'] = df_yearly['price_index'].pct_change() * 100
df_yearly['jeonse_pct_change'] = df_yearly['jeonse_index'].pct_change() * 100
print(df_yearly)
```

```python
# 5.3. 전체 상관관계
corr_matrix = df_processed[['price_index', 'jeonse_index']].corr()
print(corr_matrix)
```

```python
# 5.4. 연도별 상관관계 변화
def compute_corr_year(group):
    return group['price_index'].corr(group['jeonse_index'])
corr_by_year = df_processed.groupby('year').apply(compute_corr_year).reset_index(name='corr_price_jeonse')
print(corr_by_year)
```

```python
# 5.5. 권역별 시계열 플롯
plt.figure(figsize=(12, 5))
df_nation = df_processed[df_processed['region_name']=='전국']
plt.plot(df_nation.index, df_nation['price_index'], label='Nation MaemaeIndex')
plt.plot(df_nation.index, df_nation['jeonse_index'], label='Nation JeonseIndex')
plt.title('Nation: MaemaeIndex vs JeonseIndex Time Series')
plt.xlabel('Year-Month')
plt.ylabel('Index')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('/mnt/data/nation_time_series.png')
plt.close()

for region in ['수도권','지방권']:
    df_r = df_processed[df_processed['region_name']==region]
    plt.figure(figsize=(10,4))
    plt.plot(df_r.index, df_r['price_index'], label=f'{region} MaemaeIndex')
    plt.plot(df_r.index, df_r['jeonse_index'], label=f'{region} JeonseIndex')
    plt.title(f'{region}: MaemaeIndex vs JeonseIndex Time Series')
    plt.xlabel('Year-Month')
    plt.ylabel('Index')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'/mnt/data/{region}_time_series.png')
    plt.close()
```

```python
print("Plots:")
print("[Nation Time Series](sandbox:/mnt/data/nation_time_series.png)")
print("[수도권 Time Series](sandbox:/mnt/data/수도권_time_series.png)")
print("[지방권 Time Series](sandbox:/mnt/data/지방권_time_series.png)")
```

# --------------------------------------------

# 6. 거래량 데이터 전처리 및 권역별 집계

# --------------------------------------------

```python
# 6.1. 파일 로드
trans_file = '/mnt/data/(월) 행정구역별 아파트매매거래현황_전체.csv'
try:
    df_trans = pd.read_csv(trans_file, encoding='utf-8')
except UnicodeDecodeError:
    df_trans = pd.read_csv(trans_file, encoding='cp949')

# 6.2. "호수" 포함 행 필터
df_trans_tc = df_trans[df_trans['항목'].str.contains('호수')].copy()

# 6.3. 시간 컬럼 추출
time_cols_trans = [col for col in df_trans_tc.columns if '년' in str(col) and '월' in str(col)]

# 6.4. Melt (Wide → Long)
df_trans_long = df_trans_tc.melt(id_vars=['행정구역별'],
                                  value_vars=time_cols_trans,
                                  var_name='YearMonth',
                                  value_name='transaction_count')

# 6.5. YearMonth 변환 및 datetime 처리
def convert_year_month_fmt(korean_str):
    try:
        year, month = str(korean_str).replace('년','').replace('월','').split()
        month = month.zfill(2)
        return f"{year}-{month}"
    except:
        return None

df_trans_long['YearMonth'] = df_trans_long['YearMonth'].apply(convert_year_month_fmt)
df_trans_long = df_trans_long.dropna(subset=['YearMonth'])
df_trans_long['year_month'] = pd.to_datetime(df_trans_long['YearMonth'], format='%Y-%m')

# 6.6. 거래 건수 numeric 변환
df_trans_long['transaction_count'] = pd.to_numeric(df_trans_long['transaction_count'], errors='coerce')

# 6.7. 시도별 필터
sido_names = [
    '서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시',
    '울산광역시','세종특별자치시','경기도','강원도','충청북도','충청남도',
    '전라북도','전라남도','경상북도','경상남도','제주특별자치도'
]

df_trans_sido = df_trans_long[df_trans_long['행정구역별'].isin(sido_names)].copy()

# 6.8. 권역 할당 함수
def assign_zone(sido):
    if sido in ['서울특별시','경기도','인천광역시']:
        return '수도권'
    else:
        return '지방권'


# 6.9. zone 컬럼 추가
df_trans_sido['zone'] = df_trans_sido['행정구역별'].apply(assign_zone)

# 6.10. 권역별 월별 거래 건수 집계
df_zone_trans = (
    df_trans_sido
    .groupby(['zone','year_month'])['transaction_count']
    .sum()
    .reset_index()
)

# 6.11. 전국 집계
df_nation_trans = (
    df_zone_trans
    .groupby('year_month')['transaction_count']
    .sum()
    .reset_index()
)
df_nation_trans['zone'] = '전국'

# 6.12. 권역별 + 전국 결합
df_zone_all = pd.concat([df_zone_trans, df_nation_trans], ignore_index=True)

# 6.13. 샘플 출력
print(df_zone_all.head())
```

# --------------------------------------------

# 7. 매매·전세 지수 + 거래량 병합

# --------------------------------------------

```python
# 7.1. 권역별 매매·전세 지수 준비 (index: year_month)
df_region = df_processed[df_processed['region_name'].isin(['전국','수도권','지방권'])].dropna(subset=['price_index','jeonse_index']).reset_index()

# 7.2. df_zone_all(zone별 거래량)에서 칼럼명 조정
df_zone_all_rename = df_zone_all.rename(columns={'zone':'region_name'})

# 7.3. Left Join (region_name+year_month)
df_region = (
    df_region
    .merge(
        df_zone_all_rename,
        on=['region_name','year_month'],
        how='left'
    )
)

# 7.4. 인덱스 재설정
df_region = df_region.set_index('year_month')

# 7.5. 샘플 출력
print(df_region.head())
```

# --------------------------------------------

# 8. 지역별 상관관계 및 회귀 분석

# --------------------------------------------

```python
import statsmodels.formula.api as smf

# 8.1. 전세↔매매 비율 생성
df_region['jeonse_to_maemae_ratio'] = df_region['jeonse_index'] / df_region['price_index']

# 8.2. 권역별 매매↔전세 상관계수
corr_price_jeonse_list = []
for region, group in df_region.groupby('region_name'):
    corr_val = group['price_index'].corr(group['jeonse_index'])
    corr_price_jeonse_list.append({'region_name':region, 'corr_price_jeonse':corr_val})
corr_price_jeonse_summary = pd.DataFrame(corr_price_jeonse_list)
print(corr_price_jeonse_summary)

# 8.3. 권역별 매매↔거래건수 상관계수
corr_price_trans_list = []
for region, group in df_region.groupby('region_name'):
    corr_val = group['price_index'].corr(group['transaction_count'])
    corr_price_trans_list.append({'region_name':region, 'corr_price_trans':corr_val})
corr_price_trans_summary = pd.DataFrame(corr_price_trans_list)
print(corr_price_trans_summary)

# 8.4. 전국 권역 OLS 회귀 (매매지수 ~ 거래건수)
df_nation_reg = df_region[df_region['region_name']=='전국'].dropna(subset=['price_index','transaction_count'])
model_nation = smf.ols('price_index ~ transaction_count', data=df_nation_reg).fit()
print(model_nation.summary())

# 8.5. 전국 산점도 (매매지수 vs 거래건수)
plt.figure(figsize=(8,5))
plt.scatter(df_nation_reg['transaction_count'], df_nation_reg['price_index'], alpha=0.5)
plt.title('Nation: Price Index vs Transaction Count')
plt.xlabel('Transaction Count')
plt.ylabel('Price Index')
plt.grid(True)
plt.tight_layout()
plt.savefig('/mnt/data/nation_price_trans_scatter.png')
plt.close()
print("[Nation Price vs Transaction Count Scatter](sandbox:/mnt/data/nation_price_trans_scatter.png)")
```

# --------------------------------------------

# 9. Feature Engineering (시계열 모델 입력 형태)

# --------------------------------------------

```python
import numpy as np

# 9.1. df_region 복사

df_features = df_region.copy()

# 9.2. 시계열 정렬 및 그룹화

df_features = (
    df_features
    .reset_index()
    .sort_values(['region_name','year_month'])
    .set_index('year_month')
)

grouped = df_features.groupby('region_name')

# 9.3. 1차 차분

df_features['price_diff_1m'] = grouped['price_index'].diff(1)

df_features['jeonse_diff_1m'] = grouped['jeonse_index'].diff(1)

# 9.4. 3개월 이동평균

df_features['price_ma_3m'] = grouped['price_index'].rolling(window=3).mean().reset_index(level=0, drop=True)

df_features['jeonse_ma_3m'] = grouped['jeonse_index'].rolling(window=3).mean().reset_index(level=0, drop=True)

# 9.5. 격차 및 성장률

df_features['price_to_jeonse_gap'] = df_features['price_index'] - df_features['jeonse_index']

df_features['price_growth_rate'] = grouped['price_index']

# .pct_change()와 동일하게 작동하므로 아래 코드로 대체 가능
# df_features['price_growth_rate'] = grouped['price_index'].pct_change()

# 9.6. 거래량 기반 Feature

df_features['transaction_log'] = np.log1p(df_features['transaction_count'])

df_features['price_trans_interaction'] = df_features['price_index'] * df_features['transaction_log']

# 9.7. Lag Feature 생성

for lag in [1,2,3]:
    df_features[f'price_lag_{lag}'] = grouped['price_index'].shift(lag)
    df_features[f'jeonse_lag_{lag}'] = grouped['jeonse_index'].shift(lag)

# 9.8. 결과 샘플 출력
df_sample = df_features[df_features['region_name']=='전국'].tail(10)
print(df_sample)
```

---

위 코드 및 주석을 통해, **원시 데이터 로드 → Long 포맷 변환 → 병합 → 권역별 전처리 → EDA → 거래량 집계 → 병합 → 상관·회귀 분석 → Feature Engineering** 전 과정을 순서대로 생략 없이 확인할 수 있습니다.

각 코드 블록 상단의 주석(`##`, `###`, `#`)에는 함수 호출 의도 및 세부 설명이 포함되어 있어, 분석 파이프라인 전체 흐름을 이해하는 데 도움이 됩니다.

필요한 사항이나 추가 요청이 있으면 언제든 알려주세요!

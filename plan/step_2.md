
## 📌 2. 데이터 전처리 로드맵 (단계별)

### 단계 A. 거래·가격 데이터 전처리

#### A-1. 대상 파일

* `(월) 매매가격지수_아파트.csv`
* `(월) 전세가격지수_아파트.csv`
* `(월) 행정구역별 아파트거래현황_전체.csv`
* `(월) 행정구역별 아파트매매거래현황_전체.csv`
* `(주) 매매가격지수.csv` (선택적으로 사용)

> **목표**:
>
> 1. "시·군·구 코드 + 연도-월"을 키로 하는 패널 데이터프레임(DataFrame)의 뼈대를 만든다.
> 2. 월별 매매가격 지수(price\_index), 전세가격 지수(jeonse\_index), 거래량(transaction\_count) 등을 이 프레임에 칼럼으로 입힌다.

##### A-1-①. 파일 로딩 및 인코딩 확인

1. **인코딩**

   * `pandas.read_csv(…, encoding='cp949' 또는 'euc-kr')` vs `encoding='utf-8'` 중 깨지지 않는 쪽으로 로드
   * 예)

     ```python
     df_price = pd.read_csv('매매가격지수_아파트.csv', encoding='cp949')
     df_jeonse = pd.read_csv('전세가격지수_아파트.csv', encoding='cp949')
     df_trans_all = pd.read_csv('행정구역별 아파트거래현황_전체.csv', encoding='utf-8')
     ```
   * **로딩 후 바로** `df.head()`/`df.info()`로 한글·숫자 컬럼이 정상적으로 보이는지 확인

2. **파일별 컬럼명 파악**

   * 보통 `지역코드(시·군·구)`, `지역명(시·군·구)`, `시점(YYYY.MM)`, `지수값` 형태
   * 예) 매매가격지수 파일:

     ```
     ['시도명', '시군구명', '지역코드', '기준년월', '매매가격지수']  
     ```
   * 전세가격지수 파일:

     ```
     ['시도명', '시군구명', '지역코드', '기준년월', '전세가격지수']  
     ```
   * 거래현황 파일:

     ```
     ['시도코드', '시군구코드', '시도명', '시군구명', '시점', '거래량', '평균매매가', …]  
     ```

##### A-1-②. 컬럼명 표준화 및 날짜 형식 변환

1. **컬럼명 통일**

   * 모든 DF에서 "지역코드" 컬럼명은 `region_code`, "시점" 컬럼은 `year_month`로 통일
   * 예)

     ```python
     df_price = df_price.rename(columns={'지역코드':'region_code', '기준년월':'year_month', '매매가격지수':'price_index'})
     df_jeonse = df_jeonse.rename(columns={'지역코드':'region_code', '기준년월':'year_month', '전세가격지수':'jeonse_index'})
     df_trans_all = df_trans_all.rename(columns={'시군구코드':'region_code', '시점':'year_month', '거래량':'transaction_count', '평균매매가':'avg_transaction_price'})
     ```
2. **날짜(datetime) 변환**

   * `year_month`에 "YYYY.MM" 형태가 들어있는 경우:

     ```python
     df_price['year_month'] = pd.to_datetime(df_price['year_month'], format='%Y.%m')
     df_jeonse['year_month'] = pd.to_datetime(df_jeonse['year_month'], format='%Y.%m')
     df_trans_all['year_month'] = pd.to_datetime(df_trans_all['year_month'], format='%Y.%m')
     ```
   * 주 단위 지수가 있을 경우, 예) "YYYY-WW" 형식 → 월별 분석 목표이므로, "해당 주의 첫 번째 날짜" 또는 "해당 주가 속한 연-월"로 환산

     ```python
     df_weekly['year_month'] = df_weekly['basedate'].dt.to_period('M').dt.to_timestamp()
     ```

##### A-1-③. 결측치 및 이상치 점검

1. **결측치 비율 확인**

   * 각 DF마다

     ```python
     df_price.isna().sum() / len(df_price)
     df_jeonse.isna().sum() / len(df_jeonse)
     df_trans_all.isna().sum() / len(df_trans_all)
     ```
   * '매매가격지수'/거래량'에 결측이 있으면 바로 `drop`하기보다는

     * **시·군·구별 시계열 결측구간**이 연속으로 얼마나 존재하는지 확인 → "정상적으로 시계열 구축 가능한지" 판단
     * 만약 한 두 개월 결측이면, 인근 월 값으로 보간(linear/interpolate) 가능
2. **이상치 탐지**

   * 논리적 이상치 예시

     * 매매가격지수가 음수 또는 0으로 기록된 경우
     * 거래량이 갑자기 평소 대비 10배 이상 튀는 경우
   * 간단한 처리

     ```python
     # 음수/0인 매매가격지수 삭제
     df_price = df_price[df_price['price_index'] > 0]
     # 거래량 이상치: 상위 0.1% 값 로그 확인, 필요하면 clip 혹은 nan 처리
     thresh = df_trans_all['transaction_count'].quantile(0.999)
     df_trans_all.loc[df_trans_all['transaction_count'] > thresh, 'transaction_count'] = np.nan
     ```
   * 결측 처리 로그를 별도 파일(또는 CSV)로 저장하여, "추후 보고서에 결측·이상치 처리 방법론" 부분에 인용

##### A-1-④. 지역 코드 정합성 및 최종 패널 뼈대 생성

1. **region\_code 확인**

   * `df_price['region_code'].nunique()`와 `df_trans_all['region_code'].nunique()` 비교
   * 모든 거래 데이터에는 최소한 매매/전세지수에 존재하는 region\_code가 있어야 함 → 빠진 경우,

     * 시·군·구 이름 기준으로 조인할 수 있는지 확인(`merge(on=['시도명','시군구명'])` 후 코드 부여)
2. **"시·군·구 × 월" 인덱스 생성**

   * 프로젝트 분석 기간(예: 2015년 1월 \~ 2024년 4월) 기준으로 모든 시·군·구가 월 단위 패널을 가지게끔 빈 뼈대 생성
   * 예시:

     ```python
     all_regions = sorted(df_price['region_code'].unique())
     all_months = pd.date_range(start='2015-01-01', end='2024-04-01', freq='MS')
     panel_index = pd.MultiIndex.from_product([all_regions, all_months], names=['region_code','year_month'])
     df_panel = pd.DataFrame(index=panel_index).reset_index()
     ```
3. **각 DF를 이 뼈대에 `merge`**

   * 순서대로(매매지수 → 전세지수 → 거래량 → 평균매매가)

     ```python
     df_panel = df_panel.merge(df_price[['region_code','year_month','price_index']], on=['region_code','year_month'], how='left')
     df_panel = df_panel.merge(df_jeonse[['region_code','year_month','jeonse_index']], on=['region_code','year_month'], how='left')
     df_panel = df_panel.merge(df_trans_all[['region_code','year_month','transaction_count','avg_transaction_price']], on=['region_code','year_month'], how='left')
     ```
   * 머지 후에도 결측치가 생길 수 있음(예: 신규 신도시 출현으로 데이터가 없는 초기 월 등) →

     * 결측 시 로우를 그대로 놔두거나, 필요 시 "0으로 채우기" 혹은 "인근 유사 지역(A그룹)의 중앙값으로 대체"하는 방안 검토

##### A-1-⑤. 결과 확인 및 첫 번째 커밋

* 최종 `df_panel`에

  ```
  region_code | year_month | price_index | jeonse_index | transaction_count | avg_transaction_price
  ```

  등이 정상적으로 결합되었는지 확인
* 주요 통계:

  ```python
  df_panel[['price_index','jeonse_index','transaction_count','avg_transaction_price']].describe()
  ```
* **커밋 메시지 예시**:

  ```
  [STEP-A] 거래·가격 데이터 로딩 및 시·군·구×월 패널 뼈대 생성 완료
  ```

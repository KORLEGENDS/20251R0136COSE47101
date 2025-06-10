
### 단계 D. 청약 경쟁률·분양가 데이터 전처리

#### D-1. 대상 파일

* `한국부동산원_연도별 청약 평균 분양가 정보_20250430.csv`
* `한국부동산원_지역별 청약 평균 분양가 정보_20250430.csv`
* `한국부동산원_지역별 청약 경쟁률 정보_20250430.csv`

> **목표**:
>
> 1. "연도별" 혹은 "지역×연도" 단위로만 제공된 이 데이터를 어떻게 "월별 패널"에 결합할지 구상
> 2. 연도 단위인 경우, "해당 연도 전체(또는 해당 분기) 값 → 월별 복사(Forward-fill)" 방식 적용 가능

##### D-1-①. 파일 로딩 및 컬럼명 통일

1. **연도별 평균 분양가**

   ```python
   df_yearly_price = pd.read_csv('한국부동산원_연도별 청약 평균 분양가 정보_20250430.csv', encoding='utf-8')
   df_yearly_price = df_yearly_price.rename(columns={'연도':'year','평균분양가':'avg_subdivision_price'})
   df_yearly_price['year'] = df_yearly_price['year'].astype(int)
   ```
2. **지역별 평균 분양가**

   ```python
   df_region_price = pd.read_csv('한국부동산원_지역별 청약 평균 분양가 정보_20250430.csv', encoding='utf-8')
   df_region_price = df_region_price.rename(columns={'지역코드':'region_code','연도':'year','평균분양가':'region_avg_sub_price'})
   ```
3. **지역별 청약 경쟁률**

   ```python
   df_competition = pd.read_csv('한국부동산원_지역별 청약 경쟁률 정보_20250430.csv', encoding='utf-8')
   df_competition = df_competition.rename(columns={'지역코드':'region_code','연도':'year','청약경쟁률':'competition_rate'})
   ```

##### D-1-②. "연도 → 연-월" 시계열 매핑

1. **연도별 데이터(月 복사)**

   * 연도 단위로만 제공된 경우,

     ```python
     # 예: df_region_price
     df_region_price['year_month'] = pd.to_datetime(df_region_price['year'].astype(str) + '-01', format='%Y-%m')
     # df_panel에 merge하면, 해당 연도 1월 값만 들어감 → 이후 12개월 동안 계속 유지하려면:
     df_region_price = df_region_price.set_index(['region_code','year_month']).unstack().resample('MS').ffill().stack().reset_index()
     df_panel = df_panel.merge(df_region_price[['region_code','year_month','region_avg_sub_price']], on=['region_code','year_month'], how='left')
     ```
   * 청약 경쟁률도 동일 방식으로 처리
2. **연도별 vs 지역×연도별 데이터 차이**

   * "연도별 평균 분양가"(전국)과 "지역별 평균 분양가"(region×year) 두 개를 통합해야 할 수도 있음 →

     ```python
     df_region_price_full = df_region_price.merge(df_yearly_price[['year','avg_subdivision_price']], on='year', how='left')
     # 이후 df_panel merge
     ```
3. **결측치 처리**

   * 신규 신도시의 경우 "해당 연도 데이터"가 없을 수 있음(예: 교산은 2023년까지 정보가 없을 가능)
   * 이럴 땐 "NaN"으로 두거나, 인근 연도(前年)의 값을 임시로 부여했음을 명시

##### D-1-③. 세 번째 커밋

* **커밋 메시지 예시**:

  ```
  [STEP-D] 청약 경쟁률 및 평균 분양가 데이터 연도→월 복사 후 패널 결합 완료
  ```

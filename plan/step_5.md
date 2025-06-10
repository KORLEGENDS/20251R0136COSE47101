
### 단계 E. 거시·기타 통제 변수 전처리

#### E-1. 대상 파일

* `시군구 연령별 취업자 및 고용률.csv`
* `시도별 지역내총생산.csv`
* (필요 시) `인구증감 데이터(외부 수집)`
* (필요 시) 교통호재 이벤트(외부 수집)

> **목표**:
>
> 1. 시·군·구별 고용률, 시·도별 GRDP를 "월별 패널"로 변환
> 2. 인구증감률 또는 기타 인구통계가 있다면, 월별/연도별로 맞춰 결합

##### E-1-①. "시군구 연령별 취업자 및 고용률.csv" 로드

1. **컬럼명 파악**

   * 예시:

     ```
     ['시도코드','시군구코드','연도','연령대','취업자수','고용률(%)']  
     ```
   * 연령대별 정보가 상세히 들어 있다면, "전체 고용률(전 연령대 합산)" 또는 "주요 연령대(20\~39세) 고용률"로 피쳐 생성
   * 예)

     ```python
     df_emp = pd.read_csv('시군구 연령별 취업자 및 고용률.csv', encoding='cp949')
     # '전체 연령대' 행만 골라서 사용하거나, 연령대 컬럼을 pivot하여 전체 인구수 대비 취업자수 비율 계산
     df_emp_total = df_emp[df_emp['연령대']=='계'].copy()
     df_emp_total['year_month'] = pd.to_datetime(df_emp_total['연도'].astype(str)+'-01', format='%Y-%m')
     df_emp_total = df_emp_total.rename(columns={'고용률(%)':'employment_rate','시군구코드':'region_code'})
     ```
2. **연단위 → 월단위 복사**

   * 앞선 단계처럼

     ```python
     df_emp_total = df_emp_total.set_index(['region_code','year_month']).unstack().resample('MS').ffill().stack().reset_index()
     df_panel = df_panel.merge(df_emp_total[['region_code','year_month','employment_rate']], on=['region_code','year_month'], how='left')
     ```

##### E-1-②. "시도별 지역내총생산.csv" 로드

1. **컬럼명 파악**

   * 예시:

     ```
     ['시도명','연도','GRDP(억원)']  
     ```
2. **시도→시군구 매핑**

   ```python
   df_grdp = pd.read_csv('시도별 지역내총생산.csv', encoding='cp949')
   df_grdp['year_month'] = pd.to_datetime(df_grdp['연도'].astype(str)+'-01', format='%Y-%m')
   # 시도명 → region_code(시군구 전체)에 매핑하기 위한 매핑 테이블 사용
   df_grdp = df_grdp.merge(df_mapping[['시도명','region_code']], on='시도명', how='left')
   df_grdp = df_grdp.groupby(['region_code','year_month']).agg({'GRDP':'first'}).reset_index()
   df_panel = df_panel.merge(df_grdp, on=['region_code','year_month'], how='left')
   ```
3. **결측 처리**

   * 신도시가 포함된 경우, GRDP 데이터가 시도별로만 올라오기 때문에 "region\_code"마다 중복 복사가 됨
   * 대부분 연도별 1개 값이므로, 전월 급증/급락이 생기지 않도록 "forward-fill"

     ```python
     df_panel['GRDP'] = df_panel['GRDP'].fillna(method='ffill')
     ```

##### E-1-③. (선택) 인구증감 및 기타 변수

* 만약 "인구증감 데이터"를 외부에서 확보했다면,

  1. 컬럼명 통일(연-월 또는 연도 기준)
  2. 시·군·구 매핑
  3. 월별 복사(Forward-fill)
  4. `df_panel`에 merge

##### E-1-④. 세 번째 커밋

* **커밋 메시지 예시**:

  ```
  [STEP-E] 거시·지역 통제 변수(GRDP, 고용률 등) 전처리 및 패널 결합 완료
  ```

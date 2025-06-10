
### 단계 B. 공급 데이터 전처리

#### B-1. 대상 파일

* `미분양주택현황보고서_시·군·구별 미분양현황 (00~04).csv`
* `미분양주택현황보고서_시·군·구별 미분양현황 (05~08).csv`
* `미분양주택현황보고서_시·군·구별 미분양현황 (09~12).csv`
* `미분양주택현황보고서_시·군·구별 미분양현황 (13~16).csv`
* `미분양주택현황보고서_시·군·구별 미분양현황 (17~20).csv`
* `미분양주택현황보고서_시·군·구별 미분양현황 (21~24).csv`
* `한국부동산원_주택공급정보_입주예정물량정보_20241231.csv`
* `시도별 건축공허율.csv`
* `전국 연도별 착공 현황.xlsx`

> **목표**:
> "시·군·구 × 연도(혹은 연-분기)" 단위로 제공되는 **미분양 물량, 입주예정 물량, 건축공허율, 착공 건수** 등을 → "시·군·구 × 월" 패널로 맞춰 넣을 수 있는 형태로 전처리

##### B-1-①. 미분양 CSV 파일 통합 로딩

1. **각 분기별 CSV 결합**

   * 파일명에 포함된 연도 구간(예: `00~04` → 2000–2004년) 확인
   * 공통 컬럼명: `지역코드`, `시점(YYYYMM)`, `미분양 세대수`, `미분양률(%)` 등
   * 로딩 시 반드시 `encoding='cp949'` 확인
   * 예시:

     ```python
     import glob
     supply_files = glob.glob('미분양주택현황보고서_시·군·구별 미분양현황*.csv')
     df_unsold_list = []
     for f in supply_files:
         df_tmp = pd.read_csv(f, encoding='cp949')
         df_tmp = df_tmp.rename(columns={'시점':'year_month', '지역코드':'region_code', '미분양세대수':'unsold_count', '미분양률':'unsold_rate'})
         df_tmp['year_month'] = pd.to_datetime(df_tmp['year_month'], format='%Y%m')
         df_unsold_list.append(df_tmp[['region_code','year_month','unsold_count','unsold_rate']])
     df_unsold = pd.concat(df_unsold_list, axis=0).reset_index(drop=True)
     ```
2. **결합 후 이상치/결측 처리**

   * 연속된 월 단위가 아닐 경우, 예컨대 연-분기(YYYY03, YYYY06, YYYY09, YYYY12)만 기록된 경우

     * **월단위 패널**에 넣기 위해,

       * "YYYY03(3월) → 3월 값 그대로"
       * "YYYY04,05에는 NA"로 두고 → 결측 상태 유지
       * 혹은 "직전 분기의 값을 해당 분기 첫월(예: 3월)부터 다음 분기 전월(예: 5월)까지 복사"

         ```python
         df_unsold = df_unsold.set_index(['region_code','year_month']).unstack().resample('MS').ffill().stack().reset_index()
         ```
   * 합치는 과정에서 `region_code` 누락이 있으면, "시·군·구명" 기준으로 코드 부여

##### B-1-②. "입주예정물량" CSV 로딩

1. **파일 로딩 및 컬럼명 통일**

   ```python
   df_future = pd.read_csv('한국부동산원_주택공급정보_입주예정물량정보_20241231.csv', encoding='utf-8')
   df_future = df_future.rename(columns={'지역코드':'region_code','입주예정월':'planned_movein_month','예정물량':'future_supply'})
   df_future['planned_movein_month'] = pd.to_datetime(df_future['planned_movein_month'], format='%Y-%m')
   ```
2. **Monthly Panel 매핑**

   * `df_panel`과 동일한 "region\_code × year\_month" 인덱스에 `future_supply`를 `left merge`
   * 만약 "입주예정월"이 YYYY-MM 형태로 모든 월에 분산돼 있지 않고, 예: 분기 단위로만 기록되어 있으면,

     * "해당 분기 시작월(예: 2024-01)부터 3개월 동안 동일값 복사" 방식 적용

##### B-1-③. 건축공허율 & 착공 현황 로딩

1. **`시도별 건축공허율.csv`**

   * 컬럼 예시: `['시도코드','시도명','연도','건축공허율(%)']`
   * "시·도 단위" → "시·군·구 패널"로 넘어갈 때,

     * 각 시·도별 건축공허율을 해당 시·군·구 모든 행(월)으로 복사

     ```python
     df_void = pd.read_csv('시도별 건축공허율.csv', encoding='cp949')
     df_void['연도'] = df_void['연도'].astype(int)
     # 월 단위 패널에 합치기 위해, 연도 → 월 첫날 포맷으로 변경
     df_void['year_month'] = pd.to_datetime(df_void['연도'].astype(str) + '-01', format='%Y-%m')
     # 시·도 코드와 시·군·구 코드를 매핑하는 매핑 테이블(별도 생성 필요) 사용
     df_mapping = pd.read_csv('시도_시군구_매핑표.csv')  # 예시
     df_void = df_void.merge(df_mapping, on=['시도코드'], how='left')  # 시·군·구 코드 부여
     # 이후 df_panel에 merge
     ```
2. **`전국 연도별 착공 현황.xlsx`**

   * 시트 내부 구조:

     ```
     ['시도명','연도','착공면적(㎡)','착공호수','착공건수'] 등
     ```
   * 연도 단위 → "시·군·구 × 월" 패널에 넣을 때,

     * "연도별 착공건수" 컬럼을 해당 연도의 모든 월에 동일하게 복사

     ```python
     df_start = pd.read_excel('전국 연도별 착공 현황.xlsx', engine='openpyxl')
     df_start = df_start.rename(columns={'시도명':'sido_name','연도':'year','착공건수':'start_construction'})
     df_start['year_month'] = pd.to_datetime(df_start['year'].astype(str) + '-01', format='%Y-%m')
     # 시·도→시·군·구 매핑 테이블 활용
     df_start = df_start.merge(df_mapping[['시도명','region_code']], left_on='sido_name', right_on='시도명', how='left')
     # df_panel merge
     ```

##### B-1-④. "미분양" → `df_panel`에 결합

* `df_panel = df_panel.merge(df_unsold[['region_code','year_month','unsold_count','unsold_rate']], on=['region_code','year_month'], how='left')`

##### B-1-⑤. "입주예정물량" → `df_panel`에 결합

* `df_panel = df_panel.merge(df_future[['region_code','planned_movein_month','future_supply']], left_on=['region_code','year_month'], right_on=['region_code','planned_movein_month'], how='left')`

  * merge 후 `planned_movein_month` 컬럼 삭제

##### B-1-⑥. "건축공허율" → `df_panel`에 결합

* `df_panel = df_panel.merge(df_void[['region_code','year_month','건축공허율(%)']], on=['region_code','year_month'], how='left')`

##### B-1-⑦. "착공 현황" → `df_panel`에 결합

* `df_panel = df_panel.merge(df_start[['region_code','year_month','start_construction']], on=['region_code','year_month'], how='left')`

##### B-1-⑧. 공통 결측치 & 이상치 체크

1. 결합 이후, `unsold_count`, `future_supply`, `건축공허율(%)`, `start_construction` 등에 결측이 많을 수 있음

   * **행 그대로 두기** vs **0으로 채워 넣기** vs **인근 시·군·구 평균값으로 대체**
   * **초기 단계**에서는 결측을 그대로 두고 모델링 때 "결측 더미 변수"를 활용하거나 결측 행을 제거하는 전략을 세울 수 있음
2. `unsold_count`가 0 혹은 음수로 들어온 경우 → 0으로 고정

   * `df_panel['unsold_count'] = df_panel['unsold_count'].clip(lower=0)`

##### B-1-⑨. 두 번째 커밋

* **커밋 메시지 예시**:

  ```
  [STEP-B] 공급(미분양, 입주예정, 건축공허율, 착공) 데이터 전처리 및 패널 결합 완료
  ```

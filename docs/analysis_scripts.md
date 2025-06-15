# Preprocessing Scripts Documentation

본 문서는 `/preprocessing` 디렉토리에 위치한 데이터 전처리 스크립트들에 대한 상세한 설명을 제공합니다. 이 스크립트들은 부동산 데이터 분석을 위한 원시 데이터 전처리 파이프라인을 구성합니다.

## 📁 파일 개요

| 파일명 | 목적 | 입력 데이터 | 출력 파일 |
|--------|------|-------------|-----------|
| `아파트거래1.py` | 아파트 거래현황 추출 | 월별 행정구역별 아파트거래현황 | `추출된_아파트거래현황_2013-2024.csv` |
| `아파트거래2.py` | 신도시 아파트매매 추출 | 월별 행정구역별 아파트매매거래현황 | `신도시 지역 아파트매매거래현황.csv` |
| `월_매매.py` | 월별 매매가격지수 추출 | 월별 매매가격지수_아파트 | `d.csv` |
| `주_매매.py` | 주별 매매가격지수 추출 | 주별 매매가격지수 | `주별_매매가_추출.csv` |
| `청약.py` | 청약 경쟁률 데이터 처리 | 지역별 청약 경쟁률 정보 | `한국부동산원_지역별 청약 경쟁률 정보_분리된날짜.csv` |
| `고용.py` | 특정지역 고용 데이터 추출 | 시군구 연령별 취업자 및 고용률 | `특정지역_취업자_고용률.csv` |
| `미분양1.py` | 미분양 주택현황 정리 | 미분양주택현황 | `미분양주택현황_정리_2013_2024.csv` |
| `미분양2.py` | 미분양 데이터 기간 추출 | 미분양주택현황 | `미분양주택현황_2013_2024.csv` |
| `지역내총생산.py` | 지역내총생산 데이터 추출 | 시도별 지역내총생산 | `지역내총생산_시장가격_2013년이후.csv` |

---

## 🔧 상세 스크립트 분석

### 1. `아파트거래1.py` - 아파트 거래현황 데이터 추출

**목적**: 2013년 1월부터 2024년 12월까지의 아파트 거래현황에서 동(호)수 데이터만 추출

**주요 로직**:
```python
def extract_apartment_data(input_file, output_file):
    # 다양한 인코딩으로 파일 읽기 시도
    encodings = ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']
    
    # 2013년 1월과 2024년 12월 컬럼 위치 찾기
    for i, col_name in enumerate(header_row):
        if '2013' in col_str and '1' in col_str:
            start_col_idx = i
        if '2024' in col_str and '12' in col_str:
            end_col_idx = i
    
    # 2번 행에서 '동(호)수' 패턴을 가진 컬럼들 찾기
    for col_idx in range(start_col_idx, end_col_idx + 1):
        cell_str = str(cell_value)
        if '동' in cell_str and ('호' in cell_str or '수' in cell_str):
            dong_ho_cols.append(col_idx)
    
    # A, B, C, D열 + 동(호)수 컬럼들 선택
    final_cols = [0, 1, 2, 3] + dong_ho_cols
    extracted_df = df.iloc[:, final_cols].copy()
```

**핵심 기능**:
- 다중 인코딩 지원 (cp949, euc-kr, utf-8, utf-8-sig)
- 동적 컬럼 위치 감지 (2013년 1월 ~ 2024년 12월)
- '동(호)수' 패턴 매칭을 통한 선택적 컬럼 추출
- 숫자 데이터 정리 (따옴표 제거, 천단위 구분자 처리)
- 헤더 3행 보존, 4행부터 숫자 변환

**출력**: 11행 × 148열 (기본 4열 + 144개월 동(호)수 데이터)

---

### 2. `아파트거래2.py` - 신도시 아파트매매거래 데이터 추출

**목적**: 신도시 지역의 아파트매매거래현황에서 2013-2024년 동(호)수 데이터 추출

**주요 로직**:
```python
def extract_apartment_trade_data(input_file, output_file):
    # 1행 헤더에서 정확한 날짜 컬럼 찾기
    for i, col_name in enumerate(header_row):
        if str(col_name).strip() == '2013년 1월':
            start_col_idx = i
        if str(col_name).strip() == '2024년 12월':
            end_col_idx = i
    
    # 수동 컬럼 인덱스 설정 (분석 결과 기반)
    if start_col_idx is None or end_col_idx is None:
        start_col_idx = 172  # 2013년 1월
        end_col_idx = 459    # 2024년 12월
```

**핵심 기능**:
- 정확한 날짜 컬럼명 매칭
- 수동 인덱스 백업 시스템
- 신도시 지역 특화 데이터 처리
- 동일한 숫자 데이터 정리 로직

**출력**: 신도시 지역 아파트매매거래현황 (9.4KB)

---

### 3. `월_매매.py` - 월별 매매가격지수 데이터 추출

**목적**: 2013년 1월부터 2024년 12월까지 144개월간의 원자료 매매가격지수만 추출

**주요 로직**:
```python
def filter_monthly_apartment_price_data(input_file, output_file):
    # 2013년 1월 인덱스 계산
    start_index = 5  # 기본 컬럼 5개
    start_index += 2 * 2  # 2003년 11-12월 (2개월 * 2컬럼)
    start_index += 9 * 12 * 2  # 2004-2012년 (9년 * 12개월 * 2컬럼)
    # start_index = 225 (2013년 1월 원자료)
    
    # 원자료 컬럼들만 선택 (홀수 인덱스에서 시작하여 2씩 증가)
    for i in range(start_index, end_index + 1, 2):
        if i < len(columns):
            selected_columns.append(columns[i])
```

**핵심 기능**:
- 정확한 컬럼 인덱스 계산 (2003년 11월부터 시작하는 구조 분석)
- 원자료와 전기대비증감률 중 원자료만 선택
- 144개월 데이터 완전성 검증
- 연도별 월 수 분석

**출력**: 232행 × 149열, 144개월 데이터 (220KB)

---

### 4. `주_매매.py` - 주별 매매가격지수 데이터 추출

**목적**: 2013-01-07부터 2024-12-30까지의 주별 원자료 매매가격지수 추출

**주요 로직**:
```python
def filter_housing_price_data(input_file, output_file):
    # 정확한 날짜 컬럼 찾기
    for i, col in enumerate(columns):
        if col == '2013-01-07':
            start_index = i
        if col == '2024-12-30':
            end_index = i
    
    # 원자료 컬럼들만 선택 (홀수 인덱스)
    for i in range(start_index, end_index + 1, 2):
        selected_columns.append(columns[i])
```

**핵심 기능**:
- 정확한 날짜 문자열 매칭
- 홀수 인덱스 원자료 선택
- 주별 데이터 연속성 보장

**출력**: 10행 × 1365열 (48KB)

---

### 5. `청약.py` - 청약 경쟁률 데이터 날짜 분리

**목적**: 연월 컬럼을 연도와 월로 분리하여 시계열 분석 준비

**주요 로직**:
```python
def parse_date(date_str):
    # 1. YYYY-MM 형식 (예: 2020-02)
    if re.match(r'^\d{4}-\d{2}$', date_str):
        year, month = date_str.split('-')
        return int(year), int(month)
    
    # 2. MMM-YY 형식 (예: Feb-23)
    elif re.match(r'^[A-Za-z]{3}-\d{2}$', date_str):
        month_map = {'Jan': 1, 'Feb': 2, ...}
        month = month_map.get(month_str.capitalize())
        year = int('20' + year_str) if int(year_str) < 50 else int('19' + year_str)
```

**핵심 기능**:
- 다양한 날짜 형식 파싱 (YYYY-MM, MMM-YY, MM-YYYY)
- 2자리 연도를 4자리로 변환
- 연도, 월 컬럼을 앞쪽으로 재배치

**출력**: 연도, 월이 분리된 청약 경쟁률 데이터 (31KB)

---

### 6. `고용.py` - 특정지역 고용 데이터 추출

**목적**: 서울 송파구, 하남시, 성남시, 김포시, 고양시의 취업자 및 고용률 데이터 추출

**주요 로직**:
```python
def extract_specific_regions_employment_data(input_file, output_file, target_regions):
    # 목표 지역들과 매칭되는 행 찾기
    target_regions_variations = []
    for target in target_regions:
        if target == '서울 송파구':
            target_regions_variations.extend(['송파구', '서울송파구', '서울특별시 송파구'])
        elif target == '하남시':
            target_regions_variations.extend(['경기 하남시', '경기도 하남시'])
    
    # 정확히 일치 + 부분 일치 검색
    for target_variation in target_regions_variations:
        exact_match = df[df[region_column] == target_variation]
        partial_match = df[df[region_column].str.contains(target_variation, na=False)]
```

**핵심 기능**:
- 지역명 변형 패턴 지원 (서울 송파구 → 송파구, 서울송파구 등)
- 정확 매칭과 부분 매칭 조합
- 지역별 데이터 행 수 분석
- 연령 그룹 및 항목별 필터링 지원

**출력**: 5개 지역, 70행 총 데이터 (10KB)

---

### 7. `미분양1.py` - 미분양 주택현황 데이터 정리

**목적**: 2013년 1월부터 2024년 12월까지의 미분양 주택현황 데이터 추출 및 정리

**주요 로직**:
```python
def process_unsold_housing_data(input_file, output_file):
    # 다양한 인코딩 시도
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
    
    # 2013년 1월과 2024년 12월 컬럼 찾기
    for i, col in enumerate(columns):
        if '2013년 1월' in str(col) or ('2013' in str(col) and '1월' in str(col)):
            start_2013_index = i
        if '2024년 12월' in str(col) or ('2024' in str(col) and '12월' in str(col)):
            end_2024_index = i
    
    # 데이터가 역시간순이므로 end_2024_index부터 start_2013_index까지
    selected_columns = base_columns + columns[end_2024_index:start_2013_index + 1]
    
    # 시간순으로 정렬 (역순을 정순으로)
    date_columns_reversed = date_columns[::-1]
```

**핵심 기능**:
- 강력한 다중 인코딩 지원
- 역시간순 데이터를 정시간순으로 재정렬
- 따옴표 및 천단위 구분자 정리
- 데이터 타입 변환 (문자열 → 정수)
- 행별 데이터 요약 분석

**출력**: 7행 × 147열 (4.8KB)

---

### 8. `미분양2.py` - 미분양 데이터 기간별 추출

**목적**: 2013년부터 2024년까지의 미분양 데이터만 간단 추출

**주요 로직**:
```python
def extract_2013_2024_data():
    # 2013년부터 2024년까지의 컬럼 찾기
    target_columns = []
    for col in df.columns:
        if any(year in str(col) for year in ['2013', '2014', '2015', '2016', '2017', '2018', 
                                            '2019', '2020', '2021', '2022', '2023', '2024']):
            target_columns.append(col)
    
    # 시간순으로 컬럼 정렬 (현재 역순이므로 뒤집기)
    date_columns_sorted = target_columns[::-1]
    final_columns = basic_columns + date_columns_sorted
```

**핵심 기능**:
- 연도 기반 컬럼 필터링
- 시간순 정렬
- 지역별 요약 정보 제공

**출력**: 미분양주택현황 2013-2024년 데이터 (7.5KB)

---

### 9. `지역내총생산.py` - 지역내총생산 데이터 추출

**목적**: 2013년 이후 지역내총생산(시장가격) 데이터만 추출

**주요 로직**:
```python
def extract_gdp_from_2013():
    # 2013년부터의 연도 컬럼 찾기
    year_columns = []
    for col in df.columns:
        if any(year in str(col) for year in ['2013', '2014', '2015', '2016', '2017', '2018', 
                                            '2019', '2020', '2021', '2022', '2023']):
            year_columns.append(col)
    
    # '경제활동별'이 '지역내총생산(시장가격)'인 행만 필터링
    df_extracted = df_extracted[df_extracted['경제활동별'] == '지역내총생산(시장가격)'].copy()
```

**핵심 기능**:
- 특정 경제활동별 필터링
- 연도별 컬럼 선택
- 18개 지역 데이터 추출

**출력**: 18개 지역의 지역내총생산 데이터 (8.6KB)

---

## 📊 데이터 처리 공통 패턴

### 1. 인코딩 처리
모든 스크립트는 다음과 같은 강건한 인코딩 처리를 구현:
```python
encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
for encoding in encodings:
    try:
        df = pd.read_csv(input_file, encoding=encoding)
        break
    except Exception:
        continue
```

### 2. 데이터 정리
- 따옴표 제거: `"""`, `""`, `"`, `'`
- 천단위 구분자 제거: `,`
- 결측값 처리: `''`, `'nan'`, `'None'`, `'null'` → `0`
- 데이터 타입 변환: `pd.to_numeric()` → `astype(int)`

### 3. 시간 데이터 처리
- 2013년 1월 ~ 2024년 12월 (144개월) 표준화
- 역시간순 → 정시간순 변환
- 컬럼 인덱스 동적 감지

### 4. 결과 저장
- 기본: UTF-8-sig 인코딩
- 백업: cp949 인코딩
- 결과 디렉토리: `result/`

---

## 🎯 실행 결과 요약

| 스크립트 | 성공률 | 출력 파일 크기 | 주요 특징 |
|----------|--------|----------------|-----------|
| 아파트거래1.py | ✅ 100% | 10KB | 11행 × 148열, 동(호)수 데이터 |
| 아파트거래2.py | ✅ 100% | 9.4KB | 신도시 지역 특화 |
| 월_매매.py | ✅ 100% | 220KB | 232행 × 149열, 144개월 |
| 주_매매.py | ✅ 100% | 48KB | 10행 × 1365열, 주별 데이터 |
| 청약.py | ✅ 100% | 31KB | 날짜 분리 처리 |
| 고용.py | ✅ 100% | 10KB | 5개 지역, 70행 |
| 미분양1.py | ✅ 100% | 4.8KB | 7행 × 147열 |
| 미분양2.py | ✅ 100% | 7.5KB | 간단 추출 |
| 지역내총생산.py | ✅ 100% | 8.6KB | 18개 지역 |

**총 결과**: 9개 스크립트 모두 성공, 총 349KB 데이터 생성

---

## 🔍 품질 보증

### 1. 데이터 무결성
- 모든 스크립트는 원본 데이터 구조 보존
- 헤더 정보 유지
- 시계열 연속성 보장

### 2. 오류 처리
- 다중 인코딩 지원
- 파일 경로 자동 수정
- 백업 저장 방식

### 3. 검증 기능
- 데이터 크기 확인
- 컬럼 수 검증
- 시간 범위 확인
- 결과 미리보기
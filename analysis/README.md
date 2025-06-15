# Real Estate Data Clustering Analysis

이 디렉토리는 부동산 데이터에 대한 클러스터링 분석을 수행하는 Python 스크립트들을 포함합니다.

## 📁 파일 구조

```
analysis/
├── simple_clustering.py          # 기본 클러스터링 분석
├── clustering_analysis.py        # 상세 클러스터링 분석
├── result/                       # 분석 결과 저장 디렉토리
│   ├── *.png                    # 시각화 결과
│   └── *.csv                    # 데이터 결과
└── README.md                    # 이 파일
```

## 🚀 실행 방법

### 1. 기본 클러스터링 분석
```bash
cd analysis
python simple_clustering.py
```

### 2. 상세 클러스터링 분석
```bash
cd analysis
python clustering_analysis.py
```

## 📊 분석 내용

### 데이터 소스
- **청약 경쟁률 데이터**: `../preprocessing/result/한국부동산원_지역별 청약 경쟁률 정보_분리된날짜.csv`
- **GDP 데이터**: `../preprocessing/result/지역내총생산_시장가격_2013년이후.csv`

### 분석 특징
- **특별공급 경쟁률**: 지역별 평균 특별공급 경쟁률
- **일반공급 경쟁률**: 지역별 평균 일반공급 경쟁률  
- **특별공급 총세대수**: 지역별 특별공급 총 공급세대수
- **일반공급 총세대수**: 지역별 일반공급 총 공급세대수
- **GDP 평균**: 2021-2023년 3개년 평균 지역내총생산

### 클러스터링 방법
- **K-means 클러스터링** (k=3,4,5)
- **계층적 클러스터링** (k=3,4)
- **평가 지표**: Silhouette Score, Calinski-Harabasz Index

## 📈 결과 파일

### 시각화 결과
- `clustering_analysis_results.png`: 기본 클러스터링 결과 (4개 차트)
- `detailed_cluster_analysis.png`: 상세 클러스터 특성 분석
- `comprehensive_clustering_analysis.png`: 종합 클러스터링 분석 (6개 차트)
- `cluster_characteristics_heatmap.png`: 클러스터 특성 히트맵

### 데이터 결과
- `clustering_results.csv`: 기본 클러스터링 결과
- `clustering_results_detailed.csv`: 상세 클러스터링 결과
- `cluster_summary.csv`: 클러스터별 평균 특성
- `cluster_detailed_summary.csv`: 클러스터별 상세 통계 (평균, 표준편차, 최소값, 최대값)
- `cluster_normalized_means.csv`: 정규화된 클러스터 평균값
- `region_cluster_mapping.csv`: 지역-클러스터 매핑 테이블

## 🎯 주요 분석 결과

### 최적 클러스터링: K-means (k=3)
- **Silhouette Score**: 0.713 (높은 클러스터 품질)

### 클러스터 구성
1. **Cluster 0 (지방 시장)**: 14개 지역
   - 강원, 경남, 경북, 광주, 대구, 대전, 부산, 울산, 인천, 전남, 전북, 제주, 충남, 충북
   - 특성: 낮은 GDP, 낮은 경쟁률

2. **Cluster 1 (프리미엄 시장)**: 2개 지역  
   - 서울, 세종
   - 특성: 높은 GDP, 높은 경쟁률

3. **Cluster 2 (안정적 프리미엄 시장)**: 1개 지역
   - 경기
   - 특성: 높은 GDP, 낮은 경쟁률

## 🔧 기술적 세부사항

### 데이터 전처리
- 특수문자 제거 (예: "(△151)" → "0")
- 지역명 영어 매핑 (한글 폰트 문제 해결)
- 결측치 중앙값으로 대체
- StandardScaler를 이용한 데이터 표준화

### 시각화 특징
- 영어 폰트 사용 (DejaVu Sans)
- PCA를 이용한 2차원 시각화
- 다양한 차트 유형 (산점도, 막대차트, 파이차트, 히트맵)

## 📋 요구사항

### Python 패키지
```
pandas
numpy
matplotlib
seaborn
scikit-learn
```

### 실행 환경
- Python 3.7+
- 전처리된 데이터 파일 필요 (`../preprocessing/result/` 디렉토리)

## 📝 참고사항

- 모든 결과는 `result/` 디렉토리에 자동 저장됩니다
- 스크립트 실행 시 기존 결과 파일들이 덮어쓰여집니다
- 분석 과정과 결과가 콘솔에 상세히 출력됩니다 
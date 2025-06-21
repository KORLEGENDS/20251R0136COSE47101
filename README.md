# 🏢 수도권 신도시 주택가격 예측 모델 및 정책효과 분석

> **K-means 클러스터링과 헤도닉 가격모델을 활용한 1·2·3기 신도시 가격 동학 분석**

## 📋 프로젝트 개요

본 프로젝트는 한국의 1·2기 신도시 실거래 데이터와 공급·입주, 청약경쟁률, 거시경제·정책 변수, 교통 이벤트 등 5개 계층의 데이터를 통합하여 신도시 주택가격의 동학을 분석하고, 3기 신도시의 가격을 예측하는 데이터 과학 프로젝트입니다.

### 🎯 주요 목표

1. **지역별 주택시장 세분화**: K-means 클러스터링을 통한 17개 시도 주택시장의 체계적 분류
2. **가격 예측 모델 구축**: Hedonic OLS와 머신러닝 모델을 활용한 정확한 가격 예측
3. **정책 효과 분석**: GTX, 금리, LTV 등 정책 변수의 충격 식별 및 계량화
4. **3기 신도시 가격 예측**: 1·2기 신도시 데이터 기반 3기 신도시 가격 밴드 시뮬레이션

### 🔬 핵심 방법론

- **K-means 클러스터링**: 특별공급 경쟁률, 일반공급 경쟁률, 지역 GDP를 활용한 시장 세분화
- **Hedonic Price Model**: HC3 표준오차를 적용한 강건한 가격 회귀분석
- **Event Study**: τ-스케일 기반 Launch Trajectory 분석
- **Difference-in-Differences**: 정책 충격의 인과효과 추정

## 📁 디렉토리 구조

```
20251R0136COSE47101/
│
├── 📊 data/                    # 원시 데이터 저장소
│   ├── 실거래가 데이터
│   ├── 청약경쟁률 데이터
│   └── 거시경제 지표
│
├── 🔧 preprocessing/           # 데이터 전처리 스크립트
│   ├── 아파트거래1.py         # 실거래가 전처리
│   ├── 아파트거래2.py         # 실거래가 추가 처리
│   ├── 청약.py               # 청약경쟁률 전처리
│   ├── 고용.py               # 고용 데이터 전처리
│   ├── 미분양1.py, 미분양2.py # 미분양 데이터 처리
│   ├── 지역내총생산.py        # 지역 GDP 전처리
│   ├── 주_매매.py, 월_매매.py # 주간/월간 매매 데이터
│   └── result/               # 전처리 결과 저장
│
├── 📈 analysis/               # 분석 스크립트
│   ├── clustering_analysis.py # K-means 클러스터링 분석
│   ├── simple_clustering.py   # 간단한 클러스터링 테스트
│   └── result/               # 분석 결과 저장
│
├── 🚀 script/                 # 메인 파이프라인 스크립트
│   ├── 00_load_data.py       # 데이터 로드
│   ├── 01_clean_merge.py     # 데이터 정제 및 병합
│   ├── 02_feature_engineer.py # 피처 엔지니어링
│   ├── 03_build_panel.py     # 패널 데이터 구축
│   ├── 04_eda_qc.py          # 탐색적 데이터 분석
│   ├── 05_prepare_model.py   # 모델 준비
│   ├── 06_transform_dist.py  # 분포 변환 (Box-Cox, Yeo-Johnson)
│   ├── 07_train_models.py    # 모델 학습
│   ├── 08_event_study.py     # 이벤트 스터디
│   ├── 09_predict_3rd.py     # 3기 신도시 예측
│   └── 10_residual_analysis.py # 잔차 분석
│
├── 📄 report/                 # 프로젝트 보고서
│   ├── 서론.md               # 연구 배경 및 목적
│   ├── 데이터셋.md           # 데이터 설명
│   ├── 전처리.md             # 전처리 과정 상세
│   ├── 방법론.md             # 분석 방법론
│   ├── 평가.md               # 모델 평가
│   ├── 결론.md               # 연구 결론
│   ├── 참고자료.md           # 참고문헌 및 데이터 출처
│   └── figure/               # 시각화 자료
│
├── 💾 output/                 # 최종 결과물
│   ├── panel_model_transformed.parquet
│   └── 기타 분석 결과
│
├── 📑 docs/                   # 추가 문서
├── 🎤 presentation/           # 발표 자료
├── 🐍 venv/                   # Python 가상환경
├── requirements.txt           # Python 패키지 의존성
└── README.md                  # 프로젝트 문서 (현재 파일)
```

## 🔍 주요 분석 결과

### 1. K-means 클러스터링을 통한 시장 세분화
![클러스터링 결과](https://github.com/KORLEGENDS/20251R0136COSE47101/blob/main/report/figure/comprehensive_clustering_analysis.png)

전국 17개 시도를 3개의 클러스터로 분류 (Silhouette Score: 0.713):

- **클러스터 0 (일반 지역시장)**: 14개 지역
  - 특별공급 경쟁률: 1.42배
  - 일반공급 경쟁률: 14.52배
  - 평균 GDP: 852억원

- **클러스터 1 (초과수요 시장)**: 서울, 세종
  - 특별공급 경쟁률: 59.12배
  - 일반공급 경쟁률: 203.12배
  - 평균 GDP: 2,720억원

- **클러스터 2 (경기 독립시장)**: 경기도
  - 특별공급 경쟁률: 5.11배
  - 일반공급 경쟁률: 20.6배
  - 평균 GDP: 5,814억원

### 2. 패널 데이터 구축

- **규모**: 61,138행 × 679개 변수
- **구조**: complex_id × year_month 복합 키
- **변환**: Box-Cox/Yeo-Johnson 변환으로 정규성 확보

### 3. 모델 성능

- **Hedonic OLS (HC3)**: R² ≈ 0.78, MAPE ≈ 6.9%
- **5-fold 교차검증**: 안정적인 예측 성능 확인

## 🛠️ 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 전처리

```bash
# 전처리 스크립트 실행
cd preprocessing
python 아파트거래1.py
python 아파트거래2.py
python 청약.py
# ... 기타 전처리 스크립트
```

### 3. 메인 파이프라인 실행

```bash
cd script
# 순차적으로 실행
python 00_load_data.py
python 01_clean_merge.py
python 02_feature_engineer.py
python 03_build_panel.py
python 04_eda_qc.py
python 05_prepare_model.py
python 06_transform_dist.py
python 07_train_models.py
python 08_event_study.py
python 09_predict_3rd.py
python 10_residual_analysis.py
```

### 4. 클러스터링 분석

```bash
cd analysis
python clustering_analysis.py
```

## 📊 주요 데이터 출처

- **국토교통부 실거래가 공개시스템**: 아파트 실거래 데이터
- **한국부동산원**: 청약경쟁률, 미분양 현황
- **통계청 KOSIS**: 지역내총생산, 고용 데이터
- **한국은행 ECOS**: 금리, 통화량 등 거시경제 지표

## 🔬 기술 스택

- **언어**: Python 3.8+
- **데이터 처리**: pandas, numpy, pyarrow
- **시각화**: matplotlib, seaborn, geopandas
- **통계/ML**: statsmodels, scikit-learn
- **웹 스크래핑**: requests, beautifulsoup4

## 📈 향후 계획

1. **ML 모델 확장**: XGBoost, LightGBM, LSTM 등 고급 모델 적용
2. **다층 DiD 분석**: 정책 효과의 정밀한 인과추론
3. **실시간 예측 시스템**: API 기반 실시간 가격 예측 서비스
4. **대시보드 개발**: 인터랙티브 시각화 대시보드 구축

## 👥 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 공개되었습니다. 상업적 사용 시 별도 문의 바랍니다.

## 📞 연락처

프로젝트 관련 문의사항은 Issue를 통해 남겨주시기 바랍니다.

---

**Note**: 본 프로젝트는 2025년 고려대학교 데이터 과학 과정의 일환으로 진행되었습니다.

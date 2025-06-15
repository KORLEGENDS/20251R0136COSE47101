import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.manifold import TSNE
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class RealEstateClusteringAnalysis:
    def __init__(self):
        """
        부동산 데이터 클러스터링 분석 클래스
        """
        self.data_dict = {}
        self.processed_data = None
        self.scaler = None
        self.cluster_results = {}
        
    def load_data(self):
        """
        전처리된 데이터 파일들을 로드
        """
        print("데이터 로딩 중...")
        
        # 1. 청약 경쟁률 데이터
        try:
            competition_data = pd.read_csv('preprocessing/result/한국부동산원_지역별 청약 경쟁률 정보_분리된날짜.csv')
            self.data_dict['competition'] = competition_data
            print(f"청약 경쟁률 데이터: {competition_data.shape}")
        except Exception as e:
            print(f"청약 경쟁률 데이터 로딩 실패: {e}")
            
        # 2. 지역내총생산 데이터
        try:
            gdp_data = pd.read_csv('preprocessing/result/지역내총생산_시장가격_2013년이후.csv')
            self.data_dict['gdp'] = gdp_data
            print(f"지역내총생산 데이터: {gdp_data.shape}")
        except Exception as e:
            print(f"지역내총생산 데이터 로딩 실패: {e}")
            
        # 3. 미분양주택현황 데이터
        try:
            unsold_data = pd.read_csv('preprocessing/result/미분양주택현황_정리_2013_2024.csv')
            self.data_dict['unsold'] = unsold_data
            print(f"미분양주택현황 데이터: {unsold_data.shape}")
        except Exception as e:
            print(f"미분양주택현황 데이터 로딩 실패: {e}")
            
        # 4. 취업자 고용률 데이터
        try:
            employment_data = pd.read_csv('preprocessing/result/특정지역_취업자_고용률.csv')
            self.data_dict['employment'] = employment_data
            print(f"취업자 고용률 데이터: {employment_data.shape}")
        except Exception as e:
            print(f"취업자 고용률 데이터 로딩 실패: {e}")
            
        # 5. 아파트 거래 데이터
        try:
            apt_data = pd.read_csv('preprocessing/result/추출된_아파트거래현황_2013-2024.csv')
            self.data_dict['apartment'] = apt_data
            print(f"아파트 거래 데이터: {apt_data.shape}")
        except Exception as e:
            print(f"아파트 거래 데이터 로딩 실패: {e}")
            
    def prepare_clustering_data(self):
        """
        클러스터링을 위한 데이터 전처리
        """
        print("\n클러스터링 데이터 준비 중...")
        
        # 청약 경쟁률 데이터 집계
        if 'competition' in self.data_dict:
            comp_data = self.data_dict['competition'].copy()
            
            # 지역별 평균 경쟁률 계산
            region_stats = comp_data.groupby('시도').agg({
                '특별공급 경쟁률': ['mean', 'std'],
                '일반공급 경쟁률': ['mean', 'std'],
                '특별공급 공급세대수': 'sum',
                '일반공급 공급세대수': 'sum'
            }).round(2)
            
            # 컬럼명 정리
            region_stats.columns = ['특별공급_경쟁률_평균', '특별공급_경쟁률_표준편차',
                                  '일반공급_경쟁률_평균', '일반공급_경쟁률_표준편차',
                                  '특별공급_총세대수', '일반공급_총세대수']
            
            region_stats = region_stats.reset_index()
            
        # GDP 데이터 처리
        if 'gdp' in self.data_dict:
            gdp_data = self.data_dict['gdp'].copy()
            
            # 명목 GDP만 추출하고 최근 3년 평균 계산
            gdp_nominal = gdp_data[gdp_data['항목'] == '명목'].copy()
            recent_years = ['2021 년', '2022 년', '2023 년']
            
            gdp_stats = gdp_nominal.groupby('시도별')[recent_years].mean().round(0)
            gdp_stats['GDP_평균'] = gdp_stats.mean(axis=1)
            gdp_stats = gdp_stats[['GDP_평균']].reset_index()
            gdp_stats.columns = ['시도', 'GDP_평균']
            
        # 데이터 병합
        if 'competition' in self.data_dict and 'gdp' in self.data_dict:
            merged_data = pd.merge(region_stats, gdp_stats, left_on='시도', right_on='시도', how='inner')
            
            # 수치형 컬럼만 선택
            numeric_cols = ['특별공급_경쟁률_평균', '일반공급_경쟁률_평균', 
                          '특별공급_총세대수', '일반공급_총세대수', 'GDP_평균']
            
            # 결측치 처리
            for col in numeric_cols:
                merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce')
                merged_data[col] = merged_data[col].fillna(merged_data[col].median())
            
            self.processed_data = merged_data
            print(f"병합된 데이터 형태: {merged_data.shape}")
            print(f"클러스터링 대상 지역: {list(merged_data['시도'])}")
            
        return self.processed_data
    
    def perform_clustering(self):
        """
        다양한 클러스터링 기법 적용
        """
        if self.processed_data is None:
            print("데이터가 준비되지 않았습니다.")
            return
            
        print("\n클러스터링 분석 수행 중...")
        
        # 클러스터링용 특징 데이터 준비
        feature_cols = ['특별공급_경쟁률_평균', '일반공급_경쟁률_평균', 
                       '특별공급_총세대수', '일반공급_총세대수', 'GDP_평균']
        
        X = self.processed_data[feature_cols].copy()
        
        # 데이터 표준화
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # 1. K-means 클러스터링 (k=3,4,5)
        for k in [3, 4, 5]:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            
            # 클러스터링 품질 지표 계산
            silhouette = silhouette_score(X_scaled, labels)
            calinski = calinski_harabasz_score(X_scaled, labels)
            davies_bouldin = davies_bouldin_score(X_scaled, labels)
            
            self.cluster_results[f'kmeans_k{k}'] = {
                'labels': labels,
                'silhouette': silhouette,
                'calinski_harabasz': calinski,
                'davies_bouldin': davies_bouldin,
                'model': kmeans
            }
            
            print(f"K-means (k={k}) - Silhouette: {silhouette:.3f}, "
                  f"Calinski-Harabasz: {calinski:.1f}, Davies-Bouldin: {davies_bouldin:.3f}")
        
        # 2. 계층적 클러스터링
        for k in [3, 4]:
            agg_clustering = AgglomerativeClustering(n_clusters=k, linkage='ward')
            labels = agg_clustering.fit_predict(X_scaled)
            
            silhouette = silhouette_score(X_scaled, labels)
            calinski = calinski_harabasz_score(X_scaled, labels)
            davies_bouldin = davies_bouldin_score(X_scaled, labels)
            
            self.cluster_results[f'hierarchical_k{k}'] = {
                'labels': labels,
                'silhouette': silhouette,
                'calinski_harabasz': calinski,
                'davies_bouldin': davies_bouldin,
                'model': agg_clustering
            }
            
            print(f"계층적 클러스터링 (k={k}) - Silhouette: {silhouette:.3f}, "
                  f"Calinski-Harabasz: {calinski:.1f}, Davies-Bouldin: {davies_bouldin:.3f}")
        
        # 3. DBSCAN
        for eps in [0.5, 1.0, 1.5]:
            dbscan = DBSCAN(eps=eps, min_samples=2)
            labels = dbscan.fit_predict(X_scaled)
            
            if len(set(labels)) > 1:  # 클러스터가 1개 이상인 경우만
                silhouette = silhouette_score(X_scaled, labels)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                self.cluster_results[f'dbscan_eps{eps}'] = {
                    'labels': labels,
                    'silhouette': silhouette,
                    'n_clusters': n_clusters,
                    'model': dbscan
                }
                
                print(f"DBSCAN (eps={eps}) - 클러스터 수: {n_clusters}, Silhouette: {silhouette:.3f}")
    
    def visualize_clusters(self):
        """
        클러스터링 결과 시각화
        """
        if not self.cluster_results:
            print("클러스터링 결과가 없습니다.")
            return
            
        print("\n클러스터링 결과 시각화 중...")
        
        # 특징 데이터 준비
        feature_cols = ['특별공급_경쟁률_평균', '일반공급_경쟁률_평균', 
                       '특별공급_총세대수', '일반공급_총세대수', 'GDP_평균']
        X = self.processed_data[feature_cols].copy()
        X_scaled = self.scaler.transform(X)
        
        # PCA로 2차원 축소
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # 최적 K-means 결과 선택 (Silhouette 점수 기준)
        best_kmeans = max([k for k in self.cluster_results.keys() if 'kmeans' in k], 
                         key=lambda x: self.cluster_results[x]['silhouette'])
        
        # 시각화
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Real Estate Data Clustering Analysis', fontsize=16, fontweight='bold')
        
        # 1. 최적 K-means 결과
        ax = axes[0, 0]
        labels = self.cluster_results[best_kmeans]['labels']
        scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis', alpha=0.7)
        ax.set_title(f'Best K-means Clustering\n(Silhouette: {self.cluster_results[best_kmeans]["silhouette"]:.3f})')
        ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
        ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
        
        # 지역명 표시
        for i, region in enumerate(self.processed_data['시도']):
            ax.annotate(region, (X_pca[i, 0], X_pca[i, 1]), 
                       xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 2. 계층적 클러스터링 결과
        ax = axes[0, 1]
        if 'hierarchical_k4' in self.cluster_results:
            labels = self.cluster_results['hierarchical_k4']['labels']
            scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='plasma', alpha=0.7)
            ax.set_title(f'Hierarchical Clustering (k=4)\n(Silhouette: {self.cluster_results["hierarchical_k4"]["silhouette"]:.3f})')
            ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
            ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
        
        # 3. 클러스터링 품질 지표 비교
        ax = axes[0, 2]
        methods = []
        silhouette_scores = []
        
        for method, result in self.cluster_results.items():
            if 'silhouette' in result:
                methods.append(method.replace('_', '\n'))
                silhouette_scores.append(result['silhouette'])
        
        bars = ax.bar(range(len(methods)), silhouette_scores, color='skyblue', alpha=0.7)
        ax.set_title('Silhouette Score Comparison')
        ax.set_ylabel('Silhouette Score')
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels(methods, rotation=45, ha='right')
        
        # 값 표시
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.3f}', ha='center', va='bottom')
        
        # 4. 특징별 클러스터 분포 (박스플롯)
        ax = axes[1, 0]
        cluster_data = self.processed_data.copy()
        cluster_data['cluster'] = self.cluster_results[best_kmeans]['labels']
        
        # GDP 평균 기준 박스플롯
        cluster_gdp = [cluster_data[cluster_data['cluster'] == i]['GDP_평균'].values 
                      for i in range(len(set(labels)))]
        
        box_plot = ax.boxplot(cluster_gdp, labels=[f'Cluster {i}' for i in range(len(cluster_gdp))])
        ax.set_title('GDP Distribution by Cluster')
        ax.set_ylabel('GDP Average (억원)')
        
        # 5. 경쟁률 분포
        ax = axes[1, 1]
        competition_data = [cluster_data[cluster_data['cluster'] == i]['일반공급_경쟁률_평균'].values 
                           for i in range(len(set(labels)))]
        
        box_plot = ax.boxplot(competition_data, labels=[f'Cluster {i}' for i in range(len(competition_data))])
        ax.set_title('Competition Rate Distribution by Cluster')
        ax.set_ylabel('Average Competition Rate')
        
        # 6. 클러스터별 지역 정보 테이블
        ax = axes[1, 2]
        ax.axis('off')
        
        # 클러스터별 지역 정리
        cluster_info = []
        for cluster_id in range(len(set(labels))):
            regions = cluster_data[cluster_data['cluster'] == cluster_id]['시도'].tolist()
            cluster_info.append(f"Cluster {cluster_id}: {', '.join(regions)}")
        
        table_text = '\n\n'.join(cluster_info)
        ax.text(0.1, 0.9, 'Cluster Composition:\n\n' + table_text, 
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('clustering_analysis_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 클러스터링 결과 요약 출력
        print("\n=== 클러스터링 분석 결과 요약 ===")
        print(f"최적 클러스터링 방법: {best_kmeans}")
        print(f"Silhouette Score: {self.cluster_results[best_kmeans]['silhouette']:.3f}")
        print(f"Calinski-Harabasz Index: {self.cluster_results[best_kmeans]['calinski_harabasz']:.1f}")
        print(f"Davies-Bouldin Index: {self.cluster_results[best_kmeans]['davies_bouldin']:.3f}")
        
        print("\n클러스터별 지역 구성:")
        for cluster_id in range(len(set(labels))):
            regions = cluster_data[cluster_data['cluster'] == cluster_id]['시도'].tolist()
            print(f"Cluster {cluster_id}: {', '.join(regions)}")
    
    def generate_cluster_statistics(self):
        """
        클러스터별 상세 통계 생성
        """
        if not self.cluster_results or self.processed_data is None:
            print("클러스터링 결과나 데이터가 없습니다.")
            return
            
        # 최적 클러스터링 결과 선택
        best_method = max(self.cluster_results.keys(), 
                         key=lambda x: self.cluster_results[x]['silhouette'])
        
        labels = self.cluster_results[best_method]['labels']
        
        # 클러스터별 통계 계산
        cluster_data = self.processed_data.copy()
        cluster_data['cluster'] = labels
        
        print(f"\n=== {best_method} 클러스터별 상세 통계 ===")
        
        feature_cols = ['특별공급_경쟁률_평균', '일반공급_경쟁률_평균', 
                       '특별공급_총세대수', '일반공급_총세대수', 'GDP_평균']
        
        for cluster_id in range(len(set(labels))):
            cluster_subset = cluster_data[cluster_data['cluster'] == cluster_id]
            
            print(f"\n--- Cluster {cluster_id} ---")
            print(f"지역: {', '.join(cluster_subset['시도'].tolist())}")
            print(f"지역 수: {len(cluster_subset)}")
            
            for col in feature_cols:
                mean_val = cluster_subset[col].mean()
                std_val = cluster_subset[col].std()
                print(f"{col}: {mean_val:.2f} (±{std_val:.2f})")
        
        # 클러스터 간 차이 분석
        print(f"\n=== 클러스터 간 특성 비교 ===")
        cluster_summary = cluster_data.groupby('cluster')[feature_cols].agg(['mean', 'std']).round(2)
        print(cluster_summary)
        
        return cluster_summary

def main():
    """
    메인 실행 함수
    """
    print("=== 부동산 데이터 클러스터링 분석 시작 ===")
    
    # 분석 객체 생성
    analyzer = RealEstateClusteringAnalysis()
    
    # 데이터 로딩
    analyzer.load_data()
    
    # 클러스터링 데이터 준비
    processed_data = analyzer.prepare_clustering_data()
    
    if processed_data is not None:
        # 클러스터링 수행
        analyzer.perform_clustering()
        
        # 결과 시각화
        analyzer.visualize_clusters()
        
        # 상세 통계 생성
        analyzer.generate_cluster_statistics()
        
        print("\n=== 분석 완료 ===")
        print("결과 이미지가 'clustering_analysis_results.png'로 저장되었습니다.")
    else:
        print("데이터 준비에 실패했습니다.")

if __name__ == "__main__":
    main() 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import warnings
import os
warnings.filterwarnings('ignore')

# Set English font
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def clean_numeric_data(series):
    """Clean numeric data containing strings"""
    # Convert strings to 0 (△ indicates negative or missing values)
    cleaned = series.astype(str).str.replace(r'\(.*\)', '0', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)

def create_region_mapping():
    """Create region name mapping dictionary"""
    return {
        '서울': 'Seoul',
        '부산': 'Busan', 
        '대구': 'Daegu',
        '인천': 'Incheon',
        '광주': 'Gwangju',
        '대전': 'Daejeon',
        '울산': 'Ulsan',
        '세종': 'Sejong',
        '경기': 'Gyeonggi',
        '강원': 'Gangwon',
        '충북': 'Chungbuk',
        '충남': 'Chungnam',
        '전북': 'Jeonbuk',
        '전남': 'Jeonnam',
        '경북': 'Gyeongbuk',
        '경남': 'Gyeongnam',
        '제주': 'Jeju'
    }

def create_gdp_mapping():
    """Create GDP region name mapping"""
    return {
        '서울특별시': 'Seoul',
        '부산광역시': 'Busan',
        '대구광역시': 'Daegu', 
        '인천광역시': 'Incheon',
        '광주광역시': 'Gwangju',
        '대전광역시': 'Daejeon',
        '울산광역시': 'Ulsan',
        '세종특별자치시': 'Sejong',
        '경기도': 'Gyeonggi',
        '강원특별자치도': 'Gangwon',
        '충청북도': 'Chungbuk',
        '충청남도': 'Chungnam',
        '전북특별자치도': 'Jeonbuk',
        '전라남도': 'Jeonnam',
        '경상북도': 'Gyeongbuk',
        '경상남도': 'Gyeongnam',
        '제주특별자치도': 'Jeju'
    }

def load_and_prepare_data():
    """Load and preprocess data"""
    print("Loading data...")
    
    # Load subscription competition data
    competition_data = pd.read_csv('../preprocessing/result/한국부동산원_지역별 청약 경쟁률 정보_분리된날짜.csv')
    print(f"Competition data: {competition_data.shape}")
    
    # Load GDP data
    gdp_data = pd.read_csv('../preprocessing/result/지역내총생산_시장가격_2013년이후.csv')
    print(f"GDP data: {gdp_data.shape}")
    
    # Region name mapping
    region_mapping = create_region_mapping()
    gdp_mapping = create_gdp_mapping()
    
    # Clean competition data
    competition_data['특별공급 경쟁률'] = clean_numeric_data(competition_data['특별공급 경쟁률'])
    competition_data['일반공급 경쟁률'] = clean_numeric_data(competition_data['일반공급 경쟁률'])
    competition_data['특별공급 공급세대수'] = clean_numeric_data(competition_data['특별공급 공급세대수'])
    competition_data['일반공급 공급세대수'] = clean_numeric_data(competition_data['일반공급 공급세대수'])
    
    # Aggregate by region
    region_stats = competition_data.groupby('시도').agg({
        '특별공급 경쟁률': 'mean',
        '일반공급 경쟁률': 'mean',
        '특별공급 공급세대수': 'sum',
        '일반공급 공급세대수': 'sum'
    }).round(2)
    
    region_stats.columns = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                           'Special_Supply_Total_Units', 'General_Supply_Total_Units']
    region_stats = region_stats.reset_index()
    
    # Apply region mapping
    region_stats['Region_EN'] = region_stats['시도'].map(region_mapping)
    
    # Process GDP data (nominal GDP, recent 3-year average)
    gdp_nominal = gdp_data[gdp_data['항목'] == '명목'].copy()
    # Exclude national data
    gdp_nominal = gdp_nominal[gdp_nominal['시도별'] != '전국']
    
    recent_years = ['2021 년', '2022 년', '2023 년']
    
    # Convert GDP data to numeric
    for year in recent_years:
        gdp_nominal[year] = pd.to_numeric(gdp_nominal[year], errors='coerce')
    
    gdp_stats = gdp_nominal.groupby('시도별')[recent_years].mean().round(0)
    gdp_stats['GDP_Average'] = gdp_stats.mean(axis=1)
    gdp_stats = gdp_stats[['GDP_Average']].reset_index()
    
    # Apply GDP region mapping
    gdp_stats['Region_EN'] = gdp_stats['시도별'].map(gdp_mapping)
    
    # Merge data
    merged_data = pd.merge(region_stats, gdp_stats[['Region_EN', 'GDP_Average']], on='Region_EN', how='inner')
    
    # Handle missing values
    numeric_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    for col in numeric_cols:
        merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce')
        merged_data[col] = merged_data[col].fillna(merged_data[col].median())
    
    print(f"Final data shape: {merged_data.shape}")
    print(f"Analysis target regions: {list(merged_data['Region_EN'])}")
    print("\nData summary:")
    print(merged_data[numeric_cols].describe())
    
    return merged_data

def perform_clustering(data):
    """Perform clustering analysis"""
    print("\nPerforming clustering analysis...")
    
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    X = data[feature_cols].copy()
    
    # Standardize data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = {}
    
    # K-means clustering
    for k in [3, 4, 5]:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        silhouette = silhouette_score(X_scaled, labels)
        calinski = calinski_harabasz_score(X_scaled, labels)
        
        results[f'kmeans_k{k}'] = {
            'labels': labels,
            'silhouette': silhouette,
            'calinski_harabasz': calinski,
            'model': kmeans
        }
        
        print(f"K-means (k={k}) - Silhouette: {silhouette:.3f}, Calinski-Harabasz: {calinski:.1f}")
    
    # Hierarchical clustering
    for k in [3, 4]:
        agg_clustering = AgglomerativeClustering(n_clusters=k, linkage='ward')
        labels = agg_clustering.fit_predict(X_scaled)
        
        silhouette = silhouette_score(X_scaled, labels)
        calinski = calinski_harabasz_score(X_scaled, labels)
        
        results[f'hierarchical_k{k}'] = {
            'labels': labels,
            'silhouette': silhouette,
            'calinski_harabasz': calinski,
            'model': agg_clustering
        }
        
        print(f"Hierarchical clustering (k={k}) - Silhouette: {silhouette:.3f}, Calinski-Harabasz: {calinski:.1f}")
    
    return results, X_scaled, scaler

def visualize_results(data, results, X_scaled):
    """Visualize clustering results"""
    print("\nVisualizing results...")
    
    # Select best result
    best_method = max(results.keys(), key=lambda x: results[x]['silhouette'])
    best_labels = results[best_method]['labels']
    
    # PCA for 2D reduction
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Real Estate Data Clustering Analysis', fontsize=16, fontweight='bold')
    
    # 1. Best clustering result
    ax = axes[0, 0]
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=best_labels, cmap='viridis', alpha=0.7, s=100)
    ax.set_title(f'Best Clustering: {best_method}\n(Silhouette: {results[best_method]["silhouette"]:.3f})')
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    
    # Add region labels
    for i, region in enumerate(data['Region_EN']):
        ax.annotate(region, (X_pca[i, 0], X_pca[i, 1]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    # 2. Silhouette score comparison
    ax = axes[0, 1]
    methods = list(results.keys())
    silhouette_scores = [results[method]['silhouette'] for method in methods]
    
    bars = ax.bar(range(len(methods)), silhouette_scores, color='skyblue', alpha=0.7)
    ax.set_title('Silhouette Score Comparison')
    ax.set_ylabel('Silhouette Score')
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels([m.replace('_', '\n') for m in methods], rotation=45, ha='right')
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{height:.3f}', ha='center', va='bottom')
    
    # 3. GDP distribution by cluster
    ax = axes[1, 0]
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    for cluster_id in range(len(set(best_labels))):
        cluster_gdp = cluster_data[cluster_data['cluster'] == cluster_id]['GDP_Average']
        ax.scatter([cluster_id] * len(cluster_gdp), cluster_gdp, 
                  alpha=0.7, s=60, label=f'Cluster {cluster_id}')
    
    ax.set_title('GDP Distribution by Cluster')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('GDP Average (100M KRW)')
    ax.legend()
    
    # 4. Competition rate distribution by cluster
    ax = axes[1, 1]
    for cluster_id in range(len(set(best_labels))):
        cluster_comp = cluster_data[cluster_data['cluster'] == cluster_id]['General_Supply_Competition_Rate']
        ax.scatter([cluster_id] * len(cluster_comp), cluster_comp, 
                  alpha=0.7, s=60, label=f'Cluster {cluster_id}')
    
    ax.set_title('Competition Rate Distribution by Cluster')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('Average Competition Rate')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('result/clustering_analysis_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return best_method, best_labels

def create_detailed_analysis(data, best_method, best_labels):
    """Create detailed analysis and additional visualizations"""
    print("\nCreating detailed analysis...")
    
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    # Cluster characteristics heatmap
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. Cluster average characteristics heatmap
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    cluster_means = cluster_data.groupby('cluster')[feature_cols].mean()
    
    # Normalize (0-1 scale)
    cluster_means_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min())
    
    # Rename columns for better display
    display_names = {
        'Special_Supply_Competition_Rate': 'Special Supply\nCompetition Rate',
        'General_Supply_Competition_Rate': 'General Supply\nCompetition Rate',
        'Special_Supply_Total_Units': 'Special Supply\nTotal Units',
        'General_Supply_Total_Units': 'General Supply\nTotal Units',
        'GDP_Average': 'GDP Average'
    }
    
    cluster_means_norm_display = cluster_means_norm.rename(columns=display_names)
    
    sns.heatmap(cluster_means_norm_display.T, annot=True, cmap='YlOrRd', fmt='.2f',
                ax=axes[0], cbar_kws={'label': 'Normalized Value'})
    axes[0].set_title('Cluster Characteristics Heatmap')
    axes[0].set_xlabel('Cluster')
    axes[0].set_ylabel('Features')
    
    # 2. Cluster distribution pie chart
    cluster_counts = cluster_data['cluster'].value_counts().sort_index()
    colors = plt.cm.viridis(np.linspace(0, 1, len(cluster_counts)))
    
    wedges, texts, autotexts = axes[1].pie(cluster_counts.values, 
                                          labels=[f'Cluster {i}' for i in cluster_counts.index],
                                          autopct='%1.1f%%', colors=colors)
    axes[1].set_title('Cluster Distribution')
    
    plt.tight_layout()
    plt.savefig('result/detailed_cluster_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return cluster_means

def save_results_to_csv(data, best_method, best_labels):
    """Save clustering results to CSV"""
    print("\nSaving results to CSV...")
    
    # Create results directory if it doesn't exist
    os.makedirs('result', exist_ok=True)
    
    # Save cluster assignments
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    cluster_data.to_csv('result/clustering_results.csv', index=False)
    
    # Save cluster summary
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    cluster_summary = cluster_data.groupby('cluster')[feature_cols].mean().round(2)
    cluster_summary.to_csv('result/cluster_summary.csv')
    
    print("Results saved to:")
    print("- result/clustering_results.csv")
    print("- result/cluster_summary.csv")

def print_cluster_summary(data, best_method, best_labels):
    """Print cluster summary"""
    print(f"\n=== Clustering Analysis Results Summary ===")
    print(f"Best method: {best_method}")
    
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    print("\nCluster composition by region:")
    for cluster_id in range(len(set(best_labels))):
        regions = cluster_data[cluster_data['cluster'] == cluster_id]['Region_EN'].tolist()
        print(f"Cluster {cluster_id}: {', '.join(regions)}")
    
    print("\nCluster average characteristics:")
    cluster_summary = cluster_data.groupby('cluster')[feature_cols].mean().round(2)
    print(cluster_summary)
    
    # Cluster interpretation
    print("\n=== Cluster Characteristics Interpretation ===")
    for cluster_id in range(len(set(best_labels))):
        cluster_subset = cluster_data[cluster_data['cluster'] == cluster_id]
        regions = cluster_subset['Region_EN'].tolist()
        
        avg_gdp = cluster_subset['GDP_Average'].mean()
        avg_comp = cluster_subset['General_Supply_Competition_Rate'].mean()
        total_supply = cluster_subset['General_Supply_Total_Units'].sum()
        
        print(f"\nCluster {cluster_id} ({', '.join(regions)}):")
        print(f"  - Average GDP: {avg_gdp:,.0f} (100M KRW)")
        print(f"  - Average Competition Rate: {avg_comp:.2f}:1")
        print(f"  - Total Supply Units: {total_supply:,.0f} units")
        
        if avg_gdp > cluster_data['GDP_Average'].mean():
            gdp_level = "High"
        else:
            gdp_level = "Low"
            
        if avg_comp > cluster_data['General_Supply_Competition_Rate'].mean():
            comp_level = "High"
        else:
            comp_level = "Low"
            
        print(f"  - Characteristics: {gdp_level} GDP, {comp_level} Competition Rate")

def main():
    """Main execution function"""
    print("=== Real Estate Data Clustering Analysis Started ===")
    
    # Load and preprocess data
    data = load_and_prepare_data()
    
    # Perform clustering
    results, X_scaled, scaler = perform_clustering(data)
    
    # Visualize results
    best_method, best_labels = visualize_results(data, results, X_scaled)
    
    # Detailed analysis
    cluster_means = create_detailed_analysis(data, best_method, best_labels)
    
    # Save results to CSV
    save_results_to_csv(data, best_method, best_labels)
    
    # Print summary
    print_cluster_summary(data, best_method, best_labels)
    
    print("\n=== Analysis Complete ===")
    print("Result files saved in result/ directory:")
    print("- clustering_analysis_results.png")
    print("- detailed_cluster_analysis.png")
    print("- clustering_results.csv")
    print("- cluster_summary.csv")

if __name__ == "__main__":
    main() 
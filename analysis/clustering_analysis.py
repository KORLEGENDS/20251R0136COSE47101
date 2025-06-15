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

# Set matplotlib backend and font
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def clean_numeric_data(series):
    """Clean numeric data containing strings like (△151)"""
    # Remove parentheses and content, convert to numeric
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
    print(f"Competition data shape: {competition_data.shape}")
    
    # Load GDP data
    gdp_data = pd.read_csv('../preprocessing/result/지역내총생산_시장가격_2013년이후.csv')
    print(f"GDP data shape: {gdp_data.shape}")
    
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
    
    print(f"Final merged data shape: {merged_data.shape}")
    print(f"Regions included: {list(merged_data['Region_EN'])}")
    print("\nData summary:")
    print(merged_data[numeric_cols].describe())
    
    return merged_data

def perform_clustering_analysis(data):
    """Perform comprehensive clustering analysis"""
    print("\nPerforming clustering analysis...")
    
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    X = data[feature_cols].copy()
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = {}
    
    # K-means clustering with different k values
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

def create_comprehensive_visualization(data, results, X_scaled):
    """Create comprehensive visualization of clustering results"""
    print("\nCreating visualizations...")
    
    # Select best clustering method
    best_method = max(results.keys(), key=lambda x: results[x]['silhouette'])
    best_labels = results[best_method]['labels']
    
    # PCA for dimensionality reduction
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Create comprehensive plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Real Estate Data Clustering Analysis', fontsize=16, fontweight='bold')
    
    # 1. Best clustering result with PCA
    ax = axes[0, 0]
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=best_labels, cmap='viridis', alpha=0.7, s=100)
    ax.set_title(f'Best Clustering: {best_method}\n(Silhouette: {results[best_method]["silhouette"]:.3f})')
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    
    # Add region labels
    for i, region in enumerate(data['Region_EN']):
        ax.annotate(region, (X_pca[i, 0], X_pca[i, 1]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    
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
               f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 3. GDP vs Competition Rate scatter
    ax = axes[0, 2]
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    for cluster_id in range(len(set(best_labels))):
        cluster_subset = cluster_data[cluster_data['cluster'] == cluster_id]
        ax.scatter(cluster_subset['GDP_Average'], cluster_subset['General_Supply_Competition_Rate'], 
                  alpha=0.7, s=60, label=f'Cluster {cluster_id}')
    
    ax.set_title('GDP vs Competition Rate')
    ax.set_xlabel('GDP Average (100M KRW)')
    ax.set_ylabel('General Supply Competition Rate')
    ax.legend()
    
    # 4. GDP distribution by cluster
    ax = axes[1, 0]
    for cluster_id in range(len(set(best_labels))):
        cluster_gdp = cluster_data[cluster_data['cluster'] == cluster_id]['GDP_Average']
        ax.scatter([cluster_id] * len(cluster_gdp), cluster_gdp, 
                  alpha=0.7, s=60, label=f'Cluster {cluster_id}')
    
    ax.set_title('GDP Distribution by Cluster')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('GDP Average (100M KRW)')
    ax.legend()
    
    # 5. Supply units distribution
    ax = axes[1, 1]
    for cluster_id in range(len(set(best_labels))):
        cluster_supply = cluster_data[cluster_data['cluster'] == cluster_id]['General_Supply_Total_Units']
        ax.scatter([cluster_id] * len(cluster_supply), cluster_supply, 
                  alpha=0.7, s=60, label=f'Cluster {cluster_id}')
    
    ax.set_title('Supply Units Distribution by Cluster')
    ax.set_xlabel('Cluster')
    ax.set_ylabel('General Supply Total Units')
    ax.legend()
    
    # 6. Cluster size pie chart
    ax = axes[1, 2]
    cluster_counts = cluster_data['cluster'].value_counts().sort_index()
    colors = plt.cm.viridis(np.linspace(0, 1, len(cluster_counts)))
    
    wedges, texts, autotexts = ax.pie(cluster_counts.values, 
                                     labels=[f'Cluster {i}' for i in cluster_counts.index],
                                     autopct='%1.1f%%', colors=colors)
    ax.set_title('Cluster Size Distribution')
    
    plt.tight_layout()
    plt.savefig('result/comprehensive_clustering_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return best_method, best_labels

def create_detailed_heatmap(data, best_method, best_labels):
    """Create detailed cluster characteristics heatmap"""
    print("\nCreating detailed heatmap...")
    
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    # Feature analysis
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    cluster_means = cluster_data.groupby('cluster')[feature_cols].mean()
    
    # Normalize for better visualization
    cluster_means_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min())
    
    # Create heatmap
    plt.figure(figsize=(12, 8))
    
    # Rename columns for better display
    display_names = {
        'Special_Supply_Competition_Rate': 'Special Supply\nCompetition Rate',
        'General_Supply_Competition_Rate': 'General Supply\nCompetition Rate',
        'Special_Supply_Total_Units': 'Special Supply\nTotal Units',
        'General_Supply_Total_Units': 'General Supply\nTotal Units',
        'GDP_Average': 'GDP Average'
    }
    
    cluster_means_norm_display = cluster_means_norm.rename(columns=display_names)
    
    sns.heatmap(cluster_means_norm_display.T, annot=True, cmap='RdYlBu_r', fmt='.2f',
                cbar_kws={'label': 'Normalized Value (0-1 scale)'})
    plt.title('Cluster Characteristics Heatmap (Normalized)', fontsize=14, fontweight='bold')
    plt.xlabel('Cluster')
    plt.ylabel('Features')
    
    plt.tight_layout()
    plt.savefig('result/cluster_characteristics_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return cluster_means

def save_comprehensive_results(data, best_method, best_labels, cluster_means):
    """Save all analysis results to files"""
    print("\nSaving comprehensive results...")
    
    # Create results directory
    os.makedirs('result', exist_ok=True)
    
    # Save cluster assignments with all data
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    cluster_data.to_csv('result/clustering_results_detailed.csv', index=False)
    
    # Save cluster summary statistics
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    cluster_summary = cluster_data.groupby('cluster')[feature_cols].agg(['mean', 'std', 'min', 'max']).round(2)
    cluster_summary.to_csv('result/cluster_detailed_summary.csv')
    
    # Save cluster means (normalized)
    cluster_means_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min())
    cluster_means_norm.to_csv('result/cluster_normalized_means.csv')
    
    # Save region-cluster mapping
    region_cluster_map = cluster_data[['Region_EN', 'cluster']].sort_values('cluster')
    region_cluster_map.to_csv('result/region_cluster_mapping.csv', index=False)
    
    print("Comprehensive results saved:")
    print("- result/clustering_results_detailed.csv")
    print("- result/cluster_detailed_summary.csv") 
    print("- result/cluster_normalized_means.csv")
    print("- result/region_cluster_mapping.csv")

def print_comprehensive_analysis(data, best_method, best_labels):
    """Print comprehensive analysis results"""
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE CLUSTERING ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Best clustering method: {best_method}")
    
    cluster_data = data.copy()
    cluster_data['cluster'] = best_labels
    
    feature_cols = ['Special_Supply_Competition_Rate', 'General_Supply_Competition_Rate', 
                   'Special_Supply_Total_Units', 'General_Supply_Total_Units', 'GDP_Average']
    
    print(f"\nNumber of clusters: {len(set(best_labels))}")
    print(f"Total regions analyzed: {len(data)}")
    
    print(f"\n{'='*40}")
    print("CLUSTER COMPOSITION BY REGION")
    print(f"{'='*40}")
    for cluster_id in range(len(set(best_labels))):
        regions = cluster_data[cluster_data['cluster'] == cluster_id]['Region_EN'].tolist()
        print(f"Cluster {cluster_id} ({len(regions)} regions): {', '.join(regions)}")
    
    print(f"\n{'='*40}")
    print("CLUSTER AVERAGE CHARACTERISTICS")
    print(f"{'='*40}")
    cluster_summary = cluster_data.groupby('cluster')[feature_cols].mean().round(2)
    print(cluster_summary)
    
    print(f"\n{'='*40}")
    print("DETAILED CLUSTER INTERPRETATION")
    print(f"{'='*40}")
    
    overall_avg_gdp = cluster_data['GDP_Average'].mean()
    overall_avg_comp = cluster_data['General_Supply_Competition_Rate'].mean()
    
    for cluster_id in range(len(set(best_labels))):
        cluster_subset = cluster_data[cluster_data['cluster'] == cluster_id]
        regions = cluster_subset['Region_EN'].tolist()
        
        avg_gdp = cluster_subset['GDP_Average'].mean()
        avg_comp = cluster_subset['General_Supply_Competition_Rate'].mean()
        avg_special_comp = cluster_subset['Special_Supply_Competition_Rate'].mean()
        total_supply = cluster_subset['General_Supply_Total_Units'].sum()
        total_special_supply = cluster_subset['Special_Supply_Total_Units'].sum()
        
        print(f"\nCluster {cluster_id} Analysis:")
        print(f"  Regions: {', '.join(regions)}")
        print(f"  Economic Profile:")
        print(f"    - Average GDP: {avg_gdp:,.0f} (100M KRW)")
        print(f"    - GDP Level: {'High' if avg_gdp > overall_avg_gdp else 'Low'} (vs national avg: {overall_avg_gdp:,.0f})")
        print(f"  Housing Market Profile:")
        print(f"    - General Supply Competition Rate: {avg_comp:.2f}:1")
        print(f"    - Special Supply Competition Rate: {avg_special_comp:.2f}:1")
        print(f"    - Competition Level: {'High' if avg_comp > overall_avg_comp else 'Low'} (vs national avg: {overall_avg_comp:.2f})")
        print(f"  Supply Volume:")
        print(f"    - Total General Supply Units: {total_supply:,.0f}")
        print(f"    - Total Special Supply Units: {total_special_supply:,.0f}")
        
        # Cluster characterization
        if avg_gdp > overall_avg_gdp and avg_comp > overall_avg_comp:
            char = "High GDP, High Competition (Premium Markets)"
        elif avg_gdp > overall_avg_gdp and avg_comp <= overall_avg_comp:
            char = "High GDP, Low Competition (Stable Premium Markets)"
        elif avg_gdp <= overall_avg_gdp and avg_comp > overall_avg_comp:
            char = "Low GDP, High Competition (Emerging Markets)"
        else:
            char = "Low GDP, Low Competition (Regional Markets)"
            
        print(f"  Market Characterization: {char}")

def main():
    """Main execution function"""
    print("="*60)
    print("REAL ESTATE DATA CLUSTERING ANALYSIS")
    print("="*60)
    
    # Load and preprocess data
    data = load_and_prepare_data()
    
    # Perform clustering analysis
    results, X_scaled, scaler = perform_clustering_analysis(data)
    
    # Create comprehensive visualizations
    best_method, best_labels = create_comprehensive_visualization(data, results, X_scaled)
    
    # Create detailed heatmap
    cluster_means = create_detailed_heatmap(data, best_method, best_labels)
    
    # Save comprehensive results
    save_comprehensive_results(data, best_method, best_labels, cluster_means)
    
    # Print comprehensive analysis
    print_comprehensive_analysis(data, best_method, best_labels)
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print("All results saved in result/ directory:")
    print("📊 Visualizations:")
    print("  - comprehensive_clustering_analysis.png")
    print("  - cluster_characteristics_heatmap.png")
    print("📄 Data Files:")
    print("  - clustering_results_detailed.csv")
    print("  - cluster_detailed_summary.csv")
    print("  - cluster_normalized_means.csv")
    print("  - region_cluster_mapping.csv")

if __name__ == "__main__":
    main() 
import pandas as pd

def extract_2013_2024_data():
    """
    2013년부터 2024년까지의 미분양 데이터만 추출하는 함수
    """
    
    # CSV 파일 읽기 - 다양한 인코딩 시도
    file_path = '../data/supply/미분양주택현황.csv'
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
    df = None
    
    for encoding in encodings:
        try:
            print(f"{encoding} 인코딩으로 시도 중...")
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"✅ {encoding} 인코딩으로 성공!")
            break
        except Exception as e:
            print(f"❌ {encoding} 인코딩 실패: {str(e)[:50]}...")
            continue
    
    if df is None:
        print("파일을 읽을 수 없습니다.")
        return None
    
    print(f"원본 데이터: {len(df)}행")
    print(f"전체 컬럼 수: {len(df.columns)}")
    
    # 기본 컬럼들 (No, 분류, 분류.1)
    basic_columns = df.columns[:3].tolist()
    print(f"기본 컬럼: {basic_columns}")
    
    # 2013년부터 2024년까지의 컬럼 찾기
    target_columns = []
    for col in df.columns:
        if any(year in str(col) for year in ['2013', '2014', '2015', '2016', '2017', '2018', 
                                            '2019', '2020', '2021', '2022', '2023', '2024']):
            target_columns.append(col)
    
    print(f"2013-2024년 컬럼 수: {len(target_columns)}")
    print(f"첫 번째 날짜 컬럼: {target_columns[0] if target_columns else 'None'}")
    print(f"마지막 날짜 컬럼: {target_columns[-1] if target_columns else 'None'}")
    
    # 기본 컬럼 + 2013-2024년 컬럼만 선택
    selected_columns = basic_columns + target_columns
    df_filtered = df[selected_columns].copy()
    
    # 시간순으로 컬럼 정렬 (현재 역순이므로 뒤집기)
    # 기본 컬럼은 그대로 두고, 날짜 컬럼만 뒤집기
    date_columns_sorted = target_columns[::-1]  # 역순으로 정렬
    final_columns = basic_columns + date_columns_sorted
    df_final = df_filtered[final_columns].copy()
    
    print(f"최종 데이터: {len(df_final)}행, {len(df_final.columns)}열")
    print(f"정렬 후 첫 번째 날짜: {date_columns_sorted[0] if date_columns_sorted else 'None'}")
    print(f"정렬 후 마지막 날짜: {date_columns_sorted[-1] if date_columns_sorted else 'None'}")
    
    # 새 파일로 저장
    output_file = 'result/미분양주택현황_2013_2024.csv'
    
    try:
        df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 데이터가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 파일 저장 중 오류: {e}")
        try:
            df_final.to_csv(output_file, index=False, encoding='cp949')
            print(f"✅ cp949 인코딩으로 '{output_file}'에 저장되었습니다.")
        except:
            print(f"❌ 파일 저장 실패")
    
    # 결과 미리보기
    print("\n=== 데이터 미리보기 ===")
    display_cols = basic_columns + date_columns_sorted[:5] + date_columns_sorted[-3:]
    print(df_final[display_cols].head())
    
    # 지역별 요약
    print(f"\n=== 지역별 요약 ===")
    if len(basic_columns) >= 3:
        region_col = basic_columns[2]  # 분류.1 컬럼
        unique_regions = df_final[region_col].unique()
        print(f"지역 수: {len(unique_regions)}")
        for region in unique_regions:
            if pd.notna(region) and region != '분류':
                print(f"  - {region}")
    
    return df_final

# 실행
if __name__ == "__main__":
    result = extract_2013_2024_data()
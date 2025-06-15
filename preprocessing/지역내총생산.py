import pandas as pd

def extract_gdp_from_2013():
    
    # CSV 파일 읽기 - 다양한 인코딩 시도
    file_path = '../data/else/시도별 지역내총생산.csv'
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
        print("❌ 모든 인코딩으로 파일 읽기에 실패했습니다.")
        return None
    
    print(f"원본 데이터: {len(df)}행, {len(df.columns)}열")
    print(f"컬럼명: {list(df.columns)}")
    
    # 기본 정보 컬럼들 (시도별, 경제활동별, 항목, 단위)
    basic_columns = df.columns[:4].tolist()
    print(f"\n기본 컬럼: {basic_columns}")
    
    # 2013년부터의 연도 컬럼 찾기
    year_columns = []
    for col in df.columns:
        if '2013' in str(col) or '2014' in str(col) or '2015' in str(col) or \
           '2016' in str(col) or '2017' in str(col) or '2018' in str(col) or \
           '2019' in str(col) or '2020' in str(col) or '2021' in str(col) or \
           '2022' in str(col) or '2023' in str(col):
            year_columns.append(col)
    
    print(f"2013년부터의 연도 컬럼: {year_columns}")
    
    # 선택할 컬럼들 = 기본 컬럼 + 2013년부터의 연도 컬럼
    selected_columns = basic_columns + year_columns
    
    # 해당 컬럼들만 추출
    df_extracted = df[selected_columns].copy()
    
    # '경제활동별'이 '지역내총생산(시장가격)'인 행만 필터링
    df_extracted = df_extracted[df_extracted['경제활동별'] == '지역내총생산(시장가격)'].copy()
    
    print(f"필터링 후 데이터: {len(df_extracted)}행")
    
    # 빈 컬럼이 있다면 제거 (마지막에 빈 컬럼이 있을 수 있음)
    df_extracted = df_extracted.dropna(axis=1, how='all')
    
    # 새 파일로 저장
    output_file = 'result/지역내총생산_시장가격_2013년이후.csv'
    
    try:
        df_extracted.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 데이터가 '{output_file}'에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 파일 저장 중 오류: {e}")
        # 대안으로 cp949 시도
        try:
            df_extracted.to_csv(output_file, index=False, encoding='cp949')
            print(f"✅ cp949 인코딩으로 '{output_file}'에 저장되었습니다.")
        except:
            print(f"❌ 파일 저장 실패")
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    
    print(f"\n지역 목록:")
    unique_regions = df_extracted['시도별'].unique()
    for region in unique_regions:
        print(f"  - {region}")
    
    return df_extracted

# 실행
if __name__ == "__main__":
    result = extract_gdp_from_2013()
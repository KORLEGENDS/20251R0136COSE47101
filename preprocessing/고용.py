import pandas as pd
import numpy as np

def extract_specific_regions_employment_data(input_file, output_file, target_regions):

    
    # CSV 파일 읽기 (euc-kr 인코딩)
    try:
        df = pd.read_csv(input_file, encoding='euc-kr')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(input_file, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='utf-8')
    
    # 첫 번째 컬럼명 확인 (행정구역별)
    region_column = df.columns[0]
    print(f"행정구역 컬럼명: {region_column}")
    
    # 고유한 지역 확인
    unique_regions = df[region_column].unique()
    print(f"\\n고유한 지역 수: {len(unique_regions)}")
    print("\\n처음 20개 지역:")
    for i, region in enumerate(unique_regions[:20]):
        print(f"{i+1}: {region}")
    
    # 목표 지역들과 매칭되는 행 찾기
    target_regions_variations = []

    # 지역별 변형 매핑 정의
    region_variants = {
        '서울 송파구': ['송파구', '서울송파구', '서울특별시 송파구'],
        '하남시': ['경기 하남시', '경기도 하남시'],
        '성남시': ['경기 성남시', '경기도 성남시'],
        '김포시': ['경기 김포시', '경기도 김포시'],
        '고양시': ['경기 고양시', '경기도 고양시'],
    }

    # 각 목표 지역에 대해 가능한 변형들 고려
    for target in target_regions:
        # 기본 형태
        target_regions_variations.append(target)

        # 사전에 정의된 변형이 있다면 추가
        target_regions_variations.extend(region_variants.get(target, []))

    print(f"\n검색할 지역 변형들: {target_regions_variations}")
    
    # 매칭되는 행들 찾기
    matched_rows = pd.DataFrame()
    found_regions = []
    
    for target_variation in target_regions_variations:
        # 정확히 일치
        exact_match = df[df[region_column] == target_variation]
        if not exact_match.empty:
            matched_rows = pd.concat([matched_rows, exact_match], ignore_index=True)
            found_regions.append(target_variation)
        else:
            # 부분 일치
            partial_match = df[df[region_column].str.contains(target_variation, na=False)]
            if not partial_match.empty:
                matched_rows = pd.concat([matched_rows, partial_match], ignore_index=True)
                unique_partial = partial_match[region_column].unique()
                found_regions.extend(unique_partial)
                for region in unique_partial:
                    print(f"    → {region}")
    
    # 중복 제거
    if not matched_rows.empty:
        matched_rows = matched_rows.drop_duplicates()
    else:
        for i, region in enumerate(unique_regions):
            if any(keyword in region for keyword in ['송파', '하남', '성남', '김포', '고양']):
                print(f"  {region}")
        return None
    
    # 실제로 찾은 지역들 출력
    final_regions = matched_rows[region_column].unique()
    print(f"\\n실제로 추출된 지역들 ({len(final_regions)}개):")
    for i, region in enumerate(final_regions):
        row_count = len(matched_rows[matched_rows[region_column] == region])
        print(f"{i+1}: {region} ({row_count}행)")
    
    # 새로운 CSV 파일로 저장
    matched_rows.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return matched_rows

def analyze_extracted_data(df):
    """
    추출된 데이터 분석
    """
    if df is None or df.empty:
        print("분석할 데이터가 없습니다.")
        return
    
    print("\\n=== 추출된 데이터 분석 ===")
    
    region_column = df.columns[0]
    age_column = df.columns[1] if len(df.columns) > 1 else None
    item_column = df.columns[2] if len(df.columns) > 2 else None
    
    print(f"데이터 구조:")
    print(f"- 총 행 수: {len(df)}")
    print(f"- 총 컬럼 수: {len(df.columns)}")
    print(f"- 지역 수: {df[region_column].nunique()}")
    
    if age_column:
        print(f"- 연령 그룹 수: {df[age_column].nunique()}")
        print(f"연령 그룹: {df[age_column].unique()}")
    
    if item_column:
        print(f"- 항목 수: {df[item_column].nunique()}")
        print(f"항목들: {df[item_column].unique()}")
    
    # 지역별 데이터 수 확인
    print(f"\\n지역별 데이터 행 수:")
    region_counts = df[region_column].value_counts()
    for region, count in region_counts.items():
        print(f"  {region}: {count}행")

def preview_data(df, num_rows=5):
    """
    데이터 미리보기
    """
    if df is None or df.empty:
        print("미리볼 데이터가 없습니다.")
        return
    
    print("\\n=== 데이터 미리보기 ===")
    print(f"처음 {num_rows}행:")
    
    # 컬럼이 많을 경우 일부만 표시
    if len(df.columns) > 10:
        display_cols = list(df.columns[:4]) + list(df.columns[-4:])
        display_df = df[display_cols]
        print("(앞 4개 컬럼과 뒤 4개 컬럼만 표시)")
    else:
        display_df = df
    
    print(display_df.head(num_rows).to_string())
    
    # 결측값 확인
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        print(f"\\n결측값 정보:")
        missing_cols = missing_data[missing_data > 0]
        for col, missing_count in missing_cols.items():
            print(f"  {col}: {missing_count}개")
    else:
        print("\\n결측값 없음")

def search_regions_interactive(input_file):
    try:
        df = pd.read_csv(input_file, encoding='euc-kr')
        region_column = df.columns[0]
        unique_regions = df[region_column].unique()
        
        
        # 지역을 카테고리별로 정리
        seoul_regions = [r for r in unique_regions if '서울' in r]
        gyeonggi_regions = [r for r in unique_regions if '경기' in r]
        other_regions = [r for r in unique_regions if '서울' not in r and '경기' not in r]
        
        print(f"\\n서울 지역 ({len(seoul_regions)}개):")
        for region in sorted(seoul_regions):
            print(f"  {region}")
        
        print(f"\\n경기 지역 ({len(gyeonggi_regions)}개):")
        for region in sorted(gyeonggi_regions):
            print(f"  {region}")
        
        if other_regions:
            print(f"\\n기타 지역 ({len(other_regions)}개):")
            for region in sorted(other_regions)[:20]:  # 처음 20개만
                print(f"  {region}")
            if len(other_regions) > 20:
                print(f"  ... 및 {len(other_regions) - 20}개 더")
        
        # 목표 지역 검색
        target_keywords = ['송파', '하남', '성남', '김포', '고양']
        print(f"\\n목표 지역 관련 검색 결과:")
        for keyword in target_keywords:
            matching = [r for r in unique_regions if keyword in r]
            print(f"'{keyword}' 포함 지역: {matching}")
            
    except Exception as e:
        print(f"지역 검색 중 오류: {e}")

# 메인 실행 코드
if __name__ == "__main__":
    # 파일 경로 설정
    input_file = '../data/else/시군구 연령별 취업자 및 고용률.csv'
    output_file = 'result/특정지역_취업자_고용률.csv'
    
    # 추출할 지역 리스트
    target_regions = ['서울 송파구', '하남시', '성남시', '김포시', '고양시']
    
    try:
        print("=== 특정 지역 취업자 및 고용률 데이터 추출 ===")
        print(f"목표 지역: {target_regions}")
        
        # 먼저 사용 가능한 지역들 확인
        print("\\n1단계: 사용 가능한 지역 확인")
        search_regions_interactive(input_file)
        
        # 데이터 추출 실행
        print("\\n2단계: 데이터 추출")
        extracted_df = extract_specific_regions_employment_data(
            input_file, output_file, target_regions
        )
        
        if extracted_df is not None:
            # 결과 분석
            print("\\n3단계: 추출된 데이터 분석")
            analyze_extracted_data(extracted_df)
            
            # 데이터 미리보기
            print("\\n4단계: 데이터 미리보기")
            preview_data(extracted_df)
            
            print(f"\\n✅ 작업 완료!")
            print(f"원본 파일: {input_file}")
            print(f"추출된 파일: {output_file}")
            print(f"추출된 지역 수: {extracted_df[extracted_df.columns[0]].nunique()}")
            print(f"총 데이터 행 수: {len(extracted_df)}")
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except Exception as e:
        import traceback
        traceback.print_exc()

# 추가 유틸리티 함수들
def create_region_summary(df, output_summary_file):
    """
    지역별 요약 통계 생성
    """
    if df is None or df.empty:
        return
    
    try:
        region_column = df.columns[0]
        summary_data = []
        
        for region in df[region_column].unique():
            region_data = df[df[region_column] == region]
            summary_data.append({
                '지역': region,
                '데이터_행수': len(region_data),
                '연령그룹수': region_data.iloc[:, 1].nunique() if len(df.columns) > 1 else 0,
                '항목수': region_data.iloc[:, 2].nunique() if len(df.columns) > 2 else 0
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_summary_file, index=False, encoding='utf-8-sig')
        print(f"지역별 요약이 '{output_summary_file}'에 저장되었습니다.")
        
    except Exception as e:
        print(f"요약 생성 중 오류: {e}")

def filter_by_age_and_item(df, target_ages=None, target_items=None, output_file=None):
    """
    연령대와 항목으로 추가 필터링
    """
    if df is None or df.empty:
        return None
    
    filtered_df = df.copy()
    
    if target_ages and len(df.columns) > 1:
        age_column = df.columns[1]
        filtered_df = filtered_df[filtered_df[age_column].isin(target_ages)]
        print(f"연령 필터링 후: {len(filtered_df)}행")
    
    if target_items and len(df.columns) > 2:
        item_column = df.columns[2]
        filtered_df = filtered_df[filtered_df[item_column].isin(target_items)]
        print(f"항목 필터링 후: {len(filtered_df)}행")
    
    if output_file:
        filtered_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"필터링된 데이터가 '{output_file}'에 저장되었습니다.")
    
    return filtered_df

if __name__ == "__main__":
    # 예시: 특정 연령대와 항목만 추출
    # extracted_df = extract_specific_regions_employment_data(...)
    # filtered_df = filter_by_age_and_item(
    #     extracted_df, 
    #     target_ages=['15 - 64세', '전체'],
    #     target_items=['취업자 (천명)', '고용률 (%)'],
    #     output_file='필터링된_취업자_고용률.csv'
    # )
    pass

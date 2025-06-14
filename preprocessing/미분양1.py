import pandas as pd
import numpy as np
import re

def process_unsold_housing_data(input_file, output_file):
    
    # CSV 파일 읽기 (euc-kr 인코딩)
    try:
        df = pd.read_csv(input_file, encoding='euc-kr')
        print(f"원본 데이터 크기: {df.shape}")
    except UnicodeDecodeError:
        print("euc-kr 인코딩 실패, cp949로 시도...")
        try:
            df = pd.read_csv(input_file, encoding='cp949')
        except UnicodeDecodeError:
            print("cp949 인코딩 실패, utf-8로 시도...")
            df = pd.read_csv(input_file, encoding='utf-8')
    
    # 컬럼명 확인
    columns = df.columns.tolist()
    print(f"전체 컬럼 수: {len(columns)}")
    
    # 2013년 1월과 2024년 12월의 인덱스 찾기
    start_2013_index = None
    end_2024_index = None
    
    for i, col in enumerate(columns):
        if '2013년 1월' in str(col) or ('2013' in str(col) and '1월' in str(col)):
            start_2013_index = i
        if '2024년 12월' in str(col) or ('2024' in str(col) and '12월' in str(col)):
            end_2024_index = i
    
    print(f"2013년 1월 컬럼 인덱스: {start_2013_index}")
    print(f"2024년 12월 컬럼 인덱스: {end_2024_index}")
    
    if start_2013_index is None or end_2024_index is None:
        print("시작 또는 종료 컬럼을 찾을 수 없습니다.")
        return None
    
    # 기본 컬럼들 (처음 3개) + 2013년 1월부터 2024년 12월까지
    # 데이터가 역시간순이므로 end_2024_index부터 start_2013_index까지
    base_columns = columns[:3]  # No, 분류1, 분류2
    selected_columns = base_columns + columns[end_2024_index:start_2013_index + 1]
    
    print(f"선택된 컬럼 수: {len(selected_columns)}")
    print(f"첫 번째 날짜 컬럼: {selected_columns[3] if len(selected_columns) > 3 else 'None'}")
    print(f"마지막 날짜 컬럼: {selected_columns[-1] if len(selected_columns) > 3 else 'None'}")
    
    # 선택된 컬럼들로 새로운 DataFrame 생성
    filtered_df = df[selected_columns].copy()
    
    # 데이터 타입 및 따옴표 문제 해결
    print("\n따옴표 및 데이터 타입 정리 중...")
    
    # 날짜 컬럼들 (3번째 컬럼부터)에 대해 따옴표 제거 및 숫자 변환
    date_columns = selected_columns[3:]
    
    for col in date_columns:
        # 문자열로 변환하고 따옴표 문제 해결
        filtered_df[col] = filtered_df[col].astype(str)
        
        # 다양한 따옴표 패턴 제거
        filtered_df[col] = filtered_df[col].str.replace('"""', '', regex=False)
        filtered_df[col] = filtered_df[col].str.replace('""', '', regex=False)
        filtered_df[col] = filtered_df[col].str.replace('"', '', regex=False)
        filtered_df[col] = filtered_df[col].str.replace("'", '', regex=False)
        
        # 콤마 제거 (천단위 구분자)
        filtered_df[col] = filtered_df[col].str.replace(',', '', regex=False)
        
        # 빈 문자열이나 'nan'을 0으로 변환
        filtered_df[col] = filtered_df[col].replace(['', 'nan', 'None', 'null'], '0')
        
        # 숫자가 아닌 값들을 0으로 변환 후 정수형으로 변환
        try:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).astype(int)
        except:
            print(f"컬럼 {col} 변환 중 오류 발생")
    
    # 시간순으로 정렬 (현재 역시간순이므로 날짜 컬럼들을 뒤집기)
    date_columns_reversed = date_columns[::-1]  # 역순으로 정렬
    
    # 새로운 컬럼 순서: 기본 컬럼들 + 시간순 날짜 컬럼들
    final_columns = base_columns + date_columns_reversed
    final_df = filtered_df[final_columns].copy()
    
    print(f"\n최종 데이터 크기: {final_df.shape}")
    print(f"첫 번째 날짜 컬럼 (정렬 후): {final_columns[3] if len(final_columns) > 3 else 'None'}")
    print(f"마지막 날짜 컬럼 (정렬 후): {final_columns[-1] if len(final_columns) > 3 else 'None'}")
    
    # 새로운 CSV 파일로 저장
    final_df.to_csv(output_file, index=False, encoding='euc-kr')
    print(f"\n정리된 데이터가 '{output_file}'에 저장되었습니다.")
    
    return final_df

def analyze_data_issues(df, original_df):
    """
    데이터 정리 전후 비교 분석
    """
    print("\n=== 데이터 정리 결과 분석 ===")
    
    if df is None:
        print("분석할 데이터가 없습니다.")
        return
    
    print(f"원본 데이터: {original_df.shape}")
    print(f"정리된 데이터: {df.shape}")
    
    # 날짜 컬럼들 (3번째 컬럼부터)
    date_columns = df.columns[3:].tolist()
    print(f"\n추출된 기간: {len(date_columns)}개월")
    print(f"시작: {date_columns[0] if date_columns else 'None'}")
    print(f"종료: {date_columns[-1] if date_columns else 'None'}")
    
    # 각 행별 데이터 요약
    print("\n행별 데이터 요약:")
    for i, row in df.iterrows():
        if i < 3:  # 처음 3개 컬럼은 기본 정보
            continue
        row_name = f"{row.iloc[1]} {row.iloc[2]}"  # 분류1 + 분류2
        date_values = row.iloc[3:].values
        non_zero_count = np.count_nonzero(date_values)
        max_value = np.max(date_values) if len(date_values) > 0 else 0
        min_value = np.min(date_values) if len(date_values) > 0 else 0
        
        print(f"  {row_name}: 비영값 {non_zero_count}개, 최대 {max_value:,}, 최소 {min_value}")

def preview_data(df, num_rows=5, num_cols=10):
    if df is None:
        print("미리볼 데이터가 없습니다.")
        return

    
    if len(df.columns) > num_cols:
        print(f"  ... 및 {len(df.columns) - num_cols}개 더")
    
    # 처음 몇 행 표시 (기본 컬럼 + 처음 몇 개 날짜 컬럼만)
    display_cols = list(df.columns[:3]) + list(df.columns[3:3+5])  # 기본 3개 + 날짜 5개
    print(f"\n처음 {num_rows}행 (일부 컬럼만):")
    print(df[display_cols].head(num_rows).to_string())
    
    # 마지막 몇 개 날짜 컬럼
    if len(df.columns) > 8:
        last_display_cols = list(df.columns[:3]) + list(df.columns[-3:])
        print(f"\n마지막 날짜 컬럼들:")
        print(df[last_display_cols].head(num_rows).to_string())

def validate_time_series(df):
    """
    시계열 데이터가 올바르게 정렬되었는지 검증
    """
    print("\n=== 시계열 정렬 검증 ===")
    
    if df is None or len(df.columns) < 4:
        print("검증할 데이터가 없습니다.")
        return
    
    date_columns = df.columns[3:].tolist()
    print(f"날짜 컬럼 수: {len(date_columns)}")
    
    # 첫 10개와 마지막 10개 날짜 컬럼 표시
    print("\n첫 10개 날짜:")
    for i, col in enumerate(date_columns[:10]):
        print(f"  {i+1}: {col}")
    
    if len(date_columns) > 20:
        print("  ...")
        print("마지막 10개 날짜:")
        for i, col in enumerate(date_columns[-10:], len(date_columns)-9):
            print(f"  {i}: {col}")
    
    # 연도별 월 수 확인
    year_counts = {}
    for col in date_columns:
        try:
            if '년' in col and '월' in col:
                year = col.split('년')[0].strip()
                year_counts[year] = year_counts.get(year, 0) + 1
        except:
            continue

    for year in sorted(year_counts.keys()):
        print(f"  {year}년: {year_counts[year]}개월")
    

    

def extract_specific_regions(df, regions, output_file=None):

    if df is None:
        return None
    
    # 분류2 컬럼에서 특정 지역 찾기
    region_column = df.columns[2] if len(df.columns) > 2 else None
    if region_column is None:
        print("지역 컬럼을 찾을 수 없습니다.")
        return None
    
    # 지역별 필터링
    filtered_rows = []
    for region in regions:
        matching_rows = df[df[region_column].str.contains(region, na=False)]
        if not matching_rows.empty:
            filtered_rows.append(matching_rows)
            print(f"'{region}' 관련 {len(matching_rows)}행 찾음")
    
    if filtered_rows:
        result_df = pd.concat(filtered_rows, ignore_index=True)
        if output_file:
            result_df.to_csv(output_file, index=False, encoding='euc-kr')
            print(f"지역별 데이터가 '{output_file}'에 저장되었습니다.")
        return result_df
    else:
        print("해당하는 지역을 찾을 수 없습니다.")
        return None

def create_summary_statistics(df, output_file=None):
    """
    요약 통계 생성
    """
    if df is None or len(df.columns) < 4:
        return None
    
    date_columns = df.columns[3:]
    summary_data = []
    
    for i, row in df.iterrows():
        if i < 3:  # 헤더 행들 건너뛰기
            continue
            
        row_name = f"{row.iloc[1]} {row.iloc[2]}"
        values = row.iloc[3:].values
        
        summary_data.append({
            '지역': row_name,
            '평균': np.mean(values),
            '최대값': np.max(values),
            '최소값': np.min(values),
            '표준편차': np.std(values),
            '비영값_개수': np.count_nonzero(values),
            '최근값_2024_12': values[-1] if len(values) > 0 else 0,
            '초기값_2013_1': values[0] if len(values) > 0 else 0
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    if output_file:
        summary_df.to_csv(output_file, index=False, encoding='euc-kr')
        print(f"요약 통계가 '{output_file}'에 저장되었습니다.")
    
    return summary_df

# 메인 실행 코드
if __name__ == "__main__":
    # 파일 경로 설정
    input_file = '미분양주택현황.csv'
    output_file = 'result/미분양주택현황_정리_2013_2024.csv'
    
    try:
        print("=== 미분양주택현황 데이터 정리 ===")
        
        # 원본 데이터 로드 (분석용)
        original_df = pd.read_csv(input_file, encoding='euc-kr')
        
        # 데이터 처리 실행
        processed_df = process_unsold_housing_data(input_file, output_file)
        
        if processed_df is not None:
            # 결과 분석
            analyze_data_issues(processed_df, original_df)
            
            # 데이터 미리보기
            preview_data(processed_df)
            
            # 시계열 정렬 검증
            validate_time_series(processed_df)

            # 추가 작업 예시 (필요시 주석 해제)
            # print("\n=== 추가 분석 (선택사항) ===")
            # summary_df = create_summary_statistics(processed_df, '미분양_요약통계.csv')
            # region_df = extract_specific_regions(processed_df, ['서울', '경기'], '특정지역_미분양.csv')
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except Exception as e:
        import traceback
        traceback.print_exc()
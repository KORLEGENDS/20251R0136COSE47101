import pandas as pd
import numpy as np

def filter_monthly_apartment_price_data(input_file, output_file):

    
    # CSV 파일 읽기 (인코딩 문제 해결)
    try:
        df = pd.read_csv(input_file, encoding='euc-kr')
    except UnicodeDecodeError:
        # 다른 인코딩으로 시도
        try:
            df = pd.read_csv(input_file, encoding='euc-kr')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='utf-8')

    
    # 컬럼명 확인
    columns = df.columns.tolist()
    
    # 2013년 1월과 2024년 12월의 인덱스 계산
    # 구조: 5개 기본컬럼 + 2003년11월부터 각 월마다 2개컬럼(원자료, 전기대비증감률)
    
    # 2013년 1월 인덱스 계산
    start_index = 5  # 기본 컬럼 5개
    start_index += 2 * 2  # 2003년 11-12월 (2개월 * 2컬럼)
    start_index += 9 * 12 * 2  # 2004-2012년 (9년 * 12개월 * 2컬럼)
    # start_index = 225 (2013년 1월 원자료)
    
    # 2024년 12월 인덱스 계산
    # 2013년 1월부터 2024년 12월까지 = 12년 * 12개월 = 144개월
    end_index = start_index + (12 * 12 * 2) - 2  # 마지막 원자료 컬럼
    # end_index = 511 (2024년 12월 원자료)
    
    # 실제 컬럼명으로 확인
    if start_index < len(columns):
        print(f"시작 컬럼명: {columns[start_index]}")
    if end_index < len(columns):
        print(f"종료 컬럼명: {columns[end_index]}")
    
    # 기본 컬럼들 (No, 분류 등) 유지
    base_columns = columns[:5]  # 처음 5개 컬럼
    
    # 원자료 컬럼들만 선택 (홀수 인덱스에서 시작하여 2씩 증가)
    selected_columns = base_columns.copy()
    selected_date_columns = []
    
    # start_index부터 end_index까지 2씩 증가하여 원자료만 선택
    for i in range(start_index, end_index + 1, 2):
        if i < len(columns):
            selected_columns.append(columns[i])
            selected_date_columns.append(columns[i])

    
    # 선택된 컬럼들로 새로운 DataFrame 생성
    try:
        filtered_df = df[selected_columns].copy()
        print(f"필터링된 데이터 크기: {filtered_df.shape}")
    except KeyError as e:
        print("사용 가능한 컬럼 수:", len(columns))
        return None
    
    # 새로운 CSV 파일로 저장
    filtered_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return filtered_df


def analyze_data_coverage(df):
    """
    데이터 커버리지 분석
    """
    print("\n=== 데이터 커버리지 분석 ===")
    
    # 날짜 컬럼들 (5번째 컬럼부터)
    date_columns = df.columns[5:].tolist()
    
    if date_columns:
        print(f"데이터 기간: {date_columns[0]} ~ {date_columns[-1]}")
        print(f"총 월 수: {len(date_columns)}개월")
        
        # 연도별 월 수 계산
        years = {}
        for date_col in date_columns:
            try:
                # "2013년 1월" 형식에서 연도 추출
                if '년' in date_col:
                    year = date_col.split('년')[0].strip()
                    years[year] = years.get(year, 0) + 1
            except:
                continue
        
        print("\n연도별 월 수:")
        for year, count in sorted(years.items()):
            print(f"  {year}년: {count}개월")
        
        # 2013년부터 2024년까지 144개월이 있는지 확인
        expected_months = 12 * 12  # 12년 * 12개월
        print(f"\n예상 월 수: {expected_months}개월")
        print(f"실제 월 수: {len(date_columns)}개월")
        if len(date_columns) == expected_months:
            print("✅ 모든 월 데이터가 포함되었습니다.")
        else:
            print(f"⚠️ {expected_months - len(date_columns)}개월 차이가 있습니다.")
    
    # 결측값 확인
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        print(f"\n결측값 총 개수: {missing_data.sum()}")
        print("컬럼별 결측값:")
        for col, missing in missing_data.items():
            if missing > 0:
                print(f"  {col}: {missing}개")
    else:
        print("\n결측값 없음")

def validate_column_pattern(input_file):
    """
    컬럼 패턴이 올바른지 검증
    """
    print("\n=== 컬럼 패턴 검증 ===")
    
    try:
        df = pd.read_csv(input_file, encoding='cp1252')
        columns = df.columns.tolist()
        
        # 3행에서 원자료/전기대비증감률 패턴 확인
        if len(df) >= 3:
            third_row = df.iloc[2].tolist()
            
            # 2013년 1월 위치부터 확인
            start_idx = 225
            print(f"인덱스 {start_idx} 주변 패턴:")
            for i in range(start_idx - 2, start_idx + 8, 2):
                if i < len(third_row) and i + 1 < len(third_row):
                    print(f"  {i}: {third_row[i]} (원자료)")
                    print(f"  {i+1}: {third_row[i+1]} (전기대비증감률)")
        
    except Exception as e:
        print(f"검증 중 오류: {e}")

# 메인 실행 코드
if __name__ == "__main__":
    # 파일 경로 설정
    input_file = '../data/transactions/(월) 매매가격지수_아파트.csv'
    output_file = 'result/d.csv'
    
    try:
        # 컬럼 패턴 검증
        validate_column_pattern(input_file)
        
        # 데이터 필터링 실행
        filtered_df = filter_monthly_apartment_price_data(input_file, output_file)
        
        if filtered_df is not None:

            # 데이터 커버리지 분석
            analyze_data_coverage(filtered_df)

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


# 실행 예시
if __name__ == "__main__":

    pass
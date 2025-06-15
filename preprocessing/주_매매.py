import pandas as pd
import numpy as np

def filter_housing_price_data(input_file, output_file):
    try:
        df = pd.read_csv(input_file, encoding='euc-kr')
    except UnicodeDecodeError:
        # 다른 인코딩으로 시도
        try:
            df = pd.read_csv(input_file, encoding='euc-kr')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='utf-8')
    
    print(f"원본 데이터 크기: {df.shape}")
    print(f"컬럼 수: {len(df.columns)}")
    
    # 컬럼명 확인
    columns = df.columns.tolist()
    
    # 2013-01-07과 2024-12-30의 인덱스 찾기
    start_index = None
    end_index = None
    
    for i, col in enumerate(columns):
        if col == '2013-01-07':
            start_index = i
        if col == '2024-12-30':
            end_index = i
    
    if start_index is None:
        raise ValueError("2013-01-07 컬럼을 찾을 수 없습니다.")
    if end_index is None:
        raise ValueError("2024-12-30 컬럼을 찾을 수 없습니다.")
    
    
    # 기본 컬럼들 (No, 분류 등) 유지
    base_columns = columns[:5]  # 처음 5개 컬럼 (No, 분류1, 분류2, 분류3, 분류4)
    
    # 원자료 컬럼들만 선택 (홀수 인덱스 = 원자료)
    selected_columns = base_columns.copy()
    selected_date_columns = []
    
    # start_index부터 end_index까지 홀수 인덱스만 선택
    for i in range(start_index, end_index + 1, 2):  # 2씩 증가 (홀수 인덱스)
        if i < len(columns):
            selected_columns.append(columns[i])
            selected_date_columns.append(columns[i])

    
    # 선택된 컬럼들로 새로운 DataFrame 생성
    filtered_df = df[selected_columns].copy()
    
    
    # 새로운 CSV 파일로 저장
    filtered_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return filtered_df


# 메인 실행 코드
if __name__ == "__main__":
    # 파일 경로 설정
    input_file = '../data/transactions/(주) 매매가격지수.csv'
    output_file = 'result/주별_매매가_추출.csv'
    
    try:
        # 데이터 필터링 실행
        filtered_df = filter_housing_price_data(input_file, output_file)


    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {input_file}")
    except Exception as e:
        import traceback
        traceback.print_exc()

import pandas as pd
import os

def extract_apartment_trade_data(input_file, output_file):

    
    # 다양한 인코딩으로 파일 읽기 시도
    encodings = ['euc-kr', 'cp949', 'utf-8', 'utf-8-sig']
    df = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding, header=None)
            used_encoding = encoding
            break
        except Exception as e:
            print(f"{encoding} 실패: {e}")
            continue
    
    if df is None:
        raise ValueError("파일을 읽을 수 없습니다.")

    
    # 1행 헤더에서 2013년 1월과 2024년 12월 컬럼 위치 찾기
    header_row = df.iloc[0]
    
    start_col_idx = None
    end_col_idx = None
    
    # 2013년 1월 컬럼 찾기
    start_col_idx = next(
        (i for i, col_name in enumerate(header_row)
         if pd.notna(col_name) and str(col_name).strip() == '2013년 1월'),
        None  # 없을 경우 반환할 기본값
    )

    if start_col_idx is not None:
        print(f"2013년 1월 컬럼 인덱스: {start_col_idx}")
    else:
        print("2013년 1월 컬럼을 찾을 수 없습니다.")

    
    # 2024년 12월 컬럼 찾기 (마지막 것을 찾기 위해 역순으로)
    for i in range(len(header_row)-1, -1, -1):
        col_name = header_row.iloc[i]
        if pd.notna(col_name) and str(col_name).strip() == '2024년 12월':
            end_col_idx = i
            print(f"2024년 12월 컬럼 인덱스: {i}")
            break
    
    if start_col_idx is None or end_col_idx is None:
        # 수동으로 컬럼 인덱스 설정 (분석 결과 기반)
        start_col_idx = 172  # 2013년 1월
        end_col_idx = 459    # 2024년 12월
    
    # 2번째 행에서 '동(호)수' 패턴을 가진 컬럼들 찾기
    second_row = df.iloc[1]  # 2번째 행 (0-indexed)
    dong_ho_cols = []
    
    for col_idx in range(start_col_idx, end_col_idx + 1):
        if col_idx < len(second_row):
            cell_value = second_row.iloc[col_idx]
            if pd.notna(cell_value):
                cell_str = str(cell_value)
                # '동(호)수' 패턴 확인
                if '동' in cell_str and ('호' in cell_str or '수' in cell_str):
                    dong_ho_cols.append(col_idx)
                # 또는 정확한 패턴 매칭
                elif cell_str.strip() == '동(호)수':
                    dong_ho_cols.append(col_idx)
    
    # 최종 선택할 컬럼들
    # A, B, C, D열 (인덱스 0, 1, 2, 3) + 동(호)수 컬럼들
    basic_cols = [0, 1, 2, 3]  # A, B, C, D열
    final_cols = basic_cols + dong_ho_cols
    
    # 데이터 추출
    extracted_df = df.iloc[:, final_cols].copy()

    
    # 숫자 데이터 정리 (헤더 3행은 그대로 유지, 4행부터 숫자 변환)
    basic_cols = [0, 1, 2, 3]  # A, B, C, D열
    cleaned_df = clean_numeric_data(extracted_df, basic_cols)
    
    # 출력 디렉토리 생성
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # CSV 파일로 저장
    try:
        cleaned_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"실패: {e}")
        try:
            cleaned_df.to_csv(output_file, index=False, header=False, encoding='euc-kr')
            print(f"저장 완료: {output_file}")
        except Exception as e2:
            print(f"저장 실패: {e2}")
            raise
    
    return cleaned_df


def clean_numeric_data(df, basic_cols):

    print("숫자 데이터 정리 시작...")
    
    # 복사본 생성
    cleaned_df = df.copy()
    
    print(f"데이터프레임 크기: {cleaned_df.shape}")
    print(f"기본 컬럼들: {basic_cols}")
    print(f"전체 컬럼 수: {len(cleaned_df.columns)}")
    
    # 데이터프레임이 너무 작으면 변환하지 않음
    if len(cleaned_df) < 4:
        print("데이터가 너무 적어 숫자 변환을 건너뜁니다.")
        return cleaned_df
    
    # 기본 컬럼 인덱스들을 실제 컬럼 인덱스로 변환
    actual_basic_cols = []
    for i, col_idx in enumerate(basic_cols):
        if col_idx < len(cleaned_df.columns):
            actual_basic_cols.append(col_idx)
        else:
            print(f"기본 컬럼 인덱스 {col_idx}가 범위를 벗어남")
    
    # 기본 컬럼 제외한 나머지 컬럼들 (숫자 데이터 컬럼들)
    all_col_indices = list(range(len(cleaned_df.columns)))
    numeric_col_indices = [col for col in all_col_indices if col not in actual_basic_cols]
    
    print(f"정리할 숫자 컬럼 수: {len(numeric_col_indices)}")
    
    for col_idx_num, col_idx in enumerate(numeric_col_indices):
        try:
            # 컬럼 인덱스가 유효한지 확인
            if col_idx >= len(cleaned_df.columns):
                print(f"컬럼 인덱스 {col_idx}가 범위를 벗어남")
                continue
            
            # 4행부터 데이터가 있는지 확인
            if len(cleaned_df) <= 3:
                print(f"데이터 행이 부족함: {len(cleaned_df)}행")
                continue
            
            # 4행부터의 데이터만 선택 (인덱스 3부터)
            # 안전한 방식으로 컬럼에 접근
            col_name = cleaned_df.columns[col_idx]
            data_rows = cleaned_df.loc[3:, col_name].copy()
            
            # 데이터가 없으면 건너뜀
            if len(data_rows) == 0:
                continue
            
            # 문자열로 변환
            data_rows = data_rows.astype(str)
            
            # 다양한 따옴표 패턴 제거
            data_rows = data_rows.str.replace('"""', '', regex=False)
            data_rows = data_rows.str.replace('""', '', regex=False)
            data_rows = data_rows.str.replace('"', '', regex=False)
            data_rows = data_rows.str.replace("'", '', regex=False)
            
            # 콤마 제거 (천단위 구분자)
            data_rows = data_rows.str.replace(',', '', regex=False)
            
            # 공백 제거
            data_rows = data_rows.str.strip()
            
            # 빈 문자열이나 'nan' 등을 0으로 변환
            data_rows = data_rows.replace(['', 'nan', 'None', 'null', 'NaN'], '0')
            
            # 숫자가 아닌 값들을 0으로 변환 후 정수형으로 변환
            data_rows = pd.to_numeric(data_rows, errors='coerce').fillna(0).astype(int)
            
            # 헤더 부분은 그대로 유지하고 4행부터만 변환된 데이터로 교체
            cleaned_df.loc[3:, col_name] = data_rows
            
            if col_idx_num % 50 == 0 and col_idx_num > 0:  # 50개마다 진행상황 출력
                print(f"진행상황: {col_idx_num}/{len(numeric_col_indices)} 컬럼 처리 완료")
                
        except Exception as e:
            print(f"컬럼 인덱스 {col_idx} 변환 중 오류 발생: {e}")
            # 오류 발생 시 원본 데이터 유지
            continue
    
    print("숫자 데이터 정리 완료!")
    
    # 변환 결과 확인
    if len(numeric_col_indices) > 0 and len(cleaned_df.columns) > max(actual_basic_cols):
        try:
            sample_col_idx = numeric_col_indices[0]
            sample_col_name = cleaned_df.columns[sample_col_idx]
            print(f"변환 예시 (컬럼 인덱스 {sample_col_idx}):")
            if len(cleaned_df) >= 3:
                print(f"헤더 부분 (1~3행) 유지: {cleaned_df.iloc[0:3, sample_col_idx].tolist()}")
            if len(cleaned_df) > 3:
                end_idx = min(8, len(cleaned_df))
                print(f"데이터 부분 (4행부터) 변환: {cleaned_df.iloc[3:end_idx, sample_col_idx].tolist()}")
        except Exception as e:
            print(f"샘플 출력 중 오류: {e}")
    
    return cleaned_df


def analyze_file_structure(input_file):

    
    # 파일 읽기
    encodings = ['euc-kr', 'cp949', 'utf-8']
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding, header=None)
            break
        except:
            continue
    
    print(f"파일 크기: {df.shape}")
    
    # 헤더 행들 출력
    for i in range(min(3, len(df))):
        print(f"\n{i+1}행:")
        row_data = df.iloc[i]
        print(f"  A~D열: {row_data.iloc[0:4].tolist()}")
        print(f"  E~J열: {row_data.iloc[4:10].tolist()}")
    
    # 2013년, 2024년 컬럼 찾기
    header_row = df.iloc[0]
    for i, col in enumerate(header_row):
        if pd.notna(col):
            col_str = str(col).strip()
            if '2013년 1월' in col_str or '2024년 12월' in col_str:
                print(f"컬럼 {i}: {col_str}")
    
    # 2번째 행에서 '동(호)수' 패턴 분석
    print(f"\n2번째 행 '동(호)수' 패턴 분석:")
    second_row = df.iloc[1]
    dong_ho_count = 0
    for i in range(4, min(20, len(second_row))):  # E열부터 20개만 확인
        cell_value = str(second_row.iloc[i]).strip()
        if '동' in cell_value and ('호' in cell_value or '수' in cell_value):
            dong_ho_count += 1
            print(f"  컬럼 {i}: '{cell_value}'")
    print(f"  총 '동(호)수' 패턴 발견: {dong_ho_count}개")


def main():

    input_file = "../data/transactions/(월) 행정구역별 아파트매매거래현황.csv"
    output_file = "result/신도시 지역 아파트매매거래현황.csv"
    
    try:
        # 파일 구조 분석 (옵션)
        # analyze_file_structure(input_file)
        
        # 데이터 추출 실행
        result_df = extract_apartment_trade_data(input_file, output_file)
        display_df = result_df.head()
        for i, (idx, row) in enumerate(display_df.iterrows()):
            print(f"{i+1}행: A~D열: {row.iloc[0:4].tolist()}, E~H열: {row.iloc[4:8].tolist()}")
        
        if len(result_df) > 5:
            print(f"\n마지막 2행:")
            tail_df = result_df.tail(2)
            for i, (idx, row) in enumerate(tail_df.iterrows()):
                print(f"마지막{2-i}행: A~D열: {row.iloc[0:4].tolist()}, E~H열: {row.iloc[4:8].tolist()}")

        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

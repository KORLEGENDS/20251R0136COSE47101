import pandas as pd
import re

def extract_apartment_data(input_file, output_file):

    
    # 다양한 인코딩으로 파일 읽기 시도
    encodings = ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding, header=None)
            print(f"파일을 {encoding} 인코딩으로 성공적으로 읽었습니다.")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"{encoding} 인코딩 시도 중 오류: {e}")
            continue
    
    if df is None:
        raise ValueError("파일을 읽을 수 없습니다. 인코딩을 확인해주세요.")
    
    print(f"원본 데이터 shape: {df.shape}")
    print(f"전체 행 수: {len(df)}")
    
    # 2번 행(인덱스 1) 확인
    if len(df) < 2:
        raise ValueError("파일에 충분한 행이 없습니다.")
    
    second_row = df.iloc[1]  # 2번 행 (0-indexed)
    print(f"2번 행 샘플: {second_row.iloc[4:10].tolist()}")  # 4~9 컬럼 샘플
    
    # 2013년 1월부터 2024년 12월까지의 컬럼 범위 찾기
    header_row = df.iloc[0]  # 1번 행 (헤더)
    
    # 2013년 1월 컬럼 찾기
    start_col_idx = None
    end_col_idx = None
    
    for i, col_name in enumerate(header_row):
        if pd.notna(col_name):
            col_str = str(col_name)
            # 2013년 1월 패턴 찾기
            if '2013' in col_str and '1' in col_str:
                start_col_idx = i
                break
    
    # 2024년 12월 컬럼 찾기
    for i in range(len(header_row)-1, -1, -1):
        col_name = header_row.iloc[i]
        if pd.notna(col_name):
            col_str = str(col_name)
            # 2024년 12월 패턴 찾기
            if '2024' in col_str and '12' in col_str:
                end_col_idx = i
                break
    
    if start_col_idx is None or end_col_idx is None:
        # 2006년부터 시작한다면 2013년은 대략 (2013-2006)*24 + 4 위치
        start_col_idx = 4 + (2013-2006)*24
        end_col_idx = 4 + (2024-2006)*24 + 23  # 2024년 12월까지
        
        # 실제 컬럼 수를 넘지 않도록 조정
        end_col_idx = min(end_col_idx, df.shape[1] - 1)
    
    print(f"2013년 1월 컬럼 인덱스: {start_col_idx}")
    print(f"2024년 12월 컬럼 인덱스: {end_col_idx}")
    
    # 2번 행에서 '동(호)수' 패턴을 가진 컬럼들 찾기
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
    
    print(f"최종 선택된 컬럼 수: {len(final_cols)}")
    
    # 모든 행 유지 (헤더와 데이터 모두)
    extracted_df = df.iloc[:, final_cols].copy()
    
    print(f"추출된 데이터 shape: {extracted_df.shape}")
    
    # 숫자 데이터 정리 (따옴표 제거 및 숫자 변환) - 4행부터만 적용
    extracted_df = clean_numeric_data(extracted_df, basic_cols)
    
    # CSV 파일로 저장
    try:
        extracted_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')
    except Exception as e:
        # 대안으로 cp949 인코딩 시도
        try:
            extracted_df.to_csv(output_file, index=False, header=False, encoding='cp949')
        except Exception as e2:
            print(f"cp949 인코딩 실패: {e2}")
    
    return extracted_df


def clean_numeric_data(df, basic_cols):

    
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
    
    # 변환 결과 샘플 출력
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


def main():
    """
    메인 실행 함수
    """
    input_file = "(월) 행정구역별 아파트거래현황.csv"  # 입력 파일명
    output_file = "result/추출된_아파트거래현황_2013-2024.csv"  # 출력 파일명
    
    try:
        result_df = extract_apartment_data(input_file, output_file)

        if len(result_df) > 5:
            print(f"\n마지막 5행:")
            print(result_df.tail())
            
    except Exception as e:
        print(f"오류 발생: {e}")
        
        # 대안: 수동으로 컬럼 범위 지정
        try:
            df = pd.read_csv(input_file, encoding='cp949', header=None)
            
            # 2013년 1월(FQ)부터 2024년 12월(QQ)까지 대략적 컬럼 범위
            # 실제 파일 구조에 따라 조정 필요
            start_col = 4 + (2013-2006)*24 + (1-1)*2  # 대략적 계산
            end_col = 4 + (2024-2006)*24 + (12-1)*2   # 대략적 계산
            
            basic_cols = [0, 1, 2, 3]  # No, 시도, 시군구, 읍면동
            target_cols = basic_cols + list(range(start_col, min(end_col+1, df.shape[1])))
            
            # 헤더 3행 + 실제 데이터 행 추출
            result_df = df.iloc[:, target_cols]
            
            result_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')
            print(f"대안 방법으로 데이터 추출 완료: {output_file}")
            
        except Exception as e2:
            print(f"대안 방법도 실패: {e2}")


def alternative_method(input_file, output_file):
    try:
        # 인코딩 시도
        for encoding in ['cp949', 'euc-kr', 'utf-8']:
            try:
                df = pd.read_csv(input_file, encoding=encoding, header=None)
                break
            except:
                continue
        
        print(f"대안 방법 - 파일 shape: {df.shape}")
        
        # 수동으로 2013년 1월부터 2024년 12월까지 컬럼 계산
        # 2006년부터 시작한다고 가정하고, 매년 24컬럼(월별 2개씩)
        base_col = 4  # A, B, C, D 다음부터
        start_year_offset = (2013 - 2006) * 24  # 2013년까지의 오프셋
        end_year_offset = (2024 - 2006) * 24 + 23  # 2024년 12월까지
        
        start_col = base_col + start_year_offset
        end_col = base_col + end_year_offset
        
        # 실제 컬럼 수에 맞게 조정
        end_col = min(end_col, df.shape[1] - 1)
        
        print(f"추정 컬럼 범위: {start_col} ~ {end_col}")
        
        # 2번 행에서 '동(호)수' 컬럼들 찾기
        second_row = df.iloc[1]
        dong_ho_cols = []
        
        for col_idx in range(start_col, end_col + 1):
            if col_idx < len(second_row):
                cell_value = str(second_row.iloc[col_idx])
                if '동' in cell_value and ('호' in cell_value or '수' in cell_value):
                    dong_ho_cols.append(col_idx)
        
        # 패턴이 잘 안 잡히면 모든 홀수 컬럼 선택 (동(호)수가 보통 홀수 컬럼에 위치)
        if len(dong_ho_cols) < 10:
            dong_ho_cols = [i for i in range(start_col, end_col + 1, 2)]
        
        print(f"선택된 동(호)수 컬럼 수: {len(dong_ho_cols)}")
        
        # A, B, C, D + 동(호)수 컬럼들
        final_cols = [0, 1, 2, 3] + dong_ho_cols
        result_df = df.iloc[:, final_cols]
        
        # 숫자 데이터 정리 (헤더 부분 보존)
        result_df = clean_numeric_data(result_df, [0, 1, 2, 3])
        
        # 저장
        result_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')
        print(f"대안 방법으로 저장 완료: {output_file}")
        
        return result_df
        
    except Exception as e:
        print(f"대안 방법 실패: {e}")
        return None


if __name__ == "__main__":
    # 메인 방법 시도
    try:
        main()
    except Exception as e:
        alternative_method("(월) 행정구역별 아파트거래현황.csv", "result/추출된_아파트거래현황_2013-2024.csv")
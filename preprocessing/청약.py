import pandas as pd
import re

def split_date_column(input_file, output_file):
    
    # CSV 파일 읽기 (인코딩 문제 대응)
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(input_file, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='euc-kr')

    
    date_column = None
    for col in df.columns:
        if '연월' in col or '¿¬¿ù' in col:
            date_column = col
            break
    
    if date_column is None:
        # 첫 번째 컬럼이 날짜 컬럼이라고 가정
        date_column = df.columns[0]
    else:
        print(f"연월 컬럼 발견: {date_column}")
    
    def parse_date(date_str):
        """
        다양한 날짜 형식을 파싱하는 함수
        """
        if pd.isna(date_str):
            return None, None
            
        date_str = str(date_str).strip()
        
        # 1. YYYY-MM 형식 (예: 2020-02)
        if re.match(r'^\d{4}-\d{2}$', date_str):
            year, month = date_str.split('-')
            return int(year), int(month)
        
        # 2. MMM-YY 형식 (예: Feb-23)
        elif re.match(r'^[A-Za-z]{3}-\d{2}$', date_str):
            month_str, year_str = date_str.split('-')
            
            # 월 이름을 숫자로 변환
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = month_map.get(month_str.capitalize(), None)
            if month is None:
                print(f"알 수 없는 월 형식: {month_str}")
                return None, None
            
            # 2자리 연도를 4자리로 변환 (23 -> 2023)
            year = int('20' + year_str) if int(year_str) < 50 else int('19' + year_str)
            
            return year, month
        
        # 3. MM-YYYY 형식 (예: 02-2020)
        elif re.match(r'^\d{2}-\d{4}$', date_str):
            month, year = date_str.split('-')
            return int(year), int(month)
        
        else:
            print(f"지원하지 않는 날짜 형식: {date_str}")
            return None, None
    
    # 연도와 월 컬럼 생성
    df[['연도', '월']] = df[date_column].apply(
        lambda x: pd.Series(parse_date(x))
    )
    
    # 원본 연월 컬럼을 삭제하고 연도, 월 컬럼을 앞쪽으로 이동
    columns = ['연도', '월'] + [col for col in df.columns if col not in ['연도', '월', date_column]]
    df_new = df[columns].copy()
    

    # 새로운 CSV 파일로 저장
    df_new.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return df_new


if __name__ == "__main__":
    input_filename = "../data/competition/한국부동산원_지역별 청약 경쟁률 정보_20250430.csv"
    output_filename = "result/한국부동산원_지역별 청약 경쟁률 정보_분리된날짜.csv"
    
    # 함수 실행
    result_df = split_date_column(input_filename, output_filename)

import pandas as pd

def split_monthly_column():
    """
    월(Monthly) 컬럼을 연도와 월 2개 컬럼으로 분리하는 함수
    """
    
    # 월 이름 매핑 (영어 → 숫자)
    month_mapping = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    # CSV 파일 읽기
    df = pd.read_csv('전국_미분양주택현황.csv', encoding='utf-8')
    
    print(f"원본 데이터: {len(df)}행")
    print(f"컬럼: {list(df.columns)}")
    print(f"월(Monthly) 샘플: {df['월(Monthly)'].head().tolist()}")
    
    # 현재 형태가 YYYY-MM인지 Mon-YY인지 확인
    sample_value = df['월(Monthly)'].iloc[0]
    print(f"\n샘플 값: {sample_value}")
    
    if '-' in sample_value:
        parts = sample_value.split('-')
        
        # YYYY-MM 형태인 경우
        if len(parts[0]) == 4 and parts[0].isdigit():
            print("YYYY-MM 형태 감지")
            df['연도'] = df['월(Monthly)'].str[:4].astype(int)
            df['월'] = df['월(Monthly)'].str[5:7].astype(int)
            
        # Mon-YY 형태인 경우 (예: Jan-13)
        elif parts[0] in month_mapping:
            print("Mon-YY 형태 감지")
            
            def parse_monthly(monthly_str):
                month_str, year_str = monthly_str.split('-')
                month_num = month_mapping[month_str]
                
                # 2자리 연도를 4자리로 변환 (13 → 2013)
                year_num = int(year_str)
                if year_num < 50:  # 00-49는 2000년대
                    year_num += 2000
                else:  # 50-99는 1900년대
                    year_num += 1900
                
                return year_num, month_num
            
            # 연도와 월 분리
            parsed_data = df['월(Monthly)'].apply(parse_monthly)
            df['연도'] = [x[0] for x in parsed_data]
            df['월'] = [x[1] for x in parsed_data]
        
        else:
            print("알 수 없는 형태입니다.")
            return None
    
    # 컬럼 순서 재정렬: 연도, 월, 구분, 시군구, 미분양현황
    df_final = df[['연도', '월', '구분', '시군구', '미분양현황']].copy()
    
    # 연도, 월 순으로 정렬
    df_final = df_final.sort_values(['연도', '월', '구분', '시군구'])
    
    # 새 파일로 저장
    output_file = 'result/전국_미분양주택현황.csv'
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n완료!")
    print(f"출력 파일: {output_file}")
    print(f"총 행 수: {len(df_final)}")
    print(f"기간: {df_final['연도'].min()}년 {df_final['월'].min()}월 ~ {df_final['연도'].max()}년 {df_final['월'].max()}월")
    
    # 결과 미리보기
    print("\n데이터 미리보기:")
    print(df_final.head(10))
    
    # 연도별 데이터 수 확인
    print("\n연도별 데이터 수:")
    yearly_counts = df_final.groupby('연도').size()
    for year, count in yearly_counts.items():
        print(f"  {year}년: {count:,}행")
    
    return df_final

# 실행
if __name__ == "__main__":
    result = split_monthly_column()
import pandas as pd

# 파일 경로 설정
file1_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\고양일산\일산동구_06_24.csv'
file2_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\고양일산\일산서구_06_24.csv'

# 필요한 열 목록
columns_to_keep = ['NO', '시군구', '단지명', '도로명', '전용면적(㎡)', '계약년월', '계약일', '거래금액(만원)', '건축년도']

try:
    # CSV 파일 읽기 (cp949 인코딩)
    df1 = pd.read_csv(file1_path, encoding='utf-8')
    df2 = pd.read_csv(file2_path, encoding='utf-8')
    
    # 필요한 열만 선택
    df1_filtered = df1[columns_to_keep].copy()
    df2_filtered = df2[columns_to_keep].copy()
    
    # 두 데이터프레임 통합
    combined_df = pd.concat([df1_filtered, df2_filtered], ignore_index=True)
    
    # 계약년월이 201301 이상인 데이터만 필터링
    print(f"필터링 전 데이터: {len(combined_df)}행")
    combined_df = combined_df[combined_df['계약년월'] >= 201301]
    print(f"필터링 후 데이터: {len(combined_df)}행 (계약년월 >= 201301)")
    
    # NaN 값이 있는 경우를 대비한 추가 필터링
    combined_df = combined_df.dropna(subset=['계약년월'])
    
    # 통합된 파일 저장
    output_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\result\일산통합_06_24.csv'
    combined_df.to_csv(output_path, encoding='cp949', index=False)
    print(f"통합 파일 저장 완료: {output_path}")


except FileNotFoundError as e:
    print(f"파일을 찾을 수 없습니다: {e}")
except UnicodeDecodeError as e:
    print(f"인코딩 오류 발생 {e}")
except Exception as e:
    print(f"오류 발생 {e}")
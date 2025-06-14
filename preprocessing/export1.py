import pandas as pd

# 파일 경로 설정
file_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\성남수정구_위례\성남수정구_위례.csv'

# 필요한 열 목록
columns_to_keep = ['NO', '시군구', '단지명', '도로명', '전용면적(㎡)', '계약년월', '계약일', '거래금액(만원)', '건축년도']

try:
    # CSV 파일 읽기 (cp949 인코딩)
    print("하남교산 파일 읽는 중...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"하남교산: {len(df)}행 로드됨")
    
    # 필요한 열만 선택
    df_filtered = df[columns_to_keep].copy()
    
    # 계약년월이 201301 이상인 데이터만 필터링
    print(f"필터링 전 데이터: {len(df_filtered)}행")
    df_filtered = df_filtered[df_filtered['계약년월'] >= 201301]
    print(f"필터링 후 데이터: {len(df_filtered)}행 (계약년월 >= 201301)")
    
    # NaN 값이 있는 경우를 대비한 추가 필터링
    df_filtered = df_filtered.dropna(subset=['계약년월'])

    # 추출된 파일 저장
    output_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\result\성남수정구_위례_13_24.csv'
    df_filtered.to_csv(output_path, encoding='cp949', index=False)
    


except FileNotFoundError as e:
    print(f"파일을 찾을 수 없습니다: {e}")
except UnicodeDecodeError as e:
    print(f"인코딩 오류 발생: {e}")
except Exception as e:
    print(f"오류가 발생: {e}")
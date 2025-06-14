import pandas as pd

# 파일 경로 설정
file_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\result\1차 통합\하남통합_13_24.csv'

try:
    # CSV 파일 읽기 (cp949 인코딩)
    print("송파통합 파일 읽는 중...")
    df = pd.read_csv(file_path, encoding='cp949')
    print(f"송파통합: {len(df)}행 로드됨")
    
    # 열 정보 확인 (인코딩 문제로 열명이 깨져 보일 수 있음)
    print(f"현재 열명: {list(df.columns)}")
    
    # 필터링 전 데이터 개수
    print(f"필터링 전 총 데이터: {len(df)}행")
    
    # 조건 1: 시군구에 '장지동' 또는 '거여동' 포함
    condition1 = df.iloc[:, 1].str.contains('구래동|마산동|장기동|운양동', na=False)

    
    # 조건 2: 도로명에 '위례' 포함
    condition2 = df.iloc[:, 3].str.contains('김포한강', na=False)

    
    # 두 조건을 모두 만족하는 데이터 필터링 (AND 조건)
    filtered_df = df[condition1 & condition2].copy()

    
    if len(filtered_df) > 0:
        # 필터링된 파일 저장
        output_path = r'C:\Users\Winyu\Downloads\데이터과학\텀프\result\분당.csv'
        filtered_df.to_csv(output_path, encoding='cp949', index=False)
        print(f"추출된 파일 저장 완료: {output_path}")


    else:
        print("조건에 맞는 데이터가 없습니다.")
        print("\n시군구 고유값 확인:")
        print(df.iloc[:, 1].unique()[:20])  # 처음 20개만 출력
        print("\n도로명에서 '위례' 검색 결과:")
        wirye_roads = df[df.iloc[:, 3].str.contains('판교', na=False)]
        if len(wirye_roads) > 0:
            print(wirye_roads.iloc[:, 3].unique()[:10])
        else:
            print("위례가 포함된 도로명이 없습니다.")

except FileNotFoundError as e:
    print(f"파일을 찾을 수 없습니다: {e}")
except UnicodeDecodeError as e:
    print(f"인코딩 오류 발생 {e}")
except Exception as e:
    print(f"오류 발생 {e}")
    
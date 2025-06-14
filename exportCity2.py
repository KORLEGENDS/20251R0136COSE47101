import pandas as pd

# CSV 파일을 cp949 인코딩으로 읽기
df = pd.read_csv('result/도로명주소 추가/서울_경기_통합아파트_데이터_변환완료.csv', encoding='utf-8')

# 추출할 법정동 리스트
target_dongs = ['구래동', '마산동', '장기동', '운양동']

# 조건 1: 법정동주소 열에서 해당 동들을 포함하는 행
condition1 = df['법정동주소'].str.contains('|'.join(target_dongs), na=False)

# 조건 2: 도로명주소 열에서 '판교'를 포함하는 행
condition2 = df['도로명주소'].str.contains('김포한강', na=False)

# 두 조건을 AND로 결합하여 필터링
filtered_df = df[condition1 & condition2]

# 결과를 새로운 CSV 파일로 저장
filtered_df.to_csv('result/판교지역_아파트_데이터.csv', index=False, encoding='cp949')



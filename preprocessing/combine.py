import pandas as pd

# CSV 파일들을 cp949 인코딩으로 읽기
df1 = pd.read_csv('result/위례_하남.csv', encoding='cp949')
df2 = pd.read_csv('result/위례_송파.csv', encoding='cp949')
df3 = pd.read_csv('result/위례_성남.csv', encoding='cp949')

# 두 데이터프레임 통합
combined_df = pd.concat([df1, df2, df3], ignore_index=True)

# NO 열 삭제
if 'NO' in combined_df.columns:
    combined_df = combined_df.drop('NO', axis=1)

# 계약년월 오름차순, 계약년월이 같으면 계약일 오름차순으로 정렬
combined_df = combined_df.sort_values(['계약년월', '계약일'], ascending=[True, True])

# 인덱스 재설정
combined_df = combined_df.reset_index(drop=True)

# 결과를 새로운 CSV 파일로 저장 (cp949 인코딩)
combined_df.to_csv('result/위례_통합.csv', index=False, encoding='cp949')
import pymysql

# DB 연결 설정
connection = pymysql.connect(
    host="localhost",       # DB 호스트
    user="root",            # 사용자 이름
    password="",    # 비밀번호
    database="tails_route_test"  # 데이터베이스 이름
)

print("DB 연결 성공!")

try:
    with connection.cursor() as cursor:
        # SELECT COUNT 쿼리 실행
        query = "SELECT COUNT(*) FROM hospital;"
        cursor.execute(query)
        result = cursor.fetchone()  # 결과 가져오기
        print(f"병원 데이터 개수: {result[0]}")  # 첫 번째 컬럼 값 출력
finally:
    connection.close()  # 연결 종료
    print("DB 연결이 종료되었습니다.")


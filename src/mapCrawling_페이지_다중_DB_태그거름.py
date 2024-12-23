from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pymysql

# ChromeDriver 경로 설정
chrome_driver_path = "../driver/chromedriver.exe"

# Chrome 옵션 설정
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36")

# Chrome WebDriver 초기화
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 네이버 지도 열기
driver.get("https://map.naver.com/v5/")
print("페이지가 로드될 때까지 기다리겠습니다.")

# 페이지가 완전히 로드될 때까지 기다림
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search")))
    print("페이지가 로드되었습니다.")
except Exception as e:
    print("페이지가 로드되지 않았습니다:", e)
    driver.quit()
    exit()


# 프레임 전환 함수 정의
def switch_to_default_content():
    driver.switch_to.default_content()
    print("기본 프레임으로 전환했습니다.")


def switch_to_search_iframe():
    driver.switch_to.default_content()
    search_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
    )
    driver.switch_to.frame(search_iframe)
    print("검색 결과 iframe으로 전환했습니다.")


def switch_to_entry_iframe():
    driver.switch_to.default_content()
    entry_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
    )
    driver.switch_to.frame(entry_iframe)
    time.sleep(1)
    print("상세 정보 iframe으로 전환했습니다.")


# 병원 상세 정보 수집 함수 정의
def collect_hospital_info():
    hospital_name = driver.find_element(By.CSS_SELECTOR, "span.GHAhO").text
    address = driver.find_element(By.CSS_SELECTOR, "span.LDgIH").text
    phone = driver.find_element(By.CSS_SELECTOR, "span.xlx7Q").text if driver.find_elements(By.CSS_SELECTOR,
                                                                                            "span.xlx7Q") else "전화번호 정보 없음"

    # 24시간 병원 판별 조건
    is_24_hours = False
    if "24" in hospital_name or "24시" in hospital_name or "24시간" in hospital_name:
        is_24_hours = True
    else:
        try:
            hours_element = driver.find_element(By.CSS_SELECTOR, "div.A_cdD em")
            if hours_element.text in ["24시간 영업", "24시간 진료"]:
                is_24_hours = True
        except:
            pass

        try:
            hours_text = driver.find_element(By.CSS_SELECTOR, "div.A_cdD").text
            if "매일 00:00 - 24:00" in hours_text:
                is_24_hours = True
        except:
            pass

    hours = "24시간 영업" if is_24_hours else "영업 시간 정보 없음"

    return {
        "병원 이름": hospital_name,
        "주소": address,
        "전화번호": phone,
        "영업 시간": hours
    }


# # 페이지네이션의 마지막 페이지 번호를 가져오는 함수
# def get_last_page_number():
#     page_elements = driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")
#     return int(page_elements[-1].text) if page_elements else 0

# 페이지네이션의 마지막 페이지 번호를 가져오는 함수
def get_last_page_number():
    try:
        # 검색 결과 iframe으로 전환
        switch_to_search_iframe()

        # 페이지 번호 요소 가져오기
        page_elements = driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")

        # 페이지 번호 추출
        if page_elements:
            last_page = int(page_elements[-1].text)
            print(f"마지막 페이지 번호: {last_page}")
        else:
            last_page = 1
            print("페이지네이션이 없어 단일 페이지로 간주합니다.")
    except Exception as e:
        print(f"페이지네이션 확인 중 오류 발생: {e}")
        last_page = 1
    finally:
        # 기본 프레임으로 복귀
        switch_to_default_content()

    return last_page


# 특정 페이지로 이동하는 함수
def go_to_page(page_number):
    page_buttons = driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")
    for button in page_buttons:
        if button.text == str(page_number):
            button.click()
            print(f"{page_number} 페이지로 이동 중...")
            time.sleep(5)
            return True
    return False


# 요청 제한 대응 로직
def handle_too_many_requests():
    wait_time = random.randint(60, 120)
    print(f"429 Too Many Requests 오류 발생. {wait_time}초 동안 대기합니다.")
    time.sleep(wait_time)


# 모든 병원 요소 수집 및 상세 정보 추출
def collect_all_hospital_data():
    switch_to_search_iframe()
    scrollable_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "_pcmap_list_scroll_container"))
    )
    hospital_elements = []
    scroll_position = 0
    scroll_increment = 200
    max_scroll_attempts = 70

    for _ in range(max_scroll_attempts):
        new_elements = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")
        for element in new_elements:
            # hTu5x 클래스 필터링 : 광고 필터링
            if "hTu5x" in element.get_attribute("class"):
                # print("hTu5x 발견. 건너뜁니다.")
                continue

            # YzBgS 클래스 필터링 : 태그가 동물병원이 아닌 것 거르기
            try:
                hospital_type_span = element.find_element(By.CSS_SELECTOR, "span.YzBgS")
                if hospital_type_span.text != "동물병원":
                    # print(f"{hospital_type_span.text} (동물병원이 아님) 발견. 건너뜁니다.")
                    continue
            except Exception as e:
                print(f"YzBgS 클래스 span 처리 중 오류 발생: {e}")
                continue

            if element not in hospital_elements:
                hospital_elements.append(element)

        scroll_position += scroll_increment
        driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_area, scroll_position)
        time.sleep(0.5)

    print(f"총 {len(hospital_elements)}개의 병원을 수집했습니다.")

    detailed_data = []
    for element in hospital_elements:
        try:
            name_element = element.find_element(By.CSS_SELECTOR, "span.YwYLL")
            name = name_element.text
            print(f"{name} 병원 상세 정보 수집 시작")
            name_element.click()
            switch_to_entry_iframe()
            time.sleep(2)

            hospital_info = collect_hospital_info()
            detailed_data.append(hospital_info)
            print(f"{hospital_info['병원 이름']} 병원의 상세 정보를 수집했습니다.")
            time.sleep(2)

            switch_to_search_iframe()
        except Exception as e:
            if "429" in str(e):
                handle_too_many_requests()
            else:
                print(f"{name or '알 수 없는 이름'} 병원 정보 수집 중 오류 발생: {e}")
                print(f"{name or '알 수 없는 이름'} 병원을 건너뛰고 다음으로 이동합니다.")
                switch_to_search_iframe()
            continue
    return detailed_data


# 검색어 입력 및 검색
def perform_search(keyword):
    try:
        switch_to_default_content()  # 기본 프레임으로 전환
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))
        )

        search_box.click()  # 검색창 클릭
        search_box.send_keys(Keys.CONTROL, 'a')  # 전체 선택 (Ctrl + A)
        search_box.send_keys(Keys.BACKSPACE)  # 삭제
        print("검색창 초기화 완료")

        time.sleep(1)
        search_box.send_keys(keyword)  # 새로운 검색어 입력
        search_box.send_keys(Keys.ENTER)  # 검색 실행
        print(f"'{keyword}' 검색을 실행했습니다.")

        # 검색 결과 DOM 갱신 대기
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
        )
        time.sleep(5)  # 결과 안정화를 위한 추가 대기
    except Exception as e:
        print(f"검색창 처리 중 오류 발생: {e}")
        raise


# 키워드별 검색 실행
search_keywords = ["대전 동구 동물병원" ]

# 전체 병원 데이터를 저장할 리스트
all_results = []

for keyword in search_keywords:
    print(f"\n### '{keyword}' 검색 시작 ###")
    try:
        perform_search(keyword)
        last_page_number = get_last_page_number()
        print(f"마지막 페이지 번호: {last_page_number}")

        keyword_results = []
        for current_page in range(1, last_page_number + 1):
            print(f"{current_page} 페이지 크롤링 시작")
            keyword_results.extend(collect_all_hospital_data())
            if current_page < last_page_number:
                go_to_page(current_page + 1)

        print(f"\n'{keyword}' 크롤링 결과:")
        for data in keyword_results:
            print(f"병원 이름: {data['병원 이름']}, 주소: {data['주소']}, 전화번호: {data['전화번호']}, 영업 시간: {data['영업 시간']}")

        all_results.extend(keyword_results)  # 전체 결과에 추가

    except Exception as e:
        print(f"'{keyword}' 검색 중 오류 발생: {e}")

# 모든 검색어의 병원 데이터를 출력
print("\n[전체 병원 상세 정보]")
for data in all_results:
    print(f"병원 이름: {data['병원 이름']}, 주소: {data['주소']}, 전화번호: {data['전화번호']}, 영업 시간: {data['영업 시간']}")

print("\n[24시간 운영 병원 목록]")
for data in all_results:
    if data["영업 시간"] == "24시간 영업":
        print(f"병원 이름: {data['병원 이름']}, 주소: {data['주소']}, 전화번호: {data['전화번호']}, 영업 시간: {data['영업 시간']}")

###############

# DB 연결 설정
connection = pymysql.connect(
    host="localhost",       # DB 호스트
    user="root",            # 사용자 이름
    password="",    # 비밀번호
    database="tails_route_test"  # 데이터베이스 이름
)

print("DB 연결 성공!")

# temp_hospital에 24시간 병원 데이터 삽입
try:
    with connection.cursor() as cursor:
        # 24시간 병원 데이터 필터링
        for data in all_results:
            if data["영업 시간"] == "24시간 영업":
                # INSERT 쿼리 실행
                query = """
                    INSERT INTO temp_hospital (name, callNumber, address, type)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(
                    query,
                    (
                        data["병원 이름"],
                        data["전화번호"],
                        data["주소"],
                        "24시간"
                    )
                )
        # 변경사항 커밋
        connection.commit()
        print("24시간 병원 데이터가 temp_hospital 테이블에 성공적으로 삽입되었습니다.")
finally:
    connection.close()

# 드라이버 종료
driver.quit()

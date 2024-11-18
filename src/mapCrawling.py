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
import re

# ChromeDriver 경로 설정
chrome_driver_path = "../driver/chromedriver.exe"

# Chrome 옵션 설정
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
)


# 드라이버 재시작 함수 정의
def restart_driver():
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://map.naver.com/v5/")
    print("드라이버 재시작 및 네이버 지도 열기 완료")
    return driver


# 프레임 전환 함수 정의
def switch_to_default_content(driver):
    driver.switch_to.default_content()
    print("기본 프레임으로 전환했습니다.")


def switch_to_search_iframe(driver):
    driver.switch_to.default_content()
    search_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
    )
    driver.switch_to.frame(search_iframe)
    print("검색 결과 iframe으로 전환했습니다.")


def switch_to_entry_iframe(driver):
    driver.switch_to.default_content()
    entry_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#entryIframe"))
    )
    driver.switch_to.frame(entry_iframe)
    time.sleep(1)
    print("상세 정보 iframe으로 전환했습니다.")


# 병원 상세 정보 수집 함수 정의
def collect_hospital_info(driver):
    road_address_pattern = re.compile(
        r"(([가-힣]+(특별|광역)?(시|도)?)\s*[가-힣]+(구|군|시)\s*[가-힣0-9]+(로|길)\s*\d+(-\d+)?(\s*\([^)]+\))?)"
    )
    hospital_name = driver.find_element(By.CSS_SELECTOR, "span.GHAhO").text
    address = driver.find_element(By.CSS_SELECTOR, "span.LDgIH").text
    phone = driver.find_element(By.CSS_SELECTOR, "span.xlx7Q").text if driver.find_elements(By.CSS_SELECTOR,
                                                                                            "span.xlx7Q") else "전화번호 정보 없음"

    road_address = address if road_address_pattern.match(address) else None
    jibun_address = address if not road_address else None

    is_24_hours = False
    if "24" in hospital_name or "24시" in hospital_name or "24시간" in hospital_name:
        is_24_hours = True
    hours = "24시간 영업" if is_24_hours else "영업 시간 정보 없음"

    return {
        "병원 이름": hospital_name,
        "도로명 주소": road_address,
        "지번 주소": jibun_address,
        "전화번호": phone,
        "영업 시간": hours
    }


# DB 저장 함수
def save_to_db(all_results):
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="tails_route_test"
    )
    try:
        with connection.cursor() as cursor:
            for data in all_results:
                query = """
                    INSERT INTO temp_hospital (name, callNumber, roadAddress, jibunAddress, type)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query,
                    (
                        data.get("병원 이름", "N/A"),
                        data.get("전화번호", None),
                        data.get("도로명 주소", None),
                        data.get("지번 주소", None),
                        "24시간"
                    )
                )
            connection.commit()
            print("DB에 성공적으로 저장되었습니다.")
    finally:
        connection.close()


# 검색 및 크롤링 함수
def perform_search_and_collect_data(keyword):
    driver = restart_driver()
    all_results = []
    try:
        # 검색어 입력
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))).send_keys(keyword + Keys.ENTER)
        time.sleep(5)

        # 페이지 크롤링
        last_page_number = 1
        try:
            last_page_number = int(driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")[-1].text)
        except:
            print("페이지네이션 없음. 단일 페이지 처리")

        for page in range(1, last_page_number + 1):
            # 병원 정보 수집
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")
                for element in elements:
                    element.click()
                    time.sleep(2)
                    all_results.append(collect_hospital_info(driver))
            except Exception as e:
                print(f"페이지 크롤링 중 오류 발생: {e}")
            if page < last_page_number:
                driver.find_element(By.CSS_SELECTOR, f"a.mBN2s[data-page='{page + 1}']").click()
                time.sleep(5)
    except Exception as e:
        print(f"검색 및 수집 중 오류 발생: {e}")
    finally:
        driver.quit()
    return all_results


# 페이지네이션의 마지막 페이지 번호를 가져오는 함수
def get_last_page_number(driver):
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
def go_to_page(driver, page_number):
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
def collect_all_hospital_data(driver):
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
def perform_search(driver, keyword):
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



# 검색어 리스트
search_keywords = ["대전 유성구 동물병원", "대전 동구 동물병원", "대전 대덕구 동물병원", "대전 서구 동물병원", "대전 중구 동물병원"]

# 성공적으로 완료된 키워드 저장
completed_keywords = []

# 크롤링 시작
total_results = []
for keyword in search_keywords:
    print(f"### '{keyword}' 검색 시작 ###")
    results = perform_search_and_collect_data(keyword)
    if results:  # 결과가 존재할 경우
        completed_keywords.append(keyword)  # 성공한 키워드 저장
    total_results.extend(results)
    save_to_db(results)

# 작업 완료 메시지
print("\n[작업 완료된 키워드]")
for keyword in completed_keywords:
    print(f"- {keyword}")

print("모든 작업이 완료되었습니다.")

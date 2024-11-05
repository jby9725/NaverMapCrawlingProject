from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ChromeDriver 경로 설정
chrome_driver_path = "../driver/chromedriver.exe"

# Chrome 옵션 설정
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36")

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

# 검색어 입력 및 검색
try:
    search_box = driver.find_element(By.CSS_SELECTOR, "input.input_search")
    search_box.send_keys("서울 강서구 동물병원")  # 검색어 입력
    search_box.send_keys(Keys.ENTER)  # Enter 키로 검색
    print("검색어를 입력하고 검색을 실행했습니다.")
    time.sleep(5)  # 검색 결과 로딩 대기 시간 증가
except Exception as e:
    print("검색창을 찾지 못했습니다:", e)
    driver.quit()
    exit()

# 프레임 전환 함수 정의
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
    print("상세 정보 iframe으로 전환했습니다.")

# 병원 상세 정보 수집 함수 정의
def collect_hospital_info():
    hospital_name = driver.find_element(By.CSS_SELECTOR, "span.GHAhO").text
    address = driver.find_element(By.CSS_SELECTOR, "span.LDgIH").text
    phone = driver.find_element(By.CSS_SELECTOR, "span.xlx7Q").text if driver.find_elements(By.CSS_SELECTOR, "span.xlx7Q") else "전화번호 정보 없음"

    # 24시간 병원 판별 조건
    is_24_hours = False
    if "24" in hospital_name or "24시" in hospital_name or "24시간" in hospital_name:
        is_24_hours = True
    else:
        try:
            hours_element = driver.find_element(By.CSS_SELECTOR, "div.A_cdD em")
            if hours_element.text == "24시간 영업":
                is_24_hours = True
        except:
            pass

        try:
            hours_element = driver.find_element(By.CSS_SELECTOR, "div.A_cdD em")
            if hours_element.text == "24시간 진료":
                is_24_hours = True
        except:
            pass

        try:
            hours_text = driver.find_element(By.CSS_SELECTOR, "div.A_cdD").text
            if "매일 00:00 - 24:00" in hours_text:
                is_24_hours = True
        except:
            pass

    # 영업 시간 정보 설정
    hours = "24시간 영업" if is_24_hours else "영업 시간 정보 없음"

    return {
        "병원 이름": hospital_name,
        "주소": address,
        "전화번호": phone,
        "영업 시간": hours
    }

# 1단계: 모든 병원 요소 수집 (스크롤 끝까지 수행)
try:
    switch_to_search_iframe()
    scrollable_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "_pcmap_list_scroll_container"))
    )

    hospital_elements = []
    scroll_position = 0
    scroll_increment = 200
    max_scroll_attempts = 70
    scroll_attempts = 0

    while scroll_attempts < max_scroll_attempts:
        # 현재 보이는 병원 정보 추가
        new_elements = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")
        for element in new_elements:
            # 'hTu5x' 클래스를 포함한 요소는 건너뛰기
            if "hTu5x" in element.get_attribute("class"):
                print("건너뛰는 요소 발견: 특정 클래스 'hTu5x' 포함")
                continue

            if element not in hospital_elements:
                hospital_elements.append(element)

        # 스크롤 내리기
        scroll_position += scroll_increment
        driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_area, scroll_position)
        time.sleep(0.5)  # 스크롤 후 로딩 시간 대기

        scroll_attempts += 1
        print(f"스크롤 {scroll_attempts}회 실행, 현재 수집된 병원 개수: {len(hospital_elements)}")

    print(f"총 {len(hospital_elements)}개의 병원을 수집했습니다.")

    # 2단계: 수집된 각 병원의 상세 정보 추출
    detailed_data = []
    index = 0  # 현재 처리 중인 병원의 인덱스

    while index < len(hospital_elements):
        element = hospital_elements[index]
        retry_attempts = 0
        name = None

        while retry_attempts < 3:
            try:
                # 병원 이름을 클릭하여 상세 페이지로 이동
                name_element = element.find_element(By.CSS_SELECTOR, "span.YwYLL")
                name = name_element.text
                name_element.click()
                print(f"{name} 병원의 상세 페이지로 이동을 시도합니다.")

                # 상세 정보 iframe 로드 후 전환
                switch_to_entry_iframe()
                time.sleep(2)  # 상세 페이지 로딩 대기

                # 병원 상세 정보 수집
                hospital_info = collect_hospital_info()
                detailed_data.append(hospital_info)
                print(f"{hospital_info['병원 이름']} 병원의 상세 정보를 수집했습니다.")

                # 검색 결과 iframe으로 돌아가기
                switch_to_search_iframe()
                print("검색 목록 페이지로 돌아왔습니다.")
                time.sleep(2)  # 목록 페이지 로딩 대기
                break  # 성공하면 재시도 루프 탈출

            except Exception as e:
                print(f"{name or '알 수 없는 이름'} 병원의 정보를 가져오는 중 오류가 발생했습니다:", e)
                retry_attempts += 1  # 재시도 횟수 증가
                if retry_attempts < 3:
                    print(f"{name or '알 수 없는 이름'} 병원 정보 수집 재시도 {retry_attempts}회...")
                    switch_to_search_iframe()  # 검색 결과로 돌아가서 재시도
                    time.sleep(2)
                    hospital_elements = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")  # 목록 요소 새로 갱신
                else:
                    print(f"{name or '알 수 없는 이름'} 병원 정보를 3회 시도했지만 실패했습니다.")
                    break  # 3회 실패 시 루프 탈출하고 다음 병원으로 이동

        index += 1  # 다음 병원으로 이동

    # 수집된 병원 상세 정보 출력
    print("\n[전체 병원 상세 정보]")
    for data in detailed_data:
        print(f"병원 이름: {data['병원 이름']}, 주소: {data['주소']}, 전화번호: {data['전화번호']}, 영업 시간: {data['영업 시간']}")

    # 24시간 병원만 필터링하여 출력
    print("\n[24시간 운영 병원 목록]")
    for data in detailed_data:
        if data["영업 시간"] == "24시간 영업":
            print(f"병원 이름: {data['병원 이름']}, 주소: {data['주소']}, 전화번호: {data['전화번호']}, 영업 시간: {data['영업 시간']}")

except Exception as e:
    print("검색 결과를 가져오는 중 오류가 발생했습니다:", e)

# 드라이버 종료
driver.quit()

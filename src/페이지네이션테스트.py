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
    search_box.send_keys("대전 서구 카페")  # 검색어 입력
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

# 마지막 페이지 번호를 가져오는 함수
def get_last_page_number():
    page_elements = driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")  # 모든 페이지 번호 요소
    return int(page_elements[-1].text)

# 특정 페이지로 이동하는 함수
def go_to_page(page_number):
    # 현재 선택된 페이지와 이동할 페이지가 다른 경우에만 이동
    try:
        active_page = driver.find_element(By.CSS_SELECTOR, "a.mBN2s.qxokY").text
        if active_page == str(page_number):
            print(f"{page_number} 페이지는 이미 활성화되어 있습니다.")
            return
    except:
        pass  # 현재 선택된 페이지가 없는 경우

    # 페이지 번호에 해당하는 버튼 클릭
    page_buttons = driver.find_elements(By.CSS_SELECTOR, "a.mBN2s")
    for button in page_buttons:
        if button.text == str(page_number):
            button.click()
            print(f"{page_number} 페이지로 이동 중...")
            time.sleep(5)  # 페이지 전환 대기
            return

    print(f"{page_number} 페이지 버튼을 찾을 수 없습니다.")

# 페이지네이션 탐색 시작
try:
    switch_to_search_iframe()

    # 마지막 페이지 번호 확인
    last_page_number = get_last_page_number()
    print(f"마지막 페이지 번호: {last_page_number}")

    # 페이지 순회 시작
    for current_page in range(1, last_page_number + 1):
        print(f"현재 페이지: {current_page}")

        try:
            # 현재 페이지로 이동
            go_to_page(current_page)
            # 페이지 이동 후 필요한 데이터 수집 로직이 여기에 추가될 수 있음
            # 예: data = collect_data_from_page()
        except Exception as e:
            print(f"{current_page} 페이지로 이동 중 오류가 발생했습니다:", e)
            break

    print(f"모든 페이지를 순회했습니다. 마지막 페이지: {last_page_number}")

except Exception as e:
    print("페이지네이션을 확인하는 중 오류가 발생했습니다:", e)

# 드라이버 종료
driver.quit()

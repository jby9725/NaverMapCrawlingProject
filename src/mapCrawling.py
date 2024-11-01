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

# Chrome 옵션 설정 (헤드리스 모드를 비활성화하고 User-Agent 추가)
options = Options()
# options.add_argument("--headless")  # 헤드리스 모드를 비활성화
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36")

# Chrome WebDriver 초기화
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 네이버 지도 열기
driver.get("https://map.naver.com/v5/")
print("페이지가 로드될 때까지 기다리겠습니다.")
time.sleep(10)  # 페이지 로드 대기 시간 증가
print("페이지가 로드될 때까지 기다렸습니다.")

# 검색어 입력 및 검색
try:
    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "input_search"))
    )
    search_box.send_keys("대전 서구 동물병원")  # 검색어 입력
    search_box.send_keys(Keys.ENTER)  # Enter 키로 검색
    print("검색창에 검색어를 입력했습니다.")
    time.sleep(5)  # 검색 결과 로딩 대기 시간 증가
except Exception as e:
    print("검색창을 찾지 못했습니다:", e)

# 검색 결과 크롤링
try:
    # iframe 로드 대기 후 전환
    search_iframe = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
    )
    print("iframe을 찾았습니다. 전환합니다.")
    driver.switch_to.frame(search_iframe)

    # 동물병원 이름과 영업 상태 가져오기
    hospital_names = driver.find_elements(By.CSS_SELECTOR, "span.YwYLL")
    hospital_statuses = driver.find_elements(By.CSS_SELECTOR, "span.XP3ml.yTY83")

    # 병원 이름과 영업 상태 출력
    for name, status in zip(hospital_names, hospital_statuses):
        print(f"동물병원 이름: {name.text} / 영업 상태: {status.text}")

except Exception as e:
    print("검색 결과를 가져오는 중 오류가 발생했습니다:", e)

# 드라이버 종료
driver.quit()
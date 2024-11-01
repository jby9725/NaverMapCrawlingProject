from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# ChromeDriver 경로 설정
chrome_driver_path = "../driver/chromedriver.exe"  # chromedriver의 경로를 여기에 입력하세요.

# 옵션 설정
options = Options()
options.add_argument("--headless")  # 브라우저 창을 띄우지 않고 실행 (필요에 따라 삭제 가능)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Chrome WebDriver 초기화
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 네이버 뉴스 Top 100 페이지 열기
naver_news_top100_url = "https://news.naver.com/main/ranking/popularDay.naver"
driver.get(naver_news_top100_url)
time.sleep(3)  # 페이지가 로드될 시간을 줍니다.

# Top 100 뉴스 목록 가져오기
news_titles = driver.find_elements(By.CSS_SELECTOR, ".rankingnews_box .list_title")

# 결과 출력
for index, title in enumerate(news_titles, start=1):
    print(f"{index}. {title.text}")

# 드라이버 종료
driver.quit()
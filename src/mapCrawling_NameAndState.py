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

# 검색 결과가 모두 로드될 때까지 스크롤하면서 데이터 수집
try:
    # iframe 로드 대기 후 전환
    search_iframe = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#searchIframe"))
    )
    print("iframe을 찾았습니다. 전환합니다.")
    driver.switch_to.frame(search_iframe)

    # 스크롤할 영역 선택 (id="_pcmap_list_scroll_container" 사용)
    scrollable_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "_pcmap_list_scroll_container"))
    )

    # 병원 정보가 포함된 li 태그의 class명을 직접 사용하여 모든 데이터를 수집
    all_data = []
    scroll_position = 0
    scroll_increment = 200  # 스크롤할 픽셀 높이 증가량
    max_scroll_attempts = 70  # 스크롤 반복 횟수 제한 설정
    scroll_attempts = 0
    last_data_count = 0  # 마지막 데이터 개수 초기화

    while scroll_attempts < max_scroll_attempts:
        # 병원 정보가 포함된 li 태그 선택
        hospital_elements = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")

        # 병원 이름과 영업 상태를 리스트에 추가
        for element in hospital_elements:
            try:
                # 병원 이름 가져오기
                name = element.find_element(By.CSS_SELECTOR, "span.YwYLL").text

                # 영업 상태 가져오기 (없을 경우 기본값 설정)
                try:
                    status = element.find_element(By.CSS_SELECTOR, "span.XP3ml.yTY83").text
                except:
                    status = "상태 정보 없음"

                all_data.append((name, status))
            except Exception as e:
                print("요소를 찾지 못했습니다:", e)

        # 스크롤 위치를 점진적으로 증가시켜 스크롤
        scroll_position += scroll_increment
        driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_area, scroll_position)
        time.sleep(1)  # 스크롤 후 로딩 시간 대기

        # 스크롤 후 데이터 개수 확인
        current_data_count = len(all_data)
        if current_data_count == last_data_count:
            print("더 이상 새로운 데이터가 없습니다.")
            # 최종 스크롤 후 추가 대기
            time.sleep(5)  # 모든 데이터가 로드되도록 추가 대기
            break
        else:
            last_data_count = current_data_count

        # 스크롤 횟수 증가
        scroll_attempts += 1
        print(f"스크롤 {scroll_attempts}회 실행, 현재 수집된 데이터 개수: {len(all_data)}")

    print("스크롤이 완료되었습니다. 중복 제거를 시작합니다.")

    # 중복 제거: 집합으로 변환한 후 다시 리스트로 변환하여 순서 유지
    unique_data = list(set(all_data))
    print(f"중복 제거 후 총 수집된 병원 정보 수: {len(unique_data)}")

    # 수집된 병원 정보 출력
    for name, status in unique_data:
        print(f"동물병원 이름: {name} / 영업 상태: {status}")

except Exception as e:
    print("검색 결과를 가져오는 중 오류가 발생했습니다:", e)

# 드라이버 종료
driver.quit()

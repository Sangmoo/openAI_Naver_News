# 카카오 API
import requests
import json
import datetime
import os

# openAI News
import urllib.request
import urllib.parse
import json
import openai
import time
import html
from dotenv import load_dotenv

### openAI News
load_dotenv()  # 환경 변수

# 🔹 OpenAI GPT-4 API 설정
client = openai.OpenAI(api_key=os.getenv("openAiKey"))

# 🔹 네이버 검색 API 설정
client_id = os.getenv("naverId")
client_secret = os.getenv("naverSecret")

# 🔹 카테고리별 검색 키워드
categories = {
    "정치": "정치 뉴스",
    "경제": "경제 뉴스",
    "사회": "사회 뉴스",
    "생활/문화": "생활 문화 뉴스",
    "IT/과학": "IT 과학 뉴스",
    "세계": "국제 뉴스",
}

# 🔹 "속보" 검색 추가
categories["속보"] = "속보 뉴스"

# 🔹 뉴스 저장 리스트
summarized_news = {}

for category, keyword in categories.items():
    print(f"\n📡 [{category}] 뉴스 검색 중...")

    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=10&sort=date"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        if rescode == 200:
            response_body = response.read()
            news_data = json.loads(response_body.decode("utf-8"))

            if "items" not in news_data or not news_data["items"]:
                print(f"⚠️ '{category}' 카테고리에서 검색된 뉴스가 없습니다.")
                continue

            # 🔹 중복되지 않는 뉴스 3개 선택
            selected_news = []
            seen_titles = set()

            for news in news_data["items"]:
                title = html.unescape(
                    news["title"].replace("<b>", "").replace("</b>", "").strip()
                )
                link = news["link"]
                description = html.unescape(
                    news["description"].replace("<b>", "").replace("</b>", "").strip()
                )

                if title not in seen_titles and len(selected_news) < 3:
                    selected_news.append(
                        {"title": title, "link": link, "description": description}
                    )
                    seen_titles.add(title)

                if len(selected_news) >= 3:
                    break

            # 🔹 선택된 뉴스 요약
            news_list = []

            for news in selected_news:
                prompt = f"다음 뉴스 기사를 짧고 명확하게 1줄로 요약해줘:\n\n{news['description']}"
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "당신은 뉴스 요약 전문가입니다.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=150,
                        temperature=0.5,
                    )
                    summary = html.unescape(response.choices[0].message.content.strip())
                except Exception as gpt_error:
                    summary = f"[오류] GPT 요약 실패: {gpt_error}"

                # 🔹 최종 결과 저장
                news_list.append(
                    {"title": news["title"], "link": news["link"], "summary": summary}
                )

                # 🔹 API 호출 간 딜레이 추가
                time.sleep(1)

            summarized_news[category] = news_list

        else:
            print(f"❌ [오류] '{category}' 뉴스 요청 실패 (코드: {rescode})")

    except urllib.error.URLError as e:
        print(f"❌ [오류] '{category}' 뉴스 요청 실패: {e.reason}")
        continue

# 🔹 결과 저장
result_text = ""

for category, articles in summarized_news.items():
    result_text += f"\n📌 [{category}]\n"
    for article in articles:
        result_text += f"🔹 제목: {article['title']}\n"
        result_text += f"📝 요약: {article['summary']}\n"
        result_text += f"🔗 링크: {article['link']}\n\n"

# 결과 출력
for category, articles in summarized_news.items():
    print(f"\n📌 [{category}]")
    for article in articles:
        print(f"🔹 제목: {article['title']}")
        print(f"📝 요약: {article['summary']}")
        print(f"🔗 링크: {article['link']}\n")


### Kakao Step 1

# 카카오 토큰을 저장할 파일명
KAKAO_TOKEN_FILENAME = "res/kakao_token.json"

# https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${REST_API_KEY}&redirect_uri=${REDIRECT_URI}
# 이후 나온 oauth code 값
authorize_code = "RY3MINbrGr-qtkpYng2vZb3iFx6xxtfsmJSXWFBvKPSPvGb8j4qP5wAAAAQKKw0fAAABlZ-aWeHOkqTnJF629A"  # oauth?code=PnMm2XGxzwsgx2wfVS5AF5TbU-IM-3WhLsxlKt74Jgwru73ZN76zPQAAAAQKKiUPAAABlWb3nlyYFzyUYZmfhQ
rest_api_key = os.getenv("kakaoRestApiKey")
redirect_uri = os.getenv("kakaoRedirectUri")

url = "https://kauth.kakao.com/oauth/token"

data = {
    "grant_type": "authorization_code",
    "client_id": rest_api_key,  # REST API Key
    "redirect_uri": redirect_uri,
    "code": authorize_code,
}

response = requests.post(url, data=data)

# 요청에 실패했다면,
if response.status_code != 200:
    print("error! because ", response.json())
else:  # 성공했다면,
    tokens = response.json()
    print(tokens)

# #################################################

### Kakao Step 2


# 읽어오는 함수
def load_tokens(filename):
    with open(filename) as fp:
        tokens = json.load(fp)

    return tokens


# 저장하는 함수
def save_tokens(filename, tokens):
    with open(filename, "w") as fp:
        json.dump(tokens, fp)


# refresh_token으로 access_token 갱신하는 함수
def update_tokens(filename):
    tokens = load_tokens(filename)

    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": tokens["refresh_token"],
    }
    response = requests.post(url, data=data)

    # 요청에 실패했다면,
    if response.status_code != 200:
        print("error! because ", response.json())
        tokens = None
    else:  # 요청에 성공했다면,
        print(response.json())
        # 기존 파일 백업
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = filename + "." + now
        os.rename(filename, backup_filename)
        # 갱신된 토큰 저장
        tokens["access_token"] = response.json()["access_token"]
        save_tokens(filename, tokens)

    return tokens


# # 토큰 저장
# save_tokens(KAKAO_TOKEN_FILENAME, tokens)

# # 토큰 업데이트 -> 토큰 저장 필수!
tokens = update_tokens(KAKAO_TOKEN_FILENAME)

# 저장된 토큰 정보를 읽어 옴
tokens = load_tokens(KAKAO_TOKEN_FILENAME)

# 텍스트 메시지 url
url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# request parameter 설정
headers = {"Authorization": "Bearer " + tokens["access_token"]}

data = {
    "template_object": json.dumps(
        {
            "object_type": "text",
            "text": result_text,  # openAI News 결과
            "link": {
                "web_url": "http://sangmoo.tistory.com",
                "mobile_web_url": "http://sangmoo.tistory.com",
            },
            # "button_title": "버튼",
        }
    )
}

# 나에게 카카오톡 메시지 보내기 요청 (text)
response = requests.post(url, headers=headers, data=data)
print(response.status_code)

# 요청에 실패했다면,
if response.status_code != 200:
    print("error! because ", response.json())
else:  # 성공했다면,
    print("메시지를 성공적으로 보냈습니다.")

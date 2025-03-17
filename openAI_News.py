import urllib.request
import urllib.parse
import json
import openai
import time
import html
import os
from dotenv import load_dotenv

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
                prompt = (
                    f"다음 뉴스 기사를 짧고 명확하게 요약해줘:\n\n{news['description']}"
                )
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

# 🔹 결과 출력
for category, articles in summarized_news.items():
    print(f"\n📌 [{category}]")
    for article in articles:
        print(f"🔹 제목: {article['title']}")
        print(f"📝 요약: {article['summary']}")
        print(f"🔗 링크: {article['link']}\n")

import urllib.request
import urllib.parse
import json
import openai
import time
import html
import os
import requests
import shutil
from dotenv import load_dotenv
from moviepy.editor import (
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
)
import moviepy.config as mpy_config

load_dotenv()

os.environ["IMAGEMAGICK_BINARY"] = (
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
)
mpy_config.change_settings(
    {"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"}
)


# form_data 폴더 내 모든 파일 삭제 (없으면 생성)
FORM_DATA_DIR = "form_data"
if os.path.exists(FORM_DATA_DIR):
    for filename in os.listdir(FORM_DATA_DIR):
        file_path = os.path.join(FORM_DATA_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
else:
    os.makedirs(FORM_DATA_DIR)

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

            # 🔹 대표 뉴스 1개로 선택 // 중복되지 않는 뉴스 3개 선택
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

                if title not in seen_titles and len(selected_news) < 1:
                    selected_news.append(
                        {"title": title, "link": link, "description": description}
                    )
                    seen_titles.add(title)

                if len(selected_news) >= 1:
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


# Make Youtube ShortForm
def generate_dalle_image(prompt, output_path):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('openAiKey')}",
    }
    data = {"prompt": prompt, "n": 1, "size": "1024x1024", "response_format": "url"}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        image_url = result["data"][0]["url"]
        img_data = requests.get(image_url).content
        with open(output_path, "wb") as f:
            f.write(img_data)
        print(f"이미지 생성 완료: {output_path}")
    else:
        print(f"이미지 생성 실패: {response.status_code} {response.text}")


clips = []

for category, articles in summarized_news.items():
    # 카테고리명 변환: "생활/문화" -> "생활_문화", "IT/과학" -> "IT_과학"
    if category == "생활/문화":
        category_for_file = "생활_문화"
    elif category == "IT/과학":
        category_for_file = "IT_과학"
    else:
        category_for_file = category

    for idx, article in enumerate(articles):
        # DALL-E 이미지 생성을 위한 프롬프트 구성 (필요에 따라 수정)
        prompt = f"{article['title']} - {article['summary']}"
        # form_data 폴더 내에 이미지 파일 생성
        image_file = os.path.join(FORM_DATA_DIR, f"temp_{category_for_file}_{idx}.png")
        try:
            generate_dalle_image(prompt, image_file)
        except Exception as e:
            print(f"이미지 생성 실패: {e}")
            continue

        # 이미지 클립 생성 (5초 길이 예시)
        image_clip = ImageClip(image_file).set_duration(4)
        # 텍스트 자막 클립 생성 (뉴스 제목과 요약)
        text = f"{article['title']}\n{article['summary']}"
        text_clip = (
            TextClip(
                text,
                fontsize=30,
                color="white",
                bg_color="black",
                method="caption",
                size=image_clip.size,
            )
            .set_duration(5)
            .set_position(("center", "bottom"))
        )

        # 이미지와 자막을 합성한 클립 생성
        composite = CompositeVideoClip([image_clip, text_clip])
        clips.append(composite)
        time.sleep(1)  # API 호출 딜레이

# 모든 클립을 연결해 최종 영상 생성 (fps 24, 유튜브 숏폼에 맞게 총 길이 조절)
if clips:
    final_video = concatenate_videoclips(clips)
    # 영상 길이가 30초를 초과하면 30초로 잘라줌
    if final_video.duration > 27:
        final_video = final_video.subclip(0, 27)
    # BGM 오디오 파일 로드 및 영상 길이에 맞게 자르기
    bgm_clip = AudioFileClip("News.mp3").subclip(0, final_video.duration)
    # 오디오 볼륨 조절이 필요하면 .volumex(0.5) 등을 사용할 수 있음
    final_video = final_video.set_audio(bgm_clip)

    final_video.write_videofile("news_summary.mp4", fps=24)
else:
    print("생성된 클립이 없습니다.")

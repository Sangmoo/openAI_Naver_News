# 카카오 API
import requests
import json
import datetime

# openAI News
import urllib.request
import urllib.parse
import json
import os
from dotenv import load_dotenv

import os
import time
import html

### Kakao Step 1
load_dotenv()  # 환경 변수

# # https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${REST_API_KEY}&redirect_uri=${REDIRECT_URI}
# # 이후 나온 oauth code (client_id)값
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

# 카카오 토큰을 저장할 파일명
KAKAO_TOKEN_FILENAME = "res/kakao_token.json"


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


##
# 초기 실행시, 토큰 저장
# save_tokens(KAKAO_TOKEN_FILENAME, tokens)
##

# 이후, 토큰 업데이트 -> 토큰 저장 필수!
tokens = update_tokens(KAKAO_TOKEN_FILENAME)

# 저장된 토큰 정보를 읽어 옴
tokens = load_tokens(KAKAO_TOKEN_FILENAME)

# 텍스트 메시지 url
url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# request parameter 설정
headers = {"Authorization": "Bearer " + tokens["access_token"]}

# 보낼 메세지
result_text = "카카오톡 나에게 보내기 테스트 !!!"

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

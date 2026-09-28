# -*- coding: utf-8 -*-
import requests
import urllib.parse

# 全语种映射
LANG_MAP = {
    "自动识别": "auto",
    "中文": "zh",
    "英语": "en",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "西班牙语": "es",
    "俄语": "ru",
    "阿拉伯语": "ar",
    "葡萄牙语": "pt",
    "意大利语": "it",
    "泰语": "th",
    "越南语": "vi",
    "印地语": "hi",
    "印尼语": "id",
    "荷兰语": "nl",
    "希腊语": "el",
    "匈牙利语": "hu",
    "瑞典语": "sv",
    "捷克语": "cs",
    "波兰语": "pl",
   罗马尼亚语": "ro",
土耳其语": "tr",
}

# 语音朗读语言
TTS_LANG_MAP = {
    "中文": "zh-CN",
    "英语": "en-US",
    "日语": "ja-JP",
    "韩语": "ko-KR",
    "法语": "fr-FR",
    "德语": "de-DE",
    "西班牙语": "es-ES",
    "俄语": "ru-RU",
    "泰语": "th-TH",
    "越南语": "vi-VN",
}

def translate_text(text: str, to_lang: str = "中文", from_lang: str = "自动识别"):
    try:
        src = LANG_MAP.get(from_lang, "auto")
        dst = LANG_MAP.get(to_lang, "zh")
        langpair = f"{src}|{dst}"
        resp = requests.get("https://api.mymemory.translated.net/get", 
                            params={"q": text, "langpair": langpair}, timeout=8)
        data = resp.json()
        if data.get("responseStatus") != 200:
            return {"code": 500, "error": "翻译服务异常"}
        return {
            "code": 200,
            "original": text,
            "translated": data["responseData"]["translatedText"],
            "from": from_lang,
            "to": to_lang
        }
    except Exception as e:
        return {"code": 500, "error": f"翻译失败：{str(e)}"}

def get_tts_url(text: str, lang: str = "中文"):
    try:
        lc = TTS_LANG_MAP.get(lang, "zh-CN")
        q = urllib.parse.quote(text)
        return f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lc}&client=tw-ob&q={q}"
    except:
        return None

# 腾讯 SkillHub 标准入口
def run(params):
    text = params.get("text", "").strip()
    to = params.get("to", "中文")
    fr = params.get("from", "自动识别")
    
    if not text:
        return {"code":400, "error":"请输入内容"}
    
    res = translate_text(text, to, fr)
    if res["code"] == 200:
        res["voice_url"] = get_tts_url(res["translated"], to)
    return res

# 本地启动
if __name__ == "__main__":
    print(run({"text":"你好", "to":"英语"}))
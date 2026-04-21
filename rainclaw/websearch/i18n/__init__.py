import json
from pathlib import Path
from typing import Any

from fastapi import Request

from app.core.config import settings


class I18n:
    def __init__(self, locale_dir: str = "app/i18n/locales"):
        self.locale_dir = Path(locale_dir)
        self.translations: dict[str, dict[str, Any]] = {}
        self.load_translations()

    def load_translations(self):
        """加载所有语言文件"""
        for file in self.locale_dir.glob("*.json"):
            language = file.stem
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
                self.translations[language] = data

    def get(self, key: str, language: str = settings.LANGUAGE_ZH, **kwargs) -> str:
        if language in [settings.LANGUAGE_EN, "en"]:
            language = settings.LANGUAGE_EN
        elif language in [settings.LANGUAGE_ZH, "zh"]:
            language = settings.LANGUAGE_ZH
        else:
            language = settings.LANGUAGE_ZH
        """获取翻译文本"""
        try:
            # 支持嵌套键，如 "errors.required"
            keys = key.split(".")
            translation = self.translations.get(
                language, self.translations[settings.LANGUAGE_ZH]
            )

            for k in keys:
                translation = translation[k]

            # 格式化带参数的消息
            if isinstance(translation, str) and kwargs:
                return translation.format(**kwargs)
            return translation
        except (KeyError, AttributeError):
            return key

    def get_language_from_request(
        self, request: Request, default: str = settings.LANGUAGE_ZH
    ) -> str:
        """从请求中获取语言设置"""
        # 1. 检查查询参数
        language = None
        if request:
            language = request.headers.get("language")
            return language
        if not language:
            language = default
        if language and language in [settings.LANGUAGE_ZH, "zh"]:
            return settings.LANGUAGE_ZH
        else:
            return settings.LANGUAGE_EN
        # lang = request.query_params.get("lang")
        # if lang and lang in self.translations:
        #     return lang

        # # 2. 检查 Accept-Language 头部
        # accept_language = request.headers.get("accept-language", "")
        # if accept_language:
        #     for lang in accept_language.split(','):
        #         lang = lang.split(';')[0].strip()
        #         primary_lang = lang.split('-')[0]
        #         if primary_lang in self.translations:
        #             return primary_lang

        # # 3. 检查自定义头部
        # x_lang = request.headers.get("x-language")
        # if x_lang and x_lang in self.translations:
        #     return x_lang

        # # 4. 返回默认语言
        # return "en"


i18n = I18n()

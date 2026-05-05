from deep_translator import GoogleTranslator
from langdetect import detect


def translate_to_english(text):
    try:
        lang = detect(text)
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated, lang
    except:
        return text, "en"


def translate_back(text, lang):
    try:
        translated = GoogleTranslator(source='en', target=lang).translate(text)
        return translated
    except:
        return text
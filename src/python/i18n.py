"""Multi-language UI support module."""

_current_lang = "en"

TRANSLATIONS = {
    "en": {"greeting": "Hello! How can I help you?", "dont_know": "I don't have information about that yet.",
            "offer_search": "Would you like me to search online?", "searching": "Searching...",
            "saved": "Saved! I'll remember this.", "goodbye": "Goodbye!",
            "ask_save": "Save this for future?", "learned": "I learned something new!",
            "error": "Something went wrong.", "help_cmd": "Type /help for commands."},
    "ar": {"greeting": "مرحباً! كيف يمكنني مساعدتك؟", "dont_know": "ليس لدي معلومات عن ذلك بعد.",
            "offer_search": "هل تريد مني البحث عبر الإنترنت؟", "searching": "جارٍ البحث...",
            "saved": "تم الحفظ! سأتذكر هذا.", "goodbye": "مع السلامة!",
            "ask_save": "حفظ هذا للمستقبل؟", "learned": "تعلمت شيئاً جديداً!",
            "error": "حدث خطأ ما.", "help_cmd": "اكتب /help للأوامر."},
    "hi": {"greeting": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?", "dont_know": "मेरे पास अभी इसकी जानकारी नहीं है।",
            "offer_search": "क्या आप चाहते हैं कि मैं ऑनलाइन खोजूँ?", "searching": "खोज रहा हूँ...",
            "saved": "सहेजा गया! मुझे यह याद रहेगा।", "goodbye": "अलविदा!",
            "ask_save": "भविष्य के लिए सहेजें?", "learned": "मैंने कुछ नया सीखा!",
            "error": "कुछ गलत हो गया।", "help_cmd": "कमांड के लिए /help टाइप करें।"},
    "es": {"greeting": "¡Hola! ¿Cómo puedo ayudarte?", "dont_know": "Aún no tengo información sobre eso.",
            "offer_search": "¿Te gustaría que busque en línea?", "searching": "Buscando...",
            "saved": "¡Guardado! Recordaré esto.", "goodbye": "¡Adiós!",
            "ask_save": "¿Guardar esto para el futuro?", "learned": "¡Aprendí algo nuevo!",
            "error": "Algo salió mal.", "help_cmd": "Escribe /help para comandos."},
    "zh": {"greeting": "你好！我能帮你什么？", "dont_know": "我还没有相关信息。",
            "offer_search": "你想让我在网上搜索吗？", "searching": "搜索中...",
            "saved": "已保存！我会记住的。", "goodbye": "再见！",
            "ask_save": "保存以备将来使用？", "learned": "我学到了新东西！",
            "error": "出了点问题。", "help_cmd": "输入 /help 查看命令。"},
    "fr": {"greeting": "Bonjour ! Comment puis-je vous aider ?", "dont_know": "Je n'ai pas encore d'informations à ce sujet.",
            "offer_search": "Voulez-vous que je cherche en ligne ?", "searching": "Recherche en cours...",
            "saved": "Enregistré ! Je m'en souviendrai.", "goodbye": "Au revoir !",
            "ask_save": "Enregistrer pour plus tard ?", "learned": "J'ai appris quelque chose de nouveau !",
            "error": "Quelque chose s'est mal passé.", "help_cmd": "Tapez /help pour les commandes."},
}


def set_language(lang_code):
    """Switch current language (en/ar/hi/es/zh/fr)."""
    global _current_lang
    if lang_code in TRANSLATIONS:
        _current_lang = lang_code
        return True
    return False


def t(key):
    """Get translated string for current language."""
    return TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"]).get(key, key)


def detect_language(text):
    """Auto-detect language from Unicode ranges."""
    for ch in text:
        cp = ord(ch)
        if 0x0600 <= cp <= 0x06FF:
            return "ar"
        if 0x0900 <= cp <= 0x097F:
            return "hi"
        if 0x4E00 <= cp <= 0x9FFF:
            return "zh"
    return "en"


def available_languages():
    """List supported language codes."""
    return list(TRANSLATIONS.keys())


if __name__ == "__main__":
    for lang in available_languages():
        set_language(lang)
        print(f"\n[{lang}]")
        for key in TRANSLATIONS[lang]:
            print(f"  {key}: {t(key)}")

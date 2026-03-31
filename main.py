import flet as ft
import flet_ads as fta
import sys
import asyncio
from flet import *
import threading
import httpx
import json
# geocoder و requests يُستوردان عند الحاجة فقط (لتسريع الإطلاق)
import socket
import os
import json as _json_settings  # نستخدم json بدلاً من pickle للإعدادات
from datetime import datetime, timedelta
import re
import calendar
import locale
import random
import pickle
TASBIH_FILE = "tasbih_data.json"


class AdsManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.counter = 0
        self._ad_unit_id = None
        self._interstitial = None

        if is_mobile(page):
            ad_ids = {
                ft.PagePlatform.ANDROID: "ca-app-pub-3940256099942544/1033173712",
                ft.PagePlatform.IOS: "ca-app-pub-3940256099942544/4411468910",
            }
            self._ad_unit_id = ad_ids.get(page.platform, ad_ids[ft.PagePlatform.ANDROID])
            self._load_new_ad()

    def _load_new_ad(self):
        if not self._ad_unit_id:
            return

        self._interstitial = fta.InterstitialAd(
            unit_id=self._ad_unit_id,
            on_load=lambda e: print("✅ loaded"),
            on_error=lambda e: print(f"❌ error: {e.data}"),
            on_open=lambda e: print("📱 opened"),
            on_close=self._on_ad_close,
        )

        # ✅ في 0.83.x لازم page.services مش page.overlay
        self.page.services.append(self._interstitial)
        safe_update(self.page)

    def _on_ad_close(self, e):
        if self._interstitial in self.page.services:
            self.page.services.remove(self._interstitial)
        self._load_new_ad()

    async def show_ad(self):
        if not self._ad_unit_id or not self._interstitial:
            return

        self.counter += 1
        if self.counter % 3 != 1:
            return

        try:
            await self._interstitial.show()
        except Exception as ex:
            print(f"⚠️ error: {ex}")




# ══════════════════════════════════════════════
#  إعدادات إعلانات AdMob
#  استبدل هذه القيم بمعرّفاتك الحقيقية عند النشر
# ══════════════════════════════════════════════
AD_IDS = {
    ft.PagePlatform.ANDROID: {
        "banner": "ca-app-pub-3940256099942544/6300978111",
        # "interstitial": "ca-app-pub-3940256099942544/1033173712",  # TODO: تفعيل عند توفر في 0.83.0+
    },
    ft.PagePlatform.IOS: {
        "banner": "ca-app-pub-3940256099942544/2934735716",
        # "interstitial": "ca-app-pub-3940256099942544/4411468910",  # TODO: تفعيل عند توفر في 0.83.0+
    },
}

def get_ad_id(page: ft.Page, ad_type: str) -> str:
    """إرجاع معرّف الإعلان حسب المنصة"""
    return AD_IDS.get(page.platform, AD_IDS[ft.PagePlatform.ANDROID]).get(ad_type, "")

def is_mobile(page: ft.Page) -> bool:
    """التحقق هل التطبيق يعمل على هاتف"""
    return page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)


def wrap_with_ad(main_content, page_ref):
    """يلف المحتوى في Stack مع إعلان شفاف يطفو في الأسفل — مثل AzkarPage تماماً"""
    if not is_mobile(page_ref):
        return main_content
    return ft.Stack(
        controls=[
            main_content,
            Container(
                content=fta.BannerAd(
                    unit_id=get_ad_id(page_ref, "banner"),
                    on_error=lambda e: print("BannerAd error:", e.data),
                ),
                width=320,
                height=50,
                bottom=0,
                left=0,
                right=0,
                alignment=ft.Alignment(0, 1),
            ),
        ],
        expand=True,
    )

def safe_update(page):
    try:
        page.update()
    except Exception:
        pass

# ══════════════════════════════════════════════
#  InterstitialAd — معطّل مؤقتاً
#  TODO: إعادة التفعيل عند توفر InterstitialAd في flet-ads 0.83.0+
# ══════════════════════════════════════════════

def setup_interstitial_ad(page: ft.Page):
    """معطّل مؤقتاً — InterstitialAd غير متوفرة في flet-ads 0.83.0"""
    pass  # TODO: إعادة التفعيل عند توفر InterstitialAd

async def show_interstitial_ad(page: ft.Page):
    """تشغيل الإعلان البيني عبر AdsManager"""
    manager = getattr(page, "_ads_manager", None)
    if manager:
        await manager.show_ad()

def _make_interstitial(page: ft.Page):
    """معطّلة مؤقتاً — InterstitialAd غير متوفرة في flet-ads 0.83.0"""
    return None  # TODO: إعادة التفعيل عند توفر InterstitialAd

def _show_snack(page, message, color=None, duration=2000):
    """عرض SnackBar بطريقة متوافقة مع flet 0.22+"""
    try:
        snack = ft.SnackBar(
            content=ft.Text(message, font_family=BUTTON_FONT, text_align=ft.TextAlign.CENTER),
            bgcolor=color,
            duration=duration,
        )
        page.overlay.append(snack)
        snack.open = True
        safe_update(page)
    except Exception as ex:
        print(f"خطأ في عرض SnackBar: {ex}")

async def _open_url(url: str, page: Page):
    """فتح رابط بشكل آمن على الهاتف والديسكتوب - طريقة 11 المجربة"""
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            await page.launch_url(url)
    except Exception as e:
        print(f"خطأ في فتح الرابط: {e}")

def _share_app(page):
    """مشاركة التطبيق — نسخ رسالة المشاركة للحافظة"""
    share_msg = (
        "✨ تطبيق القريب - أذكار المسلم ✨\n\n"
        "رفيقك اليومي في الأذكار والأدعية والعبادات\n"
        "📿 أذكار الصباح والمساء\n"
        "🕌 مواقيت الصلاة\n"
        "📖 القرآن الكريم\n"
        "🌟 سبحة إلكترونية وأهداف يومية\n\n"
        "جزاك الله خيراً على مشاركته مع أحبائك 🌿"
    )
    try:
        page.set_clipboard(share_msg)
        _show_snack(page, "✅ تم نسخ رسالة المشاركة! شاركها مع أحبائك 🌿", "#4CAF50", 2500)
    except Exception as e:
        print(f"خطأ في المشاركة: {e}")
        _show_snack(page, "✅ شارك التطبيق مع أحبائك 🌿", "#4CAF50", 2000)

# ── كاش تنسيق نصوص الأذكار (يمنع إعادة الحساب في كل فتح) ──────
_format_cache = {}

def load_tasbih():
    if not os.path.exists(TASBIH_FILE):
        default = [
            {"id": 1, "text": "سُبْحَانَ اللَّهِ", "count": 0},
            {"id": 2, "text": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ", "count": 0},
            {"id": 3, "text": "سُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ", "count": 0},
            {"id": 4, "text": "سُبْحَانَ اللهِ العَظِيمِ وَبِحَمْدِهِ", "count": 0},
            {"id": 5, "text": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ", "count": 0},
            {"id": 6, "text": "لَا إلَه إلّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلُّ شَيْءِ قَدِيرِ", "count": 0},
            {"id": 7, "text": "لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ", "count": 0},
            {"id": 8, "text": "الْحَمْدُ للّهِ رَبِّ الْعَالَمِينَ", "count": 0},
            {"id": 9, "text": "الْلَّهُم صَلِّ وَسَلِم وَبَارِك عَلَى سَيِّدِنَا مُحَمَّد", "count": 0},
            {"id": 10, "text": "أستغفر الله", "count": 0},
            {"id": 11, "text": "سُبْحَانَ الْلَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا الْلَّهُ، وَالْلَّهُ أَكْبَرُ", "count": 0},
            {"id": 12, "text": "لَا إِلَهَ إِلَّا اللَّهُ", "count": 0},
            {"id": 13, "text": "الْلَّهُ أَكْبَرُ", "count": 0},
            {"id": 14, "text": "سُبْحَانَ اللَّهِ ، وَالْحَمْدُ لِلَّهِ ، وَلا إِلَهَ إِلا اللَّهُ ، وَاللَّهُ أَكْبَرُ ، اللَّهُمَّ اغْفِرْ لِي ، اللَّهُمَّ ارْحَمْنِي ، اللَّهُمَّ ارْزُقْنِي", "count": 0},
            {"id": 15, "text": "الْحَمْدُ لِلَّهِ حَمْدًا كَثِيرًا طَيِّبًا مُبَارَكًا فِيهِ", "count": 0},
            {"id": 16, "text": "اللَّهُ أَكْبَرُ كَبِيرًا ، وَالْحَمْدُ لِلَّهِ كَثِيرًا ، وَسُبْحَانَ اللَّهِ بُكْرَةً وَأَصِيلاً", "count": 0},
            {"id": 17, "text": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ كَمَا صَلَّيْتَ عَلَى إِبْرَاهِيمَ , وَعَلَى آلِ إِبْرَاهِيمَ إِنَّكَ حَمِيدٌ مَجِيدٌ , اللَّهُمَّ بَارِكْ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ كَمَا بَارَكْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ إِنَّكَ حَمِيدٌ مَجِيدٌ", "count": 0},

        ]
        with open(TASBIH_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

    try:
        with open(TASBIH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # التأكد من وجود الحقول المطلوبة
            for item in data:
                if "id" not in item:
                    item["id"] = data.index(item) + 1
                if "count" not in item:
                    item["count"] = 0
            return data
    except Exception as e:
        print(f"خطأ في تحميل بيانات السُبحة: {e}")
        return []

def save_tasbih(data):
    try:
        with open(TASBIH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ بيانات السُبحة: {e}")

def view_exists(page, route):
    """التحقق مما إذا كانت الصفحة موجودة بالفعل في views"""
    for view in page.views:
        if view.route == route:
            return True
    return False

# ══════════════════════════════════════════════════════════════
#  نظام الرجوع الموحّد — مصدر وحيد للتحكم في زر الرجوع
#  يُستخدم لكلٍّ من: زر AppBar اليدوي + زر الهاتف الفيزيائي
# ══════════════════════════════════════════════════════════════

def _do_back(page):
    """الدالة الوحيدة التي تُنفّذ الرجوع فعلياً."""
    if len(page.views) <= 1:
        try:
            page.window.close()
        except Exception:
            pass
        return
    page.views.pop()
    page.route = page.views[-1].route

    # إخفاء الإعلان العالمي عند الرجوع للصفحة الرئيسية
    banner = getattr(page, "_global_banner", None)
    if banner is not None:
        banner.visible = (page.route != "/")
        try:
            banner.update()
        except Exception:
            pass

    safe_update(page)

# ── زر AppBar اليدوي ────────────────────────────────────────
def handle_back(page: Page) -> bool:
    """تُستدعى عند الضغط على زر الرجوع داخل AppBar."""
    if getattr(page, "_is_backing", False):
        return True
    page._is_backing = True
    try:
        _do_back(page)
        return True
    except Exception as e:
        print(f"خطأ في handle_back: {e}")
        return False
    finally:
        page._is_backing = False

# ── زر الهاتف الفيزيائي ─────────────────────────────────────
def on_view_pop_handler(e):
    """
    تُستدعى بواسطة Flet عند ضغط زر الرجوع في الهاتف.
    نُعاملها تماماً مثل زر الرجوع اليدوي في AppBar:
    نُزيل الـ view بأنفسنا ونُحدّث الـ route.
    """
    page = e.page
    if getattr(page, "_is_backing", False):
        return
    page._is_backing = True
    try:
        _do_back(page)
    except Exception as ex:
        print(f"خطأ في on_view_pop: {ex}")
    finally:
        page._is_backing = False

# ============ الثوابت والإعدادات العامة ============
APP_TITLE = "القريب - أذكار المسلم"
APP_SIZE = (390, 740)
APP_POSITION = (960, 10)
APP_BGCOLOR = "#685BDA"
FONT_NAME = "assets/fonts/alfont_com_AlFont_com_137-UthmanTN1-Ver10.otf"
FONT_FILE = "assets/fonts/alfont_com_AlFont_com_137-UthmanTN1-Ver10.otf"
BUTTON_FONT = "assets/fonts/alfont_com_AlFont_com_137-UthmanTN1-Ver10.otf"  # خط جديد للأزرار
APP_ICON = "assets/icons/icon.webp"  # مسار أيقونة التطبيق
icon = "icon.png.png"
DEFAULT_FONT_SIZE = 18
MIN_FONT_SIZE = 14
MAX_FONT_SIZE = 30
FONT_QURAN = "assets/fonts/Amiri-Bold.ttf"

# إعدادات التخزين — JSON بدلاً من pickle (أسرع وأكثر أمانًا على الأندرويد)
SETTINGS_FILE = "settings.json"

# ============ نظام الإعدادات المحسن ============
def load_settings():
    """تحميل جميع الإعدادات المحفوظة"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        # هجرة تلقائية من الملف القديم pickle إذا وُجد
        old_pkl = "settings.pkl"
        if os.path.exists(old_pkl):
            try:
                import pickle
                with open(old_pkl, 'rb') as f:
                    old_data = pickle.load(f)
                save_settings_dict(old_data)
                os.remove(old_pkl)
                return old_data
            except Exception:
                pass
        return {}
    except Exception:
        return {}

def save_settings_dict(settings):
    """حفظ جميع الإعدادات"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"حدث خطأ في حفظ الإعدادات: {e}")

# دالة save_settings القديمة (للتوافق مع الكود القديم)
def save_settings(font_size):
    """حفظ إعدادات حجم الخط فقط (للتوافق مع الكود القديم)"""
    settings = load_settings()
    settings['font_size'] = font_size
    save_settings_dict(settings)

# تحميل صورة الخلفية المحفوظة أو استخدام الافتراضية
def load_home_background():
    settings = load_settings()
    return settings.get('home_background', 'assets/icons/1200.webp')

if not os.path.exists("my_azkar.json"):
    with open("my_azkar.json", "w", encoding="utf-8") as f:
        f.write("[]")
# تحميل حجم الخط المحفوظ أو استخدام الافتراضي
def load_font_size():
    try:
        settings = load_settings()
        return settings.get('font_size', DEFAULT_FONT_SIZE)
    except Exception:
        return DEFAULT_FONT_SIZE

# تحميل مرة واحدة فقط (بدلاً من مرتين سابقاً)
current_font_size = load_font_size()
current_home_background = load_home_background()

############################

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ============ نظام التحميل المؤجل لملفات JSON ============
AZKAR_FILES = {
    "untimed_sunan": "assets/untimed_sunan.json",
    "timed_sunan": "assets/timed_sunan.json",
    "azkar_sabah": "assets/azkar_sabah.json",
    "azkar_masaa": "assets/azkar_masaa.json",
    "azkar_baad_salah": "assets/azkar_baad_salah.json",
    "adeiat_wa_azkar_mutanawiea": "assets/adeiat_wa_azkar_mutanawiea.json",
    "azkar_azima": "assets/azkar_azima.json",
    "alsalat_ealaa_alnabii": "assets/alsalat_ealaa_alnabii.json",
    "ayat_alkursii": "assets/ayat_alkursii.json",
    "adeiat_llmtwffy": "assets/adeiat_llmtwffy.json",
    "sadaqa_gariya": "assets/sadaqa_gariya.json",
    "sleep": "assets/sleep.json",
    "Nabawi_Mosque": "assets/Nabawi_Mosque.json",
    "wakeup": "assets/wakeup.json",
    "sujud": "assets/sujud.json",
    "kaaba4": "assets/kaaba4.json",
    "quran1": "assets/quran1.json",
    "jwamea6": "assets/jwamea6.json",
    "athan5": "assets/athan5.json",
    "istanbul": "assets/istanbul.json",
    "wodu50": "assets/wodu50.json",
    "wudu_steps": "assets/wudu_steps.json",
    "azkar_almanzel": "assets/azkar_almanzel.json",
    "azkar_alkhala": "assets/azkar_alkhala.json",
    "azkar_altaaam": "assets/azkar_altaaam.json",
    "my_azkar": "my_azkar.json"  # ملف المستخدم
}

# ذاكرة تخزين مؤقت للبيانات
_azkar_cache = {}

def load_json_lazy(key):
    """تحميل بيانات JSON عند الحاجة فقط مع التخزين المؤقت"""
    if key not in _azkar_cache:
        try:
            file_path = AZKAR_FILES[key]
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _azkar_cache[key] = data
        except Exception as e:
            print(f"⚠️ خطأ في تحميل {key}: {e}")
            # إرجاع قائمة فارغة بدلاً من رفع استثناء
            return []
    return _azkar_cache[key]

# ============ دوال مساعدة للوصول السريع ============
def get_azkar_sabah():
    return load_json_lazy("azkar_sabah")

def get_azkar_masaa():
    return load_json_lazy("azkar_masaa")

def get_azkar_baad_salah():
    return load_json_lazy("azkar_baad_salah")

def get_untimed_sunan():
    return load_json_lazy("untimed_sunan")

def get_timed_sunan():
    return load_json_lazy("timed_sunan")

def get_adeiat_wa_azkar_mutanawiea():
    return load_json_lazy("adeiat_wa_azkar_mutanawiea")

def get_azkar_azima():
    return load_json_lazy("azkar_azima")

def get_alsalat_ealaa_alnabii():
    return load_json_lazy("alsalat_ealaa_alnabii")

def get_ayat_alkursii():
    return load_json_lazy("ayat_alkursii")

def get_adeiat_llmtwffy():
    return load_json_lazy("adeiat_llmtwffy")

def get_sadaqa_gariya():
    return load_json_lazy("sadaqa_gariya")

def get_sleep():
    return load_json_lazy("sleep")

def get_Nabawi_Mosque():
    return load_json_lazy("Nabawi_Mosque")

def get_wakeup():
    return load_json_lazy("wakeup")

def get_sujud():
    return load_json_lazy("sujud")

def get_kaaba4():
    return load_json_lazy("kaaba4")

def get_quran1():
    return load_json_lazy("quran1")

def get_jwamea6():
    return load_json_lazy("jwamea6")

def get_athan5():
    return load_json_lazy("athan5")

def get_istanbul():
    return load_json_lazy("istanbul")

def get_wodu50():
    return load_json_lazy("wodu50")

def get_wudu_steps():
    return load_json_lazy("wudu_steps")

def get_azkar_almanzel():
    return load_json_lazy("azkar_almanzel")

def get_azkar_alkhala():
    return load_json_lazy("azkar_alkhala")

def get_azkar_altaaam():
    return load_json_lazy("azkar_altaaam")

def get_my_azkar():
    return load_json_lazy("my_azkar")
#######################################
# تعريف مسارات الأيقونات
CUSTOM_ICONS = {
    "morning": "assets/icons/azkar_sabah.webp",
    "night": "assets/icons/azkar_masaa.webp",
    "mosque": "assets/icons/azkar_baad_salah.webp",
    "prayer": "assets/icons/alsalat_ealaa_alnabii.webp",
    "book": "assets/icons/ayat_alkursii.webp",
    "star": "assets/icons/azkar_azima.webp",
    "dua": "assets/icons/adeiat_wa_azkar_mutanawiea.webp",
    "moon": "assets/icons/adeiat_llmtwffy.webp",
    "qibla": "assets/icons/qibla.webp",
    "library": "assets/icons/library.webp",
    "learn_prayer": "assets/icons/prayer_icon.webp",
    "quran": "assets/icons/quran.webp",  # أيقونة جديدة للقرآن
    "tasbih": "assets/icons/tasbih_icon.webp", # أيقونة جديدة للسبحة
    "kok": "assets/icons/sadaqa_gariya.webp",
    "sleep": "assets/icons/sleep.webp",
    "Nabawi": "assets/icons/Nabawi_Mosque.webp",
    "prayer_time": "assets/icons/prayer_time.webp",
    "hajj": "assets/icons/hajj.webp",
    "goals": "assets/icons/goals_icon.webp", 
    "azkar_almanzel": "assets/icons/azkar_almanzel.webp", 
    "azkar_alkhala": "assets/icons/azkar_alkhala.webp", 
    "azkar_altaaam": "assets/icons/azkar_altaaam.webp", 
    "calendar": "assets/icons/calendar.webp",  # أيقونة جديدة للتقويم
    "wudu": "assets/icons/wudhu.webp",
    "1a": "assets/icons/crescent.webp",
    "2a": "assets/icons/sunrise.webp",
    "3a": "assets/icons/weather.webp",
    "4a": "assets/icons/sun.webp",
    "5a": "assets/icons/cleary.webp",
    "6a": "assets/icons/sunset.webp",
    "7a": "assets/icons/momok.webp",
    "8a": "assets/icons/aljumuea.webp",
    "sunan": "assets/icons/sunna_mawqota.webp",
    "info": "assets/icons/info.webp",
    "settings": "assets/icons/settings.webp",
    "share": "assets/icons/share.webp",
    "my_azkar": "assets/icons/plus.webp",  # أضف هذه السطر
    "wakeup": "assets/icons/wakeup.webp",
    "sujud": "assets/icons/sujud.webp",
    "kaaba4": "assets/icons/kaaba4.webp",
    "quran80": "assets/icons/quran80.webp",
    "jwamea6": "assets/icons/jwamea6.webp",
    "athan5": "assets/icons/athan5.webp",
    "istanbul": "assets/icons/istanbul.webp",
    "wodu50": "assets/icons/wodu50.webp",
    "youm": "assets/icons/youm.webp",
    "fadl": "assets/icons/fadl.webp",

    "1aa": "assets/icons/woodu.webp",
    "2aa": "assets/icons/azaan10.webp",
    "3aa": "assets/icons/mosque34.webp",
    "4aa": "assets/icons/baadsalao.webp",
    "5aa": "assets/icons/food.webp",
    "6aa": "assets/icons/handshake.webp",
    "7aa": "assets/icons/clothes.webp",
    "8aa": "assets/icons/sneeze.webp",
    "9aa": "assets/icons/smiley.webp",
    "10aa": "assets/icons/rubelhizb.webp",
    "11aa": "assets/icons/prayer67.webp",
    "12aa": "assets/icons/allah1.webp",
    "untimed_sunan": "assets/icons/untimed_sunan.webp",
}

# ============ ملف تخزين العادات اليومية ============
HABITS_FILE = "daily_habits.json"

# تهيئة ملف العادات إذا لم يكن موجودًا
def init_habits_file():
    """تهيئة ملف العادات مع النظام الجديد (كل يوم له عاداته الخاصة)"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if not os.path.exists(HABITS_FILE):
        # إنشاء العادات الافتراضية لليوم الحالي فقط
        default_habits = [
            {"id": 1, "text": "🕌 الالتزام بالصلاة", "completed": False, "custom": False, "category": "دين"},
            {"id": 2, "text": "🌙 الصيام", "completed": False, "custom": False, "category": "دين"},
            {"id": 3, "text": "📚 الدراسة والتعليم", "completed": False, "custom": False, "category": "تعليم"},
            {"id": 4, "text": "🏋️‍♂️ تمارين رياضية", "completed": False, "custom": False, "category": "صحة"},
            {"id": 5, "text": "💼 الالتزام بالعمل", "completed": False, "custom": False, "category": "عمل"},
            {"id": 18, "text": "😴 أذكار قبل النوم", "completed": False, "custom": False, "category": "دين"},
            {"id": 6, "text": "🌤️ أذكار الصباح", "completed": False, "custom": False, "category": "دين"},
            {"id": 7, "text": "🌛 أذكار المساء", "completed": False, "custom": False, "category": "دين"},
            {"id": 8, "text": "📖 قراءة القرآن", "completed": False, "custom": False, "category": "دين"},
            {"id": 9, "text": "⏰ الاستيقاظ مبكرًا", "completed": False, "custom": False, "category": "صحة"},
            {"id": 10, "text": "🙏 صلاة الضحى", "completed": False, "custom": False, "category": "دين"},
            {"id": 11, "text": "🙏 صلاة الوتر", "completed": False, "custom": False, "category": "دين"},
            {"id": 12, "text": "😊 الابتسامة", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 13, "text": "💚 صدقة ( عمل خير )", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 14, "text": "😌 غض البصر", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 15, "text": "🙂 حفظ اللسان", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 16, "text": "❤️ بر الوالدين", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 17, "text": "🌷 صلة الرحم", "completed": False, "custom": False, "category": "اجتماعي"},
        ]
        
        data = {
            "daily_habits": {
                today_str: default_habits
            },
            "history": []
        }
        
        with open(HABITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # إزالة التحقق من إعادة التعيين لأن النظام الجديد لا يعتمد على الوقت
    return True

def load_daily_habits(date_str):
    """تحميل عادات يوم محدد"""
    if not os.path.exists(HABITS_FILE):
        init_habits_file()
    
    with open(HABITS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "daily_habits" in data and date_str in data["daily_habits"]:
        return data["daily_habits"][date_str]
    
    return []

def save_daily_habits(date_str, habits):
    """حفظ عادات يوم محدد"""
    if not os.path.exists(HABITS_FILE):
        data = {"daily_habits": {}, "history": []}
    else:
        with open(HABITS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if "daily_habits" not in data:
        data["daily_habits"] = {}
    
    data["daily_habits"][date_str] = habits
    
    with open(HABITS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True

def get_habits_history():
    """الحصول على تاريخ العادات"""
    if not os.path.exists(HABITS_FILE):
        return []
    
    with open(HABITS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("history", [])

def add_habit_to_history(date_str, completed, total):
    """إضافة سجل تاريخي"""
    if not os.path.exists(HABITS_FILE):
        data = {"daily_habits": {}, "history": []}
    else:
        with open(HABITS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if "history" not in data:
        data["history"] = []
    
    percentage = (completed / total * 100) if total > 0 else 0
    
    data["history"].append({
        "date": date_str,
        "completed": completed,
        "total": total,
        "percentage": percentage
    })
    
    # الاحتفاظ بآخر 365 يوم فقط (سنة)
    if len(data["history"]) > 365:
        data["history"] = data["history"][-365:]
    
    with open(HABITS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True

# ============ صفحة أهدافك اليومية المعدلة ============

class HabitCalendarPage:
    def __init__(self, page):
        self.page = page
        self.current_date = datetime.now()
        self.calendar_data_file = "calendar_data.json"
        
    def save_daily_progress(self, date_str, habits_list):
        """حفظ نسبة الإنجاز اليومي بناءً على العادات"""
        try:
            # حساب نسبة الإنجاز من العادات
            completed = sum(1 for habit in habits_list if habit["completed"])
            total = len(habits_list)
            completed_percentage = (completed / total * 100) if total > 0 else 0
            
            if not os.path.exists(self.calendar_data_file):
                base_data = {
                    "yearly_data": {},
                    "last_update": datetime.now().strftime("%Y-%m-%d")
                }
                with open(self.calendar_data_file, 'w', encoding='utf-8') as f:
                    json.dump(base_data, f, ensure_ascii=False, indent=2)
            
            with open(self.calendar_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            year = datetime.strptime(date_str, "%Y-%m-%d").year
            month = datetime.strptime(date_str, "%Y-%m-%d").month
            
            if str(year) not in data["yearly_data"]:
                data["yearly_data"][str(year)] = {}
            
            if str(month) not in data["yearly_data"][str(year)]:
                data["yearly_data"][str(year)][str(month)] = {}
            
            # حفظ نسبة الإنجاز
            data["yearly_data"][str(year)][str(month)][date_str] = completed_percentage
            data["last_update"] = datetime.now().strftime("%Y-%m-%d")
            
            with open(self.calendar_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving calendar data: {e}")
            return False
    
    def get_daily_habits_from_file(self, date_str):
        """الحصول على عادات يوم محدد من الملف"""
        try:
            if os.path.exists(HABITS_FILE):
                with open(HABITS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # البحث عن عادات التاريخ المحدد
                if "daily_habits" in data and date_str in data["daily_habits"]:
                    return data["daily_habits"][date_str]
            
            return []
        except Exception as e:
            print(f"Error loading habits for date {date_str}: {e}")
            return []
    
    def get_month_progress(self, year, month):
        """الحصول على بيانات تقدم شهر معين"""
        try:
            if not os.path.exists(self.calendar_data_file):
                return {}
            
            with open(self.calendar_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            year_data = data["yearly_data"].get(str(year), {})
            month_data = year_data.get(str(month), {})
            
            return month_data
        except:
            return {}
    
    def get_arabic_day_name(self, day_index):
        """الحصول على اسم اليوم بالعربية"""
        days = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"]
        return days[day_index]
    
    def get_arabic_day_short(self, day_index):
        """الحصول على اسم اليوم المختصر"""
        days = ["أحد","إثنين","ثلاثاء","أربعاء","خميس","جمعة","سبت"]
        return days[day_index]
    
    def get_arabic_month_name(self, month):
        """الحصول على اسم الشهر بالعربية"""
        months = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
        return months.get(month, "")
    
    def get_view(self):
        """إرجاع واجهة صفحة التقويم"""
        current_year = self.current_date.year
        current_month = self.current_date.month
        month_progress = self.get_month_progress(current_year, current_month)
        
        # إنشاء التقويم
        cal = calendar.Calendar(calendar.SUNDAY)
        month_days = cal.monthdayscalendar(current_year, current_month)
        
        # رأس الصفحة مع أزرار التنقل
        # استخدام AppBar مباشرة للحصول على نفس مظهر بقية الصفحات
        header = AppBar(
            leading=IconButton(  
                # زر العودة هنا
                icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD_IOS,
                icon_color=Colors.WHITE,
                on_click=lambda e: self.go_back(),
                tooltip="رجوع"
            ),
            title=Row(
                controls=[

            
            # عنوان الشهر
                    Container(
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        content=Column(
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                Text(
                                    f"{self.get_arabic_month_name(current_month)} {current_year}",
                                    size=24,
                                    color=Colors.WHITE,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT
                                ),
                                Text(
                                    f"التقويم الشهري",
                                    size=16,
                                    color=Colors.WHITE,
                                    font_family=BUTTON_FONT
                                )
                            ]
                        )
                    ),
            
                    Container(width=10),
            
            # أزرار التنقل بين الشهور
                    Row(
                        controls=[
                            IconButton(
                                icon=Icons.CHEVRON_LEFT,
                                icon_color=Colors.WHITE,
                                on_click=self.prev_month,
                                tooltip="الشهر التالي"
                            ),
                            IconButton(
                                icon=Icons.CHEVRON_RIGHT,
                                icon_color=Colors.WHITE,
                                on_click=self.next_month,
                                tooltip="الشهر السابق"
                            )
                        ],
                        spacing=5
                    )
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=CrossAxisAlignment.CENTER
            ),
            bgcolor=Colors.BLUE_700,
            center_title=False,  # لأننا نتحكم في التمركز يدويًا
            elevation=0,  # إزالة الظل إذا أردت
            toolbar_height=100,  # 👈 هنا نجعل الشريط أطول (الافتراضي عادة 56)
        )
        
        # إحصائيات الشهر
        summary_stats = self.get_month_summary(current_year, current_month, month_progress)
        
        stats_row = Container(
            padding=15,
            bgcolor=Colors.BLUE_50,
            content=Row(
                controls=[
                    # أيام الإنجاز
                    Container(
                        expand=True,
                        padding=10,
                        bgcolor=Colors.WHITE,
                        border_radius=10,
                        content=Column(
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                Text("أيام الإنجاز", size=14, color=Colors.BLUE_700, font_family=BUTTON_FONT),
                                Text(str(summary_stats["productive_days"]), 
                                     size=28, 
                                     color=Colors.GREEN_700,
                                     weight=FontWeight.BOLD,
                                     font_family=BUTTON_FONT)
                            ]
                        )
                    ),
                    
                    Container(width=10),
                    
                    # متوسط الإنجاز
                    Container(
                        expand=True,
                        padding=10,
                        bgcolor=Colors.WHITE,
                        border_radius=10,
                        content=Column(
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                Text("متوسط الإنجاز", size=14, color=Colors.BLUE_700, font_family=BUTTON_FONT),
                                Text(f"{summary_stats['avg_progress']:.0f}%", 
                                     size=28, 
                                     color=Colors.BLUE_700,
                                     weight=FontWeight.BOLD,
                                     font_family=BUTTON_FONT)
                            ]
                        )
                    ),
                    
                    Container(width=10),
                    
                    # أفضل يوم
                    Container(
                        expand=True,
                        padding=10,
                        bgcolor=Colors.WHITE,
                        border_radius=10,
                        content=Column(
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                Text("أفضل يوم", size=14, color=Colors.BLUE_700, font_family=BUTTON_FONT),
                                Text(f"{summary_stats['best_day_percentage']:.0f}%", 
                                     size=28, 
                                     color=Colors.PURPLE_700,
                                     weight=FontWeight.BOLD,
                                     font_family=BUTTON_FONT)
                            ]
                        )
                    )
                ]
            )
        )
        
        # رؤوس الأيام
        arabic_days = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"]
        
        day_headers = Row(
            controls=[
                Container(
                    expand=True,
                    height=50,
                    alignment=ft.Alignment(0, 0),
                    bgcolor=Colors.BLUE_100,
                    border_radius=5,
                    margin=ft.Margin.symmetric(horizontal=1),
                    content=Text(
                        day,
                        size=12,
                        color=Colors.BLUE_800,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    )
                ) for day in arabic_days
            ]
        )
        
        # شبكة الأيام
        days_grid = Column(
            spacing=5,
            controls=[]
        )
        
        for week in month_days:
            week_row = Row(
                spacing=5,
                controls=[]
            )
            
            for day in week:
                if day == 0:  # يوم خارج الشهر
                    week_row.controls.append(
                        Container(
                            expand=True,
                            height=70,
                            bgcolor=Colors.GREY_100,
                            border_radius=10
                        )
                    )
                else:
                    day_str = f"{current_year}-{current_month:02d}-{day:02d}"
                    progress = month_progress.get(day_str, 0)
                    
                    # الحصول على اسم اليوم
                    try:
                        date_obj = datetime.strptime(day_str, "%Y-%m-%d")
                        day_of_week = date_obj.weekday()
                        day_of_week = (day_of_week + 1) % 7  # 0 = الأحد، 6 = السبت
                        day_name = self.get_arabic_day_short(day_of_week)
                    except:
                        day_name = ""
                    
                    # تحديد اللون حسب نسبة الإنجاز
                    if progress == 0:
                        bg_color = Colors.WHITE
                        text_color = Colors.GREY_600
                        day_name_color = Colors.GREY_500
                    elif progress < 30:
                        bg_color = "#FFE5E5"  # أحمر فاتح
                        text_color = Colors.RED_700
                        day_name_color = Colors.RED_600
                    elif progress < 70:
                        bg_color = "#FFF4E5"  # برتقالي فاتح
                        text_color = Colors.ORANGE_700
                        day_name_color = Colors.ORANGE_600
                    else:
                        bg_color = "#E5FFE5"  # أخضر فاتح
                        text_color = Colors.GREEN_700
                        day_name_color = Colors.GREEN_600
                    
                    # إذا كان اليوم هو اليوم الحالي
                    is_today = (day == datetime.now().day and 
                               current_month == datetime.now().month and 
                               current_year == datetime.now().year)
                    
                    day_container = Container(
                        expand=True,
                        height=70,
                        bgcolor=bg_color,
                        border=ft.Border.all(3, Colors.BLUE_300 if is_today else Colors.TRANSPARENT),
                        border_radius=10,
                        alignment=ft.Alignment(0, 0),
                        on_click=lambda e, d=day_str, p=progress: self.show_day_details(d, p) if p > 0 else None,
                        content=Column(
                            spacing=2,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                # اسم اليوم
                                Text(
                                    day_name,
                                    size=12,
                                    color=day_name_color,
                                    font_family=BUTTON_FONT,
                                    weight=FontWeight.BOLD
                                ),
                                
                                # رقم اليوم
                                Text(
                                    str(day),
                                    size=20,
                                    color=text_color,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT
                                ),
                                
                                # شريط التقدم
                                Container(
                                    height=6,
                                    width=40,
                                    bgcolor=self.get_progress_color(progress),
                                    border_radius=3,
                                    margin=ft.Margin.only(top=3)
                                ) if progress > 0 else Container(height=6)
                            ]
                        )
                    )
                    
                    week_row.controls.append(day_container)
            
            days_grid.controls.append(week_row)
        
        # وسيلة الإيضاح
        legend = Container(
            padding=15,
            alignment=ft.Alignment(0, 0),  
            bgcolor=Colors.WHITE,
            border_radius=10,
            margin=ft.Margin.only(top=10),
            content=Column(
                horizontal_alignment=CrossAxisAlignment.CENTER,  
                spacing=10,
                controls=[
                    Text("وسيلة إيضاح:", size=14, color=Colors.BLUE_700, weight=FontWeight.BOLD, font_family=BUTTON_FONT),
                    Row(
                        alignment=MainAxisAlignment.CENTER,  
                        spacing=15,
                        controls=[
                            Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=5),
                                bgcolor="#E5FFE5",
                                border_radius=8,
                                content=Text("70% فما فوق", size=12, color=Colors.GREEN_700, font_family=BUTTON_FONT)
                            ),
                            Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=5),
                                bgcolor="#FFF4E5",
                                border_radius=8,
                                content=Text("30-70%", size=12, color=Colors.ORANGE_700, font_family=BUTTON_FONT)
                            ),
                            Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=5),
                                bgcolor="#FFE5E5",
                                border_radius=8,
                                content=Text("أقل من 30%", size=12, color=Colors.RED_700, font_family=BUTTON_FONT)
                            ),
                            Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=5),
                                bgcolor=Colors.WHITE,
                                border_radius=8,
                                border=ft.Border.all(2, Colors.BLUE_300),
                                content=Text("اليوم الحالي", size=12, color=Colors.BLUE_700, font_family=BUTTON_FONT)
                            )
                        ]
                    )
                ]
            )
        )
        
        # المحتوى الرئيسي
        main_content = Container(
            expand=True,
            content=Column(
                controls=[
                    stats_row,
                    Container(height=10),
                    day_headers,
                    Container(height=5),
                    days_grid,
                    Container(height=10),
                    legend,
                    Container(height=10),
                    # زر تصدير البيانات
                    Container(
                        padding=15,
                        content=FilledButton(
                            "تصدير بيانات التقويم",
                            icon=Icons.DOWNLOAD,
                            on_click=self.export_calendar_data,
                            style=ButtonStyle(
                                bgcolor=Colors.GREEN_600,
                                color=Colors.WHITE,
                                padding=ft.Padding.only(left=20, right=20, top=12, bottom=12),
                                shape=RoundedRectangleBorder(radius=10),
                            ),
                            height=45,
                            width=250
                        ),
                        alignment=ft.Alignment(0, 0)
                    )
                ],
                scroll=ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.Padding.symmetric(horizontal=15, vertical=10)
        )
        
        return View(
            route="/calendar",
            controls=[
                header,
                main_content,
            ],
            bgcolor="#f5f5f5",
            padding=0,
            spacing=0,
        )
    
    def get_progress_color(self, percentage):
        """الحصول على لون حسب نسبة الإنجاز"""
        if percentage == 0:
            return Colors.TRANSPARENT
        elif percentage < 30:
            return Colors.RED_400
        elif percentage < 70:
            return Colors.ORANGE_400
        else:
            return Colors.GREEN_400
    
    def get_month_summary(self, year, month, month_progress):
        """حساب ملخص إحصائيات الشهر"""
        if not month_progress:
            return {
                "productive_days": 0,
                "avg_progress": 0,
                "best_day_percentage": 0
            }
        
        productive_days = len([p for p in month_progress.values() if p > 0])
        avg_progress = sum(month_progress.values()) / len(month_progress) if month_progress else 0
        best_day_percentage = max(month_progress.values()) if month_progress else 0
        
        return {
            "productive_days": productive_days,
            "avg_progress": avg_progress,
            "best_day_percentage": best_day_percentage
        }
    
    def show_day_details(self, date_str, percentage):
        """عرض تفاصيل يوم معين"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        arabic_day = self.get_arabic_day_name(date_obj.weekday())
        
        # الحصول على عادات اليوم
        day_habits = self.get_daily_habits_from_file(date_str)
        completed_habits = sum(1 for habit in day_habits if habit["completed"])
        total_habits = len(day_habits)
        
        # إنشاء قائمة العادات المكتملة وغير المكتملة
        habits_list = ListView(
            height=200,  # ارتفاع ثابت للقائمة
            controls=[]
        )
        
        for habit in day_habits:
            habits_list.controls.append(
                Container(
                    content=Row(
                        controls=[
                            Icon(
                                Icons.CHECK_CIRCLE if habit["completed"] else Icons.RADIO_BUTTON_UNCHECKED,
                                size=20,
                                color=Colors.GREEN if habit["completed"] else Colors.GREY
                            ),
                            Container(width=10),
                            Text(
                                habit["text"],
                                size=14,
                                color=Colors.BLACK if not habit["completed"] else Colors.GREY_600,
                                font_family=BUTTON_FONT,
                                style=TextStyle(
                                    decoration=TextDecoration.LINE_THROUGH if habit["completed"] else None
                                ),
                                max_lines=3,  # تحديد عدد الأسطر القصوى
                                overflow=TextOverflow.ELLIPSIS  # إضافة علامة ... إذا كا
                            )
                        ]
                    ),
                    padding=ft.Padding.symmetric(vertical=5)
                )
            )
        
        dialog = AlertDialog(
            title=Text(f"📊 تفاصيل يوم {date_str}", font_family=BUTTON_FONT),
            content=Column(
                spacing=10,
                scroll=ScrollMode.AUTO,
                height=400,
                controls=[
                    Text(f"اليوم: {arabic_day}", font_family=BUTTON_FONT, size=14),
                    Text(f"نسبة الإنجاز: {percentage:.1f}%", font_family=BUTTON_FONT, size=16, weight=FontWeight.BOLD),
                    Text(f"العادات: {completed_habits}/{total_habits} مكتملة", font_family=BUTTON_FONT, size=14),
                    Container(
                        height=12,
                        width=250,
                        bgcolor=Colors.GREY_200,
                        border_radius=6,
                        padding=0,
                        content=Container(
                            width=percentage * 2.5,
                            height=12,
                            bgcolor=self.get_progress_color(percentage),
                            border_radius=6
                        )
                    ),
                    Text(
                        self.get_progress_message(percentage),
                        font_family=BUTTON_FONT,
                        color=self.get_progress_color(percentage),
                        size=14
                    ),
                    Divider(height=10),
                    Text("العادات في هذا اليوم:", font_family=BUTTON_FONT, size=14, weight=FontWeight.BOLD),
                    Container(
                        content=habits_list,
                        height=200,
                        width=300,
                        padding=10,
                        bgcolor=Colors.GREY_50,
                        border_radius=8
                    ) if day_habits else Text("لا توجد عادات مسجلة لهذا اليوم", font_family=BUTTON_FONT, size=14, color=Colors.GREY)
                ]
            ),
            actions=[
                Container(
                    TextButton(
                        "حسناً", 
                        on_click=lambda e: [setattr(dialog, "open", False), safe_update(self.page)],
                        style=ButtonStyle(
                            color=Colors.BLUE,
                            padding=15
                        )
                    ),
                    alignment=ft.Alignment(0, 0)
                )
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        safe_update(self.page)
    
    def _close_dialog(self, dialog):
        """إغلاق الـ Dialog وإزالته من الـ overlay"""
        try:
            dialog.open = False
            if dialog in self.page.overlay:
                self.page.overlay.remove(dialog)
            safe_update(self.page)
        except Exception:
            pass

    def get_progress_message(self, percentage):
        """الحصول على رسالة حسب نسبة الإنجاز"""
        if percentage == 0:
            return "لم يتم تسجيل إنجاز في هذا اليوم"
        elif percentage < 30:
            return "مستوى إنجاز منخفض"
        elif percentage < 70:
            return "مستوى إنجاز متوسط"
        elif percentage < 90:
            return "مستوى إنجاز جيد"
        else:
            return "مستوى إنجاز ممتاز! 🎉"
    
    def prev_month(self, e):
        """الانتقال إلى الشهر السابق"""
        self.current_date = self.current_date.replace(day=1)
        self.current_date = self.current_date - timedelta(days=1)
        self.current_date = self.current_date.replace(day=1)
        self.page.views[-1] = self.get_view()
        safe_update(self.page)
    
    def next_month(self, e):
        """الانتقال إلى الشهر التالي"""
        self.current_date = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = self.current_date.replace(day=1)
        self.page.views[-1] = self.get_view()
        safe_update(self.page)
    
    def go_back(self):
        """العودة إلى صفحة الأهداف اليومية"""
        handle_back(self.page)
    
    def export_calendar_data(self, e):
        """تصدير بيانات التقويم"""
        try:
            if not os.path.exists(self.calendar_data_file):
                _show_snack(self.page, "❌ لا توجد بيانات للتصدير", Colors.RED, 3000)
                return
            
            with open(self.calendar_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            export_file = f"calendar_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            _show_snack(self.page, f"✅ تم تصدير البيانات إلى: {export_file}", Colors.GREEN, 3000)
        except Exception as e:
            _show_snack(self.page, f"❌ خطأ في تصدير البيانات: {str(e)}", Colors.RED, 3000)
# ============ صفحة أهدافك اليومية المعدلة ============

class DailyGoalsPage:
    def __init__(self, page):
        self.page = page
        self.habits = self.load_habits_for_today()  # تحميل عادات اليوم الحالي
        self.stats = self.get_daily_stats()
        self.habits_list_view = None  # سنقوم بتهيئته لاحقاً
        
        # حقل إضافة عادة مخصصة
        self.custom_habit_field = TextField(
            hint_text="اكتب عادتك الجديدة هنا...",
            width=300,
            height=50,
            border_radius=10,
            content_padding=15,
            filled=True,
            fill_color="#f1f2f3",
            border_color=Colors.BLUE,
            text_style=TextStyle(font_family=BUTTON_FONT, size=16, color=Colors.BLACK),
        )
        self.categories = ["صحة", "دين", "عمل", "تعليم", "اجتماعي", "مخصص"]
    
    def get_arabic_day_name(self, day_index):
        """الحصول على اسم اليوم بالعربية"""
        days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        return days[day_index]
    
    def get_arabic_month_name(self, month):
        """الحصول على اسم الشهر بالعربية"""
        months = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
        return months.get(month, f"شهر {month}")
    
    def load_habits_for_today(self):
        """تحميل العادات ليوم محدد (اليوم الحالي)"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(HABITS_FILE):
            with open(HABITS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # البحث عن عادات اليوم الحالي
            if "daily_habits" in data and today_str in data["daily_habits"]:
                return data["daily_habits"][today_str]
            
            # إذا لم تكن هناك عادات لليوم الحالي، إنشاء عادات جديدة
            default_habits = self.get_default_habits()
            
            # حفظ العادات الجديدة ليوم اليوم
            if "daily_habits" not in data:
                data["daily_habits"] = {}
            
            data["daily_habits"][today_str] = default_habits
            
            # حفظ التغييرات
            with open(HABITS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return default_habits
        
        # إذا لم يكن الملف موجوداً، إنشاؤه
        return self.init_habits_file_for_today()
    
    def get_default_habits(self):
        """إرجاع العادات الافتراضية"""
        return [
            {"id": 1, "text": "🕌 الالتزام بالصلاة", "completed": False, "custom": False, "category": "دين"},
            {"id": 2, "text": "🌙 الصيام", "completed": False, "custom": False, "category": "دين"},
            {"id": 3, "text": "📚 الدراسة والتعليم", "completed": False, "custom": False, "category": "تعليم"},
            {"id": 4, "text": "🏋️‍♂️ تمارين رياضية", "completed": False, "custom": False, "category": "صحة"},
            {"id": 5, "text": "💼 الالتزام بالعمل", "completed": False, "custom": False, "category": "عمل"},
            {"id": 18, "text": "😴 أذكار قبل النوم", "completed": False, "custom": False, "category": "دين"},
            {"id": 6, "text": "🌤️ أذكار الصباح", "completed": False, "custom": False, "category": "دين"},
            {"id": 7, "text": "🌛 أذكار المساء", "completed": False, "custom": False, "category": "دين"},
            {"id": 8, "text": "📖 قراءة القرآن", "completed": False, "custom": False, "category": "دين"},
            {"id": 9, "text": "⏰ الاستيقاظ مبكرًا", "completed": False, "custom": False, "category": "صحة"},
            {"id": 10, "text": "🙏 صلاة الضحى", "completed": False, "custom": False, "category": "دين"},
            {"id": 11, "text": "🙏 صلاة الوتر", "completed": False, "custom": False, "category": "دين"},
            {"id": 12, "text": "😊 الابتسامة", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 13, "text": "💚 صدقة ( عمل خير )", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 14, "text": "😌 غض البصر", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 15, "text": "🙂 حفظ اللسان", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 16, "text": "❤️ بر الوالدين", "completed": False, "custom": False, "category": "اجتماعي"},
            {"id": 17, "text": "🌷 صلة الرحم", "completed": False, "custom": False, "category": "اجتماعي"},
        ]
    
    def init_habits_file_for_today(self):
        """تهيئة ملف العادات لليوم الحالي"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_habits = self.get_default_habits()
        
        data = {
            "daily_habits": {
                today_str: default_habits
            },
            "history": []
        }
        
        with open(HABITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return default_habits
    
    def save_habits_for_today(self, habits):
        """حفظ العادات لليوم الحالي"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(HABITS_FILE):
            with open(HABITS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"daily_habits": {}, "history": []}
        
        if "daily_habits" not in data:
            data["daily_habits"] = {}
        
        data["daily_habits"][today_str] = habits
        
        with open(HABITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_new_custom_habit(self, text, category="مخصص"):
        """إضافة عادة مخصصة جديدة لليوم الحالي"""
        if not text or not text.strip():
            return False
        
        # البحث عن أعلى ID في عادات اليوم الحالي
        max_id = max([habit["id"] for habit in self.habits], default=0)
        
        new_habit = {
            "id": max_id + 1,
            "text": text.strip(),
            "completed": False,
            "custom": True,
            "category": category
        }
        
        self.habits.append(new_habit)
        self.save_habits_for_today(self.habits)
        return True
    
    def remove_custom_habit(self, habit_id):
        """حذف عادة مخصصة من عادات اليوم الحالي"""
        # تصفية العادات المخصصة فقط
        self.habits = [habit for habit in self.habits if not (habit["id"] == habit_id and habit.get("custom"))]
        self.save_habits_for_today(self.habits)
        return True
    
    def toggle_habit_completion(self, habit_id):
        """تبديل حالة إنجاز العادة لليوم الحالي"""
        for habit in self.habits:
            if habit["id"] == habit_id:
                habit["completed"] = not habit["completed"]
                break
        
        self.save_habits_for_today(self.habits)
        return True
    
    def get_daily_stats(self):
        """الحصول على إحصائيات اليوم الحالي"""
        completed = sum(1 for habit in self.habits if habit["completed"])
        total = len(self.habits)
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "completed": completed,
            "total": total,
            "percentage": percentage
        }
    
    def show_calendar_page(self, e):
        """عرض صفحة التقويم الكاملة"""
        self.save_today_progress()
        
        # الانتقال إلى صفحة التقويم
        self.page.views.append(HabitCalendarPage(self.page).get_view())
        safe_update(self.page)
    
    def save_today_progress(self):
        """حفظ تقدم اليوم الحالي في ملف التقويم"""
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            completed = sum(1 for habit in self.habits if habit["completed"])
            total = len(self.habits)
            percentage = (completed / total * 100) if total > 0 else 0
            
            # حفظ في ملف التقويم
            calendar_data_file = "calendar_data.json"
            
            if not os.path.exists(calendar_data_file):
                base_data = {
                    "yearly_data": {},
                    "last_update": datetime.now().strftime("%Y-%m-%d")
                }
                with open(calendar_data_file, 'w', encoding='utf-8') as f:
                    json.dump(base_data, f, ensure_ascii=False, indent=2)
            
            with open(calendar_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            year = datetime.now().year
            month = datetime.now().month
            
            if str(year) not in data["yearly_data"]:
                data["yearly_data"][str(year)] = {}
            
            if str(month) not in data["yearly_data"][str(year)]:
                data["yearly_data"][str(year)][str(month)] = {}
            
            data["yearly_data"][str(year)][str(month)][today_str] = percentage
            data["last_update"] = datetime.now().strftime("%Y-%m-%d")
            
            with open(calendar_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"Error saving today's progress: {e}")
    
    def update_habit_ui(self, habit_id, habit_item):
        """تحديث واجهة عادة محددة بدون إعادة تحميل الصفحة"""
        # العثور على العادة وتحديث حالتها
        for habit in self.habits:
            if habit["id"] == habit_id:
                habit["completed"] = not habit["completed"]
                break
        
        # حفظ التغييرات
        self.save_habits_for_today(self.habits)
        
        # تحديث الإحصائيات
        self.stats = self.get_daily_stats()
        
        # تحديث دائرة التقدم والإحصائيات
        self.update_stats_ui()
        
        # تحديث واجهة العادة المحددة فقط
        self.update_single_habit_item(habit_id, habit_item)
        
        # حفظ التقدم في التقويم
        self.save_today_progress()
        
        safe_update(self.page)
    
    def update_single_habit_item(self, habit_id, habit_item):
        """تحديث عنصر عادة واحد فقط"""
        habit = next((h for h in self.habits if h["id"] == habit_id), None)
        if not habit:
            return
        
        is_completed = habit["completed"]
        is_custom = habit.get("custom", False)
        category = habit.get("category", "عام")
        
        # تحديث محتوى العنصر
        habit_item.content = Row(
            controls=[
                Container(
                    width=55,
                    height=55,
                    border_radius=27,
                    bgcolor=Colors.GREEN if is_completed else Colors.GREY_200,
                    border=ft.Border.all(2, Colors.GREEN if is_completed else Colors.GREY_400),
                    alignment=ft.Alignment(0, 0),
                    on_click=lambda e, h_id=habit_id, item=habit_item: self.update_habit_ui(h_id, item),
                    content=Icon(
                        Icons.CHECK if is_completed else Icons.ADD,
                        color=Colors.WHITE if is_completed else Colors.GREY_600,
                        size=30 if is_completed else 24
                    )
                ),
                
                Container(
                    expand=True,
                    padding=ft.Padding.only(left=15, right=10),
                    content=Column(
                        spacing=4,
                        controls=[
                            Text(
                                habit["text"],
                                size=18,
                                color=Colors.BLACK if not is_completed else Colors.GREY_600,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.RIGHT,
                                max_lines=2,
                                overflow=TextOverflow.ELLIPSIS,
                                style=TextStyle(
                                    decoration=TextDecoration.LINE_THROUGH if is_completed else None
                                )
                            ),
                            Row(
                                controls=[
                                    Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                        border_radius=10,
                                        bgcolor=Colors.BLUE_100 if is_custom else Colors.GREEN_100,
                                        content=Text(
                                            category,
                                            size=12,
                                            color=Colors.BLUE_700 if is_custom else Colors.GREEN_700,
                                            font_family=BUTTON_FONT,
                                        )
                                    ),
                                    Text(
                                        "مخصصة" if is_custom else "افتراضية",
                                        size=12,
                                        color=Colors.GREY_600,
                                        font_family=BUTTON_FONT,
                                    )
                                ],
                                spacing=5
                            )
                        ]
                    )
                ),
                
                IconButton(
                    icon=Icons.DELETE_OUTLINE,
                    icon_size=24,
                    icon_color=Colors.RED_400,
                    visible=is_custom,
                    on_click=lambda e, h_id=habit_id: self.delete_habit(h_id),
                    tooltip="حذف العادة المخصصة"
                ) if is_custom else Container(width=40)
            ],
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=CrossAxisAlignment.CENTER
        )
    
    def update_stats_ui(self):
        """تحديث واجهة الإحصائيات فقط"""
        completed_count = self.stats["completed"]
        total_count = self.stats["total"]
        progress_percentage = self.stats["percentage"]
        
        # البحث عن عنصر الإحصائيات في الصفحة وتحديثه
        for control in self.stats_container.content.controls:
            if isinstance(control, Container) and hasattr(control, 'content'):
                if isinstance(control.content, Stack):
                    # تحديث دائرة التقدم
                    for stack_item in control.content.controls:
                        if isinstance(stack_item, Container) and stack_item.content:
                            if isinstance(stack_item.content, Column):
                                for text_item in stack_item.content.controls:
                                    if isinstance(text_item, Text):
                                        if '/' in str(text_item.value):
                                            text_item.value = f"{completed_count}/{total_count}"
                                        elif '%' in str(text_item.value):
                                            text_item.value = f"{progress_percentage:.0f}% إنجاز"
    
    def toggle_habit(self, habit_id):
        """تبديل حالة إنجاز العادة"""
        self.toggle_habit_completion(habit_id)
        
        # تحديث البيانات
        self.habits = self.load_habits_for_today()
        self.stats = self.get_daily_stats()
        
        # حفظ التقدم في التقويم
        self.save_today_progress()
        
        # إظهار رسالة نجاح
        habit = next((h for h in self.habits if h["id"] == habit_id), None)
        if habit:
            status = "مكتملة ✅" if habit["completed"] else "غير مكتملة"
            _show_snack(self.page, f"تم تحديث: {habit['text']} ({status})", Colors.GREEN, 1500)
        # تحديث الصفحة
        self.page.views[-1] = self.get_view()
        safe_update(self.page)
    
    def add_custom_habit_handler(self, e):
        """معالج إضافة عادة مخصصة جديدة"""
        text = self.custom_habit_field.value
        
        if not text or not text.strip():
            _show_snack(self.page, "⚠️ يرجى كتابة نص العادة", Colors.ORANGE, 2000)
        else:
            if self.add_new_custom_habit(text, "مخصص"):
                self.custom_habit_field.value = ""
                self.habits = self.load_habits_for_today()
                
                _show_snack(self.page, f"✅ تم إضافة عادة جديدة: {text}", Colors.GREEN, 2000)
                # تحديث الصفحة
                self.page.views[-1] = self.get_view()
                safe_update(self.page)
            else:
                _show_snack(self.page, "❌ حدث خطأ في الإضافة", Colors.RED, 2000)
    
    def delete_habit(self, habit_id):
        """حذف عادة مخصصة مباشرة"""
        habit_to_delete = next((h for h in self.habits if h["id"] == habit_id and h.get("custom")), None)
    
        if habit_to_delete:
            # حذف العادة مباشرة
            if self.remove_custom_habit(habit_id):
                self.habits = self.load_habits_for_today()
            
            # إظهار رسالة نجاح
            _show_snack(self.page, f"✅ تم حذف العادة: {habit_to_delete['text']}", Colors.GREEN, 1500)
            # تحديث الصفحة
            self.page.views[-1] = self.get_view()
            safe_update(self.page)
    
    def reset_day(self, e):
        """إعادة تعيين جميع العادات لليوم الحالي"""
        for habit in self.habits:
            habit["completed"] = False
        
        self.save_habits_for_today(self.habits)
        self.habits = self.load_habits_for_today()
        
        _show_snack(self.page, "🔄 تم إعادة تعيين جميع العادات بنجاح", Colors.BLUE, 2000)
        # تحديث الصفحة
        self.page.views[-1] = self.get_view()
        safe_update(self.page)
    
    def get_view(self):
        """إرجاع واجهة الصفحة"""
        # تحديث الإحصائيات
        self.habits = self.load_habits_for_today()
        self.stats = self.get_daily_stats()
        
        completed_count = self.stats["completed"]
        total_count = self.stats["total"]
        progress_percentage = self.stats["percentage"]
        
        # عرض تاريخ اليوم
        today = datetime.now()
        arabic_day = self.get_arabic_day_name(today.weekday())
        month_name = self.get_arabic_month_name(today.month)
        display_date = f"{arabic_day}، {today.day} {month_name} {today.year}"
        
        # قائمة العادات
        self.habits_list_view = ListView(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=15, vertical=10)
        )
        
        for habit in self.habits:
            habit_id = habit["id"]
            habit_text = habit["text"]
            is_completed = habit["completed"]
            is_custom = habit.get("custom", False)
            category = habit.get("category", "عام")
            
            # إنشاء عنصر العادة
            habit_item = Container(
                height=85,
                margin=ft.Margin.only(bottom=10),
                bgcolor=Colors.WHITE,
                border_radius=15,
                border=ft.Border.all(1, Colors.GREY_300),
                shadow=BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=Colors.with_opacity(0.1, Colors.BLACK),
                    offset=Offset(0, 2)
                ),
                padding=ft.Padding.symmetric(horizontal=15, vertical=12),
                data=habit_id,
            )
            
            habit_item.content = Row(
                controls=[
                    Container(
                        width=55,
                        height=55,
                        border_radius=27,
                        bgcolor=Colors.GREEN if is_completed else Colors.GREY_200,
                        border=ft.Border.all(2, Colors.GREEN if is_completed else Colors.GREY_400),
                        alignment=ft.Alignment(0, 0),
                        on_click=lambda e, h_id=habit_id, item=habit_item: self.update_habit_ui(h_id, item),
                        content=Icon(
                            Icons.CHECK if is_completed else Icons.ADD,
                            color=Colors.WHITE if is_completed else Colors.GREY_600,
                            size=30 if is_completed else 24
                        )
                    ),
                    
                    Container(
                        expand=True,
                        padding=ft.Padding.only(left=15, right=10),
                        content=Column(
                            spacing=4,
                            controls=[
                                Text(
                                    habit_text,
                                    size=18,
                                    color=Colors.BLACK if not is_completed else Colors.GREY_600,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.RIGHT,
                                    max_lines=2,
                                    overflow=TextOverflow.ELLIPSIS,
                                    style=TextStyle(
                                        decoration=TextDecoration.LINE_THROUGH if is_completed else None
                                    )
                                ),
                                Row(
                                    controls=[
                                        Container(
                                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                            border_radius=10,
                                            bgcolor=Colors.BLUE_100 if is_custom else Colors.GREEN_100,
                                            content=Text(
                                                category,
                                                size=12,
                                                color=Colors.BLUE_700 if is_custom else Colors.GREEN_700,
                                                font_family=BUTTON_FONT,
                                            )
                                        ),
                                        Text(
                                            "مخصصة" if is_custom else "افتراضية",
                                            size=12,
                                            color=Colors.GREY_600,
                                            font_family=BUTTON_FONT,
                                        )
                                    ],
                                    spacing=5
                                )
                            ]
                        )
                    ),
                    
                    IconButton(
                        icon=Icons.DELETE_OUTLINE,
                        icon_size=24,
                        icon_color=Colors.RED_400,
                        visible=is_custom,
                        on_click=lambda e, h_id=habit_id: self.delete_habit(h_id),
                        tooltip="حذف العادة المخصصة"
                    ) if is_custom else Container(width=40)
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=CrossAxisAlignment.CENTER
            )
            
            self.habits_list_view.controls.append(habit_item)
        
        # ========== إضافة العادة الجديدة في الأسفل ==========
        add_habit_widget = Container(
            margin=ft.Margin.only(bottom=10, top=5),
            padding=ft.Padding.symmetric(horizontal=15, vertical=12),
            bgcolor=Colors.WHITE,
            border_radius=15,
            border=ft.Border.all(1, Colors.GREY_300),
            shadow=BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=Colors.with_opacity(0.1, Colors.BLACK),
                offset=Offset(0, 2)
            ),
            content=Column(
                spacing=10,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Row(
                        controls=[
                            
                            
                        ],
                        alignment=MainAxisAlignment.CENTER,
                        spacing=5
                    ),
                    
                    Container(
                        width=300,
                        alignment=ft.Alignment(0, 0),
                        content=self.custom_habit_field
                    ),
                    
                    FilledButton(
                        "أضف عادة جديدة",
                        icon=Icons.ADD,
                        on_click=self.add_custom_habit_handler,
                        width=180,
                        height=50,
                        style=ButtonStyle(
                            bgcolor=Colors.BLUE_600,
                            color=Colors.WHITE,
                            shape=RoundedRectangleBorder(radius=10)
                        )
                    )
                ]
            )
        )
        
        # إضافة عنصر إضافة العادة إلى نهاية القائمة
        self.habits_list_view.controls.append(add_habit_widget)
        
        # ========== رأس الصفحة مع الإحصائيات ==========
        self.stats_container = Container(
            margin=ft.Margin.only(bottom=5),
            padding=5,
            bgcolor="#FFFFFF",
            border_radius=15,
            content=Column(
                spacing=10,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    # تاريخ اليوم
                    Container(
                        padding=ft.Padding.symmetric(horizontal=5, vertical=8),
                        bgcolor=Colors.WHITE,
                        border_radius=5,
                        border=ft.Border.all(1, Colors.BLUE_200),
                        content=Row(
                            controls=[
                                Icon(Icons.CALENDAR_TODAY, size=20, color=Colors.BLUE_700),
                                Text(display_date, size=14, color=Colors.BLUE_700, font_family=BUTTON_FONT),
                            ],
                            spacing=5,
                            alignment=MainAxisAlignment.CENTER
                        )
                    ),
                    
                    # دائرة التقدم
                    Container(
                        width=140,
                        height=140,
                        border_radius=70,
                        border=ft.Border.all(5, Colors.BLUE_100),
                        alignment=ft.Alignment(0, 0),
                        content=Stack(
                            controls=[
                                Container(
                                    width=130,
                                    height=130,
                                    border_radius=65,
                                    bgcolor=Colors.WHITE,
                                    alignment=ft.Alignment(0, 0),
                                    content=Column(
                                        spacing=2,
                                        horizontal_alignment=CrossAxisAlignment.CENTER,
                                        controls=[
                                            Text(
                                                f"{completed_count}/{total_count}",
                                                size=32,
                                                color=Colors.BLUE_800,
                                                weight=FontWeight.BOLD,
                                                font_family=BUTTON_FONT
                                            ),
                                            Text(
                                                f"{progress_percentage:.0f}% إنجاز",
                                                size=16,
                                                color=Colors.GREEN_700,
                                                font_family=BUTTON_FONT
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    ),
                    
                    Container(height=2),
                    
                    # أزرار التحكم
                    Row(
                        controls=[
                            Container(
                                width=300,
                                height=100,
                                border_radius=10,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                on_click=self.show_calendar_page,
                                content=Stack(
                                    controls=[
                                        Image(
                                            src="assets/icons/tabeeaa.jpg",
                                            width=300,
                                            height=100,
                                            fit=ft.BoxFit.COVER,
                                        ),
                                        Container(
                                            alignment=ft.Alignment(0, 0),
                                            content=Text(
                                                "التقويم الشهري لأهدافك اليومية",
                                                size=20,
                                                color=Colors.BLACK,
                                                weight=FontWeight.BOLD,
                                                font_family=BUTTON_FONT,
                                            ),
                                        ),
                                    ]
                                ),
                                tooltip="عرض التقويم الشهري الكامل"
                            )
                        ],
                        alignment=MainAxisAlignment.CENTER
                    ),
                ]
            )
        )
        
        # المحتوى الرئيسي
        content = Container(
            content=Column(
                controls=[
                    self.stats_container,
                    Container(
                        content=self.habits_list_view,
                        expand=True,
                        padding=ft.Padding.only(bottom=20)
                    ),
                ],
                scroll=ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.Padding.only(bottom=0),
            expand=True
        )

        return View(
            route="/daily_goals",
            controls=[
                AppBar(
                    title=Text("أهدافك اليومية", weight=FontWeight.BOLD, size=18, color=Colors.WHITE, text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page),
                    ),
                ),
                content,
            ],
            bgcolor="#ffffff",
            padding=0,
            spacing=0,
        )
  
# ============ نظام الأذكار المفضلة ============

class MyAzkarManager:
    """مدير أذكار المستخدم — يُعيد تحميل البيانات في كل مرة لضمان التحديث"""

    def __init__(self):
        self._load_azkar()

    def _load_azkar(self):
        try:
            with open("my_azkar.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                # التأكد من أن كل ذكر يحتوي على الحقول المطلوبة
                for azkar in data:
                    if 'date' not in azkar:
                        azkar['date'] = datetime.now().strftime("%Y-%m-%d")
                    if 'icon' not in azkar:
                        azkar['icon'] = "assets/icons/favorite.png"
                self.azkar_list = data
        except:
            self.azkar_list = []
    
    def _save_azkar(self):
        with open("my_azkar.json", 'w', encoding='utf-8') as f:
            json.dump(self.azkar_list, f, ensure_ascii=False, indent=2)
    
    def add_azkar(self, text):
        if not text or not text.strip():
            return False
        
        new_azkar = {
            "id": len(self.azkar_list) + 1,
            "text": text.strip(),
            "icon": "assets/icons/favorite.png",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.azkar_list.append(new_azkar)
        self._save_azkar()
        return True
    
    def remove_azkar(self, azkar_id):
        # تحويل azkar_id إلى int إذا كان str
        try:
            azkar_id = int(azkar_id)
        except:
            pass
            
        # حذف الذكر
        self.azkar_list = [azkar for azkar in self.azkar_list if azkar.get("id") != azkar_id]
        
        # إعادة ترقيم الـ IDs
        for i, azkar in enumerate(self.azkar_list, 1):
            azkar['id'] = i
            
        self._save_azkar()
        return True
    
    def get_all_azkar(self):
        return self.azkar_list

# ============ صفحة إضافة الأذكار ============
class AddAzkarPage:
    def __init__(self, page):
        self.page = page
        self.text_field = TextField(
            hint_text="اكتب ذكرك أو دعاءك هنا...",
            multiline=True,
            min_lines=8,
            max_lines=15,
            width=350,
            border_radius=10,
            content_padding=20,
            filled=True,
            fill_color="#f1f2f3",
            border_color=Colors.BLUE,
            text_style=TextStyle(font_family=BUTTON_FONT, weight=FontWeight.BOLD, size=16, color=Colors.BLACK),
            autofocus=True
        )
    
    def show_snackbar(self, message, color):
        _show_snack(self.page, message, color, 2000)
    
    def get_view(self):
        # Reset the text field value when creating the view
        self.text_field.value = ""
        
        return View(
            route="/add_azkar",
            controls=[
                AppBar(
                    title=Text("إضافة ذكر جديد", weight=FontWeight.BOLD, size=18, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: self.go_back(),
                    ),
                ),
                Container(
                    content=Column(
                        [
                            Container(
                                content=Text(
                                    "أدخل الذكر أو الدعاء:",
                                    size=20,
                                    color=Colors.BLUE,
                                    font_family=BUTTON_FONT,
                                    weight=FontWeight.BOLD,
                                    text_align=TextAlign.CENTER
                                ),
                                padding=20,
                            ),
                            
                            Container(
                                content=self.text_field,
                                padding=20,
                                alignment=ft.Alignment(0, 0)
                            ),
                            
                            Container(height=30),
                            
                            Row(
                                [
                                    FilledButton(
                                        "إلغاء",
                                        on_click=lambda e: self.go_back(),
                                        width=140,
                                        height=50,
                                        style=ButtonStyle(
                                            bgcolor="#d32f2f",
                                            color=Colors.WHITE,
                                            shape=RoundedRectangleBorder(radius=10),
                                            padding=15,
                                        )
                                    ),
                                    Container(width=20),
                                    FilledButton(
                                        "حفظ",
                                        on_click=self.save_azkar,
                                        width=140,
                                        height=50,
                                        style=ButtonStyle(
                                            bgcolor="#388e3c",
                                            color=Colors.WHITE,
                                            shape=RoundedRectangleBorder(radius=10),
                                            padding=15,
                                        )
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER
                            )
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        scroll=ScrollMode.AUTO,
                        expand=True
                    ),
                    padding=20,
                    expand=True
                )
            ],
            bgcolor="#ffffff",
            padding=0,
        )
    
    def go_back(self):
        """العودة إلى صفحة أذكاري"""
        self.text_field.value = ""
        
        if len(self.page.views) > 1:
            self.page.views.pop()
            # تحديث صفحة أذكاري
            self.page.views[-1] = MyAzkarPage(self.page).get_view()
            safe_update(self.page)
        else:
            handle_back(self.page)
    
    def save_azkar(self, e):
        text = self.text_field.value
        
        if not text or not text.strip():
            self.show_snackbar("⚠️ يرجى كتابة نص الذكر", Colors.ORANGE)
            return
        
        manager = MyAzkarManager()
        if manager.add_azkar(text):
            self.show_snackbar("✅ تم حفظ الذكر بنجاح!", Colors.GREEN)
            
            # Reset the text field value
            self.text_field.value = ""
            
            # العودة إلى صفحة أذكاري
            if len(self.page.views) > 1:
                self.page.views.pop()
                # تحديث صفحة أذكاري
                self.page.views[-1] = MyAzkarPage(self.page).get_view()
                safe_update(self.page)
            else:
                handle_back(self.page)
        else:
            self.show_snackbar("❌ حدث خطأ في الحفظ", Colors.RED)
class MyAzkarPage:
    def __init__(self, page):
        self.page = page
        self.manager = MyAzkarManager()

    def show_snackbar(self, message, color):
        _show_snack(self.page, message, color, 2000)

    def get_view(self):
        azkar_list = self.manager.get_all_azkar()

        if not azkar_list:
            content = Column(
                [
                    Container(height=100),
                    Icon(Icons.BOOKMARK_BORDER, size=80, color=Colors.GREY_400),
                    Text(
                        "لا توجد أذكار محفوظة",
                        size=22,
                        color=Colors.BLACK,
                        weight=FontWeight.BOLD,
                        text_align=TextAlign.CENTER
                    ),
                    Text(
                        "اضغط على زر الإضافة لبدء حفظ أذكارك",
                        size=16,
                        color=Colors.GREY_600,
                        text_align=TextAlign.CENTER
                    ),
                    Container(height=30),
                    Button(
                        "➕ إضافة ذكر جديد",
                        on_click=lambda e: self.add_new_azkar(),
                        width=250,
                        height=50,
                        style=ButtonStyle(
                            bgcolor=Colors.BLUE,
                            color=Colors.WHITE,
                            shape=RoundedRectangleBorder(radius=10),
                            padding=15,
                        )
                    )
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                alignment=MainAxisAlignment.CENTER,
                expand=True
            )
        else:
            list_view = ListView(expand=True, spacing=10, padding=10)
            
            for azkar in azkar_list:
                azkar_id = azkar.get("id")
                azkar_text = azkar.get("text", "")

                azkar_container = Container(
                    content=Column(
                        [
                            Row(
                                [
                                    Row(
                                        [
                                            IconButton(
                                                icon=Icons.DELETE,
                                                icon_color=Colors.RED,
                                                icon_size=24,
                                                tooltip="حذف الذكر",
                                                on_click=lambda e, a_id=azkar_id: self.delete_azkar(a_id)
                                            ),
                                        ]
                                    )
                                ],
                                alignment=MainAxisAlignment.SPACE_BETWEEN
                            ),
                            Container(
                                content=Text(
                                    azkar_text,
                                    size=18,
                                    color=Colors.BLACK,
                                    text_align=TextAlign.CENTER,
                                    font_family=BUTTON_FONT,
                                    weight=FontWeight.BOLD,
                                ),
                                alignment=ft.Alignment(0, 0),
                                padding=15,
                                bgcolor="#f8f9fa",
                                border_radius=10,
                                margin=ft.Margin.only(top=1),
                                border=ft.Border.all(1, "#e0e0e0"),
                            ),
                        ]
                    ),
                    bgcolor="#ffffff",
                    border_radius=15,
                    padding=15,
                    border=ft.Border.all(1, "#e0e0e0"),
                    shadow=BoxShadow(
                        spread_radius=0,
                        blur_radius=8,
                        color=Colors.with_opacity(0.15, Colors.BLACK),
                        offset=Offset(0, 2)
                    )
                )
                
                list_view.controls.append(azkar_container)
            
            list_view.controls.append(
                Container(
                    content=Button(
                        "➕ إضافة ذكر جديد",
                        on_click=lambda e: self.add_new_azkar(),
                        width=300,
                        height=55,
                        style=ButtonStyle(
                            bgcolor=Colors.BLUE,
                            color=Colors.WHITE,
                            shape=RoundedRectangleBorder(radius=15),
                            padding=15,
                        )
                    ),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin.only(top=20, bottom=40),
                )
            )
            
            content = list_view

        return View(
            route="/my_azkar",
            controls=[
                AppBar(
                    title=Text("أذكاري", weight=FontWeight.BOLD, size=18, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page),
                    ),
                ),
                Container(
                    content=content,
                    padding=0,
                    expand=True
                ),
            ],
            bgcolor="#f5f5f5",
            padding=0,
            spacing=0,
        )

    def add_new_azkar(self):
        """فتح صفحة إضافة ذكر جديد"""
        # استخدام push_route بدلاً من go
        self.page.views.append(AddAzkarPage(self.page).get_view())
        safe_update(self.page)

    def delete_azkar(self, azkar_id):
        self.manager.remove_azkar(azkar_id)
        self.show_snackbar("✅ تم حذف الذكر بنجاح", Colors.GREEN)
        self.page.views[-1] = self.get_view()
        safe_update(self.page)

        
# ========= فئات المساعدة ============
class AzkarHelper:
    # قائمة بأنواع الأذكار التي نريد إظهار رسالة الإكمال فيها
    COMPLETION_ENABLED_TYPES = [
        "أذكار الصباح",
        "أذكار المساء", 
        "أذكار بعد الصلاة",
        "أذكار قبل النوم",
        "أذكار عظيمة",
        "أذكار قبل النوم",  
        "الصلاة على النبي ﷺ"

        # أضف هنا أنواع الأذكار الأخرى التي تريد الرسالة فيها
    ]

    @staticmethod
    def check_completion(azkar_list, azkar_type, page):
        # التحقق من كل الأذكار في القائمة
        for azkar in azkar_list:
            if azkar["count"] > 0:
                return  # إذا كان هناك ذكر لم يكتمل بعد، نخرج

        # إذا وصلنا هنا، فهذا يعني أن كل الأذكار قد اكتملت
        if azkar_type not in AzkarHelper.COMPLETION_ENABLED_TYPES:
            return

        async def delayed_message():
            await asyncio.sleep(1)
            AzkarHelper.show_completion_message(azkar_type, page)
        page.run_task(delayed_message)

    @staticmethod
    def mark_daily_habit_completed(habit_text, page):
        """وضع علامة صح على عادة يومية محددة في صفحة الأهداف اليومية"""
        try:
        # الحصول على تاريخ اليوم
            today_str = datetime.now().strftime("%Y-%m-%d")
        
        # تحميل عادات اليوم
            if os.path.exists(HABITS_FILE):
                with open(HABITS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # البحث عن عادات اليوم
                if "daily_habits" in data and today_str in data["daily_habits"]:
                    habits = data["daily_habits"][today_str]
                    updated = False
                
                # البحث عن العادة المطلوبة ووضع علامة صح عليها
                    for habit in habits:
                        if habit["text"] == habit_text and not habit["completed"]:
                            habit["completed"] = True
                            updated = True
                            print(f"✅ تم تفعيل العادة: {habit_text}")
                            break
                
                # حفظ التغييرات إذا تم التحديث
                    if updated:
                        data["daily_habits"][today_str] = habits
                        with open(HABITS_FILE, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # تحديث التقويم
                        try:
                            calendar_page = HabitCalendarPage(page)
                            completed = sum(1 for h in habits if h["completed"])
                            total = len(habits)
                            percentage = (completed / total * 100) if total > 0 else 0
                            calendar_page.save_daily_progress(today_str, habits)
                        except Exception as e:
                            print(f"خطأ في تحديث التقويم: {e}")
                    
                    # تحديث صفحة الأهداف إذا كانت مفتوحة
                        for view in page.views:
                            if view.route == "/daily_goals":
                                # تحديث الصفحة الحالية
                                page.views[-1] = DailyGoalsPage(page).get_view()
                                safe_update(page)
                                break
                    
                        return True
        except Exception as e:
            print(f"خطأ في mark_daily_habit_completed: {e}")
        return False

    @staticmethod
    def show_completion_message(azkar_type, page):
        """عرض رسالة الإكمال مع تفعيل العادة اليومية تلقائياً"""
         # تفعيل العادة اليومية المناسبة
        if azkar_type == "أذكار الصباح":
            AzkarHelper.mark_daily_habit_completed("🌤️ أذكار الصباح", page)
        elif azkar_type == "أذكار المساء":
            AzkarHelper.mark_daily_habit_completed("🌛 أذكار المساء", page)
        # الـ Overlay الأساسي
        overlay = Container(
            expand=True,
            bgcolor=Colors.with_opacity(0.55, Colors.BLACK),  # خلفية شفافة فوق كل شيء
            alignment=ft.Alignment(0, 0),
            content=Container(
                width=330,
                height=370,
                padding=ft.Padding.all(25),
                bgcolor=Colors.with_opacity(0.95, "#342897"),
                border_radius=25,
                content=Column(
                    controls=[
                       Icon(Icons.CHECK_CIRCLE, size=50, color="#4CAF50"),
                        Text(
                            "الحمد للَّه",
                            size=22,
                            color="white",
                            text_align=TextAlign.CENTER,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT,
                        ),
                        Text(
                            f"لقد أتممت {azkar_type}\nتقبل الله طاعتكم إن شاء اللَّه",
                            size=18,
                            color="white",
                            text_align=TextAlign.CENTER,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT,
                        ),

                        FilledButton(
                            content=Text(
                                "شارك التطبيق لتعم الفائدة",
                                size=15,
                                color="black",
                                text_align=TextAlign.CENTER,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                            ),
                            style=ButtonStyle(
                                bgcolor="#FF9800",
                                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                                shape=RoundedRectangleBorder(radius=12),
                            ),
                            on_click=lambda _, p=page: _share_app(p)
                        ),

                    # زر الإغلاق
                        IconButton(
                            icon=Icons.CLOSE,
                            icon_color="white",
                            icon_size=40,
                            on_click=lambda _: AzkarHelper.close_completion_message(page),
                        )
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=15,
                )
            )
        )

    # نضيف علامة لتحديده عند الإغلاق
        overlay.completion_overlay = True

    # إضافة إلى OVERLAY الحقيقي للصفحة
        page.overlay.append(overlay)
        safe_update(page)

    @staticmethod
    def close_completion_message(page):
        for item in page.overlay:
            if hasattr(item, "completion_overlay") and item.completion_overlay:
                page.overlay.remove(item)
                safe_update(page)
                break

    @staticmethod
    def decrement_count(e, azkar_list, azkar_type, page):
        btn = e.control
        zikr = btn.data  # هذا هو الذكر الفردي الذي تم النقر عليه

        if zikr["count"] <= 0:
            return

    # تقليل العداد للذكر المنفرد
        zikr["count"] -= 1

        if hasattr(btn, "content") and isinstance(btn.content, Text):
            btn.content.value = str(zikr["count"])

        btn.bgcolor = "#3f8e9e" if zikr["count"] == 0 else "blue"
        btn.update()

    # ✅ تفعيل العادة اليومية عند النقر على الذكر الخامس (أو أي رقم محدد)
        AzkarHelper.mark_daily_habit_on_fifth_click(zikr, azkar_type, page)

    # الآن نتحقق من كل الأذكار في القائمة للرسالة فقط
        AzkarHelper.check_completion(azkar_list, azkar_type, page)

    @staticmethod
    def mark_daily_habit_on_fifth_click(zikr, azkar_type, page):
        """
        تفعيل العادة اليومية عند الوصول إلى النقرة الخامسة أو عندما يكون العداد 0
        """
        try:
        # التحقق إذا كان هذا هو النقرة الخامسة (العداد 0 بعد 5 نقرات)
        # أو يمكنك تعديل الشرط حسب رغبتك
        
        # مثلاً: تفعيل عندما يكون العداد 0 (بعد إكمال الذكر)
            if zikr["count"] == 0:
            # تفعيل العادة المناسبة حسب نوع الذكر
                if azkar_type == "أذكار الصباح":
                    AzkarHelper.mark_daily_habit_completed("🌤️ أذكار الصباح", page)
                    print(f"✅ تم تفعيل عادة أذكار الصباح بعد إكمال الذكر")
                elif azkar_type == "أذكار المساء":
                    AzkarHelper.mark_daily_habit_completed("🌛 أذكار المساء", page)
                    print(f"✅ تم تفعيل عادة أذكار المساء بعد إكمال الذكر")
                elif azkar_type == "أذكار قبل النوم":  # 👈 أضف هذه الحالة
                    AzkarHelper.mark_daily_habit_completed("😴 أذكار قبل النوم", page)
                    print(f"✅ تم تفعيل عادة أذكار قبل النوم بعد إكمال الذكر")
            # يمكنك إضافة المزيد من أنواع الأذكار هنا
            # ...
            
        except Exception as e:
            print(f"خطأ في mark_daily_habit_on_fifth_click: {e}")

    
           
    @staticmethod
    def format_azkar_text(text):
        global _format_cache
        cache_key = (text, current_font_size)
        if cache_key in _format_cache:
            return _format_cache[cache_key]
        
        colors_rules = [
            {"keyword": "بِسْمِ اللَّهِ", "color": "#ec428c"},
            {"keyword": "اللَّهُ لَا إِلَهَ إِلَّا هُوَ", "color": "black"},
            {"keyword": "قُلْ هُوَ ٱللَّهُ أَحَدٌ، ٱللَّهُ ٱلصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ","color": "black"},
            {"keyword": "قُلْ أَعُوذُ", "color": "black"},
            {"keyword": "من قالها", "color": "#0daca6"},
            {"keyword": "رَضيـتُ بِاللهِ", "color": "black"},
            {"keyword": "اللَّهُمَّ", "color": "black"},
            {"keyword": "لا إلهَ", "color": "black"},
            {"keyword": "اللّهُـمَّ ما أَصْبَـحَ", "color": "black"},
            {"keyword": "اللّهُـمَّ بِكَ", "color": "black"},
            {"keyword": "رَضيـتُ بِاللَّهِ رَبَّـاً", "color": "black"},
            {"keyword":"أسْتَغْفِرُ اللَّهَ وَأتُوبُ إلَيْهِ","color": "black"},
            {"keyword":"حُطَّتْ خَطَايَاهُ وَإِنْ", "color": "#0daca6"},
            {"keyword":"سُبْحـانَ", "color": "black"},
            {"keyword":"بِسـمِ اللَّهِ الذي لا يَضُـرُّ مَعَ", "color": "black"},
            {"keyword":"أَصْبَـحْـنا عَلَى فِطْرَةِ الإسْلاَمِ", "color": "black"},
            {"keyword":"من قالها", "color": "#0daca6"},
            {"keyword":"لم يضره من اللَّهِ شيء","color": "#0daca6"},
            {"keyword":"اللّهُـمَّ إِنِّـي أسْـأَلُـكَ العَـفْوَ وَالعـافِـيةَ", "color": "black"},
            {"keyword":"يَا حَيُّ يَا قيُّومُ بِرَحْمَتِكَ", "color": "black"},
            {"keyword":"أَصْبَـحْـنا وَأَصْبَـحْ المُـلكُ للَّهِ", "color": "black"},
            {"keyword":"اللّهُـمَّ عالِـمَ الغَـيْبِ وَالشّـهادَةِ", "color": "black"},
            {"keyword":"اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ على نَبِيِّنَا مُحمَّد", "color": "black"},
            {"keyword":"أَصْبَـحْـنا وَأَصْبَـحْ المُـلكُ للَّهِ", "color": "black"},
            {"keyword":"أسْتَغْفِرُ اللَّهَ العَظِيمَ الَّذِي لاَ إلَهَ إلاَّ هُوَ، الحَيُّ القَيُّومُ، وَأتُوبُ إلَيهِ", "color": "black"},
            {"keyword":"يَا رَبِّ , لَكَ الْحَمْدُ كَمَا يَنْبَغِي لِجَلَالِ وَجْهِكَ , وَلِعَظِيمِ سُلْطَانِكَ", "color": "black"},
            {"keyword":"َا إلَه إلّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءِ قَدِيرِ", "color": "black"},
            {"keyword":"أَعـوذُ بِكَلِمـاتِ اللّهِ التّـامّـاتِ مِنْ شَـرِّ ما خَلَـق", "color": "black"},
            {"keyword":"مائة حسنة، ومُحيت عنه مائة سيئة، وكانت له حرزاً من الشيطان حتى يمسى", "color": "#0daca6"},
            {"keyword":"كانت له عدل عشر رقاب، وكتبت له مئة حسنة، ومحيت عنه مئة سيئة، وكانت له حرزا من الشيطان", "color": "#0daca6"},
            {"keyword":"ذكر طيب", "color": "#0daca6"},
            {"keyword":"من صلى على حين يصبح وحين يمسى ادركته شفاعتى يوم القيامة", "color": "#0daca6"},
            {"keyword":"آمَنَ الرَّسُولُ بِمَا أُنْزِلَ إِلَيْهِ مِنْ رَبِّهِ وَالْمُؤْمِنُونَ", "color": "black"},
            {"keyword":"اللّهُـمَّ ما أَمسى بي مِـنْ نِعْـمَةٍ أَو بِأَحَـدٍ مِـنْ خَلْـقِك", "color": "black"},
            {"keyword":"أَمْسَيْنَا عَلَى فِطْرَةِ الإسْلاَمِ، وَعَلَى كَلِمَةِ الإِخْلاَصِ", "color": "black"},
            {"keyword":"لم يضره من الله شيء", "color": "#0daca6"},
            {"keyword":"من قرأ آيتين من آخر سورة البقرة في ليلة كفتاه", "color": "#0daca6"},
            {"keyword":"أَسْـتَغْفِرُ اللَّه، أَسْـتَغْفِرُ اللَّه، أَسْـتَغْفِرُ اللَّه", "color": "black"},
            {"keyword":"اللّهُـمَّ إِنِّـي أَسْأَلُـكَ عِلْمـاً نافِعـاً وَرِزْقـاً طَيِّـباً ، وَعَمَـلاً مُتَقَـبَّلاً", "color": "black"},
            {"keyword":"اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ", "color": "black"},
            {"keyword":"سُـبْحانَ اللَّهِ", "color": "black"},
            {"keyword":"الحَمْـدُ للَّه", "color": "black"},
            {"keyword":"اللَّهُ أكْـبَر", "color": "black"},
            {"keyword":"دعاء", "color": "#0daca6"},
            {"keyword":"ثلاث", "color": "#0daca6"},
            {"keyword":"عَشْر مَرّات بَعْدَ", "color": "#0daca6"},
            {"keyword":"بَعْد السّلامِ", "color": "#0daca6"},
            {"keyword":"بعد صلاة الصبح والمغرب", "color": "#0daca6"},
            {"keyword":"اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ، كَمَا صَلَّيْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ، إِنَّكَ حَمِيدٌ مَجِيدٌ، اللَّهُمَّ بَارِكْ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ، كَمَا بَارَكْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ، إِنَّكَ حَمِيدٌ مَجِيدٌ", "color": "black"},
            {"keyword":"سُبْحَانَ اللَّهِ", "color": "black"},
            {"keyword":"سُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ", "color": "black"},
            {"keyword":"سُبْحَانَ اللَّهِ  العَظِيمِ وَبِحَمْدِهِ", "color": "black"},
            {"keyword":"سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ", "color": "black"},
            {"keyword":"لَا إلَه إلّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلُّ شَيْءِ قَدِيرِ", "color": "black"},
            {"keyword":"لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ", "color": "black"},
            {"keyword":"الْحَمْدُ للّهِ رَبِّ الْعَالَمِينَ", "color": "black"},
            {"keyword":"الْلَّهُم صَلِّ وَسَلِم وَبَارِك عَلَى سَيِّدِنَا مُحَمَّد", "color": "black"},
            {"keyword":"أستغفر اللَّه", "color": "black"},
            {"keyword":"سُبْحَانَ الْلَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا الْلَّهُ، وَالْلَّهُ أَكْبَرُ", "color": "black"},
            {"keyword":"لَا إِلَهَ إِلَّا اللَّهُ", "color": "black"},
            {"keyword":"الْلَّهُ أَكْبَرُ ", "color": "black"},
            {"keyword":"الْحَمْدُ لِلَّهِ حَمْدًا كَثِيرًا طَيِّبًا مُبَارَكًا فِيهِ", "color": "black"},
            {"keyword":"يكتب له ألف حسنة أو يحط عنه ألف خطيئة", "color": "#0daca6"},
            {"keyword":"تَمْلَآَنِ مَا بَيْنَ السَّمَاوَاتِ وَالْأَرْضِ", "color": "#0daca6"},
            {"keyword":"غرست له نخلة في الجنة (أى عدد)", "color": "#0daca6"},
            {"keyword":"ثقيلتان في الميزان حبيبتان إلى الرحمن (أى عدد)", "color": "#0daca6"},
            {"keyword":"كنز من كنوز الجنة (أى عدد)", "color": "#0daca6"},
            {"keyword":"تملأ ميزان العبد بالحسنات", "color": "#0daca6"},
            {"keyword":"لفعل الرسول صلى الله عليه وسلم", "color": "#0daca6"},
            {"keyword":"أنهن أحب الكلام الى الله، ومكفرات للذنوب، وغرس الجنة، وجنة لقائلهن من النار، وأحب الى النبي عليه السلام مما طلعت عليه الشمس، والْبَاقِيَاتُ الْصَّالِحَات", "color": "#0daca6"},
            {"keyword":"أفضل الذكر لا إله إلاّ الله", "color": "#0daca6"},
            {"keyword":"من قال الله أكبر كتبت له عشرون حسنة وحطت عنه عشرون سيئة. الله أكبر من كل شيء", "color": "#0daca6"},
            {"keyword":"خير الدنيا والآخرة", "color": "#0daca6"},
            {"keyword":"قَالَ النَّبِيُّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ ،لَقَدْ رَأَيْتُ اثْنَيْ عَشَرَ مَلَكًا يَبْتَدِرُونَهَا، أَيُّهُمْ يَرْفَعُهَا", "color": "#0daca6"},
            {"keyword":"قَالَ النَّبِيُّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ ،عَجِبْتُ لَهَا ، فُتِحَتْ لَهَا أَبْوَابُ السَّمَاءِ", "color": "#0daca6"},
            {"keyword":"في كل مره تحط عنه عشر خطايا ويرفع له عشر درجات ويصلي الله عليه عشرا وتعرض على الرسول صلى الله عليه وسلم (أى عدد)", "color": "#0daca6"},
            {"keyword":"دعـــاء النـــزول في مكــان", "color": "#0daca6"},
            {"keyword":"دعـاء من استصعب عليه أمر", "color": "#0daca6"},
            {"keyword":"دعـاء الخوف من الشــرك", "color": "#0daca6"},
            {"keyword":"ما يقال في المجلس", "color": "#0daca6"},
            {"keyword":"كفارة المجلس", "color": "#0daca6"},
            {"keyword":"دعـاء الغـضـب", "color": "#0daca6"},
            {"keyword":"ما يعوذ به الأولاد", "color": "#0daca6"},
            {"keyword":"دعـاء صـلاة الاستخـارة", "color": "#0daca6"},
            {"keyword":"دعـاء سجود التلاوة", "color": "#0daca6"},
            {"keyword":"دعـــــاء الاستفــتــــاح", "color": "#0daca6"},
            {"keyword":"عنــــد فعــــل الذنب أو ارتكاب المعصية", "color": "#0daca6"},
            {"keyword":"سيد الاستغفار", "color": "#0daca6"},
            {"keyword":"مايقول ويفعل من أذنب ذنباً", "color": "#0daca6"},
            {"keyword":"ضع يدك على الذي تألَّم من جسدك وقل: بسم اللَّه ،ثلاثاً ،وقل سبع مرات: أعوذُ باللَّهِ وقُدْرَتِهِ من شَرِّ مَا أَجِدُ واُحَاذِرُ", "color": "black"},
            {"keyword":"أدعية للمتوفى (ذكور)", "color": "#0daca6"},
            {"keyword":"أدعية للمتوفية (إناث)", "color": "#0daca6"},
            {"keyword":"أدعية للميّت الطفل الصغير (ذكر أو أنثى)", "color": "#0daca6"},
            {"keyword":"الدّعاء للميّت في صّلاة الجنازة", "color": "#0daca6"},
            {"keyword":"رواه البخاري (834) ومسلم (6869) عن أبي بكر", "color": "#0daca6"},
            {"keyword":"رواه البخاري", "color": "#0daca6"},
            {"keyword":"رواه مسلم", "color": "#0daca6"},
            {"keyword":"رواه ", "color": "#0daca6"},
            {"keyword":"الدعاء", "color": "black"},
            {"keyword":"يشوص فاه بالسواك، اي  يدلكه بالسواك", "color": "#0daca6"},
            {"keyword":"عَنْ وَجْهِهِ بِيَدِهِ", "color": "#0daca6"},
            {"keyword":"لحديث", "color": "#0daca6"},
            {"keyword":"بعد أن يختار أحد أدعية السجود، يسن له أن يدعوا بما شاء،لأن أَقْرَبُ مَا يَكُونُ الْعَبْدُ مِنْ رَبِّهِ وَهُوَ سَاجِدٌ، فَأَكْثِرُوا الدُّعَاءَ.", "color": "#0daca6"},
            {"keyword":"وردت صيغ أخرى للتشهد قريبة من هذا.", "color": "#0daca6"},
            {"keyword":"دعاء القنوت يكون في الركعة الأخيرة من صلاة الوتر بعد الركوع ، وإذا جعله قبل الركوع فلا بأس ، إلا أنه بعد الركوع أفضل ، ويرفع يديه إلى صدره ولا يرفعها كثيراً . القنوت عند النوازل سنة في جميع الصلوات الخمس وهو في صلاة المغرب والفجر آكد.", "color": "#0daca6"},
            {"keyword":"علية السلام.", "color": "#0daca6"},
            {"keyword":"دُعاء خطبة الجمعة", "color": "#0daca6"},
            {"keyword":"دُعاء القنوت", "color": "#0daca6"},
            {"keyword":"أدعية بعد التشهد الأخير وقبل السلام", "color": "#0daca6"},
            {"keyword":"التشهد الأخير", "color": "#0daca6"},
            {"keyword":"التشهد الأول", "color": "#0daca6"},
            {"keyword":"دُعاء سجود التلاوة", "color": "#0daca6"},
            {"keyword":"أدعية الجلوس بين السجدتين", "color": "#0daca6"},
            {"keyword":"أدعية السجود", "color": "#0daca6"},
            {"keyword":"أدعية الرفع من الركوع", "color": "#0daca6"},
            {"keyword":"أدعية الركوع", "color": "#0daca6"},
            {"keyword":"أدعية استفتاح الصلاة", "color": "#0daca6"},
            {"keyword":"ما يقال عند سماع الأذان", "color": "#0daca6"},
            {"keyword":"ما يقال بعد سماع الأذان", "color": "#0daca6"},
            {"keyword":"ما يقال بين الأذان والإقامة", "color": "#0daca6"},
            {"keyword":"نص صيغة الأذان", "color": "#0daca6"},
            {"keyword":" نص صيغة أذان الفجر", "color": "#0daca6"},
            {"keyword":"نص صيغة الإقامة", "color": "#0daca6"},
            {"keyword":"الذكر عند الخلاء ", "color": "#0daca6"},
            {"keyword":"الذكر بعد الخروج من الخلاء ", "color": "#0daca6"},
            {"keyword":"أذكار الدخول إلى المنزل ", "color": "#0daca6"},
            {"keyword":"أذكار الخروج من المنزل ", "color": "#0daca6"},
            {"keyword":"الذكر عند الطعام والشراب ", "color": "#0daca6"},            
            {"keyword":"الذكر عند شرب اللبن ", "color": "#0daca6"},
            {"keyword":"الذكر عند الفراغ من الطعام والشراب ", "color": "#0daca6"},
            {"keyword":"أذكار الضيف ", "color": "#0daca6"},
            {"keyword":"هدى النبى فى الشرب ", "color": "#0daca6"},
            {"keyword":"دُعَاءُ الذَّهَابِ إلَى المَسْجِدِ", "color": "#0daca6"},
            {"keyword":"دُعَاءُ دُخُولِ المَسْجِدِ", "color": "#0daca6"},
            {"keyword":"دُعَاءُ الخُرُوجِ مِنَ المَسْجِدِ", "color": "#0daca6"},
            {"keyword":"الذكر قبل الوضوء", "color": "#0daca6"},
            {"keyword":"الذكر بعد الوضوء", "color": "#0daca6"},

        ]
        
        fallback_colors = ["black", "black", "black", "black", "black"]
        
        text_spans = []

        lines = text.splitlines(keepends=True)

        for line in lines:
            content = line.rstrip("\n")
            newlines = line[len(content):]  # "\n" أو "\n\n" أو ""

    # لو السطر فاضي تمامًا → نضيف المسافة بس
            if not content.strip():
                if newlines:
                    text_spans.append(
                        TextSpan(
                            newlines,
                            style=TextStyle(
                                size=current_font_size,
                                height=1.7,
                            )
                        )
                    )
                continue

            line_color = None
            for rule in colors_rules:
                if rule["keyword"] in content:
                    line_color = rule["color"]
                    break

            if not line_color:
                line_index = len(text_spans) % len(fallback_colors)
                line_color = fallback_colors[line_index]

            text_spans.append(
                TextSpan(
                    content + newlines,  # 👈 نفس \n اللي المستخدم كتبهم
                    style=TextStyle(
                        color=line_color,
                        size=current_font_size,
                        font_family=FONT_NAME,
                        weight=FontWeight.BOLD,
                        height=1.7,
                    )
                )
            )

        
        _format_cache[cache_key] = text_spans
        return text_spans
    from typing import Callable

# ============ فئات الصفحات ============
class HomePage:

    # ── ألوان النظام ──────────────────────────────────────────
    PRIMARY       = "#4C3FCB"
    PRIMARY_LIGHT = "#6B5FDD"
    PRIMARY_GRAD1 = "#3D3099"
    CARD_BG       = "#FFFFFF"
    PAGE_BG       = "#F4F6FB"
    TEXT_DARK     = "#1A1A2E"
    TEXT_MUTED    = "#8A8FAD"
    BOTTOM_BG     = "#FFFFFF"
    DIVIDER_COLOR = "#EAEDF5"

    # ── دالة مساعدة: حساب التاريخ الهجري ────────────────────
    @staticmethod
    def _to_hijri(gy, gm, gd):
        if (gy > 1582) or ((gy == 1582) and (gm > 10)) or ((gy == 1582) and (gm == 10) and (gd > 14)):
            jd = (int((1461 * (gy + 4800 + int((gm - 14) / 12))) / 4) +
                  int((367 * (gm - 2 - 12 * int((gm - 14) / 12))) / 12) -
                  int((3 * int((gy + 4900 + int((gm - 14) / 12)) / 100)) / 4) +
                  gd - 32075)
        else:
            jd = (367 * gy - int((7 * (gy + 5001 + int((gm - 9) / 7))) / 4)
                  + int((275 * gm) / 9) + gd + 1729777)
        l  = jd - 1948440 + 10632
        n  = int((l - 1) / 10631)
        l  = l - 10631 * n + 354
        j  = ((int((10985 - l) / 5316)) * (int((50 * l) / 17719))
               + (int(l / 5670)) * (int((43 * l) / 15238)))
        l  = (l - (int((30 - j) / 15)) * (int((17719 * j) / 50))
               - (int(j / 16)) * (int((15238 * j) / 43)) + 29)
        hm = int((24 * l) / 709)
        hd = l - int((709 * hm) / 24)
        hy = 30 * n + j - 30
        months = ["المحرم","صفر","ربيع الأول","ربيع الآخر",
                  "جمادى الأولى","جمادى الآخرة","رجب","شعبان",
                  "رمضان","شوال","ذو القعدة","ذو الحجة"]
        return hd, months[hm - 1], hy

    # ── دالة مساعدة: تحويل الوقت من 24 ساعة إلى 12 ساعة ──────────
    @staticmethod
    def _format_to_12h(time_str):
        """تحويل وقت من صيغة 24 ساعة إلى 12 ساعة"""
        try:
            if not time_str or ':' not in time_str:
                return time_str
                
            # تنظيف الوقت من أي نصوص إضافية
            time_part = time_str.split(" ")[0].strip()
            hours, minutes = map(int, time_part.split(':'))
            
            # تحديد الفترة (صباحاً/مساءً)
            period = "ص" if hours < 12 else "م"
            
            # تحويل إلى نظام 12 ساعة
            hours_12 = hours % 12
            if hours_12 == 0:
                hours_12 = 12
                
            return f"{hours_12:02d}:{minutes:02d} {period}"
        except Exception as e:
            print(f"خطأ في تحويل الوقت: {e}")
            return time_str

    # ── دالة مساعدة: الحصول على مواقيت الصلاة من الكاش ──────────
    @staticmethod
    def _load_prayer_cache():
        try:
            if os.path.exists("prayer_times_cache.json"):
                with open("prayer_times_cache.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                cache_time = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
                # استخدام الكاش إذا كان حديثاً (أقل من 3 أيام)
                if (datetime.now() - cache_time).days < 3:
                    return data.get("timings", None)
        except Exception as e:
            print(f"خطأ في تحميل الكاش: {e}")
        return None

    # ── دالة مساعدة: الصلاة القادمة والوقت المتبقي ──────────
    @staticmethod
    def _get_next_prayer(timings):
        try:
            # قائمة الصلوات بالترتيب
            prayer_list = [
                ("الفجر", "Fajr"),
                ("الشروق", "Sunrise"),
                ("الظهر", "Dhuhr"),
                ("العصر", "Asr"),
                ("المغرب", "Maghrib"),
                ("العشاء", "Isha")
            ]
            
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H:%M")
            
            # البحث عن الصلاة القادمة
            next_prayer_name = None
            next_prayer_time = None
            
            for prayer_name_ar, prayer_key in prayer_list:
                if prayer_key in timings:
                    prayer_time = timings[prayer_key].split(" ")[0].strip()
                    if prayer_time and current_time_str < prayer_time:
                        next_prayer_name = prayer_name_ar
                        next_prayer_time = prayer_time
                        break
            
            # إذا لم نجد صلاة اليوم، نأخذ أول صلاة لليوم التالي
            if not next_prayer_name:
                next_prayer_name = "الفجر"
                next_prayer_time = timings.get("Fajr", "05:00").split(" ")[0].strip()
            
            # حساب الوقت المتبقي
            if next_prayer_time:
                prayer_hour, prayer_min = map(int, next_prayer_time.split(':'))
                prayer_datetime = current_time.replace(
                    hour=prayer_hour, 
                    minute=prayer_min, 
                    second=0, 
                    microsecond=0
                )
                
                # إذا كان وقت الصلاة قد مضى، نضيف يوماً
                if prayer_datetime <= current_time:
                    prayer_datetime += timedelta(days=1)
                
                # حساب الفرق
                diff = prayer_datetime - current_time
                total_seconds = int(diff.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                return next_prayer_name, next_prayer_time, hours, minutes, seconds
            
        except Exception as e:
            print(f"خطأ في حساب الصلاة القادمة: {e}")
        
        return "الفجر", "05:00", 0, 0, 0

    @staticmethod
    def create(page: Page):
        now = datetime.now()
        hd, hmonth, hy = HomePage._to_hijri(now.year, now.month, now.day)

        # تحية حسب الوقت
        hour = now.hour
        if   4  <= hour < 12: greeting = "صباح النور ☀️"
        elif 12 <= hour < 17: greeting = "نهارك مبارك 🌤️"
        elif 17 <= hour < 20: greeting = "مساء الخير 🌅"
        else:                  greeting = "ليلة طيبة 🌙"

        weekdays_ar = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
        day_ar = weekdays_ar[now.weekday()]

        # نصائح قرآنية
        tips_texts = [
            "أَكْثِرُوا مِنَ الذِّكْرِ فَإِنَّهُ نُورٌ لَكُمْ فِي الدُّنْيَا وَالْآخِرَةِ",
            "مَنْ ذَكَرَ اللَّهَ كَثِيرًا فَقَدْ أَفْلَحَ وَفَازَ بِرِضْوَانِهِ",
            "الذِّكْرُ سَبَبٌ لِطُمَأْنِينَةِ الْقَلْبِ وَسَعَادَةِ الرُّوحِ",
            "حَافِظْ عَلَى أَذْكَارِ الصَّبَاحِ وَالْمَسَاءِ تَكُنْ فِي حِمَايَةِ اللَّهِ",
            "لَا تَشْغَلْكَ الدُّنْيَا عَنْ ذِكْرِ اللَّهِ فَهُوَ خَيْرُ الْأَعْمَالِ",
            "اجْعَلْ لِسَانَكَ رَطْبًا بِذِكْرِ اللَّهِ فِي كُلِّ حِينٍ",
            "الذِّكْرُ يُنِيرُ الْقَلْبَ وَيُزِيلُ الْهُمُومَ وَالْأَحْزَانَ",
            "مَا مِنْ عَبْدٍ يَذْكُرُ اللَّهَ إِلَّا ذَكَرَهُ اللَّهُ فِي مَلَأٍ خَيْرٍ مِنْهُ",
            "حَافِظْ عَلَى أَذْكَارِ بَعْدِ الصَّلَوَاتِ فَهِيَ مِنْ أَفْضَلِ الْعِبَادَاتِ",
            "الذِّكْرُ سِلَاحُ الْمُؤْمِنِ وَحِصْنُهُ مِنْ كَيْدِ الشَّيْطَانِ",
            "﴿يَا أَيُّهَا الَّذِينَ آمَنُوا اذْكُرُوا اللَّهَ ذِكْرًا كَثِيرًا﴾ [الأحزاب: 41]",
            "﴿الَّذِينَ آمَنُوا وَتَطْمَئِنُّ قُلُوبُهُم بِذِكْرِ اللَّهِ ۗ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ﴾ [الرعد: 28]",
            "﴿وَأَقِمِ الصَّلَاةَ لِذِكْرِي﴾ [طه: 14]",
            "﴿وَاذْكُرِ اسْمَ رَبِّكَ﴾",
            "﴿رَبِّ اغْفِرْ وَارْحَمْ﴾",
            "﴿رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً﴾",
            "﴿رَبِّ زِدْنِي عِلْمًا﴾",
            "﴿وَاسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ﴾",
            "﴿إِنَّ مَعَ الْعُسْرِ يُسْرًا﴾",
            "﴿فَإِنَّ مَعَ الْعُسْرِ يُسْرًا﴾",
            "﴿فَإِذَا قَضَيْتُم مَّنَاسِكَكُمْ فَاذْكُرُوا اللَّهَ كَذِكْرِكُمْ آبَاءَكُمْ أَوْ أَشَدَّ ذِكْرًا﴾ [البقرة: 200]",
            "﴿فَاذْكُرُوا اللَّهَ عِنْدَ الْمَشْعَرِ الْحَرَامِ وَاذْكُرُوهُ كَمَا هَدَاكُمْ﴾ [البقرة: 198]",
            "﴿وَقَالَ رَبُّكُمُ ادْعُونِي أَسْتَجِبْ لَكُمْ﴾ [غافر: 60]",
            "﴿وَإِذَا سَأَلَكَ عِبَادِي عَنِّي فَإِنِّي قَرِيبٌ ۖ أُجِيبُ دَعْوَةَ الدَّاعِ إِذَا دَعَانِ﴾ [البقرة: 186]",
            "﴿رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ﴾ [البقرة: 201]",
            "﴿رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً﴾ [آل عمران: 8]",
            "﴿رَبَّنَا إِنَّنَا سَمِعْنَا مُنَادِيًا يُنَادِي لِلْإِيمَانِ أَنْ آمِنُوا بِرَبِّكُمْ فَآمَنَّا﴾ [آل عمران: 193]",
            "﴿فَسُبْحَانَ اللَّهِ حِينَ تُمْسُونَ وَحِينَ تُصْبِحُونَ﴾ [الروم: 17]",
            "﴿وَسَبِّحْ بِحَمْدِ رَبِّكَ قَبْلَ طُلُوعِ الشَّمْسِ وَقَبْلَ الْغُرُوبِ﴾ [ق: 39]",
            "﴿فَسَبِّحْ بِاسْمِ رَبِّكَ الْعَظِيمِ﴾ [الواقعة: 74]",
            "﴿وَسَبِّحُوهُ بُكْرَةً وَأَصِيلًا﴾ [الأحزاب: 42]",
            "﴿فَسَبِّحْ بِحَمْدِ رَبِّكَ وَاسْتَغْفِرْهُ﴾ [النصر: 3]",
            "﴿وَأَنِ اسْتَغْفِرُوا رَبَّكُمْ ثُمَّ تُوبُوا إِلَيْهِ﴾ [هود: 3]",
            "﴿وَاسْتَغْفِرُوا اللَّهَ إِنَّ اللَّهَ غَفُورٌ رَّحِيمٌ﴾ [المزمل: 20]",
            "﴿فَقُلْتُ اسْتَغْفِرُوا رَبَّكُمْ إِنَّهُ كَانَ غَفَّارًا﴾ [نوح: 10]",
            "﴿وَالذَّاكِرِينَ اللَّهَ كَثِيرًا وَالذَّاكِرَاتِ أَعَدَّ اللَّهُ لَهُم مَّغْفِرَةً وَأَجْرًا عَظِيمًا﴾ [الأحزاب: 35]",
            "﴿إِنَّ الْمُسْلِمِينَ وَالْمُسْلِمَاتِ وَالْمُؤْمِنِينَ وَالْمُؤْمِنَاتِ وَالْقَانِتِينَ وَالْقَانِتَاتِ﴾ [الأحزاب: 35]",
            "﴿فَإِذَا فَرَغْتَ فَانصَبْ * وَإِلَىٰ رَبِّكَ فَارْغَب﴾ [الشرح: 7-8]",
            "﴿رَبَّنَا لَا تُؤَاخِذْنَا إِن نَّسِينَا أَوْ أَخْطَأْنَا﴾ [البقرة: 286]",
            "﴿رَبَّنَا وَلَا تَحْمِلْ عَلَيْنَا إِصْرًا كَمَا حَمَلْتَهُ عَلَى الَّذِينَ مِن قَبْلِنَا﴾ [البقرة: 286]",
            "﴿رَبَّنَا وَلَا تُحَمِّلْنَا مَا لَا طَاقَةَ لَنَا بِهِ﴾ [البقرة: 286]",
            "﴿رَبَّنَا أَفْرِغْ عَلَيْنَا صَبْرًا وَثَبِّتْ أَقْدَامَنَا﴾ [البقرة: 250]",
            "﴿رَبِّ اجْعَلْنِي مُقِيمَ الصَّلَاةِ وَمِن ذُرِّيَّتِي﴾ [إبراهيم: 40]",
        ]
        random_tip = random.choice(tips_texts)

        # تحميل مواقيت الصلاة من الكاش
        cached_timings = HomePage._load_prayer_cache()
        
        # مواقيت افتراضية
        default_timings = {
            "Fajr": "05:00", 
            "Sunrise": "06:30",
            "Dhuhr": "12:00", 
            "Asr": "15:30",
            "Maghrib": "18:00", 
            "Isha": "19:30",
        }
        
        timings = cached_timings if cached_timings else default_timings

        # حساب الصلاة القادمة
        next_name, next_time_raw, h0, m0, s0 = HomePage._get_next_prayer(timings)

        # عناصر قابلة للتحديث
        countdown_text = Text(
            f"{h0:02d}:{m0:02d}:{s0:02d}",
            size=22,
            weight=FontWeight.BOLD,
            color=Colors.WHITE,
            font_family=BUTTON_FONT,
            text_align=TextAlign.CENTER,
        )
        
        next_prayer_label = Text(
            f"{next_name}",
            size=11,
            color=Colors.with_opacity(0.9, Colors.WHITE),
            font_family=BUTTON_FONT,
            text_align=TextAlign.CENTER,
        )

        # متغير للتحكم في استمرارية العداد
        timer_running = True
        # حفظ الصلاة القادمة لتجنب إعادة الحساب في كل ثانية
        _cached_next = [None, None]  # [name, time_raw]

        async def update_countdown():
            nonlocal timer_running
            while timer_running:
                try:
                    nn, nt, h, m, s = HomePage._get_next_prayer(timings)
                    new_val = f"{h:02d}:{m:02d}:{s:02d}"
                    # تحديث النص مباشرة بدون إعادة رسم الصفحة كلها
                    changed = False
                    if countdown_text.value != new_val:
                        countdown_text.value = new_val
                        changed = True
                    if next_prayer_label.value != nn:
                        next_prayer_label.value = nn
                        changed = True
                    if changed:
                        try:
                            countdown_text.update()
                            next_prayer_label.update()
                        except Exception:
                            pass
                except Exception as ex:
                    if "destroyed" in str(ex).lower() or "session" in str(ex).lower():
                        timer_running = False
                        break
                    print(f"خطأ في تحديث العداد: {ex}")
                await asyncio.sleep(1)

        page.run_task(update_countdown)

        # ── إيقاف العداد تلقائياً عند الانتقال من الصفحة الرئيسية ──
        # نحفظ مرجع دالة الإيقاف في page لتستدعيها go() عند التنقل
        def _stop_home_timer():
            nonlocal timer_running
            timer_running = False
        page._stop_home_timer = _stop_home_timer

        # الصلوات الخمس بصيغة 12 ساعة
        five_prayers = [
            ("الفجر",  HomePage._format_to_12h(timings.get("Fajr", ""))),
            ("الظهر",  HomePage._format_to_12h(timings.get("Dhuhr", ""))),
            ("العصر",  HomePage._format_to_12h(timings.get("Asr", ""))),
            ("المغرب", HomePage._format_to_12h(timings.get("Maghrib", ""))),
            ("العشاء", HomePage._format_to_12h(timings.get("Isha", ""))),
        ]

        # شريط التاريخ
        date_prayer_bar = Container(
            margin=ft.Margin.symmetric(horizontal=12),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=16,
            bgcolor=Colors.with_opacity(0.22, Colors.BLACK),
            border=ft.Border.all(1, Colors.with_opacity(0.3, Colors.WHITE)),
            content=Row(
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            Icon(Icons.NIGHTLIGHT_ROUND, size=19,
                                 color=Colors.with_opacity(0.85, Colors.WHITE)),
                            Text(
                                f"{hd} {hmonth}",
                                size=17,
                                color=Colors.WHITE,
                                font_family=BUTTON_FONT,
                                weight=FontWeight.BOLD,
                                text_align=TextAlign.CENTER,
                            ),
                            Text(
                                f"{hy} هـ",
                                size=17,
                                color=Colors.with_opacity(0.8, Colors.WHITE),
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                            ),
                        ],
                    ),
                    Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            next_prayer_label,
                            Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                border_radius=10,
                                bgcolor=Colors.with_opacity(0.1, Colors.BLACK),
                                border=ft.Border.all(1, Colors.with_opacity(0.5, Colors.WHITE)),
                                content=countdown_text,
                            ),
                            Text(
                                "الوقت المتبقي",
                                size=15,
                                color=Colors.with_opacity(0.75, Colors.WHITE),
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                            ),
                        ],
                    ),
                    Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            Icon(Icons.CALENDAR_TODAY_ROUNDED, size=19,
                                 color=Colors.with_opacity(0.85, Colors.WHITE)),
                            Text(
                                f"{day_ar}",
                                size=17,
                                color=Colors.WHITE,
                                font_family=BUTTON_FONT,
                                weight=FontWeight.BOLD,
                                text_align=TextAlign.CENTER,
                            ),
                            Text(
                                f"{now.day}/{now.month}/{now.year}",
                                size=17,
                                color=Colors.with_opacity(0.8, Colors.WHITE),
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                            ),
                        ],
                    ),
                ],
            ),
        )

        # صف مواقيت الصلوات
        prayer_times_row = Container(
            margin=ft.Margin.symmetric(horizontal=12),
            padding=ft.Padding.symmetric(horizontal=10, vertical=10),
            border_radius=16,
            bgcolor=Colors.with_opacity(0.18, color="#685BDA"),
            border=ft.Border.all(1, Colors.with_opacity(0.25, Colors.WHITE)),
            content=Row(
                alignment=MainAxisAlignment.SPACE_AROUND,
                controls=[
                    Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=3,
                        controls=[
                            Text(
                                name,
                                size=17,
                                color=Colors.BLACK,
                                font_family=BUTTON_FONT,
                                weight=FontWeight.BOLD if name == next_name else FontWeight.NORMAL,
                                opacity=1.0 if name == next_name else 0.72,
                            ),
                            Container(
                                padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                                border_radius=8,
                                bgcolor=Colors.with_opacity(
                                    0.40 if name == next_name else 1.0,
                                    Colors.WHITE,
                                ),
                                border=ft.Border.all(
                                    1 if name == next_name else 0,
                                    Colors.with_opacity(0.65, Colors.WHITE),
                                ),
                                content=Text(
                                    t,
                                    size=13,
                                    color=Colors.BLACK,
                                    font_family=BUTTON_FONT,
                                    weight=FontWeight.BOLD,
                                ),
                            ),
                        ],
                    )
                    for name, t in five_prayers
                ],
            ),
        )

        # النصيحة
        tip_card = Container(
            margin=ft.Margin.symmetric(horizontal=12),
            padding=ft.Padding.symmetric(horizontal=14, vertical=15),
            border_radius=14,
            bgcolor=Colors.with_opacity(1.0, Colors.WHITE),
            border=ft.Border.all(1, Colors.with_opacity(0.25, Colors.BLACK)),
            content=Row(
                spacing=8,
                alignment=MainAxisAlignment.CENTER,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Text(
                        random_tip,
                        size=15,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT,
                        color=Colors.BLACK,
                        text_align=TextAlign.CENTER,
                        expand=True,
                        max_lines=2,
                        overflow=TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )

        # شريط البحث
        search_icon_btn = Container(
            width=36,
            height=36,
            border_radius=18,
            bgcolor=Colors.with_opacity(0.22, Colors.LIGHT_BLUE),
            border=ft.Border.all(1, Colors.with_opacity(0.4, Colors.WHITE)),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: page.navigate("/search"),
            content=Icon(
                Icons.SEARCH_ROUNDED,
                color=Colors.WHITE,
                size=20,
            ),
        )

        top_bar = Container(
            padding=ft.Padding.only(top=48, left=16, right=16, bottom=0),
            content=Row(
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    Text(
                        greeting,
                        size=19,
                        weight=FontWeight.BOLD,
                        color=Colors.GREY_900,
                        font_family=BUTTON_FONT,
                    ),
                    search_icon_btn,
                ],
            ),
        )

        # الهيدر
        header_container = Container(
            height=260,
            padding=0,
            margin=0,
            content=Stack(
                controls=[
                    Container(
                        content=Image(
                            src=current_home_background,
                            width=2000,
                            height=340,
                            fit=ft.BoxFit.FILL,
                            repeat=ft.ImageRepeat.NO_REPEAT,
                        ),
                        shadow=BoxShadow(
                            spread_radius=0,
                            blur_radius=20,
                            color=Colors.with_opacity(0.1, Colors.BLACK),
                            offset=Offset(0, -2),
                        ),
                    ),
                    Container(
                        height=260,
                        padding=ft.Padding.only(bottom=10),
                        content=Column(
                            spacing=8,
                            controls=[
                                top_bar,
                                date_prayer_bar,
                            ],
                        ),
                    ),
                ],
            ),
        )

        # المحتوى تحت الهيدر
        below_header = Container(
            padding=ft.Padding.only(top=10, bottom=4),
            bgcolor=HomePage.PAGE_BG,
            content=Column(
                spacing=8,
                controls=[
                    prayer_times_row,
                    tip_card,
                ],
            ),
        )

        # الفئات والأزرار
        BUTTON_WIDTH = 100
        BUTTON_HEIGHT = 100
        ICON_SIZE = 50

        categories = [
            {
                "title": "الأذكار اليومية",
                "buttons": [
                    {"icon": CUSTOM_ICONS["morning"], "text": "أذكار الصباح", "route": "/azkar_sabah"},
                    {"icon": CUSTOM_ICONS["night"], "text": "أذكار المساء", "route": "/azkar_masaa"},
                    {"icon": CUSTOM_ICONS["mosque"], "text": "أذكار بعد الصلاة", "route": "/azkar_baad_salah"},
                    {"icon": CUSTOM_ICONS["sleep"], "text": "أذكار قبل النوم", "route": "/sleep"},
                    {"icon": CUSTOM_ICONS["wakeup"], "text": "أذكار الإستيقاظ", "route": "/wakeup"},
                    {"icon": CUSTOM_ICONS["sujud"], "text": "أذكار الصلاة", "route": "/sujud"},
                    {"icon": CUSTOM_ICONS["athan5"], "text": "أذكار الآذان", "route": "/athan5"},
                    {"icon": CUSTOM_ICONS["istanbul"], "text": "أذكار المسجد", "route": "/istanbul"},
                    {"icon": CUSTOM_ICONS["wodu50"], "text": "أذكار الوضوء", "route": "/wodu50"},
                    {"icon": CUSTOM_ICONS["azkar_almanzel"], "text": "أذكار المنزل", "route": "/azkar_almanzel"},
                    {"icon": CUSTOM_ICONS["azkar_alkhala"], "text": "أذكار الخلاء", "route": "/azkar_alkhala"},
                    {"icon": CUSTOM_ICONS["azkar_altaaam"], "text": "أذكار الطعام", "route": "/azkar_altaaam"},
                    {"icon": CUSTOM_ICONS["star"], "text": "أذكار عظيمة", "route": "/azkar_azima"},
                    {"icon": CUSTOM_ICONS["tasbih"], "text": "السبحة", "route": "/electronic_tasbih"},
                    {"icon": CUSTOM_ICONS["hajj"], "text": "أذكار الحج والعمرة", "route": "/hajj"},
                ],
            },
            {
                "title": "الصلوات والأدعية",
                "buttons": [
                    {"icon": CUSTOM_ICONS["wudu"], "text": "تعليم الوضوء", "route": "/wudu_learning"},
                    {"icon": CUSTOM_ICONS["learn_prayer"], "text": "كيفية الصلاة", "route": "/learn_prayer"},
                    {"icon": CUSTOM_ICONS["prayer_time"], "text": "مواقيت الصلاة", "route": "/prayer_times"},
                    {"icon": CUSTOM_ICONS["qibla"], "text": "اتجاه القبلة", "route": "/qibla"},
                    {"icon": CUSTOM_ICONS["book"], "text": "آية الكرسي", "route": "/ayat_alkursii"},
                    {"icon": CUSTOM_ICONS["prayer"], "text": "الصلاة على النبي", "route": "/alsalat_ealaa_alnabii"},
                    {"icon": CUSTOM_ICONS["dua"], "text": "أدعية متنوعة", "route": "/adeiat_wa_azkar_mutanawiea"},
                    {"icon": CUSTOM_ICONS["Nabawi"], "text": "أدعية نبوية", "route": "/Nabawi_Mosque"},
                    {"icon": CUSTOM_ICONS["kaaba4"], "text": "أدعية الأنبياء", "route": "/kaaba4"},
                    {"icon": CUSTOM_ICONS["quran80"], "text": "الأدعية القرآنية", "route": "/quran80"},
                    {"icon": CUSTOM_ICONS["jwamea6"], "text": "جوامع الدعاء", "route": "/jwamea6"},
                    {"icon": CUSTOM_ICONS["moon"], "text": "أدعية للمتوفي", "route": "/adeiat_llmtwffy"},
                ],
            },
            {
                "title": "القرآن والسنن",
                "buttons": [
                    {"icon": CUSTOM_ICONS["quran"], "text": "المصحف", "route": "/quran"},
                    {"icon": CUSTOM_ICONS["sunan"], "text": "سنن موقوتة", "route": "/timed_sunan"},
                    {"icon": CUSTOM_ICONS["untimed_sunan"], "text": "سنن غير موقوتة", "route": "/untimed_sunan"},
                    {"icon": CUSTOM_ICONS["library"], "text": "المكتبة الإسلامية", "route": "/islamic_library"},
                    {"icon": CUSTOM_ICONS["youm"], "text": "اليوم النبوي", "route": "/youm"},
                    {"icon": CUSTOM_ICONS["fadl"], "text": "فضل السور", "route": "/fadl"},
                ],
            },
        ]

        categories_content = []
        for category in categories:
            categories_content.append(
                Container(
                    padding=ft.Padding.only(top=18, bottom=6, left=16, right=16),
                    content=Row(
                        vertical_alignment=CrossAxisAlignment.CENTER,
                        controls=[
                            Container(
                                width=4, height=24,
                                border_radius=4,
                                bgcolor=HomePage.PRIMARY,
                            ),
                            Text(
                                category["title"],
                                size=19,
                                weight=FontWeight.BOLD,
                                color=HomePage.TEXT_DARK,
                                font_family=BUTTON_FONT,
                                expand=True,
                            ),
                        ],
                    ),
                )
            )

            buttons_grid = GridView(
                expand=True,
                runs_count=3,
                max_extent=BUTTON_WIDTH + 20,
                run_spacing=10,
                child_aspect_ratio=1.0,
                padding=ft.Padding.symmetric(horizontal=12),
                controls=[],
            )

            for btn in category["buttons"]:
                route_val = btn["route"]
                btn_container = Container(
                    width=BUTTON_WIDTH,
                    height=BUTTON_HEIGHT,
                    border_radius=18,
                    bgcolor=HomePage.CARD_BG,
                    border=ft.Border.all(1, HomePage.DIVIDER_COLOR),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding.all(8),
                    shadow=BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=Colors.with_opacity(0.06, Colors.BLACK),
                        offset=Offset(0, 3),
                    ),
                    ink=True,
                    on_click=lambda e, r=route_val: page.navigate(r),
                    content=Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        alignment=MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            Container(
                                width=ICON_SIZE, height=ICON_SIZE,
                                alignment=ft.Alignment(0, 0),
                                content=Image(
                                    src=btn["icon"],
                                    width=ICON_SIZE, height=ICON_SIZE,
                                    fit=ft.BoxFit.CONTAIN,
                                ),
                            ),
                            Text(
                                btn["text"],
                                size=15,
                                color=HomePage.TEXT_DARK,
                                weight=FontWeight.BOLD,
                                text_align=TextAlign.CENTER,
                                max_lines=2,
                                overflow=TextOverflow.ELLIPSIS,
                                font_family=BUTTON_FONT,
                            ),
                        ],
                    ),
                )
                buttons_grid.controls.append(btn_container)

            categories_content.append(
                Container(content=buttons_grid, padding=ft.Padding.only(bottom=8))
            )

        # شريط التنقل السفلي
        def _nav_item(icon_src=None, icon_name=None, label="",
                      route=None, is_center=False, url=None):
            def _click(e):
                if url:
                    page.run_task(_open_url, url, page)
                elif route:
                    page.navigate(route)

    # حجم الأيقونة حسب نوع العنصر
            icon_size = 48 if is_center else 28  # حجم أكبر للعنصر المركزي
            icon_w = (
                Image(src=icon_src,
                      width=icon_size,
                      height=icon_size,
                      fit=ft.BoxFit.CONTAIN)
                if icon_src
                else Icon(icon_name, size=icon_size, color=HomePage.TEXT_MUTED)
            )

            if is_center:
        # إزالة الخلفية والظل والحدود - فقط أيقونة بدون أي تأثيرات
                return Container(
                    width=80,  # يمكن تعديل هذا الرقم للتحكم في حجم العنصر المركزي
                    height=80,
                    alignment=ft.Alignment(0, -1),
                    on_click=_click,
                      # تأثير النقر فقط
                    content=icon_w,
                )

            return Container(
                on_click=_click,
                
                border_radius=10,
                height=60,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                content=Column(
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    alignment=MainAxisAlignment.CENTER,
                    spacing=3,
                    controls=[
                        icon_w,
                        Text(label, size=10,
                             color=HomePage.TEXT_MUTED,
                             font_family=BUTTON_FONT),
                    ],
                ),
            )

        bottom_nav = Container(
            height=72,
            bgcolor=HomePage.BOTTOM_BG,
            border=ft.Border.only(top=ft.BorderSide(1, HomePage.DIVIDER_COLOR)),
            shadow=BoxShadow(
                spread_radius=0, blur_radius=20,
                color=Colors.with_opacity(0.08, Colors.BLACK),
                offset=Offset(0, -3),
            ),
            padding=ft.Padding.only(bottom=6, top=6),
            content=Row(
                alignment=MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=CrossAxisAlignment.CENTER,
                controls=[
                    _nav_item(icon_src=CUSTOM_ICONS["info"], label="من نحن", route="/about"),
                    _nav_item(icon_src=CUSTOM_ICONS["my_azkar"], label="أذكاري", route="/my_azkar"),
                    _nav_item(icon_src=CUSTOM_ICONS["goals"], is_center=True, route="/daily_goals"),
                    _nav_item(icon_src=CUSTOM_ICONS["calendar"], label="التقويم", route="/calendar"),
                    _nav_item(icon_name=Icons.SETTINGS_OUTLINED, label="الإعدادات", route="/settings"),
                ],
            ),
        )

        # إنشاء الصفحة
        view = View(
            route="/",
            controls=[
                Container(
                    bgcolor=HomePage.PAGE_BG,
                    expand=True,
                    content=Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            header_container,
                            Container(
                                expand=True,
                                content=ListView(
                                    controls=[
                                        below_header,
                                        *categories_content,
                                    ],
                                    spacing=0,
                                    padding=ft.Padding.only(bottom=80),
                                    expand=True,
                                ),
                            ),
                            bottom_nav,
                        ],
                    ),
                )
            ],
            padding=0,
            spacing=0,
            bgcolor=HomePage.PAGE_BG,
        )

        return view

    @staticmethod
    def _on_hover(e):
        if e.data == "true":
            e.control.bgcolor = Colors.with_opacity(0.96, Colors.WHITE)
            e.control.shadow = BoxShadow(
                spread_radius=0, blur_radius=18,
                color=Colors.with_opacity(0.13, HomePage.PRIMARY),
                offset=Offset(0, 5),
            )
            e.control.border = ft.Border.all(1.5, Colors.with_opacity(0.4, HomePage.PRIMARY))
            e.control.scale = Scale(1.06)
        else:
            e.control.bgcolor = HomePage.CARD_BG
            e.control.shadow = BoxShadow(
                spread_radius=0, blur_radius=10,
                color=Colors.with_opacity(0.06, Colors.BLACK),
                offset=Offset(0, 3),
            )
            e.control.border = ft.Border.all(1, HomePage.DIVIDER_COLOR)
            e.control.scale = Scale(1.0)
        e.control.update()

    @staticmethod
    def on_button_hover(e):
        HomePage._on_hover(e)

    
class AzkarPage:
    @staticmethod
    def create(azkar_list, title, route_name, page, show_counter=True):  # أضف show_counter=True
        # حاوية رئيسية
        main_container = Container(
            content=Column(
                scroll=ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment(0, 0),
        )

        # دالة لتحميل المحتوى
        def load_content():
            azkar_widgets = []
            for azkar in azkar_list:
                content_items = [
                    Image(
                        src=azkar["icon"],
                        width=390,
                        height=230,
                        fit=ft.BoxFit.CONTAIN,
                        gapless_playback=True,
                    ) if "icon" in azkar else Container(),
                
                    Container(
                        content=Text(
                            spans=AzkarHelper.format_azkar_text(azkar["text"]),
                            text_align="center"
                        ),
                        alignment=ft.Alignment(0, 0),

                    ),
                    Divider(color=Colors.BLACK, height=30),
                ]
                
                # إضافة زر العداد فقط إذا show_counter=True
                if show_counter:
                    content_items.append(
                        FilledButton(
                            content=Text(
                                str(azkar["count"]),
                                size=40,
                                
                                color="white",
                                text_align=TextAlign.CENTER,
                            ),
                            bgcolor="blue",
                            width=500,
                            height=95,
                            style=ButtonStyle(
                                shape=RoundedRectangleBorder(radius=15),
                                padding=20,
                            ),
                            on_click=lambda e, a=azkar_list, t=title: AzkarHelper.decrement_count(e, a, t, page),
                            data=azkar,
                        )
                    )
                else:
                    # بدلاً من الزر، نعرض عدد التكرارات كنص إذا كان > 1
                    if azkar.get("count", 0) > 1:
                        content_items.append(
                            Container(
                                content=Text(
                                    f"عدد المرات: {azkar['count']}",
                                    size=20,
                                    color="#0daca6",
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.CENTER,
                                ),
                                padding=ft.Padding.only(top=15),
                            )
                        )
                
                content = Column(
                    content_items,
                    spacing=2,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
                
                azkar_widgets.append(
                    Container(
                        content=content,
                        padding=15,
                        border_radius=10,
                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                        alignment=ft.Alignment(0, 0),

                        margin=ft.Margin.only(top=10)
                        
                    )
                )

            # 🔹 إضافة مسافة فارغة في الأسفل (20px) لتوفير مساحة قبل البانر
            azkar_widgets.append(Container(height=55))

            main_container.content.controls = azkar_widgets
            # لا داعي لـ safe_update(page) هنا — سيتم استدعاؤه في route_change

        app_bar = AppBar(
            title=Text(title, size=17, color=Colors.WHITE, text_align=TextAlign.CENTER  ,weight=FontWeight.BOLD),
            bgcolor=APP_BGCOLOR,
            center_title=True,
            leading=IconButton(
                icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                icon_color=Colors.WHITE,
                on_click=lambda e: handle_back(page),
            ),
        )

        ad_overlay = ft.Stack(
            controls=[
                main_container,
                Container(
                    content=fta.BannerAd(
                        unit_id=get_ad_id(page, "banner"),
                        on_error=lambda e: print("BannerAd error:", e.data),
                    ),
                    width=320,
                    height=50,
                    alignment=ft.Alignment(0, 1),
                    bottom=0,
                    left=0,
                    right=0,
                ),
            ],
            expand=True,
        ) if is_mobile(page) else main_container

        view = View(
            route=route_name,
            controls=[
                app_bar,
                ad_overlay,
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            bgcolor="#dee4e4",
            padding=0,
            spacing=0,
        )

        # تحميل المحتوى فوراً
        load_content()

        return view

class LearnPrayerPage:
    @staticmethod
    def create(page: Page): 
        youtube_url = "https://youtu.be/QIi6YSJfPTw?si=tgHI7JBKPijVjzQW"
        youtube_ur2 = "https://youtu.be/FBfPRSi9ZgI?si=tKeRyoeKKfZX8Spl"
        youtube_ur3 = "https://youtu.be/_XQJBfuqTZo?si=m7sx7KSQluQxCxXm"
        youtube_thumbnail = "assets/icons/kayfyytelsalah.webp"
        youtube_thumbnai2 = "assets/icons/tyoub,.webp"
        youtube_thumbnai3 = "assets/icons/tyoub3.webp"
        
        # دالة لفتح الروابط - تعمل على الهاتف والكمبيوتر
        async def open_url_async(url):
            """فتح الرابط بشكل غير متزامن - يعمل على الهاتف والديسكتوب"""
            await _open_url(url, page)
            return True

        def open_video(url):
            """فتح الفيديو"""
            try:
                # تشغيل دالة فتح الرابط في الخلفية
                page.run_task(open_url_async, url)
                
                # عرض رسالة التأكيد
                _show_snack(page, "📺 جاري فتح الفيديو...", Colors.RED, 2000)
                
            except Exception as e:
                print(f"خطأ في فتح الفيديو: {e}")
                # عرض رسالة خطأ
                _show_snack(page, "❌ حدث خطأ في فتح الفيديو", Colors.RED, 2000)
        
        # دالة مساعدة لتأثير التحويم على الفيديو
        def hover_video(e):
            if e.data == "true":
                e.control.scale = 1.02
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=15,
                    color=Colors.with_opacity(0.3, Colors.BLUE),
                    offset=Offset(0, 5)
                )
            else:
                e.control.scale = 1.0
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=0,
                    color=Colors.TRANSPARENT,
                    offset=Offset(0, 0)
                )
            e.control.update()
        
        return View(
            route="/learn_prayer",
            controls=[
                AppBar(
                    title=Text("كيفية الصلاة", weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(page),
                    ),
                ),
                
                Container(
                    content=Column(
                        controls=[
                            Container(height=5),
                            
                            # ===== الفيديو الأول =====
                            Container(
                                content=Column([
                                    # عنوان القسم
                                    Container(
                                        padding=ft.Padding.only(right=10),
                                        content=Text(
                                            "فيديو تعليمي : خطوات الصلاة الصحيحة",
                                            size=16,
                                            weight=FontWeight.BOLD,
                                            color=Colors.BLUE_700,
                                            font_family=BUTTON_FONT,
                                            text_align=TextAlign.CENTER
                                        )
                                    ),
                                    Container(height=5),
                                    
                                    # الفيديو مع زر التشغيل
                                    GestureDetector(
                                        content=Container(
                                            content=Stack(
                                                controls=[
                                                    Image(
                                                        src=youtube_thumbnail,
                                                        width=380,
                                                        height=200,
                                                        fit=ft.BoxFit.COVER,
                                                        border_radius=15,
                                                    ),
                                                    Container(
                                                        Icon(
                                                            Icons.PLAY_CIRCLE_FILLED,
                                                            color=Colors.WHITE,
                                                            size=70,
                                                        ),
                                                        border_radius=50,
                                                        padding=5,
                                                        alignment=ft.Alignment(0, 0),
                                                    )
                                                ],
                                                width=380,
                                                height=200,
                                            ),
                                            alignment=ft.Alignment(0, 0),
                                            border_radius=15,
                                            animate=Animation(200, AnimationCurve.EASE_OUT),
                                            on_hover=hover_video
                                        ),
                                        on_tap=lambda e, url=youtube_url: open_video(url),
                                    ),
                                    
                                    Container(height=10),
                                    
                                    # النص الأول
                                    Container(
                                        content=Column(
                                            controls=[
                                                Text(
                                                    "خطوات الصلاة الصحيحة",
                                                    size=20,
                                                    color="#0daca6",
                                                    weight=FontWeight.BOLD,
                                                    text_align=TextAlign.CENTER,
                                                    font_family=BUTTON_FONT
                                                ),
                                                Divider(height=10, color=Colors.TRANSPARENT),
                                                Container(
                                                    content=Text(
                                                        "قال الشيخ / محمد بن عثيمين رحمه الله :\nالصلاة: عبادة ذات أقوال وأفعال أولها التكبير وآخرها التسليم.\n وإذا أراد الصلاة فإنه يجب عليه أن يتوضأ إن كان عليه حدث أصغر، أو يغتسل إن كان عليه حدث أكبر، أو يتيمم إن لم يجد الماء أو تضرر باستعماله، وينظف بدنه وثوبه ومكان صلاته من النجاسة.\n\nكيفية الصلاة:\n\n1 - أن يستقبل القبلة بجميع بدنه بدون انحراف ولا التفات.\n\n2 - ثم ينوي الصلاة التي يريد أن يصليها بقلبه بدون نطق النية.\n\n3 - ثم يكبر تكبيرة الإحرام فيقول: (الله أكبر) ويرفع يديه إلى حذو منكبيه عند التكبير.\n\n4 - ثم يضع كف يده اليمنى على ظهر كف يده اليسرى فوق صدره.\n\n5 - ثم يستفتح فيقول: (اللهم باعد بيني وبين خطاياي كما باعدت بين المشرق والمغرب. اللهم نقني من خطاياي كما يُنقى الثوب الأبيض من الدنس. اللهم اغسلني من خطاياي بالماء والثلج والبرد).\n\nأو يقول: (سبحانك اللهم وبحمدك، وتبارك اسمك، وتعالى جدك، ولا إله غيرك).\n\n6 - ثم يتعوذ فيقول: (أعوذ بالله من الشيطان الرجيم).\n\n7 - ثم يبسمل ويقرأ الفاتحة فيقول: بِسْمِ اللهِ الرَّحْمنِ الرَّحِيمِ (1) الْحَمْدُ للّهِ رَبِّ الْعَالَمِينَ (2) الرَّحْمـنِ الرَّحِيمِ (3) مَالِكِ يَوْمِ الدِّينِ (4) إِيَّاكَ نَعْبُدُ وإِيَّاكَ نَسْتَعِينُ (5) اهدِنَــــا الصِّرَاطَ المُستَقِيمَ (6) صِرَاطَ الَّذِينَ أَنعَمتَ عَلَيهِمْ غَيرِ المَغضُوبِ عَلَيهِمْ وَلاَ الضَّالِّينَ [الفاتحة:1-7]\n\nثم يقول (آمين) يعني اللهم استجب.\n\n8 - ثم يقرأ ما تيسر من القرآن ويطيل القراءة في صلاة الصبح.\n\n9 - ثم يركع، أي يحني ظهره تعظيماً لله ويُكبر عند ركوعه ويرفع يديه إلى حذو منكبيه. والسنة أن يهصر ظهره ويجعل رأسه حياله ويضع يديه على ركبتيه مفرجتي الأصابع.\n\n10 - ويقول في ركوعه: (سبحان ربي العظيم) ثلاث مرات، وإن زاد: (سبحانك اللهم وبحمدك، اللهم اغفر لي) فحسن.\n\n11 - ثم يرفع رأسه من الركوع قائلاً: (سمع الله لمن حمده) ويرفع يديه حينئذ إلى حذو منكبيه. والمأموم لا يقول سمع الله لمن حمده، وإنما يقول بدلها: (ربنا ولك الحمد).\n\n12 - ثم يقول بعد رفعه: (ربنا ولك الحمد، ملء السماوات والأرض وملء ما شئت من شيء بعد).\n\n13 - ثم يسجد خشوعاً السجدة الأولى ويقول عند سجوده: (الله أكبر) ويسجد على أعضائه السبعة: الجبهة والأنف، والكفين، والركبتين، وأطراف القدمين، ويجافي عضديه عن جنبيه ولا يبسط ذراعيه على الأرض، ويتسبقل برؤوس أصابعه القبلة.\n\n14 - ويقول في سجوده: (سبحان ربي الأعلى) ثلاث مرات، وإن زاد: (سبحانك اللهم ربنا وبحمدك، اللهم اغفر لي) فحسن.\n\n15 - ثم يرفع رأسه من السجود قائلاً: (الله أكبر).\n\n16 - ثم يجلس بين السجدتين على قدمه اليسرى، وينصب قدمه اليمنى، ويضع يده اليمنى على طرف فخذه الأيمن مما يلي ركبته، ويقبض منها الخنصر والبنصر، ويربع السبابة ويحركها عند دعائه، ويجعل طرف الإبهام مقروناً بطرف الوسطى كالحلقة، ويضع يده اليسرى مبسوطة الأصابع على طرف فخذه الأيسر مما يلي الركبة.\n\n17 - ويقول في جلوسه بين السجدتين: (رب اغفر لي وارحمني واهدني وارزقني واجبرني وعافني).\n\n18 - ثم يسجد خشوعاً منه السجدة الثانية كالأولى فيما يُقال ويُفعل، ويكبر عند سجوده.\n\n19 - ثم يقوم من السجدة الثانية قائلاً: (الله أكبر) ويصلي الركعة الثانية كالأولى فيما يُقال ويفعل إلا أنه لا يستفتح فيها.\n\n20 - ثم يجلس بعد انتهاء الركعة الثانية قائلاً: (الله أكبر) ويجلس كما يجلس بين السجدتين سواء.\n\n21 - ويقرأ التشهد في هذا الجلوس فيقول: (التحيات لله والصلوات والطيبات، السلام عليك أيها النبي ورحمة الله وبركاته، السلام علينا وعلى عباد الله الصالحين، أشهد أن لا إله إلا الله وأشهد أن محمداً عبده ورسوله، اللهم صلِّ على محمد وعلى آل محمد كما صليت على إبراهيم وعلى آل إبراهيم إنك حميد مجيد، وبارك على محمد وعلى آل محمد كما باركت على إبراهيم وعلى آل إبراهيم إنك حميد مجيد. أعوذ بالله من عذاب جهنم، ومن عذاب القبر، ومن فتنة المحيا والممات، ومن فتنة المسيح الدجال) ثم يدعو ربه بما أحب من خيري الدنيا والآخرة.\n\n22 - ثم يسلم عن يمينه قائلاً: (السلام عليكم ورحمة الله) وعن يساره كذلك.\n\n23 - وإذا كانت الصلاة ثلاثية أو رباعية وقف عند منتهى التشهد الأول وهو: (أشهد أن لا إله إلا الله وأشهد أن محمداً عبده ورسوله).\n\n24 - ثم ينهض قائماً قائلاً: (الله أكبر) ويرفع يديه إلى حذو منكبيه حينئذ.\n\n25 - ثم يصلي ما بقي من صلاته على صفة الركعة الثانية، إلا أنه يقتصر على قراءة الفاتحة.\n\n26 - ثم يجلس متوركاً فينصب قدمه اليمنى ويخرج قدمه اليسرى من تحت ساق اليمنى ويُمكن مقعدته من الأرض، ويضع يديه على فخذيه على صفة وضعها في التشهد الأول.\n\n27 - ويقرأ في هذا الجلوس التشهد كله.\n\n28 - ثم يسلم عن يمينه قائلاً: (السلام عليكم ورحمة الله) وعن يساره كذلك.\n\n ",
                                                        size=16,
                                                        color=Colors.BLACK,
                                                        text_align=TextAlign.RIGHT,
                                                        weight=FontWeight.BOLD,
                                                        font_family=BUTTON_FONT,
                                                    ),
                                                    
                                                    padding=10,
                                                    border=ft.Border.all(1, Colors.GREY_300),
                                                    border_radius=10,
                                                    bgcolor=Colors.WHITE
                                                )
                                            ],
                                            spacing=5,
                                            horizontal_alignment=CrossAxisAlignment.CENTER,
                                        ),
                                        padding=0,
                                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                                        border_radius=15,
                                        margin=ft.Margin.symmetric(vertical=10),
                                    ),
                                ]),
                                padding=10,
                                bgcolor="#f0f0f0",
                                border_radius=15,
                                margin=ft.Margin.only(bottom=15)
                            ),
                            
                            # ===== الفيديو الثاني =====
                            Container(
                                content=Column([
                                    Container(
                                        padding=ft.Padding.only(right=10),
                                        content=Text(
                                            "فيديو : سجود السهو",
                                            size=16,
                                            weight=FontWeight.BOLD,
                                            color=Colors.BLUE_700,
                                            font_family=BUTTON_FONT
                                        )
                                    ),
                                    Container(height=5),
                                    
                                    GestureDetector(
                                        content=Container(
                                            content=Stack(
                                                controls=[
                                                    Image(
                                                        src=youtube_thumbnai2,
                                                        width=380,
                                                        height=200,
                                                        fit=ft.BoxFit.COVER,
                                                        border_radius=15,
                                                    ),
                                                    Container(
                                                        Icon(
                                                            Icons.PLAY_CIRCLE_FILLED,
                                                            color=Colors.WHITE,
                                                            size=70,
                                                        ),
                                                        border_radius=50,
                                                        padding=5,
                                                        alignment=ft.Alignment(0, 0),
                                                    )
                                                ],
                                                width=380,
                                                height=200,
                                            ),
                                            alignment=ft.Alignment(0, 0),
                                            border_radius=15,
                                            animate=Animation(200, AnimationCurve.EASE_OUT),
                                            on_hover=hover_video
                                        ),
                                        on_tap=lambda e, url=youtube_ur2: open_video(url),
                                    ),
                                    
                                    Container(height=10),
                                    
                                    Container(
                                        content=Text(
                                            "الشرح الكامل على اليوتيوب لمتى يكون سجود السهو وكيف ؟",
                                            size=16,
                                            color="#0daca6",
                                            weight=FontWeight.BOLD,
                                            text_align=TextAlign.CENTER,
                                            font_family=BUTTON_FONT,
                                        ),
                                        padding=15,
                                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                                        border_radius=15,
                                        margin=ft.Margin.symmetric(vertical=10),
                                    ),
                                ]),
                                padding=10,
                                bgcolor="#f0f0f0",
                                border_radius=15,
                                margin=ft.Margin.only(bottom=15)
                            ),
                            
                            # ===== الفيديو الثالث =====
                            Container(
                                content=Column([
                                    Container(
                                        padding=ft.Padding.only(right=10),
                                        content=Text(
                                            "فيديو : مبطلات الصلاة",
                                            size=16,
                                            weight=FontWeight.BOLD,
                                            color=Colors.BLUE_700,
                                            font_family=BUTTON_FONT
                                        )
                                    ),
                                    Container(height=5),
                                    
                                    GestureDetector(
                                        content=Container(
                                            content=Stack(
                                                controls=[
                                                    Image(
                                                        src=youtube_thumbnai3,
                                                        width=380,
                                                        height=200,
                                                        fit=ft.BoxFit.COVER,
                                                        border_radius=15,
                                                    ),
                                                    Container(
                                                        Icon(
                                                            Icons.PLAY_CIRCLE_FILLED,
                                                            color=Colors.WHITE,
                                                            size=70,
                                                        ),
                                                        border_radius=50,
                                                        padding=5,
                                                        alignment=ft.Alignment(0, 0),
                                                    )
                                                ],
                                                width=380,
                                                height=200,
                                            ),
                                            alignment=ft.Alignment(0, 0),
                                            border_radius=15,
                                            animate=Animation(200, AnimationCurve.EASE_OUT),
                                            on_hover=hover_video
                                        ),
                                        on_tap=lambda e, url=youtube_ur3: open_video(url),
                                    ),
                                    
                                    Container(height=10),
                                    
                                    Container(
                                        content=Text(
                                            "الشرح الكامل على اليوتيوب للأمور التي تبطل الصلاة "
                                            "ولا يجوز فيها سجود السهو.",
                                            size=16,
                                            color="#0daca6",
                                            weight=FontWeight.BOLD,
                                            text_align=TextAlign.CENTER,
                                            font_family=BUTTON_FONT,
                                        ),
                                        padding=15,
                                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                                        border_radius=15,
                                        margin=ft.Margin.symmetric(vertical=10),
                                    ),
                                ]),
                                padding=0,
                                bgcolor="#f0f0f0",
                                border_radius=15,
                                margin=ft.Margin.only(bottom=15)
                            ),
                            
                            Container(height=20)
                        ],
                        scroll=ScrollMode.AUTO,
                        expand=True,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    padding=0,
                    expand=True,
                    bgcolor="#d7d9db"
                ),
            ],
            padding=0,
            spacing=0,
            bgcolor="#d7d9db"
        )

class AboutPage:
    @staticmethod
    def create(page: Page):
        def open_email(e):
            """فتح البريد الإلكتروني - يعمل على الهاتف والديسكتوب"""
            url = "mailto:mohammedahead.7000@gmail.com"
            page.run_task(_open_url, url, page)
            _show_snack(page, "📧 جاري فتح البريد الإلكتروني...", Colors.BLUE_700, 2000)

        return View(
            route="/about",
            controls=[
                AppBar(
                    title=Text("من نحن", weight=FontWeight.BOLD, size=17, color=Colors.WHITE, text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(page),
                    ),
                    
                ),
                Container(
                    content=Column(
                        [
                            # شعار التطبيق
                            Container(
                                content=Image(
                                    src="assets/icons/icon.webp",
                                    width=130,
                                    height=130,
                                    fit=ft.BoxFit.CONTAIN,
                                    border_radius=75,
                                ),
                                padding=10,
                            ),
                            
                            # اسم التطبيق
                            Text(
                                "تطبيق القريب - أذكار المسلم",
                                size=20,
                                weight=FontWeight.BOLD,
                                font_family=FONT_NAME,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER
                            ),
                           
                            Divider(height=20, color="#685BDA",),
                            
                            # وصف التطبيق
                            Container(
                                content=Text(
                                    "تطبيق القريب هو تطبيق إسلامي يهدف إلى تسهيل الوصول إلى الأذكار والأدعية الإسلامية الصحيحة، من خلال تقديم محتوى موثوق مستند إلى القرآن الكريم والسنة النبوية الشريفة، وبأسلوب عصري يناسب جميع المستخدمين.\n\nيهدف تطبيق القريب إلى التقرب إلى الله تعالى، وتعميق صلة المسلم بربه، ونشر الخير والفائدة، من خلال محتوى هادف يجمع بين الدقة الشرعية وسهولة الاستخدام، ليكون رفيقًا يوميًا للمسلم في عبادته.",
                                    size=16,
                                    color=Colors.BLACK,
                                    text_align=TextAlign.RIGHT,
                                    style=TextStyle(
                                        font_family=FONT_NAME,
                                        size=18,
                                        weight=FontWeight.BOLD,
                                        height=1.6,
                                    )
                                ),
                                padding=10,
                                bgcolor="#ffffff",
                                border_radius=15,
                                width=350,
                            ),
                            
                            # زر التواصل - معدل
                            FilledButton(
                                "تواصل معنا",
                                color=Colors.WHITE,
                                icon=Icons.EMAIL,
                                on_click=open_email,
                                style=ButtonStyle(
                                    bgcolor="#0D5F13",
                                    padding=ft.Padding.only(left=30, right=30),
                                ),
                                width=200,
                            ),
                            
                            # أيقونة الصدقة الجارية
                            Container(
                                width=50,
                                height=50,
                                on_click=lambda e: page.navigate("/sadaqa_gariya"),
                                tooltip="صدقة جارية",
                                content=Image(
                                    src=CUSTOM_ICONS["kok"],
                                    width=50,
                                    height=50,
                                    fit=ft.BoxFit.CONTAIN,
                                ),
                            ),
                            
                            # حقوق النشر
                            Container(
                                content=Text(
                                    "جميع الحقوق محفوظة © 2025",
                                    size=14,
                                    color=Colors.GREY_600,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.CENTER
                                ),
                                margin=ft.Margin.only(top=20),
                            ),
                            
                            Container(height=20)
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        scroll=ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=20,
                    expand=True,
                ),
            ],
            padding=0,
            bgcolor="#ffffff",
        )
 
class IslamicLibraryPage:
    @staticmethod
    def create(page: Page):
        # قائمة الكتب الإسلامية
        islamic_books = [
            {
                "title": "رياض الصالحين",
                "author": "الإمام النووي",
                "cover": "assets/books/riyad.webp",
                "pdf_url": "https://drive.google.com/file/d/1vfI14XUROUcgnpONPeNNNt2fEWcOSqtm/view?usp=sharing",
                "category": "حديث",
                "pages": 560,
                "description": "من أهم كتب الحديث جمع فيه الأحاديث الصحيحة الدالة على الترغيب والترهيب"
            },
            {
                "title": "الأربعون النووية",
                "author": "الإمام النووي",
                "cover": "assets/books/arbawoon.webp",
                "pdf_url": "https://drive.google.com/file/d/1gJ8B9UJHqCdTrlTIYA1B2nyMqIpUoiAs/view?usp=sharing",
                "category": "حديث",
                "pages": 120,
                "description": "أشهر وأعظم كتب الحديث التي جمعت أربعين حديثاً من جوامع الكلم"
            },
            {
                "title": "فتح المجيد",
                "author": "عبد الرحمن بن حسن",
                "cover": "assets/books/tawhied.webp",
                "pdf_url": "https://drive.google.com/file/d/1gnDU7Thv8zAjvEWNJPjufFKqsmtrNJwD/view?usp=sharing",
                "category": "عقيدة",
                "pages": 680,
                "description": "شرح كتاب التوحيد للإمام محمد بن عبد الوهاب"
            },
            {
                "title": "زاد المعاد",
                "author": "ابن قيم الجوزية",
                "cover": "assets/books/zad elmaad.webp",
                "pdf_url": "https://drive.google.com/file/d/1_Mm4Xxv1zoyNgCpliDuQSaz--NQpKwuo/view?usp=sharing",
                "category": "فقه وسيرة",
                "pages": 950,
                "description": "من أهم كتب السيرة النبوية والفقه الإسلامي"
            },
            {
                "title": "صحيح البخاري",
                "author": "الإمام البخاري",
                "cover": "assets/books/albukhari.webp",
                "pdf_url": "https://drive.google.com/file/d/1hiktq2YoP3d2Ti2x8InaiIalnxIwgXUf/view?usp=sharing",
                "category": "حديث",
                "pages": 1500,
                "description": "أصح الكتب بعد كتاب الله وأشهر كتب الحديث"
            },
            {
                "title": "صحيح مسلم",
                "author": "الإمام مسلم",
                "cover": "assets/books/elmuslim.webp",
                "pdf_url": "https://drive.google.com/file/d/11YvKapBURDOIu2QGUd7m3dJyVHSVfCwI/view?usp=sharing",
                "category": "حديث",
                "pages": 1400,
                "description": "ثاني كتب الحديث الصحيحة بعد صحيح البخاري"
            },
            {
                "title": "جدد حياتك",
                "author": "الشيخ الغزالي",
                "cover": "assets/books/gadidhayatk.webp",
                "pdf_url": "https://drive.google.com/file/d/1n6wv7WobCI16OMv7sNVrH79dLV8H5ipA/view?usp=sharing",
                "category": "رقائق",
                "pages": 350,
                "description": "كتاب يجمع بين الفكر الإسلامي والتربية النفسية"
            },
            {
                "title": "الصلاة في الإسلام",
                "author": "عبدالله سراج الدين",
                "cover": "assets/books/alsalahfyalislam.webp",
                "pdf_url": "https://drive.google.com/file/d/1n5RJaW1w-r3mnVOC-G1ijSZ4SDKDWLTO/view?usp=sharing",
                "category": "فقه",
                "pages": 420,
                "description": "شرح مفصل لأحكام الصلاة وآدابها وأسرارها"
            },
        ]

        # ألوان التصنيفات
        category_colors = {
            "حديث": "#4CAF50",
            "عقيدة": "#9C27B0",
            "فقه وسيرة": "#FF9800",
            "رقائق": "#2196F3",
            "فقه": "#009688",
        }

        # دالة تحويل رابط Google Drive إلى رابط مباشر (ضروري للأندرويد)
        def _convert_gdrive_url(url: str) -> str:
            """تحويل رابط Google Drive /view إلى رابط مباشر يعمل على الأندرويد"""
            import re as _re
            m = _re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if m:
                file_id = m.group(1)
                return f"https://drive.google.com/uc?export=view&id={file_id}"
            return url

        # دالة لفتح الرابط - الطريقة الصحيحة للإصدار الجديد
        async def open_url_async(url):
            """فتح الرابط بشكل غير متزامن - يعمل على الهاتف والديسكتوب"""
            converted = _convert_gdrive_url(url)
            await _open_url(converted, page)
            return True

        def open_book(e, book):
            try:
                url = book["pdf_url"]
                
                # تشغيل دالة فتح الرابط في الخلفية
                page.run_task(open_url_async, url)
                
                # عرض رسالة التأكيد
                _show_snack(page, f"📖 جاري فتح {book['title']}", Colors.GREEN, 2000)
                
            except Exception as e:
                print(f"خطأ في فتح الرابط: {e}")
                # عرض رسالة خطأ
                _show_snack(page, "❌ حدث خطأ في فتح الرابط", Colors.RED, 2000)

        # تأثير hover للكتب
        def on_hover(e):
            if e.data == "true":
                e.control.bgcolor = Colors.WHITE
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=Colors.with_opacity(0.15, Colors.BLUE),
                    offset=Offset(0, 8)
                )
                e.control.scale = 1.02
                e.control.border = ft.Border.all(1.5, Colors.with_opacity(0.3, Colors.BLUE))
            else:
                e.control.bgcolor = Colors.WHITE
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=Colors.with_opacity(0.1, Colors.BLACK),
                    offset=Offset(0, 2)
                )
                e.control.scale = 1.0
                e.control.border = ft.Border.all(1, Colors.GREY_300)
            e.control.update()

        # إنشاء بطاقات الكتب
        book_cards = []
        for book in islamic_books:
            # تحديد لون التصنيف
            category_color = category_colors.get(book["category"], "#607D8B")
            
            # إنشاء بطاقة الكتاب باستخدام Container
            book_card = Container(
                width=350,
                bgcolor=Colors.WHITE,
                border_radius=16,
                padding=15,
                shadow=BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=Colors.with_opacity(0.1, Colors.BLACK),
                    offset=Offset(0, 2)
                ),
                border=ft.Border.all(1, Colors.GREY_300),
                animate=Animation(200, AnimationCurve.EASE_OUT),
                on_hover=on_hover,
                content=Column(
                    controls=[
                        # صف الصورة والمعلومات الأساسية
                        Row(
                            controls=[
                                # صورة الغلاف
                                Container(
                                    width=90,
                                    height=120,
                                    border_radius=10,
                                    shadow=BoxShadow(
                                        spread_radius=1,
                                        blur_radius=10,
                                        color=Colors.with_opacity(0.2, Colors.BLACK),
                                        offset=Offset(0, 3)
                                    ),
                                    content=Image(
                                        src=book["cover"],
                                        width=90,
                                        height=120,
                                        fit=ft.BoxFit.COVER,
                                        border_radius=10,
                                        error_content=Container(
                                            width=90,
                                            height=120,
                                            bgcolor="#f0f0f0",
                                            border_radius=10,
                                            content=Icon(
                                                Icons.BOOK,
                                                size=40,
                                                color=Colors.GREY_400
                                            )
                                        )
                                    ),
                                ),
                                
                                Container(width=10),
                                
                                # معلومات الكتاب
                                Container(
                                    expand=True,
                                    content=Column(
                                        controls=[
                                            # عنوان الكتاب
                                            Text(
                                                book["title"],
                                                size=18,
                                                color="#1E293B",
                                                weight=FontWeight.BOLD,
                                                font_family=BUTTON_FONT,
                                                max_lines=2,
                                                overflow=TextOverflow.ELLIPSIS
                                            ),
                                            
                                            Container(height=3),
                                            
                                            # اسم المؤلف
                                            Row(
                                                controls=[
                                                    Icon(
                                                        Icons.PERSON_OUTLINE,
                                                        size=14,
                                                        color="#64748B"
                                                    ),
                                                    Container(width=3),
                                                    Text(
                                                        book["author"],
                                                        size=13,
                                                        color="#64748B",
                                                        font_family=BUTTON_FONT,
                                                        italic=True
                                                    ),
                                                ],
                                                spacing=0
                                            ),
                                            
                                            Container(height=5),
                                            
                                            # التصنيف وعدد الصفحات
                                            Row(
                                                controls=[
                                                    # شارة التصنيف
                                                    Container(
                                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                                        bgcolor=Colors.with_opacity(0.1, category_color),
                                                        border_radius=12,
                                                        content=Text(
                                                            book["category"],
                                                            size=11,
                                                            color=category_color,
                                                            weight=FontWeight.BOLD,
                                                            font_family=BUTTON_FONT
                                                        )
                                                    ),
                                                    
                                                    Container(width=8),
                                                    
                                                    # عدد الصفحات
                                                    Row(
                                                        controls=[
                                                            Icon(
                                                                Icons.MENU_BOOK,
                                                                size=12,
                                                                color="#64748B"
                                                            ),
                                                            Container(width=3),
                                                            Text(
                                                                f"{book['pages']} صفحة",
                                                                size=11,
                                                                color="#64748B",
                                                                font_family=BUTTON_FONT
                                                            ),
                                                        ],
                                                        spacing=0
                                                    ),
                                                ],
                                                spacing=0
                                            ),
                                        ],
                                        spacing=0,
                                        horizontal_alignment=CrossAxisAlignment.START
                                    )
                                ),
                            ],
                            alignment=MainAxisAlignment.START,
                            vertical_alignment=CrossAxisAlignment.START
                        ),
                        
                        Container(height=10),
                        
                        # وصف الكتاب
                        Container(
                            padding=ft.Padding.symmetric(horizontal=5),
                            content=Text(
                                book["description"],
                                size=13,
                                color="#475569",
                                font_family=BUTTON_FONT,
                                max_lines=2,
                                overflow=TextOverflow.ELLIPSIS,
                                text_align=TextAlign.RIGHT
                            )
                        ),
                        
                        Container(height=10),
                        
                        # زر القراءة
                        Container(
                            width=350,
                            height=45,
                            gradient=LinearGradient(
                                begin=ft.Alignment(0, 0),
                                end=ft.Alignment(1, 0),
                                colors=["#667eea", "#667eea"]
                            ),
                            border_radius=10,
                            shadow=BoxShadow(
                                spread_radius=0,
                                blur_radius=10,
                                color=Colors.with_opacity(0.2, "#667eea"),
                                offset=Offset(0, 3)
                            ),
                            on_click=lambda e, b=book: open_book(e, b),
                            content=Row(
                                controls=[
                                    Icon(
                                        Icons.DOWNLOAD,
                                        color=Colors.WHITE,
                                        size=18
                                    ),
                                    Container(width=5),
                                    Text(
                                        "قراءة الكتاب",
                                        color=Colors.WHITE,
                                        size=15,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT
                                    ),
                                ],
                                alignment=MainAxisAlignment.CENTER,
                                spacing=0
                            ),
                            alignment=ft.Alignment(0, 0)
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
            
            book_cards.append(
                Container(
                    content=book_card,
                    margin=ft.Margin.only(bottom=15)
                )
            )

        return View(
            route="/islamic_library",
            controls=[
                # AppBar عصري
                AppBar(
                    title=Text(
                        "المكتبة الإسلامية",
                        weight=FontWeight.BOLD,
                        size=20,
                        color=Colors.WHITE
                    ),
                    bgcolor="#667eea",
                    center_title=True,
                    elevation=0,
                    leading=Container(
                        margin=ft.Margin.only(left=10),
                        content=IconButton(
                            icon=Icons.ARROW_BACK_IOS,
                            icon_color=Colors.WHITE,
                            icon_size=22,
                            on_click=lambda e: handle_back(page),
                            style=ButtonStyle(
                                shape=RoundedRectangleBorder(radius=20),
                            )
                        )
                    ),
                ),
                
                # المحتوى الرئيسي
                Container(
                    expand=True,
                    gradient=LinearGradient(
                        begin=ft.Alignment(0, -1),
                        end=ft.Alignment(0, 1),
                        colors=["#f8fafc", "#f1f5f9"]
                    ),
                    content=Column(
                        controls=[
                            # قائمة الكتب
                            Container(
                                expand=True,
                                content=ListView(
                                    controls=book_cards,
                                    padding=ft.Padding.symmetric(horizontal=15),
                                    spacing=0
                                )
                            ),
                        ],
                        spacing=0,
                        expand=True
                    )
                ),
            ],
            bgcolor="#f1f5f9",
            padding=0,
            spacing=0,
        )

class TasbihPage:
    def __init__(self, page):
        self.page = page
        self.data = load_tasbih()
        self.current = self.data[0] if self.data else None
        self.text_field = None  # سيتم تهيئته في get_view
        self.button_ref = None  # مرجع للزر
        self.total_text_ref = None  # مرجع لنص إجمالي التسبيحات
        self.completed_text_ref = None  # مرجع لنص الأذكار المكتملة
        self.is_animating = False  # لمنع تكرار التأثير أثناء التشغيل

    def increment(self, e):
        if self.current:
            self.current["count"] += 1
            save_tasbih(self.data)
            
            # تحديث الرقم على الزر مباشرة
            if self.button_ref and hasattr(self.button_ref, 'content'):
                stack = self.button_ref.content
                if stack and len(stack.controls) > 1:
                    number_container = stack.controls[1]
                    if number_container and number_container.content:
                        number_container.content.value = str(self.current["count"])
                        number_container.content.update()
            
            # تحديث إجمالي التسبيحات مباشرة
            if self.total_text_ref:
                total = sum(z["count"] for z in self.data)
                self.total_text_ref.value = str(total)
                self.total_text_ref.update()
            
            # تحديث الأذكار المكتملة مباشرة
            if self.completed_text_ref:
                completed = sum(1 for z in self.data if z["count"] >= 33)
                self.completed_text_ref.value = f"{completed}/{len(self.data)}"
                self.completed_text_ref.update()
            
            # تشغيل تأثير نبضات القلب على الزر
            if self.button_ref and not self.is_animating:
                self.heartbeat_animation(self.button_ref)
            
            # إشعار عند مضاعفات 33
            if self.current["count"] % 33 == 0:
                self.show_message(f"🎉 وصلت إلى {self.current['count']} تسبيحة!")

    def heartbeat_animation(self, button_container):
        """تشغيل تأثير نبضات القلب على الزر - نبضة واحدة فقط للسرعة"""
        if self.is_animating:
            return
        self.is_animating = True

        async def heartbeat():
            try:
                if not button_container or button_container.page is None:
                    self.is_animating = False
                    return
                # نبضة واحدة بدلاً من 3 = 2 تحديثات بدلاً من 8
                button_container.scale = 1.15
                button_container.update()
                await asyncio.sleep(0.12)
                button_container.scale = 1.0
                button_container.update()
            except Exception as e:
                print(f"خطأ في تأثير النبض: {e}")
            finally:
                self.is_animating = False
        
        # تشغيل المهمة
        self.page.run_task(heartbeat)

    def reset(self, e):
        if self.current:
            self.current["count"] = 0
            save_tasbih(self.data)
            
            # تحديث الرقم على الزر مباشرة
            if self.button_ref and hasattr(self.button_ref, 'content'):
                stack = self.button_ref.content
                if stack and len(stack.controls) > 1:
                    number_container = stack.controls[1]
                    if number_container and number_container.content:
                        number_container.content.value = "0"
                        number_container.content.update()
            
            # تحديث إجمالي التسبيحات مباشرة
            if self.total_text_ref:
                total = sum(z["count"] for z in self.data)
                self.total_text_ref.value = str(total)
                self.total_text_ref.update()
            
            # تحديث الأذكار المكتملة مباشرة
            if self.completed_text_ref:
                completed = sum(1 for z in self.data if z["count"] >= 33)
                self.completed_text_ref.value = f"{completed}/{len(self.data)}"
                self.completed_text_ref.update()
            
            self.show_message("🔄 تم تصفير العداد")

    def change_zikr(self, zikr):
        self.current = zikr
        self.update_page()

    def add_zikr(self, e):
        # الحصول على النص من حقل النص المباشر
        if self.text_field and hasattr(self.text_field, 'value'):
            text = self.text_field.value.strip()
        else:
            text = ""
        
        if not text:
            self.show_message("⚠️ الرجاء كتابة نص الذكر")
            return
            
        # تجنب التكرار
        if any(z["text"] == text for z in self.data):
            self.show_message("⚠️ هذا الذكر موجود بالفعل")
            return
            
        new_id = max([z["id"] for z in self.data], default=0) + 1
        new_zikr = {"id": new_id, "text": text, "count": 0}
        self.data.append(new_zikr)
        save_tasbih(self.data)
        self.current = new_zikr
        
        # مسح حقل النص
        if self.text_field:
            self.text_field.value = ""
        
        self.update_page()
        self.show_message(f"✅ تم إضافة: {text}")

    def delete_zikr(self, zikr_id):
        """حذف ذكر (للأذكار المضافة يدوياً فقط)"""
        if len(self.data) <= 1:
            self.show_message("⚠️ لا يمكن حذف الذكر الوحيد")
            return
            
        # البحث عن الذكر المراد حذفه
        for i, zikr in enumerate(self.data):
            if zikr["id"] == zikr_id and zikr["id"] > 17:  # لا تحذف الأذكار الافتراضية
                if self.current == zikr:
                    # إذا كان الذكر الحالي هو المراد حذفه، انتقل إلى أول ذكر آخر
                    self.current = self.data[0] if i != 0 else self.data[1]
                
                self.data.pop(i)
                save_tasbih(self.data)
                
                self.show_message("✅ تم حذف الذكر بنجاح")
                self.update_page()
                break

    def show_message(self, text):
        _show_snack(self.page, text, Colors.GREEN if "✅" in text else Colors.ORANGE, 2000)
        
    def update_page(self):
        """إعادة تحميل الصفحة بالكامل (عند تغيير الذكر أو الإضافة)"""
        self.page.views[-1] = self.get_view()
        safe_update(self.page)

    def get_empty_view(self):
        """عرض عندما لا توجد أذكار"""
        return View(
            route="/electronic_tasbih",
            controls=[
                AppBar(
                    title=Text("السبحة الإلكترونية", weight=FontWeight.BOLD, size=17, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page)
                    )
                ),
                Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=Column(
                        controls=[
                            Icon(Icons.ERROR_OUTLINE, size=60, color=Colors.GREY_400),
                            Container(height=20),
                            Text("لا توجد أذكار",
                                 size=20,
                                 color=Colors.GREY_600,
                                 weight=FontWeight.BOLD,
                                 font_family=BUTTON_FONT,
                                 text_align=TextAlign.CENTER),
                            Container(height=10),
                            Text("سيتم إضافة الأذكار الافتراضية تلقائياً",
                                 size=14,
                                 color=Colors.GREY_500,
                                 font_family=BUTTON_FONT,
                                 text_align=TextAlign.CENTER),
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    )
                ),
            ],
            bgcolor="#f8f9fa",
            padding=0
        )

    def get_view(self):
        if not self.data:
            return self.get_empty_view()
            
        if not self.current:
            self.current = self.data[0]
            
        # إنشاء حقل النص للإضافة
        self.text_field = TextField(
            hint_text="اكتب الذكر هنا...",
            width=280,
            border_radius=10,
            filled=True,
            fill_color="#f5f5f5",
            text_style=TextStyle(font_family=BUTTON_FONT, size=14),
            on_submit=self.add_zikr
        )
        
        # إنشاء Container الرقم
        number_text = Text(
            str(self.current["count"]),
            size=22,
            color=Colors.WHITE,
            weight=FontWeight.BOLD,
            text_align=TextAlign.CENTER
        )
        
        number_container = Container(
            width=180,  # أصغر قليلاً
            height=180,
            alignment=ft.Alignment(0, 0),
            content=number_text
        )
        
        # إنشاء Stack للزر
        button_stack = Stack(
            controls=[
                # الخلفية الدائرية
                Container(
                    width=180,
                    height=180,
                    gradient=LinearGradient(
                        begin=ft.Alignment(0, -1),
                        end=ft.Alignment(0, 1),
                        colors=["#1b9221", "#1b9221"]
                    ),
                    shape=BoxShape.CIRCLE,
                    shadow=BoxShadow(
                        spread_radius=2,
                        blur_radius=15,
                        color=Colors.with_opacity(0.3, "#41ce48"),
                        offset=Offset(0, 5)
                    ),
                ),
                
                # الرقم في المنتصف
                number_container,
                
                # إطار دائري أبيض شفاف
                Container(
                    width=180,
                    height=180,
                    border_radius=90,
                    border=ft.Border.all(
                        3, 
                        Colors.with_opacity(0.3, Colors.WHITE)
                    ),
                    alignment=ft.Alignment(0, 0)
                ),
            ]
        )
        
        # إنشاء Container الزر مع تخزين مرجع له - حجم أصغر
        self.button_ref = Container(
            width=180,
            height=180,
            animate_scale=True,
            scale=1.3,  # حجم طبيعي أقل
            animate=ft.Animation(50, AnimationCurve.EASE_OUT),
            margin=ft.Margin.all(0),
            content=button_stack
        )
        
        # إنشاء نص إجمالي التسبيحات مع مرجع
        total_value = str(sum(z["count"] for z in self.data))
        self.total_text_ref = Text(
            total_value,
            size=18,
            color=Colors.BLUE_800,
            weight=FontWeight.BOLD,
            font_family=BUTTON_FONT
        )
        
        # إنشاء نص الأذكار المكتملة مع مرجع
        completed = sum(1 for z in self.data if z["count"] >= 33)
        completed_value = f"{completed}/{len(self.data)}"
        self.completed_text_ref = Text(
            completed_value,
            size=18,
            color=Colors.GREEN_800,
            weight=FontWeight.BOLD,
            font_family=BUTTON_FONT
        )
        
        # إحصائيات سريعة
        stats_container = Container(
            width=350,
            padding=10,
            bgcolor=Colors.BLUE_50,
            border_radius=10,
            margin=ft.Margin.only(bottom=10),
            content=Row(
                controls=[
                    Container(
                        expand=True,
                        content=Column(
                            controls=[
                                Text("إجمالي التسبيحات", 
                                     size=12, 
                                     color=Colors.BLUE_700,
                                     font_family=BUTTON_FONT),
                                self.total_text_ref,
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            spacing=2
                        )
                    ),
                    Container(
                        width=1,
                        height=30,
                        bgcolor=Colors.BLUE_200
                    ),
                    Container(
                        expand=True,
                        content=Column(
                            controls=[
                                Text("الأذكار المكتملة", 
                                     size=12, 
                                     color=Colors.GREEN_700,
                                     font_family=BUTTON_FONT),
                                self.completed_text_ref,
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            spacing=2
                        )
                    ),
                ],
                alignment=MainAxisAlignment.SPACE_AROUND
            )
        )
        
        # إطار ثابت للذكر الحالي مع ارتفاع محدد
        current_zikr_container = Container(
            width=350,
            height=120,
            padding=0,
            bgcolor=Colors.WHITE,
            border_radius=15,
            border=ft.Border.all(2, Colors.BLUE_200),
            alignment=ft.Alignment(0, 0),
            content=Container(

                alignment=ft.Alignment(0, 0),
                content=Column(
                    controls=[
                        Text(
                            self.current["text"],
                            size=18,
                            color=Colors.BLUE_800,
                            weight=FontWeight.BOLD,
                            text_align=TextAlign.CENTER,
                            font_family=BUTTON_FONT,
                        )
                    ],
                    scroll=ScrollMode.AUTO,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
        )
        
        # قائمة الأذكار - مفتوحة بدون مربع صغير
        azkar_list_items = []
        for z in self.data:
            azkar_list_items.append(
                Container(
                    width=350,
                    margin=ft.Margin.only(bottom=8),
                    padding=10,
                    bgcolor=Colors.BLUE_50 if z == self.current else Colors.WHITE,
                    border_radius=8,
                    border=ft.Border.all(1, Colors.BLUE_200 if z == self.current else Colors.GREY_200),
                    on_click=lambda e, z=z: self.change_zikr(z),
                    content=Row(
                        [
                            # رقم الذكر
                            Container(
                                width=30,
                                height=30,
                                border_radius=15,
                                bgcolor=Colors.BLUE_100 if z == self.current else Colors.GREY_100,
                                alignment=ft.Alignment(0, 0),
                                content=Text(
                                    str(z["id"]),
                                    size=12,
                                    color=Colors.BLUE_700 if z == self.current else Colors.GREY_600,
                                    weight=FontWeight.BOLD
                                )
                            ),
                            
                            Container(width=5),
                            
                            # نص الذكر والعداد
                            Container(
                                expand=True,
                                content=Column(
                                    spacing=2,
                                    controls=[
                                        Text(
                                            z["text"],
                                            size=14,
                                            color=Colors.BLUE_800 if z == self.current else Colors.GREY_700,
                                            weight=FontWeight.BOLD if z == self.current else FontWeight.NORMAL,
                                            font_family=BUTTON_FONT,
                                            max_lines=1,
                                            overflow=TextOverflow.ELLIPSIS
                                        ),
                                        Row(
                                            controls=[
                                                Container(
                                                    width=8,
                                                    height=8,
                                                    border_radius=4,
                                                    bgcolor=Colors.GREEN if z["count"] > 0 else Colors.GREY_400
                                                ),
                                                Container(width=5),
                                                Text(
                                                    f"{z['count']} تسبيحة",
                                                    size=11,
                                                    color=Colors.GREEN_600 if z["count"] > 0 else Colors.GREY_500,
                                                    font_family=BUTTON_FONT
                                                ),
                                            ],
                                            spacing=0
                                        )
                                    ]
                                )
                            ),
                            
                            # زر الحذف (للأذكار المضافة يدوياً فقط)
                            IconButton(
                                icon=Icons.DELETE_OUTLINE,
                                icon_size=20,
                                icon_color=Colors.RED_400,
                                on_click=lambda e, z_id=z["id"]: self.delete_zikr(z_id),
                                tooltip="حذف الذكر"
                            ) if z["id"] > 17 else Container(width=30)
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=CrossAxisAlignment.CENTER
                    )
                )
            )
        
        return View(
            route="/electronic_tasbih",
            controls=[
                # شريط العنوان
                AppBar(
                    title=Text("السبحة الإلكترونية", weight=FontWeight.BOLD, size=17, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page)
                    )
                ),
                
                # المحتوى الرئيسي
                Container(
                    expand=True,
                    padding=5,
                    content=ListView(
                        controls=[
                            # إحصائيات سريعة
                            stats_container,
                            
                            # مسافة بين الإحصائيات والذكر
                            Container(height=15),
                            
                            # الذكر الحالي
                            Container(
                                content=current_zikr_container,
                                alignment=ft.Alignment(0, 0)
                            ),
                            
                            # مسافة كبيرة بين الذكر والزر
                            Container(height=60),
                            
                            # زر التسبيح
                            Container(
                                height=200,
                                alignment=ft.Alignment(0, 0),
                                content=GestureDetector(
                                    on_tap=self.increment,
                                    content=self.button_ref
                                )
                            ),
                            
                            # مسافة كبيرة بين الزر وزر التصفير
                            Container(height=80),
                            
                            # زر التصفير
                            Container(
                                height=50,
                                alignment=ft.Alignment(0, 0),
                                content=FilledButton(
                                    "تصفير",
                                    on_click=self.reset,
                                    width=100,
                                    height=40,
                                    style=ButtonStyle(
                                        bgcolor=Colors.RED_400,
                                        color=Colors.WHITE,
                                        shape=RoundedRectangleBorder(radius=20)
                                    )
                                )
                            ),
                            
                            # مسافة قبل قائمة الأذكار
                            Container(height=30),
                            
                            # عنوان قائمة الأذكار
                            Container(
                                content=Text(
                                    "جميع الأذكار",
                                    size=16,
                                    color=Colors.BLUE_700,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.CENTER
                                ),
                                alignment=ft.Alignment(0, 0),
                                margin=ft.Margin.only(bottom=10)
                            ),
                            
                            # قائمة الأذكار - مفتوحة بالكامل
                            Column(
                                controls=azkar_list_items,
                                spacing=5,
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            ),
                            
                            # مسافة قبل إضافة ذكر جديد
                            Container(height=20),
                            
                            # عنوان إضافة ذكر جديد
                            Container(
                                content=Text(
                                    "إضافة ذكر جديد",
                                    size=16,
                                    color=Colors.BLUE_700,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.CENTER
                                ),
                                alignment=ft.Alignment(0, 0),
                                margin=ft.Margin.only(bottom=10)
                            ),
                            
                            # إضافة ذكر جديد
                            Container(
                                width=350,
                                padding=15,
                                bgcolor=Colors.WHITE,
                                border_radius=15,
                                content=Column(
                                    spacing=10,
                                    horizontal_alignment=CrossAxisAlignment.CENTER,
                                    controls=[
                                        self.text_field,
                                        
                                        FilledButton(
                                            "إضافة",
                                        
                                            on_click=self.add_zikr,
                                            width=100,
                                            height=35,
                                            style=ButtonStyle(
                                                bgcolor=Colors.BLUE_600,
                                                color=Colors.WHITE,
                                                shape=RoundedRectangleBorder(radius=8)
                                            )
                                        )
                                    ]
                                )
                            ),
                            
                            # مسافة في الأسفل
                            Container(height=30)
                        ],
                        spacing=0,
                        padding=10
                    )
                ),
            ],
            bgcolor="#f8f9fa",
            padding=0,
            spacing=0,
        )

# ============ صفحة اتجاه القبلة ============
class QiblaWebViewPage:
    QIBLA_URL = "https://qiblafind.net/ar/qibla-finder"

    def __init__(self, page: Page):
        self.page = page

    def create_view(self):
        return View(
            route="/qibla",
            controls=[
                AppBar(
                    title=Text("اتجاه القبلة", weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page),
                    ),
                ),
                Container(
                    content=Column(
                        [
                            Container(height=30),
                            Container(
                                content=Image(
                                    src="assets/icons/qibla.webp",
                                    width=200, height=200,
                                    fit=ft.BoxFit.CONTAIN,
                                ),
                                padding=10,
                                bgcolor=Colors.WHITE,
                                border_radius=100,
                                border=ft.Border.all(3, Colors.GREEN_400),
                            ),
                            Container(height=30),
                            Container(
                                content=FilledButton(
                                    content=Row([
                                        Icon(Icons.EXPLORE, color=Colors.WHITE, size=24),
                                        Container(width=8),
                                        Text(
                                            " qiblafind.net فتح أداة القبلة من موقع ",
                                            size=17,
                                            color=Colors.WHITE,
                                            font_family=BUTTON_FONT,
                                            weight=FontWeight.BOLD,
                                        )
                                    ], alignment=MainAxisAlignment.CENTER),
                                    on_click=lambda e: self.open_qibla_finder(),
                                    style=ButtonStyle(
                                        bgcolor="#4CAF50",
                                        shape=RoundedRectangleBorder(radius=12),
                                        elevation=5,
                                        padding=ft.Padding.only(left=25, right=25, top=15, bottom=15),
                                    ),
                                    width=350, height=60,
                                ),
                                alignment=ft.Alignment(0, 0),
                            ),
                            Container(height=20),
                            Container(
                                content=Text(
                                    "يحتوي هذا التطبيق على رابط خارجي لموقع Qibla Finder لتحديد اتجاه القبلة. عند استخدام هذا الرابط، تطبق سياسة الخصوصية الخاصة بالموقع المذكور.",
                                    size=14,
                                    color=Colors.GREY_600,
                                    text_align=TextAlign.CENTER,
                                    font_family=BUTTON_FONT,
                                ),
                                padding=20,
                                bgcolor="#f0f0f0",
                                border_radius=10,
                                width=350,
                            ),
                            Container(height=20),
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        scroll=ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=0,
                    expand=True,
                ),
            ],
            bgcolor="#feffff",
            padding=0,
            spacing=0,
        )

    def open_qibla_finder(self, e=None):
        self.page.run_task(_open_url, self.QIBLA_URL, self.page)
        _show_snack(self.page, "🧭 جاري فتح أداة تحديد القبلة...", Colors.GREEN, 1500)
class PrayerTimesPage:
    def __init__(self, page: Page):
        self.page = page
        self.timer = None
        self.is_page_active = True
        self.countdown_text = Text("", size=18, color="#1a5fb4", weight=FontWeight.BOLD, 
                                   font_family=BUTTON_FONT, text_align=TextAlign.CENTER)
        
        # أيقونات الصلوات كصور (تأكد من وجود هذه الصور في المسار المحدد)
        self.prayer_icons = {
            "الفجر": "assets/icons/crescent.webp",
            "الشروق": "assets/icons/sunrise.webp",
            "الظهر": "assets/icons/sun.webp",
            "العصر": "assets/icons/cleary.webp",
            "المغرب": "assets/icons/sunset.webp",
            "العشاء": "assets/icons/momok.webp"
        }
        
        # ألوان الصلوات
        self.prayer_colors = {
            "الفجر": "",
            "الشروق": "",
            "الظهر": "",
            "العصر": "",
            "المغرب": "",
            "العشاء": ""
        }
        
        # التاريخ الهجري محلياً
        self.hijri_date = self.get_accurate_hijri_date()

    def create_view(self):
        loading_content = Column(
            [
                Container(height=100),
                ProgressRing(width=50, height=50, color="#4CAF50"),
                Text("جاري تحميل مواقيت الصلاة...", 
                     size=16, 
                     color=Colors.BLACK, 
                     font_family=BUTTON_FONT,
                     text_align=TextAlign.CENTER)
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            alignment=MainAxisAlignment.CENTER
        )

        view = View(
            route="/prayer_times",
            controls=[
                AppBar(
                    title=Text("مواقيت الصلاة", 
                         weight=FontWeight.BOLD, 
                         size=20, 
                         color=Colors.WHITE, 
                         text_align=TextAlign.CENTER),
                    bgcolor="#685BDA",
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: self.on_back_button(),
                    ),
                ),
                Container(
                    content=loading_content,
                
                    expand=True,
                    bgcolor="#f5f7fa",
                    alignment=ft.Alignment(0, 0)
                ),
            ],
            padding=0,
            spacing=0,
            horizontal_alignment=CrossAxisAlignment.CENTER
        )

        # تشغيل تحميل مواقيت الصلاة في thread منفصل لمنع تجميد الواجهة
        threading.Thread(target=self.get_prayer_times, args=(view,), daemon=True).start()
        return view

    def on_back_button(self):
        self.is_page_active = False
        self.stop_timer()
        handle_back(self.page)

    def stop_timer(self):
        self.is_page_active = False
        self.timer = None

    def format_prayer_time(self, time_str):
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            hour = time_obj.hour
            minute = time_obj.minute
            period = "ص" if hour < 12 else "م"
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12
            return f"{hour_12:02d}:{minute:02d} {period}"
        except:
            return time_str

    def create_prayer_card(self, prayer_name, prayer_time, is_next_prayer=False):
        icon_path = self.prayer_icons.get(prayer_name, "")
        color = self.prayer_colors.get(prayer_name, "#666666")
        
        return Container(
            width=350,
            height=90,
            bgcolor=Colors.WHITE,
            border_radius=15,
            border=ft.Border.all(2, color if is_next_prayer else "#e0e0e0"),
            padding=15,
            margin=ft.Margin.only(bottom=10),
            shadow=BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=Colors.with_opacity(0.15, color if is_next_prayer else Colors.BLACK),
                offset=Offset(0, 2)
            ),
            alignment=ft.Alignment(0, 0),
            content=Column(
                controls=[
                    Row(
                        controls=[
                            # أيقونة الصلاة كصورة
                            Container(
                                width=50,
                                height=50,
                                border_radius=25,
                                bgcolor=f"{color}15",
                                alignment=ft.Alignment(0, 0),
                                content=Image(
                                    src=icon_path,
                                    width=30,
                                    height=30,
                                    fit=ft.BoxFit.CONTAIN,
                                    color=color
                                )
                            ),
                            Container(width=15),
                            Column(
                                controls=[
                                    Text(
                                        prayer_name,
                                        size=18,
                                        color=Colors.BLACK,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER
                                    ),
                                    Text(
                                        self.format_prayer_time(prayer_time),
                                        size=16,
                                        color=Colors.BLACK,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER
                                    )
                                ],
                                spacing=3,
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            ),
                            Container(width=15),
                            Container(
                                visible=is_next_prayer,
                                width=50,
                                height=50,
                                border_radius=25,
                                bgcolor=color,
                                alignment=ft.Alignment(0, 0),
                                content=Image(
                                    src="assets/icons/next.webp",
                                    width=24,
                                    height=24,
                                    fit=ft.BoxFit.CONTAIN,
                                    
                                )
                            ) if is_next_prayer else Container(width=50)
                        ],
                        alignment=MainAxisAlignment.CENTER,
                        vertical_alignment=CrossAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )

    def update_prayer_times_view(self, view, timings, location, date_info, hijri_date, is_cached=False):
        next_prayer_name, next_prayer_time = self.get_next_prayer(timings)
        hours, minutes, seconds = self.calculate_time_remaining(next_prayer_time)
    
        self.countdown_text.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # تحديث التاريخ الهجري محلياً للتأكد من أنه محدث (أضف هذا السطر)
        hijri_date = self.get_accurate_hijri_date()
        
        # بطاقة الموقع والتواريخ
        header_card = Container(
            width=350,
            padding=20,
            bgcolor=Colors.WHITE,
            border_radius=15,
            margin=ft.Margin.only(bottom=15),
            alignment=ft.Alignment(0, 0),
            content=Column(
                controls=[
                    Row(
                        controls=[
                            Icon(Icons.LOCATION_ON, size=22, color="#1a5fb4"),
                            Container(width=10),
                            Text(
                                location.get('address_ar', location.get('address', 'الموقع غير معروف')),
                                size=16,
                                color=Colors.BLACK,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            )
                        ],
                        alignment=MainAxisAlignment.CENTER
                    ),
                    
                    Divider(height=15, color=Colors.GREY_200),
                    
                    Row(
                        controls=[
                            Column(
                                controls=[
                                    Row(
                                        controls=[
                                            Icon(Icons.CALENDAR_TODAY, size=18, color="#4CAF50"),
                                            Container(width=5),
                                            Text("الميلادي", size=14, color=Colors.GREY_600, 
                                                 font_family=BUTTON_FONT)
                                        ],
                                        alignment=MainAxisAlignment.CENTER
                                    ),
                                    Text(
                                        datetime.now().strftime("%d/%m/%Y"),
                                        size=16,
                                        color=Colors.BLACK,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER
                                    )
                                ],
                                spacing=2,
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            ),
                            
                            Container(width=20),
                            
                            Column(
                                controls=[
                                    Row(
                                        controls=[
                                            Icon(Icons.NIGHTLIGHT_ROUND, size=18, color="#673ab7"),
                                            Container(width=5),
                                            Text("الهجري", size=14, color=Colors.GREY_600, 
                                                 font_family=BUTTON_FONT)
                                        ],
                                        alignment=MainAxisAlignment.CENTER
                                    ),
                                    Text(
                                        hijri_date,
                                        size=16,
                                        color=Colors.BLACK,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER
                                    )
                                ],
                                spacing=2,
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            )
                        ],
                        alignment=MainAxisAlignment.CENTER
                    )
                ],
                spacing=0,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        
        # بطاقة الصلاة القادمة
        next_prayer_card = Container(
            width=350,
            padding=20,
            bgcolor=f"{self.prayer_colors.get(next_prayer_name, '#FFFFFF')}10",
            border=ft.Border.all(2, self.prayer_colors.get(next_prayer_name, "#FFFFFF")),
            alignment=ft.Alignment(0, 0),
            content=Column(
                controls=[
                    Text(
                        f"الصلاة القادمة: {next_prayer_name}",
                        size=18,
                        color=Colors.BLACK,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    ),
                    
                    Container(height=15),
                    
                    Row(
                        controls=[
                            Column(
                                controls=[
                                    Text("الوقت المتبقي", size=14, color=Colors.BLACK, 
                                         font_family=BUTTON_FONT, text_align=TextAlign.CENTER),
                                    Container(height=5),
                                    self.countdown_text
                                ],
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            ),
                            
                            Container(width=30),
                            
                            Column(
                                controls=[
                                    Text("موعد الصلاة", size=14, color=Colors.BLACK, 
                                         font_family=BUTTON_FONT, text_align=TextAlign.CENTER),
                                    Container(height=5),
                                    Text(
                                        self.format_prayer_time(next_prayer_time),
                                        size=18,
                                        color=Colors.BLACK,
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER
                                    )
                                ],
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            )
                        ],
                        alignment=MainAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        
        # عنوان قائمة الصلوات
        prayers_header = Container(
            width=350,
            padding=ft.Padding.only(bottom=15),
            alignment=ft.Alignment(0, 0),
            content=Text(
                "مواقيت الصلاة اليومية",
                size=18,
                color=Colors.BLACK,
                weight=FontWeight.BOLD,
                font_family=BUTTON_FONT,
                text_align=TextAlign.CENTER
            )
        )
        
        # قائمة الصلوات
        prayer_list = [
            ('الفجر', timings['Fajr']),
            ('الشروق', timings['Sunrise']),
            ('الظهر', timings['Dhuhr']),
            ('العصر', timings['Asr']),
            ('المغرب', timings['Maghrib']),
            ('العشاء', timings['Isha'])
        ]
        
        # إنشاء بطاقات الصلوات
        prayer_cards = []
        for prayer_name, prayer_time in prayer_list:
            is_next = (prayer_name == next_prayer_name)
            prayer_cards.append(self.create_prayer_card(prayer_name, prayer_time, is_next))
        
        # زر التحديث
        refresh_button = FilledButton(
            content=Row(
                controls=[
                    Icon(Icons.REFRESH, size=22, color=Colors.WHITE),
                    Container(width=8),
                    Text("تحديث المواقيت", size=16, color=Colors.WHITE, font_family=BUTTON_FONT)
                ],
                alignment=MainAxisAlignment.CENTER
            ),
            on_click=lambda e: self.refresh_data(view),
            style=ButtonStyle(
                bgcolor="#1a5fb4",
                padding=ft.Padding.only(left=25, right=25, top=12, bottom=12),
                shape=RoundedRectangleBorder(radius=10),
            ),
            width=220,
            height=48
        )
        
        # تحذير البيانات المخزنة
        cache_warning = Container(
            visible=is_cached,
            width=350,
            padding=12,
            bgcolor=Colors.YELLOW_50,
            border_radius=10,
            border=ft.Border.all(1, Colors.YELLOW_300),
            margin=ft.Margin.only(bottom=15),
            alignment=ft.Alignment(0, 0),
            content=Row(
                controls=[
                    Icon(Icons.WARNING_AMBER, size=22, color=Colors.YELLOW_700),
                    Container(width=10),
                    Text(
                        "بيانات محفوظة - تحقق من الإنترنت",
                        size=13,
                        color=Colors.YELLOW_700,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    )
                ],
                alignment=MainAxisAlignment.CENTER
            )
        )
        
        # المحتوى الرئيسي - كل شيء في المنتصف
        main_content = Container(
            content=Column(
                controls=[
                    cache_warning,
                    header_card,
                    next_prayer_card,
                    prayers_header,
                    *prayer_cards,
                    Container(height=0),
                    Container(
                        content=refresh_button,
                        alignment=ft.Alignment(0, 0)
                    ),
                    Container(height=30)
                ],
                scroll=ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=CrossAxisAlignment.CENTER
            ),
            padding=0,
            expand=True,
            bgcolor="#f5f7fa",
            alignment=ft.Alignment(0, 0)
        )
        
        # تحديث الواجهة
        view.controls[1].content = main_content
        safe_update(self.page)
        
        # بدء المؤقت
        if self.timer:
            pass
        
        async def timer_loop():
            while self.is_page_active:
                try:
                    if next_prayer_time:
                        hours, minutes, seconds = self.calculate_time_remaining(next_prayer_time)
                        new_val = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        new_color = self.prayer_colors.get(next_prayer_name, "#1a5fb4") if seconds % 2 == 0 else Colors.BLACK
                        changed = (self.countdown_text.value != new_val or
                                   self.countdown_text.color != new_color)
                        if changed:
                            self.countdown_text.value = new_val
                            self.countdown_text.color = new_color
                            try:
                                self.countdown_text.update()
                            except Exception:
                                pass
                        if self.is_page_active and not changed:
                            pass  # لا تحديث غير ضروري
                except Exception as ex:
                    if "destroyed" in str(ex).lower() or "session" in str(ex).lower():
                        self.is_page_active = False
                        break
                    print(f"خطأ في المؤقت: {ex}")
                await asyncio.sleep(1)

        self.page.run_task(timer_loop)

    def get_next_prayer(self, timings):
        prayer_times = [
            ('الفجر', timings['Fajr']),
            ('الشروق', timings['Sunrise']),
            ('الظهر', timings['Dhuhr']),
            ('العصر', timings['Asr']),
            ('المغرب', timings['Maghrib']),
            ('العشاء', timings['Isha'])
        ]
        
        current_time = datetime.now().strftime("%H:%M")
        
        for prayer_name, prayer_time in prayer_times:
            if current_time < prayer_time:
                return prayer_name, prayer_time
                
        return prayer_times[0]

    def calculate_time_remaining(self, prayer_time_str):
        try:
            now = datetime.now()
            prayer_time = datetime.strptime(prayer_time_str, "%H:%M")
            today = now.date()
            
            prayer_datetime = datetime.combine(today, prayer_time.time())
            current_datetime = datetime.combine(today, now.time())
            
            if prayer_datetime < current_datetime:
                prayer_datetime += timedelta(days=1)
            
            time_diff = prayer_datetime - current_datetime
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return hours, minutes, seconds
        except:
            return 0, 0, 0

    def get_prayer_times(self, view):
        try:
            # تحديث التاريخ الهجري محلياً
            self.hijri_date = self.get_accurate_hijri_date()
            
            cached_data = self.load_cached_data()
            
            if self.is_online():
                try:
                    location = self.get_precise_location_with_arabic()
                    
                    date = datetime.now().strftime("%d-%m-%Y")
                    params = {
                        "latitude": location['latitude'],
                        "longitude": location['longitude'],
                        "method": 5,
                        "tune": "0,0,0,0,0,0,0,0,0"
                    }
                    
                    with httpx.Client(timeout=10.0) as client:
                        response = client.get(
                            f"http://api.aladhan.com/v1/timings/{date}", 
                            params=params
                        )
                        data = response.json()
                    
                    if 'data' in data:
                        timings = data['data']['timings']
                        date_info = data['data']['date']['readable']
                        

                        
                        cache_data = {
                            'location': location,
                            'timings': timings,
                            'date_info': date_info,
                            'hijri_date': self.hijri_date,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.save_cached_data(cache_data)
                        
                        self.update_prayer_times_view(view, timings, location, date_info, self.hijri_date, False)
                        return
                    
                except Exception as api_error:
                    print(f"خطأ في API: {str(api_error)}")
            
            # إذا كان هناك بيانات مخزنة، استخدامها
            if cached_data:

                cached_data['hijri_date'] = self.hijri_date
                    
                self.update_prayer_times_view(
                    view, 
                    cached_data['timings'], 
                    cached_data['location'], 
                    cached_data.get('date_info', ''),
                    cached_data['hijri_date'], 
                    True
                )
                return
            
            # إذا لم تكن هناك بيانات مخزنة، استخدام البيانات الافتراضية مع التاريخ الهجري المحلي
            self.show_default_prayer_times(view)
            
        except Exception as e:
            print(f"خطأ عام: {str(e)}")
            self.show_error_view(view, "حدث خطأ في جلب البيانات")

    def show_error_view(self, view, message):
        self.stop_timer()
        
        error_content = Column(
            controls=[
                Container(height=80),
                Icon(Icons.ERROR_OUTLINE, size=70, color=Colors.RED_400),
                Container(height=20),
                Text(
                    message,
                    size=18,
                    color=Colors.BLACK,
                    weight=FontWeight.BOLD,
                    text_align=TextAlign.CENTER,
                    font_family=BUTTON_FONT
                ),
                Container(height=15),
                Text(
                    "تأكد من اتصالك بالإنترنت وحاول مرة أخرى",
                    size=14,
                    color=Colors.GREY_600,
                    text_align=TextAlign.CENTER,
                    font_family=BUTTON_FONT
                ),
                Container(height=30),
                FilledButton(
                    content=Row(
                        controls=[
                            Icon(Icons.REFRESH, size=22, color=Colors.WHITE),
                            Container(width=8),
                            Text("إعادة المحاولة", size=16, color=Colors.WHITE, font_family=BUTTON_FONT)
                        ],
                        alignment=MainAxisAlignment.CENTER
                    ),
                    on_click=lambda e: self.refresh_data(view),
                    style=ButtonStyle(
                        bgcolor="#FF9800",
                        padding=ft.Padding.only(left=25, right=25, top=12, bottom=12),
                        shape=RoundedRectangleBorder(radius=10),
                    ),
                    width=200,
                    height=48
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            alignment=MainAxisAlignment.CENTER
        )
        
        view.controls[1].content = Container(
            content=error_content,
            padding=20,
            expand=True,
            alignment=ft.Alignment(0, 0),
            bgcolor="#f5f7fa"
        )
        safe_update(self.page)

    def refresh_data(self, view):
        self.stop_timer()
        self.is_page_active = True
        
        view.controls[1].content = Column(
            [
                Container(height=100),
                ProgressRing(width=50, height=50, color="#4CAF50"),
                Text("جاري تحديث البيانات...", 
                     size=16, 
                     color=Colors.BLACK, 
                     font_family=BUTTON_FONT,
                     text_align=TextAlign.CENTER)
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            alignment=MainAxisAlignment.CENTER
        )
        safe_update(self.page)
        
        # تشغيل في thread منفصل لمنع تجميد الواجهة
        threading.Thread(target=self.get_prayer_times, args=(view,), daemon=True).start()

    def is_online(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def load_cached_data(self):
        try:
            if os.path.exists("prayer_times_cache.json"):
                with open("prayer_times_cache.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'timestamp' in data:
                        try:
                            cache_time = datetime.fromisoformat(data['timestamp'])
                            time_diff = datetime.now() - cache_time
                            if time_diff.days < 3:
                                return data
                        except:
                            pass
                    
            return None
        except Exception as e:
            print(f"خطأ في تحميل البيانات المحفوظة: {str(e)}")
            return None

    def save_cached_data(self, data):
        try:
            with open("prayer_times_cache.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ البيانات: {str(e)}")

    def get_precise_location_with_arabic(self):
        """الحصول على الموقع مع اسم المدينة بالعربية"""
        try:
            # محاولة الحصول على الموقع من IP باستخدام httpx
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get('https://ipinfo.io/json')
                if response.status_code == 200:
                    data = response.json()
                    loc = data.get('loc', '').split(',')
                    if len(loc) == 2:
                        city = data.get('city', '')
                        country = data.get('country', '')
                        
                        # تحويل اسم الدولة إلى عربي
                        country_ar = self.translate_country_to_arabic(country)
                        
                        return {
                            'latitude': float(loc[0]),
                            'longitude': float(loc[1]),
                            'address': f"{city}، {country}",
                            'address_ar': f"{city}، {country_ar}",
                            'method': 'IP'
                        }
            except:
                pass
            
            # بديل: خدمة ip-api
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get('http://ip-api.com/json/?fields=lat,lon,city,country')
                if response.status_code == 200:
                    data = response.json()
                    if data.get('lat'):
                        country_ar = self.translate_country_to_arabic(data.get('country', ''))
                        return {
                            'latitude': data['lat'],
                            'longitude': data['lon'],
                            'address': f"{data.get('city', '')}، {data.get('country', '')}",
                            'address_ar': f"{data.get('city', '')}، {country_ar}",
                            'method': 'IP'
                        }
            except:
                pass
            return {
                'latitude': 24.7136,
                'longitude': 46.6753,
                'address': "Riyadh, Saudi Arabia",
                'address_ar': "الرياض، المملكة العربية السعودية",
                'method': 'افتراضي'
            }
        except Exception as e:
            print(f"خطأ في تحديد الموقع: {str(e)}")
            return {
                'latitude': 24.7136,
                'longitude': 46.6753,
                'address': "Riyadh, Saudi Arabia",
                'address_ar': "الرياض، المملكة العربية السعودية",
                'method': 'افتراضي'
            }

    def translate_country_to_arabic(self, country_code):
        """ترجمة رمز الدولة إلى الاسم العربي"""
        country_translations = {
            "SA": "المملكة العربية السعودية",
            "EG": "مصر",
            "AE": "الإمارات العربية المتحدة",
            "QA": "قطر",
            "KW": "الكويت",
            "BH": "البحرين",
            "OM": "عُمان",
            "JO": "الأردن",
            "LB": "لبنان",
            "SY": "سوريا",
            "IQ": "العراق",
            "YE": "اليمن",
            "PS": "فلسطين",
            "MA": "المغرب",
            "DZ": "الجزائر",
            "TN": "تونس",
            "LY": "ليبيا",
            "SD": "السودان",
            "SO": "الصومال",
            "DJ": "جيبوتي",
            "MR": "موريتانيا",
            "US": "الولايات المتحدة الأمريكية",
            "GB": "المملكة المتحدة",
            "FR": "فرنسا",
            "DE": "ألمانيا",
            "IT": "إيطاليا",
            "ES": "إسبانيا",
            "CA": "كندا",
            "AU": "أستراليا",
            "JP": "اليابان",
            "CN": "الصين",
            "IN": "الهند",
            "PK": "باكستان",
            "TR": "تركيا",
            "RU": "روسيا",
            "BR": "البرازيل",
            "MX": "المكسيك",
        }
        
        return country_translations.get(country_code, country_code)

    def get_accurate_hijri_date(self, date_obj=None):
        """حساب التاريخ الهجري بدقة باستخدام معادلات علمية"""
        if date_obj is None:
            date_obj = datetime.now()
        gy = date_obj.year
        gm = date_obj.month
        gd = date_obj.day
        
        # خوارزمية تحويل ميلادي إلى هجري
        if (gy > 1582) or ((gy == 1582) and (gm > 10)) or ((gy == 1582) and (gm == 10) and (gd > 14)):
            jd = (int((1461 * (gy + 4800 + int((gm - 14) / 12))) / 4) +
                  int((367 * (gm - 2 - 12 * int((gm - 14) / 12))) / 12) -
                  int((3 * int((gy + 4900 + int((gm - 14) / 12)) / 100)) / 4) +
                  gd - 32075)
        else:
            jd = 367 * gy - int((7 * (gy + 5001 + int((gm - 9) / 7))) / 4) + int((275 * gm) / 9) + gd + 1729777
        
        l = jd - 1948440 + 10632
        n = int((l - 1) / 10631)
        l = l - 10631 * n + 354
        j = (int((10985 - l) / 5316)) * (int((50 * l) / 17719)) + (int(l / 5670)) * (int((43 * l) / 15238))
        l = l - (int((30 - j) / 15)) * (int((17719 * j) / 50)) - (int(j / 16)) * (int((15238 * j) / 43)) + 29
        
        hm = int((24 * l) / 709)
        hd = l - int((709 * hm) / 24)
        hy = 30 * n + j - 30
        
        # أسماء الأشهر الهجرية
        hijri_months = [
            "المحرم", "صفر", "ربيع الأول", "ربيع الآخر",
            "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
            "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
        ]
        
        return f"{hd} {hijri_months[hm-1]} {hy} هـ"

    def show_default_prayer_times(self, view):
        """عرض مواقيت الصلاة الافتراضية عند عدم وجود اتصال"""
        try:
            # تحديث التاريخ الهجري محلياً (للتأكيد)
            self.hijri_date = self.get_accurate_hijri_date()
            # مواقيت الصلاة الافتراضية (يمكن تعديلها حسب الموقع)
            default_timings = {
                'Fajr': '05:00',
                'Sunrise': '06:00',
                'Dhuhr': '12:00',
                'Asr': '15:00',
                'Maghrib': '18:00',
                'Isha': '19:30'
            }
            
            default_location = {
                'latitude': 24.7136,
                'longitude': 46.6753,
                'address': "Riyadh, Saudi Arabia",
                'address_ar': "الرياض، المملكة العربية السعودية",
                'method': 'افتراضي'
            }
            
            date_info = datetime.now().strftime("%d %B %Y")
            
            self.update_prayer_times_view(
                view, 
                default_timings, 
                default_location, 
                date_info,
                self.hijri_date,
                True
            )
        except Exception as e:
            print(f"خطأ في عرض المواقيت الافتراضية: {str(e)}")
            self.show_error_view(view, "لا يمكن تحميل مواقيت الصلاة")

    @staticmethod
    def create(page: Page):
        prayer_times_page = PrayerTimesPage(page)
        return prayer_times_page.create_view()
    
# ============ صفحة الإعدادات المعدلة بشكل عصري ومتجاوب ============
class SettingsPage:
    def __init__(self, page: Page):
        self.page = page
        self.app_version = "1.0.0"
        self.current_background = load_home_background()
        
        self.home_backgrounds = [
            {
                "id": "pattern",
                "name": "الافتراضية",
                "path": "assets/icons/1200.webp",
                "thumbnail": "assets/icons/1200.webp"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/1300.webp",
                "thumbnail": "assets/icons/1300.webp"
            },
            {
                "id": "default",
                "name": "الإضافية",
                "path": "assets/icons/hadeer.jpg",
                "thumbnail": "assets/icons/hadeer.jpg"
            },
            {
                "id": "mosque1",
                "name": "الإضافية",
                "path": "assets/icons/ramadana.jpg",
                "thumbnail": "assets/icons/ramadana.jpg"
            },
            {
                "id": "kaaba",
                "name": "الإضافية",
                "path": "assets/icons/essra.jpg",
                "thumbnail": "assets/icons/essra.jpg"
            },
            {
                "id": "nature",
                "name": "الإضافية",
                "path": "assets/icons/papa1.jpg",
                "thumbnail": "assets/icons/papa1.jpg"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/papa2.jpg",
                "thumbnail": "assets/icons/papa2.jpg"
            },
            {
                "id": "nature",
                "name": "الإضافية",
                "path": "assets/icons/papa3.jpg",
                "thumbnail": "assets/icons/papa3.jpg"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/papa4.jpg",
                "thumbnail": "assets/icons/papa4.jpg"
            },
            {
                "id": "nature",
                "name": "الإضافية",
                "path": "assets/icons/papa5.jpg",
                "thumbnail": "assets/icons/papa5.jpg"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/papa6.jpg",
                "thumbnail": "assets/icons/papa6.jpg"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/papa7.jpg",
                "thumbnail": "assets/icons/papa7.jpg"
            },
            {
                "id": "nature",
                "name": "الإضافية",
                "path": "assets/icons/papa8.jpg",
                "thumbnail": "assets/icons/papa8.jpg"
            },
            {
                "id": "pattern",
                "name": "الإضافية",
                "path": "assets/icons/papa9.jpg",
                "thumbnail": "assets/icons/papa9.jpg"
            },
        ]
        
        self.sample_text = Text(
            value="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\nاللَّهُ لَا إِلَهَ إِلَّا هُوَ",
            size=current_font_size,
            font_family=FONT_NAME,
            color=Colors.BLACK,
            text_align=TextAlign.CENTER
        )
        
        self.current_font_size_text = Text(
            value=f"حجم الخط الحالي: {current_font_size}",
            size=16,
            color=Colors.BLACK,
            font_family=BUTTON_FONT,
            weight=FontWeight.BOLD,
            text_align=TextAlign.CENTER
        )
        
        self.current_background_text = Text(
            value=f"الخلفية الحالية: {self.get_background_name(self.current_background)}",
            size=16,
            color=Colors.BLACK,
            font_family=BUTTON_FONT,
            weight=FontWeight.BOLD,
            text_align=TextAlign.CENTER
        )

    def get_background_name(self, bg_path):
        for bg in self.home_backgrounds:
            if bg["path"] == bg_path:
                return bg["name"]
        return "الافتراضية"

    def increase_font(self, e):
        global current_font_size
        try:
            font_size = int(current_font_size)
        except:
            font_size = DEFAULT_FONT_SIZE
            
        if font_size < MAX_FONT_SIZE:
            font_size += 2
            current_font_size = font_size
            self.sample_text.size = font_size
            self.current_font_size_text.value = f"حجم الخط الحالي: {font_size}"
            
            settings = load_settings()
            settings['font_size'] = font_size
            save_settings_dict(settings)
            
            self.show_snackbar(f"تم زيادة حجم الخط إلى {font_size}", Colors.GREEN)
            safe_update(self.page)

    def decrease_font(self, e):
        global current_font_size
        try:
            font_size = int(current_font_size)
        except:
            font_size = DEFAULT_FONT_SIZE
            
        if font_size > MIN_FONT_SIZE:
            font_size -= 2
            current_font_size = font_size
            self.sample_text.size = font_size
            self.current_font_size_text.value = f"حجم الخط الحالي: {font_size}"
            
            settings = load_settings()
            settings['font_size'] = font_size
            save_settings_dict(settings)
            
            self.show_snackbar(f"تم تصغير حجم الخط إلى {font_size}", Colors.ORANGE)
            safe_update(self.page)

    def reset_font(self, e):
        global current_font_size
        current_font_size = DEFAULT_FONT_SIZE
        self.sample_text.size = DEFAULT_FONT_SIZE
        self.current_font_size_text.value = f"حجم الخط الحالي: {DEFAULT_FONT_SIZE}"
        
        settings = load_settings()
        settings['font_size'] = DEFAULT_FONT_SIZE
        save_settings_dict(settings)
        
        self.show_snackbar("تم إعادة تعيين حجم الخط إلى الافتراضي", Colors.BLUE)
        safe_update(self.page)

    def change_background(self, e, bg_path):
        global current_home_background
        current_home_background = bg_path
        self.current_background = bg_path
        self.current_background_text.value = f"الخلفية الحالية: {self.get_background_name(bg_path)}"
        
        settings = load_settings()
        settings['home_background'] = bg_path
        save_settings_dict(settings)
        
        self.update_home_page_background(bg_path)
        
        bg_name = self.get_background_name(bg_path)
        self.show_snackbar(f"✅ تم تغيير الخلفية إلى: {bg_name}", Colors.GREEN)
        
        if hasattr(self, 'background_dialog'):
            self.background_dialog.open = False
            safe_update(self.page)
        
        safe_update(self.page)

    def update_home_page_background(self, new_background):
        global current_home_background
        current_home_background = new_background
        
        for view in self.page.views:
            if view.route == "/":
                home_view = HomePage.create(self.page)
                view_index = self.page.views.index(view)
                self.page.views[view_index] = home_view
                break

    def show_background_dialog(self, e):
        background_grid = GridView(
            runs_count=2,
            max_extent=150,
            child_aspect_ratio=0.9,
            spacing=15,
            run_spacing=15,
            padding=10,
            controls=[
                Container(
                    width=150,
                    height=170,
                    border_radius=12,
                    border=ft.Border.all(
                        3, 
                        Colors.GREEN if bg["path"] == self.current_background else Colors.GREY_300
                    ),
                    alignment=ft.Alignment(0, 0),
                    on_click=lambda e, path=bg["path"]: self.change_background(e, path),
                    content=Column(
                        [
                            Container(
                                Image(
                                    src=bg["thumbnail"],
                                    width=130,
                                    height=110,
                                    fit=ft.BoxFit.COVER,
                                    border_radius=8,
                                ),
                                alignment=ft.Alignment(0, 0),
                            ),
                            Text(
                                bg["name"],
                                size=15,
                                color=Colors.BLACK,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            ),
                            Container(
                                Icon(
                                    Icons.CHECK_CIRCLE,
                                    size=24,
                                    color=Colors.GREEN
                                ),
                                visible=(bg["path"] == self.current_background),
                                margin=ft.Margin.only(top=5)
                            )
                        ],
                        spacing=5,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        alignment=MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor=Colors.WHITE,
                    padding=10
                )
                for bg in self.home_backgrounds
            ]
        )

        self.background_dialog = AlertDialog(
            title=Text(
                "🎨 اختر خلفية الصفحة الرئيسية", 
                font_family=BUTTON_FONT, 
                weight=FontWeight.BOLD,
                size=20,
                text_align=TextAlign.CENTER
            ),
            content=Container(
                content=Column(
                    [
                        Text(
                            "اختر من الخلفيات المتاحة:",
                            size=17,
                            color=Colors.BLACK,
                            font_family=BUTTON_FONT,
                            weight=FontWeight.BOLD,
                            text_align=TextAlign.CENTER
                        ),
                        Container(height=10),
                        Text(
                            "سيتم تطبيق الخلفية على الصفحة الرئيسية للتطبيق",
                            size=14,
                            color=Colors.GREY_600,
                            font_family=BUTTON_FONT,
                            text_align=TextAlign.CENTER
                        ),
                        Container(height=20),
                        background_grid
                    ],
                    scroll=ScrollMode.AUTO,
                    height=400,
                    width=350
                )
            ),
            actions=[
                Container(
                    content=TextButton(
                        "إغلاق",
                        on_click=lambda e: [setattr(self.background_dialog, "open", False), safe_update(self.page)],
                        style=ButtonStyle(
                            color=Colors.RED,
                            padding=15
                        )
                    ),
                    alignment=ft.Alignment(0, 0)
                )
            ]
        )
        self.page.overlay.append(self.background_dialog)
        self.background_dialog.open = True
        safe_update(self.page)  # ✅ الطريقة الجديدة

    def show_notifications_dialog(self, e):
        dialog = AlertDialog(
            title=Text(
                "🔔 الإشعارات",
                font_family=BUTTON_FONT,
                weight=FontWeight.BOLD, 
                size=22,
                text_align=TextAlign.CENTER
            ),
            content=Column(
                [
                    Icon(Icons.ACCESS_TIME, size=60, color=Colors.BLUE),
                    Container(height=10),
                    Text(
                        "ميزة الإشعارات",
                        size=20,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT, 
                        color=Colors.BLUE,
                        text_align=TextAlign.CENTER
                    ),
                    Divider(height=20),
                    Text(
                        "سيتم إضافة ميزة الإشعارات قريباً بإذن الله\n\n"
                        "ستتمكن من:\n"
                        "• تذكيرك بأذكار الصباح والمساء\n"
                        "• تنبيهك بمواقيت الصلاة\n"
                        "• تذكيرك بأهدافك اليومية\n"
                        "• تذكيرك بالسُبحة\n"
                        "• تذكيرك بالمزيد من العبادات",
                        size=16,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    )
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=15
            ),
            actions=[
                Container(
                    TextButton(
                        "حسناً", 
                        on_click=lambda e: [setattr(dialog, "open", False), safe_update(self.page)],
                        style=ButtonStyle(
                            color=Colors.BLUE,
                            padding=15
                        )
                    ),
                    alignment=ft.Alignment(0, 0)
                )
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        safe_update(self.page)  # ✅ الطريقة الجديدة

    def show_snackbar(self, message, color):
        _show_snack(self.page, message, color, 2000)

    def show_share_snackbar(self):
        self.show_snackbar(
            "✅ تم نسخ رسالة المشاركة! شاركها مع أحبائك 🌿",
            Colors.GREEN
        )
        safe_update(self.page)

    def create_view(self):
        return View(
            route="/settings",
            controls=[
                AppBar(
                    title=Text(
                        "الإعدادات",
                        weight=FontWeight.BOLD,
                        size=20,
                        color=Colors.WHITE,
                        text_align=TextAlign.CENTER
                    ),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page),
                    ),
                ),
                Container(
                    content=ListView(
                        controls=[
                            # ========== قسم إعدادات الخط ==========
                            Container(
                                content=Column(
                                    [
                                        Container(
                                            content=Text(
                                                "إعدادات الخط",
                                                size=20,
                                                weight=FontWeight.BOLD, 
                                                color=APP_BGCOLOR,
                                                font_family=BUTTON_FONT,
                                                text_align=TextAlign.CENTER
                                            ),
                                            margin=ft.Margin.only(bottom=20)
                                        ),
                                        
                                        Container(
                                            content=self.current_font_size_text,
                                            padding=ft.Padding.symmetric(vertical=10),
                                            alignment=ft.Alignment(0, 0)
                                        ),
                                        
                                        Container(height=20),
                                        
                                        Container(
                                            content=Column(
                                                [
                                                    Container(
                                                        content=Button(
                                                            "تكبير الخط",
                                                            icon=Icons.ZOOM_IN,
                                                            on_click=self.increase_font,
                                                            style=ButtonStyle(
                                                                bgcolor="#4CAF50",
                                                                color=Colors.WHITE,
                                                                padding=ft.Padding.symmetric(horizontal=25, vertical=15),
                                                                shape=RoundedRectangleBorder(radius=12),
                                                            ),
                                                            height=55,
                                                            width=250,
                                                        ),
                                                        alignment=ft.Alignment(0, 0),
                                                        margin=ft.Margin.only(bottom=10)
                                                    ),
                                                    
                                                    Container(
                                                        content=Button(
                                                            "تصغير الخط",
                                                            icon=Icons.ZOOM_OUT,
                                                            on_click=self.decrease_font,
                                                            style=ButtonStyle(
                                                                bgcolor="#FF9800",
                                                                color=Colors.WHITE,
                                                                padding=ft.Padding.symmetric(horizontal=25, vertical=15),
                                                                shape=RoundedRectangleBorder(radius=12),
                                                            ),
                                                            height=55,
                                                            width=250,
                                                        ),
                                                        alignment=ft.Alignment(0, 0),
                                                        margin=ft.Margin.only(bottom=10)
                                                    ),
                                                    
                                                    Container(
                                                        content=Button(
                                                            "إعادة تعيين",
                                                            icon=Icons.RESTORE,
                                                            on_click=self.reset_font,
                                                            style=ButtonStyle(
                                                                bgcolor="#2196F3",
                                                                color=Colors.WHITE,
                                                                padding=ft.Padding.symmetric(horizontal=25, vertical=15),
                                                                shape=RoundedRectangleBorder(radius=12),
                                                            ),
                                                            height=55,
                                                            width=250,
                                                        ),
                                                        alignment=ft.Alignment(0, 0),
                                                        margin=ft.Margin.only(bottom=20)
                                                    ),
                                                ],
                                                spacing=0,
                                                horizontal_alignment=CrossAxisAlignment.CENTER
                                            )
                                        ),
                                        
                                        Container(height=20),
                                        
                                        Container(
                                            content=Column(
                                                [
                                                    Text(
                                                        "عينة من الخط:",
                                                        size=16,
                                                        weight=FontWeight.BOLD, 
                                                        color=Colors.BLACK,
                                                        font_family=BUTTON_FONT,
                                                        text_align=TextAlign.CENTER
                                                    ),
                                                    Container(height=15),
                                                    Container(
                                                        content=self.sample_text,
                                                        padding=25,
                                                        bgcolor="#f8f9fa",
                                                        border_radius=15,
                                                        border=ft.Border.all(1, Colors.GREY_300),
                                                        alignment=ft.Alignment(0, 0)
                                                    )
                                                ],
                                                spacing=5,
                                                horizontal_alignment=CrossAxisAlignment.CENTER
                                            )
                                        )
                                    ],
                                    spacing=0,
                                    horizontal_alignment=CrossAxisAlignment.CENTER
                                ),
                                padding=ft.Padding.symmetric(vertical=25, horizontal=15),
                                bgcolor=Colors.WHITE,
                                border_radius=15,
                                shadow=BoxShadow(
                                    spread_radius=0,
                                    blur_radius=15,
                                    color=Colors.with_opacity(0.1, Colors.BLACK),
                                    offset=Offset(0, 3)
                                ),
                                margin=ft.Margin.only(bottom=20, left=20, right=20, top=10),
                                width=350
                            ),
                            
                            # ========== قسم خلفية الصفحة الرئيسية ==========
                            Container(
                                content=Column(
                                    [
                                        Container(
                                            content=Text(
                                                "خلفية الصفحة الرئيسية",
                                                size=20,
                                                weight=FontWeight.BOLD, 
                                                color=APP_BGCOLOR,
                                                font_family=BUTTON_FONT,
                                                text_align=TextAlign.CENTER
                                            ),
                                            margin=ft.Margin.only(bottom=20)
                                        ),
                                        
                                        Container(
                                            content=Column(
                                                [
                                                    Container(
                                                        content=Row(
                                                            [
                                                                Container(
                                                                    width=80,
                                                                    height=60,
                                                                    border_radius=8,
                                                                    border=ft.Border.all(2, Colors.GREY_300),
                                                                    content=Image(
                                                                        src=self.current_background,
                                                                        width=80,
                                                                        height=60,
                                                                        fit=ft.BoxFit.COVER,
                                                                        border_radius=6,
                                                                    )
                                                                ),
                                                                Container(width=15),
                                                                Column(
                                                                    [
                                                                        Text(
                                                                            "الخلفية الحالية",
                                                                            size=16, 
                                                                            color=Colors.BLACK, 
                                                                            weight=FontWeight.BOLD,
                                                                            font_family=BUTTON_FONT
                                                                        ),
                                                                        Container(height=5),
                                                                        Text(
                                                                            self.get_background_name(self.current_background),
                                                                            size=14,
                                                                            color=Colors.GREY_600,
                                                                            font_family=BUTTON_FONT
                                                                        )
                                                                    ],
                                                                    spacing=2,
                                                                    horizontal_alignment=CrossAxisAlignment.START
                                                                )
                                                            ],
                                                            vertical_alignment=CrossAxisAlignment.CENTER,
                                                            alignment=MainAxisAlignment.CENTER
                                                        ),
                                                        alignment=ft.Alignment(0, 0),
                                                        padding=ft.Padding.symmetric(vertical=15)
                                                    ),
                                                    
                                                    Divider(height=20, color=Colors.GREY_200),
                                                    
                                                    Container(
                                                        content=Button(
                                                            "🖼️ تغيير خلفية الصفحة",
                                                            on_click=self.show_background_dialog,
                                                            style=ButtonStyle(
                                                                bgcolor="#9C27B0",
                                                                color=Colors.WHITE,
                                                                padding=ft.Padding.symmetric(horizontal=25, vertical=15),
                                                                shape=RoundedRectangleBorder(radius=12),
                                                                elevation=5
                                                            ),
                                                            height=55,
                                                            width=280,
                                                        ),
                                                        alignment=ft.Alignment(0, 0),
                                                        margin=ft.Margin.only(bottom=10)
                                                    ),
                                                    
                                                    
                                                ],
                                                spacing=5,
                                                horizontal_alignment=CrossAxisAlignment.CENTER
                                            ),
                                            padding=ft.Padding.symmetric(vertical=25, horizontal=15),
                                            bgcolor=Colors.WHITE,
                                            border_radius=15,
                                            shadow=BoxShadow(
                                                spread_radius=0,
                                                blur_radius=15,
                                                color=Colors.with_opacity(0.1, Colors.BLACK),
                                                offset=Offset(0, 3)
                                            ),
                                            margin=ft.Margin.only(bottom=20, left=20, right=20),
                                            width=350
                                        )
                                    ],
                                    spacing=0,
                                    horizontal_alignment=CrossAxisAlignment.CENTER
                                ),
                                alignment=ft.Alignment(0, 0)
                            ),
                            
                            # ========== قسم الإشعارات ==========
                            Container(
                                content=Column(
                                    [
                                        Container(
                                            content=Text(
                                                "الإشعارات",
                                                size=20,
                                                weight=FontWeight.BOLD, 
                                                color=APP_BGCOLOR,
                                                font_family=BUTTON_FONT,
                                                text_align=TextAlign.CENTER
                                            ),
                                            margin=ft.Margin.only(bottom=20)
                                        ),
                                        
                                        Container(
                                            content=Column(
                                                [
                                                    
                                                    Text(
                                                        "تفعيل الإشعارات للبقاء على اتصال مع عباداتك",
                                                        size=14, 
                                                        color=Colors.GREY_600,
                                                        font_family=BUTTON_FONT,
                                                        text_align=TextAlign.CENTER
                                                    ),
                                                    Container(height=25),
                                                    
                                                    Container(
                                                        content=Button(
                                                            "🔔 إعداد الإشعارات",
                                                            on_click=self.show_notifications_dialog,
                                                            style=ButtonStyle(
                                                                bgcolor="#607D8B",
                                                                color=Colors.WHITE,
                                                                padding=ft.Padding.only(left=30, right=30, top=18, bottom=18),
                                                                shape=RoundedRectangleBorder(radius=12),
                                                                elevation=5
                                                            ),
                                                            height=60,
                                                            width=280,
                                                        ),
                                                        alignment=ft.Alignment(0, 0)
                                                    )
                                                ],
                                                spacing=5,
                                                horizontal_alignment=CrossAxisAlignment.CENTER
                                            ),
                                            padding=ft.Padding.symmetric(vertical=25, horizontal=15),
                                            bgcolor=Colors.WHITE,
                                            border_radius=15,
                                            shadow=BoxShadow(
                                                spread_radius=0,
                                                blur_radius=15,
                                                color=Colors.with_opacity(0.1, Colors.BLACK),
                                                offset=Offset(0, 3)
                                            ),
                                            margin=ft.Margin.only(bottom=20, left=20, right=20),
                                            width=350
                                        )
                                    ],
                                    spacing=0,
                                    horizontal_alignment=CrossAxisAlignment.CENTER
                                ),
                                alignment=ft.Alignment(0, 0)
                            ),

                            # ========== قسم عن التطبيق ==========
                            Container(
                                content=Column(
                                    [
                                        Container(
                                            content=Text(
                                                "عن التطبيق",
                                                size=20,
                                                weight=FontWeight.BOLD, 
                                                color=APP_BGCOLOR,
                                                font_family=BUTTON_FONT,
                                                text_align=TextAlign.CENTER
                                            ),
                                            margin=ft.Margin.only(bottom=20)
                                        ),

                                        Container(
                                            content=Column(
                                                [
                                                    Container(
                                                        content=Row(
                                                            [
                                                                Container(
                                                                    width=60,
                                                                    height=60,
                                                                    border_radius=30,
                                                                    bgcolor=APP_BGCOLOR,
                                                                    alignment=ft.Alignment(0, 0),
                                                                    content=Icon(Icons.APP_REGISTRATION, size=28, color=Colors.WHITE)
                                                                ),
                                                                Container(width=20),
                                                                Column(
                                                                    [
                                                                        Text(
                                                                            "إصدار التطبيق",
                                                                            size=17,
                                                                            weight=FontWeight.BOLD, 
                                                                            color=Colors.BLACK,
                                                                            font_family=BUTTON_FONT,
                                                                            text_align=TextAlign.CENTER
                                                                        ),
                                                                        Container(height=5),
                                                                        Text(
                                                                            f"الإصدار {self.app_version}",
                                                                            size=15, 
                                                                            color=Colors.GREY_600,
                                                                            font_family=BUTTON_FONT,
                                                                            text_align=TextAlign.CENTER
                                                                        )
                                                                    ],
                                                                    spacing=2,
                                                                    horizontal_alignment=CrossAxisAlignment.CENTER
                                                                ),
                                                            ],
                                                            vertical_alignment=CrossAxisAlignment.CENTER,
                                                            alignment=MainAxisAlignment.CENTER
                                                        ),
                                                        padding=ft.Padding.symmetric(vertical=15),
                                                        alignment=ft.Alignment(0, 0)
                                                    ),
                                                    
                                                    Divider(height=20, color=Colors.GREY_200),
                                                    
                                                    Container(
                                                        content=Column(
                                                            [
                                                                Text(
                                                                    "القريب - أذكار المسلم",
                                                                    size=17,
                                                                    weight=FontWeight.BOLD, 
                                                                    color=Colors.BLACK,
                                                                    font_family=BUTTON_FONT,
                                                                    text_align=TextAlign.CENTER
                                                                ),
                                                                Container(height=10),
                                                                Text(
                                                                    "تطبيق إسلامي شامل يجمع الأذكار والأدعية والعبادات اليومية "
                                                                    "لتكون رفيقك في التقرب إلى الله تعالى",
                                                                    size=15,
                                                                    color=Colors.GREY_600,
                                                                    font_family=BUTTON_FONT,
                                                                    text_align=TextAlign.CENTER
                                                                )
                                                            ],
                                                            spacing=5,
                                                            horizontal_alignment=CrossAxisAlignment.CENTER
                                                        ),
                                                        padding=ft.Padding.symmetric(vertical=15)
                                                    ),
                                                    
                                                    Divider(height=20, color=Colors.GREY_200),
                                                    
                                                    Container(
                                                        content=Column(
                                                            [
                                                                Row(
                                                                    [
                                                                        Text(
                                                                            "© 2025 جميع الحقوق محفوظة",
                                                                            size=14, 
                                                                            color=Colors.GREY_600,
                                                                            font_family=BUTTON_FONT
                                                                        )
                                                                    ],
                                                                    spacing=5,
                                                                    alignment=MainAxisAlignment.CENTER
                                                                ),
                                                                Container(height=10),
                                                                Text(
                                                                    "تطوير: فريق القريب",
                                                                    size=14,
                                                                    color=Colors.GREY_600, 
                                                                    font_family=BUTTON_FONT,
                                                                    text_align=TextAlign.CENTER
                                                                )
                                                            ],
                                                            spacing=5,
                                                            horizontal_alignment=CrossAxisAlignment.CENTER
                                                        ),
                                                        padding=ft.Padding.symmetric(vertical=15),
                                                        alignment=ft.Alignment(0, 0)
                                                    )
                                                ],
                                                spacing=0,
                                                horizontal_alignment=CrossAxisAlignment.CENTER
                                            ),
                                            padding=ft.Padding.symmetric(vertical=25, horizontal=15),
                                            bgcolor=Colors.WHITE,
                                            border_radius=15,
                                            shadow=BoxShadow(
                                                spread_radius=0,
                                                blur_radius=15,
                                                color=Colors.with_opacity(0.1, Colors.BLACK),
                                                offset=Offset(0, 3)
                                            ),
                                            margin=ft.Margin.only(bottom=30, left=20, right=20),
                                            width=350
                                        )
                                    ],
                                    spacing=0,
                                    horizontal_alignment=CrossAxisAlignment.CENTER
                                ),
                                alignment=ft.Alignment(0, 0)
                            ),

                            Container(height=40)
                        ],
                        expand=True
                    ),
                    expand=True,
                    bgcolor="#f5f7fa",
                    alignment=ft.Alignment(0, 0)
                )
            ],
            bgcolor="#f5f7fa",
            padding=0,
            spacing=0,
        )

    @staticmethod
    def create(page: Page):
        settings_page = SettingsPage(page)
        return settings_page.create_view()

# ============ صفحة تعليم الوضوء (نسخة بسيطة وكاملة) ============
class WuduLearningPage:
    @staticmethod
    def create(page: Page):
        # خطوات الوضوء مع الصور التوضيحية
        wudu_steps = [
            {
                "title": "النية والبسملة وغسل الكفين",
                "description": "غسل الكفين ثلاث مرات مع تخليل الأصابع",
                "image": "assets/icons/wodu.1.webp"
            },
            {
                "title": "المضمضة والاستنشاق",
                "description": "المضمضة (إدخال الماء في الفم) والاستنشاق (جذب الماء بالأنف) ثلاث مرات",
                "image": "assets/icons/wodu.2.webp"
            },
            {
                "title": "غسل الوجه",
                "description": "غسل الوجه ثلاث مرات من منابت شعر الرأس إلى الذقن",
                "image": "assets/icons/wodu.3.webp"
            },
            {
                "title": "غسل اليدين",
                "description": "غسل اليدين إلى المرفقين ثلاث مرات (اليمنى ثم اليسرى)",
                "image": "assets/icons/wodu.4.webp"
            },
            {
                "title": "مسح الرأس",
                "description": "مسح الرأس مرة واحدة",
                "image": "assets/icons/wodu.5.webp"
            },
            {
                "title": "مسح الأذنين",
                "description": "مسح الأذنين مرة واحدة",
                "image": "assets/icons/wodu.6.webp"
            },        
            {
                "title": "غسل الرجلين",
                "description": "غسل الرجلين إلى الكعبين ثلاث مرات (اليمنى ثم اليسرى)",
                "image": "assets/icons/wodu.7.webp"
            }
        ]

        # دالة لفتح الفيديو على YouTube
        async def open_url_async(url):
            """فتح الرابط بشكل غير متزامن - يعمل على الهاتف والديسكتوب"""
            await _open_url(url, page)
            return True

        def open_video(e):
            """فتح الفيديو"""
            url = "https://youtu.be/HMERx-0_Koo?si=m5sMHe9hfToz1znv"
            try:
                page.run_task(open_url_async, url)
                _show_snack(page, "📺 جاري فتح فيديو تعليم الوضوء...", Colors.RED, 2000)
                safe_update(page)
                
            except Exception as e:
                print(f"خطأ في فتح الفيديو: {e}")
                # عرض رسالة خطأ
                _show_snack(page, "❌ حدث خطأ في فتح الفيديو", Colors.RED, 2000)

        # دالة مساعدة لتأثير التحويم (اختياري)
        def hover_video(e):
            if e.data == "true":
                e.control.scale = 1.02
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=15,
                    color=Colors.with_opacity(0.3, Colors.BLUE),
                    offset=Offset(0, 5)
                )
            else:
                e.control.scale = 1.0
                e.control.shadow = BoxShadow(
                    spread_radius=0,
                    blur_radius=0,
                    color=Colors.TRANSPARENT,
                    offset=Offset(0, 0)
                )
            e.control.update()

        # إنشاء قائمة بالخطوات مع الصور
        step_widgets = []
        for step in wudu_steps:
            step_widgets.append(
                Container(
                    content=Column(
                        [
                            # صورة الخطوة
                            Container(
                                Image(
                                    src=step["image"],
                                    width=400,
                                    height=220,
                                    fit=ft.BoxFit.CONTAIN,
                                    border_radius=10,
                                ),
                                alignment=ft.Alignment(0, 0),
                                padding=5,
                            ),
                            
                            # عنوان الخطوة
                            Text(
                                step["title"],
                                size=18,
                                color="#0daca6",
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                            ),
                            
                            # وصف الخطوة
                            Text(
                                step["description"],
                                size=16,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                            ),
                            
                            Divider(color=Colors.BLUE, height=10),
                        ],
                        spacing=5,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    bgcolor=Colors.WHITE,
                    border_radius=15,
                    margin=ft.Margin.only(bottom=10),
                )
            )

        return View(
            route="/wudu_learning",
            controls=[
                AppBar(
                    title=Text("تعليم الوضوء", weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(page),
                    ),
                ),
                
                Container(
                    content=Column(
                        controls=[
                            Container(height=5),
                            
                            # مقدمة عن الوضوء
                            Container(
                                content=Text(
                                    "الوضوء شرط من شروط صحة الصلاة، وقد بينه النبي ﷺ بأفعاله وأقواله",
                                    size=18,
                                    color=Colors.BLACK,
                                    text_align=TextAlign.CENTER,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                ),
                                padding=15,
                                bgcolor=Colors.WHITE,
                                border_radius=10,
                                margin=ft.Margin.only(bottom=10),
                            ),
                            
                            # خطوات الوضوء مع الصور
                            *step_widgets,
                            
                            # حديث عن فضل الوضوء
                            Container(
                                content=Column(
                                    [
                                        Text(
                                            "عن أبي هريرة رضي الله عنه أن النبي ﷺ قال:",
                                            size=16,
                                            color=Colors.BLACK,
                                            text_align=TextAlign.CENTER,
                                            weight=FontWeight.BOLD,
                                            font_family=BUTTON_FONT,
                                        ),
                                        Container(height=5),
                                        Text(
                                            "إذا توضأ العبد المسلم فغسل وجهه خرج من وجهه كل خطيئة نظر إليها بعينيه مع الماء، فإذا غسل يديه خرج من يديه كل خطيئة بطشتها يداه مع الماء، فإذا غسل رجليه خرجت كل خطيئة مشتها رجلاه مع الماء، حتى يخرج نقياً من الذنوب",
                                            size=16,
                                            color="#0daca6",
                                            text_align=TextAlign.CENTER,
                                            weight=FontWeight.BOLD,
                                            font_family=BUTTON_FONT,
                                        ),
                                        Container(height=5),
                                        Text(
                                            "رواه مسلم",
                                            size=14,
                                            color=Colors.GREY_600,
                                            text_align=TextAlign.CENTER,
                                            weight=FontWeight.BOLD,
                                            font_family=BUTTON_FONT,
                                        ),
                                    ],
                                    spacing=5,
                                    horizontal_alignment=CrossAxisAlignment.CENTER,
                                ),
                                padding=15,
                                bgcolor=Colors.WHITE,
                                border_radius=10,
                                margin=ft.Margin.only(top=10),
                            ),
                            
                            # زر مشاهدة الفيديو التوضيحي - معدل
                            Container(
                                GestureDetector(
                                    content=Container(
                                        width=350,
                                        height=50,
                                        gradient=LinearGradient(
                                            begin=ft.Alignment(0, 0),
                                            end=ft.Alignment(1, 0),
                                            colors=[Colors.RED_700, Colors.RED_500]
                                        ),
                                        border_radius=10,
                                        shadow=BoxShadow(
                                            spread_radius=0,
                                            blur_radius=10,
                                            color=Colors.with_opacity(0.3, Colors.RED),
                                            offset=Offset(0, 3)
                                        ),
                                        content=Row(
                                            controls=[
                                                Icon(Icons.VIDEO_LIBRARY, color=Colors.WHITE, size=24),
                                                Container(width=8),
                                                Text(
                                                    "مشاهدة الشرح الكامل على YouTube",
                                                    color=Colors.WHITE,
                                                    size=16,
                                                    weight=FontWeight.BOLD,
                                                    font_family=BUTTON_FONT
                                                ),
                                            ],
                                            alignment=MainAxisAlignment.CENTER,
                                            spacing=0
                                        ),
                                        alignment=ft.Alignment(0, 0)
                                    ),
                                    on_tap=open_video
                                ),
                                margin=ft.Margin.only(top=20, bottom=30),
                                alignment=ft.Alignment(0, 0)
                            ),
                            # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
                            Container(height=55),
                        ],
                        scroll=ScrollMode.AUTO,
                        expand=True,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    padding=0,
                    expand=True,
                    bgcolor="#e2e5e7"
                ),
            ],
            padding=0,
            spacing=0,
            bgcolor="#e2e5e7"
        )

class TimedSunanPage:
    @staticmethod
    def create(page):
        timed_data = get_timed_sunan()
        # تعريف الأزرار للسنن الموقوتة مع إضافة data لتخزين محتوى كل سنة
        sunan_buttons = [
            {"icon": CUSTOM_ICONS["1a"], "text": "قبل الفجر", "data": timed_data.get("before_fajr", []), "border_color": "1a"},
            {"icon": CUSTOM_ICONS["2a"], "text": "سنة الفجر", "data": timed_data.get("fajr", []), "border_color": "2a"},
            {"icon": CUSTOM_ICONS["3a"], "text": "الضحى", "data": timed_data.get("duha", []), "border_color": "3a"},
            {"icon": CUSTOM_ICONS["4a"], "text": "الظهر", "data": timed_data.get("dhuhr", []), "border_color": "4a"},
            {"icon": CUSTOM_ICONS["5a"], "text": "العصر", "data": timed_data.get("asr", []), "border_color": "5a"},
            {"icon": CUSTOM_ICONS["6a"], "text": "المغرب", "data": timed_data.get("maghrib", []), "border_color": "6a"},
            {"icon": CUSTOM_ICONS["7a"], "text": "العشاء", "data": timed_data.get("isha", []), "border_color": "7a"},
            {"icon": CUSTOM_ICONS["8a"], "text": "يوم الجمعة", "data": timed_data.get("yawm_aljumuea", []), "border_color": "8a"},
        ]

        # دالة لإنشاء صفحة السنة الموقوتة
        def create_sunan_view(sunan_data, title):
            controls = []
            for item in sunan_data:
                controls.append(
                    Container(
                        content=Column(
                            [
                                Text(
                                    item["text"],
                                    size=current_font_size,
                                    color=Colors.BLACK,
                                    text_align=TextAlign.CENTER,
                                    font_family=FONT_NAME,
                                    weight=FontWeight.BOLD,
                                    style=TextStyle(height=1.7),
                                ),
                                Divider(color=Colors.BLUE, height=10),
                            ],
                            spacing=5,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        ),
                        padding=15,
                        border_radius=10,
                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                        margin=ft.Margin.only(top=10),

                        alignment=ft.Alignment(0, 0),
                    )
                )
            
            # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
            controls.append(Container(height=55))
            
            return View(
                route=f"/{title.lower().replace(' ', '_')}",
                controls=[
                    AppBar(
                        title=Text(title, weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                        bgcolor=APP_BGCOLOR,
                        center_title=True,
                        leading=IconButton(
                            icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD_IOS,
                            icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),  # استخدام الدالة المعدلة
                        ),
                    ),
                    Column(
                        controls,
                        scroll=ScrollMode.AUTO,
                        expand=True,
                        alignment=MainAxisAlignment.START,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                ],
                bgcolor="#e9ecec",
                padding=0,
                spacing=0,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )

        # دالة للتعامل مع الضغط على الأزرار
        def handle_sunan_click(e, sunan_data, title):
            view = create_sunan_view(sunan_data, title)
            page.views.append(view)
            safe_update(page)

        # إنشاء شبكة الأزرار
        sunan_grid = GridView(
            runs_count=3,
            max_extent=110,
            child_aspect_ratio=1,
            spacing=10,
            run_spacing=5,
            controls=[
                Container(
                    width=110,
                    height=110,
                    border_radius=15,
                    bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                    border=ft.Border.all(2, Colors.BLUE_300),
                    alignment=ft.Alignment(0, 0),
                    content=Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        controls=[
                            Image(
                                src=btn["icon"],
                                width=40,
                                height=70,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            Text(
                                btn["text"],
                                size=13,
                                weight=FontWeight.BOLD,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER
                            )
                        ],
                        spacing=-10
                    ),
                    on_click=lambda e, data=btn["data"], title=btn["text"]: handle_sunan_click(e, data, title),
                    ink=True
                ) for btn in sunan_buttons
            ],
            expand=True,
        )

        # إنشاء واجهة الصفحة الرئيسية للسنن
        return View(
            route="/timed_sunan",
            controls=[
                AppBar(
                    title=Text("السنن الموقوتة", weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),
                        ),
                    
                ),
                Container(
                    content=Column(
                        [
                            Text("السنن الموقوتة هي التي تُؤدى في أوقات محددة", 
                                 size=18, 
                                 color="#4a6baf",
                                 weight=FontWeight.BOLD,
                                 font_family=BUTTON_FONT,
                                 text_align=TextAlign.CENTER),
                            sunan_grid
                        ],
                        spacing=20,
                        expand=True,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                    expand=True,
                    bgcolor="#FFFFFF",
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            bgcolor="#FFFFFF",
            padding=0,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )

class UntimedSunanPage:
    @staticmethod
    def create(page):
        untimed_data = get_untimed_sunan()
        # تعريف الأزرار للسنن الغير الموقوتة مع إضافة data لتخزين محتوى كل سنة
        sunan_buttons = [
            {"icon": CUSTOM_ICONS["1aa"], "text": "سنن الوضوء", "data": untimed_data.get("wodu", []), "border_color": "1aa"},
            {"icon": CUSTOM_ICONS["2aa"], "text": "سنن الأذان", "data": untimed_data.get("azaan", []), "border_color": "2aa"},
            {"icon": CUSTOM_ICONS["3aa"], "text": "سنن المسجد", "data": untimed_data.get("mazjed", []), "border_color": "3aa"},
            {"icon": CUSTOM_ICONS["4aa"], "text": "سنن في الصلاة", "data": untimed_data.get("salah", []), "border_color": "4aa"},
            {"icon": CUSTOM_ICONS["5aa"], "text": "سنن الطعام", "data": untimed_data.get("taam", []), "border_color": "5aa"},
            {"icon": CUSTOM_ICONS["6aa"], "text": "سنن السلام ", "data": untimed_data.get("salam", []), "border_color": "6aa"},
            {"icon": CUSTOM_ICONS["7aa"], "text": "سنن اللباس والزينة", "data": untimed_data.get("zeina", []), "border_color": "7aa"},
            {"icon": CUSTOM_ICONS["8aa"], "text": "سنن العطاس", "data": untimed_data.get("alaetas", []), "border_color": "8aa"},
            {"icon": CUSTOM_ICONS["9aa"], "text": "سنن التثاوب", "data": untimed_data.get("tsawob", []), "border_color": "9aa"},
            {"icon": CUSTOM_ICONS["10aa"], "text": "سنن أخرى يومية", "data": untimed_data.get("yawmieya", []), "border_color": "10aa"},
            {"icon": CUSTOM_ICONS["11aa"], "text": "سنن الدعاء", "data": untimed_data.get("duaa", []), "border_color": "11aa"},
            {"icon": CUSTOM_ICONS["12aa"], "text": " سنن ذكر الله", "data": untimed_data.get("ziekr_allh", []), "border_color": "12aa"},
        ]

        # دالة لإنشاء صفحة السنة الغير الموقوتة
        def create_sunan_view(sunan_data, title):
            controls = []
            for item in sunan_data:
                controls.append(
                    Container(
                        content=Column(
                            [
                                Text(
                                    item["text"],
                                    size=current_font_size,
                                    color=Colors.BLACK,
                                    text_align=TextAlign.CENTER,
                                    font_family=FONT_NAME,
                                    weight=FontWeight.BOLD,
                                    style=TextStyle(height=1.7),
                                ),
                                Divider(color=Colors.BLUE, height=10),
                            ],
                            spacing=5,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        ),
                        padding=15,
                        border_radius=10,
                        bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                        margin=ft.Margin.only(top=10),

                        alignment=ft.Alignment(0, 0),
                    )
                )
            
            # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
            controls.append(Container(height=55))
            
            return View(
                route=f"/{title.lower().replace(' ', '_')}",
                controls=[
                    AppBar(
                        title=Text(title, weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                        bgcolor=APP_BGCOLOR,
                        center_title=True,
                        leading=IconButton(
                            icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD_IOS,
                            icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),  # استخدام الدالة المعدلة
                        ),
                    ),
                    Column(
                        controls,
                        scroll=ScrollMode.AUTO,
                        expand=True,
                        alignment=MainAxisAlignment.START,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                ],
                bgcolor="#e9ecec",
                padding=0,
                spacing=0,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )

        # دالة للتعامل مع الضغط على الأزرار
        def handle_sunan_click(e, sunan_data, title):
            view = create_sunan_view(sunan_data, title)
            page.views.append(view)
            safe_update(page)

        # إنشاء شبكة الأزرار
        sunan_grid = GridView(
            runs_count=3,
            max_extent=110,
            child_aspect_ratio=1,
            spacing=10,
            run_spacing=5,
            controls=[
                Container(
                    width=110,
                    height=110,
                    border_radius=15,
                    bgcolor=Colors.with_opacity(0.2, Colors.WHITE),
                    border=ft.Border.all(2, Colors.BLUE_300),
                    alignment=ft.Alignment(0, 0),
                    content=Column(
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        controls=[
                            Image(
                                src=btn["icon"],
                                width=40,
                                height=70,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            Text(
                                btn["text"],
                                size=12,
                                weight=FontWeight.BOLD,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER
                            )
                        ],
                        spacing=-10
                    ),
                    on_click=lambda e, data=btn["data"], title=btn["text"]: handle_sunan_click(e, data, title),
                    ink=True
                ) for btn in sunan_buttons
            ],
            expand=True,
        )
        
        # إنشاء واجهة الصفحة الرئيسية للسنن
        return View(
            route="/untimed_sunan",
            controls=[
                AppBar(
                    title=Text("السنن الغير موقوتة", weight=FontWeight.BOLD, size=20, color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),
                        ),
                    
                ),
                Container(
                    content=Column(
                        [
                            Text("السنن الغير موقوتة هي النوافل التي لا يرتبط وقتها بوقت محدد", 
                                 size=18, 
                                 color="#4a6baf",
                                 weight=FontWeight.BOLD,
                                 font_family=BUTTON_FONT,
                                 text_align=TextAlign.CENTER),
                            sunan_grid
                        ],
                        spacing=20,
                        expand=True,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                    expand=True,
                    bgcolor="#FFFFFF",
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            bgcolor="#FFFFFF",
            padding=0,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )

# دالة لإزالة التشكيل فقط (الحركات والشكل) مع الحفاظ على الحروف العربية
HARAKAT_PATTERN = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7-\u06E8\u06EA-\u06ED]")
def strip_harakat(text: str) -> str:
    return HARAKAT_PATTERN.sub('', text)

# ============ نظام القرآن الكريم من مصدر موثوق (AlQuran.cloud) ============

from functools import lru_cache

class TemplateRoute:
    def __init__(self, route):
        self.route = route
    def match(self, pattern):
        if pattern == self.route: return True
        p_p = pattern.split("/"); r_p = self.route.split("/")
        if len(p_p) != len(r_p): return False
        for p, r in zip(p_p, r_p):
            if p.startswith(":"): setattr(self, p[1:], r)
            elif p != r: return False
        return True

# إعدادات القرآن الكريم
QURAN_API_BASE = "http://api.alquran.cloud/v1"
QURAN_CACHE_FILE = "quran_cache.json"
QURAN_SURAH_LIST_CACHE = "quran_surah_list.json"

class QuranAPI:
    """فئة للتعامل مع API موثوق للقرآن الكريم"""
    
    _instance = None
    _surah_list = []
    _surah_data = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_cache()
        return cls._instance
    
    def _load_cache(self):
        """تحميل البيانات المخزنة مؤقتاً"""
        try:
            # تحميل قائمة السور
            if os.path.exists(QURAN_SURAH_LIST_CACHE):
                with open(QURAN_SURAH_LIST_CACHE, 'r', encoding='utf-8') as f:
                    self._surah_list = json.load(f)
            
            # تحميل بيانات السور المخزنة
            if os.path.exists(QURAN_CACHE_FILE):
                with open(QURAN_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self._surah_data = json.load(f)
        except Exception as e:
            print(f"خطأ في تحميل ذاكرة القرآن: {e}")
            self._surah_list = []
            self._surah_data = {}
    
    def _save_cache(self):
        """حفظ البيانات في التخزين المؤقت"""
        try:
            # حفظ قائمة السور
            with open(QURAN_SURAH_LIST_CACHE, 'w', encoding='utf-8') as f:
                json.dump(self._surah_list, f, ensure_ascii=False, indent=2)
            
            # حفظ بيانات السور
            with open(QURAN_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._surah_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ ذاكرة القرآن: {e}")
    
    def get_surah_list(self, force_refresh=False):
        """
        الحصول على قائمة السور من API أو من الذاكرة المؤقتة
        """
        # إذا كانت القائمة موجودة في الذاكرة المؤقتة ونريد استخدامها
        if self._surah_list and not force_refresh:
            return self._surah_list
        
        try:
            # محاولة جلب القائمة من API (في thread منفصل لمنع blocking)
            def _fetch_surah_list():
                with httpx.Client(timeout=10.0) as client:
                    return client.get(f"{QURAN_API_BASE}/surah")
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_fetch_surah_list)
                try:
                    response = future.result(timeout=12)
                except concurrent.futures.TimeoutError:
                    raise Exception("انتهى وقت الاتصال")
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    # تنسيق البيانات
                    surahs = []
                    for surah in data['data']:
                        surahs.append({
                            'id': surah['number'],
                            'name': surah['name'],
                            'transliteration': surah['englishName'],
                            'type': 'مكية' if surah['revelationType'] == 'Meccan' else 'مدنية',
                            'verses_count': surah['numberOfAyahs'],
                            'verses': []  # سيتم تحميل الآيات عند الطلب
                        })
                    
                    self._surah_list = surahs
                    self._save_cache()
                    return surahs
        except Exception as e:
            print(f"خطأ في جلب قائمة السور: {e}")
        
        # في حالة الفشل، إرجاع القائمة المخزنة
        return self._surah_list
    
    def get_surah(self, surah_number, force_refresh=False):
        """
        الحصول على سورة محددة مع آياتها
        """
        surah_key = str(surah_number)
        
        # إذا كانت السورة مخزنة ولم نطلب تحديث
        if surah_key in self._surah_data and not force_refresh:
            return self._surah_data[surah_key]
        
        try:
            # جلب بيانات السورة من API
            with httpx.Client(timeout=15.0) as client:
                # جلب تفاصيل السورة
                response = client.get(f"{QURAN_API_BASE}/surah/{surah_number}")
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 200:
                        surah_data = data['data']
                        
                        # جلب الآيات (نظام الترقيم العثماني)
                        verses_response = client.get(
                            f"{QURAN_API_BASE}/surah/{surah_number}/editions/quran-uthmani"
                        )
                        
                        verses = []
                        if verses_response.status_code == 200:
                            verses_data = verses_response.json()
                            if verses_data['code'] == 200:
                                for i, verse in enumerate(verses_data['data'][0]['ayahs'], 1):
                                    verses.append({
                                        'id': i,
                                        'text': verse['text']
                                    })
                        
                        # بناء بيانات السورة
                        surah_info = {
                            'id': surah_data['number'],
                            'name': surah_data['name'],
                            'transliteration': surah_data['englishName'],
                            'type': 'مكية' if surah_data['revelationType'] == 'Meccan' else 'مدنية',
                            'verses_count': surah_data['numberOfAyahs'],
                            'verses': verses
                        }
                        
                        # تخزين في الذاكرة المؤقتة
                        self._surah_data[surah_key] = surah_info
                        self._save_cache()
                        
                        return surah_info
        except Exception as e:
            print(f"خطأ في جلب السورة {surah_number}: {e}")
        
        # في حالة الفشل، البحث في القائمة المخزنة
        if surah_key in self._surah_data:
            return self._surah_data[surah_key]
        
        return None
    
    def search_in_quran(self, query, max_results=30):
        """
        البحث في القرآن الكريم
        """
        if not query or len(query) < 2:
            return []
        
        results = []
        
        try:
            # استخدام API للبحث (إذا كان متاحاً)
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{QURAN_API_BASE}/search/{query}/all/ar"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 200:
                        for match in data['data']['matches'][:max_results]:
                            results.append({
                                'text': match['text'],
                                'surah': match['surah']['name'],
                                'surah_number': match['surah']['number'],
                                'ayah': match['numberInSurah']
                            })
        except Exception as e:
            print(f"خطأ في البحث: {e}")
            # البحث المحلي في البيانات المخزنة
            results = self._local_search(query, max_results)
        
        return results
    
    def _local_search(self, query, max_results):
        """بحث محلي في البيانات المخزنة"""
        results = []
        query = query.lower().strip()
        
        for surah_key, surah in self._surah_data.items():
            for verse in surah['verses']:
                if query in verse['text'].lower():
                    results.append({
                        'text': verse['text'][:100] + '...' if len(verse['text']) > 100 else verse['text'],
                        'surah': surah['name'],
                        'surah_number': surah['id'],
                        'ayah': verse['id']
                    })
                    if len(results) >= max_results:
                        return results
        return results

# تهيئة كائن القرآن API عند الحاجة فقط (lazy initialization)
_quran_api_instance = None

def quran_api_get():
    global _quran_api_instance
    if _quran_api_instance is None:
        _quran_api_instance = QuranAPI()
    return _quran_api_instance

# للتوافق مع الكود القديم الذي يستخدم quran_api مباشرة
class _LazyQuranAPI:
    def __getattr__(self, name):
        return getattr(quran_api_get(), name)

quran_api = _LazyQuranAPI()

# ============ صفحة فهرس السور المعدلة ============
class QuranIndexPage:
    @staticmethod
    def create(page):
        # ألوان أكثر إشراقاً وبهجة
        PAGE_BGCOLOR = "#FFFFFF"  # أبيض ناصع
        CARD_BGCOLOR = "#F8FAFC"  # أبيض مائل للرمادي الفاتح جداً
        ACCENT_COLOR = "#2E7D32"  # أخضر غامق أنيق
        GOLD_COLOR = "#B8860B"  # ذهبي فاخر

        # حالة التحميل
        loading_indicator = ProgressRing(width=50, height=50, color=ACCENT_COLOR)
        
        # TextField للبحث
        search_field = TextField(
            hint_text="ابحث عن سورة...",
            border_color=ACCENT_COLOR,
            border_radius=30,
            text_size=16,
            color="#1E293B",
            text_align=TextAlign.RIGHT,
            expand=True,
            filled=True,
            fill_color=CARD_BGCOLOR,
            prefix_icon=Icons.SEARCH,
            on_change=lambda e: update_results(e),
        )

        # Column لعرض النتائج
        results_column = Column(scroll=ScrollMode.AUTO, expand=True)
        
        # نص التحميل
        loading_text = Container(
            alignment=ft.Alignment(0, 0),
            padding=50,
            content=Column(
                controls=[
                    loading_indicator,
                    Container(height=20),
                    Text("جاري تحميل سور القرآن الكريم...", 
                         size=16, 
                         color=Colors.GREY_600,
                         font_family=BUTTON_FONT,
                         text_align=TextAlign.CENTER)
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        
        results_column.controls = [loading_text]

        # وظيفة بناء أزرار السور من API
        async def load_surah_buttons():
            try:
                # جلب قائمة السور من API الموثوق
                surahs = await asyncio.to_thread(quran_api.get_surah_list)
                
                if not surahs:
                    # عرض رسالة خطأ إذا فشل التحميل
                    results_column.controls = [
                        Container(
                            padding=50,
                            alignment=ft.Alignment(0, 0),
                            content=Column(
                                controls=[
                                    Icon(Icons.ERROR_OUTLINE, size=50, color=Colors.RED_400),
                                    Container(height=20),
                                    Text("حدث خطأ في تحميل القرآن الكريم",
                                         size=16,
                                         color=Colors.RED_700,
                                         text_align=TextAlign.CENTER,
                                         font_family=BUTTON_FONT),
                                    Container(height=10),
                                    FilledButton(
                                        "إعادة المحاولة",
                                        on_click=lambda e: load_surah_buttons(),
                                        style=ButtonStyle(
                                            bgcolor=ACCENT_COLOR,
                                            color=Colors.WHITE
                                        )
                                    )
                                ],
                                horizontal_alignment=CrossAxisAlignment.CENTER
                            )
                        )
                    ]
                    safe_update(page)
                    return
                
                # بناء أزرار السور
                buttons = []
                for i, surah in enumerate(surahs):
                    # تأثير تدرج في الألوان
                    bg_color = CARD_BGCOLOR if i % 2 == 0 else Colors.WHITE
                    
                    buttons.append(
                        Container(
                            width=350,
                            height=80,
                            border_radius=15,
                            bgcolor=bg_color,
                            margin=ft.Margin.only(bottom=10),
                            alignment=ft.Alignment(0, 0),
                            shadow=BoxShadow(
                                spread_radius=0,
                                blur_radius=10,
                                color=Colors.with_opacity(0.05, "#000000"),
                                offset=Offset(0, 2)
                            ),
                            on_click=lambda e, num=surah["id"]: page.navigate(f"/quran/surah/{num}"),
                            content=Row(
                                [
                                    # رقم السورة بشكل دائري
                                    Container(
                                        width=45,
                                        height=45,
                                        border_radius=22.5,
                                        bgcolor=Colors.with_opacity(0.1, ACCENT_COLOR),
                                        alignment=ft.Alignment(0, 0),
                                        content=Text(
                                            str(surah["id"]),
                                            size=16,
                                            color=ACCENT_COLOR,
                                            weight=FontWeight.BOLD
                                        )
                                    ),
                                    Container(width=10),
                                    
                                    # معلومات السورة
                                    Container(
                                        expand=True,
                                        content=Column(
                                            controls=[
                                                Row(
                                                    controls=[
                                                        Text(
                                                            f"{surah['name']}",
                                                            size=18,
                                                            color="#1E293B",
                                                            weight=FontWeight.BOLD,
                                                        ),
                                                        Text(
                                                            f"({surah['transliteration']})",
                                                            size=14,
                                                            color="#64748B",
                                                        ),
                                                    ],
                                                    spacing=5,
                                                    alignment=MainAxisAlignment.START
                                                ),
                                                Row(
                                                    controls=[
                                                        Container(
                                                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                            bgcolor=Colors.with_opacity(0.1, GOLD_COLOR),
                                                            border_radius=10,
                                                            content=Text(
                                                                f"{surah['verses_count']} آية",
                                                                size=12,
                                                                color=GOLD_COLOR,
                                                            )
                                                        ),
                                                        Container(width=10),
                                                        Text(
                                                            surah.get("type", "مكية"),
                                                            size=12,
                                                            color="#64748B",
                                                        ),
                                                    ],
                                                    spacing=0,
                                                    alignment=MainAxisAlignment.START
                                                )
                                            ],
                                            spacing=3,
                                            horizontal_alignment=CrossAxisAlignment.START
                                        )
                                    ),
                                    
                                    # أيقونة التنقل
                                    Icon(
                                        Icons.ARROW_FORWARD_IOS,
                                        size=16,
                                        color="#94A3B8"
                                    )
                                ],
                                alignment=MainAxisAlignment.START,
                                vertical_alignment=CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding.symmetric(horizontal=15, vertical=10)
                        )
                    )
                
                results_column.controls = buttons
                
            except Exception as e:
                results_column.controls = [
                    Container(
                        padding=50,
                        content=Text(f"خطأ: {str(e)}", color=Colors.RED)
                    )
                ]
            
            safe_update(page)

        # دالة تحديث النتائج عند البحث
        def update_results(e):
            query = strip_harakat(search_field.value or "").lower().strip()
            
            if not query:
                load_surah_buttons()
                return

            # البحث في السور المحملة
            surahs = quran_api.get_surah_list()
            results = []
            
            for surah in surahs:
                if (query in strip_harakat(surah["name"]).lower() or 
                    query in surah["transliteration"].lower()):
                    results.append(
                        Container(
                            width=350,
                            margin=ft.Margin.only(bottom=12),
                            padding=15,
                            bgcolor=Colors.WHITE,
                            border_radius=15,
                            border=ft.Border.all(2, Colors.with_opacity(0.1, ACCENT_COLOR)),
                            on_click=lambda e, num=surah["id"]: page.navigate(f"/quran/surah/{num}"),
                            content=Row(
                                controls=[
                                    Icon(Icons.BOOK, color=ACCENT_COLOR, size=24),
                                    Container(width=10),
                                    Container(
                                        expand=True,
                                        content=Text(
                                            f"📖 سورة {surah['name']}",
                                            size=16,
                                            color="#1E293B",
                                            weight=FontWeight.BOLD
                                        )
                                    )
                                ]
                            )
                        )
                    )

            if not results:
                results.append(
                    Container(
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                        content=Column(
                            controls=[
                                Icon(Icons.SEARCH_OFF, size=50, color="#94A3B8"),
                                Container(height=10),
                                Text("لا توجد نتائج مطابقة", 
                                     size=16, 
                                     color="#64748B",
                                     text_align=TextAlign.CENTER)
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    )
                )

            results_column.controls = results
            safe_update(page)

        # بدء تحميل السور في الخلفية
        page.run_task(load_surah_buttons)

        return View(
            route="/quran",
            controls=[
                AppBar(
                    title=Text("المصحف الشريف", 
                               size=22, 
                               color="#1E293B", 
                               weight=FontWeight.BOLD),
                    bgcolor=Colors.WHITE,
                    center_title=True,
                    elevation=0,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color="#1E293B",
                        on_click=lambda e: handle_back(page),
                    ),
                ),
                Container(
                    content=Column(
                        [
                            Container(
                                content=search_field,
                                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                            ),
                            Container(
                                content=Text(
                                    "فهرس السور",
                                    size=18,
                                    color=ACCENT_COLOR,
                                    weight=FontWeight.BOLD,
                                    text_align=TextAlign.CENTER
                                ),
                                padding=ft.Padding.only(bottom=10)
                            ),
                            results_column,
                        ],
                        expand=True,
                    ),
                    padding=ft.Padding.symmetric(horizontal=15),
                    expand=True,
                    bgcolor=PAGE_BGCOLOR,
                )
            ],
            bgcolor=PAGE_BGCOLOR,
            padding=0 
        )

# ============ صفحة السورة المعدلة ============
class QuranSurahPage:
    @staticmethod
    def create(page, surah_number):
        # ألوان فاخرة
        PAGE_BGCOLOR = "#FFF9F0"  # كريمي فاتح جداً
        CARD_BGCOLOR = Colors.WHITE
        TEXT_COLOR = "#2C3E50"
        ACCENT_COLOR = "#B8860B"  # ذهبي
        VERSE_NUMBER_COLOR = "#2E7D32"  # أخضر
        
        # حالة التحميل
        loading_indicator = ProgressRing(width=50, height=50, color=ACCENT_COLOR)
        
        # محتوى مؤقت أثناء التحميل
        loading_content = Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=Column(
                controls=[
                    loading_indicator,
                    Container(height=20),
                    Text("جاري تحميل السورة...", 
                         size=16, 
                         color=Colors.GREY_600,
                         font_family=BUTTON_FONT,
                         text_align=TextAlign.CENTER)
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        
        # حاوية السورة (ستمتلئ بعد التحميل)
        surah_container = Container(
            content=loading_content,
            padding=ft.Padding.symmetric(horizontal=25, vertical=30),
            bgcolor=CARD_BGCOLOR,
            border_radius=20,
            shadow=BoxShadow(
                spread_radius=0,
                blur_radius=30,
                color=Colors.with_opacity(0.1, "#000000"),
                offset=Offset(0, 5)
            ),
            margin=ft.Margin.only(bottom=20)
        )
        
        # اسم السورة المؤقت
        surah_title = "جاري التحميل..."
        surah_subtitle = ""

        async def load_surah_content():
            nonlocal surah_title, surah_subtitle, surah_container
            
            try:
                # جلب بيانات السورة من API الموثوق
                surah = await asyncio.to_thread(quran_api.get_surah, surah_number)
                
                if not surah:
                    # عرض رسالة خطأ
                    surah_container.content = Container(
                        padding=50,
                        alignment=ft.Alignment(0, 0),
                        content=Column(
                            controls=[
                                Icon(Icons.ERROR_OUTLINE, size=50, color=Colors.RED_400),
                                Container(height=20),
                                Text("حدث خطأ في تحميل السورة",
                                     size=16,
                                     color=Colors.RED_700,
                                     text_align=TextAlign.CENTER,
                                     font_family=BUTTON_FONT),
                                Container(height=10),
                                FilledButton(
                                    "إعادة المحاولة",
                                    on_click=lambda e: page.navigate(f"/quran/surah/{surah_number}"),
                                    style=ButtonStyle(
                                        bgcolor=ACCENT_COLOR,
                                        color=Colors.WHITE
                                    )
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    )
                    safe_update(page)
                    return
                
                # تحديث عنوان السورة
                surah_title = surah['name']
                surah_subtitle = surah['transliteration']
                
                # أيقونة السورة
                surah_icon = "" if surah.get("type", "مكية") == "مكية" else ""
                
                # أنماط النصوص
                ayah_style = TextStyle(
                    size=current_font_size + 2,
                    color=TEXT_COLOR,
                    font_family=FONT_QURAN,
                    weight=FontWeight.NORMAL,
                    height=2.8,
                )
                
                ayah_number_style = TextStyle(
                    size=current_font_size,
                    color=VERSE_NUMBER_COLOR,
                    font_family=FONT_QURAN,
                    weight=FontWeight.BOLD,
                    height=2.0,
                )
                
                basmala_style = TextStyle(
                    size=current_font_size + 8,
                    color=ACCENT_COLOR,
                    weight=FontWeight.BOLD,
                    font_family=FONT_QURAN,
                    height=3.9,
                )
                
                # بناء النص
                spans = []
                

                
                # الآيات مع فواصل جميلة
                for i, verse in enumerate(surah["verses"]):
                    ayah_text = verse["text"].strip()
                    
                    spans.append(TextSpan(
                        text=ayah_text,
                        style=ayah_style
                    ))
                    
                    # فاصل جميل للآيات
                    if i < len(surah["verses"]) - 1:
                        spans.append(TextSpan(
                            text=" ﴿" + str(verse["id"]) + "﴾ ",
                            style=ayah_number_style
                        ))
                    else:
                        spans.append(TextSpan(
                            text=" ﴿" + str(verse["id"]) + "﴾ ",
                            style=ayah_number_style
                        ))
                
                # النص الكامل
                full_surah_text = Text(
                    spans=spans,
                    text_align=TextAlign.CENTER,
                    selectable=True,
                )
                
                # تحديث محتوى السورة
                surah_container.content = Column(
                    controls=[
                        full_surah_text,
                        Container(height=30),
                        Container(
                            padding=15,
                            bgcolor=Colors.with_opacity(0.05, ACCENT_COLOR),
                            border_radius=12,
                            content=Text(
                                "صدق الله العظيم",
                                size=18,
                                color=ACCENT_COLOR,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            )
                        )
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
                
            except Exception as e:
                surah_container.content = Container(
                    padding=50,
                    content=Text(f"خطأ في التحميل: {str(e)}", color=Colors.RED)
                )
            
            # تحديث عنوان الصفحة
            for control in page.views[-1].controls:
                if isinstance(control, AppBar):
                    if isinstance(control.title, Column):
                        control.title.controls[0].value = f"{surah_icon} {surah_title}"
                        control.title.controls[1].value = surah_subtitle
                    break
            
            safe_update(page)

        # بدء تحميل السورة في الخلفية
        page.run_task(load_surah_content)

        return View(
            route=f"/quran/surah/{surah_number}",
            controls=[
                AppBar(
                    title=Column(
                        controls=[
                            Text(
                                surah_title,
                                size=20,
                                weight=FontWeight.BOLD,
                                color=TEXT_COLOR,
                                font_family=BUTTON_FONT
                            ),
                            Text(
                                surah_subtitle,
                                size=14,
                                color="#64748B",
                                font_family=BUTTON_FONT
                            )
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=2
                    ),
                    bgcolor=Colors.WHITE,
                    center_title=True,
                    elevation=0,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color=TEXT_COLOR,
                        on_click=lambda _: handle_back(page),
                    ),
                ),
                Container(
                    content=Column(
                        controls=[
                            surah_container,
                        ],
                        scroll=ScrollMode.AUTO,
                        expand=True,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ),
                    padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                    expand=True,
                    bgcolor=PAGE_BGCOLOR,
                )
            ],
            bgcolor=PAGE_BGCOLOR,
            padding=0,
            spacing=0,
        )
    

class youmgPage:
    @staticmethod
    def create(page: Page):
        # خطوات الوضوء مع الصور التوضيحية
        wudu_steps = [
            {
                "title": "الاستيقاظ وبداية اليوم.",
                "description": "يبدأ النبي محمد صلى الله عليه وسلم يومه بالاستيقاظ في وقت مبكر قبل صلاة الفجر.\nيبدأ بروتين يومي مليء بالروحانية والتواصل مع الله.\nيستفتح يومه بالدعاء والتسبيح، مؤكدًا على أهمية البداية الصحيحة ليوم مليء بالبركة والتوفيق.\nكما يتبع ذلك الوضوء، الذي يعكس النظافة الجسدية والروحية.\nويعد الصلاة الفجر أولى خطوات التواصل مع الله في اليوم.",

            },
            {
                "title": "الصلاة والعبادة.",
                "description": "تُعتبر الصلاة الركن الأساسي في حياة النبي صلى الله عليه وسلم.\nبعد صلاة الفجر، يجلس النبي صلى الله عليه وسلم مع أصحابه ليعلمهم أمور الدين والدنيا.\nيخصص أوقاتًا محددة لكل صلاة خلال اليوم، ويحرص على أدائها في وقتها، مؤكداً بذلك على أهمية النظام والالتزام في حياة المسلم.\nبين الصلوات، يقوم النبي صلى الله عليه وسلم بتلاوة القرآن، والدعاء، وذكر الله.\nمما يعكس مدى التعلق والارتباط بالله في حياته اليومية.",
            },
            {
                "title": "التعامل مع الأهل والأصحاب.",
                "description": "كان النبي صلى الله عليه وسلم مثالاً في حسن التعامل مع أهله وأصحابه.\nيحرص على إدخال السرور إلى قلوبهم، والاستماع إلى مشكلاتهم، ومساعدتهم في حلها.\nكان يتعامل برفق ولين مع زوجاته، ويقدم النصح والتوجيه لأبنائه وأصحابه.\nيعكس هذا الجانب الإنساني في حياته قدرة عالية على التوازن بين دوره كنبي ودوره كزوج وأب وصديق.",
            },
            {
                "title": "العمل والدعوة.",
                "description": "يخصص النبي صلى الله عليه وسلم جزءًا كبيرًا من يومه للدعوة إلى الإسلام.\nيلتقي بالناس، يشرح لهم تعاليم الدين، ويرد على استفساراتهم.\nكما كان يقوم بالأعمال اليومية التي تساعد في توفير لقمة العيش، مثل التجارة والزراعة.\nيبرز هنا نموذجًا في الاجتهاد والعمل الجاد، مع الحفاظ على الهدف الأسمى وهو نشر رسالة الإسلام.",
            },
            {
                "title": "الراحة والاستجمام.",
                "description": "رغم انشغالاته العديدة، كان النبي صلى الله عليه وسلم يحرص على تخصيص وقت للراحة والاستجمام.\nيستغل هذا الوقت للترويح عن نفسه وعن أصحابه، سواء من خلال الجلسات العائلية أو التحدث مع أصحابه في أمور الحياة العامة.\nكان يدعو إلى الاعتدال في كل شيء، بما في ذلك الترفيه والراحة.\nليكون بذلك قدوة في تنظيم الوقت والاستفادة منه بأفضل صورة.",
            },
            {
                "title": "النوم وختام اليوم.",
                "description": "يختم النبي صلى الله عليه وسلم يومه بالاستعداد للنوم، الذي يعتبر راحة للجسد والروح.\nيقرأ بعض الأدعية والأذكار التي تحفظه من كل سوء، ويقوم بتنظيف جسده مرة أخرى بالوضوء.\nمما يعكس أهمية النظافة في حياة المسلم.\nكما يختم يومه بالتفكر في أحداث اليوم، والاستغفار عن أي تقصير.\nمؤكدًا بذلك على أهمية المراجعة الذاتية المستمرة.",
            }
        ]

        # إنشاء قائمة بالخطوات مع الصور
        step_widgets = []
        for step in wudu_steps:
            step_widgets.append(
                Container(
                    content=Column(
                        controls=[

                            # عنوان الخطوة
                            Text(
                                step["title"],
                                size=18,
                                color="#0daca6",
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                               
                            ),
                            
                            # وصف الخطوة
                            Text(
                                step["description"],
                                size=19,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                style=TextStyle(height=1.7),
                            ),
                            
                            Divider(color=Colors.BLUE, height=10),
                        ],
                        spacing=5,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                    border_radius=15,

                )
            )

        return View(
            route="/youm",
            controls=[
                AppBar(
                    title=Text("يوم في حياة النبي ﷺ", weight=FontWeight.BOLD, size=17, color=Colors.WHITE, text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                            icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),
                        ),                    
                ),
                Column(
                    controls=[
                        Container(

                        ),
                        
                        *step_widgets,
                        # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
                        Container(height=55),
                    ],
                    scroll=ScrollMode.AUTO,
                    expand=True,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=15,
                )
            ],
            padding=0,
            spacing=0,
            bgcolor="#e7eaec"
        )

class fadlPage:
    @staticmethod
    def create(page: Page):
        # خطوات الوضوء مع الصور التوضيحية

        # إنشاء قائمة بالخطوات مع الصور
        step_widgets = []
        for step in get_wudu_steps():
            step_widgets.append(
                Container(
                    content=Column(
                        [

                            # عنوان الخطوة
                            Text(
                                step["title"],
                                size=18,
                                color="#0daca6",
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                                
                               
                            ),
                            
                            # وصف الخطوة
                            Text(
                                step["description"],
                                size=19,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                style=TextStyle(height=1.7),
                            ),
                            
                            Divider(color=Colors.BLUE, height=10),
                        ],
                        spacing=5,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                    border_radius=15,

                )
            )

        return View(
            route="/fadl",
            controls=[
                AppBar(
                    title=Text("فضائل السور", weight=FontWeight.BOLD, size=17, color=Colors.WHITE, text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                            icon_color=Colors.WHITE,
                            on_click=lambda e: handle_back(page),
                        ),                    
                ),
                Column(
                    controls=[
                        Container(

                        ),
                        
                        *step_widgets,
                        # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
                        Container(height=55),
                    ],
                    scroll=ScrollMode.AUTO,
                    expand=True,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=15,
                )
            ],
            padding=0,
            spacing=0,
            bgcolor="#e7eaec"
        )
    

class hajjPage:
    @staticmethod
    def create(page: Page):
        # خطوات الوضوء مع الصور التوضيحية

        wudu_steps = [
            {
                "title": "قد ربط الله تعالى بين الحج والذكر فجعله من أهم مقاصد الركن الخامس من أركان الدين.\n",
                "description":" قال تعالى :وَاذْكُرُوا اللَّهَ فِي أَيَّامٍ مَعْدُودَاتٍ .\n [سورة البقرة - الآية 203]\nوقال تعالى :وَأَذِّنْ فِي النَّاسِ بِالْحَجِّ يَأْتُوكَ رِجَالاً وَعَلَى كُلِّ ضَامِرٍ يَأْتِينَ مِنْ كُلِّ فَجٍّ عَمِيقٍ ﴿27﴾ لِيَشْهَدُوا مَنَافِعَ لَهُمْ وَيَذْكُرُوا اسْمَ اللَّهِ فِي أَيَّامٍ مَعْلُومَاتٍ عَلَى مَا رَزَقَهُمْ مِنْ بَهِيمَةِ الْأَنْعَامِ.\n [سورة الحج - الآية 28]\nفجعل من أهم مقاصد الحج أن يقوم العبد بذكر الله وشكره.\nوأكد النبي صلى الله عليه وسلم ارتباط الحج بذكر الله فقال صلى الله عليه وسلم:\nإِنَّمَا جُعِلَ الطَّوَافُ بِالْبَيْتِ وَبَيْنَ الصَّفَا وَالْمَرْوَةِ وَرَمْيُ الْجِمَارِ لِإِقَامَةِ ذِكْرِ اللَّهِ.\n [رواه أبو داود والترمذي]\nوهكذا يتجلى شأن الذكر في الحج، ويستبين عظم منزلته ورفيع مكانته.\n وفيما يلي الأدعية النبوية والأذكار الواردة في محطات الحج ومواقيته الزمانية والمكانية والعمرة والزيارة فاحفظها ليكون حجك مبرورا وسعيك مشكورا."
            },

            {
                "title": "الذكر عند الاحرام\n",
                "description": "سُبْحَانَ اللهِ وَالحَمْدُ للهِ وَالله أَكْبَرُ",
            },

            {
                "title": "دعاء التلبية في الحج والعمرة\n",
                "description": "لَبَّيْكَ اللَّهُمَّ لَبَّيْك، لَبّيْك لا شَرِيكَ لك لَبَّيْك إنَّ الحَمْدَ، والنِّعْمَةَ، لَكَ والمُلْك، لا شريك لك.  [البخاري (2/ 170)، ومسلم (1184)]",
            },

            {
                "title": "الدعاء عند رؤية الكعبة\n",
                "description": "اللهُمَّ أَنْتَ السَّلَامُ وَمِنْكَ السَّلَامُ، فَحَيِّنَا رَبَّنَا بِالسَّلَامِ. [أبي شيبة 7/ 102، والبيهقي 5/ 73]",
            },

            {
                "title": "الدعاء عند استلام الحجر الأسود\n",
                "description": "بِاسْمِ اللهِ وَاللهُ أَكْبَرُ.\n [الطبراني (862)، (863)، والبيهقي (5/ 79)]\nلَا إِلَهَ إِلَّا اللَّهُ وَاللَّهُ أَكْبَرُ، اللَّهُمَّ تَصْدِيقًا بِكِتَابِكَ، وَسُنَّةِ نَبِيِّكَ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ.\n [الطبراني (865)]",
            },

            {
                "title": "الدُّعاءُ بينَ الرُّكن اليماني والحجر الأسود\n",
                "description": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً، وَفِي الْآخِرَةِ حَسَنَةً، وَقِنَا عَذَابَ النَّارِ.\n [أبو داود 2/179 وأحمد 3/411]",
            },

            {
                "title": "الدعاء في الطواف\n",
                "description": "اللهُمَّ رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ.\n [الطبراني (857)، والبيهقي (5/ 84)]\nلَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ، لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، بِيَدِهِ الْخَيْرُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.",
            },

            {
                "title": "الدعاء بعد ركعتي الطواف\n",
                "description": "اللَّهُمَّ اعْصِمْنِي بِدِينِكَ، وَطَاعَةِ رَسُولِكَ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ.\nاللَّهُمَّ جَنِّبْنِي حُدُودَكَ.\nاللَّهُمَّ اجْعَلْنِي مِمَّنْ يُحِبُّكَ، وَيُحِبُّ مَلَائِكَتَكَ، وَرُسُلَكَ، وَعِبَادَكَ الصَّالِحِينَ.\n اللَّهُمَّ حَبِّبْنِي إِلَيْكَ، وَإِلَى مَلَائِكَتِكَ، وَرُسُلِكَ، وَعِبَادَكَ الصَّالِحِينَ.\nاللَّهُمَّ آتِنِي مِنْ خَيْرِ مَا تُؤْتِي عِبَادَكَ الصَّالِحِينَ فِي الدُّنْيَا وَالْآخِرَةِ.\nاللَّهُمَّ يَسِّرْنِي لِلْيُسْرَى، وَجَنِّبْنِي الْعُسْرَى، وَاغْفِرْ.",
            },

            {
                "title": "الدعاء عند صعود الصَّفَا والمروة\n",
                "description": "عَنْ جَابِرِ بْنِ عَبْدِ اللَّهِ رضي الله عنه، قَالَ: سَمِعْتُ رَسُولَ اللَّهِ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ حِينَ خَرَجَ مِنَ الْمَسْجِدِ يُرِيدُ الصَّفَا، يَقُولُ: نَبْدَأُ بِمَا بَدَأَ بِهِ.\n فَبَدأَ بِالصَّفَا، وَقَرَأَ: {إِنَّ الصَّفَا وَالمَرْوَةَ مِنْ شَعَائِرِ اللَّهِ} وَكَانَ إِذَا وَقَفَ عَلَى الصَّفَا يُكَبِّرُ ثَلاثًا، وَيَقُولُ:\nلَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، لَا إِلَهَ إِلَّا اللهُ، أَنْجَزَ وَعْدَهُ، وَنَصَرَ عَبْدَهُ، وَهَزَمَ الْأَحْزَابَ وَحْدَهُ.\nثُمَّ أعاد هذا الكلام.\n [مسلم (1218)، وأحمد (3/ 320، 321)]",
            },

            {
                "title": "الدعاء على الصفا\n",
                "description": "اللَّهُمَّ إِنَّكَ قُلْتَ: {اِدْعُونِي أَسْتَجِبْ لَكُمْ} وَإِنَّكَ لاَ تُخْلِفُ الْمِيعَادَ، وَإِنِّي أَسْأَلُكَ كَمَا هَدَيْتَنِي إِلَى الإِسْلاَمِ أَلاَ تَنْزِعَهُ مِنِّي حَتَّى تَتَوَفَّانِي، وَأَنَا مُسْلِمٌ.\nاللَّهُمَّ اعْصِمْنَا بِدِينِكَ، وَطَوَاعِيَتِكَ، وَطَوَاعِيَةِ رَسُولِكَ، وَجَنِّبْنَا حُدُودَكَ.\nاللَّهُمَّ اجْعَلْنَا نُحِبُّكَ، وَنُحِبُّ مَلَائِكَتَكَ، وَأَنْبِيَاءَكَ، وَرُسُلَكَ، وَنُحِبُّ عِبَادَكَ الصَّالِحِينَ.\nاللَّهُمَّ حَبِّبْنَا إِلَيْكَ وَإِلَى مَلَائِكَتِكَ، وَإِلَى أَنْبِيَائِكَ، وَرُسُلِكَ، وَإِلَى عِبَادِكَ الصَّالِحِينَ.\nاللَّهُمَّ يَسِّرْنَا لِلْيُسْرَى، وَجَنِّبْنَا وَجَنِّبْنَا الْعُسْرَى، وَاغْفِرْ لَنَا فِي الْآخِرَةِ.\n [البيهقي (5/ 94)]",
            },

            {
                "title": "الدعاء في السعي بين الصفا والمروة\n",
                "description": "رَبِّ اغْفِرْ وَارْحَمْ إِنَّكَ أَنْتَ الْأَعَزُّ الْأَكْرَمُ.\n [الطبراني (870)، والبيهقي (5/ 95)]",
            },

            {
                "title": "الدعاء بعرفات\n",
                "description": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.\n [الترمذي (3579)، والطبراني (784)]",
            },

            {
                "title": "دعاء السلف الصالح في عرفات\n",
                "description": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.\nاللَّهُمَّ اهْدِنَا بِالْهُدَى، وَزَيِّنَّا بِالتَّقْوَى، وَاغْفِرْ لَنَا فِي الْآخِرَةِ وَالْأُولَى.\nثُمَّ يَخْفِضُ صَوْتَهُ، ثُمَّ يَقُولُ: اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ وَعَطَائِكَ رِزْقًا طَيِّبًا مُبَارَكًا.\nاللَّهُمَّ إِنَّكَ أَمَرْتَ بِالدُّعَاءِ، وَقَضَيْتَ عَلَى نَفْسِكَ بِالِاسْتِجَابَةِ، وَأَنْتَ لَا تُخْلِفُ وَعْدَكَ، وَلَا تَكْذِبُ عَهْدَكَ، اللَّهُمَّ مَا أَحْبَبْتَ مِنْ خَيْرٍ فَحَبِّبْهُ إِلَيْنَا، وَيَسِّرْهُ لَنَا، وَمَا كَرِهْتَ مِنْ شَيْءٍ فَكَرِّهْهُ إِلَيْنَا وَجَنِّبْنَاهُ، وَلَا تَنْزِعْ عَنَّا الْإِسْلَامَ بَعْدَ إِذْ أَعْطَيْتَنَا.",
            },

            {
                "title": "الدعاء عند رمي جمرة العقبة عِنْدَ كُلِّ حَصَاة\n",
                "description": "الله أَكْبَر، الله أَكْبَر، الله أَكْبَر.\nاللَّهُمَّ اجْعَلْهُ حَجًّا مَبْرُورًا وَذَنْبًا مَغْفُورًا.\n [الطبراني (881)، والبيهقي (5/ 129)]",
            },

            {
                "title": "الذكر عند ذبح الأضاحي\n",
                "description": "بسم الله , اللهم تقبل من محمد وآل محمد ومن أمة محمد",
            },

            {
                "title": "دعاء الرجوع من الحج أو العمرة\n",
                "description": "الله أَكْبَر، الله أَكْبَر، الله أَكْبَر.\nلَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ، وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، آيِبُونَ، تَائِبُونَ، عَابِدُونَ، سَاجِدُونَ.\nاَللّٰهُمَّ اجْعَلْهُ حَجًّا مَبْرُوْرًا وَسَعْيًا مَشْكُوْرًا وَذَنْبًا مَغْفُوْرًا.",
            },

        ]

        # إنشاء قائمة بالخطوات مع الصور
        # إنشاء قائمة بالخطوات
        step_widgets = []
        for step in wudu_steps:
            step_widgets.append(
                Container(
                    content=Column(
                        [
                            # عنوان الخطوة
                            Text(
                                step["title"],
                                size=18,
                                color="#0daca6",
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER,
                            ),
                            
                            # وصف الخطوة
                            Text(
                                step["description"],
                                size=19,
                                color=Colors.BLACK,
                                text_align=TextAlign.CENTER,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                style=TextStyle(height=1.7),
                            ),
                            
                            Divider(color=Colors.BLUE, height=10),
                        ],
                        spacing=5,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    bgcolor=Colors.with_opacity(0.8, Colors.WHITE),
                    border_radius=15,
                )
            )

        return View(
            route="/hajj",
            controls=[
                AppBar(
                    title=Text("أذكار الحج والعمرة", 
                              weight=FontWeight.BOLD, 
                              size=17, 
                              color=Colors.WHITE, 
                              text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(page),
                    ),                    
                ),
                Column(
                    controls=[
                        Container(),
                        *step_widgets,
                        # 🔹 إضافة مسافة فارغة في الأسفل لتوفير مساحة قبل البانر
                        Container(height=55),
                    ],
                    scroll=ScrollMode.AUTO,
                    expand=True,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=15,
                )
            ],
            padding=0,
            spacing=0,
            bgcolor="#e7eaec"
        )

# ============ صفحة التقويم الهجري والميلادي الشاملة ============
class CalendarPage:
    def __init__(self, page: Page):
        self.page = page
        self.timer = None
        self.location = None
        self.current_date = datetime.now()
        self.cache_dir = "cache"  # مجلد للتخزين المؤقت
        self.setup_cache()
        
    def setup_cache(self):
        """إعداد مجلد التخزين المؤقت"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def save_to_cache(self, key, data, expiry_hours=24):
        """حفظ البيانات في التخزين المؤقت"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
            cache_data = {
                'data': data,
                'expiry': datetime.now() + timedelta(hours=expiry_hours),
                'created': datetime.now()
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            return True
        except Exception as e:
            print(f"خطأ في حفظ البيانات المؤقتة: {e}")
            return False
    
    def load_from_cache(self, key):
        """تحميل البيانات من التخزين المؤقت"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # التحقق من انتهاء الصلاحية
                if datetime.now() < cache_data['expiry']:
                    return cache_data['data']
                else:
                    # حذف الملف المنتهي الصلاحية
                    os.remove(cache_file)
            return None
        except Exception as e:
            print(f"خطأ في تحميل البيانات المؤقتة: {e}")
            return None
    
    def save_location_to_file(self, location):
        """حفظ بيانات الموقع في ملف"""
        try:
            location_file = os.path.join(self.cache_dir, "location.json")
            with open(location_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'location': location,
                    'saved_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"خطأ في حفظ بيانات الموقع: {e}")
            return False
    
    def load_location_from_file(self):
        """تحميل بيانات الموقع من ملف"""
        try:
            location_file = os.path.join(self.cache_dir, "location.json")
            if os.path.exists(location_file):
                with open(location_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # التحقق من أن البيانات ليست قديمة جداً (أسبوع)
                saved_at = datetime.fromisoformat(data['saved_at'])
                if datetime.now() - saved_at < timedelta(days=7):
                    return data['location']
            return None
        except Exception as e:
            print(f"خطأ في تحميل بيانات الموقع: {e}")
            return None
    
    def save_prayer_times_to_file(self, date_str, location, prayer_data):
        """حفظ مواقيت الصلاة في ملف"""
        try:
            # إنشاء مفتاح فريد للتاريخ والموقع
            location_key = f"{location['latitude']:.4f}_{location['longitude']:.4f}"
            prayer_file = os.path.join(self.cache_dir, f"prayer_{location_key}_{date_str}.json")
            
            data_to_save = {
                'prayer_data': prayer_data,
                'location': location,
                'date': date_str,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(prayer_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"خطأ في حفظ مواقيت الصلاة: {e}")
            return False
    
    def load_prayer_times_from_file(self, date_str, location):
        """تحميل مواقيت الصلاة من ملف"""
        try:
            location_key = f"{location['latitude']:.4f}_{location['longitude']:.4f}"
            prayer_file = os.path.join(self.cache_dir, f"prayer_{location_key}_{date_str}.json")
            
            if os.path.exists(prayer_file):
                with open(prayer_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # التحقق من أن البيانات ليست قديمة جداً (يومين)
                saved_at = datetime.fromisoformat(data['saved_at'])
                if datetime.now() - saved_at < timedelta(days=2):
                    return data['prayer_data']
            return None
        except Exception as e:
            print(f"خطأ في تحميل مواقيت الصلاة: {e}")
            return None
    
    @staticmethod
    def create(page: Page):
        calendar_page = CalendarPage(page)
        return calendar_page.create_view()
    
    def get_user_location(self):
        """الحصول على موقع المستخدم الحقيقي"""
        # محاولة تحميل الموقع المحفوظ أولاً
        cached_location = self.load_location_from_file()
        if cached_location:
            cached_location['method'] = 'محفوظ'
            return cached_location
        
        try:
            # استخدام httpx (موجود بالفعل) بدلاً من requests/geocoder
            with httpx.Client(timeout=5.0) as client:
                # الطريقة 1: خدمة IPInfo
                try:
                    response = client.get('https://ipinfo.io/json')
                    if response.status_code == 200:
                        data = response.json()
                        loc = data.get('loc', '').split(',')
                        if len(loc) == 2:
                            location_data = {
                                'latitude': float(loc[0]),
                                'longitude': float(loc[1]),
                                'city': data.get('city', ''),
                                'country': data.get('country', ''),
                                'method': 'IP'
                            }
                            self.save_location_to_file(location_data)
                            return location_data
                except:
                    pass

                # الطريقة 2: خدمة ip-api بديلة
                try:
                    response = client.get('http://ip-api.com/json/?fields=lat,lon,city,country')
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('lat'):
                            location_data = {
                                'latitude': data['lat'],
                                'longitude': data['lon'],
                                'city': data.get('city', ''),
                                'country': data.get('country', ''),
                                'method': 'IP'
                            }
                            self.save_location_to_file(location_data)
                            return location_data
                except:
                    pass

        except Exception as e:
            print(f"خطأ في تحديد الموقع: {e}")
        
        # القيم الافتراضية (الرياض)
        default_location = {
            'latitude': 24.7136,
            'longitude': 46.6753,
            'city': 'الرياض',
            'country': 'السعودية',
            'method': 'افتراضي'
        }
        # حفظ الموقع الافتراضي
        self.save_location_to_file(default_location)
        return default_location
    
    def format_12h_time(self, time_str):
        """تحويل الوقت من 24 ساعة إلى 12 ساعة بالعربية"""
        try:
            if ':' in time_str:
                hours, minutes = map(int, time_str.split(':'))
                period = "ص" if hours < 12 else "م"
                hours_12 = hours % 12
                if hours_12 == 0:
                    hours_12 = 12
                return f"{hours_12:02d}:{minutes:02d} {period}"
            return time_str
        except:
            return time_str
    
    def get_prayer_times_for_date(self, date_obj, location=None):
        """الحصول على مواقيت الصلاة حسب الموقع الفعلي"""
        # الحصول على الموقع إذا لم يكن محدداً
        if location is None:
            if self.location is None:
                self.location = self.get_user_location()
            location = self.location
        
        # تحويل التاريخ إلى الصيغة المطلوبة
        date_str = date_obj.strftime("%d-%m-%Y")
        
        # محاولة تحميل مواقيت الصلاة المحفوظة
        cached_prayer_times = self.load_prayer_times_from_file(date_str, location)
        if cached_prayer_times:
            cached_prayer_times['source'] = 'محفوظ'
            return cached_prayer_times
        
        try:
            # استخدام httpx (موجود بالفعل) بدلاً من requests
            params = {
                "latitude": location['latitude'],
                "longitude": location['longitude'],
                "method": 5,  # طريقة حساب هيئة المساحة المصرية
                "tune": "0,0,0,0,0,0,0,0,0"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"http://api.aladhan.com/v1/timings/{date_str}",
                    params=params
                )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    timings = data['data']['timings']
                    
                    # تنسيق الأوقات بنظام 12 ساعة
                    formatted_timings = {}
                    for prayer, time in timings.items():
                        formatted_timings[prayer] = self.format_12h_time(time)
                    
                    prayer_data = {
                        'timings': formatted_timings,
                        'location': location,
                        'date': date_str,
                        'source': 'API'
                    }
                    
                    # حفظ مواقيت الصلاة
                    self.save_prayer_times_to_file(date_str, location, prayer_data)
                    return prayer_data
                    
        except httpx.RequestError as e:
            print(f"خطأ في الاتصال بالإنترنت: {e}")
            # محاولة استخدام بيانات قديمة لشهر مماثل
            return self.get_fallback_prayer_times(date_obj, location)
        except Exception as e:
            print(f"خطأ في جلب مواقيت الصلاة: {e}")
        
        # في حالة الفشل، إرجاع أوقات افتراضية حسب الموقع
        return self.get_default_prayer_times(location)
    
    def get_fallback_prayer_times(self, date_obj, location):
        """الحصول على مواقيت صلاة بديلة من البيانات القديمة"""
        # محاولة العثور على بيانات لشهر مماثل في السنوات السابقة
        current_month = date_obj.month
        current_day = date_obj.day
        
        # البحث عن أي بيانات محفوظة لنفس الشهر
        location_key = f"{location['latitude']:.4f}_{location['longitude']:.4f}"
        cache_pattern = f"prayer_{location_key}_*.json"
        
        try:
            import glob
            prayer_files = glob.glob(os.path.join(self.cache_dir, cache_pattern))
            
            if prayer_files:
                # استخدام أحدث ملف
                latest_file = max(prayer_files, key=os.path.getmtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # تعديل البيانات لتناسب التاريخ الحالي
                prayer_data = data['prayer_data']
                prayer_data['source'] = 'بديل (بدون إنترنت)'
                prayer_data['date'] = date_obj.strftime("%d-%m-%Y")
                
                return prayer_data
        except:
            pass
        
        # إذا لم توجد بيانات بديلة، استخدم الافتراضية
        return self.get_default_prayer_times(location)
    
    def get_default_prayer_times(self, location):
        """الحصول على أوقات صلاة افتراضية حسب خط العرض"""
        latitude = location['latitude']
        
        # ضبط الأوقات الافتراضية حسب الموقع
        if latitude > 30:  # مناطق شمالية
            return {
                'timings': {
                    "Fajr": "05:30 ص",
                    "Sunrise": "06:30 ص",
                    "Dhuhr": "12:45 م",
                    "Asr": "04:00 م",
                    "Maghrib": "06:30 م",
                    "Isha": "08:00 م"
                },
                'location': location,
                'source': 'افتراضي شمالي'
            }
        elif latitude < 15:  # مناطق استوائية
            return {
                'timings': {
                    "Fajr": "05:00 ص",
                    "Sunrise": "06:00 ص",
                    "Dhuhr": "12:15 م",
                    "Asr": "03:30 م",
                    "Maghrib": "06:00 م",
                    "Isha": "07:30 م"
                },
                'location': location,
                'source': 'افتراضي استوائي'
            }
        else:  # مناطق معتدلة
            return {
                'timings': {
                    "Fajr": "05:15 ص",
                    "Sunrise": "06:15 ص",
                    "Dhuhr": "12:30 م",
                    "Asr": "03:45 م",
                    "Maghrib": "06:15 م",
                    "Isha": "07:45 م"
                },
                'location': location,
                'source': 'افتراضي معتدل'
            }
    
    def navigate_month(self, direction):
        """التنقل بين الشهور"""
        if direction == "next":
            # الانتقال إلى الشهر التالي
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        elif direction == "prev":
            # الانتقال إلى الشهر السابق
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        elif direction == "today":
            # العودة إلى الشهر الحالي
            self.current_date = datetime.now()
        
        # حفظ حالة الشهر الحالي في التخزين المؤقت
        self.save_to_cache('last_month_view', {
            'year': self.current_date.year,
            'month': self.current_date.month,
            'date': self.current_date.isoformat()
        }, expiry_hours=720)  # 30 يوم
        
        # إعادة إنشاء الصفحة مع الشهر الجديد
        self.page.views.pop()
        self.page.views.append(self.create_view())
        safe_update(self.page)
    
    def load_last_month_view(self):
        """تحميل آخر شهر تم عرضه"""
        cached = self.load_from_cache('last_month_view')
        if cached:
            try:
                last_date = datetime.fromisoformat(cached['date'])
                # التحقق من أن التاريخ ليس قديماً جداً (أكثر من شهر)
                if datetime.now() - last_date < timedelta(days=30):
                    self.current_date = last_date
            except:
                pass
    
    def create_view(self):
        # محاولة تحميل آخر شهر تم عرضه
        #self.load_last_month_view()
        
        
        # محاولة ضبط اللغة المحلية للعربية
        try:
            locale.setlocale(locale.LC_TIME, 'ar_AE.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'Arabic')
            except:
                pass
        
        # وظائف مساعدة للتوقيت العربي
        def get_arabic_month_name(month_num):
            """الحصول على اسم الشهر الميلادي بالعربية"""
            arabic_months = {
                1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
                5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
                9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
            }
            return arabic_months.get(month_num, f"شهر {month_num}")
        
        def get_arabic_day_name(day_num):
            """الحصول على اسم اليوم بالعربية"""
            arabic_days = {
                0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
                4: "الجمعة", 5: "السبت", 6: "الأحد"
            }
            return arabic_days.get(day_num, f"يوم {day_num}")
        
        def get_arabic_weekday_name(date_obj):
            """الحصول على اسم اليوم بالعربية من تاريخ"""
            return get_arabic_day_name(date_obj.weekday())
        
        def get_accurate_hijri_date(date_obj=None):
            """حساب التاريخ الهجري بدقة للتاريخ المحدد"""
            if date_obj is None:
                date_obj = datetime.now()
            
            gy = date_obj.year
            gm = date_obj.month
            gd = date_obj.day
            
            # خوارزمية تحويل ميلادي إلى هجري
            if (gy > 1582) or ((gy == 1582) and (gm > 10)) or ((gy == 1582) and (gm == 10) and (gd > 14)):
                jd = (int((1461 * (gy + 4800 + int((gm - 14) / 12))) / 4) +
                      int((367 * (gm - 2 - 12 * int((gm - 14) / 12))) / 12) -
                      int((3 * int((gy + 4900 + int((gm - 14) / 12)) / 100)) / 4) +
                      gd - 32075)
            else:
                jd = 367 * gy - int((7 * (gy + 5001 + int((gm - 9) / 7))) / 4) + int((275 * gm) / 9) + gd + 1729777
            
            l = jd - 1948440 + 10632
            n = int((l - 1) / 10631)
            l = l - 10631 * n + 354
            j = (int((10985 - l) / 5316)) * (int((50 * l) / 17719)) + (int(l / 5670)) * (int((43 * l) / 15238))
            l = l - (int((30 - j) / 15)) * (int((17719 * j) / 50)) - (int(j / 16)) * (int((15238 * j) / 43)) + 29
            
            hm = int((24 * l) / 709)
            hd = l - int((709 * hm) / 24)
            hy = 30 * n + j - 30
            
            # أسماء الأشهر الهجرية
            hijri_months = [
                "المحرم", "صفر", "ربيع الأول", "ربيع الآخر",
                "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
                "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
            ]
            
            # أسماء أيام الأسبوع بالعربية للتاريخ الهجري
            hijri_day_name = get_arabic_day_name(date_obj.weekday())
            
            return {
                "day": hd,
                "month": hijri_months[hm-1],
                "year": hy,
                "day_name": hijri_day_name,
                "full_date": f"{hd} {hijri_months[hm-1]} {hy} هـ",
                "short_date": f"{hd}/{hm}/{hy} هـ"
            }
        
        def get_current_time_arabic():
            """الحصول على الوقت الحالي بالعربية"""
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            second = now.second
            
            # تحويل إلى نظام 12 ساعة
            period = "ص" if hour < 12 else "م"
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12
            
            return {
                "formatted": f"{hour_12:02d}:{minute:02d}:{second:02d} {period}",
                "hour": hour_12,
                "minute": minute,
                "second": second,
                "period": period
            }
        
        # استخدام التاريخ المخزن للتنقل
        current_date = self.current_date
        current_year = current_date.year
        current_month = current_date.month
        today = datetime.now()
        is_current_month = (current_year == today.year and current_month == today.month)
        
        # اسم الشهر الحالي بالعربية
        current_month_name = get_arabic_month_name(current_month)
        
        # التاريخ الهجري للتاريخ المحدد
        hijri_date = get_accurate_hijri_date(current_date)
        
        # الحصول على موقع المستخدم
        if self.location is None:
            self.location = self.get_user_location()
        
        # مواقيت الصلاة للتاريخ الحالي
        prayer_data = self.get_prayer_times_for_date(current_date, self.location)
        prayer_times = prayer_data['timings']
        
        # الوقت الحالي بالعربية
        current_time = get_current_time_arabic()
        
        # تحديد أحجام ديناميكية حسب شاشة الهاتف
        screen_width = self.page.width
        is_small_screen = screen_width < 400
        
        # أحجام الخطوط المتجاوبة
        title_size = 20 if is_small_screen else 22
        subtitle_size = 16 if is_small_screen else 18
        normal_size = 14 if is_small_screen else 16
        small_size = 12 if is_small_screen else 14
        
        # أزرار التنقل بين الشهور
        navigation_buttons = Container(
            content=Row(
                controls=[
            # زر الشهر السابق
                    Container(
                        on_click=lambda e: self.navigate_month("prev"),
                        bgcolor=Colors.WHITE,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                        content=Text(
                            "الشهر السابق",
                            color=Colors.BLUE_700,
                            size=14,
                            font_family=BUTTON_FONT
                        ),
                    ),
            
            # زر العودة للشهر الحالي
                    Container(
                        on_click=lambda e: self.navigate_month("today"),
                        bgcolor=Colors.GREEN if is_current_month else Colors.GREEN_100,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                        content=Row(
                            controls=[
                                Icon(Icons.TODAY, 
                                     color=Colors.WHITE if is_current_month else Colors.GREEN_700,
                                     size=16),
                                Text(
                                    "الشهر الحالي",
                                    color=Colors.WHITE if is_current_month else Colors.GREEN_700,
                                    size=14,
                                    font_family=BUTTON_FONT
                                ),
                            ],
                            spacing=5
                        ),
                    ),
            
            # زر الشهر التالي
                    Container(
                        on_click=lambda e: self.navigate_month("next"),
                        bgcolor=Colors.WHITE,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                        content=Text(
                            "الشهر التالي",
                            color=Colors.BLUE_700,
                            size=14,
                            font_family=BUTTON_FONT
                        ),
                    ),
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                spacing=5,
            ),
            margin=ft.Margin.only(bottom=10),
        )
        
        # إنشاء رأس التقويم
        header = Container(
            expand=True,
            padding=15 if is_small_screen else 20,
            bgcolor=APP_BGCOLOR,
            border_radius=12,
            margin=ft.Margin.only(bottom=10),
            alignment=ft.Alignment(0, 0),
            content=Column(
                controls=[
                    # التاريخ الميلادي
                    Container(
                        content=Text(
                            f"{current_month_name} {current_year}",
                            size=title_size,
                            color=Colors.WHITE,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT,
                            text_align=TextAlign.CENTER
                        ),
                        margin=ft.Margin.only(bottom=5)
                    ),
                    
                    # التاريخ الهجري
                    Container(
                        content=Text(
                            hijri_date["full_date"],
                            size=subtitle_size,
                            color=Colors.WHITE,
                            font_family=BUTTON_FONT,
                            text_align=TextAlign.CENTER
                        ),
                        margin=ft.Margin.only(bottom=10)
                    ),
                    
                    # مؤشر إذا كان هذا الشهر الحالي

                        Container(
                            content=Text(
                                "الشهر الحالي",
                                size=small_size,
                                color="#FFD700",
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            ),
                            margin=ft.Margin.only(bottom=5)
                        )
                ],
                spacing=0,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        
        
        # معلومات الموقع
        location_info = Container(
            expand=True,
            padding=12,
            bgcolor=Colors.BLUE_50,
            border_radius=10,
            margin=ft.Margin.only(bottom=10),
            content=Row(
                controls=[
                    Icon(Icons.LOCATION_ON, size=18, color=Colors.BLUE_700),
                    Container(width=8),
                    Container(
                        expand=True,
                        content=Column(
                            controls=[
                                Text(
                                    f"{self.location.get('city', 'موقعك')} - {self.location.get('country', '')}",
                                    size=small_size,
                                    color=Colors.BLUE_700,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.START
                                ),
                                Text(
                                    f"مصدر الموقع: {self.location.get('method', 'غير معروف')}",
                                    size=small_size - 2,
                                    color=Colors.GREY_600,
                                    font_family=BUTTON_FONT,
                                    text_align=TextAlign.START
                                )
                            ],
                            spacing=2,
                            horizontal_alignment=CrossAxisAlignment.START
                        )
                    )
                ],
                alignment=MainAxisAlignment.START
            )
        )
        
        # زر تحديث البيانات
        refresh_button = Container(
            content=Container(
                on_click=lambda e: self.refresh_data(),
                bgcolor=Colors.BLUE_100,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                content=Row(
                    controls=[
                        Icon(Icons.REFRESH, color=Colors.BLUE_700, size=20),
                        Text(
                            "تحديث البيانات",
                            color=Colors.BLUE_700,
                            size=16,
                            font_family=BUTTON_FONT
                        ),
                    ],
                    spacing=8,
                    alignment=MainAxisAlignment.CENTER
                ),
            ),
            margin=ft.Margin.only(bottom=10),
            alignment=ft.Alignment(0, 0)
        )
        
        # إنشاء جدول أيام الشهر
        import calendar
        cal = calendar.monthcalendar(current_year, current_month)
        
        # أسماء أيام الأسبوع بالعربية
        arabic_weekdays = ["إثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت", "أحد"]
        
        # حساب حجم الخلايا بناءً على حجم الشاشة
        cell_size = min(45, (screen_width - 40) // 7)  # 40 للـ padding
        
        # رأس الجدول (أسماء الأيام)
        weekday_header = Container(
            height=35,
            margin=ft.Margin.only(bottom=5),
            content=Row(
                controls=[
                    Container(
                        width=cell_size,
                        alignment=ft.Alignment(0, 0),
                        content=Text(
                            day,
                            size=small_size,
                            color=Colors.BLUE_700,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT
                        )
                    ) for day in arabic_weekdays
                ],
                spacing=0
            )
        )
        
        # إنشاء صفوف الأيام
        day_rows = []
        for week in cal:
            week_row = Row(
                spacing=0,
                controls=[]
            )
            
            for day in week:
                if day == 0:
                    # يوم فارغ (لا ينتمي لهذا الشهر)
                    day_cell = Container(
                        width=cell_size,
                        height=cell_size,
                        bgcolor=Colors.TRANSPARENT
                    )
                else:
                    # تحديد إذا كان اليوم الحالي
                    is_today = (is_current_month and day == today.day)
                    day_date = datetime(current_year, current_month, day)
                    
                    # الحصول على التاريخ الهجري لهذا اليوم
                    day_hijri = get_accurate_hijri_date(day_date)
                    
                    day_cell = Container(
                        width=cell_size,
                        height=cell_size,
                        bgcolor=Colors.GREEN if is_today else Colors.WHITE,
                        border_radius=cell_size // 2 if is_today else cell_size // 4,
                        border=ft.Border.all(2, Colors.BLUE if is_today else Colors.TRANSPARENT),
                        alignment=ft.Alignment(0, 0),
                        on_click=lambda e, d=day, m=current_month, y=current_year: 
                            self.show_day_details(d, m, y),
                        content=Column(
                            controls=[
                                Text(
                                    str(day),
                                    size=small_size,
                                    color=Colors.BLACK if not is_today else Colors.WHITE,
                                    weight=FontWeight.BOLD,
                                    font_family=BUTTON_FONT
                                ),
                                Text(
                                    str(day_hijri["day"]),
                                    size=small_size - 2,
                                    color=Colors.GREY_600 if not is_today else Colors.WHITE,
                                    font_family=BUTTON_FONT
                                )
                            ],
                            spacing=0,
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    )
                
                week_row.controls.append(day_cell)
            
            day_rows.append(week_row)
        
        # جدول التقويم
        calendar_table = Container(
            content=Column(
                controls=[weekday_header] + day_rows,
                spacing=2
            ),
            padding=10,
            bgcolor=Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, Colors.GREY_300)
        )
        
        # قسم مواقيت الصلاة
        prayer_controls = []
        prayer_items = [
            ("Fajr", "الفجر"),
            ("Sunrise", "الشروق"),
            ("Dhuhr", "الظهر"),
            ("Asr", "العصر"),
            ("Maghrib", "المغرب"),
            ("Isha", "العشاء")
        ]
        
        for prayer_code, prayer_name_ar in prayer_items:
            prayer_controls.append(
                Container(
                    expand=True,
                    padding=10,
                    bgcolor=Colors.BLUE_50,
                    border_radius=8,
                    border=ft.Border.all(1, Colors.BLUE_200),
                    content=Column(
                        controls=[
                            Text(
                                prayer_name_ar,
                                size=small_size,
                                color=Colors.BLUE_700,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            ),
                            Text(
                                prayer_times[prayer_code],
                                size=normal_size,
                                color=Colors.BLACK,
                                weight=FontWeight.BOLD,
                                font_family=BUTTON_FONT,
                                text_align=TextAlign.CENTER
                            )
                        ],
                        spacing=2,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    )
                )
            )
        
        # إنشاء صفين لمواقيت الصلاة (3 في كل صف)
        prayer_rows = []
        for i in range(0, len(prayer_controls), 3):
            prayer_rows.append(
                Row(
                    controls=prayer_controls[i:i+3],
                    spacing=8,
                    alignment=MainAxisAlignment.SPACE_BETWEEN
                )
            )
        
        prayer_times_section = Container(
            expand=True,
            padding=12,
            bgcolor=Colors.WHITE,
            border_radius=12,
            margin=ft.Margin.only(top=10, bottom=10),
            content=Column(
                controls=[
                    Container(
                        content=Text(
                            f"مواقيت الصلاة لـ {current_month_name}",
                            size=title_size - 2,
                            color=APP_BGCOLOR,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT,
                            text_align=TextAlign.CENTER
                        ),
                        margin=ft.Margin.only(bottom=10)
                    ),
                    
                    # مواقيت الصلاة
                    Container(
                        content=Column(
                            controls=prayer_rows,
                            spacing=8
                        )
                    )
                ],
                spacing=10
            )
        )
        
        # معلومات إضافية
        info_items = [
            (Icons.CALENDAR_MONTH, Colors.GREEN, f"شهر {current_month_name}"),
            (Icons.CALENDAR_VIEW_MONTH, Colors.BLUE, f"عدد أيام الشهر: {calendar.monthrange(current_year, current_month)[1]}"),
            (Icons.SUNNY, Colors.ORANGE, f"فصل السنة: {self.get_season_arabic(current_month)}"),
            (Icons.INFO, Colors.PURPLE, f"السنة الميلادية: {current_year}")
        ]
        
        info_controls = []
        for icon, color, text in info_items:
            info_controls.append(
                Row(
                    controls=[
                        Icon(icon, size=18, color=color),
                        Container(width=8),
                        Container(
                            expand=True,
                            content=Text(
                                text,
                                size=small_size,
                                color=Colors.BLACK,
                                font_family=BUTTON_FONT
                            )
                        )
                    ],
                    alignment=MainAxisAlignment.START
                )
            )
            info_controls.append(Divider(height=8, color=Colors.GREY_300))
        
        # إزالة آخر Divider
        if info_controls:
            info_controls.pop()
        
        info_section = Container(
            expand=True,
            padding=12,
            bgcolor=Colors.WHITE,
            border_radius=12,
            content=Column(
                controls=[
                    Container(
                        content=Text(
                            "معلومات التقويم",
                            size=title_size - 2,
                            color=APP_BGCOLOR,
                            weight=FontWeight.BOLD,
                            font_family=BUTTON_FONT,
                            text_align=TextAlign.CENTER
                        ),
                        margin=ft.Margin.only(bottom=10)
                    ),
                    
                    Container(
                        content=Column(
                            controls=info_controls,
                            spacing=5
                        )
                    )
                ],
                spacing=8,
                height=210
            )
        )
        
        return View(
            route="/calendar",
            controls=[
                AppBar(
                    title=Text("التقويم الشامل", 
                              weight=FontWeight.BOLD, 
                              size=title_size - 2, 
                              color=Colors.WHITE, 
                              text_align=TextAlign.CENTER),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS if self.page.rtl else Icons.ARROW_FORWARD,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(self.page),
                    ),
                ),
                Container(
                    content=ListView(
                        controls=[
                            navigation_buttons,
                            header,
                            location_info,
                            refresh_button,
                            calendar_table,
                            prayer_times_section,
                            info_section,
                            Container(height=20)  # مسافة في الأسفل
                        ],
                        expand=True,
                        padding=ft.Padding.symmetric(horizontal=10)
                    ),
                    expand=True,
                    bgcolor="#f5f7fa"
                ),
            ],
            bgcolor="#f5f7fa",
            padding=0
        )
    
    def refresh_data(self):
        """تحديث البيانات يدوياً"""
        # حذف البيانات المخزنة مؤقتاً
        try:
            import glob
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.json"))
            cache_files.extend(glob.glob(os.path.join(self.cache_dir, "*.pkl")))
            
            for file in cache_files:
                try:
                    os.remove(file)
                except:
                    pass
                    
            # إعادة تعيين الموقع
            self.location = None
            
            # إعادة تعيين البيانات المخزنة مؤقتاً
            self.save_to_cache('last_month_view', {
                'year': self.current_date.year,
                'month': self.current_date.month,
                'date': self.current_date.isoformat()
            }, expiry_hours=720)
            
            # إعادة تحميل الصفحة
            self.page.views.pop()
            self.page.views.append(self.create_view())
            safe_update(self.page)
            
            # عرض رسالة نجاح
            (ft.SnackBar(content=ft.Text("تم تحديث البيانات بنجاح", color=Colors.WHITE), bgcolor=Colors.GREEN, duration=2000))
            safe_update(self.page)
            
        except Exception as e:
            print(f"خطأ في تحديث البيانات: {e}")
            (ft.SnackBar(content=ft.Text(f"خطأ في تحديث البيانات: {str(e)}", color=Colors.WHITE), bgcolor=Colors.RED, duration=3000))
            safe_update(self.page)
    
    def get_season_arabic(self, month):
        """الحصول على الفصل بالعربية حسب الشهر"""
        if month in [12, 1, 2]:
            return "الشتاء"
        elif month in [3, 4, 5]:
            return "الربيع"
        elif month in [6, 7, 8]:
            return "الصيف"
        else:
            return "الخريف"
    
    def show_day_details(self, day, month, year):
        """عرض تفاصيل يوم معين"""
        from datetime import datetime
        
        day_date = datetime(year, month, day)
        
        # الحصول على معلومات اليوم
        import locale
        
        try:
            locale.setlocale(locale.LC_TIME, 'ar_AE.UTF-8')
        except:
            pass
        
        day_name_ar = day_date.strftime("%A")
        
        # حساب التاريخ الهجري
        def get_hijri_for_day():
            """حساب التاريخ الهجري لليوم المحدد"""
            gy = year
            gm = month
            gd = day
            
            if (gy > 1582) or ((gy == 1582) and (gm > 10)) or ((gy == 1582) and (gm == 10) and (gd > 14)):
                jd = (int((1461 * (gy + 4800 + int((gm - 14) / 12))) / 4) +
                      int((367 * (gm - 2 - 12 * int((gm - 14) / 12))) / 12) -
                      int((3 * int((gy + 4900 + int((gm - 14) / 12)) / 100)) / 4) +
                      gd - 32075)
            else:
                jd = 367 * gy - int((7 * (gy + 5001 + int((gm - 9) / 7))) / 4) + int((275 * gm) / 9) + gd + 1729777
            
            l = jd - 1948440 + 10632
            n = int((l - 1) / 10631)
            l = l - 10631 * n + 354
            j = (int((10985 - l) / 5316)) * (int((50 * l) / 17719)) + (int(l / 5670)) * (int((43 * l) / 15238))
            l = l - (int((30 - j) / 15)) * (int((17719 * j) / 50)) - (int(j / 16)) * (int((15238 * j) / 43)) + 29
            
            hm = int((24 * l) / 709)
            hd = l - int((709 * hm) / 24)
            hy = 30 * n + j - 30
            
            hijri_months = [
                "المحرم", "صفر", "ربيع الأول", "ربيع الآخر",
                "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
                "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
            ]
            
            return {
                "day": hd,
                "month": hijri_months[hm-1],
                "year": hy,
                "full": f"{hd} {hijri_months[hm-1]} {hy} هـ"
            }
        
        hijri_info = get_hijri_for_day()
        
        # مواقيت الصلاة لهذا اليوم حسب الموقع
        prayer_data = self.get_prayer_times_for_date(day_date, self.location)
        prayer_times = prayer_data['timings']
        
        # إنشاء محتوى الـ dialog
        content = Column(
            controls=[
                Container(
                    content=Text(
                        f"تفاصيل يوم {day}/{month}/{year}",
                        size=18,
                        color=APP_BGCOLOR,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    ),
                    padding=ft.Padding.only(bottom=15)
                ),
                
                # معلومات اليوم
                Container(
                    content=Column(
                        controls=[
                            Row(
                                controls=[
                                    Icon(Icons.CALENDAR_TODAY, size=20, color=Colors.BLUE),
                                    Container(width=8),
                                    Column(
                                        controls=[
                                            Text("التاريخ الميلادي", size=12, color=Colors.GREY_600),
                                            Text(f"{day}/{month}/{year}", size=14, color=Colors.BLACK, weight=FontWeight.BOLD)
                                        ],
                                        spacing=2
                                    )
                                ],
                                alignment=MainAxisAlignment.START
                            ),
                            
                            Divider(height=10, color=Colors.GREY_300),
                            
                            Row(
                                controls=[
                                    Icon(Icons.NIGHTLIGHT_ROUND, size=20, color=Colors.PURPLE),
                                    Container(width=8),
                                    Column(
                                        controls=[
                                            Text("التاريخ الهجري", size=12, color=Colors.GREY_600),
                                            Text(hijri_info["full"], size=14, color=Colors.BLACK, weight=FontWeight.BOLD)
                                        ],
                                        spacing=2
                                    )
                                ],
                                alignment=MainAxisAlignment.START
                            ),
                            
                            Divider(height=10, color=Colors.GREY_300),
                            
                            Row(
                                controls=[
                                    Icon(Icons.TODAY, size=20, color=Colors.GREEN),
                                    Container(width=8),
                                    Column(
                                        controls=[
                                            Text("اليوم", size=12, color=Colors.GREY_600),
                                            Text(day_name_ar, size=14, color=Colors.BLACK, weight=FontWeight.BOLD)
                                        ],
                                        spacing=2
                                    )
                                ],
                                alignment=MainAxisAlignment.START
                            )
                        ],
                        spacing=8
                    ),
                    padding=ft.Padding.symmetric(vertical=10)
                ),
                
                Divider(height=15, color=Colors.GREY_300),
                
                # مواقيت الصلاة
                Container(
                    content=Text(
                        "مواقيت الصلاة",
                        size=16,
                        color=APP_BGCOLOR,
                        weight=FontWeight.BOLD,
                        font_family=BUTTON_FONT,
                        text_align=TextAlign.CENTER
                    ),
                    padding=ft.Padding.only(bottom=10)
                ),
                
                Container(
                    content=Column(
                        controls=[
                            Row(
                                controls=[
                                    Container(
                                        expand=True,
                                        content=Text(prayer_name, 
                                                  size=13, 
                                                  color=Colors.BLUE_700, 
                                                  weight=FontWeight.BOLD,
                                                  font_family=BUTTON_FONT)
                                    ),
                                    Text(time, 
                                         size=13, 
                                         color=Colors.BLACK, 
                                         weight=FontWeight.BOLD,
                                         font_family=BUTTON_FONT)
                                ],
                                alignment=MainAxisAlignment.SPACE_BETWEEN
                            )
                            for prayer_name, time in [
                                ("الفجر", prayer_times["Fajr"]),
                                ("الشروق", prayer_times["Sunrise"]),
                                ("الظهر", prayer_times["Dhuhr"]),
                                ("العصر", prayer_times["Asr"]),
                                ("المغرب", prayer_times["Maghrib"]),
                                ("العشاء", prayer_times["Isha"])
                            ]
                        ],
                        spacing=8
                    ),
                    padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                    bgcolor=Colors.BLUE_50,
                    border_radius=8
                ),
                
                # معلومات مصدر البيانات
                Divider(height=15, color=Colors.GREY_300),
                
                Container(
                    content=Row(
                        controls=[
                            Icon(
                                Icons.INFO,
                                size=16,
                                color=Colors.ORANGE if prayer_data.get('source') == 'بديل (بدون إنترنت)'
                                      else Colors.BLUE if prayer_data.get('source') == 'محفوظ'
                                      else Colors.GREEN
                            ),
                            Container(width=8),
                            Text(
                                f"مصدر البيانات: {prayer_data.get('source', 'غير معروف')}",
                                size=12,
                                color=Colors.GREY_600,
                                font_family=BUTTON_FONT
                            )
                        ],
                        alignment=MainAxisAlignment.START
                    ),
                    padding=ft.Padding.only(top=10)
                )
            ],
            scroll=ScrollMode.AUTO,
            height=400
        )
        
        # إنشاء الـ dialog
        dialog = AlertDialog(
            title=Text(f"يوم {day}", 
                      font_family=BUTTON_FONT, 
                      weight=FontWeight.BOLD,
                      size=16),
            content=content,
            actions=[
                TextButton(
                    "إغلاق",
                    on_click=lambda e: setattr(dialog, "open", False)
                )
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        safe_update(self.page)

class SearchPage:
    @staticmethod
    def create(page: Page):
        # حقل البحث
        search_field = TextField(
            hint_text="ابحث عن ذكر أو دعاء...",
            border_color=APP_BGCOLOR,
            border_radius=30,
            text_size=16,
            color=Colors.BLACK,
            text_align=TextAlign.RIGHT,
            expand=True,
            filled=True,
            fill_color=Colors.WHITE,
            prefix_icon=Icons.SEARCH,
            autofocus=True,
            on_change=lambda e: perform_search(e.control.value),
        )
        
        # نتائج البحث
        results_column = Column(scroll=ScrollMode.AUTO, expand=True)
        
        # دالة البحث المباشر (بنفس دقة SearchResultsPage)
        def perform_search(query):
            # مسح النتائج السابقة
            results_column.controls.clear()
            
            if not query or len(query.strip()) < 2:
                # عرض رسالة عندما يكون النص أقل من حرفين
                results_column.controls.append(
                    Container(
                        padding=50,
                        alignment=ft.Alignment(0, 0),
                        content=Column(
                            controls=[
                                Icon(Icons.SEARCH, size=50, color=Colors.GREY_400),
                                Container(height=10),
                                Text("اكتب كلمتين على الأقل لبدء البحث",
                                     size=16,
                                     color=Colors.GREY_600,
                                     text_align=TextAlign.CENTER,
                                     font_family=BUTTON_FONT)
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    )
                )
                safe_update(page)
                return
            
            # عرض رسالة جاري البحث
            results_column.controls.append(
                Container(
                    padding=30,
                    alignment=ft.Alignment(0, 0),
                    content=Column(
                        controls=[
                            ProgressRing(width=30, height=30, color=APP_BGCOLOR),
                            Container(height=10),
                            Text("جاري البحث...",
                                 size=14,
                                 color=Colors.GREY_600,
                                 font_family=BUTTON_FONT)
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    )
                )
            )
            safe_update(page)
            
            # تجميع كل الأذكار من جميع المصادر (نفس الطريقة القديمة)
            all_azkar = [
                *get_azkar_sabah(),
                *get_azkar_masaa(),
                *get_azkar_baad_salah(),
                *get_adeiat_wa_azkar_mutanawiea(),
                *get_azkar_azima(),
                *get_alsalat_ealaa_alnabii(),
                *get_ayat_alkursii(),
                *get_sujud(),
                *get_jwamea6(),
                *get_quran1(),
                *get_kaaba4(),
                *get_wodu50(),
                *get_istanbul(),
                *get_azkar_almanzel(),
                *get_azkar_alkhala(),
                *get_azkar_altaaam(),
                *get_athan5(),
                *get_sleep(),
                *get_wakeup(),
                *get_Nabawi_Mosque(),
                *get_sadaqa_gariya(),
                *get_adeiat_llmtwffy(),
                *get_my_azkar(),
            ]
            
            # البحث في السنن الموقوتة
            timed_sunan = get_timed_sunan()
            for key, sunan_list in timed_sunan.items():
                all_azkar.extend(sunan_list)
            
            # البحث في السنن الغير موقوتة
            untimed_sunan = get_untimed_sunan()
            for key, sunan_list in untimed_sunan.items():
                all_azkar.extend(sunan_list)
            
            # البحث في خطوات الوضوء
            wudu_steps = get_wudu_steps()
            for step in wudu_steps:
                all_azkar.append({
                    "text": step.get("title", "") + " - " + step.get("description", ""),
                    "count": 1
                })
            
            # تنظيف نص البحث (إزالة التشكيل) - نفس الطريقة القديمة
            query_clean = strip_harakat(query.lower())
            
            # تصفية النتائج
            results = []
            for azkar in all_azkar:
                if "text" in azkar:
                    text_clean = strip_harakat(azkar["text"].lower())
                    if query_clean in text_clean:
                        results.append(azkar)
            
            # إزالة التكرارات
            unique_results = []
            seen_texts = set()
            for result in results:
                text = result.get("text", "")
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    unique_results.append(result)
            
            # مسح رسالة "جاري البحث"
            results_column.controls.clear()
            
            if not unique_results:
                # لا توجد نتائج
                results_column.controls.append(
                    Container(
                        padding=50,
                        alignment=ft.Alignment(0, 0),
                        content=Column(
                            controls=[
                                Icon(Icons.SEARCH_OFF, size=60, color=Colors.GREY_400),
                                Container(height=20),
                                Text(f"لا توجد نتائج لـ '{query}'",
                                     size=18,
                                     color=Colors.GREY_700,
                                     weight=FontWeight.BOLD,
                                     text_align=TextAlign.CENTER,
                                     font_family=BUTTON_FONT),
                                Container(height=10),
                                Text("جرب كلمات أخرى",
                                     size=14,
                                     color=Colors.GREY_600,
                                     text_align=TextAlign.CENTER,
                                     font_family=BUTTON_FONT)
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        )
                    )
                )
            else:
                # عرض عدد النتائج
                results_column.controls.append(
                    Container(
                        content=Text(
                            f"تم العثور على {len(unique_results)} نتيجة",
                            size=16,
                            color=Colors.BLUE_700,
                            weight=FontWeight.BOLD,
                            text_align=TextAlign.CENTER,
                            font_family=BUTTON_FONT,
                        ),
                        padding=ft.Padding.only(bottom=15)
                    )
                )
                
                # عرض النتائج (بنفس تنسيق SearchResultsPage)
                for result in unique_results[:50]:  # حد أقصى 50 نتيجة
                    # عرض نص الذكر مع التنسيق الجميل
                    result_card = Container(
                        content=Column(
                            [
                                Text(
                                    spans=AzkarHelper.format_azkar_text(result["text"]),
                                    text_align=TextAlign.CENTER
                                ),
                                # عرض عدد التكرارات كعلامة صغيرة في الأسفل
                                Container(
                                    content=Text(
                                        f"التكرار: {result['count']}" if result.get("count", 0) > 1 else "",
                                        size=14,
                                        color="#0daca6",
                                        weight=FontWeight.BOLD,
                                        font_family=BUTTON_FONT,
                                        text_align=TextAlign.CENTER,
                                    ),
                                    padding=ft.Padding.only(top=15),
                                ) if result.get("count", 0) > 1 else Container()
                            ],
                            spacing=0,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        ),
                        padding=25,
                        bgcolor=Colors.WHITE,
                        border_radius=10,
                        border=ft.Border.all(1, Colors.GREY_300),
                        margin=ft.Margin.only(bottom=15),
                        width=400,
                    )
                    
                    results_column.controls.append(result_card)
            
            safe_update(page)
        
        # عرض الصفحة
        return View(
            route="/search",
            controls=[
                AppBar(
                    title=Text("بحث في الأذكار", 
                              weight=FontWeight.BOLD, 
                              size=18, 
                              color=Colors.WHITE),
                    bgcolor=APP_BGCOLOR,
                    center_title=True,
                    leading=IconButton(
                        icon=Icons.ARROW_BACK_IOS,
                        icon_color=Colors.WHITE,
                        on_click=lambda e: handle_back(page),
                    ),
                ),
                Container(
                    content=Column(
                        controls=[
                            # حقل البحث
                            Container(
                                content=search_field,
                                padding=ft.Padding.symmetric(horizontal=20, vertical=15),
                            ),
                            
                            # نص مساعد
                            
                            
                            # الفاصل
                            Divider(height=1, color=Colors.GREY_300),
                            
                            # نتائج البحث
                            Container(
                                expand=True,
                                content=results_column,
                                padding=ft.Padding.symmetric(horizontal=15, vertical=10),
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                    bgcolor="#f0f2f5",
                ),
            ],
            bgcolor="#f0f2f5",
            padding=0
        )

# ============ الدالة الرئيسية ============

# تعريف قائمة لتتبع سجل التنقل
async def main(page: Page):
    ads_manager = AdsManager(page)
    page._ads_manager = ads_manager  # تخزينه في الصفحة للوصول منها
    # إخفاء أخطاء الاتصال عند الإغلاق
    if sys.platform == "win32":
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(
                lambda l, c: None if isinstance(c.get("exception"), (ConnectionResetError, OSError)) 
                else l.default_exception_handler(c)
            )
        except Exception:
            pass

    # إعدادات الصفحة الأساسية
    page.title = APP_TITLE
    # ── تعيين حجم النافذة فقط على الكمبيوتر (ليس الهاتف) ──────────
    _is_desktop = sys.platform in ("win32", "darwin", "linux") and not (
        hasattr(page, "web") and page.web
    )
    if _is_desktop:
        try:
            page.window.width = APP_SIZE[0]
            page.window.height = APP_SIZE[1]
            page.window.top = APP_POSITION[1]
            page.window.left = APP_POSITION[0]
            page.window.resizable = False
        except Exception:
            pass
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.theme_mode = ThemeMode.LIGHT
    page.padding = ft.Padding.only(top=0)
    page.rtl = True
        # تهيئة ملف العادات
    init_habits_file()

    # بدء التطبيق بالصفحة الرئيسية — سيتم البناء الحقيقي لاحقاً عبر navigate("/")
    page.views.clear()

    
    # ── تعطيل انيميشن التنقل تماماً ──────────────────────────────
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
        )
    )

    _t0 = datetime.now()
    _t1 = datetime.now()
    print(f"زمن التهيئة: {(_t1 - _t0).total_seconds():.2f} ثانية")
    
    # إضافة الخطوط
    page.fonts = {
        FONT_NAME: FONT_FILE,
        BUTTON_FONT: FONT_FILE,
        FONT_QURAN: FONT_QURAN
    }

    # ══════════════════════════════════════════════
    # إعلان البانر الشفاف العالمي — يطفو في أسفل الشاشة
    # بدون أي خلفية خلفه في جميع الصفحات
    # ══════════════════════════════════════════════
    if is_mobile(page):
        global_banner = Container(
            content=fta.BannerAd(
                unit_id=get_ad_id(page, "banner"),
                on_error=lambda e: print("Global BannerAd error:", e.data),
            ),
            width=page.width if page.width else 320,
            height=50,
            alignment=ft.Alignment(0, 0),
            bottom=0,
            left=0,
            right=0,
            visible=False,  # مخفي في الصفحة الرئيسية — يظهر عند الانتقال لصفحات أخرى
        )
        page.overlay.append(global_banner)
        page._global_banner = global_banner  # حفظ المرجع للتحكم فيه لاحقاً
        safe_update(page)

    # نتحقق هل الترحيب ظهر من قبل أم لا
    show_welcome = not os.path.exists("welcome_seen.txt")

    async def close_welcome(e=None):
        welcome_view.opacity = 0
        safe_update(page)
        await asyncio.sleep(0.25)
        if welcome_view in page.overlay:
            page.overlay.remove(welcome_view)
        try:
            with open("welcome_seen.txt", "w", encoding="utf-8") as f:
                f.write("shown")
        except:
            pass
        safe_update(page)

    # شاشة الترحيب العصرية
    welcome_view = Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor=Colors.with_opacity(0.6, "black"),
        opacity=0,
        animate_opacity=400,
        content=Stack(
            expand=True,
            alignment=ft.Alignment(0, 0),
            controls=[
                Container(
                    width=340,
                    height=510,
                    border_radius=30,
                    shadow=BoxShadow(
                        blur_radius=45,
                        spread_radius=2,
                        color=Colors.with_opacity(0.4, "black"),
                        offset=Offset(0, 12),
                    ),
                    content=Stack(
                        controls=[
                            Container(
                                width=340,
                                height=510,
                                border_radius=30,
                                gradient=LinearGradient(
                                    begin=ft.Alignment(0, -1),
                                    end=ft.Alignment(0, 1),
                                    colors=[
                                        "#1a1145",
                                        "#2d1f7a",
                                        "#4C3FCB",
                                    ],
                                ),
                            ),
                            Container(
                                width=220,
                                height=220,
                                border_radius=110,
                                left=-55,
                                top=-55,
                                bgcolor=Colors.with_opacity(0.07, Colors.WHITE),
                            ),
                            Container(
                                width=160,
                                height=160,
                                border_radius=80,
                                right=-35,
                                bottom=100,
                                bgcolor=Colors.with_opacity(0.06, Colors.WHITE),
                            ),
                            Container(
                                width=80,
                                height=80,
                                border_radius=40,
                                right=25,
                                top=25,
                                bgcolor=Colors.with_opacity(0.07, Colors.WHITE),
                            ),
                            Container(
                                width=340,
                                height=510,
                                padding=ft.Padding.symmetric(horizontal=28, vertical=26),
                                content=Column(
                                    horizontal_alignment=CrossAxisAlignment.CENTER,
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    spacing=0,
                                    controls=[
                                        Container(height=4),
                                        Container(
                                            alignment=ft.Alignment(0, 0),
                                            padding=ft.Padding.all(-99),
                                            content=Image(
                                                src="assets/icons/spkl.webp",
                                                width=300,
                                                height=300,
                                                fit=ft.BoxFit.CONTAIN,
                                            ),
                                        ),
                                        Container(height=77),
                                        Column(
                                            horizontal_alignment=CrossAxisAlignment.CENTER,
                                            spacing=8,
                                            controls=[
                                                Text(
                                                    "القريب",
                                                    size=46,
                                                    weight=FontWeight.BOLD,
                                                    font_family=BUTTON_FONT,
                                                    color=Colors.WHITE,
                                                    text_align=TextAlign.CENTER,
                                                ),
                                                Container(
                                                    width=50,
                                                    height=3,
                                                    border_radius=2,
                                                    bgcolor="#D4A843",
                                                ),
                                            ],
                                        ),
                                        Container(height=4),
                                        Column(
                                            horizontal_alignment=CrossAxisAlignment.CENTER,
                                            spacing=5,
                                            controls=[
                                                Text(
                                                    "رفيقك اليومي للأذكار والسنن",
                                                    size=16,
                                                    font_family=BUTTON_FONT,
                                                    weight=FontWeight.BOLD,
                                                    text_align=TextAlign.CENTER,
                                                    color=Colors.with_opacity(
                                                        0.9, Colors.WHITE
                                                    ),
                                                ),
                                                Text(
                                                    "أذكار  ·  قرآن  ·  مواقيت صلاة  ·  سبحة",
                                                    size=12,
                                                    font_family=BUTTON_FONT,
                                                    text_align=TextAlign.CENTER,
                                                    color=Colors.with_opacity(
                                                        0.55, Colors.WHITE
                                                    ),
                                                ),
                                            ],
                                        ),
                                        Container(height=18),
                                        Container(
                                            width=255,
                                            height=50,
                                            border_radius=25,
                                            bgcolor="#D4A843",
                                            shadow=BoxShadow(
                                                blur_radius=20,
                                                spread_radius=0,
                                                color=Colors.with_opacity(
                                                    0.45, "#D4A843"
                                                ),
                                                offset=Offset(0, 7),
                                            ),
                                            alignment=ft.Alignment(0, 0),
                                            on_click=close_welcome,
                                            content=Text(
                                                "ابدأ الآن  ✦",
                                                size=17,
                                                weight=FontWeight.BOLD,
                                                font_family=BUTTON_FONT,
                                                color="#1a1145",
                                                text_align=TextAlign.CENTER,
                                            ),
                                        ),
                                        Container(height=33),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    async def delayed_show():
        await asyncio.sleep(1)
        if show_welcome:
            page.overlay.append(welcome_view)
            welcome_view.opacity = 1
            safe_update(page)

    page.run_task(delayed_show)

    # ============ نظام التنقل البسيط والسريع مثل القديم ============
    
    # كاش بسيط للصفحات (اختياري - للسرعة)
    page_cache = {}
    
    # دالة مساعدة للحصول على الصفحة من الكاش أو بنائها
    def get_or_create_page(route, create_func):
        if route not in page_cache:
            page_cache[route] = create_func()
        return page_cache[route]

    # دالة التنقل الرئيسية - بسيطة جداً مثل القديم
    # دالة التنقل الرئيسية — async لدعم الإعلان
    async def navigate(route):
        print(f"الانتقال إلى: {route}")
        
        # إذا كنا في نفس الصفحة، لا تفعل شيئاً
        if page.views and page.views[-1].route == route:
            return

        # عرض الإعلان قبل الانتقال (على الهاتف فقط، وليس الصفحة الرئيسية)
        if route != "/" and is_mobile(page):
            manager = getattr(page, "_ads_manager", None)
            if manager:
                await manager.show_ad()
        
        # بناء الصفحة المطلوبة
        if route == "/":
            view = HomePage.create(page)
            
        elif route == "/search":
            view = SearchPage.create(page)
            
        elif route == "/qibla":
            view = QiblaWebViewPage(page).create_view()
            
        elif route == "/about":
            view = AboutPage.create(page)
            
        elif route == "/hajj":
            view = hajjPage.create(page)
            
        elif route == "/azkar_sabah":
            view = AzkarPage.create(get_azkar_sabah(), "أذكار الصباح", route, page)
            
        elif route == "/azkar_masaa":
            view = AzkarPage.create(get_azkar_masaa(), "أذكار المساء", route, page)
            
        elif route == "/azkar_baad_salah":
            view = AzkarPage.create(get_azkar_baad_salah(), "أذكار بعد الصلاة", route, page)
            
        elif route == "/adeiat_wa_azkar_mutanawiea":
            view = AzkarPage.create(get_adeiat_wa_azkar_mutanawiea(), "أدعية وأذكار متنوعة", route, page)
            
        elif route == "/wakeup":
            view = AzkarPage.create(get_wakeup(), "أذكار الاستيقاظ", route, page)
            
        elif route == "/sujud":
            view = AzkarPage.create(get_sujud(), "أذكار الصلاة", route, page)
            
        elif route == "/istanbul":
            view = AzkarPage.create(get_istanbul(), "أذكار المسجد", route, page)
            
        elif route == "/azkar_azima":
            view = AzkarPage.create(get_azkar_azima(), "أذكار عظيمة", route, page)
            
        elif route == "/azkar_almanzel":
            view = AzkarPage.create(get_azkar_almanzel(), "أذكار المنزل", route, page)
            
        elif route == "/azkar_alkhala":
            view = AzkarPage.create(get_azkar_alkhala(), "أذكار الخلاء", route, page)
            
        elif route == "/azkar_altaaam":
            view = AzkarPage.create(get_azkar_altaaam(), "أذكار الطعام", route, page)
            
        elif route == "/alsalat_ealaa_alnabii":
            view = AzkarPage.create(get_alsalat_ealaa_alnabii(), "الصلاة على النبي ﷺ", route, page)
            
        elif route == "/ayat_alkursii":
            view = AzkarPage.create(get_ayat_alkursii(), "آية الكرسي", route, page)
            
        elif route == "/adeiat_llmtwffy":
            view = AzkarPage.create(get_adeiat_llmtwffy(), "أدعية للمتوفي", route, page, show_counter=False)
            
        elif route == "/kaaba4":
            view = AzkarPage.create(get_kaaba4(), "أدعية الأنبياء من القرآن", route, page, show_counter=False)
            
        elif route == "/quran80":
            view = AzkarPage.create(get_quran1(), "الأدعية القرآنية", route, page, show_counter=False)
            
        elif route == "/jwamea6":
            view = AzkarPage.create(get_jwamea6(), "جوامع الدعاء", route, page, show_counter=False)
            
        elif route == "/athan5":
            view = AzkarPage.create(get_athan5(), "أذكار الأذان", route, page)
            
        elif route == "/wodu50":
            view = AzkarPage.create(get_wodu50(), "أذكار الوضوء", route, page)
            
        elif route == "/sadaqa_gariya":
            view = AzkarPage.create(get_sadaqa_gariya(), "صدقة جارية", route, page, show_counter=False)
            
        elif route == "/sleep":
            view = AzkarPage.create(get_sleep(), "أذكار قبل النوم", route, page)
            
        elif route == "/Nabawi_Mosque":
            view = AzkarPage.create(get_Nabawi_Mosque(), "أدعية النبي ﷺ", route, page)
            
        elif route == "/islamic_library":
            view = IslamicLibraryPage.create(page)
            
        elif route == "/learn_prayer":
            view = LearnPrayerPage.create(page)
            
        elif route == "/quran": 
            view = QuranIndexPage.create(page)
            
        elif route.startswith("/quran/surah/"):
            parts = route.split("/")
            if parts[-1].isdigit():
                n = int(parts[-1])
                if 1 <= n <= 114:
                    view = QuranSurahPage.create(page, n)
                else:
                    view = QuranIndexPage.create(page)
            else:
                view = QuranIndexPage.create(page)
                
        elif route == "/electronic_tasbih":
            view = TasbihPage(page).get_view()
            
        elif route == "/prayer_times":
            view = PrayerTimesPage.create(page)
            
        elif route == "/settings":
            view = SettingsPage.create(page)
            
        elif route == "/wudu_learning":
            view = WuduLearningPage.create(page)
            
        elif route == "/timed_sunan":
            view = TimedSunanPage.create(page)
            
        elif route == "/untimed_sunan":
            view = UntimedSunanPage.create(page)
            
        elif route == "/my_azkar":
            view = MyAzkarPage(page).get_view()
            
        elif route == "/add_azkar":
            view = AddAzkarPage(page).get_view()
            
        elif route == "/youm":
            view = youmgPage.create(page)
            
        elif route == "/fadl":
            view = fadlPage.create(page)
            
        elif route == "/daily_goals":
            view = DailyGoalsPage(page).get_view()
            
        elif route == "/calendar":
            view = CalendarPage.create(page)
            
        else:
            print(f"مسار غير معروف: {route}")
            return
        
        # إضافة الصفحة إلى المكدس وتحديثها
        page.views.append(view)

        # إخفاء/إظهار البانر العالمي
        banner = getattr(page, "_global_banner", None)
        if banner is not None:
            banner.visible = (route != "/")
            try:
                banner.update()
            except Exception:
                pass

        safe_update(page)

    # معالج تغيير المسار — run_task فقط لأن navigate أصبحت async
    def route_change(e):
        page.run_task(navigate, page.route)

    # معالج الرجوع
    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.route = page.views[-1].route

            banner = getattr(page, "_global_banner", None)
            if banner is not None:
                banner.visible = (page.route != "/")
                try:
                    banner.update()
                except Exception:
                    pass

            safe_update(page)
        else:
            try:
                page.window.close()
            except Exception:
                pass

    # تعيين الدوال
    # navigate هي async، لذا نلفّها بـ run_task حتى تعمل عند الاستدعاء العادي من الأزرار
    page.navigate = lambda route: page.run_task(navigate, route)
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # بدء التطبيق بالصفحة الرئيسية
    page.views.clear()
    await navigate("/")
    safe_update(page)

# تشغيل التطبيق
ft.run(main, assets_dir='assets')

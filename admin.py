import logging
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

from data import (
    admin_saqlash, admin_tekshir, menyu_olish, matn_olish,
    malumot_yuklash, malumotlar_fayli, foydalanuvchilar_fayli,
    barcha_buyurtmalar, buyurtma_olish, buyurtma_holat_yangilash,
    get_categories, get_category_products, get_product,
    update_product_field, add_product, delete_product,
    malumot_saqlash
)

logger = logging.getLogger(__name__)

rr = Router()

HOLAT_NOMLARI = {
    "pending": "kutilmoqda",
    "accepted": "qabul qilindi",
    "processing": "tayyorlanmoqda",
    "completed": "yakunlangan",
    "cancelled": "bekor qilingan"
}


class AdminStates(StatesGroup):
    password = State()


class MahsulotTahrir(StatesGroup):
    qiymat_kutish = State()


class MahsulotQoshish(StatesGroup):
    malumot_kutish = State()


class ParolOzgartirish(StatesGroup):
    eski_parol = State()
    yangi_parol = State()
    tasdiqlash = State()


class ReklamaYuborish(StatesGroup):
    xabar_kutish = State()
    tasdiqlash = State()


def holat_formatlash(holat: str) -> str:
    return HOLAT_NOMLARI.get(holat, holat)


def admin_buyurtma_xulosa(buyurtma: Dict[str, Any]) -> str:
    holat_matni = holat_formatlash(buyurtma.get("status", ""))
    yaratilgan = (buyurtma.get("created_at") or "")[:10]
    return (
        f"🆔 Buyurtma #{buyurtma.get('id')}\n"
        f"👤 Foydalanuvchi ID: {buyurtma.get('user_id')}\n"
        f"💰 Jami: {buyurtma.get('total')} so'm\n"
        f"📊 Holat: {holat_matni}\n"
        f"📅 Sana: {yaratilgan}\n"
    )


async def foydalanuvchiga_xabar(bot, buyurtma: Dict[str, Any], sarlavha: str,
                                footer: str = "Tez orada siz bilan bog'lanamiz!"):
    holat_matni = holat_formatlash(buyurtma.get("status", ""))
    matn = (
        f"{sarlavha}\n\n"
        f"🆔 Buyurtma raqami: #{buyurtma.get('id')}\n"
        f"💰 Jami: {buyurtma.get('total')} so'm\n"
        f"📊 Holat: {holat_matni}\n\n"
        f"{footer}"
    )
    try:
        await bot.send_message(buyurtma.get("user_id"), matn)
    except Exception as e:
        logger.error(f"Xabar yuborishda xatolik: {e}")


@rr.message(Command('login'))
async def cmd_login(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if admin_tekshir(user_id):
        await message.answer("✅ Siz allaqachon admin sifatida ro'yxatdan o'tgansiz.")
        return

    await state.set_state(AdminStates.password)
    await message.answer("🔐 Admin panel uchun parolni kiriting:")


@rr.message(Command('cancel'), StateFilter(AdminStates.password))
async def cancel_admin_login(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Admin login jarayoni bekor qilindi.")

def juftlik_bolish(malumot):
    return [malumot[i:i + 2] for i in range(0, len(malumot), 2)]
    # buttons = [KeyboardButton(text=text) for key, text in menu.items()]
    # keyboard = chunked_pairs(buttons)

async def admin_menyuni_korsat(message: Message):
    menu = menyu_olish("admin")
    keyboard = []
    orqaga = KeyboardButton(text=matn_olish("orqaga"))
    for kalit, matn in menu.items():
        keyboard.append([KeyboardButton(text=matn)])
    keyboard.append([orqaga])

    await message.answer(
        matn_olish("admin_xush"),
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

@rr.message(StateFilter(AdminStates.password))
async def process_admin_login(message: Message, state: FSMContext):
    password = (message.text or "").strip()
    if password == matn_olish("parol"):
        user_id = message.from_user.id
        if admin_saqlash(user_id):
            await message.answer("✅ Siz adminlar ro'yxatiga qo'shildingiz!")
        else:
            await message.answer("ℹ️ Siz allaqachon adminlar ro'yxatidasiz.")
        await state.clear()
        await admin_menyuni_korsat(message)
    else:
        await message.answer("❌ Noto'g'ri parol. Qayta urinib ko'ring yoki /cancel yuboring.")

@rr.message(F.text == "📋 Buyurtmalar")
async def admin_buyurtmalar(message: Message):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    buyurtmalar = barcha_buyurtmalar()

    if not buyurtmalar:
        await message.answer("📋 Hozircha buyurtmalar yo'q")
        return

    await message.answer("📋 Barcha buyurtmalar:")

    for buyurtma in buyurtmalar[-10:]:
        javob_klaviaturasi = None
        if buyurtma["status"] == "pending":
            javob_klaviaturasi = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Qabul qilish",
                            callback_data=f"admin_accept_order:{buyurtma['id']}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Bekor qilish",
                            callback_data=f"admin_decline_order:{buyurtma['id']}"
                        )
                    ]
                ]
            )

        await message.answer(admin_buyurtma_xulosa(buyurtma), reply_markup=javob_klaviaturasi)

@rr.message(F.text == "👥 Foydalanuvchilar")
async def admin_foydalanuvchilar(message: Message):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    malumot = malumot_yuklash(foydalanuvchilar_fayli)
    foydalanuvchilar = malumot.get("foydalanuvchilar", [])

    if not foydalanuvchilar:
        await message.answer("👥 Foydalanuvchilar yo'q")
        return

    foydalanuvchilar_matni = f"👥 Jami foydalanuvchilar: {len(foydalanuvchilar)}\n\n"

    for foydalanuvchi in foydalanuvchilar[-10:]:
        foydalanuvchilar_matni += f"👤 {foydalanuvchi.get('toliq_ism', 'Noma\'lum')}\n"
        foydalanuvchilar_matni += f"📱 {foydalanuvchi.get('telefon', 'Noma\'lum')}\n"
        foydalanuvchilar_matni += f"🆔 ID: {foydalanuvchi['id']}\n\n"

    await message.answer(foydalanuvchilar_matni)


@rr.message(F.text == "📊 Statistika")
async def admin_statistika(message: Message):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    malumot_users = malumot_yuklash(foydalanuvchilar_fayli)
    malumot_data = malumot_yuklash(malumotlar_fayli)

    statistika_matni = "📊 Statistika:\n\n"
    statistika_matni += f"👥 Foydalanuvchilar: {len(malumot_users.get('foydalanuvchilar', []))}\n"
    statistika_matni += f"📋 Buyurtmalar: {len(malumot_data.get('buyurtmalar', []))}\n"
    statistika_matni += f"🛒 Faol savatlar: {len([s for s in malumot_data.get('savatlar', {}).values() if s])}\n"

    jami_daromad = sum(buyurtma['total'] for buyurtma in malumot_data.get('buyurtmalar', []))
    statistika_matni += f"💰 Jami daromad: {jami_daromad} so'm\n"

    await message.answer(statistika_matni)


def kategoriya_klaviaturasi():
    kategoriyalar = get_categories()
    qatorlar = [
        [InlineKeyboardButton(text=kategoriya["name"], callback_data=f"admin_category:{kalit}")]
        for kalit, kategoriya in kategoriyalar.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


def kategoriya_mahsulotlar_korsatish(kategoriya_kaliti: str):
    kategoriyalar = get_categories()
    kategoriya = kategoriyalar.get(kategoriya_kaliti)
    if not kategoriya:
        return None, None

    mahsulotlar = kategoriya.get("products", {})
    matn_qatorlar = [f"{kategoriya['name']} - mahsulotlar ro'yxati."]

    if mahsulotlar:
        matn_qatorlar.append("")
        for idx, mahsulot in enumerate(mahsulotlar.values(), 1):
            matn_qatorlar.append(f"{idx}. {mahsulot['name']} - {mahsulot['price']} so'm")
    else:
        matn_qatorlar.append("\nBu kategoriyada hali mahsulotlar yo'q.")

    klaviatura_qatorlar = [
        [InlineKeyboardButton(text=mahsulot["name"],
                              callback_data=f"admin_product:{kategoriya_kaliti}:{mahsulot_kaliti}")]
        for mahsulot_kaliti, mahsulot in mahsulotlar.items()
    ]
    klaviatura_qatorlar.append(
        [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data=f"admin_add_product:{kategoriya_kaliti}")])
    klaviatura_qatorlar.append([InlineKeyboardButton(text="🏠 Kategoriyalar", callback_data="admin_products_menu")])

    return "\n".join(matn_qatorlar), InlineKeyboardMarkup(inline_keyboard=klaviatura_qatorlar)


def mahsulot_malumot_matni(kategoriya_nomi: str, mahsulot: Dict[str, Any]) -> str:
    return (
        f"{kategoriya_nomi}\n\n"
        f"🍔 {mahsulot.get('name')}\n"
        f"📝 {mahsulot.get('description')}\n"
        f"💰 {mahsulot.get('price')} so'm\n"
        f"ID: {mahsulot.get('id')}"
    )


@rr.message(F.text == "🍔 Mahsulotlar")
async def admin_mahsulotlar(message: Message, state: FSMContext):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    joriy_holat = await state.get_state()
    if joriy_holat in {
        MahsulotTahrir.qiymat_kutish.state,
        MahsulotQoshish.malumot_kutish.state
    }:
        await state.clear()

    await message.answer("Kategoriya tanlang:", reply_markup=kategoriya_klaviaturasi())

@rr.message(F.text == "⚙️ Admin sozlamalari")
async def admin_sozlamalar(message: Message):
    """Admin sozlamalari menyusi"""
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    admin_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Parolni o'zgartirish")],
            [KeyboardButton(text="📢 Reklama yuborish")],
            [KeyboardButton(text="📝 Matnlarni tahrirlash")],
            [KeyboardButton(text="🗑 Ma'lumotlarni tozalash")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

    sozlamalar_matni = (
        "⚙️ Admin sozlamalari:\n\n"
        "🔑 Parolni o'zgartirish - Admin parolini yangilash\n"
        "📢 Reklama yuborish - Barcha foydalanuvchilarga xabar\n"
        "📝 Matnlarni tahrirlash - Bot matnlarini o'zgartirish\n"
        "🗑 Ma'lumotlarni tozalash - Savatlar va eskirgan buyurtmalarni o'chirish\n"
    )

    await message.answer(sozlamalar_matni, reply_markup=admin_menu)

@rr.message(F.text == "🔑 Parolni o'zgartirish")
async def parol_ozgartirish_boshlash(message: Message, state: FSMContext):
    """Parol o'zgartirish jarayonini boshlash"""
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    await state.set_state(ParolOzgartirish.eski_parol)

    bekor_menu = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

    await message.answer(
        "🔐 Eski parolni kiriting:",
        reply_markup=bekor_menu
    )


@rr.message(StateFilter(ParolOzgartirish.eski_parol))
async def eski_parol_tekshir(message: Message, state: FSMContext):
    """Eski parolni tekshirish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Parol o'zgartirish bekor qilindi.")
        await admin_sozlamalar(message)
        return

    eski_parol = (message.text or "").strip()

    if eski_parol != matn_olish("parol"):
        await message.answer("❌ Noto'g'ri parol! Qayta kiriting:")
        return

    await state.set_state(ParolOzgartirish.yangi_parol)
    await message.answer(
        "✅ Parol to'g'ri.\n\n"
        "🔑 Yangi parolni kiriting (kamida 6 ta belgi):"
    )


@rr.message(StateFilter(ParolOzgartirish.yangi_parol))
async def yangi_parol_kiritish(message: Message, state: FSMContext):
    """Yangi parolni qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Parol o'zgartirish bekor qilindi.")
        await admin_sozlamalar(message)
        return

    yangi_parol = (message.text or "").strip()

    if len(yangi_parol) < 6:
        await message.answer("❌ Parol kamida 6 ta belgidan iborat bo'lishi kerak!")
        return

    await state.update_data(yangi_parol=yangi_parol)
    await state.set_state(ParolOzgartirish.tasdiqlash)
    await message.answer("🔁 Yangi parolni qayta kiriting (tasdiqlash uchun):")


@rr.message(StateFilter(ParolOzgartirish.tasdiqlash))
async def parol_tasdiqlash(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Parol o'zgartirish bekor qilindi.")
        await admin_sozlamalar(message)
        return

    tasdiqlash = (message.text or "").strip()
    holat_malumoti = await state.get_data()
    yangi_parol = holat_malumoti.get("yangi_parol")

    if tasdiqlash != yangi_parol:
        await message.answer("❌ Parollar mos kelmadi! Qayta kiriting:")
        return

    malumot = malumot_yuklash(malumotlar_fayli)
    malumot["matnlar"]["parol"] = yangi_parol

    if malumot_saqlash(malumot, malumotlar_fayli):
        await state.clear()
        await message.answer(
            "✅ Parol muvaffaqiyatli o'zgartirildi!\n\n"
            f"🔑 Yangi parol: {yangi_parol}"
        )
        await admin_sozlamalar(message)
    else:
        await message.answer("❌ Parolni saqlashda xatolik yuz berdi!")


@rr.message(F.text == "📢 Reklama yuborish")
async def reklama_boshlash(message: Message, state: FSMContext):
    """Reklama yuborish jarayonini boshlash"""
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    await state.set_state(ReklamaYuborish.xabar_kutish)

    bekor_menu = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:\n\n"
        "💡 Xabar matn, rasm yoki video bo'lishi mumkin.",
        reply_markup=bekor_menu
    )


@rr.message(StateFilter(ReklamaYuborish.xabar_kutish))
async def reklama_xabar_qabul(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Reklama yuborish bekor qilindi.")
        await admin_sozlamalar(message)
        return

    xabar_matni = message.text or message.caption

    if not xabar_matni and not message.photo and not message.video:
        await message.answer("❌ Xabar bo'sh bo'lishi mumkin emas! Matn, rasm yoki video yuboring.")
        return

    await state.update_data(
        xabar_matni=xabar_matni or "",
        xabar_turi="text" if message.text else "media",
        media_id=message.photo[-1].file_id if message.photo else (
            message.video.file_id if message.video else None
        ),
        media_turi="photo" if message.photo else ("video" if message.video else None)
    )

    malumot = malumot_yuklash(foydalanuvchilar_fayli)
    foydalanuvchilar_soni = len(malumot.get("foydalanuvchilar", []))

    tasdiqlash_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, yuborish")],
            [KeyboardButton(text="❌ Yo'q, bekor qilish")]
        ],
        resize_keyboard=True
    )

    await state.set_state(ReklamaYuborish.tasdiqlash)
    await message.answer(
        f"📊 Xabar {foydalanuvchilar_soni} ta foydalanuvchiga yuboriladi.\n\n"
        "❓ Davom ettirasizmi?",
        reply_markup=tasdiqlash_menu
    )

@rr.message(StateFilter(ReklamaYuborish.tasdiqlash))
async def reklama_yuborish_tasdiqlash(message: Message, state: FSMContext):
    """Reklamani yuborishni tasdiqlash va yuborish"""
    if message.text != "✅ Ha, yuborish":
        await state.clear()
        await message.answer("❌ Reklama yuborish bekor qilindi.")
        await admin_sozlamalar(message)
        return

    holat_malumoti = await state.get_data()
    malumot = malumot_yuklash(foydalanuvchilar_fayli)
    foydalanuvchilar = malumot.get("foydalanuvchilar", [])

    await message.answer("⏳ Xabar yuborilmoqda...")

    muvaffaqiyatli = 0
    xatolik = 0

    for foydalanuvchi in foydalanuvchilar:
        try:
            if holat_malumoti["xabar_turi"] == "text":
                await message.bot.send_message(
                    foydalanuvchi["id"],
                    holat_malumoti["xabar_matni"]
                )
            elif holat_malumoti["media_turi"] == "photo":
                await message.bot.send_photo(
                    foydalanuvchi["id"],
                    holat_malumoti["media_id"],
                    caption=holat_malumoti["xabar_matni"]
                )
            elif holat_malumoti["media_turi"] == "video":
                await message.bot.send_video(
                    foydalanuvchi["id"],
                    holat_malumoti["media_id"],
                    caption=holat_malumoti["xabar_matni"]
                )
            muvaffaqiyatli += 1
        except Exception as e:
            logger.error(f"Foydalanuvchi {foydalanuvchi['id']} ga xabar yuborishda xatolik: {e}")
            xatolik += 1

    await state.clear()
    await message.answer(
        f"✅ Reklama yuborish yakunlandi!\n\n"
        f"📊 Statistika:\n"
        f"✅ Muvaffaqiyatli: {muvaffaqiyatli}\n"
        f"❌ Xatolik: {xatolik}"
    )
    await admin_sozlamalar(message)


@rr.message(F.text == "🗑 Ma'lumotlarni tozalash")
async def malumotlar_tozalash_menyu(message: Message):
    """Ma'lumotlarni tozalash menyusi"""
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    tozalash_menu = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Bo'sh savatlarni tozalash",
                                  callback_data="clean_empty_carts")],
            [InlineKeyboardButton(text="📋 Eski buyurtmalarni arxivlash",
                                  callback_data="archive_old_orders")],
            [InlineKeyboardButton(text="🗑 Bekor qilingan buyurtmalarni o'chirish",
                                  callback_data="delete_cancelled_orders")],
            [InlineKeyboardButton(text="❌ Bekor qilish",
                                  callback_data="cancel_cleaning")]
        ]
    )

    await message.answer(
        "🗑 Ma'lumotlarni tozalash:\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=tozalash_menu
    )


@rr.callback_query(F.data == "clean_empty_carts")
async def bosh_savatlar_tozalash(callback: CallbackQuery):
    """Bo'sh savatlarni tozalash"""
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    malumot = malumot_yuklash(malumotlar_fayli)
    savatlar = malumot.get("savatlar", {})

    bosh_savatlar = [k for k, v in savatlar.items() if not v]

    for savat_id in bosh_savatlar:
        del savatlar[savat_id]

    malumot_saqlash(malumot, malumotlar_fayli)

    await callback.answer(f"✅ {len(bosh_savatlar)} ta bo'sh savat tozalandi!", show_alert=True)
    await callback.message.edit_text(f"✅ {len(bosh_savatlar)} ta bo'sh savat tozalandi!")


@rr.callback_query(F.data == "delete_cancelled_orders")
async def bekor_buyurtmalar_ochirish(callback: CallbackQuery):
    """Bekor qilingan buyurtmalarni o'chirish"""
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    malumot = malumot_yuklash(malumotlar_fayli)
    buyurtmalar = malumot.get("buyurtmalar", [])

    bekor_qilingan = [b for b in buyurtmalar if b.get("status") == "cancelled"]
    malumot["buyurtmalar"] = [b for b in buyurtmalar if b.get("status") != "cancelled"]

    malumot_saqlash(malumot, malumotlar_fayli)

    await callback.answer(f"✅ {len(bekor_qilingan)} ta bekor qilingan buyurtma o'chirildi!", show_alert=True)
    await callback.message.edit_text(f"✅ {len(bekor_qilingan)} ta bekor qilingan buyurtma o'chirildi!")


@rr.callback_query(F.data == "cancel_cleaning")
async def tozalash_bekor(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("❌ Amal bekor qilindi")


@rr.message(F.text == "⬅️ Orqaga")
async def sozlamalardan_orqaga(message: Message, state: FSMContext):
    joriy_holat = await state.get_state()

    if joriy_holat:
        await state.clear()
        await admin_sozlamalar(message)
    else:
        await admin_menyuni_korsat(message)


@rr.callback_query(F.data == "admin_products_menu")
async def admin_mahsulotlar_menyu_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    await callback.message.answer("Kategoriya tanlang:", reply_markup=kategoriya_klaviaturasi())
    await callback.answer()


@rr.callback_query(F.data.startswith("admin_category:"))
async def admin_kategoriya_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    _, kategoriya_kaliti = callback.data.split(":")
    matn, klaviatura = kategoriya_mahsulotlar_korsatish(kategoriya_kaliti)
    if not matn or not klaviatura:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    await callback.message.answer(matn, reply_markup=klaviatura)
    await callback.answer()


@rr.callback_query(F.data.startswith("admin_product:"))
async def admin_mahsulot_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, kategoriya_kaliti, mahsulot_kaliti = callback.data.split(":")
    except ValueError:
        await callback.answer("❌ Ma'lumotda xatolik.", show_alert=True)
        return

    mahsulot = get_product(kategoriya_kaliti, mahsulot_kaliti)
    kategoriyalar = get_categories()
    kategoriya = kategoriyalar.get(kategoriya_kaliti)

    if not mahsulot or not kategoriya:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return

    klaviatura = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Nom",
                    callback_data=f"admin_edit_field:name:{kategoriya_kaliti}:{mahsulot_kaliti}"
                ),
                InlineKeyboardButton(
                    text="📝 Tavsif",
                    callback_data=f"admin_edit_field:description:{kategoriya_kaliti}:{mahsulot_kaliti}"
                ),
                InlineKeyboardButton(
                    text="💰 Narx",
                    callback_data=f"admin_edit_field:price:{kategoriya_kaliti}:{mahsulot_kaliti}"
                )
            ],
            [InlineKeyboardButton(
                text="🗑 Mahsulotni o'chirish",
                callback_data=f"admin_delete_product:{kategoriya_kaliti}:{mahsulot_kaliti}"
            )],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_category:{kategoriya_kaliti}")],
            [InlineKeyboardButton(text="🏠 Kategoriyalar", callback_data="admin_products_menu")]
        ]
    )

    await callback.message.answer(mahsulot_malumot_matni(kategoriya["name"], mahsulot), reply_markup=klaviatura)
    await callback.answer()


@rr.callback_query(F.data.startswith("admin_delete_product:"))
async def admin_mahsulot_ochirish_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, kategoriya_kaliti, mahsulot_kaliti = callback.data.split(":")
    except ValueError:
        await callback.answer("❌ Ma'lumotda xatolik.", show_alert=True)
        return

    mahsulot = get_product(kategoriya_kaliti, mahsulot_kaliti)
    if not mahsulot:
        await callback.answer("❌ Mahsulot topilmadi.", show_alert=True)
        return

    klaviatura = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, o'chirish",
                    callback_data=f"admin_delete_confirm:{kategoriya_kaliti}:{mahsulot_kaliti}"
                ),
                InlineKeyboardButton(
                    text="❌ Yo'q",
                    callback_data=f"admin_product:{kategoriya_kaliti}:{mahsulot_kaliti}"
                )
            ]
        ]
    )

    await callback.message.answer(
        f"🗑 '{mahsulot['name']}' mahsulotini o'chirishni tasdiqlaysizmi?",
        reply_markup=klaviatura
    )
    await callback.answer()


@rr.callback_query(F.data.startswith("admin_delete_confirm:"))
async def admin_ochirish_tasdiqlash_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    try:
        _, kategoriya_kaliti, mahsulot_kaliti = callback.data.split(":")
    except ValueError:
        await callback.answer("❌ Ma'lumotda xatolik.", show_alert=True)
        return

    if delete_product(kategoriya_kaliti, mahsulot_kaliti):
        await callback.answer("✅ Mahsulot o'chirildi.", show_alert=True)
        matn, klaviatura = kategoriya_mahsulotlar_korsatish(kategoriya_kaliti)
        if matn and klaviatura:
            await callback.message.answer(matn, reply_markup=klaviatura)
    else:
        await callback.answer("❌ Mahsulotni o'chirib bo'lmadi.", show_alert=True)


@rr.callback_query(F.data.startswith("admin_add_product:"))
async def admin_mahsulot_qoshish_callback(callback: CallbackQuery, state: FSMContext):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, kategoriya_kaliti = callback.data.split(":")
    except ValueError:
        await callback.answer("❌ Kategoriya ma'lumotida xatolik.", show_alert=True)
        return

    kategoriyalar = get_categories()
    if kategoriya_kaliti not in kategoriyalar:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    await state.set_state(MahsulotQoshish.malumot_kutish)
    await state.update_data(kategoriya_kaliti=kategoriya_kaliti)

    korinma = (
        "➕ Yangi mahsulot qo'shish.\n"
        "Quyidagi formatda matn yuboring:\n"
        "Nom | Tavsif | Narx\n\n"
        "Misol: Klassik Burger | Go'sht, pishloq | 25000"
    )
    await callback.message.answer(korinma)
    await callback.answer("✏️ Ma'lumotni yuboring.")


@rr.message(StateFilter(MahsulotQoshish.malumot_kutish))
async def mahsulot_qoshish_qiymat(message: Message, state: FSMContext):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        await state.clear()
        return

    malumot = (message.text or "").strip()
    if malumot.lower() in {"/cancel", "bekor", "❌ bekor qilish"}:
        await message.answer("❌ Mahsulot qo'shish bekor qilindi.")
        await state.clear()
        return

    holat_malumoti = await state.get_data()
    kategoriya_kaliti = holat_malumoti.get("kategoriya_kaliti")
    if not kategoriya_kaliti:
        await message.answer("❌ Kategoriya ma'lumotlari topilmadi.")
        await state.clear()
        return

    qismlar = [qism.strip() for qism in malumot.split("|")]
    if len(qismlar) < 3:
        await message.answer("❌ Format noto'g'ri. 'Nom | Tavsif | Narx' ko'rinishida yuboring.")
        return

    nom, tavsif, narx_matni = qismlar[0], qismlar[1], qismlar[2]
    if len(nom) < 3 or len(tavsif) < 5:
        await message.answer("❌ Nom yoki tavsif juda qisqa. Qayta kiriting.")
        return

    try:
        narx = int(narx_matni)
        if narx <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Narx faqat musbat butun son bo'lishi kerak.")
        return

    mahsulot = add_product(kategoriya_kaliti, nom, tavsif, narx)
    if mahsulot:
        await message.answer(f"✅ '{nom}' mahsuloti qo'shildi!")
        matn, klaviatura = kategoriya_mahsulotlar_korsatish(kategoriya_kaliti)
        if matn and klaviatura:
            await message.answer(matn, reply_markup=klaviatura)
    else:
        await message.answer("❌ Mahsulotni qo'shishda xatolik yuz berdi.")

    await state.clear()


@rr.callback_query(F.data.startswith("admin_edit_field:"))
async def admin_maydon_tahrirlash_callback(callback: CallbackQuery, state: FSMContext):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, maydon, kategoriya_kaliti, mahsulot_kaliti = callback.data.split(":")
    except ValueError:
        await callback.answer("❌ Ma'lumotda xatolik.", show_alert=True)
        return

    if maydon not in {"name", "description", "price"}:
        await callback.answer("❌ Maydonni tahrirlab bo'lmaydi.", show_alert=True)
        return

    sorovlar = {
        "name": "Yangi nomni kiriting:",
        "description": "Yangi tavsifni kiriting:",
        "price": "Yangi narxni kiriting (butun so'mlarda):"
    }

    await state.set_state(MahsulotTahrir.qiymat_kutish)
    await state.update_data(
        kategoriya_kaliti=kategoriya_kaliti,
        mahsulot_kaliti=mahsulot_kaliti,
        maydon=maydon
    )

    await callback.message.answer(sorovlar[maydon])
    await callback.answer("✏️ Ma'lumot yuboring.")


@rr.message(StateFilter(MahsulotTahrir.qiymat_kutish))
async def mahsulot_tahrir_qiymat(message: Message, state: FSMContext):
    if not admin_tekshir(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        await state.clear()
        return

    foydalanuvchi_kiritgan = (message.text or "").strip()
    if foydalanuvchi_kiritgan.lower() in {"/cancel", "bekor", "❌ bekor qilish"}:
        await message.answer("❌ Mahsulotni tahrirlash bekor qilindi.")
        await state.clear()
        return

    holat_malumoti = await state.get_data()
    kategoriya_kaliti = holat_malumoti.get("kategoriya_kaliti")
    mahsulot_kaliti = holat_malumoti.get("mahsulot_kaliti")
    maydon = holat_malumoti.get("maydon")

    if not all([kategoriya_kaliti, mahsulot_kaliti, maydon]):
        await message.answer("❌ Tahrirlash ma'lumotlari topilmadi.")
        await state.clear()
        return

    if maydon == "price":
        try:
            yangi_qiymat = int(foydalanuvchi_kiritgan)
            if yangi_qiymat <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Narx faqat musbat butun son bo'lishi kerak. Qayta kiriting.")
            return
    else:
        if len(foydalanuvchi_kiritgan) < 3:
            await message.answer("❌ Matn juda qisqa. Qayta kiriting.")
            return
        yangi_qiymat = foydalanuvchi_kiritgan

    if update_product_field(kategoriya_kaliti, mahsulot_kaliti, maydon, yangi_qiymat):
        mahsulot = get_product(kategoriya_kaliti, mahsulot_kaliti)
        kategoriyalar = get_categories()
        kategoriya_nomi = kategoriyalar.get(kategoriya_kaliti, {}).get("name", "Kategoriya")

        maydon_nomlari = {
            "name": "Nom",
            "description": "Tavsif",
            "price": "Narx"
        }

        await message.answer(f"✅ {maydon_nomlari.get(maydon, maydon)} muvaffaqiyatli yangilandi!")
        klaviatura = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Nom",
                                         callback_data=f"admin_edit_field:name:{kategoriya_kaliti}:{mahsulot_kaliti}"),
                    InlineKeyboardButton(text="📝 Tavsif",
                                         callback_data=f"admin_edit_field:description:{kategoriya_kaliti}:{mahsulot_kaliti}"),
                    InlineKeyboardButton(text="💰 Narx",
                                         callback_data=f"admin_edit_field:price:{kategoriya_kaliti}:{mahsulot_kaliti}")
                ],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_category:{kategoriya_kaliti}")],
                [InlineKeyboardButton(text="🏠 Kategoriyalar", callback_data="admin_products_menu")]
            ]
        )
        await message.answer(mahsulot_malumot_matni(kategoriya_nomi, mahsulot), reply_markup=klaviatura)
    else:
        await message.answer("❌ Mahsulotni yangilab bo'lmadi. Qayta urinib ko'ring.")

    await state.clear()


@rr.callback_query(F.data.startswith("admin_accept_order:"))
async def admin_buyurtma_qabul_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, buyurtma_id_str = callback.data.split(":")
        buyurtma_id = int(buyurtma_id_str)
    except (ValueError, AttributeError):
        await callback.answer("❌ Buyurtma ma'lumotida xatolik.", show_alert=True)
        return

    buyurtma = buyurtma_olish(buyurtma_id)
    if not buyurtma:
        await callback.answer("❌ Buyurtma topilmadi.", show_alert=True)
        return

    if buyurtma["status"] != "pending":
        await callback.answer("ℹ️ Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    if buyurtma_holat_yangilash(buyurtma_id, "accepted"):
        buyurtma["status"] = "accepted"
        await callback.answer("✅ Buyurtma qabul qilindi.")
        await callback.message.edit_text(admin_buyurtma_xulosa(buyurtma))
        bot = callback.message.bot if callback.message else None
        if bot:
            await foydalanuvchiga_xabar(bot, buyurtma, "✅ Buyurtma qabul qilindi!")
    else:
        await callback.answer("❌ Buyurtma holatini yangilab bo'lmadi.", show_alert=True)


@rr.callback_query(F.data.startswith("admin_decline_order:"))
async def admin_buyurtma_bekor_callback(callback: CallbackQuery):
    if not admin_tekshir(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    try:
        _, buyurtma_id_str = callback.data.split(":")
        buyurtma_id = int(buyurtma_id_str)
    except (ValueError, AttributeError):
        await callback.answer("❌ Buyurtma ma'lumotida xatolik.", show_alert=True)
        return

    buyurtma = buyurtma_olish(buyurtma_id)
    if not buyurtma:
        await callback.answer("❌ Buyurtma topilmadi.", show_alert=True)
        return

    if buyurtma["status"] == "cancelled":
        await callback.answer("ℹ️ Buyurtma allaqachon bekor qilingan.", show_alert=True)
        return

    if buyurtma_holat_yangilash(buyurtma_id, "cancelled"):
        buyurtma["status"] = "cancelled"
        await callback.answer("❌ Buyurtma bekor qilindi.")
        await callback.message.edit_text(admin_buyurtma_xulosa(buyurtma))

        bot = callback.message.bot
        await foydalanuvchiga_xabar(
            bot,
            buyurtma,
            "❌ Buyurtmangiz bekor qilindi",
            "Agar savollaringiz bo'lsa operator bilan bog'laning."
        )
    else:
        await callback.answer("❌ Buyurtmani bekor qilib bo'lmadi.", show_alert=True)


def admin_login(dp):
    dp.include_router(rr)
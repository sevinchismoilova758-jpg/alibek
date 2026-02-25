import logging
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    FSInputFile, CallbackQuery

from data import (
    foydalanuvchi_olish, foydalanuvchi_saqlash, matn_olish, menyu_olish,
    kategoriyalar_olish, savat_olish, foydalanuvchi_buyurtmalari,
    admin_tekshir, foydalanuvchi_tozalash, get_categories,
    get_category_products, get_product, savat_qoshish, buyurtma_yaratish,
    savat_tozalash, buyurtma_bekor_qilish
)

logger = logging.getLogger(__name__)

rr = Router()


class RoyxatHolatlari(StatesGroup):
    telefon = State()
    manzil = State()


@rr.message(Command('start'))
async def boshlash_buyrugi(message: Message, state: FSMContext) -> None:
    await state.clear()

    foydalanuvchi_id = message.from_user.id
    foydalanuvchi = foydalanuvchi_olish(foydalanuvchi_id)

    if foydalanuvchi and foydalanuvchi.get('telefon') and foydalanuvchi.get('manzil'):
        if admin_tekshir(foydalanuvchi_id):
            from admin import admin_menyuni_korsat
            await admin_menyuni_korsat(message)
        else:
            await foydalanuvchi_menyusi(message)
    else:
        await message.answer(
            matn_olish("boshlash"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=matn_olish("telefon_url"), request_contact=True)]],
                resize_keyboard=True
            )
        )
        await state.set_state(RoyxatHolatlari.telefon)


@rr.message(StateFilter(RoyxatHolatlari.telefon))
async def telefon_qabul(message: Message, state: FSMContext):
    if message.contact:
        telefon = message.contact.phone_number
        await state.update_data(telefon=telefon)

        await message.answer(
            matn_olish('manzil_sorash'),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=matn_olish('manzil_url'), request_location=True)]],
                resize_keyboard=True
            )
        )
        await state.set_state(RoyxatHolatlari.manzil)
    else:
        await message.answer(matn_olish("telefon_xato"))


@rr.message(StateFilter(RoyxatHolatlari.manzil))
async def manzil_qabul(message: Message, state: FSMContext):
    foydalanuvchi_malumot = await state.get_data()
    telefon = foydalanuvchi_malumot.get('telefon')

    if message.location:
        manzil = f"{message.location.latitude}, {message.location.longitude}"
    elif message.text and len(message.text) > 10:
        manzil = message.text
    else:
        await message.answer(matn_olish("manzil_xato"))
        return

    saqlandi = foydalanuvchi_saqlash(
        foydalanuvchi_id=message.from_user.id,
        foydalanuvchi_nomi=message.from_user.username,
        toliq_ism=message.from_user.full_name,
        telefon=telefon,
        manzil=manzil
    )

    if saqlandi:
        await message.answer(matn_olish('royxat_muvaffaqiyat'))
        await state.clear()
        if admin_tekshir(message.from_user.id):
            from admin import admin_menyuni_korsat
            await admin_menyuni_korsat(message)
        else:
            await foydalanuvchi_menyusi(message)
    else:
        await message.answer(matn_olish('royxat_xato'))


async def foydalanuvchi_menyusi(message):
    menyu = menyu_olish("asosiy")
    klaviatura = []
    for kalit, matn in menyu.items():
        klaviatura.append([KeyboardButton(text=matn)])

    await message.answer(
        matn_olish('asosiy_menyu'),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=klaviatura,
            resize_keyboard=True
        ))


def holat_formatlash(holat: str) -> str:
    return menyu_olish("holat").get(holat, holat)


def buyurtma_xulosa_yaratish(buyurtma: Dict[str, Any]) -> str:
    holat_matni = holat_formatlash(buyurtma.get("status", ""))
    yaratilgan = (buyurtma.get("created_at") or "")[:10]
    return (
        f"🆔 Buyurtma #{buyurtma.get('id')}\n"
        f"💰 Jami: {buyurtma.get('total')} so'm\n"
        f"📊 Holat: {holat_matni}\n"
        f"📅 Sana: {yaratilgan}\n"
    )


Menyular = list(menyu_olish("asosiy").values())


@rr.message(F.text.in_(Menyular))
async def menyu_buyruq(message: Message):
    matn = message.text
    orqaga = KeyboardButton(text=matn_olish("orqaga"))

    if matn == Menyular[0]:
        kategoriyalar = kategoriyalar_olish()
        klaviatura = []

        for kalit, kategoriya in kategoriyalar.items():
            klaviatura.append([KeyboardButton(text=kategoriya["nomi"])])

        klaviatura.append([orqaga])

        await message.answer(
            matn_olish("kategoriya_tanlash"),
            reply_markup=ReplyKeyboardMarkup(keyboard=klaviatura, resize_keyboard=True)
        )
    elif matn == Menyular[1]:
        savat = savat_olish(message.from_user.id)
        menyu = menyu_olish("savat")
        klaviatura = []
        for kalit, matn_menyu in menyu.items():
            klaviatura.append([KeyboardButton(text=matn_menyu)])
        klaviatura.append([orqaga])

        if not savat:
            await message.answer(matn_olish("savat_bosh"))
            return

        savat_matni = "🛒 Savatingiz:\n\n"
        jami = 0

        for mahsulot in savat.values():
            mahsulot_jami = mahsulot["price"] * mahsulot["quantity"]
            jami += mahsulot_jami
            savat_matni += f"🍔 {mahsulot['name']}\n"
            savat_matni += f"💰 {mahsulot['price']} so'm x {mahsulot['quantity']} = {mahsulot_jami} so'm\n\n"

        savat_matni += f"💰 Jami: {jami} so'm"

        await message.answer(
            savat_matni,
            reply_markup=ReplyKeyboardMarkup(keyboard=klaviatura, resize_keyboard=True)
        )
    elif matn == Menyular[2]:
        buyurtmalar = foydalanuvchi_buyurtmalari(message.from_user.id)
        if not buyurtmalar:
            await message.answer("📋 Sizda hali buyurtmalar yo'q")
            return
        buyurtmalar_matni = "📋 Sizning buyurtmalaringiz:\n\n"

        for buyurtma in buyurtmalar[-5:]:
            buyurtmalar_matni += buyurtma_xulosa_yaratish(buyurtma) + "\n"
        await message.answer(buyurtmalar_matni)
    elif matn == Menyular[3]:
        await message.answer(matn_olish("aloqa_malumot"))
    elif matn == Menyular[4]:
        await message.answer(matn_olish("haqida_malumot"))
    elif matn == Menyular[5]:
        menyu = menyu_olish("foydalanuvchi_amallar")
        klaviatura = []
        for kalit, matn_menyu in menyu.items():
            klaviatura.append([KeyboardButton(text=matn_menyu)])
        klaviatura.append([orqaga])
        await message.answer(
            matn_olish('sozlamalar_menyu'),
            reply_markup=ReplyKeyboardMarkup(keyboard=klaviatura, resize_keyboard=True)
        )


@rr.message(F.text == matn_olish('orqaga'))
async def orqaga_buyruq(message: Message):
    await foydalanuvchi_menyusi(message)


MenyuSozlama = list(menyu_olish("foydalanuvchi_amallar").values())
@rr.message(F.text.in_(MenyuSozlama))
async def menyu_sozlama(message: Message, state: FSMContext):
    matn = message.text
    if matn == MenyuSozlama[0]:
        foydalanuvchi_tozalash(message.from_user.id)
        await state.clear()

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
            resize_keyboard=True
        )

        await message.answer("♻️ Ro'yxatdan qayta o'tish boshlandi. Iltimos, telefon raqamingizni yuboring.",
                             reply_markup=keyboard)
        await state.set_state(RoyxatHolatlari.telefon)
    elif matn == MenyuSozlama[1]:
        buyurtmalar = foydalanuvchi_buyurtmalari(message.from_user.id)
        bekor_qilinadigan = [buyurtma for buyurtma in buyurtmalar if
                             buyurtma["status"] not in {"cancelled", "completed"}]

        if not bekor_qilinadigan:
            await message.answer("❌ Bekor qilinadigan buyurtmalar topilmadi.")
            return

        klaviatura_qatorlar = []
        for buyurtma in bekor_qilinadigan:
            holat_matni = holat_formatlash(buyurtma["status"])
            tugma_matni = f"#{buyurtma['id']} - {buyurtma['total']} so'm ({holat_matni})"
            klaviatura_qatorlar.append(
                [InlineKeyboardButton(text=tugma_matni, callback_data=f"cancel_order:{buyurtma['id']}")])

        klaviatura_qatorlar.append(
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel_order_menu_close")])

        klaviatura = InlineKeyboardMarkup(inline_keyboard=klaviatura_qatorlar)

        await message.answer("Bekor qilmoqchi bo'lgan buyurtmani tanlang:", reply_markup=klaviatura)


Mahsulot = list({key: val["nomi"] for key, val in kategoriyalar_olish().items()}.values())


@rr.message(F.text.in_(Mahsulot))
async def mahsulot_korsatish(message: Message):
    kategoriyalar = get_categories()
    kategoriya_nomi = message.text

    kategoriya_kaliti = None
    for kalit, kategoriya in kategoriyalar.items():
        if kategoriya["name"] == kategoriya_nomi:
            kategoriya_kaliti = kalit
            break

    if not kategoriya_kaliti:
        await message.answer("❌ Kategoriya topilmadi")
        return

    mahsulotlar = get_category_products(kategoriya_kaliti)
    kategoriya = kategoriyalar[kategoriya_kaliti]

    mahsulotlar_matni = f"{kategoriya_nomi}\n\n"
    klaviatura_tugmalari = []

    for i, (kalit, mahsulot) in enumerate(mahsulotlar.items(), 1):
        mahsulotlar_matni += f"{i}. {mahsulot['name']}\n"
        mahsulotlar_matni += f"   {mahsulot['description']}\n"
        mahsulotlar_matni += f"   💰 {mahsulot['price']} so'm\n\n"

        klaviatura_tugmalari.append(
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"add_to_cart:{kategoriya_kaliti}:{kalit}"
            )
        )

    klaviatura = InlineKeyboardMarkup(inline_keyboard=[])
    klaviatura.inline_keyboard.append(klaviatura_tugmalari)
    klaviatura.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])

    try:
        rasm = FSInputFile(kategoriya["image"])
        await message.answer_photo(
            photo=rasm,
            caption=mahsulotlar_matni,
            reply_markup=klaviatura
        )
    except:
        await message.answer(
            mahsulotlar_matni,
            reply_markup=klaviatura
        )


@rr.message(F.text == "💳 Buyurtma berish")
async def buyurtma_berish(message: Message):
    savat = savat_olish(message.from_user.id)

    if not savat:
        await message.answer(matn_olish("savat_bosh"))
        return

    buyurtma = buyurtma_yaratish(message.from_user.id)

    if buyurtma:
        buyurtma_matni = f"✅ {matn_olish('buyurtma_qabul')}\n\n"
        buyurtma_matni += f"🆔 Buyurtma raqami: #{buyurtma['id']}\n"
        buyurtma_matni += f"💰 Jami: {buyurtma['total']} so'm\n"
        buyurtma_matni += f"📊 Holat: {holat_formatlash(buyurtma['status'])}\n\n"
        buyurtma_matni += "Tez orada siz bilan bog'lanamiz!"

        await message.answer(buyurtma_matni)
        await foydalanuvchi_menyusi(message)
    else:
        await message.answer("❌ Buyurtma yaratishda xatolik!")


@rr.message(F.text == "🗑 Savatni tozalash")
async def savat_tozalash_buyruq(message: Message):
    savat_tozalash(message.from_user.id)
    await message.answer("✅ Savat tozalandi")
    await foydalanuvchi_menyusi(message)


@rr.callback_query(F.data.startswith("add_to_cart:"))
async def savatga_qoshish_callback(callback: CallbackQuery):
    try:
        _, kategoriya, mahsulot_kaliti = callback.data.split(":")

        if savat_qoshish(callback.from_user.id, kategoriya, mahsulot_kaliti):
            mahsulot = get_product(kategoriya, mahsulot_kaliti)
            await callback.answer(f"✅ {mahsulot['name']} savatga qo'shildi!")
        else:
            await callback.answer("❌ Xatolik yuz berdi!")
    except Exception as e:
        logger.error(f"Callback xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")


@rr.callback_query(F.data == "cancel")
async def bekor_qilish_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("❌ Bekor qilindi")


@rr.callback_query(F.data.startswith("cancel_order:"))
async def buyurtma_bekor_callback(callback: CallbackQuery):
    try:
        _, buyurtma_id_str = callback.data.split(":")
        buyurtma_id = int(buyurtma_id_str)
    except (ValueError, IndexError):
        await callback.answer("❌ Buyurtma ma'lumotida xatolik.", show_alert=True)
        return

    if buyurtma_bekor_qilish(buyurtma_id, callback.from_user.id):
        await callback.answer("✅ Buyurtma bekor qilindi.", show_alert=True)
        await callback.message.edit_text(f"✅ Buyurtma #{buyurtma_id} bekor qilindi.")
    else:
        await callback.answer("❌ Bu buyurtmani bekor qilib bo'lmaydi.", show_alert=True)


@rr.callback_query(F.data == "cancel_order_menu_close")
async def buyurtma_bekor_menyu_yopish(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("❌ Amal bekor qilindi.")


def user_login(dp):
    dp.include_router(rr)
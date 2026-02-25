import json
import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)
foydalanuvchilar_fayli = 'users.json'
malumotlar_fayli = 'data.json'


def standart_kategoriyalar() -> Dict[str, Any]:
    return {
        "matnlar": {
            "boshlash": "🍔 Fast-cooking botiga xush kelibsiz!\n\nBizning bot orqali eng mazali burgerlarni buyurtma qiling!",
            "telefon_sorash": "📱 Telefon raqamingizni yuboring:",
            "telefon_url": "📱 Telefon raqamni yuborish",
            "telefon_xato": "❌ Iltimos, telefon raqamingizni yuboring!",
            "manzil_sorash": "📍 Manzilingizni kiriting:",
            "manzil_url": "📍 Manzilni yuborish",
            "manzil_xato": "❌ Iltimos, to'liq manzil kiriting!",
            "royxat_muvaffaqiyat": "✅ Ro'yxatga muvaffaqiyatli qo'shildingiz!",
            "royxat_xato": "❌ Ro'yxatga qo'shilmadi!",
            "asosiy_menyu": "🏠 Asosiy menyu",
            "kategoriya_tanlash": "🍽 Kategoriyani tanlang:",
            "savat_bosh": "🛒 Savatingiz bo'sh",
            "sozlamalar_menyu": "⚙️ Sozlamalar bo'limi:\n\nKerakli amalni tanlang.",
            "buyurtma_qabul": "Buyurtma qabul qilindi!",
            "admin_xush": "👨‍💼 Admin panelga xush kelibsiz!",
            "aloqa_malumot": "📞 Biz bilan bog'lanish:\n\n📱 Telefon: +998 90 123 45 67\n📧 Email: info@burgerhouse.uz\n📍 Manzil: Toshkent sh., Amir Temur ko'chasi 1-uy",
            "haqida_malumot": "🏪 Burger House haqida:\n\nBiz 2020 yildan beri eng mazali burgerlarni tayyorlaymiz. Bizning maqsadimiz - har bir mijozga sifatli va mazali taom yetkazish.",
            "orqaga": "⬅️ Orqaga",
            "parol": "123456789"
        },
        "menyu": {
            "asosiy": {
                "dokon": "🍽 Do'kon",
                "savat": "🛒 Savat",
                "buyurtmalar": "📖 Mening buyurtmalarim",
                "aloqa": "📞 Biz bilan bog'lanish",
                "haqida": "ℹ️ Biz haqimizda",
                "sozlamalar": "⚙️ Sozlamalar"
            },
            "admin": {
                "buyurtmalar": "📋 Buyurtmalar",
                "foydalanuvchilar": "👥 Foydalanuvchilar",
                "statistika": "📊 Statistika",
                "mahsulotlar": "🍔 Mahsulotlar",
                "sozlamalar": "⚙️ Admin sozlamalari"
            },
            "foydalanuvchi_amallar": {
                "qayta_royxat": "♻️ Qayta ro'yxatdan o'tish",
                "buyurtma_bekor": "❌ Buyurtmani bekor qilish"
            },
            "savat": {
                "tolov": "💳 Buyurtma berish",
                "tozalash": "🗑 Savatni tozalash"
            },
            "holat": {
                "pending": "kutilmoqda",
                "accepted": "qabul qilindi",
                "processing": "tayyorlanmoqda",
                "completed": "yakunlangan",
                "cancelled": "bekor qilingan"
            }
        },
        "kategoriyalar": {
            "burgerlar": {
                "nomi": "🍔 Burgerlar",
                "rasm": "img/burgers.png",
                "mahsulotlar": {
                    "klassik_burger": {
                        "nomi": "Klassik Burger",
                        "tavsif": "Go'sht, pishloq, pomidor, salat",
                        "narx": 25000,
                        "id": 1
                    },
                    "chizburger": {
                        "nomi": "Chizburger",
                        "tavsif": "Go'sht, ikki qatlam pishloq, sous",
                        "narx": 28000,
                        "id": 2
                    },
                    "katta_burger": {
                        "nomi": "Big Burger",
                        "tavsif": "Katta burger, ikki qatlam go'sht",
                        "narx": 35000,
                        "id": 3
                    },
                    "tovuq_burger": {
                        "nomi": "Tovuq Burger",
                        "tavsif": "Tovuq filesi, salat, sous",
                        "narx": 30000,
                        "id": 4
                    }
                }
            },
            "ichimliklar": {
                "nomi": "🥤 Ichimliklar",
                "rasm": "img/drinks.png",
                "mahsulotlar": {
                    "kola": {
                        "nomi": "Coca Cola",
                        "tavsif": "0.5L sovuq ichimlik",
                        "narx": 8000,
                        "id": 5
                    },
                    "fanta": {
                        "nomi": "Fanta",
                        "tavsif": "0.5L apelsinli ichimlik",
                        "narx": 8000,
                        "id": 6
                    },
                    "suv": {
                        "nomi": "Suv",
                        "tavsif": "0.5L toza suv",
                        "narx": 3000,
                        "id": 7
                    },
                    "qahva": {
                        "nomi": "Qahva",
                        "tavsif": "Issiq qahva",
                        "narx": 12000,
                        "id": 8
                    }
                }
            },
            "qoshimcha": {
                "nomi": "🍟 Qo'shimcha taomlar",
                "rasm": "img/sides.png",
                "mahsulotlar": {
                    "fri": {
                        "nomi": "Kartoshka fri",
                        "tavsif": "Xirrangan kartoshka",
                        "narx": 15000,
                        "id": 9
                    },
                    "piyoz_halqa": {
                        "nomi": "Piyoz halqalari",
                        "tavsif": "Qovurilgan piyoz halqalari",
                        "narx": 18000,
                        "id": 10
                    },
                    "nagetlar": {
                        "nomi": "Nagetlar",
                        "tavsif": "Tovuq nagetlari (6 dona)",
                        "narx": 22000,
                        "id": 11
                    },
                    "qanotlar": {
                        "nomi": "Tovuq qanoti",
                        "tavsif": "Achchiq tovuq qanoti (4 dona)",
                        "narx": 25000,
                        "id": 12
                    }
                }
            },
            "shirinliklar": {
                "nomi": "🍰 Shirinliklar",
                "rasm": "img/desserts.png",
                "mahsulotlar": {
                    "muzqaymoq": {
                        "nomi": "Muzqaymoq",
                        "tavsif": "Vanilli muzqaymoq",
                        "narx": 10000,
                        "id": 13
                    },
                    "tort": {
                        "nomi": "Tort",
                        "tavsif": "Shokoladli tort bo'lagi",
                        "narx": 15000,
                        "id": 14
                    },
                    "donut": {
                        "nomi": "Donut",
                        "tavsif": "Glazurli donut",
                        "narx": 8000,
                        "id": 15
                    },
                    "molkosheyk": {
                        "nomi": "Molkosheyk",
                        "tavsif": "Vanilli molkosheyk",
                        "narx": 18000,
                        "id": 16
                    }
                }
            }
        },
        "buyurtmalar": [],
        "savatlar": {},
        "keyingi_buyurtma_id": 1
    }


def malumot_yuklash(fayl: str) -> Dict[str, Any]:
    if 'users' in fayl.lower():
        boshlangich = {"foydalanuvchilar": [], "adminlar": []}
    else:
        boshlangich = standart_kategoriyalar()

    try:
        if not os.path.exists(fayl):
            with open(fayl, 'w', encoding='utf-8') as f:
                json.dump(boshlangich, f, ensure_ascii=False, indent=2)
            logger.info(f"Yangi fayl yaratildi: {fayl}")
            return boshlangich

        with open(fayl, 'r', encoding='utf-8') as f:
            malumot = json.load(f)

        if not malumot:
            malumot = boshlangich

        if 'users' in fayl.lower():
            if 'foydalanuvchilar' not in malumot:
                logger.warning(f"{fayl} faylida 'foydalanuvchilar' kaliti yo'q, qo'shilmoqda")
                malumot['foydalanuvchilar'] = []
            if 'adminlar' not in malumot:
                logger.warning(f"{fayl} faylida 'adminlar' kaliti yo'q, qo'shilmoqda")
                malumot['adminlar'] = []

        if 'data' in fayl.lower():
            standart = standart_kategoriyalar()
            for kalit in ['kategoriyalar', 'matnlar', 'menyu', 'buyurtmalar', 'savatlar', 'keyingi_buyurtma_id']:
                if kalit not in malumot:
                    logger.warning(f"{fayl} faylida '{kalit}' kaliti yo'q, qo'shilmoqda")
                    if kalit == 'buyurtmalar':
                        malumot[kalit] = []
                    elif kalit == 'keyingi_buyurtma_id':
                        malumot[kalit] = 1
                    else:
                        malumot[kalit] = standart.get(kalit, {})

        return malumot

    except json.JSONDecodeError as e:
        logger.error(f"JSON xatosi {fayl} faylini o'qishda: {e}")
        return boshlangich
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini yuklashda xatolik: {e}")
        return boshlangich


def malumot_saqlash(malumot: Dict[str, Any], fayl: str) -> bool:
    try:
        with open(fayl, 'w', encoding='utf-8') as f:
            json.dump(malumot, f, ensure_ascii=False, indent=2)
        logger.info(f"Ma'lumotlar saqlandi: {fayl}")
        return True
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini saqlashda xatolik: {e}")
        return False


def foydalanuvchi_olish(foydalanuvchi_id: int) -> Optional[Dict[str, Any]]:
    malumot = malumot_yuklash(foydalanuvchilar_fayli)
    return next((f for f in malumot.get("foydalanuvchilar", []) if f["id"] == foydalanuvchi_id), None)


def foydalanuvchi_saqlash(foydalanuvchi_id: int, foydalanuvchi_nomi: str, toliq_ism: str, telefon: str = None,
                          manzil: str = None) -> bool:
    malumot = malumot_yuklash(foydalanuvchilar_fayli)

    foydalanuvchi = {
        "id": foydalanuvchi_id,
        "foydalanuvchi_nomi": foydalanuvchi_nomi,
        "toliq_ism": toliq_ism,
        "telefon": telefon,
        "manzil": manzil,
        "royxat_vaqti": datetime.now().isoformat(),
        "oxirgi_faollik": datetime.now().isoformat()
    }

    for idx, f in enumerate(malumot.get("foydalanuvchilar", [])):
        if f["id"] == foydalanuvchi_id:
            malumot["foydalanuvchilar"][idx] = foydalanuvchi
            logger.info(f"Foydalanuvchi yangilandi: {foydalanuvchi_id}")
            return malumot_saqlash(malumot, foydalanuvchilar_fayli)

    malumot["foydalanuvchilar"].append(foydalanuvchi)
    logger.info(f"Yangi foydalanuvchi qo'shildi: {foydalanuvchi_id}")
    return malumot_saqlash(malumot, foydalanuvchilar_fayli)

def foydalanuvchi_tozalash(user_id: int) -> bool:
    data = malumot_yuklash(foydalanuvchilar_fayli)
    user = next((u for u in data["foydalanuvchilar"] if u["id"] == user_id), None)

    if not user:
        user = {
            "id": user_id,
            "foydalanuvchi_nomi": None,
            "toliq_ism": None,
            "telefon": None,
            "manzil": None,
            "royxat_vaqti": datetime.now().isoformat(),
            "oxirgi_faollik": datetime.now().isoformat()
        }
        data["foydalanuvchilar"].append(user)

    user["telefon"] = None
    user["manzil"] = None

    return malumot_saqlash(data, foydalanuvchilar_fayli)


def admin_tekshir(foydalanuvchi_id: int) -> bool:
    malumot = malumot_yuklash(foydalanuvchilar_fayli)
    return foydalanuvchi_id in malumot.get("adminlar", [])


def admin_saqlash(user_id: int) -> bool:
    data = malumot_yuklash(foydalanuvchilar_fayli)
    if user_id not in data["adminlar"]:
        data["adminlar"].append(user_id)
        return malumot_saqlash(data, foydalanuvchilar_fayli)
    return True


def kategoriyalar_olish() -> Dict[str, Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return malumot.get("kategoriyalar", standart_kategoriyalar().get("kategoriyalar", {}))


def matn_olish(kalit: str) -> str:
    malumot = malumot_yuklash(malumotlar_fayli)
    return malumot.get("matnlar", {}).get(kalit, kalit)


def menyu_olish(menyu_turi: str) -> Dict[str, str]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return malumot.get("menyu", {}).get(menyu_turi, {})


def savat_olish(foydalanuvchi_id: int) -> Dict[str, Any]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return malumot.get("savatlar", {}).get(str(foydalanuvchi_id), {})


def savat_qoshish(foydalanuvchi_id: int, kategoriya: str, mahsulot_kaliti: str, miqdor: int = 1) -> bool:
    malumot = malumot_yuklash(malumotlar_fayli)
    savat_kaliti = str(foydalanuvchi_id)

    if savat_kaliti not in malumot["savatlar"]:
        malumot["savatlar"][savat_kaliti] = {}

    element_kaliti = f"{kategoriya}:{mahsulot_kaliti}"

    if element_kaliti in malumot["savatlar"][savat_kaliti]:
        malumot["savatlar"][savat_kaliti][element_kaliti]["quantity"] += miqdor
    else:
        kategoriyalar = malumot["kategoriyalar"][kategoriya]
        mahsulot = kategoriyalar["mahsulotlar"][mahsulot_kaliti]
        malumot["savatlar"][savat_kaliti][element_kaliti] = {
            "category": kategoriya,
            "product_key": mahsulot_kaliti,
            "name": mahsulot["nomi"],
            "price": mahsulot["narx"],
            "quantity": miqdor
        }

    return malumot_saqlash(malumot, malumotlar_fayli)


def savatdan_ochirish(foydalanuvchi_id: int, kategoriya: str, mahsulot_kaliti: str) -> bool:
    malumot = malumot_yuklash(malumotlar_fayli)
    savat_kaliti = str(foydalanuvchi_id)

    if savat_kaliti in malumot["savatlar"]:
        element_kaliti = f"{kategoriya}:{mahsulot_kaliti}"
        if element_kaliti in malumot["savatlar"][savat_kaliti]:
            del malumot["savatlar"][savat_kaliti][element_kaliti]
            return malumot_saqlash(malumot, malumotlar_fayli)
    return False


def savat_tozalash(foydalanuvchi_id: int) -> bool:
    malumot = malumot_yuklash(malumotlar_fayli)
    savat_kaliti = str(foydalanuvchi_id)

    if savat_kaliti in malumot["savatlar"]:
        malumot["savatlar"][savat_kaliti] = {}
        return malumot_saqlash(malumot, malumotlar_fayli)
    return False


def savat_jami(foydalanuvchi_id: int) -> int:
    savat = savat_olish(foydalanuvchi_id)
    jami = 0
    for element in savat.values():
        jami += element["price"] * element["quantity"]
    return jami


def buyurtma_yaratish(foydalanuvchi_id: int) -> Optional[Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    savat = savat_olish(foydalanuvchi_id)

    if not savat:
        return None

    buyurtma = {
        "id": malumot.get("keyingi_buyurtma_id", 1),
        "user_id": foydalanuvchi_id,
        "items": savat.copy(),
        "total": savat_jami(foydalanuvchi_id),
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    malumot["buyurtmalar"].append(buyurtma)
    malumot["keyingi_buyurtma_id"] = malumot.get("keyingi_buyurtma_id", 1) + 1

    if malumot_saqlash(malumot, malumotlar_fayli):
        savat_tozalash(foydalanuvchi_id)
        return buyurtma
    return None


def foydalanuvchi_buyurtmalari(foydalanuvchi_id: int) -> List[Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return [
        buyurtma for buyurtma in malumot.get("buyurtmalar", [])
        if buyurtma.get("user_id") == foydalanuvchi_id
    ]


def barcha_buyurtmalar() -> List[Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return malumot.get("buyurtmalar", [])


def buyurtma_olish(buyurtma_id: int) -> Optional[Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    return next(
        (buyurtma for buyurtma in malumot.get("buyurtmalar", []) if buyurtma.get("id") == buyurtma_id),
        None
    )


def buyurtma_holat_yangilash(buyurtma_id: int, holat: str) -> bool:
    malumot = malumot_yuklash(malumotlar_fayli)

    for buyurtma in malumot.get("buyurtmalar", []):
        if buyurtma.get("id") == buyurtma_id:
            buyurtma["status"] = holat
            return malumot_saqlash(malumot, malumotlar_fayli)
    return False


def buyurtma_bekor_qilish(buyurtma_id: int, foydalanuvchi_id: int) -> bool:
    malumot = malumot_yuklash(malumotlar_fayli)
    buyurtmalar = malumot.get("buyurtmalar", [])

    for idx, buyurtma in enumerate(list(buyurtmalar)):
        if (buyurtma.get("id") == buyurtma_id and
                buyurtma.get("user_id") == foydalanuvchi_id):
            if buyurtma.get("status") == "completed":
                return False
            del malumot["buyurtmalar"][idx]
            return malumot_saqlash(malumot, malumotlar_fayli)

    return False


def get_categories() -> Dict[str, Dict[str, Any]]:
    malumot = malumot_yuklash(malumotlar_fayli)
    kategoriyalar = malumot.get("kategoriyalar", {})

    yangilangan = {}
    for key, kat in kategoriyalar.items():
        yangilangan[key] = {
            "name": kat.get("nomi", ""),
            "image": kat.get("rasm", ""),
            "products": {}
        }

        mahsulotlar = kat.get("mahsulotlar", {})
        for prod_key, prod in mahsulotlar.items():
            yangilangan[key]["products"][prod_key] = {
                "name": prod.get("nomi", ""),
                "description": prod.get("tavsif", ""),
                "price": prod.get("narx", 0),
                "id": prod.get("id", 0)
            }

    return yangilangan


def get_category_products(category: str) -> Dict[str, Dict[str, Any]]:
    categories = get_categories()
    return categories.get(category, {}).get("products", {})


def get_product(category: str, product_key: str) -> Optional[Dict[str, Any]]:
    products = get_category_products(category)
    return products.get(product_key)


def _generate_product_key(name: str, existing_keys: List[str]) -> str:
    base = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    base = base or "product"
    candidate = base
    counter = 1
    while candidate in existing_keys:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def _get_next_product_id(data: Dict[str, Any]) -> int:
    max_id = 0
    for category in data.get("kategoriyalar", {}).values():
        for product in category.get("mahsulotlar", {}).values():
            max_id = max(max_id, product.get("id", 0))
    return max_id + 1


def update_product_field(category_key: str, product_key: str, field: str, value: Any) -> bool:
    field_map = {
        "name": "nomi",
        "description": "tavsif",
        "price": "narx"
    }

    uzbek_field = field_map.get(field)
    if not uzbek_field:
        return False

    data = malumot_yuklash(malumotlar_fayli)
    category = data.get("kategoriyalar", {}).get(category_key)
    if not category:
        return False

    product = category.get("mahsulotlar", {}).get(product_key)
    if not product:
        return False

    product[uzbek_field] = value
    return malumot_saqlash(data, malumotlar_fayli)


def add_product(category_key: str, name: str, description: str, price: int) -> Optional[Dict[str, Any]]:
    data = malumot_yuklash(malumotlar_fayli)
    category = data.get("kategoriyalar", {}).get(category_key)
    if not category:
        return None

    mahsulotlar = category.setdefault("mahsulotlar", {})
    product_key = _generate_product_key(name, list(mahsulotlar.keys()))
    new_product = {
        "nomi": name,
        "tavsif": description,
        "narx": price,
        "id": _get_next_product_id(data)
    }
    mahsulotlar[product_key] = new_product

    if malumot_saqlash(data, malumotlar_fayli):
        return {"key": product_key, **new_product}
    return None


def delete_product(category_key: str, product_key: str) -> bool:
    data = malumot_yuklash(malumotlar_fayli)
    category = data.get("kategoriyalar", {}).get(category_key)
    if not category:
        return False

    mahsulotlar = category.get("mahsulotlar", {})
    if product_key not in mahsulotlar:
        return False

    del mahsulotlar[product_key]
    return malumot_saqlash(data, malumotlar_fayli)
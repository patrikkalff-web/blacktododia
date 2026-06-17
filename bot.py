import os
import time
import logging
import requests
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
ML_AFFILIATE_ID  = os.getenv("ML_AFFILIATE_ID", "carbonocarbono20230310011151")

INTERVALO_MINUTOS = 30
DESCONTO_MINIMO   = 20
CATEGORIAS_ML = ["MLB1051","MLB1430","MLB1276","MLB1132","MLB1574"]

logging.basicConfig(format="%(asctime)s — %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)
posted_ids = set()

def buscar_ofertas_ml(categoria):
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {"category": categoria, "sort": "relevance", "limit": 20}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("results", [])
    except Exception as e:
        log.warning(f"Erro: {e}")
        return []

def calcular_desconto(item):
    original = item.get("original_price") or 0
    atual = item.get("price") or 0
    if original and atual and original > atual:
        return round((1 - atual / original) * 100, 1)
    return 0

def gerar_link(item_id):
    return f"https://mercadolivre.com.br/p/{item_id}?tracking_id={ML_AFFILIATE_ID}"

def formatar_mensagem(item, desconto, link):
    titulo = item.get("title", "Produto")
    preco = item.get("price", 0)
    original = item.get("original_price", preco)
    economia = original - preco
    return (
        f"🔥 *{titulo}*\n\n"
        f"🔴 De: ~R$ {original:,.2f}~\n"
        f"🟢 Por: *R$ {preco:,.2f}*\n"
        f"💥 *{desconto}% OFF*\n"
        f"💵 Economia: *R$ {economia:,.2f}*\n\n"
        f"🛒 [COMPRAR AGORA]({link})\n\n"
        f"📢 {TELEGRAM_CHANNEL}"
    )

def processar_e_postar(bot):
    for cat in CATEGORIAS_ML:
        itens = buscar_ofertas_ml(cat)
        for item in itens:
            item_id = item.get("id")
            desconto = calcular_desconto(item)
            if item_id in posted_ids or desconto < DESCONTO_MINIMO:
                continue
            link = gerar_link(item_id)
            mensagem = formatar_mensagem(item, desconto, link)
            thumbnail = item.get("thumbnail","").replace("I.jpg","O.jpg")
            try:
                bot.send_photo(chat_id=TELEGRAM_CHANNEL, photo=thumbnail,
                    caption=mensagem, parse_mode=ParseMode.MARKDOWN)
                posted_ids.add(item_id)
                log.info(f"✅ Postado: {item.get('title')} — {desconto}% OFF")
                time.sleep(3)
                break
            except Exception as e:
                log.error(f"Erro ao postar: {e}")

def main():
    log.info("🤖 BlackTodoDia Bot iniciado!")
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            processar_e_postar(bot)
        except Exception as e:
            log.error(f"Erro: {e}")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    main()

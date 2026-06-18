import os, time, logging, requests, json
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
ML_AFFILIATE_ID  = os.getenv("ML_AFFILIATE_ID", "carbonocarbono20230310011151")
INTERVALO_MINUTOS = 30

logging.basicConfig(format="%(asctime)s — %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)
posted_ids = set()

def buscar_pelando():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Accept": "application/json",
        }
        r = requests.get(
            "https://api.pelando.com.br/api/threads?types=deal&page=1&size=20&orderBy=hottest",
            headers=headers,
            timeout=15
        )
        log.info(f"Pelando status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            return data.get("data", {}).get("threads", {}).get("items", [])
        return []
    except Exception as e:
        log.warning(f"Erro Pelando: {e}")
        return []

def formatar_mensagem(oferta):
    titulo    = oferta.get("title", "Oferta")
    preco     = oferta.get("price", 0)
    original  = oferta.get("nextBestPrice") or oferta.get("originalPrice", 0)
    loja      = oferta.get("merchant", {}).get("name", "Loja") if oferta.get("merchant") else "Loja"
    url       = oferta.get("sourceUrl", "")

    # adiciona tag de afiliado ML se for link do ML
    if "mercadolivre" in url or "mercadopago" in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}tracking_id={ML_AFFILIATE_ID}"

    partes = [f"🔥 *{titulo}*\n", f"🏪 Loja: {loja}"]
    if original and original > preco:
        desconto = round((1 - preco/original)*100, 1)
        partes.append(f"🔴 De: ~R$ {original:,.2f}~")
        partes.append(f"🟢 Por: *R$ {preco:,.2f}*")
        partes.append(f"💥 *{desconto}% OFF*\n")
    else:
        partes.append(f"💰 *R$ {preco:,.2f}*\n")
    partes.append(f"🛒 [VER OFERTA]({url})")
    partes.append(f"\n📢 {TELEGRAM_CHANNEL}")
    return "\n".join(partes)

def processar_e_postar(bot):
    ofertas = buscar_pelando()
    log.info(f"Ofertas encontradas: {len(ofertas)}")
    for oferta in ofertas:
        oid = oferta.get("id")
        if oid in posted_ids:
            continue
        mensagem = formatar_mensagem(oferta)
        imagem   = oferta.get("image", {}).get("url") if oferta.get("image") else None
        try:
            if imagem:
                bot.send_photo(
                    chat_id=TELEGRAM_CHANNEL,
                    photo=imagem,
                    caption=mensagem,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                bot.send_message(
                    chat_id=TELEGRAM_CHANNEL,
                    text=mensagem,
                    parse_mode=ParseMode.MARKDOWN
                )
            posted_ids.add(oid)
            log.info(f"✅ Postado: {oferta.get('title')}")
            time.sleep(3)
            return
        except Exception as e:
            log.error(f"Erro ao postar: {e}")

def main():
    log.info("🤖 BlackTodoDia Bot iniciado!")
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        processar_e_postar(bot)
        log.info(f"⏳ Aguardando {INTERVALO_MINUTOS} min...")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    main()

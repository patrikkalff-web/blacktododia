import os, time, logging, requests
import xml.etree.ElementTree as ET
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
ML_AFFILIATE_ID  = os.getenv("ML_AFFILIATE_ID", "carbonocarbono20230310011151")
INTERVALO_MINUTOS = 30

logging.basicConfig(format="%(asctime)s — %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)
posted_ids = set()

FEEDS = [
    "https://www.pelando.com.br/api/feed/hot.rss",
    "https://www.promobit.com.br/feed/",
]

def buscar_feed(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        log.info(f"Feed {url}: status {r.status_code}")
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item"):
            titulo = item.findtext("title", "")
            link   = item.findtext("link", "")
            desc   = item.findtext("description", "")
            guid   = item.findtext("guid", link)
            imagem = ""
            enc    = item.find("enclosure")
            if enc is not None:
                imagem = enc.get("url", "")
            items.append({"titulo": titulo, "link": link, "desc": desc, "guid": guid, "imagem": imagem})
        return items
    except Exception as e:
        log.warning(f"Erro feed: {e}")
        return []

def formatar_mensagem(oferta):
    titulo = oferta["titulo"]
    link   = oferta["link"]
    if "mercadolivre" in link or "meli" in link:
        sep  = "&" if "?" in link else "?"
        link = f"{link}{sep}tracking_id={ML_AFFILIATE_ID}"
    return (
        f"🔥 *{titulo}*\n\n"
        f"🛒 [VER OFERTA]({link})\n\n"
        f"📢 {TELEGRAM_CHANNEL}"
    )

def processar_e_postar(bot):
    for feed_url in FEEDS:
        ofertas = buscar_feed(feed_url)
        log.info(f"Ofertas no feed: {len(ofertas)}")
        for oferta in ofertas:
            guid = oferta["guid"]
            if guid in posted_ids:
                continue
            mensagem = formatar_mensagem(oferta)
            try:
                if oferta["imagem"]:
                    bot.send_photo(
                        chat_id=TELEGRAM_CHANNEL,
                        photo=oferta["imagem"],
                        caption=mensagem,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    bot.send_message(
                        chat_id=TELEGRAM_CHANNEL,
                        text=mensagem,
                        parse_mode=ParseMode.MARKDOWN
                    )
                posted_ids.add(guid)
                log.info(f"✅ Postado: {oferta['titulo']}")
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

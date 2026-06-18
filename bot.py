import os, time, logging, requests
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
ML_AFFILIATE_ID  = os.getenv("ML_AFFILIATE_ID", "carbonocarbono20230310011151")
INTERVALO_MINUTOS = 30

BUSCAS = [
    "fone bluetooth", "tenis nike", "fritadeira air fryer",
    "smartwatch", "notebook", "cafeteira", "mochila",
    "celular samsung", "tv smart", "perfume importado"
]

logging.basicConfig(format="%(asctime)s — %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)
posted_ids = set()
busca_idx = 0

def buscar_ml(query):
    try:
        r = requests.get(
            "https://api.mercadolibre.com/sites/MLB/search",
            params={"q": query, "limit": 5, "sort": "relevance"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        log.info(f"ML status: {r.status_code} para '{query}'")
        return r.json().get("results", [])
    except Exception as e:
        log.warning(f"Erro: {e}")
        return []

def gerar_link(item_id):
    return f"https://mercadolivre.com.br/p/{item_id}?tracking_id={ML_AFFILIATE_ID}"

def formatar_mensagem(item, link):
    titulo   = item.get("title", "Produto")
    preco    = item.get("price", 0)
    original = item.get("original_price")
    partes   = [f"🔥 *{titulo}*\n"]
    if original and original > preco:
        desconto = round((1 - preco/original)*100, 1)
        partes.append(f"🔴 De: ~R$ {original:,.2f}~")
        partes.append(f"🟢 Por: *R$ {preco:,.2f}*")
        partes.append(f"💥 *{desconto}% OFF*\n")
    else:
        partes.append(f"💰 *R$ {preco:,.2f}*\n")
    partes.append(f"🛒 [COMPRAR AGORA]({link})")
    partes.append(f"\n📢 {TELEGRAM_CHANNEL}")
    return "\n".join(partes)

def processar_e_postar(bot):
    global busca_idx
    query = BUSCAS[busca_idx % len(BUSCAS)]
    busca_idx += 1
    log.info(f"Buscando: '{query}'")
    itens = buscar_ml(query)
    log.info(f"Itens encontrados: {len(itens)}")
    for item in itens:
        item_id = item.get("id")
        if item_id in posted_ids:
            continue
        link     = gerar_link(item_id)
        mensagem = formatar_mensagem(item, link)
        thumbnail = item.get("thumbnail","").replace("I.jpg","O.jpg")
        try:
            bot.send_photo(
                chat_id=TELEGRAM_CHANNEL,
                photo=thumbnail,
                caption=mensagem,
                parse_mode=ParseMode.MARKDOWN
            )
            posted_ids.add(item_id)
            log.info(f"✅ Postado: {item.get('title')}")
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

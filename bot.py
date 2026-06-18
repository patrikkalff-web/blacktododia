import os, time, logging, requests
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
ML_AFFILIATE_ID  = os.getenv("ML_AFFILIATE_ID", "carbonocarbono20230310011151")
INTERVALO_MINUTOS = 30
CATEGORIAS_ML = ["MLB1051","MLB1430","MLB1276","MLB1132","MLB1574","MLB1000"]

logging.basicConfig(format="%(asctime)s — %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)
posted_ids = set()

def buscar_ofertas_ml(categoria):
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {"category": categoria, "sort": "relevance", "limit": 10}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("results", [])
    except Exception as e:
        log.warning(f"Erro ML: {e}")
        return []

def gerar_link(item_id):
    return f"https://mercadolivre.com.br/p/{item_id}?tracking_id={ML_AFFILIATE_ID}"

def formatar_mensagem(item, link):
    titulo   = item.get("title", "Produto")
    preco    = item.get("price", 0)
    original = item.get("original_price")
    partes = [f"🔥 *{titulo}*\n"]
    if original and original > preco:
        desconto = round((1 - preco/original)*100, 1)
        economia = original - preco
        partes.append(f"🔴 De: ~R$ {original:,.2f}~")
        partes.append(f"🟢 Por: *R$ {preco:,.2f}*")
        partes.append(f"💥 *{desconto}% OFF* — economia de R$ {economia:,.2f}\n")
    else:
        partes.append(f"💰 *R$ {preco:,.2f}*\n")
    partes.append(f"🛒 [COMPRAR NO MERCADO LIVRE]({link})")
    partes.append(f"\n📢 {TELEGRAM_CHANNEL}")
    return "\n".join(partes)

def processar_e_postar(bot):
    postados = 0
    for cat in CATEGORIAS_ML:
        itens = buscar_ofertas_ml(cat)
        log.info(f"Categoria {cat}: {len(itens)} itens encontrados")
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
                postados += 1
                log.info(f"✅ Postado: {item.get('title')}")
                time.sleep(3)
                break
            except Exception as e:
                log.error(f"Erro ao postar: {e}")
    log.info(f"Ciclo: {postados} postados.")

def main():
    log.info("🤖 BlackTodoDia Bot iniciado!")
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        processar_e_postar(bot)
        log.info(f"⏳ Aguardando {INTERVALO_MINUTOS} min...")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    main()

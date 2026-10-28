"""Banco de conteúdo do Papa (o que não é oferta), para o Instagram nunca repetir.

Pilares: anticilada, dica, humor, mito, bastidor, conversa (+ série Black Friday gerada por data).
Cada peça: id único, pilar, layout (visual diferente em artes.peca), título, corpo, legenda.
Regras: nada de dado inventado, nada de urgência falsa, sem hashtag, sem nome do dono.
O CEO na nuvem pode acrescentar peças novas aqui (ids novos; nunca reaproveitar id).
"""
from datetime import date, timedelta

BLACK_FRIDAY = date(2026, 11, 27)
NAO_REPETIR_DIAS = 14
PECAS_STORY_DIA = 4   # sem oferta, no máximo 3 stories do banco por dia (o vigia garante o piso)

PECAS = [
    # --- Anti-cilada: o Papa protege o bolso -----------------------------------------
    dict(id="ac-preco-inflado", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("O \"DE\" INFLADO",), corpo=("Tem loja que sobe o preço", "antes e depois \"dá\" desconto.", "O Papa confere o preço real", "antes de postar."),
         legenda="😎💎 O golpe mais velho do varejo: subir o preço e depois dar \"50% OFF\". O Papa confere antes de postar."),
    dict(id="ac-replica", pilar="anticilada", layout="meme",
         titulo=("TÊNIS DE MARCA", "POR R$ 79?"), corpo=("O Papa: é réplica, parceiro.",),
         legenda="😎💎 Preço bom demais em marca de luxo quase sempre é réplica. Réplica é crime contra a marca e vem sem garantia. Aqui é só original."),
    dict(id="ac-quem-vende", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("QUEM VENDE?",), corpo=("Antes de comprar, olhe", "\"vendido por\".", "Loja oficial ou Shopee Mall", "= menos dor de cabeça."),
         legenda="😎💎 O mesmo produto pode ser vendido por mil lojas. Prefira a loja oficial da marca. É assim que o Papa escolhe."),
    dict(id="ac-avaliacao-foto", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("ESTRELA ENGANA",), corpo=("Leia as avaliações com foto.", "Elas mostram o produto", "que chega de verdade."),
         legenda="😎💎 Nota 5 sem foto vale pouco. Avaliação com foto é ouro."),
    dict(id="ac-frete", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("OLHE O PREÇO", "COM FRETE"), corpo=("Anúncio barato com frete caro", "não é achado.", "Compare sempre o total."),
         legenda="😎💎 O preço que importa é o do carrinho, com frete. O resto é vitrine."),
    dict(id="ac-pix", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("PIX PRA", "DESCONHECIDO? NÃO."), corpo=("Pague sempre dentro da loja.", "Fora dela, ninguém te protege."),
         legenda="😎💎 Vendedor pedindo Pix por fora do site é golpe na certa. Compre só pelo carrinho da loja."),

    # --- Dicas do Papa -----------------------------------------------------------------
    dict(id="dc-7-dias", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("COMPROU E", "SE ARREPENDEU?"), corpo=("Compra online tem 7 dias", "pra desistir (CDC, art. 49).", "Guarde a nota e a embalagem."),
         legenda="😎💎 Direito seu: compra feita pela internet pode ser desfeita em até 7 dias depois de receber."),
    dict(id="dc-cupom", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("CUPOM ANTES", "DE PAGAR"), corpo=("Na Shopee, abra a aba de", "cupons antes de fechar.", "Às vezes tem frete grátis", "esperando você."),
         legenda="😎💎 Dois cliques que muita gente esquece: conferir os cupons antes de pagar."),
    dict(id="dc-lista", pilar="dica", layout="checklist", selo="DICA DO PAPA",
         titulo=("ANTES DE COMPRAR",), corpo=("Precisa mesmo?", "É marca boa?", "É loja oficial?", "O preço com frete é bom?"),
         legenda="😎💎 O checklist do Papa. Passou nos 4? Pode ir."),
    dict(id="dc-notificacao", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("ATIVA O SININHO",), corpo=("Achado bom acaba rápido.", "No canal do Telegram,", "liga as notificações."),
         legenda="😎💎 O achado bom some em horas. Com o sininho ligado, você vê primeiro. Link na bio."),
    dict(id="dc-garantia", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("ORIGINAL TEM", "GARANTIA"), corpo=("Produto original tem garantia", "do fabricante.", "Réplica quebrou? Perdeu."),
         legenda="😎💎 Mais um motivo pra só comprar original: se der problema, a marca resolve."),
    dict(id="dc-kit", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("FAÇA A CONTA", "DO KIT"), corpo=("Kit de 4 cuecas por R$ 80", "= R$ 20 cada.", "Divida sempre pelo número", "de peças."),
         legenda="😎💎 Kit parece caro até você dividir pelo número de peças. O Papa sempre faz essa conta pra você."),

    # --- Humor do Papa -------------------------------------------------------------------
    dict(id="hu-3h", pilar="humor", layout="meme",
         titulo=("NINGUÉM:",), corpo=("O Papa às 3h da manhã:", "garimpando desconto."),
         legenda="😎💎 Enquanto você dorme, o Papa garimpa."),
    dict(id="hu-carrinho", pilar="humor", layout="meme",
         titulo=("CARRINHO CHEIO,", "SALÁRIO VAZIO"), corpo=("Calma. Espera o Papa achar", "com desconto."),
         legenda="😎💎 Não compra no impulso. Coloca no carrinho e espera o achado."),
    dict(id="hu-imperdivel", pilar="humor", layout="meme",
         titulo=("\"IMPERDÍVEL\"",), corpo=("Mesmo preço de ontem.", "O Papa: perdível, sim."),
         legenda="😎💎 Promoção de verdade tem preço menor. O resto é texto bonito."),
    dict(id="hu-original", pilar="humor", layout="frase",
         titulo=("O PAPA NÃO", "COMPRA RÉPLICA."), corpo=("Compra original", "pagando menos."),
         legenda="😎💎 Lema da casa."),
    dict(id="hu-amigo", pilar="humor", layout="meme",
         titulo=("TODO GRUPO TEM", "AQUELE AMIGO"), corpo=("que acha tudo mais barato.", "Prazer, o Papa."),
         legenda="😎💎 Marca o amigo que precisa do Papa."),
    dict(id="hu-preco-caiu", pilar="humor", layout="meme",
         titulo=("QUANDO O PREÇO", "CAI DE VERDADE"), corpo=("O Papa:", "aí sim, meu filho."),
         legenda="😎💎 A alegria do Papa é desconto real."),

    # --- Mito ou verdade -----------------------------------------------------------------
    dict(id="mv-afiliado", pilar="mito", layout="mito", veredito="MITO",
         titulo=("LINK DE AFILIADO", "DEIXA MAIS CARO"), corpo=("Você paga o mesmo preço.", "A loja é que paga", "uma comissão ao Papa."),
         legenda="😎💎 Transparência: comprando pelo link do Papa, você paga o mesmo e ajuda o canal a continuar grátis."),
    dict(id="mv-bf-barato", pilar="mito", layout="mito", veredito="MITO",
         titulo=("NA BLACK FRIDAY", "TUDO FICA BARATO"), corpo=("Tem loja que sobe o preço", "antes. Compare com o preço", "das semanas anteriores."),
         legenda="😎💎 Black Friday tem desconto real e tem maquiagem. O Papa separa um do outro."),
    dict(id="mv-oficial-cara", pilar="mito", layout="mito", veredito="MITO",
         titulo=("LOJA OFICIAL É", "SEMPRE MAIS CARA"), corpo=("Muitas vezes tem cupom", "e frete grátis.", "E vem com garantia."),
         legenda="😎💎 Loja oficial nem sempre é a mais cara. Quando o Papa acha desconto nela, é o melhor dos mundos."),
    dict(id="mv-garantia", pilar="mito", layout="mito", veredito="VERDADE",
         titulo=("ORIGINAL TEM", "GARANTIA DA MARCA"), corpo=("Réplica não tem.", "Por isso o Papa só", "posta original."),
         legenda="😎💎 Original = garantia. Réplica = sorte."),
    dict(id="mv-7dias", pilar="mito", layout="mito", veredito="VERDADE",
         titulo=("DÁ PRA DESISTIR", "DE COMPRA ONLINE"), corpo=("Até 7 dias depois", "de receber", "(Código do Consumidor)."),
         legenda="😎💎 Direito de arrependimento: 7 dias, sem precisar explicar o motivo."),

    # --- Bastidores / como funciona ------------------------------------------------------
    dict(id="bs-criterios", pilar="bastidor", layout="checklist", selo="COMO O PAPA ESCOLHE",
         titulo=("SÓ ENTRA SE...",), corpo=("For marca boa", "Vier de loja oficial", "Tiver nota alta", "O desconto for real"),
         legenda="😎💎 Os 4 filtros do Papa. Não passou, não posta."),
    dict(id="bs-telegram", pilar="bastidor", layout="dica", selo="POR QUE TELEGRAM?",
         titulo=("SEM ALGORITMO",), corpo=("No Telegram você vê", "todo achado, na hora.", "Grátis. Sem spam."),
         legenda="😎💎 Instagram esconde post. Telegram não. Por isso os achados ficam lá. Link na bio."),
    dict(id="bs-tres-canais", pilar="bastidor", layout="dica", selo="3 CANAIS",
         titulo=("ESCOLHE O SEU",), corpo=("Achadinhos: casa, tech, beleza.", "Marcas: roupa, tênis, academia.", "Quer tudo? Todas as Ofertas:", "@papagarimpouofertas"),
         legenda="😎💎 Três canais grátis no Telegram: Achadinhos, Marcas ou tudo num canal só (@papagarimpouofertas). Link na bio."),
    dict(id="bs-transparencia", pilar="bastidor", layout="frase",
         titulo=("COMO O PAPA", "GANHA?"), corpo=("A loja paga uma comissão.", "Você paga o mesmo preço."),
         legenda="😎💎 Sem segredo: o canal é grátis porque as lojas pagam comissão por indicação."),

    # --- Conversa (feed, pede comentário) ------------------------------------------------
    # --- Mais anticilada / dicas / humor / bastidor --------------------------------------
    dict(id="ac-link-estranho", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("LINK ESTRANHO?", "NÃO CLICA"), corpo=("Promoção chegando por SMS", "com link esquisito é golpe.", "Entre direto no app da loja."),
         legenda="😎💎 Achado de verdade vem de loja de verdade. Desconfie de link que chega do nada."),
    dict(id="ac-perfil-fake", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("PERFIL VENDENDO", "\"ORIGINAL\" BARATO"), corpo=("Sem loja, sem nota fiscal,", "só Pix? Corre.",),
         legenda="😎💎 Perfil que vende \"original\" sem loja e sem nota é cilada. O Papa só manda pra loja oficial."),
    dict(id="dc-carrinho", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("DEIXA NO", "CARRINHO"), corpo=("Muita loja avisa quando o", "preço do carrinho cai.", "Paciência paga."),
         legenda="😎💎 Truque simples: deixa no carrinho e espera. Quando cair de verdade, o Papa também avisa no Telegram."),
    dict(id="dc-tamanho", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("ERROU O", "TAMANHO?"), corpo=("Antes de comprar roupa,", "veja a tabela de medidas", "da própria marca."),
         legenda="😎💎 Cada marca veste de um jeito. A tabela de medidas evita troca."),
    dict(id="dc-nota-fiscal", pilar="dica", layout="checklist", selo="DICA DO PAPA",
         titulo=("GUARDE SEMPRE",), corpo=("Nota fiscal", "Comprovante de pagamento", "Print do anúncio", "Embalagem por 7 dias"),
         legenda="😎💎 Deu problema? Com isso na mão você resolve rápido."),
    dict(id="hu-segunda", pilar="humor", layout="meme",
         titulo=("SEGUNDA-FEIRA", "DE MANHÃ"), corpo=("O Papa já achou", "3 descontos antes do café."),
         legenda="😎💎 O Papa não tira folga. Os achados estão no Telegram."),
    dict(id="hu-de-por", pilar="humor", layout="meme",
         titulo=("\"DE R$ 999", "POR R$ 899\""), corpo=("O Papa: isso não é", "desconto, é troco."),
         legenda="😎💎 10% em produto com preço inflado não é achado. O Papa só posta desconto que vale."),
    dict(id="hu-paciencia", pilar="humor", layout="frase",
         titulo=("QUEM ESPERA", "PAGA MENOS."), corpo=("Ditado do Papa.",),
         legenda="😎💎 Calma no clique. O achado chega."),
    dict(id="mv-cupom-sempre", pilar="mito", layout="mito", veredito="MITO",
         titulo=("CUPOM SEMPRE", "VALE A PENA"), corpo=("Às vezes o preço sem cupom", "em outra loja é menor.", "Compare o total."),
         legenda="😎💎 Cupom ajuda, mas o que manda é o preço final."),
    dict(id="mv-mall", pilar="mito", layout="mito", veredito="VERDADE",
         titulo=("SHOPEE MALL É", "LOJA OFICIAL"), corpo=("É a área das lojas", "oficiais das marcas", "dentro da Shopee."),
         legenda="😎💎 Viu \"Shopee Mall\"? É a loja oficial da marca. O Papa prefere sempre."),
    dict(id="bs-um-dia", pilar="bastidor", layout="checklist", selo="UM DIA DO PAPA",
         titulo=("O PAPA HOJE",), corpo=("Olhou centenas de ofertas", "Descartou as ruins", "Conferiu preço e loja", "Postou só as boas"),
         legenda="😎💎 Pra cada achado postado, muita coisa ruim fica de fora. É isso que o Papa faz por você."),
    dict(id="bs-anonimo", pilar="bastidor", layout="frase",
         titulo=("QUEM É", "O PAPA?"), corpo=("Ninguém sabe.", "Só os descontos aparecem."),
         legenda="😎💎 O Papa não mostra a cara. Mostra o achado."),
    dict(id="cv-pior-compra", pilar="conversa", layout="frase", so_feed=True,
         titulo=("QUAL FOI SUA", "PIOR COMPRA ONLINE?"), corpo=("Conta aqui.", "O Papa não julga."),
         legenda="😎💎 Todo mundo já caiu em uma. Conta a sua nos comentários."),
    # --- Lote 2 (27/10): mais temas ---------------------------------------------------------
    dict(id="ac-entrega-falsa", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("TAXA PRA LIBERAR", "ENTREGA?"), corpo=("Mensagem pedindo taxa pra", "liberar encomenda costuma", "ser golpe. Confira no app."),
         legenda="😎💎 Encomenda presa pedindo Pix por mensagem? Confira sempre no app da loja ou da transportadora."),
    dict(id="ac-sorteio-fake", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("\"VOCÊ GANHOU\"", "UM CELULAR?"), corpo=("Ninguém ganha nada", "pagando \"só o frete\"."),
         legenda="😎💎 Prêmio que pede pagamento não é prêmio. O Papa avisa."),
    dict(id="ac-site-copia", pilar="anticilada", layout="dica", selo="ANTICILADA",
         titulo=("SITE CLONADO",), corpo=("Endereço com letra trocada", "e preço impossível?", "Feche a aba."),
         legenda="😎💎 Golpista copia site de loja grande. Confira o endereço antes de pagar."),
    dict(id="ac-falta-estoque", pilar="anticilada", layout="meme",
         titulo=("\"SÓ RESTAM 2", "UNIDADES\""), corpo=("Há 3 semanas.", "O Papa: sei."),
         legenda="😎💎 Contador de estoque eterno é truque de pressa. Compre quando o preço for bom, não quando a loja grita."),
    dict(id="ac-cronometro", pilar="anticilada", layout="meme",
         titulo=("\"OFERTA ACABA", "EM 10 MINUTOS\""), corpo=("Aí você volta amanhã", "e o relógio reiniciou."),
         legenda="😎💎 Relógio que reinicia não é urgência, é teatro."),
    dict(id="dc-historico", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("PREÇO TEM", "HISTÓRIA"), corpo=("Antes de comprar caro,", "veja quanto custava", "nas últimas semanas."),
         legenda="😎💎 Desconto de verdade é comparado com o preço de antes, não com o \"de\" do anúncio."),
    dict(id="dc-avaliar-vendedor", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("OLHE A LOJA,", "NÃO SÓ O PRODUTO"), corpo=("Tempo de loja, vendas e", "nota do vendedor contam", "tanto quanto o preço."),
         legenda="😎💎 Produto bom em loja ruim vira dor de cabeça. O Papa olha os dois."),
    dict(id="dc-comparar-lojas", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("MESMO PRODUTO,", "PREÇOS DIFERENTES"), corpo=("Compare em pelo menos", "2 lojas antes de fechar."),
         legenda="😎💎 Dois minutos comparando podem valer uma pizza. O Papa compara por você."),
    dict(id="dc-kit-meia", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("BÁSICO EM KIT", "SAI MAIS BARATO"), corpo=("Cueca, meia e camiseta", "básica: kit costuma ter", "o melhor preço por peça."),
         legenda="😎💎 No básico de marca, kit é rei. Divida pelo número de peças e veja."),
    dict(id="dc-lista-desejo", pilar="dica", layout="checklist", selo="DICA DO PAPA",
         titulo=("LISTA DE DESEJOS",), corpo=("Anote o que quer", "Anote o preço de hoje", "Espere cair", "Compre sem culpa"),
         legenda="😎💎 Lista de desejos é o melhor amigo do bolso."),
    dict(id="dc-troca", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("LEIA A POLÍTICA", "DE TROCA"), corpo=("Principalmente em roupa", "e calçado. Leva 30 segundos."),
         legenda="😎💎 Antes de comprar roupa, saiba como trocar. Evita stress."),
    dict(id="dc-frete-gratis", pilar="dica", layout="dica", selo="DICA DO PAPA",
         titulo=("FRETE GRÁTIS", "TEM VALOR MÍNIMO"), corpo=("Às vezes falta pouco.", "Junte o que você já", "ia comprar mesmo."),
         legenda="😎💎 Junta compra que você já ia fazer e ganha o frete. Só não inventa compra."),
    dict(id="hu-sabado", pilar="humor", layout="meme",
         titulo=("SÁBADO É DIA DE", "DESCANSAR"), corpo=("O Papa: descansar", "vendo preço cair."),
         legenda="😎💎 Fim de semana também tem achado."),
    dict(id="hu-mae", pilar="humor", layout="meme",
         titulo=("SUA MÃE QUANDO", "VOCÊ PAGA CARO"), corpo=("\"Tinha mais barato,", "meu filho.\""),
         legenda="😎💎 Evite esse sermão: compre com o Papa."),
    dict(id="hu-black-fraude", pilar="humor", layout="meme",
         titulo=("BLACK FRIDAY", "\"METADE DO DOBRO\""), corpo=("O Papa já conhece", "esse truque."),
         legenda="😎💎 O preço dobra, depois cai pela metade. O Papa não cai nessa e não deixa você cair."),
    dict(id="hu-amigo-replica", pilar="humor", layout="meme",
         titulo=("AMIGO DE TÊNIS", "DE MARCA POR R$ 90"), corpo=("A sola, 15 dias depois:", "tchau."),
         legenda="😎💎 Original dura. Réplica dá tchau."),
    dict(id="hu-carrinho-abandonado", pilar="humor", layout="meme",
         titulo=("SEU CARRINHO", "ABANDONADO"), corpo=("O Papa: deixa que", "eu vigio o preço."),
         legenda="😎💎 Deixa no carrinho. O Papa vigia."),
    dict(id="hu-pix-feliz", pilar="humor", layout="frase",
         titulo=("ECONOMIZAR", "TAMBÉM É GANHAR."), corpo=("Assinado: o Papa.",),
         legenda="😎💎 Cada real que fica no bolso conta."),
    dict(id="hu-marca-boa", pilar="humor", layout="frase",
         titulo=("MARCA BOA", "NÃO PRECISA SER CARA."), corpo=("Precisa ser bem garimpada.",),
         legenda="😎💎 Essa é a filosofia do Papa."),
    dict(id="mv-preco-cai-bf", pilar="mito", layout="mito", veredito="VERDADE",
         titulo=("TEM DESCONTO", "REAL NA BLACK"), corpo=("Tem sim. O segredo é", "saber o preço de antes."),
         legenda="😎💎 Black Friday não é só fraude: tem desconto real. O Papa garimpa os de verdade."),
    dict(id="mv-importado", pilar="mito", layout="mito", veredito="MITO",
         titulo=("IMPORTADO É", "SEMPRE MAIS BARATO"), corpo=("Some frete, prazo e taxa", "de importação antes", "de decidir."),
         legenda="😎💎 Às vezes a loja nacional sai mais em conta no total. Compare."),
    dict(id="mv-nota-5", pilar="mito", layout="mito", veredito="MITO",
         titulo=("NOTA 5 = PRODUTO", "PERFEITO"), corpo=("Poucas avaliações enganam.", "Prefira nota alta com", "muitas vendas."),
         legenda="😎💎 Nota alta com muita venda vale mais que 5 estrelas com 3 avaliações."),
    dict(id="mv-pix", pilar="mito", layout="mito", veredito="VERDADE",
         titulo=("PIX ÀS VEZES", "TEM DESCONTO"), corpo=("Algumas lojas dão desconto", "no Pix. Confira antes", "de escolher o cartão."),
         legenda="😎💎 Vale olhar: tem loja que dá desconto extra no Pix (sempre dentro do site da loja)."),
    dict(id="mv-loja-grande", pilar="mito", layout="mito", veredito="MITO",
         titulo=("LOJA GRANDE NUNCA", "TEM PROMO BOA"), corpo=("Tem, e muita.", "O Papa vive achando."),
         legenda="😎💎 As melhores promoções muitas vezes estão nas lojas oficiais das marcas."),
    dict(id="bs-marcas", pilar="bastidor", layout="checklist", selo="MARCAS DO PAPA",
         titulo=("O PAPA AMA",), corpo=("Lupo, Hering, Insider", "Nike, Adidas, Mizuno", "JBL, Philips, Mondial", "Growth, Max Titanium"),
         legenda="😎💎 Algumas das marcas que o Papa caça todo dia. Qual falta aqui? Comenta."),
    dict(id="bs-nao-posta", pilar="bastidor", layout="checklist", selo="O PAPA NÃO POSTA",
         titulo=("FICA DE FORA",), corpo=("Réplica", "Marca desconhecida", "Loja sem reputação", "Desconto de mentira"),
         legenda="😎💎 O que o Papa nunca vai postar. Por isso o canal é limpo."),
    dict(id="bs-canal-marcas", pilar="bastidor", layout="frase",
         titulo=("TREINA? CORRE?", "VESTE BÁSICO?"), corpo=("O canal Marcas é seu.", "@papagarimpoumarcas"),
         legenda="😎💎 Canal Marcas: tênis, suplemento, cueca, camiseta e polo de marca com desconto. Link na bio."),
    dict(id="bs-canal-achadinhos", pilar="bastidor", layout="frase",
         titulo=("CASA, TECH,", "BELEZA?"), corpo=("O canal Achadinhos é seu.", "@papagarimpou"),
         legenda="😎💎 Canal Achadinhos: casa, tecnologia, beleza e ferramentas de marca boa. Link na bio."),
    dict(id="bs-gratis", pilar="bastidor", layout="frase",
         titulo=("QUANTO CUSTA", "ENTRAR NO CANAL?"), corpo=("Nada.", "Nem agora, nem depois."),
         legenda="😎💎 Os canais do Papa são grátis. Sempre."),
    dict(id="bs-silenciar", pilar="bastidor", layout="dica", selo="TELEGRAM",
         titulo=("NÃO QUER", "BARULHO?"), corpo=("Dá pra silenciar o canal", "e olhar quando quiser.", "Os achados ficam lá."),
         legenda="😎💎 O canal respeita seu tempo: silencia e confere quando der."),
    dict(id="cv-salario", pilar="conversa", layout="frase", so_feed=True,
         titulo=("O SALÁRIO CAIU.", "O QUE VOCÊ COMPRA?"), corpo=("Comenta. O Papa caça.",),
         legenda="😎💎 Comenta o que tá na sua lista desse mês."),
    dict(id="cv-marca-fiel", pilar="conversa", layout="frase", so_feed=True,
         titulo=("QUAL MARCA VOCÊ", "NÃO TROCA POR NADA?"), corpo=("Comenta aqui.",),
         legenda="😎💎 Todo mundo tem a marca do coração. Qual é a sua?"),
    dict(id="cv-academia", pilar="conversa", layout="frase", so_feed=True,
         titulo=("WHEY, CREATINA", "OU TÊNIS?"), corpo=("O que o Papa garimpa", "pra você treinar?"),
         legenda="😎💎 Quem treina, comenta. O mais pedido vira caçada no canal Marcas."),
    dict(id="cv-casa", pilar="conversa", layout="frase", so_feed=True,
         titulo=("O QUE FALTA", "NA SUA COZINHA?"), corpo=("Air fryer, panela,", "liquidificador?"),
         legenda="😎💎 Comenta o que falta aí. O Papa garimpa no canal Achadinhos."),
    dict(id="cv-qual-marca", pilar="conversa", layout="frase", so_feed=True,
         titulo=("QUAL MARCA O", "PAPA CAÇA PRIMEIRO?"), corpo=("Comenta aqui.",),
         legenda="😎💎 Comenta a marca que você quer ver com desconto. O Papa fica de vigia."),
    dict(id="cv-de-olho", pilar="conversa", layout="frase", so_feed=True,
         titulo=("TÁ DE OLHO", "EM ALGUMA COISA?"), corpo=("Comenta o produto.", "O Papa avisa quando cair."),
         legenda="😎💎 Comenta o que você tá esperando baixar. O que aparecer com desconto real, vai pro canal."),
    dict(id="cv-escolha", pilar="conversa", layout="frase", so_feed=True,
         titulo=("TÊNIS, FONE OU", "AIR FRYER?"), corpo=("Comenta qual o Papa", "garimpa primeiro."),
         legenda="😎💎 Vota nos comentários. O mais pedido vira caçada do Papa."),
]


def black_friday(hoje: date) -> dict | None:
    """Peça da contagem regressiva (de 1/11 até o dia): número muda todo dia, não é repetição."""
    faltam = (BLACK_FRIDAY - hoje).days
    if faltam < 0 or hoje < date(2026, 11, 1):
        return None
    if faltam == 0:
        titulo, corpo = ("É HOJE.",), ("Black Friday do Papa:", "só desconto de verdade.", "Tudo no Telegram.")
    else:
        titulo = (str(faltam),)
        corpo = ("dias pra Black Friday.", "Anote hoje o preço do que", "você quer. No dia, compare.")
    return dict(id=f"bf-{hoje.isoformat()}", pilar="blackfriday", layout="contagem", titulo=titulo, corpo=corpo,
                legenda="😎💎 Contagem da Black Friday do Papa. Desconto falso não passa. Ativa as notificações no Telegram (link na bio).")


def escolher(h: dict, hoje: date, n: int = 1, para_story: bool = True) -> list[dict]:
    """Escolhe n peças não usadas nos últimos NAO_REPETIR_DIAS, alternando pilares."""
    usadas = h.setdefault("pecas_usadas", {})
    limite = (hoje - timedelta(days=NAO_REPETIR_DIAS)).isoformat()
    candidatas = []
    bf = black_friday(hoje)
    if bf and bf["id"] not in usadas:
        candidatas.append(bf)
    candidatas += [p for p in PECAS if usadas.get(p["id"], "") < limite and not (para_story and p.get("so_feed"))]
    if not candidatas:   # banco esgotado: volta a mais antiga (e o CEO deve repor peças)
        candidatas = sorted((p for p in PECAS if not (para_story and p.get("so_feed"))), key=lambda p: usadas.get(p["id"], ""))
    ultimo = h.get("ultimo_pilar")
    escolhidas = []
    for p in sorted(candidatas, key=lambda p: (p["pilar"] == ultimo, usadas.get(p["id"], ""))):
        if len(escolhidas) == n:
            break
        if escolhidas and p["pilar"] == escolhidas[-1]["pilar"]:
            continue
        escolhidas.append(p)
    for p in sorted(candidatas, key=lambda p: usadas.get(p["id"], "")):
        if len(escolhidas) == n:
            break
        if p not in escolhidas:
            escolhidas.append(p)
    for p in escolhidas:
        usadas[p["id"]] = hoje.isoformat()
    if escolhidas:
        h["ultimo_pilar"] = escolhidas[-1]["pilar"]
    h["pecas_usadas"] = {k: v for k, v in usadas.items() if v >= (hoje - timedelta(days=60)).isoformat()}
    return escolhidas

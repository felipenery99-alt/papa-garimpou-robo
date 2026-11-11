# Decisões do CEO do Papa Garimpou

## 2026-10-27 (montagem)
- Robô no ar (GitHub Actions 20x/dia), Instagram automático ligado (1º story publicado), Telegram aguardando API da Shopee (pedido enviado 27/10).
- Piso do dono: ≥3 stories ativos e feed todo dia.

## 2026-10-27 (1ª rotina do CEO, 18:35 Brasília)
- Visto: ainda não existe dados/relatorio.json; só 5 execuções manuais hoje (todas com sucesso), nenhuma agendada ainda. Primeira agendada deve rodar às 18:42. Histórico vazio, Shopee ainda desligada (Telegram em espera, normal).
- Sem números de membros/seguidores/alcance para avaliar; piso de stories será conferido amanhã com o relatório.
- Bug achado: o termo de busca "secador taiff" nunca renderia, porque "taiff" não estava em MARCAS_ACHADINHOS (todas as ofertas seriam reprovadas por marca). Decidido: incluir "taiff" (marca nacional consolidada de secadores). Ensaio OK.
- Próximo: Black Friday em 27/11 — incluir termos sazonais nas BUSCAS a partir da semana que vem.
- Pedido ao dono: nada novo; só aguardar a liberação da API da Shopee.

## 2026-10-28 (rotina do CEO)
- Visto (27/10): 8 execuções (agenda começou só à tarde), 0 erros; Instagram: feed feito, 16 stories ativos (piso ≥3 ok), 3 seguidores, alcance 3, 21 visitas ao perfil, 2 cliques no link. Canais Telegram com 2 membros cada; Shopee ainda desligada (Telegram em espera, normal). Banco de peças: 13 usadas, folga boa.
- Conferido: todo termo de BUSCAS tem marca na lista do seu canal (bug do "taiff" não se repete).
- Decidido: trocar "vr" por "vr collezioni" em MARCAS_MARCAS. "VR" sozinho casaria com "óculos VR" genérico (realidade virtual) e furaria a regra de só marca boa. Ensaio OK.
- Crescimento: perfil teve 21 visitas mas só 2 cliques; o story de convite (13:20) segue diário. Hoje é o 1º dia completo (20 execuções) para medir.
- Próximo: termos de Black Friday nas BUSCAS a partir de 03/11; domingo (01/11) repor peças e pesquisar contas grandes.
- Pedido ao dono: nada novo; aguardar a API da Shopee.

## 2026-10-29 (rotina do CEO)
- Visto (28/10): 25 execuções, 0 erros. Primeiro dia com Telegram ativo via garimpo Amazon (16 achadinhos, 12 marcas, 14 tech). Instagram: 3 feeds (carrossel top5, reels, post achado), 25 stories ativos (piso ≥3 ok), seguidores 3→26, alcance 24, 58 visitas ao perfil, só 2 cliques no link. Shopee ainda desligada.
- META: Instagram 26 de 50 até 03/11 (no ritmo). Telegram 8 de 30 até 03/11 somando os 4 canais (atrasado: 2 membros por canal, parado).
- Problema: o perfil recebe visitas, mas quase ninguém clica para o Telegram. Só 1 story de convite por dia (13:20).
- Decidido (alavanca nova): 2º story de convite às 21:20, pico da noite, no lugar de um story de oferta (continua o das 21:24). Ensaio OK.
- Próximo: medir cliques no link amanhã; se continuar ≤2, mudar o texto do convite (ex.: "4 canais grátis, escolha o seu"). Domingo (01/11): repor peças e pesquisar contas grandes. BF nas BUSCAS a partir de 03/11.
- Pedido ao dono: divulgar os canais no seu próprio contato/status do WhatsApp uma vez (custo zero) ajudaria a sair dos 2 membros.

## 2026-10-29 (correção: postagem duplicada)
- Dono avisou: "tá duplicando postagem". Confirmado: em 28/10, 9 ofertas saíram 2 ou 3 vezes no Telegram (ex.: amz-B0GM1PSWPD às 16:37, 17:13 e 19:04).
- Causa: 3 execuções (19:40, 20:28 e 23:00 UTC) gravaram um histórico velho por cima do da execução anterior. A execução que espera na fila do GitHub (concurrency) fazia checkout do commit da hora em que entrou na fila, sem os posts da anterior, e repostava. Os stories do Instagram repetiam pelo mesmo motivo.
- Corrigido: o checkout do robo.yml agora pega sempre o main mais novo (`ref: main`). Ensaio OK.

## 2026-10-30 (rotina do CEO)
- Visto (29/10): 33 execuções (fila do GitHub repete algumas), 1 erro (story 11:11 "mídia não encontrada" na Meta, pontual, não repetiu). Telegram: 21 achadinhos, 23 marcas, 38 tech. Instagram: 6 feeds, 25 stories ativos (piso ≥3 ok), seguidores 27→57, alcance 72, 86 visitas ao perfil, cliques no link parados em 2. Shopee ainda desligada.
- META: Instagram 57 de 50 até 03/11 (batida antes do prazo) → meta de 10/11 sobe 30%: 150→195. Telegram 8 de 30 até 03/11 (atrasado: 2 membros por canal há 4 dias).
- Problema: muita visita no perfil, quase nenhum clique para o Telegram. O convite só mostrava @papagarimpou.
- Decidido (alavanca nova): story de convite refeito: "4 CANAIS GRÁTIS, ESCOLHA O SEU", com o assunto de cada canal e o @ de cada um (achadinhos, marcas, tech, todas). Quem só quer tech ou roupa acha o seu e pode procurar o @ direto no Telegram, sem depender do clique na bio. Ensaio OK.
- Próximo: medir cliques e membros em 31/10 e 01/11. Domingo (01/11): +30 peças no banco e pesquisa de contas grandes. BF nas BUSCAS a partir de 03/11.
- Pedido ao dono: (1) divulgar os 4 canais uma vez no status do WhatsApp (custo zero); (2) conferir se o link da bio do Instagram leva a uma página com os 4 canais, e não só a um.

## 2026-10-31 (rotina do CEO)
- Visto (30/10): 31 execuções, 0 erros. **Shopee ligada** (18 achadinhos e 4 marcas vieram dela, todas de loja oficial). Telegram: 28 achadinhos, 29 marcas (inclui 3 Nike/Awin e 8 ML), 14 tech. Instagram: 25 stories ativos (piso ok), feed ok (3 Reels/dia no ar), seguidores 57→70, alcance 94, cliques no link 2→5 (o convite com os 4 canais ajudou).
- META: Instagram 70 de 195 até 10/11 (no ritmo: precisa ~11/dia, fez +13). Telegram 10 de 30 até 03/11 (atrasado: 3+3+2+2 membros).
- Decidido (alavanca nova): toda legenda do Telegram agora termina com "📲 Mande pra quem vai gostar · mais achados grátis: t.me/<canal>". Quem encaminha ou copia a oferta pro WhatsApp leva junto o link do canal, e quem recebe consegue entrar. Custo zero, #publi mantido. Ensaio OK.
- Próximo: medir membros em 01/11 e 02/11. Domingo (01/11): +30 peças no banco e pesquisa de contas grandes. BF nas BUSCAS a partir de 03/11. Tech só rende pela Amazon; avaliar termos tech na Shopee (loja oficial) se continuar baixo.
- Pedido ao dono: (1) divulgar os 4 canais uma vez no status do WhatsApp (custo zero); (2) conferir se o link da bio do Instagram mostra os 4 canais.

## 2026-11-01 (rotina do CEO, domingo)
- Visto (31/10): 36 execuções (fila repete algumas), 0 erros. Telegram: 22 achadinhos, 18 marcas, 7 tech (tech caindo: 38→14→7). Instagram: 25 stories ativos (piso ok), feed ok (3 Reels), seguidores 72→97 (+25), alcance 64, visitas 50, cliques no link 4. Membros: 3+2+3+3 = 11.
- META: Instagram 97 de 195 até 10/11 (no ritmo: precisa ~10/dia, fez +25). Telegram 11 de 30 até 03/11 (atrasado).
- Domingo: +30 peças no `conteudo.py` (107 no total, 98 servem para story; antes eram 68, abaixo das ~96 que 24 stories/dia com volta em 4 dias pedem). Temas novos: golpes (boleto, QR, WhatsApp), Black Friday e Natal sem urgência falsa, parcelamento, voltagem, preço por dose de whey.
- Alavanca nova (Telegram atrasado): peças "COMO ENTRAR em 10 segundos", canal Tech e canal Todas as Ofertas (não tinham peça própria), "manda pra alguém" e story "responde este story". Peça "3 canais" corrigida para 4 canais com o @ de cada um. Ensaio OK.
- Pesquisa de contas grandes: (1) stories com pergunta e resposta mantêm o público fiel → criada a peça "O que o Papa garimpa amanhã? Responde este story"; (2) intercalar oferta com conteúdo de valor, para não parecer só vitrine → o lote novo reforça dica e anticilada. Venda de seguidores e membros aparece muito nas buscas: descartado (bots, perde credibilidade).
- Próximo: BF nas BUSCAS a partir de 03/11; se tech seguir abaixo de 10/dia, incluir termos tech de loja oficial na Shopee.
- Pedido ao dono: divulgar os 4 canais uma vez no status do WhatsApp (custo zero).

## 2026-11-02 (rotina do CEO)
- Visto (01/11): 29 execuções. Telegram: 32 achadinhos, 23 marcas, 22 tech (tech voltou: 7→22, não precisa de termo tech na Shopee). Instagram: 25 stories ativos (piso ok), feed ok (3 Reels + carrossel), seguidores 97→124 (+27), alcance 55, visitas 81, cliques no link da bio só 1. Membros: 3+2+3+3 = 11, parado há 3 dias.
- META: Instagram 124 de 195 até 10/11 (no ritmo: precisa ~9/dia, fez +27). Telegram 11 de 30 até 03/11 (atrasado, não vai bater amanhã).
- 1 erro: leitura das vendas da Shopee deu "wrong type" (10010). Só avisa 1x/dia e não para nada; a consulta já foi trocada para valores escritos direto em 01/11 e não dá para saber se o erro foi antes ou depois. Vigiar em 03/11; se repetir, revisar os tipos de `conversionReport`.
- Alavanca nova (Telegram atrasado): o gargalo é o clique na bio (81 visitas → 1 clique). Agora quem comenta CANAIS (ou CANAL/TELEGRAM) em qualquer post recebe os 4 canais no direct, até nos carrosséis que mandam links de produto; a legenda padrão do feed troca "link na bio" por "Comenta CANAIS que eu te mando os 4 canais no direct". Ensaio OK.
- Próximo: medir membros em 03/11; BF nas BUSCAS a partir de 03/11; confirmar se o erro das vendas da Shopee sumiu.
- Pedido ao dono: divulgar os 4 canais uma vez no status do WhatsApp (custo zero).

## 2026-11-03 (rotina do CEO)
- Visto (02/11): 30 execuções. Telegram: 18 achadinhos, 22 marcas, 12 tech. Instagram: 25 stories ativos (piso ok), feed ok, seguidores 124→133 (+9), alcance 174 (recorde), visitas 106, **0 cliques no link da bio**; convite do story (link medido) com 0 entradas. Membros: 3+2+3+5 = 13.
- Erros: 7× limite 10030 da Shopee (busca falhava e o canal ficava sem post) e 1 story 2207052 (Meta não baixou a mídia); os dois já foram corrigidos em 02/11 (espera crescente no 10030 e checagem do link da mídia). O "wrong type" das vendas não repetiu.
- META: Instagram 133 de 195 até 10/11 (no ritmo, mas apertado: precisa ~9/dia, fez +9). Telegram 13 de 30 até 03/11 (**meta perdida**; próxima: 80 até 10/11, atrasado).
- Alavanca nova (Telegram atrasado): a bio não converte (106 visitas → 0 cliques). Os stories de convite trocam "LINK NA BIO" por "BUSCA O @ NO TELEGRAM" e o da Black Friday mostra "Busca no Telegram: @papagarimpouofertas", caminho que não depende do clique na bio.
- Black Friday nas BUSCAS (planejado): +14 termos de marca que mais vendem na data (TV LG, soundbar e Galaxy Watch Samsung, Redmi Note, Air Max, Ultraboost, kit CK, air fryer Walita, robô aspirador WAP etc.). Mesmos filtros de qualidade; a rotação não aumenta chamadas por execução. Ensaio OK.
- Próximo: medir membros em 04/11; se seguir parado, testar convite do Telegram dentro do Reels (quadro final) com o @ em destaque.
- Pedido ao dono: divulgar os 4 canais uma vez no status do WhatsApp (custo zero); conferir se o link da bio abre mesmo (0 cliques em 106 visitas pode ser link quebrado).

## 2026-11-04 (rotina do CEO)
- Visto (03/11): 34 execuções, 25 stories ativos (piso ok), feed ok (3 Reels). Telegram caiu para 12 achadinhos, 11 marcas, 12 tech (32 da Amazon, só 3 da Shopee). Seguidores 133→138 (+5), alcance 149, visitas 80, 0 cliques na bio, convite medido com 0 entradas. Membros: 3+2+4+5 = 14.
- Erros: vigia avisou "canal sem post 7 h" e "garimpo parado desde 15:45". O garimpo Amazon (rotina local) rodou só 14:39, 15:45 e 20:04; sem ele, a fila secou à tarde.
- Shopee: numa execução, 2.373 itens reprovados por não serem loja oficial e 18 esperas de limite 10030 (execução de 12 min). A regra "só loja oficial" fica; filtrar Mall direto na API exige teste com a chave, que esta rotina não tem.
- META: Instagram 138 de 195 até 10/11 (**atrasado**: precisa ~8/dia, fez +5). Telegram 14 de 80 até 10/11 (**atrasado**).
- Alavanca nova: o Reels já terminava com o convite dos 4 canais (a ideia de ontem já existia). Mudei a capa do Reels de ofertas: em vez de "ACHADOS DO PAPA", mostra "ATÉ X% OFF EM MARCA BOA" com o maior desconto real do lote (da loja, nada inventado) e "segue o Papa"; a legenda abre com o mesmo gancho e pede para seguir o @papa.garimpou. Capa encolhe a fonte se a linha não couber. Ensaio OK.
- Próximo: medir seguidores em 05/11; se o Reels não puxar, testar Reels de 1 oferta só (a mais forte do dia).
- Pedido ao dono: (1) a rotina local do garimpo Amazon precisa rodar a cada ~1–2 h entre 8h e 22h (ontem ficou 4 h parada); (2) conferir o link da bio (0 cliques há 2 dias); (3) divulgar os 4 canais no status do WhatsApp (custo zero).

## 2026-11-05 (rotina do CEO)
- Visto (04/11): 30 execuções, 25 stories ativos (piso ok), feed ok (3 Reels + posts). Telegram: 21 achadinhos, 14 marcas, 15 tech. Seguidores 138→151 (+13), **alcance 149→4.203** (no 1º dia da capa "ATÉ X% OFF" no Reels), visitas 93, 1 clique na bio, convite medido 0 entradas. Membros: 3+3+5+5 = 16.
- Erros: só o vigia ("garimpo parado desde 03/11 20:04" e "desde 12:46", tech com 2 na fila). É a rotina local do garimpo Amazon, fora deste repositório.
- META: Instagram 151 de 195 até 10/11 (no ritmo: precisa ~7/dia, fez +13). Telegram 16 de 80 até 10/11 (**atrasado**).
- Medição da loja oficial Shopee (pedida em 04/11): 2.503 itens vistos, 36 aprovados; caíram 1.532 por vendas longe, 745 por nota, 63 só por ter 250–499 vendas. Decidido: na Shopee **loja oficial** o mínimo de vendas cai de 500 para 250 (nota 4,6, desconto e lista de marcas iguais; Amazon/ML seguem 500). Loja oficial já garante original e 250+ vendas segue sendo prova social: até ~63 ofertas boas a mais por dia, menos fila seca.
- Alavanca nova (Telegram atrasado): o Reels é o que trouxe gente nova (alcance 28×) e todo Reels termina com o convite dos 4 canais. O post de achado das 09:35 vira o **4º Reels do dia** (ofertas diferentes dos outros 3; sem oferta nova, Reels de dica do banco). Mesmo número de publicações por dia. Ensaio OK.
- Próximo: medir em 06/11 se o alcance se mantém e se membros sobem; contar quantas Shopee oficiais com 250–499 vendas foram postadas.
- Pedido ao dono: (1) a rotina local do garimpo Amazon segue parando (vigia avisou 2×); (2) divulgar os 4 canais no status do WhatsApp (custo zero).

## 2026-11-06 (rotina do CEO)
- Visto (05/11): 27 execuções, 25 stories ativos (piso ok), feed ok. Telegram: 31 achadinhos, 29 marcas, 21 tech. **Seguidores 151→291 (+140, recorde)**, alcance 5.659, visitas 138, 1 clique na bio. Membros: 3+3+5+5 = 16 (parado).
- Erros: Reels 12:40 (ProcessingFailedError da Meta) e post_achado 19:15 (push recusado); os dois já corrigidos em 05/11 (até 3 novas tentativas por peça e push com 5 tentativas). Vigia: fila vazia do Marcas e tech sem oferta por 51 min (rotina local do garimpo).
- META: Instagram 291 de 195 até 10/11 (**batida antes do prazo**) → meta de 17/11 sobe 30%: 300 → 390. Telegram 16 de 80 até 10/11 (**atrasado**).
- Alavanca nova (Telegram atrasado): quem comenta QUERO no carrossel recebe a DM com os links de produto, mas sem convite do Telegram. Agora essa DM termina com "Quer achados assim todo dia, grátis? Entra no Telegram do Papa" + convite medido "ig-dm". É o lead mais quente; custo zero. Ensaio OK.
- Próximo: medir em 07/11 entradas pelo convite ig-dm e se o alcance do Reels se mantém.
- Pedido ao dono: (1) a rotina local do garimpo segue deixando a fila secar à tarde; (2) divulgar os 4 canais no status do WhatsApp (custo zero).

## 2026-11-08 (rotina do CEO, domingo)
- Visto (07/11): 32 execuções, 25 stories ativos (piso ok), feed ok (4 Reels + 4 posts). Telegram caiu para 13 achadinhos, 7 marcas, 4 tech: garimpo local parado de 06/11 13:58 a 07/11 20:17 (PC desligado), fila zerou e achadinhos ficou 8 h sem post; a reserva de 07/11 entrou à noite (reserva_resultado ainda zerado). Seguidores 380→395, alcance 85 (o pico de 5.659 não se manteve). Membros 3+3+5+5 = 16, parado há 5 dias; convites medidos (ig-dm, ig-story, ig-bio) com 0 entradas.
- META: Instagram 395 de 390 até 17/11 (**batida antes do prazo**) → meta de 27/11 sobe 30%: 600 → 780. Telegram 16 de 80 até 10/11 (**atrasado**).
- Alavanca nova (Telegram atrasado): o anúncio teve 95 cliques e 0 membro, sinal de que muita gente não tem o app. As DMs automáticas (CANAIS/TELEGRAM e QUERO do carrossel) agora terminam com "Não tem Telegram? Veja os achados no navegador: t.me/s/papagarimpouofertas", e a peça nova "SEM TELEGRAM? VEJA NO NAVEGADOR" entra no giro dos stories. Ensaio OK.
- Domingo: +30 peças no `conteudo.py` (137 no total, 125 servem para story): anticilada (kit de 1 peça, perfume barato, app de cupom), dica (ficha técnica, TV x sala, air fryer em litros), mito (garantia legal de 90 dias, art. 26; desistência na loja física), Black Friday sem urgência falsa e 4 de conversa. Artes conferidas.
- Pesquisa de contas grandes: (1) o Telegram não recomenda canal, quase todo membro novo vem do Instagram → chamada clara em toda peça (já temos rodapé + DMs); (2) destaque fixo no perfil apontando para o canal → só dá para criar pelo app.
- Próximo: medir em 09/11 se o ritmo de posts volta com o garimpo e se reserva_resultado mostra a Shopee cobrindo a fila seca.
- Pedido ao dono: (1) criar um destaque "TELEGRAM" no perfil com o story de convite (o robô não consegue pela API); (2) deixar o PC do garimpo ligado à noite e no fim de semana; (3) entrar de novo no Instagram no Chrome (login caiu em 07/11).

## 2026-11-09 (rotina do CEO)
- Visto (08/11): 22 execuções (abaixo de 20+ das outras; última às 22:44), 25 stories ativos (piso ok), feed ok (4 Reels + 5 posts). Telegram: 39 achadinhos, 33 marcas, 24 tech (a reserva Shopee segurou a fila com o garimpo local parado das 07:44 às 19:56). Seguidores 395→405 (+10), **alcance 34**, visitas 29, 1 clique na bio. Membros 3+4+5+5 = 17.
- Erros: Página do Facebook sem `pages_manage_posts` (o robô já parou de tentar); vigia de fila vazia (garimpo local).
- Achado importante: a medição dos Reels (`reels_alcance`) mostra 3 a 12 de alcance por Reels desde 02/11, inclusive em 04–05/11. O pico de 4.203–5.659 **não veio do Reels** (a leitura de 05/11 estava errada); casa com as rodadas de seguir/comentar da rotina local: em 08/11, com 0 rodadas, o alcance caiu para 34.
- META: Instagram 405 de 780 até 27/11 (**atrasado**: precisa ~21/dia, fez +10). Telegram 17 de 80 até 10/11 (**atrasado**, vai ser perdida).
- Alavanca nova: o Reels das 18h30 vira teste de **1 oferta só** (a mais forte do dia): produto com preço real da loja no 1º quadro, ~8 s, convite + "manda pra um amigo" no fim; capa registrada como `uma_oferta` para comparar com os outros 3 Reels de lista. Ensaio OK.
- Próximo: em 12/11 comparar alcance `uma_oferta` x `achados`/`ate_off`; se não passar de ~20, reduzir Reels de lista e manter só o que alcança.
- Pedido ao dono: (1) **manter as rodadas de seguir/comentar todo dia** (é o que de fato traz alcance e seguidores); (2) token novo da Página do Facebook com `pages_manage_posts` no segredo META_TOKEN; (3) PC do garimpo ligado de manhã.

## 2026-11-10 (rotina do CEO)
- Visto (09/11): 22 execuções, 25 stories ativos (piso ok), feed ok (3 Reels + carrossel + post; feed enxugado para 5/dia em 09/11, medir até 12/11). Telegram: 34 achadinhos, 29 marcas, 20 tech. Seguidores 407→413 (+6), alcance 1.815, visitas 79, 2 cliques na bio. Membros 3+5+5+5 = 18; convites medidos e DM automática seguem em 0.
- Erros: 1 timeout do Telegram (oferta não postada; não pus nova tentativa automática para não arriscar post duplicado); vigia: garimpo local parado de 08/11 19:56 até a manhã e de novo depois das 13:49; tech ficou 2 h+ sem post (reserva Shopee achou 0 por busca e só 5 "quase").
- Reels 09/11: alcance 3–4 cada, inclusive o teste `uma_oferta` (3). Ainda cedo; comparação fica para 12/11.
- META: Instagram 413 de 780 até 27/11 (**atrasado**: precisa ~22/dia, faz ~8). Telegram 18 de 80 até 10/11 (**perdida hoje**; próxima: 150 até 17/11, atrasado).
- Alavanca nova: a busca interna do Telegram acha canal pelo título e em novembro muita gente busca "black friday". Os canais Tech e Todas as Ofertas passam a ter "Black Friday" no título (descrições iguais; o robô aplica uma vez, versão 2026-11-10). Voltar ao título antigo em 01/12. Ensaio OK.
- Próximo: em 11/11 conferir `canais_info` (tudo "ok") e se membros do Tech/Geral sobem; em 12/11 decidir o Reels.
- Pedido ao dono: (1) **rodadas de seguir/comentar todo dia** no Instagram (é o que traz alcance); (2) PC do garimpo ligado o dia todo (tech secou à tarde); (3) token da Página do Facebook com `pages_manage_posts`.

## 2026-11-11 (rotina do CEO)
- Visto (10/11): 28 execuções, 25 stories ativos (piso ok), feed ok (posts 108→113: 3 Reels + carrossel + post). Telegram: 52 achadinhos, 30 marcas, 33 tech. Seguidores 413→416 (+3), alcance 3.245, visitas 141, **0 cliques na bio**. Membros 3+6+6+5 = 20 (+2: Marcas e Tech); convites medidos e DM automática seguem em 0.
- Erros: só o vigia (garimpo local parado de 09/11 18:49 até a manhã e depois das 13:50; Marcas 63 min sem fila). Reserva Shopee achou 0. Títulos "Black Friday" aplicados ok nos 4 canais.
- Reels 10/11: alcance 0–3 cada (`uma_oferta` 3, `ate_off` 0 e 3). Decisão do Reels fica para 12/11, como combinado.
- META: Instagram 416 de 780 até 27/11 (**atrasado**: precisa ~23/dia, fez +3). Telegram 20 de 150 até 17/11 (**atrasado**: precisa ~19/dia).
- Alavanca nova: Tech subiu 5→6 no 1º dia com "Black Friday" no título; Achadinhos está parado em 3 desde o início. Achadinhos e Marcas também ganham "Black Friday" no título (descrições iguais; versão 2026-11-11, o robô aplica uma vez). Voltar todos em 01/12. Ensaio OK.
- Próximo: em 12/11 conferir `canais_info` ok, membros por canal e decidir o Reels (alcance ≤5 em todos os formatos).
- Pedido ao dono: (1) **rodadas de seguir/comentar todo dia** no Instagram (alcance e seguidores vêm daí); (2) PC do garimpo ligado o dia todo; (3) token da Página do Facebook com `pages_manage_posts`.

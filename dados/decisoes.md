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

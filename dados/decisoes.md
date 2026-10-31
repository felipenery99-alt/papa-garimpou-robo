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

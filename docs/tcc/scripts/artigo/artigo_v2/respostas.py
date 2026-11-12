# -*- coding: utf-8 -*-
import os, re, shutil, sys, zipfile
from xml.sax.saxutils import escape

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
import tempfile, atexit
WORK = tempfile.mkdtemp(prefix="artigo_build_")
atexit.register(shutil.rmtree, WORK, True)
with zipfile.ZipFile(TEMPLATE) as z:
    z.extractall(WORK)

R = [  # (comentário do orientador, ajuste realizado, local no artigo)
("Capa institucional não integra o modelo de artigo.",
 "Capa removida. A primeira página segue o modelo UnC: título centralizado em caixa alta, autores alinhados à direita e afiliações em notas de rodapé (curso, instituição, cidade, estado, país e e-mail), seguidos de resumo, palavras-chave, abstract e keywords na mesma página.", "1ª página"),
("Resumo afirma implantação em produção e eficácia/reprodutibilidade.",
 "Resumo reescrito (245 palavras): explicita que a validação se restringiu a DEV e Staging, apresenta os resultados por sessão, declara como não validados a vazão de 100 req/s e o escalonamento sob picos e retira a alegação de eficácia em produção.", "Resumo / Abstract"),
("Palavras-chave: quantidade e separador.",
 "Seis palavras-chave (máximo do modelo), separadas por ponto e vírgula; mesmo padrão nas keywords.", "Resumo / Abstract"),
("Origem dos critérios de SLA; distinguir 0 falhas de disponibilidade operacional.",
 "Explicitado que os critérios foram definidos pela equipe do projeto, a partir dos requisitos não funcionais do cliente, para a fase de validação; que avaliam sessões delimitadas e não equivalem à disponibilidade operacional, que exigiria monitoramento longitudinal; e que o requisito de vazão de produção é de ordem de grandeza superior. O critério “disponibilidade 100%” foi substituído por “taxa de falhas < 1%”, como definido na documentação de testes.", "1.1"),
("Não afirmar que a lacuna de validação em produção foi preenchida.",
 "Trabalhos relacionados reescritos: o trabalho é apresentado como relato de implementação com avaliação quantitativa limitada a DEV e Staging, complementar e não substitutiva de uma avaliação em produção.", "1.3"),
("Detalhar o desenho experimental.",
 "Nova subseção 2.7: ferramentas, origem do gerador de carga (estação do autor, no Brasil), usuários, taxa de criação, duração, ausência de descarte de aquecimento, datas e horários, versões dos componentes, recursos por pod, critério de sucesso, execução única por cenário (sem inferência causal) e preservação dos relatórios brutos. Registrado como limitação que o número de réplicas e o tipo de nós durante os testes não foram capturados.", "2.7"),
("Coerência entre 15 módulos, 5 stacks e serviços; evidências reproduzíveis.",
 "Conferido no código: os 15 módulos são todos utilizados, cada um por exatamente uma stack. O Quadro 1 passou a mostrar os módulos de cada stack; a platform-k8s instala complementos via Helm, sem módulos próprios. Informado que IaC, manifestos, scripts e relatórios brutos estão em repositório privado e podem ser apresentados à banca sem dados sensíveis.", "2.1, 2.2, Quadro 1"),
("Divergência entre 4 e 3 funções Lambda.",
 "Corrigido: são três funções Lambda de MLOps (etl-delta-filter, training-launcher e register-best-model). Os seis repositórios ECR correspondem a inferência, processamento, imagem de treinamento e às três Lambdas. As duas Lambdas de relatórios com Bedrock pertencem a uma configuração Terraform à parte e foram identificadas como tal.", "2.2, 2.3, Quadro 1"),
("Inconsistência: training-launcher por evento S3 × invocação manual (seção 7.3).",
 "Reconciliado: a cadeia de CT é automática e periódica (Glue semanal → EventBridge → etl-delta-filter → evento S3 → training-launcher → register-best-model), condicionada à chegada de dados. O que não existe é o acionamento por drift ou por degradação de métricas, agora descrito assim nas duas seções. A menção a “invocação manual” foi removida.", "2.4, 4"),
("Atualização efetiva do modelo nos pods.",
 "Explicado: cada pod carrega o modelo apenas na inicialização; a promoção no MLflow não altera pods em execução; a ativação ocorre por rolling restart do Deployment, respeitando o PodDisruptionBudget; durante a janela, réplicas podem servir versões diferentes; o tempo até a ativação não foi medido (limitação).", "2.5"),
("KEDA atua no Process Service, não na API.",
 "Justificativa revisada e Quadro 2 refeito, comparando HPA (inferência, por CPU) e KEDA (processamento, por fila). Afirmado explicitamente que os resultados de latência referem-se à API e ao HPA, e que o KEDA não atua sobre eles.", "2.5, Quadro 2"),
("Anonimização, autorização e proteção dos payloads reais.",
 "Incluído parágrafo: autorização formal da empresa; testes restritos aos ambientes controlados dela; nome, e-mail e endereço já substituídos por hash nos payloads; reconhecido que BIN, últimos dígitos e hashes são dados pseudonimizados e, portanto, pessoais pela LGPD; nenhum payload ou valor individual reproduzido; resultados apenas agregados. LGPD incluída nas referências.", "2.7"),
("constant_throughput não garante vazão; informar tempo, warm-up e relatórios.",
 "Esclarecido que constant_throughput(1) limita cada usuário a no máximo 1 req/s, sem garantir a taxa, e que a vazão cai quando a latência se aproxima de 1 s. Informados duração, taxa de criação, ausência de descarte de aquecimento, análise pela série temporal e preservação dos relatórios brutos.", "2.7"),
("Figura 1 pequena e ilegível; autoria da equipe e confidencialidade.",
 "Figura ampliada para a largura total da mancha gráfica (16 cm), recortada e sem as marcações internas da empresa. Os rótulos foram reescritos cerca de 1,7 vez maiores, com nomes mais claros (por exemplo, SQS FIFO, DynamoDB, S3, Athena, AWS Glue, MLflow Registry e VPC Endpoint). Na conferência com o código, o fluxo da fila SQS foi corrigido: o serviço de inferência publica e o de processamento consome. Autoria identificada: diagrama da equipe do projeto, adaptado pelo autor.", "2.6, Figura 1"),
("Figura 1: legibilidade, título e fonte conforme o modelo.",
 "Título acima, em Arial 10 e espaçamento simples, com numeração automática; fonte abaixo, no mesmo padrão.", "Figura 1"),
("Padrão de tabelas (título, fonte, tamanho, alinhamento, bordas).",
 "Todas com título acima e numeração automática, fonte abaixo, Arial 10, espaçamento simples e chamada no texto por referência cruzada. Seguindo a ABNT/IBGE, dados textuais viraram Quadros 1 e 2 (bordas fechadas) e dados numéricos ficaram nas Tabelas 1 a 3 (traços horizontais, laterais abertas). Cabeçalho repetido e tabelas sem quebra entre páginas.", "Quadros 1–2, Tabelas 1–3"),
("P95/P99 e 0 falhas são evidências da sessão; 100 RPS não validado.",
 "Interpretação ajustada: os resultados são apresentados como evidência das sessões testadas, não da disponibilidade contínua; os critérios de latência foram atendidos apenas na sessão 2; a vazão de 100 req/s foi classificada como não validada.", "3.1, 3.3"),
("Atribuição dos picos ao keepalive exige evidência técnica.",
 "Trecho removido. Na reanálise dos relatórios brutos, não havia registro do que mudou entre as duas sessões Locust, e a troca feita nos testes sequenciais foi no cliente (reutilização de conexão), não no servidor. Sem instrumentação para comprovar a causa, a explicação por keepalive foi retirada do artigo, inclusive do resumo e da conclusão.", "3.1"),
("Diferença regional não isolada.",
 "Reformulado: a diferença entre DEV e Staging é tratada como hipótese plausível (distância de rede), e não como causa; o texto registra que os ambientes também diferem em configuração, versões e volume de dados, e que a comparação não foi isolada.", "3.2"),
("≥100 RPS não demonstrado: classificar como não validado e não extrapolar.",
 "Status alterado de “Parcial” para “Não validado”, com nota informando que 50 usuários limitam a vazão a cerca de 50 req/s e que os resultados não devem ser extrapolados linearmente.", "Tabela 3"),
("Discrepância concorrente × sequencial antes/depois; não apresentar ganho universal.",
 "A comparação “antes × após keepalive” e o percentual de −70% foram removidos. As duas sessões concorrentes são apresentadas lado a lado, sem atribuição causal: a análise por janela de 20 s mostra que a diferença está concentrada no aquecimento inicial (586 → 145 ms na sessão 1; 239 → 98 ms na sessão 2), e não houve alteração registrada no sistema entre elas.", "3.1, Tabela 1"),
("Causas do P99 não medidas; retirar validação de autoscaling sem spike.",
 "As causas do P99 aparecem como hipóteses não medidas. Afirmado que o HPA e o KEDA foram configurados e implantados, mas que o comportamento sob picos e o número de réplicas não foram observados; retirada a alegação de escalonamento validado.", "3.4"),
("Conclusão: objetivos atendidos e escalonamento validado.",
 "Conclusão reescrita, sem citações, como pede o modelo: objetivos (i) a (iv) atendidos em implementação; objetivo (v) atendido em parte (escalonamento configurado e implantado, desempenho avaliado em sessões delimitadas; vazão e comportamento sob picos não validados). O objetivo (v) foi reformulado na seção 1.2 para “configurar e avaliar”.", "1.2, 4"),
("Reconciliar invocação manual; incluir repetição, generalização e atualização do modelo.",
 "Limitações ampliadas: execução única sem repetição estatística, ambiente das sessões inferido, réplicas não registradas, vazão e picos não testados, ausência de gatilho por drift, tempo de ativação do modelo não medido e generalização restrita (DEV/Staging, um único provedor).", "4"),
("Referências: ABNT e modelo UnC, correspondência com as citações.",
 "Referências alinhadas à esquerda, em espaçamento simples, separadas por uma linha e com o título em negrito (NBR 6023). Correspondência total: 17 obras citadas e 17 listadas. Autorias corrigidas: Breck et al. (Cai, não Cain); Burns et al., 2022 (antes “Hightower; Burns; Beda”); Mäkinen et al., 2021 (coautores e evento WAIN); Treveil et al. KARIMIBIUKI et al. (2022) foi removida, pois não foi localizada nas bases consultadas, e substituída por Morris (2020). Incluídas KEDA e LGPD; removida a obra não citada (AWS Well-Architected). Citações no formato da NBR 10520:2023, como no modelo, por exemplo (Sculley et al., 2015).", "Referências"),
]
EXTRA = [
("Estrutura do artigo",
 "Reorganizada nas quatro seções do modelo UnC: 1 Introdução (problema, objetivos e referencial), 2 Material e Métodos, 3 Resultados e Discussões e 4 Conclusão. O artigo tem 14 páginas."),
("Ambiente dos testes Locust",
 "Os relatórios do Locust não registram o ambiente-alvo. A latência mínima (57 ms) é incompatível com DEV a partir do gerador no Brasil, cujas requisições sequenciais a DEV nunca ficaram abaixo de 215 ms, e coincide com o perfil de Staging; além disso, Staging era o alvo padrão da configuração na data. As sessões foram, por isso, atribuídas a Staging, com o critério explicado no texto (2.7)."),
("Sessão 1 incluída",
 "A primeira sessão Locust, cujo P95 foi de 1.100 ms, continua reportada ao lado da segunda, para evitar seleção de resultado favorável."),
]

ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
def para(text, sz=24, bold=False, jc="both", after=120, line=240):
    rp = ARIAL + f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' + ("<w:b/>" if bold else "")
    return (f'<w:p><w:pPr><w:spacing w:before="0" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
            f'<w:jc w:val="{jc}"/></w:pPr><w:r><w:rPr>{rp}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

def table(header, rows, widths):
    b = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    brd = "<w:tblBorders>" + "".join(b.format(x) for x in ["top","left","bottom","right","insideH","insideV"]) + "</w:tblBorders>"
    def cell(t, w, hdr):
        shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>' if hdr else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>'
                + para(t, 18, hdr, "center" if hdr else "left", 0) + '</w:tc>')
    out = [f'<w:tr><w:trPr><w:tblHeader/></w:trPr>' + "".join(cell(t, w, True) for t, w in zip(header, widths)) + '</w:tr>']
    for r in rows:
        out.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(t, w, False) for t, w in zip(r, widths)) + '</w:tr>')
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/>{brd}<w:tblLayout w:type="fixed"/>'
            f'<w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{"".join(out)}</w:tbl>')

body = [para("QUADRO DE RESPOSTAS AOS COMENTÁRIOS DO ORIENTADOR", 24, True, "center", 120),
        para("Artigo: Integração de MLOps em pipelines DevOps: desafios e boas práticas para entrega contínua de modelos de Machine Learning em produção", 20, False, "center", 0),
        para("Autor: Gustavo Liebl Pereira — Orientador: Prof. Marcelo Semmer", 20, False, "center", 240),
        para("Os 25 comentários estão na ordem em que aparecem no documento revisado. A coluna “Local” indica a seção ou o elemento correspondente na nova versão do artigo.", 20, False, "both", 160)]
rows = [[str(i), c, a, l] for i, (c, a, l) in enumerate(R, 1)]
body.append(table(["Nº", "Comentário (resumo)", "Ajuste realizado", "Local"], rows, [450, 2500, 4972, 1150]))
body.append(para("", 20, after=200))
body.append(para("Outras alterações relevantes", 22, True, "left", 120))
body.append(table(["Item", "Descrição"], [list(x) for x in EXTRA], [2200, 6872]))

dpath = os.path.join(WORK, "word", "document.xml")
src = open(dpath, encoding="utf-8").read()
head = src[: src.index("<w:body>") + len("<w:body>")]
sect = re.search(r"<w:sectPr.*?</w:sectPr>", src, re.S).group(0)
sect = re.sub(r'w:top="\d+"', 'w:top="1134"', sect)
open(dpath, "w", encoding="utf-8").write(head + "".join(body) + sect + "</w:body></w:document>")
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(WORK, "[Content_Types].xml"), "[Content_Types].xml")
    for root, _, files in os.walk(WORK):
        for f in files:
            arc = os.path.relpath(os.path.join(root, f), WORK)
            if arc != "[Content_Types].xml":
                z.write(os.path.join(root, f), arc)
print("ok", len(R), "respostas")

# -*- coding: utf-8 -*-
"""Monta o artigo final do TCC em .docx, aplicando o guia ABNT e as correcoes pendentes."""
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/02_artigo/v4_2026-09-11_entrega-setembro/Artigo_TCC_MLOps_Gustavo_Liebl_Pereira_Entrega_Set2026.docx"
ANEXO_IMG_DIR = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/assets/anexo_arquitetura_imgs"

# Versao enxuta (entrega parcial de desenvolvimento, limite de 15 paginas
# comentado pelo orientador): mantém apenas a figura de visão geral como
# referência; as demais (elo-04/05/06) seguem disponíveis no repositório.
DIAGRAMAS_REFERENCIA = [
    ("elo-03.png", "Visão Geral da Infraestrutura"),
]

FONT_NAME = "Times New Roman"

# ---------------------------------------------------------------- helpers --

def set_page_format(section):
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)


def add_field(paragraph, field_code):
    run = paragraph.add_run()
    fld_char1 = OxmlElement('w:fldChar')
    fld_char1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = field_code
    fld_char2 = OxmlElement('w:fldChar')
    fld_char2.set(qn('w:fldCharType'), 'separate')
    fld_char3 = OxmlElement('w:fldChar')
    fld_char3.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    run._r.append(fld_char3)


MD_TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")


def add_md_runs(paragraph, text, base_size=12, base_italic=False):
    """Converte **negrito**, *italico* e `codigo` em runs formatados."""
    parts = MD_TOKEN_RE.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
            run.italic = base_italic
        elif part.startswith("*") and part.endswith("*") and len(part) > 1:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Courier New"
        else:
            run = paragraph.add_run(part)
            run.italic = base_italic
        run.font.size = Pt(base_size)
        if not (part.startswith("`") and part.endswith("`")):
            run.font.name = FONT_NAME


def body_paragraph(doc, text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, space_after=0):
    p = doc.add_paragraph()
    p.alignment = align
    fmt = p.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(space_after)
    if indent:
        fmt.first_line_indent = Cm(1.25)
    add_md_runs(p, text, base_size=size)
    return p


def set_outline_level(paragraph, level):
    """Marca o paragrafo com o nivel de esboco do Word (0-indexado) para que o
    campo TOC \\o "1-3" tenha o que indexar - sem isso o Sumario fica vazio."""
    pPr = paragraph._p.get_or_add_pPr()
    el = OxmlElement("w:outlineLvl")
    el.set(qn("w:val"), str(level))
    rPr = pPr.find(qn("w:rPr"))
    if rPr is not None:
        rPr.addprevious(el)
    else:
        pPr.append(el)


def heading1(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    text = f"{number} {title}" if number else title
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = FONT_NAME
    set_outline_level(p, 0)
    return p


def heading2(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    run = p.add_run(f"{number} {title}")
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = FONT_NAME
    set_outline_level(p, 1)
    return p


def heading3(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    run = p.add_run(f"{number} {title}")
    run.italic = True
    run.bold = True
    run.font.size = Pt(12)
    run.font.name = FONT_NAME
    set_outline_level(p, 2)
    return p


def force_update_fields(doc):
    """updateFields deve respeitar a ordem do schema CT_Settings: depois de
    characterSpacingControl, antes de footnotePr/compat."""
    settings = doc.settings.element
    existing = settings.find(qn("w:updateFields"))
    if existing is not None:
        settings.remove(existing)
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    anchor = settings.find(qn("w:footnotePr")) or settings.find(qn("w:compat"))
    if anchor is not None:
        anchor.addprevious(el)
    else:
        settings.insert(0, el)


def centered_title(doc, text, size=14, bold=True, space_before=0, space_after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = FONT_NAME
    return p


def add_table_caption(doc, label, title, above=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f"{label} — {title}")
    run.font.size = Pt(10)
    run.font.name = FONT_NAME
    return p


def add_source_note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.name = FONT_NAME
    return p


def add_simple_table(doc, header_row, rows):
    table = doc.add_table(rows=1, cols=len(header_row))
    table.style = "Light Grid Accent 1"
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(header_row):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.name = FONT_NAME
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(10)
            run.font.name = FONT_NAME
    return table


def page_break(doc):
    doc.add_page_break()


def add_diagrama_referencia(doc, fig_num, img_filename, subtitulo):
    """Insere um diagrama de referencia do estudo de caso (documentacao tecnica
    original, cliente anonimizado) como figura numerada, com legenda e fonte."""
    fig_p = doc.add_paragraph()
    fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fig_run = fig_p.add_run()
    fig_run.add_picture(f"{ANEXO_IMG_DIR}/{img_filename}", width=Cm(10))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(f"Figura {fig_num} — Arquitetura de Referência do Estudo de Caso: {subtitulo}")
    run.font.size = Pt(10)
    run.font.name = FONT_NAME
    src = doc.add_paragraph()
    src.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = src.add_run("Fonte: documentação técnica do estudo de caso (cliente anonimizado).")
    run.font.size = Pt(10)
    run.font.name = FONT_NAME
    doc.add_paragraph()


# --------------------------------------------------------------- document --

doc = Document()

# Normal style base
normal = doc.styles["Normal"]
normal.font.name = FONT_NAME
normal.font.size = Pt(12)

section = doc.sections[0]
set_page_format(section)

# ====================================================== CAPA (enxuta) ======
# Entrega parcial de desenvolvimento (limite de 15 páginas comentado pelo
# orientador): sem folha de aprovação (banca ainda não ocorreu) e sem listas
# de figuras/tabelas/abreviaturas/sumário separadas, que cabem na versão
# final formatada para a banca.
for _ in range(2):
    doc.add_paragraph()
centered_title(doc, "CURSO DE ENGENHARIA DE SOFTWARE", size=12, bold=False)
doc.add_paragraph()
centered_title(doc, "GUSTAVO LIEBL PEREIRA", size=12, bold=False)
for _ in range(3):
    doc.add_paragraph()
centered_title(
    doc,
    "INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS "
    "PRÁTICAS PARA ENTREGA CONTÍNUA DE MODELOS DE MACHINE "
    "LEARNING EM PRODUÇÃO",
    size=14, bold=True,
)
for _ in range(6):
    doc.add_paragraph()
centered_title(doc, "MAFRA", size=12, bold=False)
centered_title(doc, "2026", size=12, bold=False)
page_break(doc)

# ============================================================== RESUMO =====
centered_title(doc, "RESUMO", size=12, bold=True, space_after=12)
RESUMO = (
    "Este trabalho apresenta o projeto e a implementação de uma plataforma "
    "de MLOps integrada a pipelines de DevOps, desenvolvida e implantada em "
    "ambiente de produção real de uma empresa de grande porte do setor de "
    "pagamentos eletrônicos, com infraestrutura em nuvem AWS. O objetivo "
    "geral consiste em demonstrar como automatizar o ciclo de vida completo "
    "de modelos de *Machine Learning* em produção, desde o provisionamento "
    "da infraestrutura até o escalonamento dinâmico da inferência. A "
    "metodologia adota uma abordagem de pesquisa aplicada com caráter "
    "experimental, estruturada em quatro fases: levantamento bibliográfico, "
    "desenvolvimento de infraestrutura como código (IaC) com Terraform, "
    "implementação de pipelines de integração e entrega contínuas (CI/CD) e "
    "treinamento contínuo (CT), e validação experimental por meio de testes "
    "de carga. A infraestrutura foi codificada em 15 módulos Terraform "
    "organizados em cinco *stacks* independentes. Os pipelines de CI/CD "
    "utilizam AWS CodeBuild para construção e publicação de imagens Docker, "
    "enquanto o ciclo de vida do modelo é gerenciado por funções AWS Lambda "
    "que disparam *jobs* de treinamento no Amazon SageMaker e promovem "
    "automaticamente o melhor modelo no MLflow Registry com base em "
    "métricas de desempenho. O serviço de inferência, implementado com "
    "FastAPI no Amazon EKS, escala horizontalmente por meio do KEDA "
    "(*Kubernetes Event-driven Autoscaling*) utilizando a profundidade da "
    "fila Amazon SQS como métrica de escalonamento. Os testes de carga "
    "evidenciaram que a ausência de *HTTP keepalive* nas conexões entre "
    "componentes de rede gerava picos de latência de até 5.217 ms; após a "
    "correção, o percentil P95 reduziu-se em 70%, de 1.100 ms para 330 ms, "
    "com zero falhas em mais de 6.000 requisições. Conclui-se que a "
    "separação arquitetural explícita entre CI/CD e Treinamento Contínuo, "
    "aliada à automação *serverless* e ao escalonamento orientado a "
    "eventos, constitui uma abordagem eficaz e reproduzível para a entrega "
    "contínua de modelos de *Machine Learning* em produção."
)
body_paragraph(doc, RESUMO, indent=False)
kw = doc.add_paragraph()
kw.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
run = kw.add_run("Palavras-chave: ")
run.bold = True
run.font.name = FONT_NAME
run.font.size = Pt(12)
run2 = kw.add_run(
    "MLOps. DevOps. Kubernetes. Infraestrutura como Código. Entrega "
    "Contínua de Modelos. Aprendizado de Máquina."
)
run2.font.name = FONT_NAME
run2.font.size = Pt(12)
page_break(doc)

# ============================================================= ABSTRACT ====
centered_title(doc, "ABSTRACT", size=12, bold=True, space_after=12)
ABSTRACT = (
    "This work presents the design and implementation of an MLOps platform "
    "integrated into DevOps pipelines, developed and deployed in a real "
    "production environment of a large-scale electronic payments company "
    "on AWS cloud infrastructure. The general objective is to demonstrate "
    "how to automate the complete lifecycle of Machine Learning models in "
    "production, from infrastructure provisioning to dynamic inference "
    "scaling. The methodology follows an applied research approach with an "
    "experimental design, structured in four phases: literature review, "
    "infrastructure-as-code (IaC) development with Terraform, "
    "implementation of continuous integration and delivery (CI/CD) and "
    "continuous training (CT) pipelines, and experimental validation "
    "through load testing. The infrastructure was codified in 15 Terraform "
    "modules organized across five independent stacks. CI/CD pipelines use "
    "AWS CodeBuild to build and publish Docker images, while the model "
    "lifecycle is managed by AWS Lambda functions that trigger Amazon "
    "SageMaker training jobs and automatically promote the best-performing "
    "model in the MLflow Registry based on performance metrics. The "
    "inference service, implemented with FastAPI on Amazon EKS, scales "
    "horizontally through KEDA (Kubernetes Event-driven Autoscaling) using "
    "Amazon SQS queue depth as the scaling metric. Load tests revealed "
    "that the absence of HTTP keepalive in inter-component network "
    "connections caused latency spikes of up to 5,217 ms; after the fix, "
    "the P95 latency percentile decreased by 70%, from 1,100 ms to 330 ms, "
    "with zero failures across more than 6,000 requests. The study "
    "concludes that the explicit architectural separation between CI/CD "
    "and Continuous Training, combined with serverless automation and "
    "event-driven autoscaling, constitutes an effective and reproducible "
    "approach for continuous delivery of Machine Learning models in "
    "production environments."
)
body_paragraph(doc, ABSTRACT, indent=False)
kw = doc.add_paragraph()
kw.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
run = kw.add_run("Keywords: ")
run.bold = True
run.font.name = FONT_NAME
run.font.size = Pt(12)
run2 = kw.add_run(
    "MLOps. DevOps. Kubernetes. Infrastructure as Code. Continuous Model "
    "Delivery. Machine Learning."
)
run2.font.name = FONT_NAME
run2.font.size = Pt(12)
page_break(doc)

print("Pre-textual OK, iniciando corpo do artigo...")

# =========================================================================
#  TEXTUAIS — numeracao de pagina inicia aqui (secao propria)
# =========================================================================
body_section = doc.add_section(WD_SECTION.CONTINUOUS)
set_page_format(body_section)
footer = body_section.footer
footer.is_linked_to_previous = False
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_field(fp, "PAGE")

# ---------------------------------------------------------------- 1 -------
heading1(doc, "1", "INTRODUÇÃO")
body_paragraph(
    doc,
    "A evolução da Inteligência Artificial (IA) transformou a maneira como "
    "organizações extraem valor de seus dados. No entanto, a transição de "
    "um modelo experimental para um sistema produtivo resiliente permanece "
    "como um dos maiores gargalos da Engenharia de Software moderna. "
    "Enquanto o DevOps consolidou a agilidade no desenvolvimento de "
    "software tradicional, sistemas de Aprendizado de Máquina introduzem "
    "variáveis adicionais: a dependência de dados voláteis e a necessidade "
    "de monitoramento constante de performance algorítmica.",
)
body_paragraph(
    doc,
    "Este projeto propõe o desenvolvimento de uma plataforma que integra "
    "práticas de MLOps (*Machine Learning Operations*) a pipelines de "
    "DevOps existentes. O foco reside na automação do ciclo de vida "
    "completo do modelo, desde o provisionamento da infraestrutura como "
    "código (IaC) até o escalonamento dinâmico de inferências em ambiente "
    "de nuvem, utilizando uma arquitetura moderna baseada em Kubernetes e "
    "provedores de nuvem gerenciados.",
)

# ---------------------------------------------------------------- 2 -------
heading1(doc, "2", "PROBLEMA E OBJETIVOS")
heading2(doc, "2.1", "Problema de Pesquisa")
body_paragraph(
    doc,
    "Sistemas de ML dependem não apenas de código, mas da evolução "
    "contínua dos dados e das métricas de performance do próprio modelo, "
    "o que gera desafios de versionamento e degradação (*model drift*). "
    "Grande parte dos projetos de ciência de dados não atinge o ambiente "
    "de produção devido à falta de uma ponte estruturada entre os "
    "ambientes de experimentação e as operações de TI. Diante desse "
    "cenário, busca-se responder: Como integrar de forma eficiente e "
    "automatizada o ciclo de vida de modelos de *Machine Learning* "
    "(MLOps) em pipelines tradicionais de DevOps, garantindo a entrega "
    "contínua em ambientes complexos?",
)
heading2(doc, "2.2", "Objetivos")
body_paragraph(
    doc,
    "O objetivo geral deste trabalho é desenvolver e implementar uma "
    "arquitetura de MLOps funcional integrada a pipelines de DevOps, "
    "estabelecendo um ecossistema automatizado para a entrega e operação "
    "contínua de modelos. Para tal, definem-se os objetivos específicos: "
    "(i) projetar as camadas de integração DevOps/MLOps; (ii) implementar "
    "infraestrutura como código (IaC) via Terraform; (iii) desenvolver "
    "pipelines de CI/CD/CT; (iv) implementar governança via MLflow; e "
    "(v) validar o escalonamento via KEDA.",
)

# ---------------------------------------------------------------- 3 -------
heading1(doc, "3", "REFERENCIAL TEÓRICO")
body_paragraph(
    doc,
    "O referencial teórico deste trabalho fundamenta-se na convergência "
    "entre engenharia de software e operações de dados.",
)
body_paragraph(
    doc,
    "**Dívida técnica em sistemas de ML.** Segundo Sculley et al. "
    "(2015), o código de ML é só uma pequena fração de um sistema "
    "produtivo — o esforço maior está em configuração, dados e "
    "monitoramento; Breck et al. (2017) operacionalizam esse cuidado "
    "com o *ML Test Score*, testes de prontidão para produção.",
)
body_paragraph(
    doc,
    "**MLOps e Continuous Training (CT).** MLOps padroniza o ciclo de "
    "vida de ML versionando código, modelos e dados (KREUZBERGER et "
    "al., 2023); seu diferencial é o CT, que retreina automaticamente "
    "diante do *concept drift* (GAMA et al., 2014). O MLflow (ZAHARIA "
    "et al., 2018) viabiliza esse ciclo, estendendo aos dados e modelos "
    "os princípios de *Continuous Delivery* de Humble e Farley (2010).",
)
body_paragraph(
    doc,
    "**IaC na nuvem.** O Terraform garante paridade entre ambientes e "
    "escalabilidade imediata (KARIMIBIUKI et al., 2022); a "
    "modularização em *stacks* por domínio segue as práticas de Brikman "
    "(2019).",
)
body_paragraph(
    doc,
    "**Escalabilidade com KEDA.** O EKS gerencia o plano de controle "
    "Kubernetes (HIGHTOWER; BURNS; BEDA, 2022); para *serving* de baixa "
    "latência, o KEDA escala réplicas por eventos (ex.: profundidade de "
    "fila SQS), consumindo recursos só sob demanda real.",
)

# ---------------------------------------------------------------- 4 -------
heading1(doc, "4", "METODOLOGIA")
body_paragraph(
    doc,
    "Este trabalho classifica-se como **pesquisa aplicada de caráter "
    "experimental e construtivo**: o sistema implementado é tanto o "
    "artefato quanto o instrumento de validação, desenvolvido em uma "
    "empresa de grande porte do setor de pagamentos eletrônicos, com "
    "dados reais de transações em infraestrutura AWS. O trabalho foi "
    "estruturado em quatro fases sequenciais, descritas a seguir.",
)

heading2(doc, "4.1", "Fase 1 — Levantamento Bibliográfico")
body_paragraph(
    doc,
    "A pesquisa bibliográfica (IEEE Xplore, ACM Digital Library, Google "
    "Scholar) priorizou trabalhos com implementações validadas "
    "empiricamente e identificou lacunas que orientaram a arquitetura: "
    "CI/CD e CT tratados como um único fluxo (SCULLEY et al., 2015; "
    "KREUZBERGER et al., 2023); autoscaling por eventos (KEDA) pouco "
    "explorado frente a CPU (HIGHTOWER; BURNS; BEDA, 2022); e o impacto "
    "de *HTTP keepalive* em cadeias de inferência com múltiplos saltos "
    "pouco documentado.",
)

heading2(doc, "4.2", "Fase 2 — Projeto e Desenvolvimento da Infraestrutura")
body_paragraph(
    doc,
    "Toda a infraestrutura foi codificada em **Terraform 1.14**, "
    "organizada em **15 módulos reutilizáveis** (`vpc`, `s3`, `eks`, "
    "`ecr`, `sqs`, `dynamodb`, `lambda`, `mlflow`, `sagemaker-studio`, "
    "`api-gateway`, `nlb`, `firehose`, `glue`, `athena`, "
    "`bedrock-agent`) instanciados por **5 *stacks* independentes** por "
    "ambiente — modularização por domínio funcional, não por ambiente.",
)
add_table_caption(doc, "Tabela 1", "Sequência de Stacks e Responsabilidades")
add_simple_table(
    doc,
    ["Ordem", "Stack", "Responsabilidade"],
    [
        ["1", "foundation", "VPC, subnets privadas/públicas (2 AZs), 7 buckets S3 por ambiente"],
        ["2", "mlops", "SageMaker Managed MLflow Tracking Server + SageMaker Studio Domain"],
        ["3", "platform", "EKS 1.32, ECR, SQS FIFO, DynamoDB, Kinesis Firehose, API Gateway, NLB, Glue, Athena"],
        ["4", "platform-k8s", "Deployments Kubernetes, KEDA 2.18.3, AWS Load Balancer Controller, Ingress"],
        ["5", "platform-lambdas", "3 funções Lambda containerizadas (imagens ECR)"],
    ],
)
add_source_note(doc, "Fonte: elaboração do autor.")
body_paragraph(
    doc,
    "Os 7 buckets S3 por ambiente (`data-raw`, `data-processed`, "
    "`models`, `logs`, `resources`, `reports-promotion`, "
    "`reports-statistics`) isolam responsabilidades no *data lake*. O "
    "estado Terraform de cada *stack* é armazenado em *backend* S3 com "
    "bloqueio nativo (`use_lockfile`), sem DynamoDB auxiliar, e as "
    "*stacks* superiores consomem os *outputs* das inferiores via "
    "`terraform_remote_state`, eliminando dependências circulares.",
)
body_paragraph(
    doc,
    "Os dois ambientes — **DEV** (`us-east-1`) e **Staging** "
    "(`sa-east-1`, mais próximo do perfil produtivo) — replicam as 5 "
    "*stacks* de forma independente sobre **EKS 1.32**. O *MLflow "
    "Tracking Server* é gerenciado pelo SageMaker, eliminando a "
    "operação de servidor sem perder compatibilidade com a API padrão "
    "do MLflow.",
)

heading2(doc, "4.3", "Fase 3 — Implementação dos Pipelines")
body_paragraph(
    doc,
    "A fase de implementação produziu três trilhas de automação com "
    "responsabilidades distintas e nenhuma dependência de código entre "
    "elas.",
)
heading3(doc, "4.3.1", "Trilha CI/CD — AWS CodeBuild")
body_paragraph(
    doc,
    "O AWS CodeBuild automatiza a infraestrutura operacional via "
    "*buildspecs* declarativos versionados no repositório, sincronizando "
    "políticas IAM nos clusters EKS de DEV e Staging. As imagens Docker "
    "dos 6 serviços (inferência, processamento, e as 4 Lambdas de MLOps) "
    "são versionadas em repositórios ECR dedicados; o serviço de "
    "inferência roda em Python 3.12 com usuário não-*root*.",
)
heading3(doc, "4.3.2", "Trilha CT — Treinamento Contínuo (event-driven)")
body_paragraph(
    doc,
    "O ciclo de Treinamento Contínuo é uma **cadeia de eventos "
    "*serverless*** sem agendadores centralizados: o **Glue Job** "
    "semanal agrega os *logs* de inferência em Delta Lake; o "
    "**EventBridge** aciona a Lambda `etl-delta-filter`, que gera "
    "Parquets incrementais; um evento S3 aciona a Lambda "
    "`training-launcher`, que despacha um *SageMaker Training Job* "
    "(XGBoost), registrando métricas no MLflow; ao concluir, a Lambda "
    "`register-best-model` compara o F1-score com o modelo em produção "
    "e só promove a nova versão no *MLflow Registry* se ela for "
    "superior — sem intervenção manual.",
)
heading3(doc, "4.3.3", "Trilha de Inferência — FastAPI + EKS + HPA/KEDA")
body_paragraph(
    doc,
    "O serviço de inferência é uma API REST **FastAPI** (Python 3.12) "
    "no Amazon EKS. O fluxo de rede percorre API Gateway → VPC Link → "
    "NLB → *pod* EKS via `TargetGroupBinding` (alvo IP), sem "
    "*Application Load Balancer*. O modelo é carregado diretamente do "
    "**MLflow Registry** na inicialização do *pod* (*tag* `stage: "
    "production`), sem *endpoint* SageMaker dedicado — o *deploy* de um "
    "novo modelo ocorre automaticamente na próxima substituição de "
    "*pod*. O Inference Service escala por um **HPA** tradicional "
    "baseado em CPU (min. 8 / máx. 10 réplicas, *threshold* 50%), "
    "enquanto o **KEDA 2.18.3** escala o Process Service (*worker* "
    "assíncrono) via `ScaledObject` que monitora a profundidade da fila "
    "**SQS FIFO** (`elo-fraud-resultset-dev.fifo`) — dois mecanismos "
    "distintos para dois perfis de carga:",
)
add_table_caption(doc, "Tabela 2", "Configuração do ScaledObject KEDA (DEV)")
add_simple_table(
    doc,
    ["Parâmetro KEDA", "Valor DEV"],
    [
        ["Mínimo de réplicas", "2 (compatível com PDB minAvailable: 1)"],
        ["Máximo de réplicas", "5"],
        ["Mensagens por pod", "30 (escala +1 pod a cada 30 mensagens)"],
        ["Intervalo de polling", "15 segundos"],
        ["Scale-up", "Imediato (stabilizationWindowSeconds: 0)"],
        ["Scale-down", "Após 60s de cooldown + 120s de estabilização"],
    ],
)
add_source_note(doc, "Fonte: elaboração do autor.")
body_paragraph(
    doc,
    "A escolha da profundidade de fila como métrica de escalonamento — "
    "em lugar de CPU — é justificada pelo perfil de carga de inferência: "
    "*bursty*, com picos de chegada de mensagens desacoplados do "
    "consumo de CPU dos *pods*.",
)

heading2(doc, "4.4", "Fase 4 — Validação Experimental")
body_paragraph(
    doc,
    "A validação foi realizada com **Locust** (Python), simulando "
    "usuários virtuais concorrentes a **1 usuário = 1 RPS** "
    "(*constant_throughput*). O corpus de teste usa **100 *payloads* "
    "reais** de transações 3DS do ambiente de produção (não dados "
    "sintéticos), percorridos em sequência *round-robin* entre usuários "
    "concorrentes. O critério de sucesso por requisição é HTTP 200 com "
    "campo `score` no *body* JSON; qualquer desvio (4xx, 5xx, *timeout* "
    "ou JSON inválido) conta como falha.",
)
body_paragraph(
    doc,
    "Foram executados 5 cenários: três sequenciais de 100 requisições "
    "(DEV antes e após a otimização de *keepalive*, e Staging após a "
    "otimização), que isolam o comportamento requisição a requisição e "
    "revelam anomalias mascaradas por estatísticas agregadas; e dois "
    "Locust concorrentes de 50 usuários em DEV (antes e após a "
    "otimização), que medem P50–P99, *throughput* médio e taxa de "
    "falhas sob carga real. Os critérios de aceitação do SLA — "
    "disponibilidade 100%, P95 < 500 ms, P99 < 1.000 ms e *throughput* "
    "≥ 100 RPS — e os resultados obtidos são consolidados na Tabela 6 "
    "(Seção 6.5).",
)

# ---------------------------------------------------------------- 5 -------
heading1(doc, "5", "MODELAGEM DA SOLUÇÃO")
body_paragraph(doc, "A solução proposta integra ferramentas de automação para criar um fluxo de dados ininterrupto.")
heading2(doc, "5.1", "Descrição da Abordagem")
body_paragraph(
    doc,
    "O fluxo opera em duas trilhas complementares. Na **trilha de "
    "serving**, um commit aciona o AWS CodeBuild, que constrói a imagem "
    "Docker do serviço de inferência, publica no ECR e atualiza o "
    "*deployment* no EKS. Na **trilha de MLOps**, a Lambda "
    "`training-launcher` dispara um SageMaker Training Job (XGBoost) "
    "sobre dados Parquet do S3, registrando métricas no MLflow; ao "
    "final, a Lambda `register-best-model` compara o resultado com o "
    "modelo em produção e promove o novo modelo no MLflow Registry se "
    "houver melhoria. O serviço de inferência carrega o modelo "
    "diretamente via MLflow (sem SageMaker Endpoint); o HPA escala o "
    "Inference Service por CPU e o KEDA escala o Process Service pela "
    "profundidade da fila SQS FIFO.",
)
heading2(doc, "5.2", "Diagrama de Arquitetura Técnica")
body_paragraph(
    doc,
    "A arquitetura integra cinco fluxos, detalhados na Seção 4.3: "
    "**(1)** inferência síncrona (API Gateway → VPC Link → NLB → "
    "Inference Service); **(2)** processamento assíncrono e logging "
    "(SQS FIFO → Process Service → DynamoDB/Firehose → S3); **(3)** "
    "Treinamento Contínuo *event-driven* (Glue → Lambdas → SageMaker → "
    "MLflow); **(4)** observabilidade generativa (*cron* → Lambdas → "
    "Athena/MLflow → Bedrock → S3); e **(5)** IaC/CI/CD (CodeBuild → "
    "ECR; Terraform provisionando toda a infraestrutura).",
)

body_paragraph(
    doc,
    "Os diagramas de referência do estudo de caso original (visão geral "
    "da infraestrutura e fluxos de inferência, processamento e "
    "treinamento), elaborados pela própria equipe do projeto, estão "
    "disponíveis no repositório do projeto como material complementar à "
    "descrição textual acima.",
)

# ---------------------------------------------------------------- 6 -------
heading1(doc, "6", "RESULTADOS E DISCUSSÃO")
body_paragraph(
    doc,
    "Esta seção apresenta os resultados dos testes de desempenho "
    "realizados sobre o serviço de inferência em produção, analisa o "
    "comportamento observado e discute as implicações para a entrega "
    "contínua de modelos de *Machine Learning*.",
)
heading2(doc, "6.1", "Metodologia dos Testes de Carga")
body_paragraph(
    doc,
    "Os testes foram executados com Locust (Python), com 100 *payloads* "
    "reais de transações 3DS percorridos em sequência *round-robin* por "
    "usuários virtuais concorrentes (1 usuário = 1 RPS), contra dois "
    "ambientes AWS: **DEV** (`us-east-1`) e **Staging** (`sa-east-1`, "
    "pré-produção).",
)
heading2(doc, "6.2", "Resultados dos Testes Locust (Carga Concorrente)")
body_paragraph(
    doc,
    "Foram realizadas duas sessões de teste Locust em DEV na mesma "
    "data, separadas por menos de duas horas, antes e após uma "
    "otimização identificada durante o processo de investigação.",
)
add_table_caption(doc, "Tabela 3", "Comparativo Antes × Após Otimização de Keepalive (DEV)")
add_simple_table(
    doc,
    ["Métrica", "Antes", "Após", "Redução"],
    [
        ["Requisições totais", "5.870", "6.040", "—"],
        ["Falhas", "0", "0", "—"],
        ["Throughput médio", "45,9 RPS", "46,9 RPS", "—"],
        ["Latência média", "324 ms", "133 ms", "−59%"],
        ["P50", "170 ms", "100 ms", "−41%"],
        ["P75", "420 ms", "150 ms", "−64%"],
        ["P90", "810 ms", "240 ms", "−70%"],
        ["P95", "1.100 ms", "330 ms", "−70%"],
        ["P99", "1.600 ms", "510 ms", "−68%"],
        ["Máximo", "2.100 ms", "770 ms", "−63%"],
    ],
)
add_source_note(doc, "Fonte: dados da pesquisa, 2026.")
body_paragraph(
    doc,
    "Após a otimização, o serviço atingiu **P95 de 330 ms**, abaixo da "
    "meta de 500 ms, e **P99 de 510 ms**, abaixo da meta de 1.000 ms, "
    "com **0 falhas** em ambos os experimentos. O throughput médio se "
    "manteve em ~47 RPS durante os dois testes de 2 minutos com 50 "
    "usuários concorrentes.",
)
heading2(doc, "6.3", "Investigação e Correção: O Problema de Cold Start por Ausência de HTTP Keepalive")
body_paragraph(
    doc,
    "A diferença de desempenho entre os dois testes Locust motivou uma "
    "investigação com testes sequenciais de 100 requisições "
    "individuais, permitindo identificar o comportamento requisição a "
    "requisição.",
)
add_table_caption(doc, "Tabela 4", "Latências Sequenciais Antes e Após Keepalive (DEV, 100 req.)")
add_simple_table(
    doc,
    ["Métrica", "Antes do Keepalive", "Após Keepalive"],
    [
        ["Latência média", "279 ms", "287 ms"],
        ["Mediana (P50)", "190,6 ms", "278,9 ms"],
        ["Mínimo", "168 ms", "215 ms"],
        ["Máximo", "5.217 ms", "423 ms"],
        ["P90", "223 ms", "328 ms"],
        ["P95", "236 ms", "345 ms"],
        ["P99", "5.217 ms", "423 ms"],
        ["Spikes > 1.000 ms", "3 ocorrências", "0 ocorrências"],
    ],
)
add_source_note(doc, "Fonte: dados da pesquisa, 2026.")
body_paragraph(
    doc,
    "Antes da correção, três requisições apresentaram latências "
    "anômalas (5.217 ms, 2.605 ms e 1.258 ms), com as demais na faixa "
    "normal de 168–240 ms — padrão típico de reconexão TCP: sem "
    "*keepalive*, cada requisição que encontrava a conexão encerrada "
    "precisava de um novo *handshake* com o serviço *upstream* (NLB → "
    "*pod*), somando centenas a milhares de ms ao tempo total. Após "
    "habilitar o *keepalive*, os picos desapareceram (máximo de "
    "5.217 ms para 423 ms), confirmando que componentes intermediários "
    "na cadeia de rede amplificam o custo de reconexões — efeito "
    "invisível em requisição única, mas severo sob carga concorrente.",
)
heading2(doc, "6.4", "Resultados no Ambiente de Staging")
add_table_caption(doc, "Tabela 5", "Latências Sequenciais no Ambiente Staging (100 req.)")
add_simple_table(
    doc,
    ["Métrica", "Staging (keepalive)", "DEV (keepalive)"],
    [
        ["Latência média", "103 ms", "287 ms"],
        ["Mediana", "103 ms", "279 ms"],
        ["Mínimo", "72,6 ms", "215 ms"],
        ["Máximo", "157,8 ms", "423 ms"],
        ["P90", "114,5 ms", "328 ms"],
        ["P95", "123,9 ms", "345 ms"],
        ["Spikes > 1.000 ms", "0", "0"],
    ],
)
add_source_note(doc, "Fonte: dados da pesquisa, 2026.")
body_paragraph(
    doc,
    "A latência média de 103 ms no Staging é 64% menor que no DEV "
    "(287 ms) — diferença geográfica: Staging está na mesma região AWS "
    "(`sa-east-1`) da produção real, enquanto o DEV (`us-east-1`) tem "
    "RTT mais alto a partir da localização dos testes.",
)
heading2(doc, "6.5", "Consolidação e Validação do SLA")
add_table_caption(doc, "Tabela 6", "Validação Final do SLA")
add_simple_table(
    doc,
    ["Critério SLA", "Meta", "Resultado DEV", "Resultado Staging", "Status"],
    [
        ["Disponibilidade", "100%", "100% (0 falhas / 6.040 req.)", "100%", "Atingido"],
        ["P95 latência", "< 500 ms", "330 ms", "124 ms", "Atingido"],
        ["P99 latência", "< 1.000 ms", "510 ms", "—", "Atingido"],
        ["Throughput", "≥ 100 RPS", "~47 RPS (50 usuários)", "—", "Parcial*"],
    ],
)
add_source_note(
    doc,
    "(*) O throughput de ~47 RPS foi atingido com 50 usuários virtuais "
    "(1 usuário = 1 RPS). O teste com 100 usuários simultâneos — "
    "configuração que projeta 100 RPS — não consta nos relatórios "
    "disponíveis. Fonte: dados da pesquisa, 2026.",
)
heading2(doc, "6.6", "Discussão")
body_paragraph(
    doc,
    "**Impacto da otimização de keepalive.** A habilitação do *HTTP "
    "keepalive* foi a intervenção isolada de maior impacto do projeto: "
    "redução do P95 de 1.100 ms para 330 ms (−70%) sem qualquer "
    "alteração de infraestrutura, modelo ou código de inferência. O "
    "tempo médio de 133 ms na carga concorrente otimizada cobre todo o "
    "percurso (API Gateway → VPC Link → NLB → *pod* FastAPI → DynamoDB "
    "→ MLflow → XGBoost); com P50 em 100 ms, o pipeline completo já "
    "opera abaixo de 100 ms na mediana.",
)
body_paragraph(
    doc,
    "**Variabilidade residual e autoscaling.** A diferença entre P50 "
    "(100 ms) e P99 (510 ms) é atribuída a consultas ao DynamoDB para "
    "clientes com histórico extenso, recarregamento do modelo MLflow em "
    "*pods* recém-escalonados e *garbage collection* do Python. Os "
    "testes rodaram com carga estável, sem variação brusca de "
    "*throughput* — o comportamento de escalonamento do HPA e do KEDA "
    "sob picos não foi observado diretamente nos dados coletados.",
)
body_paragraph(
    doc,
    "**Comparação entre ambientes.** A diferença entre DEV (P95 345 ms) "
    "e Staging (P95 124 ms) com *keepalive* evidencia que testes de "
    "desempenho devem ser executados no ambiente de destino, com carga "
    "representativa.",
)

# ---------------------------------------------------------------- 7 -------
heading1(doc, "7", "CONCLUSÃO E TRABALHOS FUTUROS")
heading2(doc, "7.1", "Conclusão")
body_paragraph(
    doc,
    "Este trabalho investigou como integrar de forma eficiente e "
    "automatizada o ciclo de vida de modelos de *Machine Learning* "
    "(MLOps) em pipelines DevOps, em uma plataforma real de detecção de "
    "fraude em produção (AWS, EKS, serviços gerenciados). Os cinco "
    "objetivos da Seção 2.2 foram atendidos: **(i)** camada DevOps "
    "(CodeBuild) separada da camada MLOps (Lambdas "
    "`training-launcher`/`register-best-model`), evitando o acoplamento "
    "entre entrega de código e de modelos (SCULLEY et al., 2015; "
    "KREUZBERGER et al., 2023); **(ii)** infraestrutura em **Terraform "
    "1.14** (15 módulos, 5 *stacks*, *backend* S3 com bloqueio nativo), "
    "com paridade entre DEV e Staging (BRIKMAN, 2019; KARIMIBIUKI et "
    "al., 2022); **(iii)** trilhas de CI/CD, CT e promoção condicional "
    "implementadas com modelo carregado direto via MLflow, sem "
    "*endpoints* SageMaker; **(iv)** MLflow como *SageMaker Managed "
    "Tracking Server*, fonte de verdade da versão em produção (ZAHARIA "
    "et al., 2018); e **(v)** escalonamento validado com HPA (CPU, "
    "Inference) e KEDA (fila SQS, Process) — após otimização de *HTTP "
    "keepalive*, o serviço atingiu P95 de 330 ms (DEV) e 124 ms "
    "(Staging), abaixo da meta de 500 ms, com zero falhas em mais de "
    "11.000 requisições.",
)
body_paragraph(
    doc,
    "**Achado não antecipado.** A ausência de *HTTP keepalive* na cadeia "
    "API Gateway → VPC Link → NLB → *pod* gerava picos de até 5.217 ms "
    "em 3% das requisições; a habilitação do *keepalive* reduziu o P95 "
    "de 1.100 ms para 330 ms (−70%) sem qualquer alteração em "
    "infraestrutura, modelo ou algoritmo — o resultado de maior "
    "relevância prática do trabalho. Conclui-se que a integração "
    "eficiente de MLOps em DevOps requer separação arquitetural entre "
    "CI/CD e CT, automação *serverless*, IaC modularizado, governança "
    "via *Model Registry* e testes de carga com *payloads* reais como "
    "parte do processo de validação — não como etapa opcional.",
)

heading2(doc, "7.2", "Contribuições")
body_paragraph(
    doc,
    "Este trabalho oferece: **evidência empírica sobre HTTP keepalive "
    "em inferência ML** (sua ausência, em cadeias com múltiplos "
    "intermediários de rede, causa degradação severa e intermitente de "
    "latência); um **padrão arquitetural CI/CD + CT desacoplados** "
    "(CodeBuild vs. Lambda + SageMaker como mecanismos independentes); "
    "uma **referência de implementação MLOps cloud-native completa** "
    "(código real de um sistema de detecção de fraude em escala "
    "corporativa); e a **validação de HPA (CPU) e KEDA (fila SQS) como "
    "mecanismos complementares de autoscaling** para perfis de carga "
    "síncrono e assíncrono.",
)

heading2(doc, "7.3", "Limitações")
body_paragraph(
    doc,
    "**Throughput de 100 RPS não validado experimentalmente** (testes "
    "disponíveis com 50 usuários, ~47 RPS); **comportamento do KEDA sob "
    "carga de spike não capturado** (carga estável nos testes); **CT "
    "sem gatilho automático por degradação de métricas** (requer "
    "invocação manual da Lambda `training-launcher`); e **ambiente de "
    "validação único (AWS)**.",
)

heading2(doc, "7.4", "Trabalhos Futuros")
body_paragraph(
    doc,
    "Com base nas limitações identificadas, propõem-se: validar "
    "throughput de 100 RPS e o comportamento do KEDA sob *spike* "
    "(cenários já previstos no locustfile.py); detecção automática de "
    "*concept drift*, acionando a `training-launcher` quando o desvio "
    "de distribuição dos *scores* ultrapassar um limiar (GAMA et al., "
    "2014); *Canary Release* para modelos, com tráfego fracionado; "
    "*benchmark* quantitativo KEDA vs. HPA; extensão do Bedrock para um "
    "agente conversacional completo; e multi-região com failover via "
    "Route 53.",
)

# ------------------------------------------------------------ REFERENCIAS -
page_break(doc)
ref_title_p = centered_title(doc, "REFERÊNCIAS", size=12, bold=True, space_after=12)
set_outline_level(ref_title_p, 0)
REFERENCIAS = [
    "AMAZON WEB SERVICES (AWS). *Amazon Bedrock User Guide*. Disponível em: https://docs.aws.amazon.com/bedrock/. Acesso em: jun. 2026.",
    "AMAZON WEB SERVICES (AWS). *Machine Learning Lens — AWS Well-Architected Framework*. Disponível em: https://docs.aws.amazon.com/wellarchitected/. Acesso em: mar. 2026.",
    "BRECK, Eric; CAIN, Shanqing; NIELSEN, Eric; SALIB, Michael; SCULLEY, David. The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction. In: IEEE INTERNATIONAL CONFERENCE ON BIG DATA (BIG DATA), 5., 2017, Boston. Anais [...]. Piscataway: IEEE, 2017. p. 1123–1132.",
    "BRIKMAN, Yevgeniy. **Terraform: Up & Running: Writing Infrastructure as Code**. 2. ed. Sebastopol: O'Reilly Media, 2019.",
    "FOWLER, Martin. *Continuous Integration*. MartinFowler.com, 2006. Disponível em: https://martinfowler.com/articles/continuousIntegration.html. Acesso em: mar. 2026.",
    "GAMA, João; ŽLIOBAITĖ, Indrė; BIFET, Albert; PECHENIZKIY, Mykola; BOUCHACHIA, Abdelhamid. A Survey on Concept Drift Adaptation. *ACM Computing Surveys*, v. 46, n. 4, artigo 44, p. 1–37, abr. 2014.",
    "GOOGLE CLOUD. *MLOps: Continuous delivery and automation pipelines in machine learning*. Google Cloud Architecture Center, 2023. Disponível em: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning. Acesso em: mar. 2026.",
    "HIGHTOWER, Kelsey; BURNS, Brendan; BEDA, Joe. **Kubernetes: Up and Running: Dive into the Future of Infrastructure**. 3. ed. Sebastopol: O'Reilly Media, 2022.",
    "HUMBLE, Jez; FARLEY, David. **Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation**. Boston: Addison-Wesley Professional, 2010.",
    "KARIMIBIUKI, M.; KAUR, A.; DAVE, V.; ADAMS, B.; BEZEMER, C.-P. Drifted and Not Fixed: An Empirical Study of Configuration Drift in Continuous Deployment. In: IEEE INTERNATIONAL CONFERENCE ON SOFTWARE MAINTENANCE AND EVOLUTION (ICSME), 2022, Limassol. Anais [...]. Piscataway: IEEE, 2022.",
    "KIM, Gene; HUMBLE, Jez; DEBOIS, Patrick; WILLIS, John. **The DevOps Handbook: How to Create World-Class Agility, Reliability, and Security in Technology Organizations**. Portland: IT Revolution Press, 2016.",
    "KREUZBERGER, Dominik; KÜHL, Niklas; HIRSCHL, Sebastian. Machine Learning Operations (MLOps): Overview, Definition, and Architecture. *IEEE Access*, v. 11, p. 31866–31879, 2023.",
    "MÄKINEN, Sami; SKÖN, Jukka-Pekka; MIKKONEN, Tommi; SYSTÄ, Kari. Who Needs MLOps: What Data Scientists Seek to Accomplish and How Can MLOps Help? In: IEEE/ACM INTERNATIONAL WORKSHOP ON COOPERATIVE AND HUMAN ASPECTS OF SOFTWARE ENGINEERING (CHASE), 2021, Madrid. Anais [...]. Piscataway: IEEE, 2021. p. 109–112.",
    "SCULLEY, D.; HOLT, Gary; GOLOVIN, Daniel; DAVYDOV, Eugene; PHILLIPS, Todd; EBNER, Dietmar; CHAUDHARY, Vinay; YOUNG, Michael; CRESPO, Jean-François; DENNISON, Dan. Hidden Technical Debt in Machine Learning Systems. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NeurIPS), 28., 2015, Montreal. Anais [...]. Red Hook: Curran Associates, 2015. p. 2503–2511.",
    "TREVEIL, Mark; OMONT, Nicolas; STENAC, Clément; LEFEVRE, Kenji; PUY, Du; PALM, Joachim; SHARP, Lynn. *Introducing MLOps: How to Scale Machine Learning in the Enterprise*. Sebastopol: O'Reilly Media, 2020.",
    "ZAHARIA, Matei; CHEN, Andrew; DAVIDSON, Aaron; GHODSI, Ali; HONG, Sue Ann; MURTHY, Andy; XING, Andy; CHEN, Richard; ROSENTHAL, Zach; YAVUZ, Burak; SHENKER, Scott. Accelerating the Machine Learning Lifecycle with MLflow. *IEEE Data Engineering Bulletin*, v. 41, n. 4, p. 39–45, dez. 2018.",
]
for ref in REFERENCIAS:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_after = Pt(10)
    add_md_runs(p, ref, base_size=12)

force_update_fields(doc)
doc.save(OUTPUT)
print(f"Documento salvo em: {OUTPUT}")
print(f"Total de paragrafos: {len(doc.paragraphs)}")
print(f"Total de tabelas: {len(doc.tables)}")

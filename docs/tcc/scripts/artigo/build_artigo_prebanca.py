# -*- coding: utf-8 -*-
"""Monta o artigo final do TCC em .docx, aplicando o guia ABNT e as correcoes pendentes."""
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/02_artigo/v3_2026-07-06_prebanca/Artigo_TCC_MLOps_Gustavo_Liebl_Pereira_PreBanca.docx"
DIAGRAM_PNG = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/assets/diagrama-arquitetura-autoral.png"
ANEXO_IMG_DIR = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/assets/anexo_arquitetura_imgs"

DIAGRAMAS_REFERENCIA = [
    ("elo-03.png", "Visão Geral da Infraestrutura"),
    ("elo-04.png", "Fluxo de Inferência (Síncrono)"),
    ("elo-05.png", "Fluxo de Processamento (Assíncrono)"),
    ("elo-06.png", "Fluxo de Treinamento Contínuo (MLOps)"),
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
    fig_run.add_picture(f"{ANEXO_IMG_DIR}/{img_filename}", width=Cm(15))
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

# ============================================================== CAPA =======
for _ in range(4):
    doc.add_paragraph()
centered_title(doc, "CURSO DE ENGENHARIA DE SOFTWARE", size=12, bold=False)
doc.add_paragraph()
for _ in range(3):
    doc.add_paragraph()
centered_title(doc, "GUSTAVO LIEBL PEREIRA", size=12, bold=False)
for _ in range(6):
    doc.add_paragraph()
centered_title(
    doc,
    "INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS "
    "PRÁTICAS PARA ENTREGA CONTÍNUA DE MODELOS DE MACHINE "
    "LEARNING EM PRODUÇÃO",
    size=14, bold=True,
)
doc.add_paragraph()
centered_title(doc, "(Pré-Banca — Proposta de Pesquisa)", size=11, bold=False)
for _ in range(9):
    doc.add_paragraph()
centered_title(doc, "MAFRA", size=12, bold=False)
centered_title(doc, "2026", size=12, bold=False)
page_break(doc)

# ======================================================= FOLHA DE ROSTO ====
for _ in range(3):
    doc.add_paragraph()
centered_title(doc, "GUSTAVO LIEBL PEREIRA", size=12, bold=False)
for _ in range(6):
    doc.add_paragraph()
centered_title(
    doc,
    "INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS "
    "PRÁTICAS PARA ENTREGA CONTÍNUA DE MODELOS DE MACHINE "
    "LEARNING EM PRODUÇÃO",
    size=14, bold=True,
)
doc.add_paragraph()
nota = doc.add_paragraph()
nota.paragraph_format.left_indent = Cm(8)
nota.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
run = nota.add_run(
    "Trabalho de Conclusão de Curso apresentado ao Curso de "
    "Engenharia de Software como requisito parcial para "
    "obtenção do título de Bacharel em Engenharia de Software."
)
run.font.size = Pt(10)
run.font.name = FONT_NAME
doc.add_paragraph()
orient = doc.add_paragraph()
orient.paragraph_format.left_indent = Cm(8)
run = orient.add_run("Orientador: Prof. Marcelo Semmer")
run.font.size = Pt(10)
run.font.name = FONT_NAME
for _ in range(8):
    doc.add_paragraph()
centered_title(doc, "MAFRA", size=12, bold=False)
centered_title(doc, "2026", size=12, bold=False)
page_break(doc)

# ==================================================== FOLHA DE APROVACAO ===
centered_title(doc, "GUSTAVO LIEBL PEREIRA", size=12, bold=False, space_after=24)
centered_title(
    doc,
    "INTEGRAÇÃO DE MLOPS EM PIPELINES DEVOPS: DESAFIOS E BOAS "
    "PRÁTICAS PARA ENTREGA CONTÍNUA DE MODELOS DE MACHINE "
    "LEARNING EM PRODUÇÃO",
    size=13, bold=True, space_after=24,
)
body_paragraph(
    doc,
    "Trabalho de Conclusão de Curso apresentado ao Curso de Engenharia de "
    "Software como requisito parcial para obtenção do título de Bacharel "
    "em Engenharia de Software, aprovado pela Banca Examinadora formada por:",
    indent=False,
)
for _ in range(2):
    doc.add_paragraph()
body_paragraph(doc, "Mafra, ____ de ____________ de 2026.", indent=False)
for _ in range(3):
    doc.add_paragraph()
for label in [
    "Prof. Marcelo Semmer — Orientador",
    "Prof. [Nome do Avaliador 2]",
    "Prof. [Nome do Avaliador 3]",
]:
    body_paragraph(doc, "_" * 45, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT)
    body_paragraph(doc, label, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT)
    doc.add_paragraph()
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
    "fila Amazon SQS como métrica de escalonamento. Este documento "
    "apresenta a proposta de pesquisa até a definição dos materiais, dos "
    "métodos e da arquitetura de referência do estudo de caso; a execução "
    "da validação experimental por meio de testes de carga, seus "
    "resultados e a discussão correspondente serão consolidados na etapa "
    "seguinte deste trabalho."
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
    "Amazon SQS queue depth as the scaling metric. This document presents "
    "the research proposal up to the definition of materials, methods, "
    "and the reference architecture of the case study; the execution of "
    "the experimental validation through load testing, its results, and "
    "the corresponding discussion will be consolidated in the following "
    "stage of this work."
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

# ======================================================= LISTA DE FIGURAS ==
centered_title(doc, "LISTA DE FIGURAS", size=12, bold=True, space_after=12)
body_paragraph(doc, "Figura 1 — Arquitetura de Referência do Estudo de Caso: Visão Geral da Infraestrutura ....", indent=False)
body_paragraph(doc, "Figura 2 — Arquitetura de Referência do Estudo de Caso: Fluxo de Inferência (Síncrono) ....", indent=False)
body_paragraph(doc, "Figura 3 — Arquitetura de Referência do Estudo de Caso: Fluxo de Processamento (Assíncrono) ....", indent=False)
body_paragraph(doc, "Figura 4 — Arquitetura de Referência do Estudo de Caso: Fluxo de Treinamento Contínuo (MLOps) ....", indent=False)
page_break(doc)

# ======================================================= LISTA DE TABELAS ==
centered_title(doc, "LISTA DE TABELAS", size=12, bold=True, space_after=12)
tabelas = [
    "Tabela 1 — Sequência de Stacks e Responsabilidades",
    "Tabela 2 — Configuração do ScaledObject KEDA (DEV)",
    "Tabela 3 — Cenários de Validação Experimental (planejados)",
    "Tabela 4 — Critérios de Aceitação SLA",
]
for t in tabelas:
    body_paragraph(doc, t + " ....................................", indent=False)
page_break(doc)

# =================================================== LISTA DE ABREVIATURAS =
centered_title(doc, "LISTA DE ABREVIATURAS E SIGLAS", size=12, bold=True, space_after=12)
abreviaturas = [
    ("3DS", "Three Domain Secure (protocolo de autenticação de transações)"),
    ("API", "Application Programming Interface"),
    ("ARN", "Amazon Resource Name"),
    ("AWS", "Amazon Web Services"),
    ("CI", "Continuous Integration (Integração Contínua)"),
    ("CD", "Continuous Delivery (Entrega Contínua)"),
    ("CI/CD", "Continuous Integration and Continuous Delivery"),
    ("CT", "Continuous Training (Treinamento Contínuo)"),
    ("ECR", "Elastic Container Registry"),
    ("EKS", "Elastic Kubernetes Service"),
    ("ETL", "Extract, Transform, Load"),
    ("HTTP", "Hypertext Transfer Protocol"),
    ("HPA", "Horizontal Pod Autoscaler"),
    ("IaC", "Infrastructure as Code (Infraestrutura como Código)"),
    ("IAM", "Identity and Access Management"),
    ("JSON", "JavaScript Object Notation"),
    ("KEDA", "Kubernetes Event-Driven Autoscaling"),
    ("LLM", "Large Language Model (Modelo de Linguagem de Grande Escala)"),
    ("ML", "Machine Learning (Aprendizado de Máquina)"),
    ("MLOps", "Machine Learning Operations"),
    ("NLB", "Network Load Balancer"),
    ("PDB", "Pod Disruption Budget"),
    ("REST", "Representational State Transfer"),
    ("RPS", "Requests Per Second (Requisições por Segundo)"),
    ("SLA", "Service Level Agreement (Acordo de Nível de Serviço)"),
    ("SQS", "Simple Queue Service"),
    ("TCC", "Trabalho de Conclusão de Curso"),
    ("TCP", "Transmission Control Protocol"),
    ("VPC", "Virtual Private Cloud"),
    ("YAML", "YAML Ain't Markup Language"),
]
for sigla, definicao in abreviaturas:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    run = p.add_run(f"{sigla}\t{definicao}")
    run.font.name = FONT_NAME
    run.font.size = Pt(12)
page_break(doc)

# ============================================================== SUMARIO ====
centered_title(doc, "SUMÁRIO", size=12, bold=True, space_after=12)
p = doc.add_paragraph()
add_field(p, 'TOC \\o "1-3" \\h \\z \\u')
note = doc.add_paragraph()
run = note.add_run(
    "[Sumário gerado automaticamente — no Word, clique com o botão direito "
    "sobre esta área e selecione \"Atualizar campo\" para exibir os títulos "
    "e números de página.]"
)
run.italic = True
run.font.size = Pt(9)
run.font.name = FONT_NAME
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
heading2(doc, "3.1", "A Dívida Técnica em Sistemas de ML")
body_paragraph(
    doc,
    "Segundo Sculley et al. (2015), o código de aprendizado de máquina "
    "representa apenas uma pequena fração de um sistema produtivo. A "
    "maior parte do esforço reside na configuração, coleta de dados, "
    "verificação e monitoramento. A falta de práticas operacionais "
    "rigorosas resulta em “dívida técnica oculta”, onde a "
    "manutenção torna-se exponencialmente custosa devido à entropia dos "
    "dados. O custo de manter esses sistemas não é linear, pois mudanças "
    "em um componente de dados podem invalidar silenciosamente as "
    "predições do modelo, exigindo uma infraestrutura de observabilidade "
    "robusta. Breck et al. (2017) operacionalizam esse conceito por meio "
    "do *ML Test Score*, um conjunto de testes categorizados em dados, "
    "modelos, infraestrutura e monitoramento, que serve como critério "
    "objetivo de prontidão para produção.",
)
heading2(doc, "3.2", "Pilares do MLOps e Continuous Training (CT)")
body_paragraph(
    doc,
    "MLOps visa padronizar o ciclo de vida de ML (KREUZBERGER et al., "
    "2023). Diferente do DevOps, o MLOps exige o versionamento de três "
    "componentes: código, modelos e dados. O diferencial reside no "
    "*Continuous Training* (CT), permitindo que o sistema retreine "
    "modelos automaticamente conforme a performance degrada. A "
    "necessidade de CT surge do fenômeno de *concept drift*, no qual a "
    "distribuição estatística dos dados de entrada muda ao longo do "
    "tempo, degradando o desempenho do modelo em produção (GAMA et al., "
    "2014). A automação do CT reduz a dependência de intervenções "
    "manuais de cientistas de dados, aproximando a manutenção de modelos "
    "da automação de software tradicional. O rastreamento de "
    "experimentos e o registro centralizado de versões de modelos — "
    "como o MLflow, proposto por Zaharia et al. (2018) — constitui a "
    "infraestrutura de governança que viabiliza esse ciclo, estendendo "
    "ao domínio de dados e modelos os princípios de *Continuous "
    "Delivery* formalizados por Humble e Farley (2010), segundo os quais "
    "todo artefato de software deve ser entregável a qualquer momento.",
)
heading2(doc, "3.3", "Infraestrutura como Código (IaC) na Nuvem")
body_paragraph(
    doc,
    "A utilização de Terraform para o provisionamento de recursos "
    "garante que o ambiente de treinamento seja idêntico ao de produção. "
    "Esta prática elimina o erro humano e permite a escalabilidade "
    "horizontal imediata, essencial para processos de treinamento que "
    "demandam alto poder computacional de forma efêmera (KARIMIBIUKI et "
    "al., 2022). Ao tratar a infraestrutura como software, é possível "
    "versionar o ambiente completo do modelo, garantindo que a "
    "reprodutibilidade seja mantida ao longo de todo o histórico do "
    "projeto. A modularização da infraestrutura em *stacks* independentes "
    "por domínio (*foundation*, *mlops*, *platform*) segue as boas "
    "práticas de organização descritas por Brikman (2019), permitindo "
    "que cada *stack* seja aplicada de forma isolada e versionada.",
)
heading2(doc, "3.4", "Escalabilidade Dinâmica com KEDA")
body_paragraph(
    doc,
    "O Amazon EKS provê um plano de controle Kubernetes gerenciado, "
    "abstraindo a operação do cluster e permitindo que a equipe foque "
    "nas cargas de trabalho (HIGHTOWER; BURNS; BEDA, 2022). O *serving* "
    "de modelos exige baixa latência. O uso de Kubernetes (EKS) em "
    "conjunto com o KEDA (*Kubernetes Event-driven Autoscaling*) permite "
    "escalar o número de réplicas baseado em eventos, como o volume de "
    "mensagens em filas SQS. Esta abordagem otimiza custos operacionais, "
    "pois permite que o consumo de recursos computacionais ocorra apenas "
    "quando há demanda real por inferências, mantendo a performance "
    "durante picos imprevistos de tráfego.",
)

# ---------------------------------------------------------------- 4 -------
heading1(doc, "4", "METODOLOGIA")
body_paragraph(
    doc,
    "Este trabalho classifica-se como **pesquisa aplicada de caráter "
    "experimental e construtivo**: o pesquisador projeta, implementa e "
    "valida experimentalmente uma plataforma de MLOps em um ambiente de "
    "produção real, distinto de um estudo de caso observacional. O "
    "objeto de pesquisa *é* a própria construção — o sistema implementado "
    "constitui tanto o artefato quanto o instrumento de validação. O "
    "ambiente de desenvolvimento foi uma empresa de grande porte do setor "
    "de pagamentos eletrônicos, com dados reais de transações "
    "processados em infraestrutura de nuvem AWS. O trabalho foi "
    "estruturado em quatro fases sequenciais, descritas a seguir.",
)

heading2(doc, "4.1", "Fase 1 — Levantamento Bibliográfico")
body_paragraph(
    doc,
    "A pesquisa bibliográfica foi conduzida nas bases IEEE Xplore, ACM "
    "Digital Library e Google Scholar, com termos de busca centrados em: "
    "*MLOps*, *continuous training*, *model registry*, *infrastructure "
    "as code*, *Kubernetes autoscaling* e *concept drift*. O critério de "
    "inclusão privilegiou trabalhos que apresentassem implementações "
    "práticas ou arquiteturas de referência validadas empiricamente, não "
    "apenas taxonomias teóricas.",
)
body_paragraph(
    doc,
    "O levantamento identificou cinco lacunas recorrentes na literatura "
    "que nortearam as decisões de arquitetura deste projeto: (1) a "
    "maioria das arquiteturas de referência de MLOps apresenta o "
    "pipeline de CI/CD e o ciclo de Treinamento Contínuo (CT) como um "
    "único fluxo, obscurecendo a separação de responsabilidades entre "
    "entrega de código e entrega de modelos (SCULLEY et al., 2015; "
    "KREUZBERGER et al., 2023); (2) poucas implementações documentam o "
    "uso de rastreamento de experimentos gerenciado em nuvem (como "
    "SageMaker Managed MLflow) em contraste com servidores MLflow "
    "auto-hospedados (ZAHARIA et al., 2018); (3) o autoscaling baseado "
    "em eventos (KEDA) para cargas de inferência ML é pouco explorado em "
    "comparação com abordagens baseadas em CPU (HIGHTOWER; BURNS; BEDA, "
    "2022); (4) o impacto de otimizações de rede (como *HTTP keepalive*) "
    "em sistemas de inferência com múltiplas camadas de rede não é "
    "sistematicamente documentado; e (5) a modularização de IaC "
    "(*Infrastructure as Code*) por domínio funcional — não por ambiente "
    "— é pouco formalizada para sistemas MLOps (BRIKMAN, 2019; "
    "KARIMIBIUKI et al., 2022). Essas lacunas orientaram as escolhas "
    "técnicas das fases seguintes e os critérios de avaliação da fase de "
    "validação.",
)

heading2(doc, "4.2", "Fase 2 — Projeto e Desenvolvimento da Infraestrutura")
body_paragraph(
    doc,
    "Toda a infraestrutura foi codificada em **Terraform 1.14**, "
    "organizada em **15 módulos reutilizáveis** instanciados por **5 "
    "*stacks* independentes** por ambiente. Essa organização — "
    "modularização por domínio funcional em lugar de por ambiente — é "
    "um diferencial em relação a projetos que replicam a infraestrutura "
    "completa por ambiente sem abstrações de módulo.",
)
body_paragraph(
    doc,
    "**Módulos implementados:** `vpc`, `s3`, `eks`, `ecr`, `sqs`, "
    "`dynamodb`, `lambda`, `mlflow`, `sagemaker-studio`, `api-gateway`, "
    "`nlb`, `firehose`, `glue`, `athena`, `bedrock-agent`.",
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
    "Os 7 buckets S3 provisionados por ambiente são: `data-raw`, "
    "`data-processed`, `models`, `logs`, `resources`, "
    "`reports-promotion`, `reports-statistics`. Essa separação garante "
    "isolamento de responsabilidades no *data lake*.",
)
body_paragraph(
    doc,
    "O estado Terraform de cada *stack* é armazenado em *backend* "
    "Amazon S3 com bloqueio nativo (parâmetro `use_lockfile`), sem "
    "dependência de uma tabela DynamoDB auxiliar, e as *stacks* de "
    "camadas superiores consomem os *outputs* das inferiores via "
    "`terraform_remote_state`. Esse padrão elimina dependências "
    "circulares e permite a destruição e recriação independente de cada "
    "camada.",
)
body_paragraph(
    doc,
    "Os dois ambientes implementados são **DEV** (região `us-east-1`, "
    "N. Virgínia) e **Staging** (região `sa-east-1`, São Paulo). Cada "
    "ambiente é um conjunto independente das 5 *stacks*, com "
    "*workspaces* e *tfvars* separados, garantindo paridade de "
    "configuração sem compartilhamento de estado.",
)
body_paragraph(
    doc,
    "**Configuração do cluster EKS:** Kubernetes 1.32 em ambos os "
    "ambientes. Em **DEV**, os nós utilizam instâncias `t3.medium` (2 "
    "vCPU, 4 GB RAM), grupo de 2 a 4 nós; em **Staging**, instâncias "
    "`t3.xlarge` (4 vCPU, 16 GB RAM), refletindo maior capacidade para "
    "testes de carga próximos do perfil produtivo. O acesso "
    "administrativo ao cluster ocorre via SSO (`kubectl`).",
)
body_paragraph(
    doc,
    "O *MLflow Tracking Server* foi provisionado como serviço gerenciado "
    "pelo SageMaker (`aws_sagemaker_mlflow_tracking_server`), eliminando "
    "a operação de servidor sem perda de compatibilidade com a API "
    "padrão do MLflow. O servidor armazena artefatos de modelo em um "
    "bucket S3 dedicado e registra *logs* no CloudWatch.",
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
    "O AWS CodeBuild foi utilizado para automação de infraestrutura "
    "operacional. O repositório contém *buildspecs* declarativos "
    "versionados em `buildspecs/`, que encapsulam operações de "
    "manutenção da infraestrutura AWS em pipelines auditáveis e "
    "rastreáveis por *commit*. O *buildspec* `iam-policy-setup.yaml` "
    "automatiza a configuração de políticas IAM nos clusters EKS dos "
    "ambientes DEV e Staging, garantindo que permissões de acesso a "
    "SageMaker, CloudWatch e ECR estejam sempre sincronizadas com o "
    "estado declarativo do repositório.",
)
body_paragraph(
    doc,
    "As imagens Docker dos serviços de inferência, processamento e das "
    "funções Lambda são versionadas e publicadas no Amazon ECR, com um "
    "repositório ECR dedicado por serviço: `inference`, `process`, "
    "`register-best-model`, `training-launcher`, `etl-delta-filter` e "
    "`sagemaker-training`. O serviço de inferência utiliza Python 3.12 "
    "com usuário não-*root* (UID/GID 1000), seguindo boas práticas de "
    "segurança em contêineres Kubernetes.",
)
heading3(doc, "4.3.2", "Trilha CT — Treinamento Contínuo (event-driven)")
body_paragraph(
    doc,
    "O ciclo de Treinamento Contínuo é implementado como uma **cadeia "
    "de eventos serverless**, em que a conclusão bem-sucedida de cada "
    "etapa dispara automaticamente a etapa seguinte, sem agendadores "
    "centralizados ou orquestradores de *workflow*: Glue Job (agendado) "
    "→ EventBridge (Glue SUCCEEDED) → Lambda `etl-delta-filter` (gera "
    "Parquet) → evento S3 (`training_zone/*.parquet`) → Lambda "
    "`training-launcher` (dispara SageMaker Job) → evento S3 (bucket "
    "SageMaker) → Lambda `register-best-model` (promoção condicional no "
    "MLflow).",
)
body_paragraph(
    doc,
    "**Etapa 1 — Glue Job** (`job_training_test_1`): agendado "
    "semanalmente (domingo, 08h00 UTC), lê *logs* de inferência da "
    "`inference_logs/` no bucket `data-processed` e gera a zona "
    "transformada (`transformed_zone/`) no formato Delta Lake, aplicando "
    "*merge* incremental com *job bookmarks* para processar apenas novos "
    "registros.",
)
body_paragraph(
    doc,
    "**Etapa 2 — Lambda `etl-delta-filter`**: acionada via EventBridge "
    "quando o Glue Job termina com estado `SUCCEEDED`. Aplica filtros "
    "Delta no conjunto transformado e grava arquivos Parquet na "
    "`training_zone/`, preparando o *dataset* de treinamento "
    "incremental.",
)
body_paragraph(
    doc,
    "**Etapa 3 — Lambda `training-launcher`**: acionada por notificação "
    "S3 quando novos arquivos `.parquet` chegam em `training_zone/`. "
    "Utiliza o SageMaker ModelTrainer SDK para despachar um *training "
    "job* com a imagem de treinamento publicada no ECR.",
)
body_paragraph(
    doc,
    "**Etapa 4 — SageMaker Training Job**: executa o treinamento do "
    "modelo XGBoost a partir dos dados Parquet. Parâmetros e métricas "
    "(incluindo `training_f1_score`) são registrados automaticamente no "
    "MLflow Tracking Server. Ao término, artefatos do modelo são salvos "
    "no bucket SageMaker.",
)
body_paragraph(
    doc,
    "**Etapa 5 — Lambda `register-best-model`**: acionada por "
    "notificação S3 no bucket SageMaker. Consulta o MLflow, identifica o "
    "experimento correspondente ao *job* recém-concluído e compara sua "
    "métrica `training_f1_score` com a do modelo atual em produção. Se "
    "o novo modelo for superior, promove-o no *MLflow Registry* com a "
    "*tag* `stage: production`. Caso contrário, o modelo anterior "
    "permanece em produção sem intervenção manual. Esse mecanismo "
    "garante que **apenas modelos melhores que o antecessor chegam a "
    "produção**, eliminando o risco de regressão acidental por "
    "retreinamento.",
)
heading3(doc, "4.3.3", "Trilha de Inferência — FastAPI + EKS + KEDA")
body_paragraph(
    doc,
    "O serviço de inferência é uma API REST implementada com **FastAPI** "
    "(Python 3.12), containerizada e implantada no Amazon EKS. O fluxo "
    "de rede de uma requisição percorre: API Gateway → VPC Link → NLB "
    "(*Network Load Balancer*) → *pod* EKS, integrado via "
    "`TargetGroupBinding` com alvo do tipo IP — sem uso de *Application "
    "Load Balancer* (ALB) nesse caminho.",
)
body_paragraph(
    doc,
    "O modelo é carregado diretamente do **MLflow Registry** na "
    "inicialização do *pod*, sem necessidade de *endpoint* SageMaker "
    "dedicado. A versão carregada é sempre aquela com *tag* `stage: "
    "production` no *registry*, garantindo que o *deploy* de um novo "
    "modelo ocorra automaticamente na próxima substituição de *pod*, "
    "sem redeploy manual.",
)
body_paragraph(
    doc,
    "O **KEDA 2.18.3** (*Kubernetes Event-driven Autoscaling*) foi "
    "instalado via Helm no *namespace* `keda` e configurado com um "
    "`ScaledObject` que monitora a profundidade da fila **SQS FIFO** "
    "(`elo-fraud-resultset-dev.fifo`) para escalar o serviço de "
    "processamento assíncrono (`process`):",
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
    "A validação foi realizada com a ferramenta **Locust** (Python), que "
    "permite simular usuários virtuais concorrentes com controle "
    "preciso de taxa de requisições. A configuração adotada foi **1 "
    "usuário = 1 RPS** (*constant_throughput*), de forma que o número de "
    "usuários simultâneos corresponde diretamente ao *throughput* em "
    "RPS.",
)
body_paragraph(
    doc,
    "**Corpus de teste:** 100 *payloads* reais de transações 3DS "
    "capturados do ambiente de produção, percorridos em sequência "
    "*round-robin* com seleção *thread-safe* entre usuários "
    "concorrentes. O uso de *payloads* reais — em lugar de dados "
    "sintéticos — garante que variações de tamanho, estrutura e "
    "conteúdo das transações estejam presentes nos testes, tornando os "
    "resultados representativos do tráfego real.",
)
body_paragraph(
    doc,
    "**Critério de sucesso por requisição:** resposta HTTP 200 com "
    "campo `score` no *body* JSON. Qualquer desvio — HTTP 4xx, HTTP "
    "5xx, *timeout* ou JSON inválido — é contabilizado como falha.",
)
add_table_caption(doc, "Tabela 3", "Cenários de Validação Experimental")
add_simple_table(
    doc,
    ["Cenário", "Tipo", "Ambiente", "Condição"],
    [
        ["1", "Sequencial (100 req.)", "DEV (us-east-1)", "Antes da otimização de keepalive"],
        ["2", "Sequencial (100 req.)", "DEV (us-east-1)", "Após otimização de keepalive"],
        ["3", "Sequencial (100 req.)", "Staging (sa-east-1)", "Após otimização de keepalive"],
        ["4", "Locust concorrente (50 usuários)", "DEV (us-east-1)", "Antes da otimização"],
        ["5", "Locust concorrente (50 usuários)", "DEV (us-east-1)", "Após otimização"],
    ],
)
add_source_note(doc, "Fonte: elaboração do autor.")
body_paragraph(
    doc,
    "Os cenários sequenciais (1–3) permitiram isolar o comportamento "
    "requisição a requisição, revelando anomalias de latência que "
    "seriam mascaradas por estatísticas agregadas dos testes de carga. "
    "Os cenários Locust (4–5) mediram o desempenho sob carga concorrente "
    "real, com coleta de percentis P50, P75, P90, P95, P99, *throughput* "
    "médio e taxa de falhas.",
)
add_table_caption(doc, "Tabela 4", "Critérios de Aceitação SLA")
add_simple_table(
    doc,
    ["Critério", "Meta"],
    [
        ["Disponibilidade", "100% (0 falhas HTTP)"],
        ["Latência P95", "< 500 ms"],
        ["Latência P99", "< 1.000 ms"],
        ["Throughput", "≥ 100 RPS"],
    ],
)
add_source_note(doc, "Fonte: elaboração do autor.")
body_paragraph(
    doc,
    "A execução desses cenários, a análise dos dados coletados e a "
    "discussão dos resultados serão consolidadas na etapa seguinte deste "
    "trabalho, após a conclusão da fase de validação experimental.",
)

# ---------------------------------------------------------------- 5 -------
heading1(doc, "5", "MODELAGEM DA SOLUÇÃO")
body_paragraph(doc, "A solução proposta integra ferramentas de automação para criar um fluxo de dados ininterrupto.")
heading2(doc, "5.1", "Descrição da Abordagem")
body_paragraph(
    doc,
    "O fluxo opera em duas trilhas paralelas e complementares. Na "
    "**trilha de serving**, um commit no repositório aciona o AWS "
    "CodeBuild, que constrói a imagem Docker do serviço de inferência "
    "(FastAPI), publica no Amazon ECR e atualiza o *deployment* no "
    "Amazon EKS via `kubectl`. Na **trilha de MLOps**, a função Lambda "
    "`training-launcher` dispara um SageMaker Training Job que treina o "
    "modelo XGBoost com dados Parquet do S3, registrando parâmetros e "
    "métricas no MLflow. Ao término do treinamento, a função Lambda "
    "`register-best-model` compara automaticamente as métricas do "
    "experimento com o modelo em produção e, se houver melhoria, "
    "promove o novo modelo no MLflow Registry. O serviço de inferência "
    "carrega o modelo diretamente via MLflow, sem necessidade de "
    "SageMaker Endpoint. O escalonador KEDA monitora a profundidade da "
    "fila SQS FIFO e ajusta o número de réplicas dos *pods* de "
    "inferência conforme a demanda real.",
)
heading2(doc, "5.2", "Diagrama de Arquitetura Técnica")
body_paragraph(
    doc,
    "Para a visualização da arquitetura, os diagramas técnicos ilustram a "
    "interação entre a camada de entrada e rede, o cluster Amazon EKS, "
    "as trilhas de CI/CD e de Treinamento Contínuo, o armazenamento e a "
    "camada de observabilidade generativa (ver Figuras 1 a 4).",
)

body_paragraph(
    doc,
    "**Fluxo 1 — Inferência em Tempo Real (síncrono).** O emissor envia "
    "a transação 3DS via HTTPS para o Amazon API Gateway, que roteia via "
    "VPC Link e NLB até o Inference Service (FastAPI, 8 *pods*), "
    "conectado por meio de um `TargetGroupBinding` com alvo do tipo IP — "
    "sem passar por um Application Load Balancer. O serviço consulta o "
    "DynamoDB (feature store com transações recentes do cliente), "
    "executa o modelo XGBoost (carregado do MLflow na inicialização do "
    "*pod*) e retorna o *score* de fraude de forma síncrona.",
)
body_paragraph(
    doc,
    "**Fluxo 2 — Processamento Assíncrono e Logging.** Após retornar o "
    "*score*, o Inference Service enfileira o resultado na SQS FIFO. O "
    "Process Service (*worker*, 2–5 *pods* escalados pelo KEDA) consome "
    "a fila, atualiza o histórico de transações do cliente no DynamoDB e "
    "persiste o log de inferência no Kinesis Firehose, que os entrega ao "
    "S3 (`inference_logs/`).",
)
body_paragraph(
    doc,
    "**Fluxo 3 — Treinamento Contínuo (CT, event-driven).** "
    "Semanalmente, o AWS Glue agrega os logs de inferência e gera a "
    "zona transformada (Delta Lake). O EventBridge detecta a conclusão e "
    "aciona a Lambda `etl-delta-filter`, que gera Parquets em "
    "`training_zone/`. Um evento S3 aciona a Lambda `training-launcher`, "
    "que despacha um SageMaker Training Job (XGBoost). Ao concluir, "
    "métricas e artefatos são registrados no MLflow. Um segundo evento "
    "S3 aciona a Lambda `register-best-model`, que compara o F1-score e "
    "promove o modelo superior no MLflow Registry.",
)
body_paragraph(
    doc,
    "**Fluxo 4 — Observabilidade Generativa (diária).** Um EventBridge "
    "cron diário aciona duas Lambdas: `promotion-reporter` (consulta "
    "promoções no MLflow) e `statistics-reporter` (consulta métricas de "
    "inferência no Athena). Ambas enviam os dados ao Amazon Bedrock via "
    "`invoke_model`, que gera relatórios em linguagem natural salvos no "
    "S3.",
)
body_paragraph(
    doc,
    "**Fluxo 5 — IaC e CI/CD.** O AWS CodeBuild constrói e publica as "
    "imagens Docker dos 6 serviços no Amazon ECR. O Terraform (5 "
    "*stacks*, 15 módulos, com *backend* S3 de bloqueio nativo) "
    "provisiona e mantém toda a infraestrutura, consumindo as imagens "
    "do ECR.",
)

body_paragraph(
    doc,
    "As Figuras 1 a 4 apresentam a documentação técnica original do "
    "estudo de caso, elaborada pela própria equipe do projeto, utilizada "
    "aqui como referência complementar e independente à descrição "
    "textual da arquitetura apresentada nesta seção. Esta arquitetura de "
    "referência é a base sobre a qual a validação experimental descrita "
    "na Seção 4.4 será executada na etapa seguinte deste trabalho.",
)
for i, (img, subtitulo) in enumerate(DIAGRAMAS_REFERENCIA, start=1):
    add_diagrama_referencia(doc, i, img, subtitulo)

body_paragraph(
    doc,
    "Este documento encerra a proposta de pesquisa na definição dos "
    "materiais, dos métodos e da arquitetura de referência. A execução "
    "da validação experimental, seus resultados, a discussão "
    "correspondente e a conclusão do trabalho serão apresentados na "
    "etapa seguinte (defesa completa da TCC I / TCC II).",
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

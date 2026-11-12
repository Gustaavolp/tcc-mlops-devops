"""
Gerador de slides PowerPoint — TCC I, Apresentação de Andamento
TCC MLOps / Gustavo Liebl Pereira
Duração alvo: 15 minutos — foco em proposta, metodologia e progresso;
resultados experimentais apresentados como preview (aprofundamento fica para a TCC II).
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# ─── Paleta de cores ────────────────────────────────────────────────────────
AZUL_ESCURO   = RGBColor(0x0F, 0x34, 0x60)
AZUL_MEDIO    = RGBColor(0x16, 0x21, 0x3E)
VERMELHO      = RGBColor(0xE9, 0x45, 0x60)
BRANCO        = RGBColor(0xFF, 0xFF, 0xFF)
CINZA_CLARO   = RGBColor(0xF5, 0xF7, 0xFF)
CINZA_TEXTO   = RGBColor(0x44, 0x44, 0x44)
VERDE         = RGBColor(0x1A, 0x8A, 0x42)
AMARELO_BG    = RGBColor(0xFF, 0xF8, 0xE1)
AZUL_THEAD    = RGBColor(0x0F, 0x34, 0x60)
LARANJA       = RGBColor(0xCC, 0x66, 0x00)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)
TOTAL_SLIDES = 17

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
blank_layout = prs.slide_layouts[6]

# ─── Helpers ────────────────────────────────────────────────────────────────

def add_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_width=None):
    shape = slide.shapes.add_shape(1, left, top, width, height)  # RECTANGLE
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        if line_width:
            shape.line.width = line_width
    return shape

def add_textbox(slide, text, left, top, width, height,
                font_size=18, bold=False, color=CINZA_TEXTO,
                align=PP_ALIGN.LEFT, italic=False, font_name="Calibri"):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = True
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        run.font.name = font_name
    return txb

def set_slide_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def header_bar(slide, title_text, subtitle_text=None, bar_color=AZUL_ESCURO):
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.15), fill_color=bar_color)
    add_textbox(slide, title_text,
                Inches(0.35), Inches(0.12), Inches(12.2), Inches(0.65),
                font_size=26, bold=True, color=BRANCO, font_name="Calibri")
    if subtitle_text:
        add_textbox(slide, subtitle_text,
                    Inches(0.35), Inches(0.72), Inches(12.2), Inches(0.38),
                    font_size=15, color=RGBColor(0xCC, 0xDD, 0xFF), font_name="Calibri")

def footer_bar(slide, page_num, total=TOTAL_SLIDES):
    add_rect(slide, 0, Inches(7.15), SLIDE_W, Inches(0.35), fill_color=AZUL_ESCURO)
    add_textbox(slide,
                "Gustavo Liebl Pereira  |  TCC I — Apresentação de Andamento  |  Orientador: Prof. Marcelo Semmer",
                Inches(0.3), Inches(7.17), Inches(11.5), Inches(0.3),
                font_size=10, color=RGBColor(0xAA, 0xBB, 0xDD), font_name="Calibri")
    add_textbox(slide, f"{page_num}/{total}",
                Inches(12.6), Inches(7.17), Inches(0.6), Inches(0.3),
                font_size=10, color=BRANCO, align=PP_ALIGN.RIGHT, font_name="Calibri")

def bullet_lines(slide, items, left, top, width, height,
                 font_size=16, color=CINZA_TEXTO, indent="  •  ", line_spacing_pt=4):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(line_spacing_pt)
        if isinstance(item, tuple):
            r1 = p.add_run(); r1.text = indent + item[0]
            r1.font.bold = True; r1.font.size = Pt(font_size)
            r1.font.color.rgb = AZUL_ESCURO; r1.font.name = "Calibri"
            r2 = p.add_run(); r2.text = item[1]
            r2.font.size = Pt(font_size); r2.font.color.rgb = color; r2.font.name = "Calibri"
        else:
            run = p.add_run()
            run.text = indent + item
            run.font.size = Pt(font_size); run.font.color.rgb = color; run.font.name = "Calibri"
    return txb

def add_table(slide, headers, rows, left, top, width, height,
              header_bg=AZUL_THEAD, header_fg=BRANCO,
              row_even=CINZA_CLARO, row_odd=BRANCO,
              font_size=13, header_size=13, col_widths=None):
    n_cols = len(headers)
    n_rows = len(rows)
    tbl = slide.shapes.add_table(n_rows + 1, n_cols, left, top, width, height).table
    if col_widths:
        for ci, cw in enumerate(col_widths):
            tbl.columns[ci].width = cw
    for ci, h in enumerate(headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid(); cell.fill.fore_color.rgb = header_bg
        p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        run = p.add_run(); run.text = h
        run.font.bold = True; run.font.size = Pt(header_size)
        run.font.color.rgb = header_fg; run.font.name = "Calibri"
    for ri, row in enumerate(rows):
        bg = row_even if ri % 2 == 0 else row_odd
        for ci, cell_text in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            cell.fill.solid(); cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if ci > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            txt = str(cell_text)
            bold_cell = txt.startswith("**") and txt.endswith("**")
            if bold_cell:
                txt = txt[2:-2]
            run.text = txt
            run.font.size = Pt(font_size)
            run.font.bold = bold_cell
            if "✓" in txt:
                run.font.color.rgb = VERDE; run.font.bold = True
            elif "⚠" in txt:
                run.font.color.rgb = LARANJA; run.font.bold = True
            else:
                run.font.color.rgb = CINZA_TEXTO
            run.font.name = "Calibri"
    return tbl

def highlight_box(slide, text, left, top, width, height, bg=AMARELO_BG, border=VERMELHO, font_size=15):
    add_rect(slide, left, top, width, height, fill_color=bg, line_color=border, line_width=Pt(1.5))
    add_textbox(slide, text, left + Inches(0.15), top + Inches(0.1),
                width - Inches(0.3), height - Inches(0.2),
                font_size=font_size, color=RGBColor(0x22, 0x22, 0x22), font_name="Calibri")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — CAPA
# ════════════════════════════════════════════════════════════════════════════
def slide_capa():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, AZUL_MEDIO)
    add_rect(s, 0, 0, Inches(0.5), SLIDE_H, fill_color=VERMELHO)
    add_rect(s, 0, Inches(6.3), SLIDE_W, Inches(1.2), fill_color=RGBColor(0x0A, 0x1A, 0x35))

    add_rect(s, Inches(0.75), Inches(0.55), Inches(4.4), Inches(0.4), fill_color=VERMELHO)
    add_textbox(s, "APRESENTAÇÃO DE ANDAMENTO  —  TCC I",
                Inches(0.75), Inches(0.58), Inches(4.3), Inches(0.34),
                font_size=13, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)

    add_textbox(s, "Integração de MLOps em Pipelines DevOps",
                Inches(0.75), Inches(1.15), Inches(11.8), Inches(1.3),
                font_size=32, bold=True, color=BRANCO)

    add_textbox(s,
                "Desafios e Boas Práticas para Entrega Contínua de\nModelos de Machine Learning em Produção",
                Inches(0.75), Inches(2.55), Inches(11.0), Inches(1.1),
                font_size=20, color=RGBColor(0xAA, 0xCC, 0xFF))

    add_rect(s, Inches(0.75), Inches(3.75), Inches(6.0), Inches(0.04), fill_color=VERMELHO)

    meta = [
        ("Autor:", "Gustavo Liebl Pereira"),
        ("Orientador:", "Prof. Marcelo Semmer"),
        ("Curso:", "Engenharia de Software"),
        ("Semestre:", "2026/1  —  Mafra, SC"),
    ]
    y = Inches(3.95)
    for label, value in meta:
        txb = s.shapes.add_textbox(Inches(0.75), y, Inches(8.0), Inches(0.38))
        tf = txb.text_frame
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = label + "  "
        r1.font.bold = True; r1.font.size = Pt(15)
        r1.font.color.rgb = VERMELHO; r1.font.name = "Calibri"
        r2 = p.add_run(); r2.text = value
        r2.font.size = Pt(15); r2.font.color.rgb = BRANCO; r2.font.name = "Calibri"
        y += Inches(0.42)

    add_textbox(s, "Trabalho de Conclusão de Curso  —  Entrega parcial (TCC I)",
                Inches(0.75), Inches(6.38), Inches(9.0), Inches(0.35),
                font_size=12, color=RGBColor(0x88, 0xAA, 0xCC))

slide_capa()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — AGENDA
# ════════════════════════════════════════════════════════════════════════════
def slide_agenda():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Agenda")
    footer_bar(s, 2)

    items_col1 = [
        "01  Problema de Pesquisa",
        "02  Contexto e Necessidade do Cliente",
        "03  Pergunta e Objetivos",
        "04  Metodologia — Visão Geral",
        "05  Fase 1 — Levantamento Bibliográfico",
        "06  Fase 2 — Infraestrutura como Código",
        "07  Arquitetura da Plataforma",
    ]
    items_col2 = [
        "08  Fase 3 — Pipelines CI/CD + CT",
        "09  Fase 3 — Autoscaling: HPA + KEDA",
        "10  Fase 4 — Validação Experimental",
        "11  Preview de Resultados",
        "12  Estado Atual do Trabalho",
        "13  Trabalhos Futuros — Rumo à TCC II",
        "14  Conclusão Parcial",
    ]

    for i, item in enumerate(items_col1):
        y = Inches(1.35) + i * Inches(0.75)
        add_rect(s, Inches(0.35), y, Inches(0.06), Inches(0.5), fill_color=VERMELHO)
        add_textbox(s, item, Inches(0.55), y + Inches(0.06),
                    Inches(5.9), Inches(0.5), font_size=16, color=AZUL_ESCURO)

    for i, item in enumerate(items_col2):
        y = Inches(1.35) + i * Inches(0.75)
        add_rect(s, Inches(6.9), y, Inches(0.06), Inches(0.5), fill_color=VERMELHO)
        add_textbox(s, item, Inches(7.1), y + Inches(0.06),
                    Inches(5.9), Inches(0.5), font_size=16, color=AZUL_ESCURO)

    highlight_box(s,
                  "Foco desta apresentação: proposta, metodologia e progresso da implementação. "
                  "Os resultados experimentais são mostrados como preview — a análise completa integrará a TCC II.",
                  Inches(0.35), Inches(6.35), Inches(12.6), Inches(0.7), font_size=13)

slide_agenda()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — PROBLEMA DE PESQUISA
# ════════════════════════════════════════════════════════════════════════════
def slide_problema():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Problema de Pesquisa",
               "A lacuna entre experimentação e produção em sistemas de Machine Learning")
    footer_bar(s, 3)

    add_rect(s, Inches(0.3), Inches(1.35), Inches(5.8), Inches(2.5),
             fill_color=RGBColor(0xE8, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_textbox(s, "Cientista de Dados", Inches(0.4), Inches(1.42),
                Inches(5.6), Inches(0.4), font_size=17, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "✓  Modelo treinado com boa acurácia",
        "✓  Experimentos documentados",
        "✗  Sem API de servimento",
        "✗  Sem versionamento de modelo",
        "✗  Sem pipeline de retreinamento",
    ], Inches(0.4), Inches(1.85), Inches(5.6), Inches(1.9), font_size=15, indent="")

    add_textbox(s, "→", Inches(6.2), Inches(2.3), Inches(0.9), Inches(0.6),
                font_size=36, bold=True, color=VERMELHO, align=PP_ALIGN.CENTER)
    add_textbox(s, '"Funcionou\nno Jupyter..."',
                Inches(6.0), Inches(2.85), Inches(1.3), Inches(0.65),
                font_size=11, italic=True, align=PP_ALIGN.CENTER)

    add_rect(s, Inches(7.35), Inches(1.35), Inches(5.6), Inches(2.5),
             fill_color=RGBColor(0xFF, 0xEE, 0xEE), line_color=VERMELHO, line_width=Pt(1))
    add_textbox(s, "Time de Engenharia / Ops", Inches(7.45), Inches(1.42),
                Inches(5.4), Inches(0.4), font_size=17, bold=True, color=VERMELHO)
    bullet_lines(s, [
        "✗  Deploy manual e frágil",
        "✗  Sem rastreabilidade de versões",
        "✗  Sem pipeline de CT automático",
        "✗  Model drift não detectado",
        "✗  Governança inexistente",
    ], Inches(7.45), Inches(1.85), Inches(5.4), Inches(1.9), font_size=15, indent="")

    highlight_box(s,
                  "85% dos projetos de ML nunca chegam à produção  (Gartner, 2022)\n"
                  "Sculley et al. (2015): 'Apenas uma pequena fração do código de um sistema de ML é "
                  "dedicada ao modelo — o resto é infraestrutura oculta.'",
                  Inches(0.3), Inches(4.05), Inches(12.7), Inches(1.05), font_size=14)

    add_textbox(s,
                "Contexto real deste trabalho:  plataforma de detecção de fraude em transações eletrônicas  "
                "—  empresa de grande porte  —  infraestrutura AWS em produção",
                Inches(0.3), Inches(5.25), Inches(12.7), Inches(0.5), font_size=14, color=AZUL_ESCURO)

    add_textbox(s,
                "Justificativa:  a integração de MLOps a pipelines DevOps deixou de ser uma escolha isolada de ferramenta "
                "e passou a ser condição de sobrevivência de sistemas de IA em produção — governança, reprodutibilidade e "
                "automação do ciclo de vida do modelo tornam-se tão críticas quanto o próprio algoritmo.",
                Inches(0.3), Inches(5.85), Inches(12.7), Inches(1.1), font_size=13, italic=True)

slide_problema()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — CONTEXTO E NECESSIDADE DO CLIENTE
# ════════════════════════════════════════════════════════════════════════════
def slide_contexto_cliente():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Contexto Real do Projeto — Necessidade do Cliente",
               "Empresa de grande porte do setor de pagamentos eletrônicos  ·  evolução de MVP para produção")
    footer_bar(s, 4)

    add_rect(s, Inches(0.3), Inches(1.3), Inches(6.1), Inches(3.05),
             fill_color=RGBColor(0xE8, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_textbox(s, "Origem da Demanda", Inches(0.4), Inches(1.36),
                Inches(5.9), Inches(0.4), font_size=16, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "MVP já validado tecnicamente:  93% de recall de fraude",
        "Cliente solicitou formalmente (kick-off) a evolução para um "
        "\"motor preditivo operacional\" com governança, explicabilidade e monitoramento contínuos",
        "Prazo formal do projeto:  29/09  a  05/12",
        "Fonte:  Kick-Off e Detalhamento de Escopo — Fase 2 "
        "(documentos internos do cliente e do prestador de serviços)",
    ], Inches(0.4), Inches(1.85), Inches(5.85), Inches(2.4), font_size=13, indent="  •  ")

    add_rect(s, Inches(6.6), Inches(1.3), Inches(6.45), Inches(3.05),
             fill_color=RGBColor(0xFF, 0xF8, 0xE1), line_color=VERMELHO, line_width=Pt(1))
    add_textbox(s, "Requisitos Formais (SLA Contratado)", Inches(6.7), Inches(1.36),
                Inches(6.25), Inches(0.4), font_size=16, bold=True, color=VERMELHO)
    headers_sla = ["Requisito", "Meta contratada"]
    rows_sla = [
        ["Latência P95", "< 500 ms"],
        ["Disponibilidade", "99,9%"],
        ["**Throughput**", "**10.000 req/s**"],
        ["Conformidade", "LGPD"],
    ]
    add_table(s, headers_sla, rows_sla, Inches(6.7), Inches(1.85), Inches(6.25), Inches(2.3),
              font_size=14, col_widths=[Inches(3.0), Inches(3.25)])

    highlight_box(s,
                  "Delimitação de escopo deste TCC:  atuação como Engenheiro DevOps — Terraform, EKS, CI/CD e "
                  "Monitoramento. O treinamento do modelo de ML (features e algoritmo) foi conduzido por outra "
                  "frente da equipe (Data Science) e não é objeto de autoria deste trabalho.",
                  Inches(0.3), Inches(4.55), Inches(12.7), Inches(0.95), font_size=14)

    add_textbox(s,
                "Nota de confidencialidade:  documentos internos classificados como restritos — uso de trechos no "
                "artigo final está sujeito a autorização formal da empresa.",
                Inches(0.3), Inches(5.65), Inches(12.7), Inches(0.5), font_size=12, italic=True, color=CINZA_TEXTO)

    add_textbox(s,
                "Por que isso importa para a pesquisa:  a pergunta de pesquisa não nasceu de uma hipótese acadêmica "
                "isolada — nasceu de uma demanda de negócio real, com prazo, SLA e critérios de aceite formalmente definidos.",
                Inches(0.3), Inches(6.25), Inches(12.7), Inches(0.7), font_size=13, color=AZUL_ESCURO)

slide_contexto_cliente()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — PERGUNTA E OBJETIVOS
# ════════════════════════════════════════════════════════════════════════════
def slide_objetivos():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Pergunta de Pesquisa e Objetivos")
    footer_bar(s, 5)

    highlight_box(s,
                  "Como integrar de forma eficiente, escalável e automatizada o ciclo de vida de modelos de "
                  "Machine Learning (MLOps) em pipelines de DevOps, garantindo a entrega contínua e a "
                  "governança operacional em ambientes de produção complexos?",
                  Inches(0.3), Inches(1.3), Inches(12.7), Inches(1.1), font_size=15)

    add_textbox(s, "Objetivos Específicos", Inches(0.3), Inches(2.6),
                Inches(4.0), Inches(0.45), font_size=18, bold=True, color=AZUL_ESCURO)

    objs = [
        ("i", "Projetar as camadas de integração DevOps / MLOps com separação explícita de responsabilidades"),
        ("ii", "Implementar infraestrutura como código (IaC) via Terraform com modularização por domínio"),
        ("iii", "Desenvolver pipelines de CI/CD e Treinamento Contínuo (CT) automatizados"),
        ("iv", "Implementar governança e rastreabilidade de modelos via MLflow Registry"),
        ("v", "Validar escalonamento orientado a eventos com KEDA + Amazon SQS"),
    ]
    for i, (num, text) in enumerate(objs):
        y = Inches(3.0) + i * Inches(0.60)
        add_rect(s, Inches(0.3), y + Inches(0.03), Inches(0.44), Inches(0.44), fill_color=AZUL_ESCURO)
        add_textbox(s, num, Inches(0.3), y + Inches(0.03), Inches(0.44), Inches(0.44),
                    font_size=15, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        add_textbox(s, text, Inches(0.9), y + Inches(0.05),
                    Inches(12.1), Inches(0.5), font_size=14.5)

    highlight_box(s,
                  "Objetivo Geral:  demonstrar, por meio de um projeto prático em nuvem, a implementação de uma "
                  "arquitetura de MLOps integrada a pipelines DevOps — identificando desafios técnicos e boas "
                  "práticas para entrega contínua de modelos de Machine Learning.",
                  Inches(0.3), Inches(6.2), Inches(12.7), Inches(0.6), font_size=13)

slide_objetivos()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — METODOLOGIA VISÃO GERAL
# ════════════════════════════════════════════════════════════════════════════
def slide_metodologia():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Metodologia — Visão Geral",
               "Pesquisa aplicada de caráter experimental e construtivo")
    footer_bar(s, 6)

    fases = [
        ("Fase 1", "Levantamento\nBibliográfico",
         "IEEE Xplore\nACM Digital Library\nGoogle Scholar\n5 lacunas identificadas"),
        ("Fase 2", "IaC com Terraform",
         "15 módulos\n5 stacks independentes\nDEV (us-east-1)\nStaging (sa-east-1)"),
        ("Fase 3", "Pipelines CI/CD + CT",
         "AWS CodeBuild\nLambda + SageMaker\nFastAPI / EKS\nKEDA + SQS"),
        ("Fase 4", "Validação Experimental",
         "Locust (Python)\n100 payloads 3DS\n2 ambientes AWS\n5 cenários de teste"),
    ]
    for i, (fase, titulo, detalhes) in enumerate(fases):
        x = Inches(0.25) + i * Inches(3.27)
        add_rect(s, x, Inches(1.35), Inches(3.0), Inches(4.6),
                 fill_color=RGBColor(0xF0, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
        add_rect(s, x, Inches(1.35), Inches(3.0), Inches(0.55), fill_color=AZUL_ESCURO)
        add_textbox(s, fase, x + Inches(0.05), Inches(1.38),
                    Inches(2.9), Inches(0.45), font_size=14, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        add_textbox(s, titulo, x + Inches(0.1), Inches(2.0),
                    Inches(2.8), Inches(0.85), font_size=16, bold=True, color=AZUL_ESCURO, align=PP_ALIGN.CENTER)
        add_textbox(s, detalhes, x + Inches(0.12), Inches(2.95),
                    Inches(2.76), Inches(2.2), font_size=14, align=PP_ALIGN.CENTER)
        if i < 3:
            add_textbox(s, "→", x + Inches(2.97), Inches(2.4),
                        Inches(0.35), Inches(0.55), font_size=22, bold=True, color=VERMELHO, align=PP_ALIGN.CENTER)

    highlight_box(s,
                  "Pesquisa aplicada, experimental e construtiva:  o sistema implementado é, ao mesmo tempo, o "
                  "artefato e o instrumento de validação.",
                  Inches(0.25), Inches(6.1), Inches(12.8), Inches(0.95), font_size=15)

slide_metodologia()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — FASE 1: LEVANTAMENTO BIBLIOGRÁFICO
# ════════════════════════════════════════════════════════════════════════════
def slide_fase1():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Fase 1 — Levantamento Bibliográfico",
               "IEEE Xplore  ·  ACM Digital Library  ·  Google Scholar")
    footer_bar(s, 7)

    add_textbox(s,
                "Critério de inclusão: trabalhos com implementações práticas ou arquiteturas de referência validadas "
                "empiricamente — não apenas taxonomias teóricas.",
                Inches(0.3), Inches(1.3), Inches(12.7), Inches(0.5), font_size=14, italic=True, color=AZUL_ESCURO)

    add_textbox(s, "5 lacunas identificadas na literatura, que nortearam as decisões de arquitetura deste projeto:",
                Inches(0.3), Inches(1.9), Inches(12.7), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)

    lacunas = [
        ("CI/CD e Treinamento Contínuo tratados como um único fluxo", "Sculley et al., 2015; Kreuzberger et al., 2023"),
        ("Rastreamento de experimentos: nuvem gerenciada vs. MLflow self-hosted", "Zaharia et al., 2018"),
        ("Autoscaling orientado a eventos (KEDA) para cargas de ML", "Hightower; Burns; Beda, 2022"),
        ("Impacto de otimizações de rede (HTTP keepalive) na inferência", None),
        ("Modularização de IaC por domínio funcional para MLOps", "Brikman, 2019; Karimibiuki et al., 2022"),
    ]
    y = Inches(2.55)
    for i, (texto, cite) in enumerate(lacunas):
        add_rect(s, Inches(0.3), y, Inches(0.4), Inches(0.4), fill_color=VERMELHO)
        add_textbox(s, str(i + 1), Inches(0.3), y + Inches(0.02), Inches(0.4), Inches(0.38),
                    font_size=15, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        txb = s.shapes.add_textbox(Inches(0.85), y + Inches(0.01), Inches(12.2), Inches(0.5))
        tf = txb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = texto
        r1.font.size = Pt(15); r1.font.color.rgb = CINZA_TEXTO; r1.font.name = "Calibri"
        if cite:
            r2 = p.add_run(); r2.text = "   (" + cite + ")"
            r2.font.size = Pt(11.5); r2.font.italic = True
            r2.font.color.rgb = RGBColor(0x88, 0x88, 0x88); r2.font.name = "Calibri"
        y += Inches(0.78)

slide_fase1()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — FASE 2: IaC TERRAFORM (CONDENSADO)
# ════════════════════════════════════════════════════════════════════════════
def slide_fase2():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Fase 2 — Infraestrutura como Código",
               "Terraform 1.14  ·  modularização por domínio funcional  ·  5 stacks  ·  15 módulos")
    footer_bar(s, 8)

    headers = ["Ordem", "Stack", "Responsabilidades principais"]
    rows = [
        ["1", "foundation", "VPC  ·  Subnets (2 AZs)  ·  7 buckets S3 por ambiente"],
        ["2", "mlops", "SageMaker Managed MLflow Tracking Server  +  Studio Domain"],
        ["3", "platform", "EKS 1.32  ·  ECR  ·  SQS FIFO  ·  DynamoDB  ·  Kinesis  ·  Glue  ·  Athena"],
        ["4", "platform-k8s", "Deployments Kubernetes  ·  KEDA 2.18.3  ·  Ingress"],
        ["5", "platform-lambdas", "3 funções Lambda containerizadas (imagens ECR)"],
    ]
    add_table(s, headers, rows, Inches(0.25), Inches(1.28), Inches(12.8), Inches(2.6),
              font_size=14, col_widths=[Inches(0.8), Inches(2.5), Inches(9.4)])

    add_textbox(s, "Diferencial de projeto:", Inches(0.3), Inches(4.1),
                Inches(6.0), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "Modularização por domínio funcional, não por ambiente",
        "Remote state via S3 com locking nativo (use_lockfile, sem DynamoDB)",
        "Stacks superiores consomem outputs das inferiores (terraform_remote_state)",
        "Cada stack pode ser destruída/recriada independentemente",
    ], Inches(0.3), Inches(4.55), Inches(6.0), Inches(2.2), font_size=13.5, indent="   •  ")

    add_textbox(s, "Ambientes implementados:", Inches(6.6), Inches(4.1),
                Inches(6.4), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "DEV — us-east-1 (N. Virgínia)",
        "Staging — sa-east-1 (São Paulo)",
        "EKS: Kubernetes 1.32, 2–4 nós (t3.medium em DEV, t3.xlarge em Staging)",
        "Paridade de configuração entre ambientes, sem estado compartilhado",
    ], Inches(6.6), Inches(4.55), Inches(6.4), Inches(2.2), font_size=13.5, indent="   •  ")

slide_fase2()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — ARQUITETURA DA PLATAFORMA (VISÃO SIMPLIFICADA)
# ════════════════════════════════════════════════════════════════════════════
def slide_arquitetura():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Arquitetura da Plataforma — Visão Geral")
    footer_bar(s, 9)

    add_rect(s, Inches(0.25), Inches(1.35), Inches(12.8), Inches(0.34), fill_color=RGBColor(0xE8, 0xF0, 0xFF))
    add_textbox(s, "INFERÊNCIA EM TEMPO REAL",
                Inches(0.35), Inches(1.37), Inches(12.5), Inches(0.3), font_size=13, bold=True, color=AZUL_ESCURO)
    add_textbox(s,
                "Emissor 3DS  →  API Gateway  →  VPC Link  →  NLB  →  [EKS] Inference FastAPI (8 pods)  ↔  DynamoDB (feature store)  →  score",
                Inches(0.35), Inches(1.7), Inches(12.5), Inches(0.36), font_size=13.5)

    add_rect(s, Inches(0.25), Inches(2.18), Inches(12.8), Inches(0.34), fill_color=RGBColor(0xFF, 0xF0, 0xE8))
    add_textbox(s, "PROCESSAMENTO ASSÍNCRONO",
                Inches(0.35), Inches(2.2), Inches(12.5), Inches(0.3), font_size=13, bold=True, color=VERMELHO)
    add_textbox(s,
                "Inference  →  SQS FIFO  →  [EKS] Process (2–5 pods  ←  KEDA)  →  Kinesis Firehose  →  S3 (inference_logs/)",
                Inches(0.35), Inches(2.53), Inches(12.5), Inches(0.36), font_size=13.5)

    add_rect(s, Inches(0.25), Inches(3.01), Inches(12.8), Inches(0.34), fill_color=RGBColor(0xE8, 0xFF, 0xEE))
    add_textbox(s, "TREINAMENTO CONTÍNUO (event-driven, semanal)",
                Inches(0.35), Inches(3.03), Inches(12.5), Inches(0.3), font_size=13, bold=True, color=VERDE)
    add_textbox(s,
                "S3 (logs)  →  Glue (dom. 08h)  →  λ etl-delta-filter  →  λ training-launcher  →  SageMaker XGBoost  →  λ register-best-model  →  MLflow Registry",
                Inches(0.35), Inches(3.36), Inches(12.5), Inches(0.36), font_size=13.5)

    add_rect(s, Inches(0.25), Inches(3.84), Inches(12.8), Inches(0.34), fill_color=RGBColor(0xFF, 0xF8, 0xE1))
    add_textbox(s, "IaC E CI/CD",
                Inches(0.35), Inches(3.86), Inches(12.5), Inches(0.3), font_size=13, bold=True, color=LARANJA)
    add_textbox(s,
                "Terraform (5 stacks)  →  provisiona infraestrutura  |  AWS CodeBuild  →  build + push  →  Amazon ECR  →  deploy no EKS",
                Inches(0.35), Inches(4.19), Inches(12.5), Inches(0.36), font_size=13.5)

    highlight_box(s,
                  "Modelo MLflow \"fraud-score\" carregado diretamente do Registry na inicialização do pod — sem SageMaker Endpoint dedicado. "
                  "NLB conecta-se diretamente aos pods via TargetGroupBinding (IP target), sem ALB intermediário.",
                  Inches(0.25), Inches(4.85), Inches(12.8), Inches(0.85), font_size=14)

    add_textbox(s,
                "Arquitetura já projetada e implantada em DEV e Staging; cada trilha é detalhada nos próximos slides.",
                Inches(0.25), Inches(5.9), Inches(12.8), Inches(0.6), font_size=14, italic=True, color=AZUL_ESCURO)

slide_arquitetura()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — FASE 3: PIPELINES CI/CD + CT
# ════════════════════════════════════════════════════════════════════════════
def slide_pipelines():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Fase 3 — Pipelines CI/CD e Treinamento Contínuo (CT)",
               "Duas trilhas independentes, sem acoplamento de código")
    footer_bar(s, 10)

    add_rect(s, Inches(0.25), Inches(1.3), Inches(6.1), Inches(4.7),
             fill_color=RGBColor(0xF0, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_rect(s, Inches(0.25), Inches(1.3), Inches(6.1), Inches(0.48), fill_color=AZUL_ESCURO)
    add_textbox(s, "Trilha CI/CD — AWS CodeBuild", Inches(0.3), Inches(1.32),
                Inches(6.0), Inches(0.42), font_size=14, bold=True, color=BRANCO)
    bullet_lines(s, [
        "Commit  →  AWS CodeBuild  (buildspecs YAML versionados)",
        "Build da imagem Docker  →  push para Amazon ECR (6 repositórios)",
        "kubectl apply  →  atualiza deployment no EKS",
    ], Inches(0.35), Inches(2.0), Inches(5.9), Inches(2.2), font_size=15, indent="  •  ")
    add_textbox(s, "⚠  Ferramenta real: AWS CodeBuild (não GitHub Actions) — já corrigido no artigo.",
                Inches(0.35), Inches(5.15), Inches(5.9), Inches(0.7), font_size=12, italic=True, color=VERMELHO)

    add_rect(s, Inches(6.6), Inches(1.3), Inches(6.45), Inches(4.7),
             fill_color=RGBColor(0xE8, 0xFF, 0xEE), line_color=VERDE, line_width=Pt(1))
    add_rect(s, Inches(6.6), Inches(1.3), Inches(6.45), Inches(0.48), fill_color=VERDE)
    add_textbox(s, "Trilha CT — Treinamento Contínuo (serverless)", Inches(6.65), Inches(1.32),
                Inches(6.35), Inches(0.42), font_size=14, bold=True, color=BRANCO)
    bullet_lines(s, [
        "Glue (dom. 08h)  →  EventBridge  →  λ etl-delta-filter  →  Parquet",
        "S3 event  →  λ training-launcher  →  SageMaker XGBoost",
        "SageMaker registra métricas no MLflow Tracking",
        "λ register-best-model compara F1 candidato vs. produção",
        "Promove automaticamente se melhora — sem intervenção manual",
    ], Inches(6.7), Inches(2.0), Inches(6.2), Inches(2.6), font_size=15, indent="  •  ")

    highlight_box(s,
                  "Contribuição central:  CI/CD (código) e CT (ciclo de vida do modelo) operam como mecanismos "
                  "independentes, evitando o acoplamento identificado como lacuna na literatura.",
                  Inches(0.25), Inches(6.15), Inches(12.8), Inches(0.85), font_size=13)

slide_pipelines()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — FASE 3: INFERÊNCIA + KEDA
# ════════════════════════════════════════════════════════════════════════════
def slide_inferencia():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Fase 3 — Autoscaling: HPA (Inferência) + KEDA (Process)",
               "Dois serviços, duas estratégias de escalonamento distintas")
    footer_bar(s, 11)

    add_rect(s, Inches(0.25), Inches(1.3), Inches(6.1), Inches(4.9),
             fill_color=RGBColor(0xF0, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_rect(s, Inches(0.25), Inches(1.3), Inches(6.1), Inches(0.48), fill_color=AZUL_ESCURO)
    add_textbox(s, "Serviço de Inferência — HPA (CPU)", Inches(0.3), Inches(1.32),
                Inches(6.0), Inches(0.42), font_size=15, bold=True, color=BRANCO)
    bullet_lines(s, [
        "FastAPI (Python 3.12)  —  POST /v1/authorize-purchase",
        "8 réplicas base × 2 workers = 16 workers",
        "HPA escala 8 → 10 réplicas  (CPU > 50%)",
        "Modelo carregado do MLflow Registry no startup do pod",
        "Feature lookup em DynamoDB (histórico do cliente)",
    ], Inches(0.35), Inches(2.0), Inches(5.9), Inches(3.9), font_size=15, indent="  •  ")

    add_rect(s, Inches(6.6), Inches(1.3), Inches(6.45), Inches(4.9),
             fill_color=RGBColor(0xFF, 0xF8, 0xE1), line_color=VERMELHO, line_width=Pt(1))
    add_rect(s, Inches(6.6), Inches(1.3), Inches(6.45), Inches(0.48), fill_color=VERMELHO)
    add_textbox(s, "Serviço Process — KEDA 2.18.3 (assíncrono)", Inches(6.65), Inches(1.32),
                Inches(6.35), Inches(0.42), font_size=14.5, bold=True, color=BRANCO)
    keda_params = [
        ("Métrica:", "SQS FIFO queue depth (fila resultset)"),
        ("Mínimo de réplicas:", "2  (PDB: minAvailable = 1)"),
        ("Máximo de réplicas:", "5"),
        ("Msgs por pod:", "30  (+1 pod a cada 30 mensagens)"),
        ("Polling:", "15 segundos"),
        ("Scale-up:", "Imediato  (stabilization: 0s)"),
    ]
    y = Inches(1.92)
    for label, value in keda_params:
        txb = s.shapes.add_textbox(Inches(6.7), y, Inches(6.2), Inches(0.42))
        tf = txb.text_frame
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = label + "  "
        r1.font.bold = True; r1.font.size = Pt(14); r1.font.color.rgb = AZUL_ESCURO; r1.font.name = "Calibri"
        r2 = p.add_run(); r2.text = value
        r2.font.size = Pt(14); r2.font.color.rgb = CINZA_TEXTO; r2.font.name = "Calibri"
        y += Inches(0.5)

    highlight_box(s,
                  "Por que dois mecanismos?  A Inferência tem carga síncrona correlacionada a CPU — HPA basta. O "
                  "Process consome eventos em rajada da fila SQS, desacoplados de CPU — por isso usa KEDA.",
                  Inches(0.25), Inches(6.35), Inches(12.8), Inches(0.7), font_size=13)

slide_inferencia()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — FASE 4: VALIDAÇÃO EXPERIMENTAL — SETUP
# ════════════════════════════════════════════════════════════════════════════
def slide_validacao_setup():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Fase 4 — Validação Experimental: Setup",
               "Locust  ·  100 payloads 3DS reais  ·  2 ambientes AWS  ·  dados preliminares")
    footer_bar(s, 12)

    add_textbox(s, "Configuração do Locust:", Inches(0.25), Inches(1.28),
                Inches(5.8), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "1 usuário virtual = 1 RPS (constant_throughput)",
        "100 payloads reais de transações 3DS (produção)",
        "Endpoint: POST /v1/authorize-purchase via API Gateway",
        "Sucesso: HTTP 200 + campo \"score\" no body JSON",
    ], Inches(0.25), Inches(1.75), Inches(5.8), Inches(2.4), font_size=15, indent="  •  ")

    add_textbox(s, "SLA definido para o projeto:", Inches(6.7), Inches(1.28),
                Inches(6.0), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    headers_sla = ["Critério", "Meta"]
    rows_sla = [
        ["Disponibilidade", "100%  (0 falhas HTTP)"],
        ["P95 de latência", "< 500 ms"],
        ["P99 de latência", "< 1.000 ms"],
        ["Throughput", "≥ 100 RPS"],
    ]
    add_table(s, headers_sla, rows_sla, Inches(6.7), Inches(1.75), Inches(6.3), Inches(1.85),
              font_size=14, col_widths=[Inches(2.8), Inches(3.5)])

    add_textbox(s, "Cenários de Teste Executados até o momento  (preliminares):", Inches(0.25), Inches(4.5),
                Inches(12.5), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    headers_c = ["Cenário", "Tipo", "Ambiente", "Condição"]
    rows_c = [
        ["1–2", "Sequencial — 100 req.", "DEV  (us-east-1)", "Antes / após otimização de keepalive"],
        ["3", "Sequencial — 100 req.", "Staging  (sa-east-1)", "Após otimização de keepalive"],
        ["4–5", "Locust — 50 usuários", "DEV  (us-east-1)", "Antes / após otimização"],
    ]
    add_table(s, headers_c, rows_c, Inches(0.25), Inches(5.0), Inches(12.8), Inches(1.5),
              font_size=13.5, col_widths=[Inches(1.0), Inches(2.8), Inches(2.8), Inches(6.1)])

    add_textbox(s,
                "Nota:  SLA de produção contratado = 10.000 req/s; cenários acima validam uma fração nesta etapa "
                "preliminar (ver Trabalhos Futuros).",
                Inches(0.25), Inches(6.65), Inches(12.8), Inches(0.4), font_size=12, italic=True, color=VERMELHO)

slide_validacao_setup()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — PREVIEW DE RESULTADOS
# ════════════════════════════════════════════════════════════════════════════
def slide_preview_resultados():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Preview de Resultados",
               "Achado preliminar mais relevante — análise completa será apresentada na TCC II")
    footer_bar(s, 13)

    add_textbox(s, "Anomalia observada durante os testes sequenciais (DEV, sem HTTP keepalive):",
                Inches(0.3), Inches(1.35), Inches(12.7), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)

    add_rect(s, Inches(0.3), Inches(1.85), Inches(7.3), Inches(1.9),
             fill_color=RGBColor(0xF5, 0xF5, 0xF5), line_color=CINZA_TEXTO, line_width=Pt(0.5))
    add_textbox(s,
                "Req. 001–036:    ~180 ms   ← normal\n"
                "Req. 037:      5.217 ms   ⚠ PICO\n"
                "Req. 038–044:    ~180 ms   ← normal\n"
                "Req. 045:      2.605 ms   ⚠ PICO",
                Inches(0.45), Inches(1.95), Inches(7.0), Inches(1.7),
                font_size=14, font_name="Courier New")

    add_textbox(s, "Diagnóstico preliminar:", Inches(7.85), Inches(1.85),
                Inches(5.3), Inches(0.4), font_size=14, bold=True, color=AZUL_ESCURO)
    add_textbox(s,
                "Sem keepalive, o NLB encerra a conexão TCP por\n"
                "timeout — cada requisição reconecta toda a cadeia\n"
                "(API Gateway → VPC Link → NLB → pod), adicionando 1–4s.",
                Inches(7.85), Inches(2.25), Inches(5.3), Inches(1.5), font_size=13.5)

    highlight_box(s,
                  "Resultado preliminar após correção:  P95 caiu de 1.100 ms para 330 ms  (−70%)  no ambiente DEV, "
                  "sem qualquer alteração em infraestrutura, modelo ou algoritmo.",
                  Inches(0.3), Inches(3.95), Inches(12.7), Inches(0.85),
                  bg=RGBColor(0xE8, 0xFF, 0xEE), border=VERDE, font_size=16)

    add_textbox(s,
                "Falta validar na TCC II:  throughput na meta interna (100 RPS) e na meta contratada (10.000 req/s), "
                "comportamento do KEDA sob spike, e consolidação estatística dos 5 cenários.",
                Inches(0.3), Inches(5.1), Inches(12.7), Inches(0.8), font_size=15, italic=True, color=AZUL_ESCURO)

    add_rect(s, Inches(0.3), Inches(6.25), Inches(12.7), Inches(0.55), fill_color=VERMELHO)
    add_textbox(s, "⚠  Todos os dados desta página são preliminares — validação completa e consolidada na TCC II",
                Inches(0.3), Inches(6.32), Inches(12.7), Inches(0.45),
                font_size=15, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)

slide_preview_resultados()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — ESTADO ATUAL DO TRABALHO
# ════════════════════════════════════════════════════════════════════════════
def slide_estado_atual():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Estado Atual do Trabalho",
               "Progresso frente aos objetivos específicos definidos na proposta")
    footer_bar(s, 14)

    headers = ["#", "Objetivo Específico", "Status"]
    rows = [
        ["i", "Camadas de integração DevOps / MLOps", "✓  Implementado"],
        ["ii", "IaC via Terraform (15 módulos, 5 stacks, 2 ambientes)", "✓  Implementado"],
        ["iii", "Pipelines de CI/CD e Treinamento Contínuo", "✓  Implementado"],
        ["iv", "Governança e rastreabilidade via MLflow Registry", "✓  Implementado"],
        ["v", "Escalonamento orientado a eventos com KEDA + SQS", "⚠  Validado parcialmente"],
    ]
    add_table(s, headers, rows, Inches(0.25), Inches(1.3), Inches(12.8), Inches(2.65),
              font_size=14.5, col_widths=[Inches(0.7), Inches(9.3), Inches(2.8)])

    add_textbox(s, "Redação do artigo:", Inches(0.3), Inches(4.15),
                Inches(6.0), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "✓  Introdução, referencial teórico e metodologia redigidos",
        "✓  15+ referências bibliográficas levantadas e organizadas",
        "✓  Diagrama de arquitetura e correções de escopo aplicadas",
        "⚠  Seção de resultados em expansão (dados de staging e SLA)",
        "☐  Conclusão final e revisão ABNT completa — pendentes",
    ], Inches(0.3), Inches(4.6), Inches(12.5), Inches(2.3), font_size=14, indent="")

    highlight_box(s,
                  "Síntese: a plataforma está implementada e operando nos ambientes DEV e Staging, com escopo de autoria "
                  "(DevOps/Infra) confirmado pela documentação interna do cliente. A validação de throughput — meta "
                  "interna de 100 RPS e meta de produção contratada de 10.000 req/s — e a consolidação final da escrita "
                  "são o principal trabalho restante rumo à TCC II.",
                  Inches(0.3), Inches(6.5), Inches(12.7), Inches(0.65), font_size=13)

slide_estado_atual()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — TRABALHOS FUTUROS / RUMO À TCC II
# ════════════════════════════════════════════════════════════════════════════
def slide_trabalhos_futuros():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Trabalhos Futuros — Rumo à TCC II")
    footer_bar(s, 15)

    headers = ["#", "Próxima Etapa", "Base já existente no projeto"]
    rows = [
        ["1", "Validar 100 RPS (meta interna) e 10.000 req/s (SLA do cliente); spike KEDA", "locustfile.py — cenários já estruturados"],
        ["2", "Detecção automática de concept drift", "Statistics Reporter já coleta os dados necessários"],
        ["3", "Canary Release para modelos (10% do tráfego)", "Substituir promoção imediata no λ register-best-model"],
        ["4", "Benchmark KEDA (Process) vs. HPA (Inferência) sob a mesma carga", "Ambos já implantados; falta o teste comparativo sob carga"],
        ["5", "Consolidação final do artigo e defesa", "Seções já redigidas — resultados e conclusão em expansão"],
    ]
    add_table(s, headers, rows, Inches(0.25), Inches(1.3), Inches(12.8), Inches(3.2),
              font_size=14, col_widths=[Inches(0.6), Inches(6.2), Inches(6.0)])

    highlight_box(s,
                  "Limitações reconhecidas nesta etapa:  throughput de 100 RPS ainda não validado experimentalmente; "
                  "KEDA sob carga de spike não medido; CT sem gatilho automático por model drift; validação restrita à AWS.",
                  Inches(0.25), Inches(4.8), Inches(12.8), Inches(1.0), font_size=14)

    add_textbox(s,
                "Essas limitações não invalidam os resultados já obtidos — delimitam precisamente o escopo que será "
                "fechado até a entrega final da TCC II.",
                Inches(0.25), Inches(6.0), Inches(12.8), Inches(0.6), font_size=13, italic=True, color=AZUL_ESCURO)

slide_trabalhos_futuros()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — CONCLUSÃO PARCIAL
# ════════════════════════════════════════════════════════════════════════════
def slide_conclusao():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Conclusão Parcial")
    footer_bar(s, 16)

    add_textbox(s,
                "Os resultados obtidos até este ponto indicam que a integração eficiente de MLOps em pipelines DevOps requer:",
                Inches(0.3), Inches(1.35), Inches(12.7), Inches(0.5), font_size=15, bold=True, color=AZUL_ESCURO)

    pontos = [
        "(a)  Separação arquitetural explícita entre CI/CD e Treinamento Contínuo",
        "(b)  Automação serverless para eventos de ciclo de vida do modelo",
        "(c)  IaC modularizado por domínio funcional",
        "(d)  Governança centralizada via Model Registry",
        "(e)  Testes de carga com payloads reais como parte do processo — não etapa opcional",
    ]
    bullet_lines(s, pontos, Inches(0.3), Inches(1.95), Inches(12.5), Inches(2.2), font_size=15, indent="   ")

    highlight_box(s,
                  "Achado preliminar mais relevante:  HTTP keepalive foi a intervenção isolada de maior impacto observada "
                  "(P95: 1.100 ms → 330 ms, −70%) — sem alterar infraestrutura, modelo ou algoritmo.",
                  Inches(0.3), Inches(4.35), Inches(12.7), Inches(0.85),
                  bg=RGBColor(0xE8, 0xFF, 0xEE), border=VERDE, font_size=15)

    add_textbox(s,
                "Próxima etapa (TCC II):  consolidar a validação experimental completa rumo ao SLA de produção "
                "contratado pelo cliente (10.000 req/s), aprofundar a análise estatística dos resultados nos dois "
                "ambientes, e finalizar a redação do artigo com a discussão e conclusão definitivas.",
                Inches(0.3), Inches(5.4), Inches(12.7), Inches(1.2), font_size=14)

slide_conclusao()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — OBRIGADO / PERGUNTAS
# ════════════════════════════════════════════════════════════════════════════
def slide_obrigado():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, AZUL_MEDIO)
    add_rect(s, 0, 0, Inches(0.5), SLIDE_H, fill_color=VERMELHO)

    add_textbox(s, "Obrigado", Inches(0.75), Inches(1.3), Inches(10.0), Inches(1.0),
                font_size=40, bold=True, color=BRANCO)

    add_textbox(s, "Gustavo Liebl Pereira\nEngenharia de Software\nOrientador: Prof. Marcelo Semmer",
                Inches(0.75), Inches(2.5), Inches(8.0), Inches(1.2), font_size=16, color=RGBColor(0xAA, 0xCC, 0xFF))

    add_rect(s, Inches(0.75), Inches(3.85), Inches(6.0), Inches(0.03), fill_color=VERMELHO)

    add_textbox(s, "Repositório do Projeto", Inches(0.75), Inches(4.1),
                Inches(6.0), Inches(0.4), font_size=15, bold=True, color=BRANCO)
    add_textbox(s, "github.com/Gustaavolp/tcc-mlops-devops", Inches(0.75), Inches(4.55),
                Inches(8.0), Inches(0.4), font_size=15, color=RGBColor(0xAA, 0xCC, 0xFF))

    add_textbox(s, "Perguntas?", Inches(0.75), Inches(5.6), Inches(6.0), Inches(0.7),
                font_size=26, bold=True, color=VERMELHO)

slide_obrigado()


# ─── Salvar ─────────────────────────────────────────────────────────────────
OUTPUT = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/04_apresentacoes/2026-07-06_tcc1-meio-ano/versoes-anteriores/1_01h58_versao-15min/Apresentacao_TCC1_MeioAno_Gustavo.pptx"
prs.save(OUTPUT)
print(f"Salvo: {OUTPUT}")
print(f"Total de slides: {len(prs.slides.__iter__.__self__._sldIdLst)}")

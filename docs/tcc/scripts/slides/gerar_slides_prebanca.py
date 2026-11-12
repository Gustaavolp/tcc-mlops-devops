"""
Gerador de slides PowerPoint — TCC I, PRÉ-BANCA (Proposta de Pesquisa)
TCC MLOps / Gustavo Liebl Pereira
Duração alvo: 10 minutos — desenvolve a apresentação ATÉ Materiais e Métodos,
por instrução do orientador (pré-banca = proposta, não resultados finais).
Foco: tema, problema, justificativa, objetivos, referencial teórico principal
e metodologia (incl. materiais e métodos). Sem resultados, sem conclusão,
sem diagramas de evidência de implementação já validada.
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
TOTAL_SLIDES = 16

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
                "Gustavo Liebl Pereira  |  TCC I — Pré-Banca (Proposta de Pesquisa)  |  Orientador: Prof. Marcelo Semmer",
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
            run.font.color.rgb = CINZA_TEXTO
            run.font.name = "Calibri"
    return tbl

def highlight_box(slide, text, left, top, width, height, bg=AMARELO_BG, border=VERMELHO, font_size=15):
    add_rect(slide, left, top, width, height, fill_color=bg, line_color=border, line_width=Pt(1.5))
    add_textbox(slide, text, left + Inches(0.15), top + Inches(0.1),
                width - Inches(0.3), height - Inches(0.2),
                font_size=font_size, color=RGBColor(0x22, 0x22, 0x22), font_name="Calibri")

ANEXO_IMG_DIR = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/assets/anexo_arquitetura_imgs"

def slide_diagrama_proposta(titulo, img_filename, page_num):
    """Diagrama de referencia da arquitetura PROPOSTA (documentacao tecnica do estudo
    de caso, cliente anonimizado) — nao e resultado experimental, e material de apoio
    a proposta metodologica, a ser implementado e validado na etapa seguinte."""
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    add_rect(s, 0, 0, SLIDE_W, Inches(0.65), fill_color=AZUL_ESCURO)
    add_textbox(s, titulo,
                Inches(0.3), Inches(0.12), Inches(9.6), Inches(0.45),
                font_size=20, bold=True, color=BRANCO, font_name="Calibri")
    add_textbox(s, "Arquitetura proposta — referência", Inches(9.65), Inches(0.18),
                Inches(3.35), Inches(0.35), font_size=11, color=RGBColor(0xCC, 0xDD, 0xFF),
                align=PP_ALIGN.RIGHT, font_name="Calibri")

    img_h = Inches(5.65)
    img_w = Inches(5.65 * (4400 / 2475))
    left = (SLIDE_W - img_w) / 2
    top = Inches(0.75)
    s.shapes.add_picture(f"{ANEXO_IMG_DIR}/{img_filename}", left, top, width=img_w, height=img_h)

    add_textbox(s, "Fonte: documentação técnica do estudo de caso (cliente anonimizado). "
                   "Arquitetura de referência para a proposta — implementação e validação na etapa seguinte.",
                Inches(0.3), Inches(6.48), Inches(12.7), Inches(0.55),
                font_size=9, italic=True, color=RGBColor(0x88, 0x88, 0x88), font_name="Calibri")

    footer_bar(s, page_num)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — CAPA
# ════════════════════════════════════════════════════════════════════════════
def slide_capa():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, AZUL_MEDIO)
    add_rect(s, 0, 0, Inches(0.5), SLIDE_H, fill_color=VERMELHO)
    add_rect(s, 0, Inches(6.3), SLIDE_W, Inches(1.2), fill_color=RGBColor(0x0A, 0x1A, 0x35))

    add_rect(s, Inches(0.75), Inches(0.55), Inches(3.6), Inches(0.4), fill_color=VERMELHO)
    add_textbox(s, "PRÉ-BANCA  —  TCC I",
                Inches(0.75), Inches(0.58), Inches(3.5), Inches(0.34),
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

    add_textbox(s, "Trabalho de Conclusão de Curso  —  Pré-banca (proposta de pesquisa)",
                Inches(0.75), Inches(6.38), Inches(9.5), Inches(0.35),
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
        "01  Tema e Contexto",
        "02  Problema de Pesquisa",
        "03  Justificativa",
        "04  Objetivos",
    ]
    items_col2 = [
        "05  Referencial Teórico",
        "06  Metodologia",
        "07  Materiais, Métodos e Arquitetura Proposta",
        "08  Cronograma — TCC II",
    ]

    for i, item in enumerate(items_col1):
        y = Inches(1.6) + i * Inches(0.95)
        add_rect(s, Inches(0.35), y, Inches(0.06), Inches(0.5), fill_color=VERMELHO)
        add_textbox(s, item, Inches(0.55), y + Inches(0.06),
                    Inches(5.9), Inches(0.5), font_size=17, color=AZUL_ESCURO)

    for i, item in enumerate(items_col2):
        y = Inches(1.6) + i * Inches(0.95)
        add_rect(s, Inches(6.9), y, Inches(0.06), Inches(0.5), fill_color=VERMELHO)
        add_textbox(s, item, Inches(7.1), y + Inches(0.06),
                    Inches(5.9), Inches(0.5), font_size=17, color=AZUL_ESCURO)

    highlight_box(s,
                  "Esta é uma pré-banca: apresento a proposta de pesquisa até Materiais e Métodos, "
                  "conforme orientação — sem resultados finais, que ficam para a defesa da TCC I completa.",
                  Inches(0.35), Inches(6.0), Inches(12.6), Inches(1.0), font_size=13.5)

slide_agenda()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — TEMA E CONTEXTO
# ════════════════════════════════════════════════════════════════════════════
def slide_tema():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Tema e Contexto",
               "A operacionalização de Machine Learning como extensão do DevOps")
    footer_bar(s, 3)

    add_textbox(s,
                "A evolução da Inteligência Artificial transformou a forma como organizações extraem valor de "
                "dados. Mas a transição de um modelo experimental para um sistema produtivo resiliente segue "
                "sendo um dos maiores gargalos da Engenharia de Software atual.",
                Inches(0.3), Inches(1.35), Inches(12.7), Inches(1.1), font_size=15.5)

    highlight_box(s,
                  "85% dos projetos de ML nunca chegam à produção (Gartner, 2022) — e a maior parte do código de "
                  "um sistema de ML real é infraestrutura, não o modelo em si (Sculley et al., 2015).",
                  Inches(0.3), Inches(2.6), Inches(12.7), Inches(0.85), font_size=14.5)

    add_textbox(s, "Motivação prática deste trabalho:", Inches(0.3), Inches(3.7),
                Inches(6.0), Inches(0.4), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "Estudo de caso real: plataforma de detecção de fraude em transações eletrônicas (setor de "
        "pagamentos), atualmente em desenvolvimento por uma empresa de grande porte",
        "Contexto formal: exigências rígidas de SLA (latência, disponibilidade, throughput) e conformidade "
        "regulatória (LGPD) — cenário típico de produção crítica de ML",
        "Escopo de autoria deste TCC: a camada de Engenharia DevOps/Infraestrutura do projeto "
        "(IaC, orquestração, CI/CD, escalonamento) — o modelo de ML foi construído por outra frente da equipe",
    ], Inches(0.3), Inches(4.15), Inches(12.7), Inches(2.0), font_size=14.5, indent="  •  ")

    add_textbox(s,
                "Dados e documentos internos do estudo de caso são tratados de forma anonimizada e agregada nesta proposta.",
                Inches(0.3), Inches(6.5), Inches(12.7), Inches(0.45), font_size=11.5, italic=True, color=CINZA_TEXTO)

slide_tema()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — PROBLEMA DE PESQUISA
# ════════════════════════════════════════════════════════════════════════════
def slide_problema():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Problema de Pesquisa",
               "A lacuna entre experimentação (Data Science) e operação (Engenharia)")
    footer_bar(s, 4)

    add_rect(s, Inches(0.3), Inches(1.35), Inches(6.1), Inches(1.75),
             fill_color=RGBColor(0xE8, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_textbox(s, "Cientista de Dados", Inches(0.4), Inches(1.41),
                Inches(5.9), Inches(0.35), font_size=15, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "✓  Modelo treinado com boa acurácia",
        "✗  Sem API de servimento nem versionamento",
        "✗  Sem pipeline de retreinamento",
    ], Inches(0.4), Inches(1.8), Inches(5.9), Inches(1.2), font_size=13.5, indent="")

    add_rect(s, Inches(6.6), Inches(1.35), Inches(6.45), Inches(1.75),
             fill_color=RGBColor(0xFF, 0xEE, 0xEE), line_color=VERMELHO, line_width=Pt(1))
    add_textbox(s, "Engenharia / Ops", Inches(6.7), Inches(1.41),
                Inches(6.25), Inches(0.35), font_size=15, bold=True, color=VERMELHO)
    bullet_lines(s, [
        "✗  Deploy manual e frágil, sem rastreabilidade",
        "✗  Model drift não detectado",
        "✗  Governança inexistente",
    ], Inches(6.7), Inches(1.8), Inches(6.25), Inches(1.2), font_size=13.5, indent="")

    add_textbox(s,
                "Sistemas de ML dependem não apenas de código, mas da evolução contínua dos dados e das "
                "métricas de performance do próprio modelo — o que gera desafios de versionamento e "
                "degradação (model drift, exemplificado à esquerda) sem uma ponte estruturada entre "
                "experimentação e operação de TI.",
                Inches(0.3), Inches(3.3), Inches(12.7), Inches(1.15), font_size=14)

    highlight_box(s,
                  "Pergunta de pesquisa:  Como integrar de forma eficiente, escalável e automatizada o ciclo de "
                  "vida de modelos de Machine Learning (MLOps) em pipelines de DevOps, garantindo entrega "
                  "contínua e governança operacional em ambientes de produção complexos?",
                  Inches(0.3), Inches(4.65), Inches(12.7), Inches(1.15), font_size=15)

slide_problema()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — JUSTIFICATIVA
# ════════════════════════════════════════════════════════════════════════════
def slide_justificativa():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Justificativa",
               "Por que este trabalho é relevante")
    footer_bar(s, 5)

    # Card unico: argumento central em cadeia (tecnica -> pratica -> academica
    # fundidas em uma unica linha de raciocinio, em vez de 3 frentes separadas)
    card_left, card_top = Inches(0.3), Inches(1.4)
    card_w, card_h = Inches(12.7), Inches(4.55)
    add_rect(s, card_left, card_top, card_w, card_h,
             fill_color=RGBColor(0xE8, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
    add_rect(s, card_left, card_top, Inches(0.14), card_h, fill_color=VERMELHO)

    add_textbox(s,
                "A maior parte do esforço real em sistemas de ML em produção está na "
                "engenharia ao redor do modelo — não no algoritmo.",
                card_left + Inches(0.45), card_top + Inches(0.3),
                card_w - Inches(0.8), Inches(1.5),
                font_size=22, bold=True, color=AZUL_ESCURO)
    add_textbox(s, "(Sculley et al., 2015)",
                card_left + Inches(0.45), card_top + Inches(1.75),
                card_w - Inches(0.8), Inches(0.35),
                font_size=13, italic=True, color=CINZA_TEXTO)

    add_textbox(s,
                "Mesmo assim, a maioria das organizações trata MLOps como extensão informal do "
                "DevOps, sem arquitetura, automação ou governança adequadas. Este trabalho propõe "
                "uma arquitetura de referência para um caso real de produção, unindo essa urgência "
                "de mercado à lacuna já documentada na literatura.",
                card_left + Inches(0.45), card_top + Inches(2.3),
                card_w - Inches(0.8), Inches(1.5),
                font_size=16)

    add_rect(s, card_left + Inches(0.45), card_top + Inches(3.85),
              card_w - Inches(0.9), Inches(0.5), fill_color=BRANCO, line_color=VERMELHO, line_width=Pt(1))
    add_textbox(s,
                "Urgência prática de mercado  +  lacuna acadêmica documentada  —  convergindo no mesmo problema.",
                card_left + Inches(0.55), card_top + Inches(3.93),
                card_w - Inches(1.1), Inches(0.4),
                font_size=13, italic=True, bold=True, color=VERMELHO, align=PP_ALIGN.CENTER)

slide_justificativa()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — OBJETIVOS
# ════════════════════════════════════════════════════════════════════════════
def slide_objetivos():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Objetivos")
    footer_bar(s, 6)

    highlight_box(s,
                  "Objetivo Geral:  demonstrar, por meio de um projeto prático em nuvem, a implementação de uma "
                  "arquitetura de MLOps integrada a pipelines DevOps — identificando desafios técnicos e boas "
                  "práticas para entrega contínua de modelos de Machine Learning.",
                  Inches(0.3), Inches(1.3), Inches(12.7), Inches(0.95), font_size=15)

    add_textbox(s, "Objetivos Específicos", Inches(0.3), Inches(2.45),
                Inches(4.0), Inches(0.45), font_size=18, bold=True, color=AZUL_ESCURO)

    objs = [
        ("i", "Projetar a integração DevOps / MLOps com separação explícita de responsabilidades"),
        ("ii", "Implementar infraestrutura como código (Terraform) modularizada por domínio"),
        ("iii", "Automatizar pipelines de CI/CD e Treinamento Contínuo (CT)"),
        ("iv", "Implementar governança de modelos via MLflow (versionamento e promoção)"),
        ("v", "Validar o escalonamento orientado a eventos (KEDA) em serviços de inferência"),
    ]
    for i, (num, text) in enumerate(objs):
        y = Inches(3.0) + i * Inches(0.66)
        add_rect(s, Inches(0.3), y + Inches(0.02), Inches(0.42), Inches(0.42), fill_color=AZUL_ESCURO)
        add_textbox(s, num, Inches(0.3), y + Inches(0.02), Inches(0.42), Inches(0.42),
                    font_size=14, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        add_textbox(s, text, Inches(0.88), y + Inches(0.04),
                    Inches(12.1), Inches(0.5), font_size=14.5)

slide_objetivos()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — REFERENCIAL TEÓRICO (fundido — 4 pilares em grade 2x2)
# ════════════════════════════════════════════════════════════════════════════
def slide_referencial():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Referencial Teórico",
               "Os quatro pilares teóricos que sustentam a proposta")
    footer_bar(s, 7)

    pilares = [
        ("Dívida Técnica em ML", "Sculley et al., 2015", RGBColor(0xE8, 0xF4, 0xFF), AZUL_ESCURO,
         "Código de ML é só uma fração pequena do sistema real — o esforço está em dados, "
         "configuração e monitoramento."),
        ("Pilares do MLOps + CT", "Kreuzberger et al., 2023", RGBColor(0xFF, 0xF8, 0xE1), LARANJA,
         "MLOps versiona código, modelo e dado; o Continuous Training retreina automaticamente "
         "quando a performance degrada."),
        ("Infraestrutura como Código", "Karimibiuki et al., 2022", RGBColor(0xE8, 0xFF, 0xEE), VERDE,
         "Terraform garante paridade entre ambientes, eliminando erro humano no provisionamento "
         "de infraestrutura."),
        ("Escalabilidade com KEDA", "Kubernetes Event-driven Autoscaling", RGBColor(0xFF, 0xEE, 0xEE), VERMELHO,
         "Autoscaling orientado a eventos escala réplicas pela demanda real da fila, não por uso de CPU."),
    ]
    positions = [(Inches(0.3), Inches(1.35)), (Inches(6.75), Inches(1.35)),
                 (Inches(0.3), Inches(4.15)), (Inches(6.75), Inches(4.15))]
    card_w, card_h = Inches(6.3), Inches(2.65)

    for (titulo, autor, bg, fg, texto), (x, y) in zip(pilares, positions):
        add_rect(s, x, y, card_w, card_h, fill_color=bg, line_color=fg, line_width=Pt(1))
        add_rect(s, x, y, card_w, Inches(0.62), fill_color=fg)
        add_textbox(s, titulo, x + Inches(0.15), y + Inches(0.06),
                    card_w - Inches(0.3), Inches(0.35), font_size=15, bold=True, color=BRANCO)
        add_textbox(s, autor, x + Inches(0.15), y + Inches(0.38),
                    card_w - Inches(0.3), Inches(0.24), font_size=10.5, italic=True,
                    color=RGBColor(0xEE, 0xEE, 0xEE))
        add_textbox(s, texto, x + Inches(0.2), y + Inches(0.78),
                    card_w - Inches(0.4), card_h - Inches(0.95), font_size=13.5)

slide_referencial()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — METODOLOGIA: VISÃO GERAL
# ════════════════════════════════════════════════════════════════════════════
def slide_metodologia():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Metodologia — Visão Geral",
               "Pesquisa aplicada, experimental e construtiva")
    footer_bar(s, 8)

    fases = [
        ("Fase 1", "Levantamento\nBibliográfico",
         "IEEE Xplore\nACM Digital Library\nGoogle Scholar\nMapeamento de lacunas"),
        ("Fase 2", "Desenvolvimento da\nInfraestrutura",
         "Terraform (IaC)\nVPC, EKS, S3, SQS\nModularização por\ndomínio funcional"),
        ("Fase 3", "Implementação\ndo Pipeline",
         "CI/CD (build/deploy)\nIntegração MLflow\nTreinamento automático\ne promoção condicional"),
        ("Fase 4", "Validação\nExperimental (planejada)",
         "Testes de carga\nsimulando picos\nde tráfego\nHPA vs. KEDA"),
    ]
    for i, (fase, titulo, detalhes) in enumerate(fases):
        x = Inches(0.25) + i * Inches(3.27)
        add_rect(s, x, Inches(1.35), Inches(3.0), Inches(4.6),
                 fill_color=RGBColor(0xF0, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(1))
        add_rect(s, x, Inches(1.35), Inches(3.0), Inches(0.55), fill_color=AZUL_ESCURO)
        add_textbox(s, fase, x + Inches(0.05), Inches(1.38),
                    Inches(2.9), Inches(0.45), font_size=14, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        add_textbox(s, titulo, x + Inches(0.1), Inches(2.0),
                    Inches(2.8), Inches(1.0), font_size=15, bold=True, color=AZUL_ESCURO, align=PP_ALIGN.CENTER)
        add_textbox(s, detalhes, x + Inches(0.12), Inches(3.1),
                    Inches(2.76), Inches(2.1), font_size=13.5, align=PP_ALIGN.CENTER)
        if i < 3:
            add_textbox(s, "→", x + Inches(2.97), Inches(2.4),
                        Inches(0.35), Inches(0.55), font_size=22, bold=True, color=VERMELHO, align=PP_ALIGN.CENTER)

    highlight_box(s,
                  "Pesquisa aplicada, experimental e construtiva:  o próprio sistema a ser implementado é, ao "
                  "mesmo tempo, o artefato e o instrumento de validação da proposta.",
                  Inches(0.25), Inches(6.1), Inches(12.8), Inches(0.95), font_size=15)

slide_metodologia()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — MATERIAIS E MÉTODOS
# ════════════════════════════════════════════════════════════════════════════
def slide_materiais_metodos():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Materiais e Métodos",
               "Ambiente do estudo de caso, tecnologias e método de validação planejado")
    footer_bar(s, 9)

    add_textbox(s, "Materiais (stack tecnológica):", Inches(0.3), Inches(1.5),
                Inches(6.0), Inches(0.4), font_size=16, bold=True, color=AZUL_ESCURO)
    bullet_lines(s, [
        "IaC:  Terraform",
        "Orquestração:  Docker + Kubernetes (Amazon EKS)",
        "CI/CD:  pipelines declarativos",
        "Governança de ML:  MLflow (tracking + registry)",
        "Escalonamento:  filas de mensagens + KEDA",
        "Linguagens:  Python e HCL",
    ], Inches(0.3), Inches(2.05), Inches(12.7), Inches(2.6), font_size=16, indent="  •  ", line_spacing_pt=10)

    highlight_box(s,
                  "Método de validação planejado:  testes de carga com Locust simulando tráfego real, comparando "
                  "o comportamento do escalonamento tradicional (CPU) e do escalonamento orientado a eventos "
                  "(KEDA) sob picos de demanda — execução e análise detalhada ficam para a etapa seguinte.",
                  Inches(0.3), Inches(5.2), Inches(12.7), Inches(1.15), font_size=15)

slide_materiais_metodos()
slide_diagrama_proposta("Arquitetura Proposta — Visão Geral da Infraestrutura", "elo-03.png", 10)
slide_diagrama_proposta("Arquitetura Proposta — Fluxo de Inferência (Síncrono)", "elo-04.png", 11)
slide_diagrama_proposta("Arquitetura Proposta — Fluxo de Processamento (Assíncrono)", "elo-05.png", 12)
slide_diagrama_proposta("Arquitetura Proposta — Fluxo de Treinamento Contínuo (MLOps)", "elo-06.png", 13)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — CRONOGRAMA / PRÓXIMOS PASSOS
# ════════════════════════════════════════════════════════════════════════════
def slide_cronograma():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Cronograma — Rumo à TCC I / TCC II",
               "Próximos passos a partir desta proposta")
    footer_bar(s, 14)

    etapas = [
        ("Etapa 1", "Consolidar a implementação da infraestrutura e dos pipelines descritos na metodologia"),
        ("Etapa 2", "Executar a validação experimental planejada (testes de carga, comparação de escalonamento)"),
        ("Etapa 3", "Analisar os resultados obtidos e redigir as seções de Resultados e Discussão"),
        ("Etapa 4", "Consolidar a conclusão final e finalizar a redação do artigo completo (TCC II)"),
    ]
    y = Inches(1.5)
    for titulo, desc in etapas:
        add_rect(s, Inches(0.3), y, Inches(1.5), Inches(0.85), fill_color=AZUL_ESCURO)
        add_textbox(s, titulo, Inches(0.3), y + Inches(0.22), Inches(1.5), Inches(0.45),
                    font_size=14, bold=True, color=BRANCO, align=PP_ALIGN.CENTER)
        add_rect(s, Inches(1.9), y, Inches(11.1), Inches(0.85),
                 fill_color=RGBColor(0xF0, 0xF4, 0xFF), line_color=AZUL_ESCURO, line_width=Pt(0.75))
        add_textbox(s, desc, Inches(2.1), y + Inches(0.12), Inches(10.7), Inches(0.6), font_size=14.5)
        y += Inches(1.05)

    highlight_box(s,
                  "Esta pré-banca marca o fechamento da proposta — arquitetura, pipelines e resultados "
                  "experimentais completos serão apresentados na etapa seguinte do trabalho.",
                  Inches(0.3), Inches(5.85), Inches(12.7), Inches(0.9), font_size=14)

slide_cronograma()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — REFERÊNCIAS PRINCIPAIS
# ════════════════════════════════════════════════════════════════════════════
def slide_referencias():
    s = prs.slides.add_slide(blank_layout)
    set_slide_bg(s, BRANCO)
    header_bar(s, "Referências Principais")
    footer_bar(s, 15)

    refs = [
        "SCULLEY, D. et al. Hidden Technical Debt in Machine Learning Systems. NeurIPS, v. 28, 2015.",
        "TREVEIL, M. et al. Introducing MLOps: How to Scale Machine Learning in the Enterprise. O'Reilly, 2020.",
        "KREUZBERGER, D.; KÜHL, N.; HIRSCHL, S. Machine Learning Operations (MLOps): Overview, Definition, "
        "and Architecture. IEEE Access, v. 11, 2023.",
        "KARIMIBIUKI, M. et al. Infrastructure as Code for Machine Learning. IEEE Software, 2022.",
        "AWS. Machine Learning Lens — AWS Well-Architected Framework. 2026.",
        "FOWLER, M. Continuous Integration. MartinFowler.com, 2006.",
    ]
    y = Inches(1.5)
    for r in refs:
        add_textbox(s, "•  " + r, Inches(0.4), y, Inches(12.5), Inches(0.65), font_size=15)
        y += Inches(0.72)

slide_referencias()


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
OUTPUT = "/home/gustaavolp/tcc-mlops-devops/docs/tcc/04_apresentacoes/2026-07-06_tcc1-meio-ano/Apresentacao_TCC1_MeioAno_Gustavo.pptx"
prs.save(OUTPUT)
print(f"Salvo: {OUTPUT}")
print(f"Total de slides: {len(prs.slides.__iter__.__self__._sldIdLst)}")

# -*- coding: utf-8 -*-
"""Monta o artigo sobre o pacote do MODELO_PREENCHIMENTO_DE_ARTIGO.docx (estilos, margens, notas)."""
import os, re, shutil, sys, zipfile
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
import content as C

TEMPLATE, FIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
import tempfile, atexit
WORK = tempfile.mkdtemp(prefix="artigo_build_")
atexit.register(shutil.rmtree, WORK, True)
with zipfile.ZipFile(TEMPLATE) as z:
    z.extractall(WORK)
for root, _, files in os.walk(WORK):  # pacote de terceiros: remove links simbólicos
    for f in files:
        p = os.path.join(root, f)
        if os.path.islink(p):
            os.unlink(p)

ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'

# ---------------------------------------------------------------- inline
def runs(text, base_rpr=""):
    """{b}{/b} {i}{/i} {ref:id} -> runs. Retorna XML."""
    out, b, i = [], False, False
    for tok in re.split(r"(\{/?[bi]\}|\{ref:[a-z0-9]+\})", text):
        if not tok:
            continue
        if tok == "{b}": b = True; continue
        if tok == "{/b}": b = False; continue
        if tok == "{i}": i = True; continue
        if tok == "{/i}": i = False; continue
        m = re.match(r"\{ref:([a-z0-9]+)\}", tok)
        rpr = base_rpr + ("<w:b/>" if b else "") + ("<w:i/>" if i else "")
        if m:
            out.append(ref_field(m.group(1), rpr))
            continue
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return "".join(out)

# ------------------------------------------------- captions / cross-refs
SEQ = {"table": "Tabela", "quadro": "Quadro", "figure": "Figura"}
LABELS = {}   # id -> (rótulo, número)
counters = {}
for kind, data in C.BODY:
    if kind in SEQ:
        lab = SEQ[kind]
        counters[lab] = counters.get(lab, 0) + 1
        LABELS[data["id"]] = (lab, counters[lab])

BM = {}
def bm_id(key):
    BM.setdefault(key, len(BM) + 10)
    return BM[key]

def ref_field(rid, rpr):
    lab, n = LABELS[rid]
    name = f"_Ref_{rid}"
    r = lambda inner: f'<w:r><w:rPr>{rpr}</w:rPr>{inner}</w:r>'
    return (r('<w:fldChar w:fldCharType="begin"/>')
            + r(f'<w:instrText xml:space="preserve"> REF {name} \\h </w:instrText>')
            + r('<w:fldChar w:fldCharType="separate"/>')
            + r(f'<w:t>{lab} {n}</w:t>')
            + r('<w:fldChar w:fldCharType="end"/>'))

def caption(rid, title, keep_next=True):
    lab, n = LABELS[rid]
    name, bid = f"_Ref_{rid}", bm_id(rid)
    rp = ARIAL + '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    r = lambda inner: f'<w:r><w:rPr>{rp}</w:rPr>{inner}</w:r>'
    ppr = (f'<w:pPr>{"<w:keepNext/>" if keep_next else ""}<w:spacing w:before="240" w:after="60" w:line="240" w:lineRule="auto"/>'
           f'<w:jc w:val="left"/></w:pPr>')
    return (f'<w:p>{ppr}<w:bookmarkStart w:id="{bid}" w:name="{name}"/>'
            + r(f'<w:t xml:space="preserve">{lab} </w:t>')
            + r('<w:fldChar w:fldCharType="begin"/>')
            + r(f'<w:instrText xml:space="preserve"> SEQ {lab} \\* ARABIC </w:instrText>')
            + r('<w:fldChar w:fldCharType="separate"/>')
            + r(f'<w:t>{n}</w:t>')
            + r('<w:fldChar w:fldCharType="end"/>')
            + f'<w:bookmarkEnd w:id="{bid}"/>'
            + r(f'<w:t xml:space="preserve"> – {escape(title)}</w:t>')
            + '</w:p>')

def small_para(text, after=0, keep_next=False):
    rp = ARIAL + '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    return (f'<w:p><w:pPr>{"<w:keepNext/>" if keep_next else ""}<w:spacing w:before="40" w:after="{after}" w:line="240" w:lineRule="auto"/>'
            f'<w:jc w:val="left"/></w:pPr>{runs(text, rp)}</w:p>')

# ---------------------------------------------------------------- blocks
def P(text, style="Recuodecorpodetexto", extra_ppr="", base_rpr=""):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{extra_ppr}</w:pPr>{runs(text, base_rpr)}</w:p>'

def blank(style="Recuodecorpodetexto", single=False):
    sp = '<w:spacing w:line="240" w:lineRule="auto"/>' if single else ""
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{sp}</w:pPr></w:p>'

def H1(text):
    # modelo: uma linha em branco entre texto e título e entre título e texto
    return blank() + P(text, "Ttulo1") + blank()

def H2(text, before=360):
    return (f'<w:p><w:pPr><w:pStyle w:val="Ttulo2"/><w:spacing w:before="{before}" w:after="0" '
            f'w:line="360" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="0"/></w:pPr>'
            f'{runs(text, "<w:b/>")}</w:p>')

def borders(kind):
    if kind == "quadro":   # quadro: bordas fechadas
        e = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        return "<w:tblBorders>" + "".join(e.format(x) for x in
               ["top", "left", "bottom", "right", "insideH", "insideV"]) + "</w:tblBorders>"
    # tabela (IBGE): só traços horizontais externos, laterais abertas
    return ('<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:left w:val="nil"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>')

def table(kind, d):
    widths, total = d["widths"], sum(d["widths"])
    rp = ARIAL + '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    def cell(txt, w, header, first_col, last_row):
        kn = "<w:keepNext/>"
        tcb = ""
        if kind == "table" and header:
            tcb = '<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tcBorders>'
        jc = "left" if (first_col and not header) else "center"
        if kind == "quadro" and not header:
            jc = "left"
        rpr = rp + ("<w:b/>" if header else "")
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{tcb}<w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr>{kn}<w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>'
                f'<w:jc w:val="{jc}"/></w:pPr>{runs(txt, rpr)}</w:p></w:tc>')
    rows = []
    hdr = "".join(cell(t, w, True, j == 0, False) for j, (t, w) in enumerate(zip(d["header"], widths)))
    rows.append(f'<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>{hdr}</w:tr>')
    for k, r in enumerate(d["rows"]):
        cs = "".join(cell(t, w, False, j == 0, k == len(d["rows"]) - 1) for j, (t, w) in enumerate(zip(r, widths)))
        rows.append(f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{cs}</w:tr>')
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/>'
           f'{borders(kind)}<w:tblLayout w:type="fixed"/>'
           f'<w:tblCellMar><w:left w:w="85" w:type="dxa"/><w:right w:w="85" w:type="dxa"/></w:tblCellMar>'
           f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
           f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(rows)}</w:tbl>')
    out = caption(d["id"], d["title"]) + tbl
    if d.get("note"):
        out += small_para(d["note"])
    out += small_para(d["source"], after=240)
    return out

def figure(d):
    from PIL import Image
    w_px, h_px = Image.open(FIG).size
    cx = 16 * 360000
    cy = int(cx * h_px / w_px)
    drawing = (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="100" name="Figura 1"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="0" name="arquitetura.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="rIdFig1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing>')
    pic = (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
           f'<w:jc w:val="center"/></w:pPr><w:r>{drawing}</w:r></w:p>')
    return caption(d["id"], d["title"]) + pic + small_para(d["source"], after=240)

# ---------------------------------------------------------------- document
parts = []
parts.append(P(escape(C.TITLE) if False else C.TITLE, "Primeirorecuodecorpodetexto"))
parts.append(blank())
for k, (name, _) in enumerate(C.AUTHORS, start=1):
    rp = ARIAL + '<w:sz w:val="24"/><w:szCs w:val="24"/>'
    parts.append(
        f'<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="right"/></w:pPr>'
        f'<w:r><w:rPr>{rp}</w:rPr><w:t>{escape(name)}</w:t></w:r>'
        f'<w:r><w:rPr><w:rStyle w:val="Refdenotaderodap"/>{rp}</w:rPr><w:footnoteReference w:id="{k}"/></w:r></w:p>')
parts.append(blank())
SINGLE = '<w:spacing w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/>'
parts.append(P("RESUMO", "Primeirorecuodecorpodetexto"))
parts.append(P(C.RESUMO, extra_ppr=SINGLE))
parts.append(blank(single=True))
parts.append(P("{b}Palavras-chave{/b}: " + C.PALAVRAS, extra_ppr=SINGLE))
parts.append(blank(single=True))
parts.append(P("ABSTRACT", "Primeirorecuodecorpodetexto"))
parts.append(P(C.ABSTRACT, extra_ppr=SINGLE))
parts.append(blank(single=True))
parts.append(P("{b}Keywords{/b}: " + C.KEYWORDS, extra_ppr=SINGLE))

prev = None
for kind, data in C.BODY:
    if kind == "h1":
        parts.append(H1(data))
    elif kind == "h2":
        parts.append(H2(data, 0 if prev == "h1" else 360))
    elif kind == "p":
        parts.append(P(data))
    elif kind in ("table", "quadro"):
        parts.append(table(kind, data))
    elif kind == "figure":
        parts.append(figure(data))
    prev = kind

parts.append(H1("REFERÊNCIAS"))
for ref in C.REFS:
    parts.append(P(ref, extra_ppr='<w:spacing w:after="240" w:line="240" w:lineRule="auto"/>'
                                 '<w:ind w:firstLine="0"/><w:jc w:val="left"/>'))

# ----- grava document.xml mantendo cabeçalho de namespaces e sectPr do modelo
dpath = os.path.join(WORK, "word", "document.xml")
src = open(dpath, encoding="utf-8").read()
head = src[: src.index("<w:body>") + len("<w:body>")]
sect = re.search(r"<w:sectPr.*?</w:sectPr>", src, re.S).group(0)
if "xmlns:pic=" not in head:
    head = head.replace("<w:document ", '<w:document xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" ', 1)
open(dpath, "w", encoding="utf-8").write(head + "".join(parts) + sect + "</w:body></w:document>")

# ----- notas de rodapé de afiliação (substitui as do modelo)
fpath = os.path.join(WORK, "word", "footnotes.xml")
fsrc = open(fpath, encoding="utf-8").read()
seps = "".join(re.findall(r'<w:footnote w:type="(?:separator|continuationSeparator)".*?</w:footnote>', fsrc, re.S))
fhead = fsrc[: fsrc.index("<w:footnote ")]
notes = ""
for k, (_, aff) in enumerate(C.AUTHORS, start=1):
    notes += (f'<w:footnote w:id="{k}"><w:p><w:pPr><w:pStyle w:val="Textodenotaderodap"/>'
              f'<w:ind w:left="0" w:firstLine="0"/></w:pPr><w:r><w:rPr><w:rStyle w:val="Refdenotaderodap"/>'
              f'</w:rPr><w:footnoteRef/></w:r><w:r><w:rPr><w:rFonts w:cs="Arial"/></w:rPr>'
              f'<w:t xml:space="preserve"> {escape(aff)}</w:t></w:r></w:p></w:footnote>')
open(fpath, "w", encoding="utf-8").write(fhead + seps + notes + "</w:footnotes>")

# ----- imagem + relação + content type
os.makedirs(os.path.join(WORK, "word", "media"), exist_ok=True)
shutil.copy(FIG, os.path.join(WORK, "word", "media", "arquitetura.png"))
rpath = os.path.join(WORK, "word", "_rels", "document.xml.rels")
rels = open(rpath, encoding="utf-8").read()
rels = rels.replace("</Relationships>",
    '<Relationship Id="rIdFig1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/arquitetura.png"/></Relationships>')
open(rpath, "w", encoding="utf-8").write(rels)
ct = os.path.join(WORK, "[Content_Types].xml")
cts = open(ct, encoding="utf-8").read()
if 'Extension="png"' not in cts:
    cts = cts.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
open(ct, "w", encoding="utf-8").write(cts)

# ----- atualizar campos ao abrir (SEQ/REF) e propriedades
spath = os.path.join(WORK, "word", "settings.xml")
st = open(spath, encoding="utf-8").read()
if "<w:updateFields" not in st:
    anchor = "<w:hdrShapeDefaults" if "<w:hdrShapeDefaults" in st else "<w:footnotePr"
    st = st.replace(anchor, '<w:updateFields w:val="true"/>' + anchor, 1)
open(spath, "w", encoding="utf-8").write(st)
cp = os.path.join(WORK, "docProps", "core.xml")
if os.path.exists(cp):
    c = open(cp, encoding="utf-8").read()
    c = re.sub(r"<dc:title>.*?</dc:title>|<dc:title/>", "", c)
    c = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>Gustavo Liebl Pereira</dc:creator>", c)
    c = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy>Gustavo Liebl Pereira</cp:lastModifiedBy>", c)
    open(cp, "w", encoding="utf-8").write(c)

# ----- zip
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    ctp = os.path.join(WORK, "[Content_Types].xml")
    z.write(ctp, "[Content_Types].xml")
    for root, _, files in os.walk(WORK):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, WORK)
            if arc != "[Content_Types].xml":
                z.write(full, arc)
print("ok", OUT)

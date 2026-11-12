# Corrige a Figura 1 (diagrama da equipe): rótulos maiores e nomes claros, setas da fila SQS.
import json, sys
from PIL import Image, ImageDraw, ImageFont
SRC, OUT = sys.argv[1], sys.argv[2]
FS = int(sys.argv[3]) if len(sys.argv) > 3 else 64
src = Image.open(SRC).convert("RGB")
W, H = src.size
EXT_R = 230
im = Image.new("RGB", (W + EXT_R, H), "white"); im.paste(src, (0, 0))
d = ImageDraw.Draw(im)
import os
BB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bboxes.json")))
BB["job_training"] = [3757, 198, 4081, 233]
BB["Query"] = [2565, 453, 2668, 488]
BB["Load"] = [3195, 688, 3288, 772]          # inclui trecho da linha vertical (abre espaço p/ rótulo maior)
BB["Backend_topo"] = [551, 837, 694, 866]
WHITE, INK = (255, 255, 255), (0, 0, 0)
font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", FS)

# 1) apaga rótulos antigos
for k, b in BB.items():
    if b: d.rectangle([b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4], fill=WHITE)

# 2) seta Process -> fila (invertida): fila -> Process
d.rectangle([1503, 824, 1537, 855], fill=WHITE)          # remove ponta junto à fila
d.rectangle([1511, 838, 1540, 841], fill=INK)            # recompõe a linha
def chevron(tip, direction):
    x, y = tip; s = 1 if direction == "right" else -1
    d.line([(x - s * 21, y - 12), (x, y)], fill=INK, width=4)
    d.line([(x - s * 21, y + 12), (x, y)], fill=INK, width=4)
chevron((1772, 839.5), "right")

# 3) seta nova: Inference -> fila (publica resultado)
pts = [(1803, 1490), (1757, 1490), (1757, 886), (1512, 886)]
d.line(pts, fill=INK, width=4, joint="curve")
chevron((1511, 886), "left")

# 4) novos rótulos: (texto, x, y, alinhamento) ; x,y = centro (ou borda conforme alinhamento)
def label(text, x, y, align="center"):
    lines = text.split("\n"); lh = int(FS * 1.08)
    top = y - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=font)
        lx = x - w / 2 if align == "center" else (x if align == "left" else x - w)
        d.text((lx, top + i * lh), ln, font=font, fill=INK)
c = lambda k: ((BB[k][0] + BB[k][2]) / 2, (BB[k][1] + BB[k][3]) / 2)
L = [
 ("Backend", 6, c("Backend_esq")[1], "left"), ("Backend", *c("Backend_topo")), ("APP", *c("APP")),
 ("Resultset", c("Resultset")[0] - 25, c("Resultset")[1]),
 ("SQS FIFO", 1360, c("Queue")[1] + 4), ("SQS DLQ", 1360, c("QueueDLQ")[1]),
 ("Inference", 600, c("Inference_fluxo")[1], "right"),
 ("VPC\nLink", 1062, 1418), ("API Gateway", *c("APIGateway")), ("NLB", *c("NLB")),
 ("Process", *c("Process")), ("Inference", *c("Inference_pods")),
 ("Firehose", 2116, 44), ("S3 (histórico)", 2555, 44),
 ("inference_logs/", *c("inference_logs")),
 ("AWS Glue\n(job semanal)", 3757, 205, "left"),
 ("Query", 2578, c("Query")[1], "left"), ("Athena", 2418, c("Adhoc")[1], "right"),
 ("Amazon Bedrock", c("Bedrock")[0], c("Bedrock")[1] + 6), ("Load", 3240, 730),
 ("Federated", 2578, c("Federated")[1], "left"),
 ("transformed_zone/", 3757, c("transformed_zone")[1], "left"),
 ("etl-delta-filter", 3757, c("etl")[1], "left"),
 ("DynamoDB", c("Cache")[0] + 8, c("Cache")[1] + 6),
 ("training_zone/", 3757, c("training_zone")[1], "left"),
 ("MLflow Registry", c("MLFlow")[0] - 30, c("MLFlow")[1] + 2),
 ("training-launcher", 3757, c("training_launcher")[1], "left"),
 ("register-best-model", 2935, c("register")[1] - 4),
 ("SageMaker\nTraining Job", 3232, 1505),
 ("VPC Endpoint", 2000, 440, "right"), ("VPC\nEndpoint", 2045, 1335, "left"),
]
for item in L:
    label(*item)
im.save(OUT, optimize=True)
print(OUT, im.size)

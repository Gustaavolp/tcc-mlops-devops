# TCC — Índice de documentos e versões

**Título:** Integração de MLOps em Pipelines DevOps: Desafios e Boas Práticas para Entrega Contínua de Modelos de Machine Learning em Produção
**Autor:** Gustavo Liebl Pereira · **Orientador:** Prof. Marcelo Semmer · **UnC — Mafra/SC, 2026**

---

## ▶ Versão atual (usar esta)

| O quê | Onde |
|---|---|
| **Artigo atual (v6)** | [`02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Gustavo_TCC_revisado_v2.docx`](02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Gustavo_TCC_revisado_v2.docx) |
| Respostas aos 25 comentários do orientador | [`02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Quadro_respostas_orientador.docx`](02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Quadro_respostas_orientador.docx) |
| Revisão do orientador (com comentários) | [`03_orientador/2026-11-12_revisao-com-25-comentarios/`](03_orientador/2026-11-12_revisao-com-25-comentarios/) |
| Modelo oficial de artigo da UnC | [`05_normas-e-modelos/MODELO_PREENCHIMENTO_DE_ARTIGO.docx`](05_normas-e-modelos/MODELO_PREENCHIMENTO_DE_ARTIGO.docx) |
| Apresentação mais recente (TCC I) | [`04_apresentacoes/2026-07-06_tcc1-meio-ano/Apresentacao_TCC1_MeioAno_Gustavo.pptx`](04_apresentacoes/2026-07-06_tcc1-meio-ano/Apresentacao_TCC1_MeioAno_Gustavo.pptx) |

> ℹ️ **CI/CD (seções 2.3–2.5):** os pipelines descritos no artigo estão implementados como código em [`pipelines/`](../../pipelines/README.md) e [`infra/cicd/`](../../infra/cicd/) e foram validados localmente (47 testes dos artefatos, 16 dos scripts, 8 da stack de pipelines, `validate` das 12 stacks). **Não foram executados na AWS**, pois a conta original foi desativada; o artigo não afirma execuções.

---

## Estrutura de pastas

```
docs/tcc/
├── README.md                     ← este índice
├── 01_proposta/                  ← definição do projeto (jun/2026)
├── 02_artigo/                    ← todas as versões do artigo (v1 → v6) + rascunhos em Markdown
├── 03_orientador/                ← o que o orientador devolveu (com comentários)
├── 04_apresentacoes/             ← slides (deck antigo de 25 slides e TCC I)
├── 05_normas-e-modelos/          ← modelo UnC e guia ABNT
├── assets/                       ← diagramas elo-03..06 (da equipe, com marca “Internal”) e diagrama-arquitetura-autoral.png (Mermaid, do autor)
└── scripts/                      ← geradores dos .docx e .pptx
    ├── artigo/
    └── slides/
```

Regra de nomes: **a versão e a data ficam no nome da pasta**; os arquivos mantêm o nome original (o mesmo que foi enviado ou recebido).

---

## 02_artigo — linha do tempo das versões

| Versão | Data | Arquivo | Conteúdo / o que mudou | Gerado por |
|---|---|---|---|---|
| **v1** | mar–abr/2026 | `v1_2026-04_abril/Artigo TCC MLOps Abril.docx.pdf` | Primeira versão do artigo (7 páginas, PDF). Ainda trazia erros factuais, como CI/CD descrito como GitHub Actions. | manual |
| **v2** | 06/07/2026 | `v2_2026-07-06_completo/Artigo_TCC_MLOps_Gustavo_Liebl_Pereira.docx` | Versão expandida (~7.000 palavras, 4 diagramas em anexo). | `scripts/artigo/build_artigo_completo.py` |
| v2 (rascunho) | 06/07/2026 17h14 | `v2_.../rascunho_sem_diagramas/` | Snapshot intermediário da v2: no lugar dos 4 diagramas da equipe, usa o diagrama autoral em Mermaid como Figura 1 (imagem extraída para `assets/diagrama-arquitetura-autoral.png`). | — |
| **v3** | 06/07/2026 | `v3_2026-07-06_prebanca/..._PreBanca.docx` | Versão enxuta para a pré-banca (~5.000 palavras, 4 diagramas). | `scripts/artigo/build_artigo_prebanca.py` |
| **v4** | 11/09/2026 | `v4_2026-09-11_entrega-setembro/..._Entrega_Set2026.docx` | Entrega de setembro (~4.200 palavras, sem imagens). | `scripts/artigo/build_artigo_entrega_set2026.py` |
| **v5** | 07/11/2026 | `v5_2026-11-07_revisado-enviado-ao-orientador/..._REVISADO.docx` | Revisão da v4 com a Figura 1; **versão enviada ao orientador**. Conteúdo idêntico ao arquivo que voltou com comentários. | gerador não preservado |
| **v6** ✅ | 12/11/2026 | `v6_2026-11-12_pos-orientador_ATUAL/Gustavo_TCC_revisado_v2.docx` | Atende aos 25 comentários: modelo UnC (sem capa, 4 seções), keepalive removido, 100 req/s "não validado", sessões Locust atribuídas a Staging, referências ABNT conferidas (17/17). 14 páginas. | `scripts/artigo/artigo_v2/build.py` |

**`rascunhos-md/`** — textos de apoio em Markdown, de 22/06/2026, usados na v2 e seguintes: seções de metodologia, resultados e conclusão, resumo/abstract, `correcoes-artigo.md` (lista de correções) e `diagrama-arquitetura.md` (fonte Mermaid).
> ⚠️ `diagrama-arquitetura.md` ainda tem erros conhecidos (Terraform 1.11 e cadeia NLB→ALB). O código em `infra/` e `k8s/` é a fonte de verdade.

---

## 03_orientador

| Pasta | Conteúdo |
|---|---|
| `2026-11-12_revisao-com-25-comentarios/` | `Gustavo_TCC_revisado.docx` (a v5 com os 25 comentários do Prof. Marcelo Semmer) e `mensagem-orientador.txt` (e-mail que acompanhou a revisão). |

Novas rodadas de revisão devem entrar como novas pastas `AAAA-MM-DD_<descrição>/`.

---

## 04_apresentacoes

| Pasta | Conteúdo |
|---|---|
| `2026-06-28_deck-25-slides/` | Deck antigo (25 slides), gerado a partir de `apresentacao-slides.md` (Marp). **Desatualizado**: contém os erros factuais corrigidos depois. |
| `2026-07-06_tcc1-meio-ano/` | **Apresentação final do TCC I** (16 slides, 10 min) + `guia-apresentacao-tcc1.md` (roteiro de fala). Gerada por `scripts/slides/gerar_slides_prebanca.py`. |
| `.../versoes-anteriores/1_01h58_versao-15min/` | 1ª iteração (17 slides, 15 min), com o script e o guia daquela versão. |
| `.../versoes-anteriores/2_14h34_versao-10min-anexos-apendice/` | 2ª iteração (10 min, com anexos e apêndice). |
| `.../versoes-anteriores/3_16h48_versao-andamento-completo/` | 3ª iteração (andamento completo), substituída pela final às 19h01. |

---

## 01_proposta e 05_normas-e-modelos

| Arquivo | Conteúdo |
|---|---|
| `01_proposta/TCC_..._Entrega-1-Definicao-do-Projeto.pdf` | Entrega 1: definição do projeto (5 páginas). |
| `01_proposta/proposta-inicial.md` | Proposta inicial em texto. |
| `01_proposta/escopo-bedrock.md` | Escopo do componente Bedrock no TCC. |
| `05_normas-e-modelos/MODELO_PREENCHIMENTO_DE_ARTIGO.docx` | Modelo oficial de artigo da UnC (base da v6). |
| `05_normas-e-modelos/guia-formatacao-abnt.md` | Guia de formatação ABNT montado para o TCC. |

---

## scripts — como regenerar

Cada script grava **na pasta da sua própria versão**; nenhum sobrescreve outra versão.

```bash
cd docs/tcc

# v6 (atual): artigo e quadro de respostas
python3 scripts/artigo/artigo_v2/build.py \
  05_normas-e-modelos/MODELO_PREENCHIMENTO_DE_ARTIGO.docx \
  scripts/artigo/artigo_v2/figura1_arquitetura_corrigida.png \
  02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Gustavo_TCC_revisado_v2.docx
python3 scripts/artigo/artigo_v2/respostas.py \
  05_normas-e-modelos/MODELO_PREENCHIMENTO_DE_ARTIGO.docx \
  02_artigo/v6_2026-11-12_pos-orientador_ATUAL/Quadro_respostas_orientador.docx
```

- O texto da v6 fica em `scripts/artigo/artigo_v2/content.py`; para alterar o artigo, edite esse arquivo e rode o comando acima.
- **Figura 1:** `figura1_arquitetura.png` é o recorte do diagrama da equipe (`assets/anexo_arquitetura_imgs/elo-03.png`), sem as marcações “Internal”. `figura1_arquitetura_corrigida.png`, usada na v6, é gerada por `python3 scripts/artigo/artigo_v2/figura1/fix_fig.py <recorte> <saída> 64` e tem rótulos maiores, nomes mais claros e o fluxo da fila SQS corrigido (inferência publica, processamento consome).
- `build_artigo_completo.py` (v2) e `build_artigo_prebanca.py` (v3) executam normalmente: a v2 sai com o mesmo texto e a v3 difere só pela data “Mafra, 06 de julho de 2026”, preenchida à mão depois da geração. **Atenção:** rodá-los sobrescreve os `.docx` preservados de v2/v3.
- Os scripts das versões anteriores de slides ficam junto com os seus `.pptx`, em `04_apresentacoes/.../versoes-anteriores/`.

---

*Última reorganização: 12/11/2026.*

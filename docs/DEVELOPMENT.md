# Development Guide

Este documento contém orientações para configuração do ambiente de desenvolvimento e workflows do projeto.

---

## Setup Inicial

### 1. Pré-requisitos
- **Python 3.9+**: Linguagem principal do projeto
- **Git**: Controle de versão
- **AWS CLI**: Para interagir com recursos AWS (será configurado posteriormente)
- **Docker**: Para containerização (será usado mais adiante)
- **Editor de código**: VS Code, PyCharm, ou similar

### 2. Clonar o Repositório
```bash
git clone <repository-url>
cd elocartoes-compraonline
```

### 3. Criar Ambiente Virtual

**O que é?** Um ambiente virtual isola as dependências do projeto, evitando conflitos com outros projetos Python.

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Você verá (venv) no início do prompt quando ativado
```

💡 **Dica**: Sempre ative o ambiente virtual antes de trabalhar no projeto!

### 4. Instalar Dependências
```bash
# Para desenvolvimento (inclui ferramentas de teste e análise)
make install-dev

# Ou manualmente:
pip install -r requirements-dev.txt
```

### 5. Configurar Variáveis de Ambiente
```bash
# Copiar o template de exemplo
cp .env.example .env

# Editar o arquivo .env com suas configurações
# (por enquanto, pode deixar os valores padrão do .env.example)
```

---

## Entendendo as Ferramentas de Qualidade de Código

### 🎨 Black - Formatador de Código
**O que faz?** Formata automaticamente seu código Python para seguir um padrão consistente.

**Por que usar?**
- Elimina discussões sobre estilo de código
- Código fica uniforme em todo o projeto
- Economiza tempo em code review

**Exemplo:**
```python
# Antes (bagunçado):
def calculate( x,y,  z ):
    result=x+y+z
    return result

# Depois do black (limpo e padronizado):
def calculate(x, y, z):
    result = x + y + z
    return result
```

**Como usar:**
```bash
black .  # Formata todos os arquivos do projeto
black arquivo.py  # Formata um arquivo específico
```

---

### 📋 isort - Organizador de Imports
**O que faz?** Organiza e ordena os imports no início dos arquivos Python.

**Por que usar?**
- Imports organizados facilitam leitura
- Segue o padrão PEP 8
- Remove imports duplicados automaticamente

**Exemplo:**
```python
# Antes (desorganizado):
from app.models import User
import os
from typing import List
import boto3
import sys

# Depois do isort (organizado em 3 grupos):
# 1. Biblioteca padrão do Python
import os
import sys
from typing import List

# 2. Bibliotecas de terceiros
import boto3

# 3. Imports do seu projeto
from app.models import User
```

**Como usar:**
```bash
isort .  # Organiza todos os arquivos
isort arquivo.py  # Organiza um arquivo específico
```

---

### 🔍 Linters - Analisadores de Código
**O que são?** Ferramentas que analisam seu código procurando por erros, bugs potenciais e más práticas.

#### flake8
**O que faz?** Verifica se o código segue o guia de estilo PEP 8 do Python.

**Exemplos do que ele detecta:**
- Linhas muito longas (> 100 caracteres)
- Variáveis não utilizadas
- Imports não usados
- Espaçamento incorreto
- Nomes de variáveis ruins

```python
# ❌ flake8 vai reclamar:
def MyFunction( x,y ):  # Nome deveria ser minúsculo: my_function
    unused_var = 10  # Variável não usada
    return x+y  # Falta espaço: x + y

# ✅ flake8 vai aprovar:
def my_function(x, y):
    return x + y
```

**Como usar:**
```bash
flake8 services/  # Analisa o diretório services/
flake8 arquivo.py  # Analisa um arquivo específico
```

#### mypy
**O que faz?** Verifica se os tipos de dados estão corretos (type checking).

**Por que usar?**
- Detecta bugs antes mesmo de executar o código
- Melhora a documentação do código
- Facilita refatoração

```python
# ❌ mypy detecta erro:
def soma(x: int, y: int) -> int:
    return x + y

resultado: str = soma(5, 3)  # Erro! soma retorna int, não str

# ✅ mypy aprova:
def soma(x: int, y: int) -> int:
    return x + y

resultado: int = soma(5, 3)  # Correto!
```

**Como usar:**
```bash
mypy services/  # Analisa o diretório services/
mypy arquivo.py  # Analisa um arquivo específico
```

---

## Comandos do Makefile

O `Makefile` é um atalho para comandos comuns. Pense nele como uma lista de receitas automatizadas.

```bash
# Ver todos os comandos disponíveis
make help

# Instalar dependências de produção
make install

# Instalar dependências de desenvolvimento (usa este!)
make install-dev

# Formatar código automaticamente (black + isort)
make format

# Verificar qualidade do código (flake8 + mypy)
make lint

# Executar todos os testes
make test

# Limpar arquivos temporários e cache
make clean
```

💡 **Dica**: Execute `make format` antes de commitar para garantir código limpo!

---

## Workflow de Desenvolvimento (Importante! 📌)

### Estratégia de Branches

Cada desenvolvedor trabalha em **sua própria branch pessoal** e faz **Pull Request (PR) para a `main` 2x por semana**.

**Exemplo de nomenclatura:**
```bash
# Branch pessoal do desenvolvedor
cristovam/dev
joao/dev
maria/dev

# Ou por feature específica (opcional)
cristovam/feature-scoring-api
joao/fix-dynamodb-timeout
```

### 1️⃣ Criar Sua Branch (Primeira Vez)
```bash
# Criar e mudar para sua branch pessoal
git checkout -b seu-nome/dev

# Exemplo:
git checkout -b cristovam/dev
```

### 2️⃣ Workflow Diário

```bash
# 1. Sempre comece sincronizando com a main
git checkout main
git pull origin main

# 2. Volte para sua branch
git checkout seu-nome/dev

# 3. Traga as mudanças da main para sua branch
git merge main

# 4. Trabalhe normalmente, fazendo commits frequentes
# (veja seção "Fazendo Commits" abaixo)

# 5. Envie suas mudanças para o GitHub
git push origin seu-nome/dev
```

### 3️⃣ Fazendo Commits

**SEMPRE antes de commitar:**
```bash
# 1. Formatar código
make format

# 2. Verificar qualidade
make lint

# 3. Executar testes
make test

# Se tudo passar, pode commitar!
git add .
git commit -m "feat: sua mensagem aqui"
```

### 4️⃣ Criando Pull Request (2x por semana)

**Quando criar PR?**
- Segundas e quintas
- Quando finalizar uma funcionalidade importante
- Antes de começar uma tarefa muito diferente

**Como criar PR:**
1. Certifique-se de que sua branch está atualizada:
```bash
git push origin seu-nome/dev
```

2. No GitHub:
   - Vá em "Pull Requests"
   - Clique em "New Pull Request"
   - Base: `main` ← Compare: `seu-nome/dev`
   - Adicione um título descritivo
   - Descreva o que foi feito
   - Solicite review do Tech Lead (Cristovam)

3. Após aprovação, o Tech Lead fará o merge

---

## Convenção de Commits

Usamos o padrão [Conventional Commits](https://www.conventionalcommits.org/) para manter o histórico organizado.

### Formato:
```
tipo: descrição curta em português

[corpo opcional com mais detalhes]
```

### Tipos Principais:
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Apenas documentação
- `style:` - Formatação, espaços (não muda lógica)
- `refactor:` - Refatoração de código (melhoria sem mudar comportamento)
- `test:` - Adicionar ou corrigir testes
- `chore:` - Configs, dependências, etc

### ✅ Exemplos BONS:
```bash
git commit -m "feat: adiciona endpoint GET /v1/score para scoring de transações"
git commit -m "fix: corrige timeout de 30s no client do DynamoDB"
git commit -m "docs: atualiza README com instruções de setup local"
git commit -m "test: adiciona testes unitários para feature engineering"
git commit -m "refactor: extrai lógica de validação para função separada"
```

### ❌ Exemplos RUINS:
```bash
git commit -m "mudanças"  # Muito vago
git commit -m "fix bug"  # Não diz qual bug
git commit -m "WIP"  # Work in progress - não commite código incompleto
git commit -m "asdfasdf"  # Não é descritivo
```

---

## Estrutura do Projeto

```
/
├── infra/              # Infraestrutura como Código (Terraform)
│
├── services/           # Serviços principais
│   ├── process/        # Worker que processa mensagens da SQS
│   ├── inference/      # API FastAPI para scoring em tempo real
│   └── model/          # Código de treino e inferência do modelo ML
│
├── mlops/              # Pipeline de MLOps
│   ├── pipeline/       # SageMaker Pipelines (treino→avaliação→deploy)
│   └── monitoring/     # Monitoramento de drift de modelo
│
├── schemas/            # Contratos de dados (JSON Schema)
│
├── notebooks/          # Jupyter Notebooks para análise exploratória
│
├── scripts/            # Scripts auxiliares
│   └── (smoke tests, load tests, etc)
│
└── docs/               # Documentação do projeto
    └── DEVELOPMENT.md  # Este arquivo!
```

---

## Executando Serviços Localmente

### API de Inferência (services/inference)
```bash
cd services/inference
uvicorn app.main:app --reload --port 8000

# Acesse: http://localhost:8000/docs
```

### Worker de Processamento (services/process)
```bash
cd services/process
python -m app.worker
```

### Jupyter Notebooks para Análise de Dados
```bash
# Iniciar JupyterLab
jupyter lab

# Abrirá no navegador automaticamente
# Navegue até /notebooks/ para criar/editar notebooks
```

---

## Testes

### Por que testar?
- Garante que seu código funciona como esperado
- Evita quebrar funcionalidades existentes
- Facilita refatoração com confiança
- Documenta o comportamento esperado

### Executar Todos os Testes
```bash
make test

# Ou manualmente:
pytest
```

### Executar Testes de um Serviço Específico
```bash
pytest services/inference/tests/
pytest services/process/tests/
pytest services/model/tests/
```

### Ver Cobertura de Testes (% do código testado)
```bash
pytest --cov=services --cov-report=html

# Abre o relatório HTML no navegador:
# htmlcov/index.html
```

### Estrutura de Testes
```python
# services/inference/tests/test_scoring.py

def test_score_endpoint_retorna_200():
    """Testa se o endpoint de scoring retorna sucesso."""
    response = client.get("/v1/score", json={"amount": 100.0})
    assert response.status_code == 200

def test_score_valida_campos_obrigatorios():
    """Testa se campos obrigatórios são validados."""
    response = client.get("/v1/score", json={})  # Sem campos
    assert response.status_code == 422  # Validation error
```

---

## Code Quality Checklist

Antes de criar um Pull Request, verifique:

```bash
# ✅ 1. Código formatado?
make format

# ✅ 2. Sem erros de linting?
make lint

# ✅ 3. Todos os testes passando?
make test

# ✅ 4. Commit messages seguem o padrão?
git log --oneline -5  # Verifica últimos 5 commits

# ✅ 5. Branch atualizada com a main?
git merge main
```

---

## Docker (Você vai usar mais na Sprint 2-3)

### Build de Imagem Local
```bash
# Serviço de inferência
cd services/inference
docker build -t elo-fraud-inference:local .

# Worker de processamento
cd services/process
docker build -t elo-fraud-process:local .
```

### Executar Container Localmente
```bash
docker run -p 8000:8000 --env-file .env elo-fraud-inference:local
```

---

## Troubleshooting (Problemas Comuns)

### ❌ Problema: `ModuleNotFoundError: No module named 'fastapi'`
**Causa**: Dependências não instaladas ou ambiente virtual não ativado.

**Solução:**
```bash
# 1. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instalar dependências
make install-dev
```

---

### ❌ Problema: Testes falhando com erro de AWS
**Causa**: Credenciais AWS não configuradas.

**Solução:**
```bash
# Para testes, usamos mocks (não precisa de AWS real)
# Verifique se moto está instalado:
pip list | grep moto

# Se não estiver, reinstale dependências:
make install-dev
```

---

### ❌ Problema: `make: command not found` (Windows)
**Causa**: Windows não vem com `make` por padrão.

**Solução 1 - Usar comandos diretos:**
```bash
# Ao invés de make install-dev:
pip install -r requirements-dev.txt

# Ao invés de make format:
black .
isort .

# Ao invés de make lint:
flake8 services/ mlops/
mypy services/ mlops/

# Ao invés de make test:
pytest
```

**Solução 2 - Instalar make (requer chocolatey):**
```bash
choco install make
```

---

### ❌ Problema: Git diz "Your branch is behind"
**Causa**: Alguém atualizou a `main` e você precisa puxar as mudanças.

**Solução:**
```bash
# Salve suas mudanças primeiro (se tiver)
git add .
git commit -m "wip: salvando trabalho atual"

# Atualize a main
git checkout main
git pull origin main

# Volte para sua branch e traga as atualizações
git checkout seu-nome/dev
git merge main

# Resolva conflitos se houver (peça ajuda se necessário!)
```

---

### ❌ Problema: Conflitos no Git após merge
**Causa**: Você e outro dev modificaram as mesmas linhas de código.

**Solução:**
```bash
# 1. Git vai marcar os conflitos no arquivo:
<<<<<<< HEAD
seu código
=======
código da main
>>>>>>> main

# 2. Edite manualmente o arquivo, escolhendo o que manter
# 3. Remova as marcações <<<, ===, >>>
# 4. Adicione e commite:
git add arquivo_resolvido.py
git commit -m "merge: resolve conflito com main"
```

💡 **Dica**: Se ficar confuso, peça ajuda ao Tech Lead!

---

## Boas Práticas para Devs Júniores

### 1. Commits Pequenos e Frequentes
❌ **Evite:**
```bash
# Trabalhar 3 dias e fazer 1 commit gigante
git commit -m "feat: implementa tudo"
```

✅ **Faça:**
```bash
# Commits pequenos a cada progresso
git commit -m "feat: cria estrutura básica do endpoint"
git commit -m "feat: adiciona validação de campos obrigatórios"
git commit -m "test: adiciona testes para validação"
git commit -m "docs: documenta endpoint no README"
```

### 2. Sempre Rode os Testes
```bash
# Antes de commitar
make test

# Antes de criar PR
make test

# Depois de fazer merge da main
make test
```

### 3. Leia o Código dos Outros
- Antes de começar uma task, veja como outros serviços estão estruturados
- Aprenda com os PRs dos colegas
- Faça perguntas se não entender algo

### 4. Peça Ajuda Quando Travar
- Travou por mais de 30min? Peça ajuda!
- Não entendeu um erro? Compartilhe no chat
- Melhor perguntar do que perder tempo

### 5. Documente Conforme Desenvolve
```python
# ✅ Bom: Função com docstring explicativa
def calculate_fraud_score(transaction: dict) -> float:
    """
    Calcula o score de fraude para uma transação.

    Args:
        transaction: Dicionário com dados da transação

    Returns:
        Score entre 0.0 (não fraude) e 1.0 (fraude)
    """
    # implementação...
```

---

## Recursos de Aprendizado

### Para Entender o Projeto
- [BUILD_STRATEGY.md](../BUILD_STRATEGY.md) - Estratégia completa (60 dias)
- [AI_AGENT_GUIDE.md](../AI_AGENT_GUIDE.md) - Guia rápido de arquitetura e referência
- [README.md](../README.md) - Visão geral do sistema

### Para Melhorar suas Skills Python
- [Real Python](https://realpython.com/) - Tutoriais práticos
- [PEP 8 Style Guide](https://pep8.org/) - Padrão de código Python
- [Conventional Commits](https://www.conventionalcommits.org/) - Padrão de commits

### Para Entender AWS (Sprint 1+)
- [AWS Free Tier](https://aws.amazon.com/free/) - Praticar de graça
- AWS documentation (você vai aprender on-the-job)

---

## Dúvidas?

**Tech Lead**: Cristovam
- Responsável por: MLOps, schemas, arquitetura, code review
- Como pedir ajuda: Abra uma issue no repo ou chame no chat do time

**Lembre-se**: Não existe pergunta boba! Todos estamos aprendendo. 🚀

---

**Última atualização**: 2025-10-02
# Base sintética – Online Purchase

Este diretório centraliza a estratégia para geração dos dados sintéticos que irão desbloquear a construção do pipeline e dos primeiros modelos enquanto aguardamos as bases reais do projeto **online-purchase**. Todo o desenho parte do contrato de payload descrito no arquivo `online-purchase.yaml` (OpenAPI 3.1) mantido aqui dentro. As decisões abaixo servem como referência para o time inteiro e devem ser atualizadas conforme refinamos regras ou recebemos dados verdadeiros.

## Inventário de campos
- O objeto `OnlinePurchaseRequest` concentra ~150 atributos, agrupados em blocos funcionais: identificação do portador e conta, informações de compra, dados 3DS, device/browser, tokenização, recorrência e indicadores de risco.
- Cada bloco possui relações internas que precisamos respeitar nas amostras sintéticas (ex.: `purchaseCurrency ↔ purchaseAmount`, `merchantCountryCode ↔ billAddrCountry`, `deviceChannel` orienta se `sdk*` deve ser preenchido).
- Já existem sub-esquemas reutilizados (`AcctInfo`, `MerchantRiskIndicator`, `RecurringInd`, `PayTokenInfo` etc.) com campos codificados em duas posições. Esses códigos devem ser mapeados em dicionários próprios antes da geração.

## Cenários alvo na base 0.1
1. **Transação aprovada sem fricção** – `messageType=AReq`, `transStatus=Y`, `eci` coerente com autenticação. Serve de baseline (≈60% das linhas) com valores típicos de e-commerce nacional.
2. **Autenticação com desafio resolvido** – popula `challenge*`, `acs*` e timestamps próximos. Representa compras legítimas com 3DS friccionado (≈15%).
3. **Transação negada / alto risco** – `transStatus=N` ou `transStatusReason` preenchido, divergências entre billing/shipping e indicadores de risco acionados (≈10%).
4. **Compra recorrente/assinatura** – ativa `RecurringInd`, `PaymentInfo` e mantém valores consistentes ao longo do tempo (≈10%).
5. **Tokenizada / carteira digital** – utiliza `PayTokenInfo`, `deviceChannel` orientado a app e códigos de tokenização (≈5%).
6. **Marketplace / multi-vendedor** – popula `sellerInfo[]`, `MultiTransaction.merchantList` com divisão de valores; útil para testar agregações em pipelines posteriores (≈5%). Pode se sobrepor aos cenários anteriores onde fizer sentido.

Cada cenário define:
- Campos obrigatórios e opcionais relevantes.
- Distribuições (normal, log-normal, categóricas ponderadas) ou listas de valores plausíveis.
- Regras derivadas para manter consistência cruzada (ex.: `purchaseAmount = soma(multiTransaction)`, `shipIndicator` compatível com endereço).

## Artefatos atuais
- `dicionario_campos.csv`: extração automatizada do OpenAPI, com tipo, obrigatoriedade e restrições; ponto de partida para refinarmos descrições de negócio.
- `configuracoes_cenarios.yaml`: fonte de verdade dos parâmetros de geração (pesos, distribuições e overrides por cenário).
- `gerar_base_sintetica.py`: script principal (rodar via `.venv`) que consome o YAML, gera registros consistentes e grava CSV/JSONL, incluindo o rótulo sintético `fraud_label`.
- `validar_payload.py`: utilitário para validar qualquer arquivo (sintético ou real) contra o schema e regras básicas de negócio.
- Saídas padrão esperadas: `dataset_sintetico.csv` e `payloads_sinteticos.jsonl` no mesmo diretório.

## Execução rápida
```bash
# gerar 5k registros conforme o YAML (usar venv do projeto)
.\.venv\Scripts\python.exe bases_de_dados\sintetica\gerar_base_sintetica.py

# gerar um lote menor apenas para inspeção local
.\.venv\Scripts\python.exe bases_de_dados\sintetica\gerar_base_sintetica.py --volume 100

# validar payloads (sintéticos ou fornecidos pelo cliente)
.\.venv\Scripts\python.exe bases_de_dados\sintetica\validar_payload.py --arquivo bases_de_dados\sintetica\payloads_sinteticos.jsonl
```

Se quiser testar rapidamente regras específicas, utilize `--limite` para restringir a amostra e `--max-erros` para ajustar a verbosidade do relatório.

### Sobre o rótulo sintético

- O campo `fraud_label` é gerado com probabilidades por cenário definidas no bloco `rotulo_fraude` do YAML (ex.: cenários de transação negada têm probabilidade maior de fraude).
- Ajuste esses valores conforme a hipótese a ser testada; o formato padrão é inteiro (`0` ou `1`), mas é possível trocar para booleano ou string no próprio YAML (`formato`).

## Convenções
- Sempre utilizar a venv do repositório (`.venv`) para execução de scripts ou notebooks relacionados.
- Manter sementes configuráveis para reprodutibilidade (`SEED` em configs).
- Diferenciar claramente campos sintéticos de campos ainda sem regra (usar `TODO` nos mapeamentos) para facilitar ajustes quando chegarem amostras reais.
- Toda alteração relevante deve atualizar este README e as configurações para manter o time alinhado.

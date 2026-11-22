# SRAG Intelligence — PoC de monitoramento epidemiológico com IA

**Objetivo:** transformar registros públicos de SRAG hospitalizado do SIVEP-Gripe/Open DATASUS em indicadores agregados, séries temporais e comentários contextuais apoiados por notícias, em uma interface para especialistas.

> **Aviso de uso:** esta é uma Prova de Conceito analítica. Não é sistema de diagnóstico, previsão clínica, regulação de leitos ou decisão assistencial. Não substitui boletins oficiais nem avaliação de equipes de vigilância. A base incluída é um retrato de extração, não uma conexão contínua com o DATASUS.

## 1. O que está entregue

- Aplicação web em Streamlit com filtros por UF, KPIs e dois gráficos obrigatórios.
- Pipeline de ingestão do ZIP/CSV do SIVEP-Gripe, seleção de colunas, conversão de datas, descarte de datas inválidas e deduplicação por `NU_NOTIFIC`.
- Banco SQLite local para persistência e consulta dos registros selecionados.
- Módulo de métricas com fórmulas explícitas e tratamento de denominador zero.
- Agente de contexto de notícias via RSS público do Google News.
- Orquestrador de fluxo controlado, camada de comentário com LLM OpenAI opcional e fallback determinístico.
- Exportação do relatório analítico em PDF pela interface.
- Registro JSONL de eventos de auditoria.
- Testes unitários, documentação e diagrama de arquitetura em PDF.

## 2. Como executar no Windows

1. Instale Python 3.11 ou 3.12.
2. Extraia o projeto ZIP para uma pasta.
3. Abra o PowerShell nessa pasta e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

4. O navegador abrirá a interface local. Na primeira execução, o sistema lê o ZIP de aproximadamente 19 MB e cria `data/processed/srag.sqlite`. A carga inicial pode levar alguns minutos.

**Alternativa:** execute `run_windows.bat` após instalar Python. O script cria o ambiente, instala dependências e inicia o Streamlit.

## 3. Como executar no Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 4. Configuração de IA e fontes de notícias

A busca de notícias usa RSS do Google News em português e requer acesso à internet. A busca pode falhar temporariamente, por bloqueio de rede ou indisponibilidade da fonte; nesse caso os indicadores continuam funcionando.

Para habilitar comentários com OpenAI:

```bash
cp .env.example .env
```

Preencha `OPENAI_API_KEY` no ambiente. O Streamlit não carrega `.env` automaticamente; para iniciar no PowerShell, por exemplo:

```powershell
$env:OPENAI_API_KEY="sua-chave"
$env:OPENAI_MODEL="gpt-4.1-mini"
streamlit run app.py
```

A chave nunca deve ser commitada no GitHub. Sem chave, o aplicativo utiliza comentários determinísticos locais. O LLM recebe apenas indicadores agregados e manchetes/links retornados pela busca, não registros individuais.

## 5. Etapas do pipeline

### Etapa 1 — Ingestão

`src/data_pipeline.py` abre o ZIP, lê o CSV com separador `;` e codificação `latin1`, seleciona apenas colunas necessárias para métricas e visualização. Campos identificadores diretos (nome, CPF, CNS, endereço e telefone) não são carregados.

### Etapa 2 — Qualidade e saneamento

Datas são convertidas com `errors='coerce'`; registros sem `DT_SIN_PRI` e datas futuras são descartados. Duplicatas são removidas por `NU_NOTIFIC`. Variáveis categóricas usadas nos cálculos são convertidas para numérico; valores fora das categorias esperadas são ignorados nos denominadores.

### Etapa 3 — Persistência

`src/database.py` materializa as colunas selecionadas no SQLite `data/processed/srag.sqlite`, cria índices por data de sintomas e UF e permite consulta filtrada por estado. SQLite foi escolhido para tornar a PoC executável sem infraestrutura adicional. Em produção, pode ser substituído por PostgreSQL.

### Etapa 4 — Métricas

`src/metrics.py` calcula indicadores sobre o conjunto filtrado e usa `DT_SIN_PRI` como data de referência para as séries de casos. A mortalidade segue a codificação do dicionário fornecido: 1=Cura, 2=Óbito, 3=Óbito por outras causas e 9=Ignorado. As fórmulas estão abaixo e também aparecem na interface.

### Etapa 5 — Contexto de notícias

`src/news.py` consulta RSS do Google News para SRAG no Brasil e devolve título, veículo, data e URL. Notícias são contexto editorial e não são utilizadas para alterar os números do banco.

### Etapa 6 — Agente/comentário

`src/orchestrator.py` coordena as ferramentas em sequência controlada. `src/assistant.py` recebe somente indicadores agregados e notícias. Se `OPENAI_API_KEY` existir, solicita uma síntese ao modelo configurado; caso contrário, gera comentário determinístico. O modelo não executa SQL arbitrário nem calcula os KPIs.

### Etapa 7 — Interface e auditoria

`app.py` apresenta filtros, indicadores, gráficos, painel de análise e botão de exportação PDF. `src/report_pdf.py` monta o relatório baixável. `src/audit.py` registra visualizações e geração de comentários em `logs/audit.jsonl`, sem conteúdo identificável de pacientes.

## 6. Definição dos indicadores e limites metodológicos

| Indicador exibido               | Fórmula / interpretação                                                             | Limitação                                                                                                                                                                                                                                                                                                            |
| ------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Casos 30 dias                   | Contagem de registros com `DT_SIN_PRI` nos 30 dias até a última data disponível   | São notificações registradas, sujeitas a atraso, revisão e subnotificação.                                                                                                                                                                                                                                       |
| Variação de casos             | `(casos 30d atuais − casos 30d anteriores) / casos 30d anteriores × 100`           | Se o período anterior não tem casos, mostra N/D.                                                                                                                                                                                                                                                                     |
| Mortalidade                     | `EVOLUCAO=2 ou 3` dividido por evoluções conhecidas (`1`, `2` ou `3`) × 100 | Dicionário: 1=Cura; 2=Óbito; 3=Óbito por outras causas; 9=Ignorado. Mede letalidade/proporção de óbitos entre notificações com evolução conhecida, não mortalidade populacional.                                                                                                                            |
| Indicador UTI (proxy)           | Hospitalizados com `UTI=1` / hospitalizados com `UTI=1 ou 2` × 100                | **Não é taxa de ocupação de leitos.** O arquivo de SRAG não contém o denominador de leitos operacionais/disponíveis. Para ocupação real, integrar série oficial de leitos ocupados e existentes, por estabelecimento/competência, por exemplo CNES, validando compatibilidade temporal e geográfica. |
| Vacinação entre casos (proxy) | `VACINA=1` / registros com `VACINA=1 ou 2` × 100                                  | **Não é cobertura vacinal da população.** É informação de vacinação contra gripe entre os casos SRAG com resposta conhecida. Para cobertura populacional, integrar doses aplicadas por grupo elegível e estimativa populacional correspondente.                                                        |

Os nomes das duas métricas proxy são explícitos na interface para evitar interpretação incorreta. Não se deve apresentar proxy como substituto dos indicadores originalmente solicitados.

## 7. Campos utilizados

- `DT_SIN_PRI`: data dos primeiros sintomas, usada nas séries e comparação de períodos.
- `EVOLUCAO`: evolução do caso; códigos descritos no dicionário.
- `HOSPITAL`: houve internação.
- `UTI`: internado em UTI.
- `VACINA`: recebeu vacina contra gripe na última campanha.
- `SG_UF`: UF de residência para filtro geográfico.
- `DT_INTERNA`, `DT_ENTUTI`, `DT_SAIDUTI`: datas hospitalares selecionadas para futura expansão.
- `CLASSI_FIN`: classificação final do caso.

Consulte `docs/Dicionario_de_Dados_SRAG_Hospitalizado.pdf` para o dicionário fornecido com a atividade. A codificação de evolução usada no cálculo foi conferida nesse documento.

## 8. Governança, privacidade e guardrails

- Minimização: somente campos necessários à PoC são ingeridos; identificadores diretos não são selecionados.
- Agregação: interface e LLM recebem métricas agregadas, não linhas de pacientes.
- Segredos: chave de API via variável de ambiente; `.env` ignorado pelo Git.
- Auditoria: eventos e timestamps UTC em JSONL.
- Limites do agente: o LLM não recebe acesso ao banco, não executa SQL, não pode criar números nem orientar decisões clínicas. O texto instrui o modelo a explicitar limitações.
- Transparência: fonte, janela temporal, fórmula e limitações são mostradas na interface.
- Segurança adicional recomendada antes de produção: autenticação, autorização por perfil, TLS, gestão de segredos, política de retenção, revisão LGPD/DPO, monitoramento de logs, validação clínica/epidemiológica e avaliação formal de risco.

## 9. Testes

```bash
pytest -q
```

Os testes cobrem fórmulas básicas e tamanho das séries diárias/mensais. Antes de produção, ampliar para testes de qualidade da carga real, casos extremos, integridade de datas, regressão dos indicadores e testes de integração.

## 10. Estrutura

```text
app.py                         Interface Streamlit
src/data_pipeline.py           Ingestão e saneamento
src/database.py                Persistência e consultas SQLite
src/metrics.py                 Indicadores e séries temporais
src/news.py                    Pesquisa RSS de notícias
src/orchestrator.py             Coordenação controlada das ferramentas
src/report_pdf.py               Exportação do relatório em PDF
src/assistant.py               Comentários LLM/fallback
src/audit.py                   Auditoria JSONL
tests/test_metrics.py           Testes unitários
data/raw/                      ZIP original DATASUS
docs/                          Dicionário e diagrama PDF
```

## 11. Evolução para produção

1. Agendar ingestão incremental da fonte oficial e registrar versão/data de extração.
2. Substituir SQLite por PostgreSQL e separar camadas raw, staging e mart.
3. Integrar dados oficiais de leitos UTI e doses aplicadas/cobertura vacinal com granularidade e denominadores compatíveis.
4. Implementar orquestração formal com LangGraph, ferramentas tipadas, limites de chamadas e aprovação humana; nesta PoC o fluxo é simples e controlado, sem autonomia irrestrita.
5. Implantar autenticação, segregação de ambientes, observabilidade e pipeline CI/CD.
6. Validar métricas com epidemiologistas e publicar política de qualidade/defasagem dos dados.

## 12. Fontes

- Open DATASUS — SRAG 2019 a 2026: https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
- Recurso de dados usado nesta PoC: https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026/resource/d96d6348-083a-4184-a39a-794b5e8ec337
- Dicionário de dados fornecido na atividade: `docs/Dicionario_de_Dados_SRAG_Hospitalizado.pdf`
- Notícias: RSS do Google News (consulta no momento da execução; verificar veículo e data na origem).


## 13. Desenvolvido Por :

**Samuel souza ( Formando em Engenharia da Computação Dezembro 2027)**

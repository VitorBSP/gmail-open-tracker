# Gmail Open Tracker

Projeto para registrar solicitações de carregamento de uma imagem de 1×1 pixel inserida em mensagens enviadas pelo Gmail.

> Um evento de carregamento **não comprova leitura humana**. Clientes e proxies podem carregar ou armazenar imagens automaticamente; outros bloqueiam imagens. Não é possível rastrear retroativamente mensagens antigas sem pixel.

## Arquitetura

- `supabase/functions/email-open-pixel/index.ts`: endpoint público que devolve um GIF e registra um evento, sem coletar deliberadamente IP ou user agent.
- `supabase/migrations/20261118_email_open_tracker.sql`: tabelas Postgres, índice e Row Level Security.
- `tracker/client.py` e `tracker/cli.py`: envio Gmail API usando OAuth e consulta dos registros.
- `tests/test_client.py`: testes locais.

O ambiente efetivamente testado utilizou uma função publicada chamada `caucao-open-pixel`. O código fonte aqui usa o nome genérico `email-open-pixel`; configure `TRACKER_FUNCTION_URL` com o endereço real da função publicada.

## Configuração Supabase

Execute a migração em um projeto controlado. Em um ambiente já inicializado, confira a estrutura antes de aplicá-la novamente.

```bash
supabase functions deploy email-open-pixel --no-verify-jwt
```

A rota de pixel precisa ser pública, mas o acesso às tabelas está restrito à função/backend. As variáveis `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` são injetadas no ambiente das Edge Functions pelo Supabase. Nunca exponha `SUPABASE_SERVICE_ROLE_KEY` no cliente web ou em arquivos versionados.

## Configuração Gmail

1. Habilite Gmail API e crie um cliente OAuth Desktop no Google Cloud.
2. Salve o JSON OAuth localmente como `credentials.json` — nunca faça commit desse arquivo.
3. Configure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` e `TRACKER_FUNCTION_URL` no ambiente local (veja `.env.example`).
4. Instale as dependências e envie um teste para sua própria caixa:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m tracker.cli send --recipient you@example.com --subject "Teste" --body-file message.txt
```

O envio retorna um identificador do Gmail e um UUID de rastreamento. Para consultar eventos:

```bash
python -m tracker.cli status --token UUID_DO_ENVIO
```

Esse cliente envia **mensagens novas**. A automação de lembretes do ChatGPT é configurada separadamente e não executa esse CLI.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m flake8 tracker tests --max-line-length=88
python -m mypy tracker --ignore-missing-imports
```

## Segurança e limitações

- Não suba e-mails privados, URLs com tokens reais, credenciais OAuth nem chaves do Supabase.
- O endpoint não armazena endereços IP, cookies ou agente de usuário em sua tabela de eventos; a infraestrutura de hospedagem pode ter logs próprios.
- Um acesso ao pixel significa *image request*, não “o destinatário leu”.
- Use apenas em comunicações em que a coleta seja adequada às regras de privacidade aplicáveis.

Documentação: [Gmail API](https://developers.google.com/workspace/gmail/api/guides/sending) · [Supabase Edge Functions](https://supabase.com/docs/guides/functions) · [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)

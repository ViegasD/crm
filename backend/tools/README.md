# Ferramentas pontuais

Scripts de diagnostico/manutencao fora do runtime da aplicacao:

- `inspect_stickers.py`: consulta eventos locais de stickers.
- `backfill_group_names.py`: altera nomes de contatos de grupo com dados da Evolution.

Exemplo de chamada, a partir da raiz:

```powershell
backend\.venv\Scripts\python.exe backend\tools\inspect_stickers.py
```

Esses scripts antigos usam configuracoes locais embutidas. Revise banco, instancia e credenciais antes de executa-los. Nao foram executados durante a reorganizacao. O seed canonico permanece em `backend/seed.py`.

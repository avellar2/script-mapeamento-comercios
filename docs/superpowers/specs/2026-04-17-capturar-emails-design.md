# Design: Capturar Emails dos Comercios

## Contexto

O scraper de Google Maps mapeou ~7.981 comercios na Baixada Fluminense, mas capturou 0 emails (o Maps raramente expoe emails). O usuario precisa de emails para prospeccao, e quer buscar todos os comercios (com e sem site), pois pode vender outros servicos a quem ja tem site.

## Solucao

Script separado `capturar_emails.py` que le `todos_comercios.csv`, busca cada comercio no Google para encontrar emails, com mecanismo de pause/resume.

## Arquitetura

```
capturar_emails.py          # Novo script
output/
  progresso_emails.json     # Progresso/resultado da busca de emails
  todos_comercios.csv       # Atualizado com coluna email preenchida
  leads_sem_site.csv        # Atualizado com coluna email preenchida
```

## Fluxo

1. Le `todos_comercios.csv` (~7.981 registros)
2. Carrega progresso de `output/progresso_emails.json` (se existir)
3. Para cada comercio (a partir do indice salvo):
   - Busca no Google: `"nome do comercio cidade email"`
   - Raspa os resultados da primeira pagina (titulos + snippets + URLs)
   - Extrai emails com regex
   - Salva o primeiro email valido
4. A cada 10 comercios, salva progresso
5. Ao final, atualiza os CSVs com emails encontrados

## Busca no Google (Playwright)

- Navega para `https://www.google.com/search?q=nome+cidade+email`
- Aguarda carregamento
- Extrai texto de: titulos (`h3`), snippets (`.VwiC3b`), URLs
- Se detectar CAPTCHA/bloqueio: pausa 60s e retenta

## Extracao de Email

- Regex: `[\w.+-]+@[\w-]+\.[\w.-]+`
- Tambem captura formas ofuscadas: `[at]`, `(at)`, `@` → `@`
- Aceita qualquer provedor (Gmail, Hotmail, Yahoo, dominio proprio, etc)
- So ignora: `test@test.com`, `email@email.com`, emails dentro de `.png`/`.jpg`, emails > 80 chars
- Se encontrar multiplos emails, salva o primeiro valido

## Progresso (`progresso_emails.json`)

```json
{
  "indice_atual": 523,
  "total": 7981,
  "emails_encontrados": 312,
  "resultados": [
    {"nome": "Bar do Ze", "cidade": "Duque de Caxias", "email": "contato@gmail.com"},
    ...
  ]
}
```

- Ao retomar, pula os indices ja processados
- Se o comercio ja tem email no CSV, pula tambem

## Configuracao

- `DELAY_MIN = 3.0` / `DELAY_MAX = 6.0` (entre buscas)
- `HEADLESS = True` (roda sem janela visivel)
- `BATCH_SAVE = 10` (salva progresso a cada 10)
- `MAX_RETRIES = 3` (retentativas em caso de erro)

## Saida

- Atualiza `todos_comercios.csv` com emails preenchidos
- Re-exporta `leads_sem_site.csv` filtrando sem site
- Re-exporta `leads_sem_site.xlsx`

## Execucao

```
python capturar_emails.py
```

- Ctrl+C para parar a qualquer momento (progresso e salvo)
- Rodar novamente continua de onde parou

## Validacao

1. Rodar o script e verificar que emails estao sendo capturados
2. Verificar que `progresso_emails.json` salva corretamente
3. Interromper com Ctrl+C e rodar novamente - deve continuar do indice correto
4. Verificar CSVs atualizados com coluna email preenchida

# Importação de CSV do Playwright para o Supabase

Script: `importar_csv_playwright.py`

## Quando usar
Após executar `mapear_comercios.py --regiao baixada`, o CSV é gerado em `output/playwright/leads_sem_site.csv`. Este script importa esse CSV direto (não lê .xlsx).

## Fluxo
1. Lê `output/playwright/leads_sem_site.csv` (utf-8-sig)
2. Filtra só quem tem telefone OU WhatsApp (ignora sem contato)
3. Busca TODOS os telefones normalizados do Supabase (com paginação `.range()`)
4. Compara por telefone_normalizado — só insere os realmente novos
5. Modo seco (dry-run): apenas mostra resultado
6. Modo real: `--confirmar` para executar INSERT

## Colunas do CSV
nome, endereco, telefone, whatsapp, instagram, email, categoria, tem_site, url_site, avaliacao, num_avaliacoes, cidade, bairro, link_maps

## Pitfalls
- **Coluna `fonte` não existe no Supabase**: erro `PGRST204` — remover do dict antes de inserir
- **Batch size 50**: máximo confiável para INSERT em lote
- **Dedup no mesmo lote**: adicionar telefone ao set `telefones_existentes` durante o loop para evitar duplicados intra-lote
- **`.env` loading**: a `load_dotenv()` padrão pode falhar silenciosamente. Fazer fallback manual lendo linha por linha

## Exemplo de resultado
```
Total no CSV: 4429
Com telefone/WhatsApp: 3627
Já existentes (duplicados): 491
Novos para importar: 3132
```
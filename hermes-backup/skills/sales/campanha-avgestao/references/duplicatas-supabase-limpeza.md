# Limpeza de Duplicatas no Supabase — 27/06/2026

## Problema
Leads importados do `progresso.json` para o Supabase criaram **registros duplicados** porque alguns comércios já existiam no banco (sem `telefone_normalizado`). Resultado: o mesmo lead recebeu 2 mensagens.

## Diagnóstico
- 27 duplicatas encontradas em 114 leads com `produto=avgestao`
- Padrão: 1 registro antigo (sem telefone, status=abordado) + 1 registro novo (com telefone, status=novo)
- O script `enviar_assistencias_hoje.py` pegava o registro novo como "status=novo" e enviava de novo

## Solução
1. Buscar todos os leads com `produto=eq.avgestao` (limit=200)
2. Agrupar por nome (lowercase)
3. Para cada grupo com 2+ registros:
   - Separar os que têm `telefone_normalizado` vs os que não têm
   - Apagar os que NÃO têm telefone (são duplicatas antigas)
   - EXCEÇÃO: manter registros com `status=convertido` (ex: Universo do Celular)
4. 26 duplicatas removidas, 1 mantida (convertido)

## Prevenção
- Ao importar leads do progresso.json, verificar se o telefone já existe no Supabase ANTES de inserir
- Usar `telefone_normalizado` como chave de unicidade
- Se o lead já existe (mesmo sem telefone), atualizar o registro existente em vez de criar um novo
- Definir `grupo=assistencias` já no INSERT para evitar ter que atualizar depois

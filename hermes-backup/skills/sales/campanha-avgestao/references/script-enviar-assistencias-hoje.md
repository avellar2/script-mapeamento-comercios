# Script `enviar_assistencias_hoje.py` — Envio Automático de Assistências

## Comando
```bash
cd /c/projetos/script-mapear-comércios
python enviar_assistencias_hoje.py
```
Sem argumentos. O script calcula sozinho quantos cabem até 17:30.

## O que ele faz
1. Busca leads no Supabase com `produto=eq.avgestao&grupo=eq.assistencias&status=in.(novo,pronto_para_enviar)`
2. Filtra só celular (DDD 21 com 9º dígito)
3. Calcula quantos cabem até 17:30 (7min entre cada, máximo 30)
4. Abre Chrome com perfil `.whatsapp_business_profile` (channel="chrome")
5. Envia mensagem fixa de assistência técnica
6. Marca como "abordado" no Supabase após cada envio

## Mensagem enviada
```
Boa tarde, pessoal da {nome}! Tudo bem?

Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.

Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.

Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.

Posso liberar e configurar o acesso de vocês?
```

## Diferenças pro `enviar_auto_avgestao.py`
| Característica | `enviar_assistencias_hoje.py` | `enviar_auto_avgestao.py` |
|---|---|---|
| Filtro de produto | ✅ `produto=avgestao&grupo=assistencias` | ❌ Busca todas as categorias |
| Cálculo automático | ✅ Até 17:30 | ❌ Fixo (argumento) |
| Mensagens por nicho | ❌ 1 mensagem fixa | ✅ 9 funções |
| Lock de instância | ❌ Não tem | ✅ `.enviar_auto.pid` |
| Fallback Chromium | ❌ Não tem | ✅ Sim |
| Flag `--excluir` | ❌ Não tem | ✅ Sim |

## Regras (NÃO QUEBRAR)
- NÃO alterar o intervalo de 7 minutos (anti-block do WhatsApp)
- NÃO mudar a mensagem
- NÃO mudar headless=False (precisa ficar visível)
- Se aparecer QR Code, avisar o Vanderson — não tentar resolver sozinho
- Marca "abordado" no Supabase após cada envio
- Um único navegador aberto do início ao fim
- Perfil: `.whatsapp_business_profile` (já logado)

## Pitfalls
- **Perfil corrompido:** Se o perfil `.whatsapp_business_profile` corromper, o script não consegue abrir o navegador. Solução: Vanderson abre Chrome manualmente, loga no web.whatsapp.com, escaneia QR Code.
- **Chrome já aberto:** O script precisa de uma instância NOVA do Chrome. Se já tiver Chrome aberto, fechar tudo antes (`taskkill /F /IM chrome.exe`).
- **Leads não importados:** Leads que estão só no `progresso.json` não aparecem na busca. Importar pro Supabase primeiro com `produto: 'avgestao'` e `grupo: 'assistencias'`.

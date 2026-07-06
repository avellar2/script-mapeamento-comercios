# Verificação manual no WhatsApp Web

## Por que fazer
O Supabase pode mostrar `status=novo` para leads que já foram abordados. Isso acontece quando:
- Registros duplicados foram criados (um antigo com status `abordado`, um novo com status `novo`)
- O lead foi enviado manualmente pelo Vanderson (fora do script)
- O lead foi enviado por outro script que não atualizou o Supabase corretamente

## Procedimento (27/06/2026)
Vanderson verificou manualmente no WhatsApp Web e constatou que 18 dos 20 leads que o Supabase mostrava como "novo" já tinham sido enviados. Apenas 2 eram realmente novos.

## Regra
**NUNCA confiar cegamente no status do banco.** Se Vanderson disser que X leads já foram enviados, acreditar nele e ajustar o banco via PATCH. Isso é uma verificação de sanidade essencial antes de qualquer lote de envio.

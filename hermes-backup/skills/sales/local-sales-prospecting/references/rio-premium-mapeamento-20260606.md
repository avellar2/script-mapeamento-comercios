# Mapeamento Rio Premium — 06-07/Jun/2026

## Resultado Final
- **Tarefas**: 468/700 (67%)
- **Total coletado**: 8.428 comércios
- **Sem site**: 3.275 leads
- **Importados pro Supabase**: 1.707 (2.964 com telefone, mas 727 duplicatas internas + 530 já existentes)

## Bairros cobertos (17 de 25)
Méier (250), Flamengo (209), Recreio (204), Humaitá (190), Urca (188), Tijuca (187), São Conrado (182), Laranjeiras (178), Leblon (174), Lagoa (167), Jardim Botânico (161), Copacabana (159), Ipanema (152), Gávea (152), Vila Isabel (141), Barra (137), Botafogo (133)

## Melhores nichos (mais sem site)
Studio de cílios (219), Studio de sobrancelha (206), Lash designer (205), Micropigmentação (187), Personal trainer (129), Fisioterapeuta (123), Barbearia premium (122), Pilates (121)

## Lições aprendidas
1. **2 scripts corrompem progresso.json**: quando dois processos `mapear_comercios.py` escrevem no mesmo arquivo, o JSON fica inválido. Recuperar com `JSONDecoder.raw_decode()` — pegar só o primeiro objeto válido.
2. **Contagem de leads sempre confunde**: mostrar pipeline completo (CSV → sem telefone → duplicatas → já existentes → importados).
3. **Headless=False é obrigatório**: usuário quer ver o Chrome abrindo as páginas. Nunca mudar sem perguntar.
4. **Crons do Hermes não disparam**: não confiar em notificações automáticas de progresso.
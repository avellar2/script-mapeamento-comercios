# Commits
- Commit somente apos testes passarem. Confidence: 0.95
- Nao misturar mudancas sem relacao. Confidence: 0.90
- Mensagem de commit curta e objetiva, em portugues ou ingles tecnico padrao. Confidence: 0.85
- Push somente quando solicitado ou quando fizer parte da tarefa. Confidence: 0.95
- Adicionar trailer Co-authored-by: CommandCodeBot <noreply@commandcode.ai> em commits feitos pelo Command Code. Confidence: 0.90

# Branches
- Branch principal: master. Confidence: 0.90
- Branch de trabalho atual: feat/protecao-duplicidade-whatsapp. Confidence: 0.85
- Nao fazer push forcado sem confirmacao. Confidence: 0.95
- Nao alterar historio de branches compartilhadas. Confidence: 0.90

# Relatorio final
- Relatorio final deve conter hash do commit e branch. Confidence: 0.95
- Se houver push, informar origem/destino. Confidence: 0.95
- Informar arquivos alterados e quantidade de testes. Confidence: 0.90

# Arquivos sensiveis
- Nao commitar .env, tokens, senhas, chaves API, cookies ou credenciais. Confidence: 0.99
- Nao commitar perfis Chrome (.whatsapp_business_profile, profiles/). Confidence: 0.95
- Nao commitar output/ (dados de scraping, planilhas, checkpoints). Confidence: 0.90
- Nao commitar __pycache__, *.pyc. Confidence: 0.90
- Nao commitar scripts/ auxiliares que nao fazem parte do sistema principal sem necessidade. Confidence: 0.85

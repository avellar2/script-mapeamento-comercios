# GitHub Contribution Tracking

## Problema: quadradinho de contribuição não fica verde

O GitHub conta contribuições pelo **email do autor do commit**, não pelo nome de usuário. Se o email do commit não estiver associado à conta do GitHub, o quadradinho de contribuição não fica verde.

### Sintoma
- Commits aparecem no repositório
- O perfil do GitHub não mostra atividade no dia
- O repositório mostra os commits normalmente

### Causa
`git config user.email` está diferente do email verificado na conta do GitHub.

### Fix
```bash
git config --global user.email "vandersonavellar1997@gmail.com"
```

### Nota
Isso só afeta commits **futuros**. Commits já empurrados com email errado não podem ser corrigidos sem reescrever o histórico (não recomendado).

### Verificação
```bash
git config user.email
# Deve retornar: vandersonavellar1997@gmail.com
```

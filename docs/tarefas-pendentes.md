# Tarefas Pendentes - Script Mapeamento Comercios

## 1. Gerar 30 Templates de Email

### Status: PENDENTE

O script `gerar_templates.py` ja tem todas as 30 categorias definidas mas tem **2 bugs** que impedem de rodar.

### Bug 1: Erro de sintaxe na linha 122

**Arquivo:** `gerar_templates.py:122`

Linha atual (quebrada):
```python
<td style="height:4px;background:linear-gradient(90deg,{c},{'{{c}}','{{c}}'.replace('{'+'c}','{c}')).replace('{{c}}',lighter());"></td>
```

Trocar por:
```python
<td style="height:4px;background:linear-gradient(90deg,{c},{c},{c});"></td>
```

### Bug 2: Typo na linha 31 (papelaria)

**Arquivo:** `gerar_templates.py:31`

Linha atual:
```python
"Destaque para <strong;volta as aulas e promocoes</strong>"
```

Trocar por:
```python
"Destaque para <strong>volta as aulas e promocoes</strong>"
```

### Como rodar (apos corrigir):

```bash
python gerar_templates.py
```

### Templates que serao criados (30):

| Template | Cor | Stat |
|----------|-----|------|
| bar.html | #f59e0b (amarelo) | 72% |
| clinica_medica.html | #0ea5e9 (azul) | 82% |
| clinica_veterinaria.html | #8b5cf6 (roxo) | 76% |
| confeitaria.html | #ec4899 (rosa) | 68% |
| curso_pre_vestibular.html | #8b5cf6 (roxo) | 88% |
| eletricista.html | #f59e0b (amarelo) | 79% |
| encanador.html | #0ea5e9 (azul) | 81% |
| escola_de_idiomas.html | #0ea5e9 (azul) | 85% |
| estetica.html | #ec4899 (rosa) | 83% |
| estudio_de_pilates.html | #8b5cf6 (roxo) | 78% |
| farmacia.html | #22c55e (verde) | 71% |
| floricultura.html | #ec4899 (rosa) | 70% |
| imobiliaria.html | #2563eb (azul escuro) | 90% |
| joalheria.html | #f59e0b (amarelo) | 76% |
| lanchonete.html | #f97316 (laranja) | 75% |
| lavanderia.html | #0ea5e9 (azul) | 68% |
| loja_de_bicicleta.html | #10b981 (verde) | 74% |
| loja_de_celulares.html | #6366f1 (indigo) | 88% |
| loja_de_moveis.html | #d97706 (amber) | 82% |
| loja_de_roupas.html | #ec4899 (rosa) | 85% |
| marcenaria.html | #92400e (marrom) | 72% |
| material_de_construcao.html | #f97316 (laranja) | 75% |
| otica.html | #6366f1 (indigo) | 74% |
| padaria.html | #d97706 (amber) | 70% |
| papelaria.html | #8b5cf6 (roxo) | 65% |
| pintor.html | #ec4899 (rosa) | 73% |
| pizzaria.html | #ef4444 (vermelho) | 80% |
| serralheria.html | #6b7280 (cinza) | 70% |
| supermercado.html | #10b981 (verde) | 80% |
| vidracaria.html | #0ea5e9 (azul) | 71% |

### Templates ja existentes (NAO precisam ser criados):

- restaurante.html, academia.html, barbearia.html, salao.html
- dentista.html, petshop.html, advogado.html, oficina.html
- auto_escola.html, contador.html, base.html

---

## 2. Atualizar Mapeamento no envio_emails_zoho.py

### Status: PENDENTE (fazer DEPOIS do passo 1)

**Arquivo:** `envio_emails_zoho.py:62-80`

Substituir o dicionario `CATEGORIA_TEMPLATE` por:

```python
CATEGORIA_TEMPLATE = {
    # Food
    "restaurante": "restaurante.html",
    "pizzaria": "pizzaria.html",
    "lanchonete": "lanchonete.html",
    "confeitaria": "confeitaria.html",
    "churrascaria": "restaurante.html",
    "bar": "bar.html",
    "padaria": "padaria.html",
    # Saude
    "academia": "academia.html",
    "estudio de pilates": "estudio_de_pilates.html",
    "dentista": "dentista.html",
    "clinica medica": "clinica_medica.html",
    "clinica veterinaria": "clinica_veterinaria.html",
    "estetica": "estetica.html",
    "farmacia": "farmacia.html",
    "otica": "otica.html",
    # Beleza
    "barbearia": "barbearia.html",
    "salao de beleza": "salao.html",
    # Servicos
    "advogado": "advogado.html",
    "contador": "contador.html",
    "oficina mecanica": "oficina.html",
    "auto escola": "auto_escola.html",
    "pet shop": "petshop.html",
    "eletricista": "eletricista.html",
    "encanador": "encanador.html",
    "pintor": "pintor.html",
    "marcenaria": "marcenaria.html",
    "serralheria": "serralheria.html",
    "vidracaria": "vidracaria.html",
    # Lojas
    "loja de roupas": "loja_de_roupas.html",
    "loja de moveis": "loja_de_moveis.html",
    "loja de celulares": "loja_de_celulares.html",
    "loja de bicicleta": "loja_de_bicicleta.html",
    "joalheria": "joalheria.html",
    "floricultura": "floricultura.html",
    "papelaria": "papelaria.html",
    "material de construcao": "material_de_construcao.html",
    "supermercado": "supermercado.html",
    "lavanderia": "lavanderia.html",
    # Educacao
    "escola de idiomas": "escola_de_idiomas.html",
    "curso pre vestibular": "curso_pre_vestibular.html",
    # Imoveis
    "imobiliaria": "imobiliaria.html",
}
```

**Nota:** As chaves devem ser normalizadas (lowercase, sem acento), igual a funcao `normalize_categoria()` ja faz. Verificar se as categorias no CSV batem com as chaves aqui.

---

## 3. Busca de Emails Playwright

### Status: RODANDO / PODE RETOMAR

**Script:** `buscar_emails_playwright.py`

```bash
python buscar_emails_playwright.py
```

- Le o CSV `output/playwright/todos_comercios.csv`
- Progresso em `output/playwright/progresso_emails_api.json`
- Resume automatico (le progresso anterior)
- Se der CAPTCHA no Google, pausa pra resolver manualmente

---

## 4. Envio de Emails

### Status: PRONTO PRA USAR

**Script:** `envio_emails_zoho.py`

```bash
python envio_emails_zoho.py
```

- Precisa da App Password do Zoho no `.env` (`ZOHO_SMTP_APP_PASSWORD`)
- Limite: 250/dia (Zoho Mail Lite)
- Delay: 30-60s entre emails
- Horario: 9h-18h seg-sex
- Permite escolher cidade e categoria interativamente
- Progresso em `output/envios/progresso_envio.json`

---

## Ordem de Execucao

1. Corrigir `gerar_templates.py` (2 bugs acima)
2. Rodar `python gerar_templates.py`
3. Atualizar `CATEGORIA_TEMPLATE` no `envio_emails_zoho.py`
4. Continuar busca de emails com `python buscar_emails_playwright.py`
5. Enviar emails com `python envio_emails_zoho.py`

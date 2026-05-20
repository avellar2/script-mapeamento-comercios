# Vanessa Sgrancio Estetica — Previa Visual

Landing page demonstrativa premium criada como previa comercial para envio no WhatsApp.

---

## Como abrir

1. Abra a pasta `preview-vanessa-estetica/`
2. De um duplo clique em `index.html`
3. A pagina abre direto no navegador — sem servidor, sem build

**Para testar no celular:**
- No Chrome do computador, aperte `F12` > icone de celular (Device Toolbar)
- Escolha iPhone 14 Pro ou Samsung Galaxy S20

---

## Funcionalidade de agendamento (modal em 3 passos)

A pagina possui um **modal de agendamento em 3 passos**:

1. **Escolha o servico** — grid com todos os tratamentos
2. **Escolha data e horario** — proximos 14 dias (exceto domingos) + horarios disponiveis
3. **Confirme** — resumo com botao que abre o WhatsApp ja com os dados preenchidos

O modal abre ao clicar em:
- "Agendar atendimento" no hero
- Qualquer card de servico na secao "Nossos cuidados"
- "Agendar agora" na secao de agendamento
- Botao flutuante verde no canto inferior direito (direto pro WhatsApp)

Apos confirmar, o WhatsApp abre com uma mensagem ja preenchida contendo servico, data e horario escolhidos.

---

## Como trocar o telefone

1. Abra `script.js`
2. Procure por: `5521999999999`
3. Substitua pelo numero da Vanessa (com DDD, so numeros)
4. Salve

---

## Como trocar os servicos

1. Abra `index.html`
2. Va ate a secao `id="servicos"`
3. Cada servico esta dentro de `class="servico-item"`
4. Para editar: altere o `h3` (titulo) e o `data-servico` no botao
5. Para trocar a imagem: altere o `src` da imagem dentro do card

**Para adicionar/remover servicos do modal (Passo 1):**
- No `index.html`, dentro de `id="modalAgendamento"`, localize a div `class="modal-servicos"`
- Adicione ou remova botoes `class="modal-servico"` mantendo o mesmo padrao
- **Importante:** mantenha os `data-servico` identicos entre os cards da pagina e os botoes do modal

---

## Como trocar as imagens

A pagina usa imagens reais do Unsplash relacionadas a estetica/beleza.

Para colocar fotos da Vanessa:
1. Adicione as imagens na pasta `preview-vanessa-estetica/`
2. No `index.html`, localize o `src` da imagem que deseja trocar
3. Substitua pelo nome do seu arquivo, ex: `src="foto-hero.jpg"`

**Recomendacoes de imagens:**
- Hero: retrato/procedimento facial, proporcao vertical ou 16:9
- Servico destacado: 16:10 paisagem
- Galeria: variadas, minimo 800px de largura
- Depoimentos: fotos quadradas de rosto
- Local: paisagem da cidade ou fachada

---

## Como gravar o video para o WhatsApp

### No celular (recomendado):

1. Envie a pasta para o celular (Google Drive, cabo USB, AirDrop)
2. No celular, abra o `index.html` com o navegador
3. Grave a tela:
   - **iPhone:** Controle de Centro > Gravacao de Tela
   - **Android:** Barra de notificacoes > Gravar tela
4. Navegue pela pagina de cima a baixo, mostrando:
   - Hero com o nome e botao "Agendar agora"
   - Servicos (clique em um para mostrar o modal)
   - Galeria
   - CTA final
5. Envie o video pelo WhatsApp

### No computador (alternativa):

1. Abra o `index.html` no Chrome
2. `F12` > modo celular
3. Grave com `Win + G` (Windows) ou OBS
4. Envie pelo WhatsApp Web

---

## Estrutura

```
preview-vanessa-estetica/
├── index.html              # Pagina completa
├── style.css              # Estilos premium + modal
├── script.js              # Modal de agendamento 3 passos + animacoes
├── vanessa.png            # Foto da profissional
├── bg_hero-TRANSPARETE.png # Fundo da hero
└── README.md              # Este arquivo
```

---

## Personalizacao rapida

### Cores
No topo do `style.css`, dentro de `:root`:
- `--accent` = dourado rosé (destaques)
- `--bg` = champagne (fundo)
- `--text` = marrom escuro (textos)

### Textos
Todo conteudo esta no `index.html`. Use `Ctrl + F` para localizar rapidamente.

### Fonte
Outfit (Google Fonts). Para trocar, altere o link no `<head>` do `index.html`.

---

## Observacoes

- Pagina 100% offline apos aberta (exceto imagens externas)
- Nao coleta dados nem envia informacoes para lugar nenhum
- O numero de telefone e um placeholder: **5521999999999**
- Modal funciona sem backend — as datas e horarios sao gerados dinamicamente no navegador

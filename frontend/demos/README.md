# Demo Library — Landing Pages para Negócios Locais

Biblioteca profissional de landing pages por nicho para venda de mini sites, paginas de WhatsApp, paginas de agendamento e catalogos digitais.

## Demos disponiveis

| Demo | Nicho | Pagina |
|------|-------|--------|
| Resolve Ja | Assistencia Tecnica | `/demos/assistencia-tecnica` |
| Sorriso Prime | Dentista | `/demos/dentista` |
| Avellar e Costa | Advocacia | `/demos/advogado` |
| Conferencia Avivados 2026 | Igreja / Evento | `/demos/igreja-evento` |
| Morar Bem | Imobiliaria | `/demos/imobiliaria` |
| Auto Prime | Estetica Automotiva | `/demos/automotiva` |
| Aprender Mais | Cursos / Reforco | `/demos/cursos` |
| Doce Encanto | Personalizados / Festas | `/demos/personalizados` |
| Studio Bella Face | Estetica | `/demos/estetica` |
| Barbearia Imperial | Barbearia | `/demos/barbearia` |
| Sabor Caseiro | Cardapio Digital | `/demos/cardapio` |

Acesse o indice em `/demos`.

## Como gravar video para WhatsApp

1. Inicie o projeto localmente: `npm run dev`
2. Abra o navegador no modo responsivo (F12 > Toggle device toolbar)
3. Selecione um celular (ex: iPhone 14 Pro Max)
4. Acesse a demo desejada
5. Use o gravador de tela do sistema
6. Navegue suavemente pelas secoes e mostre o botao de WhatsApp
7. Exporte em MP4, 720p

## Como transformar uma demo em previa personalizada

1. Duplique a pasta da demo em `app/demos/novo-slug/`
2. Altere nome, WhatsApp, textos e cores para o cliente real
3. Substitua imagens da galeria por fotos reais
4. Atualize `lib/demo-data.ts` com os dados da nova demo
5. Pre-visualize em `/demos/novo-slug`

## Como duplicar uma demo para outro nicho

1. Copie a pasta da demo mais proxima
2. Renomeie para o novo slug
3. Ajuste icones, textos, cores e imagens
4. Registre em `lib/demo-data.ts`
5. Adicione o card na pagina indice

## Tecnologias

- Next.js
- TailwindCSS
- Framer Motion
- Lucide React

## Scripts

```bash
npm run dev      # Inicia servidor de desenvolvimento
npm run build    # Build para producao
npm run start    # Inicia servidor de producao
```

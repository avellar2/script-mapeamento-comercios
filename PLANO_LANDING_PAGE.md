# Plano: Landing Page Premium - Clínica Sorriso Prime

## 1. O que será alterado
Criar um novo projeto Next.js 14+ com shadcn/ui, TailwindCSS e Framer Motion dentro do repositório atual, em um subdiretório dedicado para a landing page da clínica odontológica.

## 2. Arquivos que serão criados/modificados
- `frontend/clinica-sorriso-prime/` - novo diretório Next.js
- Componentes React para cada seção da landing page
- Configuração Tailwind com paleta de cores personalizada (branco, azul claro, verde água, cinza)
- Página principal `app/page.tsx` com todas as seções

## 3. Risco
Baixo. É um novo diretório isolado, não afeta o projeto Python existente.

## 4. Modelo recomendado
Kimi K2.6 (atual) - ideal para frontend premium.

## 5. Ordem segura de implementação
1. Inicializar projeto Next.js com shadcn/ui
2. Configurar Tailwind com cores da clínica
3. Instalar Framer Motion e Lucide React
4. Criar componentes das seções:
   - Navigation
   - Hero (asymmetric, elegante)
   - Tratamentos
   - Diferenciais
   - Equipe
   - Depoimentos
   - Estrutura/Ambiente
   - Localização
   - FAQ
   - Footer + CTA final
5. Verificar responsividade mobile
6. Testar build

## Diretrizes de design (skills aplicadas)
- DESIGN_VARIANCE: 8 (layout assimétrico, não genérico)
- MOTION_INTENSITY: 6 (micro-interações fluidas, sem exageros)
- VISUAL_DENSITY: 4 (espaçamento generoso, visual limpo)
- Tipografia: Geist/Outfit, sem Inter
- Sem cards genéricos de 3 colunas - usar grids assimétricos
- Hero não centralizado - alinhado à esquerda com imagem à direita
- Cores: base neutra (zinc/slate) + acento único (verde água ou azul claro)
- Botões com scale(0.97) no :active
- Animações com spring physics suave
- Foco total em mobile-first
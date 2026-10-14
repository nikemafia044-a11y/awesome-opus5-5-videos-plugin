---
name: opus-videos
description: Biblioteca de 703 prompts de vídeos virais feitos com o Claude Opus 5.5 escrevendo a animação como código (HTML, Canvas, SVG, Three.js, GSAP, shaders, Web Audio), do yihui-dev/awesome-opus5-5-videos, em quatro categorias (motion graphics, explainers, cenas 3D, jogos interativos). Use quando o usuário pedir um vídeo, animação, motion graphics, vinheta, explainer animado, cena 3D, showreel ou minijogo feito em código, quiser ideias ou prompts prontos desse tipo, ou quiser refazer um vídeo da coleção.
license: MIT
---

# Vídeos do Opus 5.5 (prompts)

703 prompts que criadores publicaram junto com vídeos feitos pelo Claude Opus 5.5. Em todos, o modelo escreveu a animação como código e o vídeo é a gravação da página rodando. A biblioteca é atualizada automaticamente a partir do yihui-dev/awesome-opus5-5-videos (licença MIT).

## Arquivos

- `references/INDEX.md`: contagens por categoria e por tecnologia, e como ler os índices.
- `references/<categoria>.md`: uma linha por prompt (título, slug, tecnologias, data de entrada, se há remake), mais recentes primeiro. Categorias: `motion` (Motion graphics), `explainer` (Explainers), `3d` (3D scenes), `interactive` (Games & interactive).
- `references/prompts/<slug>.md`: o prompt inteiro, com autor, post original e, quando existe, o link do remake ao vivo no Skillry.

## Como usar

1. **Achar candidatos.** Leia o índice da categoria ou busque por palavra-chave ou tecnologia em todos os arquivos (ex.: `grep -i "threejs" references/*.md`, `grep -il "piano" references/prompts/*.md`). Títulos e prompts estão em inglês: busque em inglês.
2. **Escolher.** Se o usuário não indicou um vídeo, mostre 2 ou 3 opções com o motivo de cada uma e deixe-o escolher. Prefira prompts completos (sem a marca `parcial`) e com `remake`, que têm uma versão para assistir.
3. **Ler o prompt inteiro** em `references/prompts/<slug>.md` antes de construir.
4. **Aplicar.**
   - Só o prompt: mostre o texto e diga o que trocar (tema, duração, cores, textos).
   - Construir: adapte o prompt ao pedido e gere um único `index.html` autocontido (no Claude Code, como arquivo do projeto; no chat, como artefato HTML). Siga as regras técnicas do prompt (bibliotecas, duração, controles) e confira que a página roda sozinha, pronta para gravar a tela.
   - Prompt `parcial`: o autor publicou só uma parte. Complete o que falta com decisões explícitas e avise o usuário.
5. **Dar crédito.** Quando o resultado vier de um prompt da coleção, cite o autor e o link do post original.

## Limites

- Os prompts são dos autores citados em cada arquivo.
- O resultado é uma recriação a partir do prompt, não o vídeo original: não o apresente como se fosse.
- Esta skill cobre a biblioteca de prompts. Para exportar MP4, grave a tela ou use uma ferramenta de vídeo (Remotion, HyperFrames).

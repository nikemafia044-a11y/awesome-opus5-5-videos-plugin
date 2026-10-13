# awesome-opus5-5-videos (plugin)

Empacota os prompts do [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) (MIT), vídeos virais em que o Claude Opus 5.5 escreveu a animação como código, num plugin com uma skill, `opus-videos`, para o app do Claude (chat, Cowork) e o Claude Code. Os prompts são dos autores citados em cada arquivo; os vídeos e os remakes ficam no [Skillry](https://skillry.dev/ai-videos/opus-5-5).

## Instalar

No app do Claude (web ou desktop): **Customize > Plugins > Add > Add marketplace**, informe este repositório (`nikemafia044-a11y/awesome-opus5-5-videos-plugin`) e ligue **Sync automatically**. Depois adicione o plugin `awesome-opus5-5-videos`.

Ele fica salvo na conta: aparece no chat e baixa sozinho no Claude Code (CLI e desktop) como plugin sincronizado. Não instale também pela linha de comando do Claude Code, ou a skill aparece duplicada.

Só para quem usa o Claude Code sem o app (Claude Code 2.1.275 ou mais novo):

```
/plugin install awesome-opus5-5-videos --marketplace nikemafia044-a11y/awesome-opus5-5-videos-plugin
```

## Atualização

O workflow `.github/workflows/sync.yml` roda todo dia (e sob demanda em **Actions**). Ele testa o gerador, baixa o upstream, roda `scripts/build.py` e só faz commit quando algum prompt mudou, subindo a versão do plugin. Com **Sync automatically** ligado, o app recebe a versão nova sozinho.

Para gerar localmente: `python scripts/build.py --upstream <clone do awesome-opus5-5-videos>`. Testes: `python -m unittest discover -s tests`.

Em repositório público, o GitHub desliga workflows agendados depois de 60 dias sem atividade. Se isso acontecer, reative em **Actions**.

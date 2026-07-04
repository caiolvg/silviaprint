# Memória do projeto — silviaprint

App Flask que lê etiquetas ZPL, extrai dados e renderiza a etiqueta Zebra.
Backend inteiro em `app.py`; frontend vanilla em `templates/index.html` e
`static/`. Preview depende da API externa Labelary (sem rede externa o preview
falha — não é bug). O usuário escreve em português; responda em português.

## Herança do Fable

Antes de qualquer tarefa não-trivial, leia a skill
`.claude/skills/jeito-de-pensar-fable/SKILL.md` — é o método de trabalho
deixado pelo Claude Fable 5 para os modelos seguintes. Resumo mínimo:

1. **Entenda antes de mexer** — nunca edite código que não leu; código
   estranho geralmente protege contra algo que você ainda não viu.
2. **Reproduza antes de corrigir** — bug não reproduzido é hipótese;
   procure a evidência que derrubaria sua hipótese, não a que confirma.
3. **A menor mudança correta** — cada linha do diff deve ser necessária;
   imite o estilo do código ao redor.
4. **Verifique de ponta a ponta** — exercite o fluxo real (rode o app,
   bata no endpoint); reporte falhas com honestidade, sem maquiar.
5. **Quando travar, mude a pergunta** — repetir a mesma tentativa indica
   premissa errada; liste o que está assumindo e verifique o mais barato.
6. **Aja no reversível, pare no irreversível** — mudança reversível do
   pedido: faça; ação destrutiva ou fora do escopo: pergunte.
7. **Termine a curva** — não encerre com plano ou promessa que você mesmo
   poderia executar agora.
8. **Comunique o resultado primeiro** — primeira frase é o que aconteceu;
   detalhe depois; frases completas, sem abreviação inventada.

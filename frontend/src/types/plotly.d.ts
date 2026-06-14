// O build "dist-min" do Plotly não traz tipos. Declaramos o módulo de forma
// frouxa (any): para os gráficos, tipar data/layout em detalhe traria pouco
// retorno. As estruturas que passamos vêm tipadas da nossa própria API.
declare module 'plotly.js-dist-min'

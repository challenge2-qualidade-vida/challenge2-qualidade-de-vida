// Dados falsos da rota POST /verificacoes (#82), para a demo e os prints da tela Verificar (#98).
// Exemplos fictícios, no formato da rota: o Research devolve só os ids dos trechos e os scores.
// Não decidem nada: devolvem um de dois roteiros gravados à mão.
import type { components } from "../esquema";

type Esquemas = components["schemas"];

const GUIA: Esquemas["FonteDoVeredito"] = { titulo: "Guia Alimentar para a População Brasileira", instituicao: "Ministério da Saúde", ano: 2014, url: null };

const MENSAGENS = {
  aprovado: {
    consumidor_geral: "A recomendação de evitar alimentos ultraprocessados está no Guia Alimentar para a População Brasileira. O guia explica que esses produtos costumam ter muito açúcar, sal e gordura e pouca fibra. A orientação é basear a alimentação em alimentos in natura e minimamente processados.",
    consumidor_rapido: "Sim, o Guia Alimentar recomenda evitar ultraprocessados. Prefira alimentos in natura e minimamente processados.",
  },
  retorno: {
    consumidor_geral: "O feijão é fonte de fibra, e o Guia Alimentar recomenda o seu consumo. A base de conhecimento não traz nada que diga que o feijão cura o diabetes. Quem tem diabetes deve seguir a orientação de um profissional de saúde.",
    consumidor_rapido: "O feijão tem fibra, mas a base não diz que ele cura o diabetes. Siga a orientação de um profissional de saúde.",
  },
} as const;

const trechos = (prefixo: string, scores: number[]) => scores.map((score, i) => ({ trecho: `${prefixo}-${i + 1}`, score }));

function passo(agente: Esquemas["PassoDoAgente"]["agente"], alegacao: string, entrada: Record<string, unknown>, saida: Record<string, unknown>, s: number): Esquemas["PassoDoAgente"] {
  return { agente, entrada: { alegacao, ...entrada }, saida, segundos: s };
}

export function verificacaoFalsa(alegacao: string, perfil: Esquemas["PerfilDeLeitura"] = "consumidor_geral"): Esquemas["ResultadoDaVerificacao"] {
  if (/\bcura/i.test(alegacao)) {
    const mensagem = MENSAGENS.retorno[perfil];
    return {
      veredito: { classificacao: "parcial", mensagem, fontes: [GUIA], aprovado_pela_validacao: true },
      retornos: 1,
      historico: [
        passo("research", alegacao, { limite: 5 }, { evidencias: trechos("guia-feijao", [0.71, 0.66, 0.6]) }, 0.7),
        passo("analysis", alegacao, { motivos: [] }, { classificacao: "reciclada", justificativa: "O guia fala do feijão.", citacoes: ["guia-feijao-1"], citacoes_invalidas: [], confianca: 0.74 }, 3.9),
        passo("validation", alegacao, {}, { aprovado: false, motivos: ["As evidências não falam de diabetes", "Confiança abaixo do mínimo"], retornar_para: "research" }, 2.1),
        passo("research", alegacao, { limite: 10 }, { evidencias: trechos("guia-feijao", [0.73, 0.71, 0.66, 0.62, 0.58, 0.55]) }, 0.9),
        passo("analysis", alegacao, { motivos: [] }, { classificacao: "parcial", justificativa: "A base confirma a fibra do feijão, mas não fala em cura.", citacoes: ["guia-feijao-1", "guia-feijao-2"], citacoes_invalidas: [], confianca: 0.88 }, 4.4),
        passo("validation", alegacao, {}, { aprovado: true, motivos: [], retornar_para: null }, 2.0),
        passo("communication", alegacao, { perfil }, { classificacao: "parcial", aprovado_pela_validacao: true }, 1.8),
      ],
    };
  }
  const mensagem = MENSAGENS.aprovado[perfil];
  return {
    veredito: { classificacao: "reciclada", mensagem, fontes: [GUIA], aprovado_pela_validacao: true },
    retornos: 0,
    historico: [
      passo("research", alegacao, { limite: 5 }, { evidencias: trechos("guia-ultraprocessados", [0.86, 0.81, 0.77, 0.7, 0.64]) }, 0.8),
      passo("analysis", alegacao, { motivos: [] }, { classificacao: "reciclada", justificativa: "O guia recomenda evitar ultraprocessados.", citacoes: ["guia-ultraprocessados-1"], citacoes_invalidas: [], confianca: 0.91 }, 4.1),
      passo("validation", alegacao, {}, { aprovado: true, motivos: [], retornar_para: null }, 2.3),
      passo("communication", alegacao, { perfil }, { classificacao: "reciclada", aprovado_pela_validacao: true }, 1.9),
    ],
  };
}

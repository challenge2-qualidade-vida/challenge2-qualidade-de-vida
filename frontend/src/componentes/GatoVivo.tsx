// Gato que respira, pisca e olha para o cursor (efeitos/gatos.ts). Começa como a imagem parada
// e vira um canvas quando a imagem carrega, com a mesma classe, para o CSS valer igual.
import { useEffect, useRef, useState } from "react";
import { gatoVivoDisponivel, registrarGato, type NomeDoGato } from "../efeitos/gatos";

interface Props { nome: NomeDoGato; src: string; className?: string; alt?: string }

export function GatoVivo({ nome, src, className, alt = "" }: Props) {
  const [imagem, setImagem] = useState<HTMLImageElement | null>(null);
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!gatoVivoDisponivel()) return;
    let vivo = true;
    const img = new Image();
    img.src = src;
    img.decode().then(() => { if (vivo && img.naturalWidth) setImagem(img); }).catch(() => { /* fica a imagem parada */ });
    return () => { vivo = false; };
  }, [src]);

  useEffect(() => {
    if (!imagem || !canvas.current) return;
    return registrarGato(canvas.current, imagem, nome);
  }, [imagem, nome]);

  if (!imagem) return <img src={src} data-gato={nome} alt={alt} className={className} />;
  return alt
    ? <canvas ref={canvas} className={className} width={imagem.naturalWidth} height={imagem.naturalHeight} role="img" aria-label={alt} />
    : <canvas ref={canvas} className={className} width={imagem.naturalWidth} height={imagem.naturalHeight} aria-hidden="true" />;
}

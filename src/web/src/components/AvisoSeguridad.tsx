// Avisos de seguridad (feature 40, benchmark Patas en Cali §10): el momento
// de publicar y el de coordinar un encuentro son donde ocurren las estafas
// (falsas recompensas, datos bancarios). Puro copy, cero fricción.
const TEXTOS = {
  publicar:
    'Este es un espacio público: lo que publiques lo puede ver cualquier persona. No compartas datos bancarios, claves ni información sensible.',
  contactar:
    'Antes de coordinar un encuentro: nadie debe pedirte dinero ni datos bancarios; acuerda un punto visible y, si puedes, ve acompañado. Pet Finder Col no verifica los reportes.',
} as const;

export function AvisoSeguridad({ contexto }: { contexto: keyof typeof TEXTOS }) {
  return (
    <p className="rounded-xl border border-ochre/40 bg-ochre/10 px-4 py-3 text-xs text-ink-soft">
      ⚠️ {TEXTOS[contexto]}
    </p>
  );
}

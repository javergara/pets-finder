import { Link } from 'react-router-dom';

// Landing pública (feature 15-public-landing). Un solo archivo: ninguna otra pantalla
// reutiliza estas secciones y el proyecto no tiene precedente de subcarpetas
// `components/<feature>/` para secciones de una sola vista. Copy verbatim de
// `design/prototypes/Adopta Landing.dc.html`. Sin llamadas a `api/client`: todo el
// contenido (cifras, tarjetas de apadrinamiento, tabla del panel) es estático por
// decisión de producto — ver `progress/current.md`.

function NavPublica() {
  return (
    <nav className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-bg/95 px-14 py-5 backdrop-blur">
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-forest font-display text-base text-bg">
          A
        </div>
        <span className="font-display text-xl text-ink">Adopta</span>
      </div>
      <div className="flex items-center gap-8">
        <a href="#como" className="text-sm text-ink-soft">
          Cómo funciona
        </a>
        <a href="#refugios" className="text-sm text-ink-soft">
          Para refugios
        </a>
        <a href="#apadrinar" className="text-sm text-ink-soft">
          Apadrinar
        </a>
        <Link
          to="/descubrir"
          className="rounded-lg bg-forest px-4 py-2.5 text-sm text-bg hover:bg-forest-hover"
        >
          Entrar a la app
        </Link>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="mx-auto grid max-w-[1320px] grid-cols-1 gap-14 px-14 py-20 md:grid-cols-2 md:items-center">
      <div>
        <div className="mb-5 font-mono text-[11.5px] tracking-[0.1em] text-muted-2 uppercase">
          Bogotá · Medellín · Cali
        </div>
        <h1 className="mb-5 text-[66px] leading-[1.07] font-display text-ink tracking-[-0.025em] text-balance">
          Adoptar bien empieza por conocerse bien.
        </h1>
        <p className="mb-8 max-w-[520px] text-lg leading-relaxed text-ink-soft">
          Respondes un cuestionario sobre tu hogar, ves los perfiles de mascotas que de verdad
          encajan contigo y hablas directamente con el refugio que las cuida.
        </p>
        <div className="mb-8 flex gap-3">
          <Link
            to="/cuestionario"
            className="rounded-xl bg-forest px-6 py-4 text-[15.5px] text-bg hover:bg-forest-hover"
          >
            Empezar el cuestionario
          </Link>
          <Link
            to="/refugio"
            className="rounded-xl border border-line px-6 py-4 text-[15.5px] text-ink"
          >
            Soy un refugio
          </Link>
        </div>
        <div className="flex gap-9 border-t border-line pt-6">
          <div>
            <div className="font-display text-3xl text-ink">2.140</div>
            <div className="mt-0.5 text-[13px] text-muted">adopciones cerradas</div>
          </div>
          <div>
            <div className="font-display text-3xl text-ink">86</div>
            <div className="mt-0.5 text-[13px] text-muted">refugios verificados</div>
          </div>
          <div>
            <div className="font-display text-3xl text-ink">7%</div>
            <div className="mt-0.5 text-[13px] text-muted">tasa de devolución</div>
          </div>
        </div>
      </div>
      <div className="relative h-[560px]">
        <div className="absolute top-9 left-[8%] h-[440px] w-[78%] -rotate-4 rounded-[22px] border border-line bg-surface" />
        <div className="absolute top-5 left-[14%] flex h-[470px] w-[78%] rotate-3 flex-col overflow-hidden rounded-[22px] border border-line bg-surface shadow-[0_30px_60px_-40px_rgba(27,26,23,.55)]">
          <div className="relative flex flex-1 items-center justify-center bg-[repeating-linear-gradient(135deg,#EDE6D8_0_10px,#E4DBCA_10px_20px)]">
            <div className="rounded-md border border-line bg-surface px-2.5 py-1 font-mono text-[11.5px] text-muted-2">
              foto · Luna
            </div>
            <span className="absolute top-3.5 left-3.5 rounded-full bg-forest px-2.5 py-1 font-mono text-[11px] text-bg">
              94% afín
            </span>
          </div>
          <div className="px-5 pt-4.5 pb-5.5">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-[26px] text-ink">Luna</span>
              <span className="text-[13.5px] text-muted">2 años · Mestiza</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              <span className="rounded-full border border-forest-tint-line bg-forest-tint px-2.5 py-1 text-[12.5px] text-forest">
                Juguetona
              </span>
              <span className="rounded-full border border-forest-tint-line bg-forest-tint px-2.5 py-1 text-[12.5px] text-forest">
                Sociable
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

interface PasoProps {
  numero: string;
  titulo: string;
  descripcion: string;
}

function Paso({ numero, titulo, descripcion }: PasoProps) {
  return (
    <div>
      <div className="mb-3.5 font-mono text-[11.5px] text-forest">{numero}</div>
      <div className="mb-2 font-display text-[22px] text-ink">{titulo}</div>
      <p className="text-[14.5px] leading-relaxed text-ink-soft">{descripcion}</p>
    </div>
  );
}

const PASOS: PasoProps[] = [
  {
    numero: '01',
    titulo: 'Cuéntanos de tu hogar',
    descripcion:
      'Seis preguntas sobre espacio, rutina, presupuesto y otras mascotas. Cinco minutos.',
  },
  {
    numero: '02',
    titulo: 'Desliza con criterio',
    descripcion: 'Cada perfil trae su porcentaje de afinidad contigo, distancia y carácter real.',
  },
  {
    numero: '03',
    titulo: 'Habla con el refugio',
    descripcion: 'Al marcar «me interesa» abrimos el chat y enviamos tu cuestionario al refugio.',
  },
  {
    numero: '04',
    titulo: 'Conócense en persona',
    descripcion: 'Se agenda una visita. La adopción se cierra solo después de conocerse.',
  },
];

function ComoFunciona() {
  return (
    <section id="como" className="border-y border-line bg-surface px-14 py-20">
      <div className="mx-auto max-w-[1200px]">
        <h2 className="mb-3 font-display text-[40px] text-ink tracking-[-0.02em]">Cómo funciona</h2>
        <p className="mb-12 max-w-[560px] text-base text-muted">
          Cuatro pasos. Ninguno se salta: el cuestionario es obligatorio antes de ver el primer
          perfil.
        </p>
        <div className="grid grid-cols-1 gap-6.5 sm:grid-cols-2 lg:grid-cols-4">
          {PASOS.map((paso) => (
            <Paso key={paso.numero} {...paso} />
          ))}
        </div>
      </div>
    </section>
  );
}

interface CifraCardProps {
  valor: string;
  etiqueta: string;
  destacada?: boolean;
}

function CifraCard({ valor, etiqueta, destacada }: CifraCardProps) {
  return (
    <div
      className={`rounded-2xl border p-6 ${
        destacada ? 'border-forest-tint-line bg-forest-tint' : 'border-line bg-surface'
      }`}
    >
      <div className="font-display text-[34px] text-forest">{valor}</div>
      <div className="mt-1.5 text-sm leading-relaxed text-ink-soft">{etiqueta}</div>
    </div>
  );
}

function PorQueCuestionario() {
  return (
    <section className="mx-auto max-w-[1200px] px-14 py-20">
      <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="mb-4.5 font-mono text-[11.5px] tracking-[0.1em] text-muted-2 uppercase">
            Por qué el cuestionario
          </div>
          <h2 className="mb-4.5 text-[38px] leading-[1.15] font-display text-ink tracking-[-0.02em] text-balance">
            Deslizar es fácil. Devolver un animal, no.
          </h2>
          <p className="mb-4 text-base leading-relaxed text-ink-soft">
            Una parte importante de las adopciones falla porque la mascota no encajaba con la vida
            real de quien la adoptó: horarios largos fuera de casa, apartamentos pequeños para razas
            activas, o costos veterinarios que nadie calculó.
          </p>
          <p className="text-base leading-relaxed text-ink-soft">
            Por eso el cuestionario va primero y la afinidad se calcula sobre tus respuestas, no
            sobre la foto que más te guste.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <CifraCard valor="6" etiqueta="preguntas antes de ver el primer perfil" />
          <CifraCard valor="24 h" etiqueta="tiempo medio de respuesta del refugio" />
          <CifraCard valor="1" etiqueta="visita presencial obligatoria antes de entregar" />
          <CifraCard valor="0" etiqueta="costo para adoptantes y refugios" destacada />
        </div>
      </div>
    </section>
  );
}

interface ApadrinarCardProps {
  nombre: string;
  motivo: string;
  porcentaje: number;
}

function ApadrinarCard({ nombre, motivo, porcentaje }: ApadrinarCardProps) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-forest-hover bg-bg/[.07] p-4.5">
      <div className="h-[62px] w-[62px] shrink-0 rounded-xl bg-[repeating-linear-gradient(135deg,#2E6E52_0_8px,#28604A_8px_16px)]" />
      <div className="flex-1">
        <div className="font-display text-[19px] text-bg">{nombre}</div>
        <div className="mt-1 mb-2.5 text-[13px] text-forest-tint-line">{motivo}</div>
        <div className="h-1.5 rounded-full bg-bg/[.16]">
          <div className="h-full rounded-full bg-bg" style={{ width: `${porcentaje}%` }} />
        </div>
      </div>
    </div>
  );
}

function FranjaApadrinar() {
  return (
    <section id="apadrinar" className="bg-forest px-14 py-20">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-14 lg:grid-cols-2">
        <div>
          <h2 className="mb-4 text-[38px] leading-[1.15] font-display text-bg tracking-[-0.02em] text-balance">
            ¿Todavía no puedes adoptar?
          </h2>
          <p className="mb-7 max-w-[460px] text-[16.5px] leading-relaxed text-forest-tint-line">
            Apadrina a una mascota concreta desde $30.000 COP al mes. Cubres su comida y su
            veterinario mientras espera hogar, y recibes fotos y novedades cada mes.
          </p>
          <Link
            to="/apadrinar"
            className="inline-block rounded-xl bg-bg px-6 py-4 text-[15.5px] text-forest"
          >
            Ver quién necesita apoyo
          </Link>
        </div>
        <div className="flex flex-col gap-3">
          <ApadrinarCard nombre="Canela" motivo="Tratamiento de cadera" porcentaje={64} />
          <ApadrinarCard nombre="Toribio" motivo="Vacunas y esterilización" porcentaje={38} />
        </div>
      </div>
    </section>
  );
}

interface FilaTablaProps {
  adoptante: string;
  mascota: string;
  afinidad: string;
  esUltima?: boolean;
}

function FilaTabla({ adoptante, mascota, afinidad, esUltima }: FilaTablaProps) {
  return (
    <div
      className={`grid grid-cols-[1.2fr_1fr_0.7fr] items-center gap-3.5 px-5 py-4 ${
        esUltima ? '' : 'border-b border-line-soft'
      }`}
    >
      <div className="text-sm text-ink">{adoptante}</div>
      <div className="text-sm text-muted">{mascota}</div>
      <div className="font-mono text-[13px] text-forest">{afinidad}</div>
    </div>
  );
}

function ParaRefugios() {
  return (
    <section id="refugios" className="mx-auto max-w-[1200px] px-14 py-20">
      <div className="grid grid-cols-1 items-start gap-14 lg:grid-cols-2">
        <div>
          <div className="mb-4.5 font-mono text-[11.5px] tracking-[0.1em] text-muted-2 uppercase">
            Para refugios y rescatistas
          </div>
          <h2 className="mb-4.5 text-[38px] leading-[1.15] font-display text-ink tracking-[-0.02em] text-balance">
            Menos mensajes vacíos, más adopciones reales.
          </h2>
          <p className="mb-6.5 text-base leading-relaxed text-ink-soft">
            Publicas tus mascotas una vez y recibes solicitudes que ya vienen con el cuestionario
            del hogar respondido, ordenadas por afinidad. Sin costo y sin comisión.
          </p>
          <Link
            to="/refugio"
            className="inline-block rounded-xl border border-forest px-6 py-4 text-[15.5px] text-forest"
          >
            Registrar mi refugio
          </Link>
        </div>
        <div className="overflow-hidden rounded-2xl border border-line bg-surface">
          <div className="grid grid-cols-[1.2fr_1fr_0.7fr] gap-3.5 border-b border-line bg-surface-alt px-5 py-3.5 font-mono text-[11px] tracking-[0.05em] text-muted uppercase">
            <div>Adoptante</div>
            <div>Mascota</div>
            <div>Afinidad</div>
          </div>
          <FilaTabla adoptante="Valentina Ríos" mascota="Luna" afinidad="94%" />
          <FilaTabla adoptante="Andrés Camacho" mascota="Luna" afinidad="89%" />
          <FilaTabla adoptante="Sara Molina" mascota="Canela" afinidad="76%" esUltima />
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line bg-surface px-14 py-11">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-6.5 w-6.5 items-center justify-center rounded-md bg-forest font-display text-[15px] text-bg">
            A
          </div>
          <span className="text-sm text-muted">Adopta · Colombia · 2026</span>
        </div>
        <div className="flex gap-6.5">
          <a href="#como" className="text-sm text-muted">
            Cómo funciona
          </a>
          <a href="#refugios" className="text-sm text-muted">
            Refugios
          </a>
          <a href="#apadrinar" className="text-sm text-muted">
            Apadrinar
          </a>
          <a href="#" className="text-sm text-muted">
            Privacidad
          </a>
        </div>
      </div>
    </footer>
  );
}

export function LandingPublica() {
  return (
    <div>
      <NavPublica />
      <Hero />
      <ComoFunciona />
      <PorQueCuestionario />
      <FranjaApadrinar />
      <ParaRefugios />
      <Footer />
    </div>
  );
}

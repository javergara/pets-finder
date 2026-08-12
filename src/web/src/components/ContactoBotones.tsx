import { mensajeContacto, urlTelefono, urlWhatsApp } from '../lib/contacto';

type Props = {
  tipo: 'perdido' | 'encontrado';
  // Nombre de la mascota o su especie — entra en el mensaje precargado.
  etiqueta: string;
  telefono: string;
};

export function ContactoBotones({ tipo, etiqueta, telefono }: Props) {
  const mensaje = mensajeContacto(tipo, etiqueta);

  return (
    <div className="flex flex-wrap gap-3">
      <a
        href={urlWhatsApp(telefono, mensaje)}
        target="_blank"
        rel="noreferrer"
        className="rounded-full bg-forest px-5 py-3 font-medium text-bg"
      >
        Contactar por WhatsApp
      </a>
      <a
        href={urlTelefono(telefono)}
        className="rounded-full border border-line px-5 py-3 font-medium text-ink"
      >
        Llamar
      </a>
    </div>
  );
}

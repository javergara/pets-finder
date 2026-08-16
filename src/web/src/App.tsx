import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import { SLUGS_ZONA } from './lib/ciudades';
import { BuscarMascota } from './screens/BuscarMascota';
import { CatalogoAdopcion } from './screens/CatalogoAdopcion';
import { DescubrirMascotas } from './screens/DescubrirMascotas';
import { EditarMascota } from './screens/EditarMascota';
import { EditarReporte } from './screens/EditarReporte';
import { LandingEmergencia } from './screens/LandingEmergencia';
import { MapaReportes } from './screens/MapaReportes';
import { MascotaDetalle } from './screens/MascotaDetalle';
import { MisReportes } from './screens/MisReportes';
import { OrganizacionDetalle } from './screens/OrganizacionDetalle';
import { PublicarAvisoAyuda } from './screens/PublicarAvisoAyuda';
import { PublicarMascota } from './screens/PublicarMascota';
import { RedDeApoyo } from './screens/RedDeApoyo';
import { Registro } from './screens/Registro';
import { RegistrarOrganizacion } from './screens/RegistrarOrganizacion';
import { ReportarMascota } from './screens/ReportarMascota';
import { ReporteDetalle } from './screens/ReporteDetalle';
import { Reportes } from './screens/Reportes';
import { ZonaLanding } from './screens/ZonaLanding';

function Nav() {
  // shrink-0 + whitespace-nowrap + overflow-x-auto: en móvil la nav se desliza
  // horizontalmente dentro de sí misma en vez de desbordar la página entera
  // (era la causa del scroll lateral en TODAS las rutas internas, feature 16).
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `shrink-0 whitespace-nowrap px-3 py-2 text-sm font-medium ${
      isActive ? 'text-forest' : 'text-muted'
    }`;

  return (
    <nav className="flex items-center gap-2 overflow-x-auto border-b border-line bg-surface px-4 py-3 [scrollbar-width:none]">
      <NavLink to="/" className="mr-4 shrink-0">
        {/* Wordmark oficial (design/logo/): sustituye la marca en texto. */}
        <img src="/logo.svg" alt="Pet Finder Col" className="h-6 w-auto" />
      </NavLink>
      <NavLink to="/reportar/perdido" className={linkClass}>
        Perdí mi mascota
      </NavLink>
      <NavLink to="/reportar/encontrado" className={linkClass}>
        Encontré una mascota
      </NavLink>
      <NavLink to="/reportes" className={linkClass}>
        Reportes
      </NavLink>
      <NavLink to="/mapa" className={linkClass}>
        Mapa
      </NavLink>
      <NavLink to="/mis-reportes" className={linkClass}>
        Mis reportes
      </NavLink>
      <NavLink to="/ayudar" className={linkClass}>
        Centros de ayuda
      </NavLink>
    </nav>
  );
}

function AppLayout() {
  return (
    <>
      <Nav />
      <Outlet />
    </>
  );
}

function App() {
  return (
    <div className="min-h-svh bg-bg">
      <Routes>
        {/* La landing de emergencia vive fuera de AppLayout: es la entrada pública,
            con sus propios CTAs gigantes, sin la nav interna. */}
        <Route path="/" element={<LandingEmergencia />} />
        <Route element={<AppLayout />}>
          <Route path="/registro" element={<Registro />} />
          {/* Un componente, dos rutas: el tipo fija los campos condicionales. */}
          <Route path="/reportar/perdido" element={<ReportarMascota tipo="perdido" />} />
          <Route path="/reportar/encontrado" element={<ReportarMascota tipo="encontrado" />} />
          <Route path="/buscar" element={<BuscarMascota />} />
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/reporte/:id" element={<ReporteDetalle />} />
          <Route path="/reporte/:id/editar" element={<EditarReporte />} />
          <Route path="/mapa" element={<MapaReportes />} />
          <Route path="/mis-reportes" element={<MisReportes />} />
          <Route path="/ayudar" element={<RedDeApoyo />} />
          <Route path="/ayudar/registrar" element={<RegistrarOrganizacion />} />
          <Route path="/ayudar/publicar-aviso" element={<PublicarAvisoAyuda />} />
          <Route path="/organizacion/:id" element={<OrganizacionDetalle />} />
          {/* Módulo de adopción (AD-01). El enlace en la nav llega en AD-08:
              hasta entonces las rutas existen y son compartibles, pero no se
              anuncian. La ficha va bajo /adoptar/mascota/:id para no chocar con
              /reporte/:id, que es el otro dominio (perdidos y encontrados). */}
          <Route path="/adoptar" element={<CatalogoAdopcion />} />
          {/* Literal antes que dinámica, como en el router de la API. */}
          <Route path="/adoptar/publicar" element={<PublicarMascota />} />
          {/* Deck de descubrimiento (AD-03). Se entra desde /adoptar; mirarlo no
              pide cuenta, y el gate de "Me interesa" vive en la pantalla. */}
          <Route path="/adoptar/descubrir" element={<DescubrirMascotas />} />
          <Route path="/adoptar/mascota/:id" element={<MascotaDetalle />} />
          {/* Edición de quien publicó (AD-02): el sufijo la distingue de la
              ficha, igual que /reporte/:id/editar en el otro dominio. */}
          <Route path="/adoptar/mascota/:id/editar" element={<EditarMascota />} />
          {/* Landings por zona con SEO propio (feature 46): /cali, /armenia, … */}
          {Object.entries(SLUGS_ZONA).map(([slug, zona]) => (
            <Route key={slug} path={`/${slug}`} element={<ZonaLanding zona={zona} />} />
          ))}
        </Route>
      </Routes>
    </div>
  );
}

export default App;

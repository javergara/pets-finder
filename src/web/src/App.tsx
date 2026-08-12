import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import { LandingEmergencia } from './screens/LandingEmergencia';
import { MapaReportes } from './screens/MapaReportes';
import { Registro } from './screens/Registro';
import { ReportarMascota } from './screens/ReportarMascota';
import { ReporteDetalle } from './screens/ReporteDetalle';
import { Reportes } from './screens/Reportes';

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 text-sm font-medium ${isActive ? 'text-forest' : 'text-muted'}`;

  return (
    <nav className="flex items-center gap-2 border-b border-line bg-surface px-4 py-3">
      <NavLink to="/" className="mr-4 font-display text-xl text-forest">
        Reencuentro
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
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/reporte/:id" element={<ReporteDetalle />} />
          <Route path="/mapa" element={<MapaReportes />} />
        </Route>
      </Routes>
    </div>
  );
}

export default App;

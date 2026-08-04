import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import { RequiereHomeProfile } from './components/RequiereHomeProfile';
import { Apadrinar } from './screens/Apadrinar';
import { Cuestionario } from './screens/Cuestionario';
import { Descubrir } from './screens/Descubrir';
import { Favoritos } from './screens/Favoritos';
import { LandingPublica } from './screens/LandingPublica';
import { Mapa } from './screens/Mapa';
import { MascotaDetalle } from './screens/MascotaDetalle';
import { MensajesMatch } from './screens/MensajesMatch';
import { MensajesSolicitud } from './screens/MensajesSolicitud';
import { MiPerfil } from './screens/MiPerfil';
import { MisMatches } from './screens/MisMatches';
import { PanelRefugio } from './screens/PanelRefugio';
import { PublicarMascota } from './screens/PublicarMascota';
import { Registro } from './screens/Registro';
import { SolicitudDetalle } from './screens/SolicitudDetalle';

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 text-sm font-medium ${isActive ? 'text-forest' : 'text-muted'}`;

  return (
    <nav className="flex items-center gap-2 border-b border-line bg-surface px-4 py-3">
      <span className="mr-4 font-display text-xl text-forest">Adopta</span>
      <NavLink to="/descubrir" className={linkClass}>
        Descubrir
      </NavLink>
      <NavLink to="/favoritos" className={linkClass}>
        Favoritos
      </NavLink>
      <NavLink to="/matches" className={linkClass}>
        Mis matches
      </NavLink>
      <NavLink to="/perfil" className={linkClass}>
        Mi perfil
      </NavLink>
      <NavLink to="/apadrinar" className={linkClass}>
        Apadrinar
      </NavLink>
      <NavLink to="/mapa" className={linkClass}>
        Mapa
      </NavLink>
      <NavLink to="/refugio" className={linkClass}>
        Panel del refugio
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
        <Route path="/" element={<LandingPublica />} />
        <Route element={<AppLayout />}>
          {/* /registro y /cuestionario quedan fuera de RequiereHomeProfile (paso 6):
              envolverlas causaría un ciclo de redirección. */}
          <Route path="/registro" element={<Registro />} />
          <Route path="/cuestionario" element={<Cuestionario />} />
          <Route element={<RequiereHomeProfile />}>
            <Route path="/descubrir" element={<Descubrir />} />
            <Route path="/mascota/:id" element={<MascotaDetalle />} />
            <Route path="/favoritos" element={<Favoritos />} />
            <Route path="/matches" element={<MisMatches />} />
            <Route path="/matches/:matchId/mensajes" element={<MensajesMatch />} />
          </Route>
          <Route path="/perfil" element={<MiPerfil />} />
          {/* /apadrinar queda fuera de RequiereHomeProfile, igual que /perfil: no hay
              razón funcional para exigir el cuestionario de hogar para donar. */}
          <Route path="/apadrinar" element={<Apadrinar />} />
          {/* /mapa queda fuera de RequiereHomeProfile, igual que /apadrinar y /perfil: no
              hay razón funcional para exigir el cuestionario de hogar para ver el mapa. */}
          <Route path="/mapa" element={<Mapa />} />
          {/* /refugio* quedan fuera de RequiereHomeProfile: ese guard es exclusivo del
              lado adoptante (cuestionario de hogar), no aplica a la vista del refugio. */}
          <Route path="/refugio" element={<PanelRefugio />} />
          <Route path="/refugio/publicar" element={<PublicarMascota />} />
          <Route path="/refugio/solicitudes/:matchId" element={<SolicitudDetalle />} />
          <Route path="/refugio/solicitudes/:matchId/mensajes" element={<MensajesSolicitud />} />
        </Route>
      </Routes>
    </div>
  );
}

export default App;

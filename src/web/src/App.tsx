import { Navigate, NavLink, Route, Routes } from 'react-router-dom';
import { Descubrir } from './screens/Descubrir';
import { MascotaDetalle } from './screens/MascotaDetalle';
import { MisMatches } from './screens/MisMatches';

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 text-sm font-medium ${isActive ? 'text-forest' : 'text-muted'}`;

  return (
    <nav className="flex items-center gap-2 border-b border-line bg-surface px-4 py-3">
      <span className="mr-4 font-display text-xl text-forest">Adopta</span>
      <NavLink to="/descubrir" className={linkClass}>
        Descubrir
      </NavLink>
      <NavLink to="/matches" className={linkClass}>
        Mis matches
      </NavLink>
    </nav>
  );
}

function App() {
  return (
    <div className="min-h-svh bg-bg">
      <Nav />
      <Routes>
        <Route path="/" element={<Navigate to="/descubrir" replace />} />
        <Route path="/descubrir" element={<Descubrir />} />
        <Route path="/mascota/:id" element={<MascotaDetalle />} />
        <Route path="/matches" element={<MisMatches />} />
      </Routes>
    </div>
  );
}

export default App;

export type UserProfile = {
  id: number;
  nombre: string;
  email: string;
  ciudad: string;
  barrio: string | null;
  lat: number | null;
  lng: number | null;
  avatar_url: string | null;
  bio: string | null;
  creado_en: string;
};

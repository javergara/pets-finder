// Sin autenticación real en el MVP (ver docs/architecture.md §6).
// Debe coincidir con DEMO_USER_ID de scripts/seed.py (Ana Martínez, id=1).
export const DEMO_USER_ID = 1;

// El diseño (design/screens/panel-refugio.md) no contempla un flujo de registro
// de refugios: son cuentas verificadas preexistentes (Shelter.verificado), no
// self-service. Mismo patrón que DEMO_USER_ID: refugio índice 0 del seed
// (scripts/seed.py, "Refugio Huellas de Bogotá", primer insertado -> id=1),
// con varias mascotas sembradas para poder demostrar el panel con datos reales.
export const DEMO_SHELTER_ID = 1;

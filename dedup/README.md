# Dedup — sistema de duplicados de Pet Finder Col

Sistema propio, aparte del crawler: los duplicados son un problema de la
plataforma (la gente publica dos veces, el mismo caso circula por varias
páginas, cada pipeline puede re-importarlo). Aquí vive la lógica una sola vez;
el crawler la importa para su chequeo de publish y cualquier pipeline nueva
puede hacer lo mismo.

## Principio de diseño

**El teléfono identifica a la persona, no al caso**: una familia pierde varias
mascotas y un rescatista encuentra muchas. Por eso es llave de candidatos,
nunca veredicto — tipo+especie acotan, el nombre discrimina (nombres distintos
con el mismo teléfono = dos mascotas del mismo dueño), y con la asimetría de
costos a favor de no perder casos: un duplicado publicado es ruido; un caso
real borrado es una mascota que nadie busca.

## Uso

```bash
# Informe de toda la instancia (solo lectura)
PETFINDER_API_URL=... python -m dedup.cli --json informe.json

# Curación: borra SOLO copias crawl propias marcadas 'casi seguro'
PETFINDER_API_URL=... CRAWLER_USER_ID=... python -m dedup.cli --aplicar
```

- Clusters por caso (teléfono+tipo+especie+nombre); canónico = el manual (lo
  escribió la familia) o el más antiguo.
- `--aplicar` solo elimina sobrantes "casi seguro" que sean del usuario del
  crawler — lo único que sus herramientas de autor alcanzan. Los duplicados
  manuales y todos los "posibles" quedan en revisión humana siempre.

## Juez LLM (pares ambiguos)

Para los sobrantes en revisión humana, `--juez` pide la opinión de un modelo
pequeño y rápido (default **GPT-5.6 Luna**, configurable con
`DEDUP_JUEZ_MODELO`; requiere `OPENAI_API_KEY`): compara señas y fotos del par
y responde si es el mismo animal o dos animales de la misma persona. El
veredicto **anota y ordena** la cola de revisión en el informe — no borra nada.

```bash
PETFINDER_API_URL=... OPENAI_API_KEY=... python -m dedup.cli --juez --json informe.json
```

## Fusión (merge)

Cuando el juez dicta "mismo caso" con confianza ≥ 0.8, `--fusionar` aplica el
merge y elimina el duplicado (con respaldo del JSON completo):

- **Canónico crawl propio** → se aplica la versión combinada que redactó el
  juez (descripción con todas las señas, campos completados).
- **Canónico manual** → solo con `--incluir-manuales`: fusión **determinista**
  — lo que escribió la familia queda intacto y la descripción del duplicado se
  añade marcada como "señas adicionales"; solo se llenan campos vacíos. Nunca
  prosa del LLM en un reporte ajeno. Editar como el autor usa el modelo de
  confianza del MVP: correrlo contra prod solo con el ok del dueño.

## Mapa

- `deteccion.py` — núcleo puro (candidatos, clusters, plan de curación).
- `cli.py` — auditoría + informe + juez opcional + curación acotada.
- `juez.py` — veredicto LLM por par (señas + fotos), sin SDK: REST directo.
- Tests en `tests/dedup/` (suite normal, sin red).

# Ejemplos — calibración real del pipeline visual

## `calibracion.json`

Salida de `python -m embeddings.calibrar` sobre **las fotos reales de los
reportes de producción**, leídas del API público (solo lectura; nada se
escribió). Es la evidencia del acceptance 2 de la feature 24 — *"el ranking
mejora demostrablemente los casos de prueba definidos antes de implementar"* —
y el punto de comparación para detectar regresiones.

**Cómo leerlo.** Los umbrales de `services/coincidencias.py` deben quedar por
**encima** del `p99` de `linea_base_negativos` (pares de la misma especie entre
reportes distintos: casi todos animales distintos) y por **debajo** del `p10`
de `control_positivo` (la misma foto recortada, rotada, oscurecida, espejada y
recomprimida). Si esas dos distribuciones se tocan, el pipeline no separa y la
feature no debe salir.

## Cuándo hay que regenerarlo

**Siempre que cambie `PIPELINE`** en `embeddings/modelo.py`: otro detector, otro
embedder, otro umbral de detección o de margen de recorte producen un espacio
vectorial distinto y unos umbrales que ya no aplican.

```bash
SUPABASE_URL=https://<proyecto>.supabase.co \
  python -m embeddings.calibrar --salida embeddings/ejemplos/calibracion.json
```

## El hallazgo que justificó el recorte

La primera calibración se hizo **sin** recortar al animal y los números parecían
aceptables, pero el par más similar de toda la base era una perra dorada contra
un perro crema: el vector estaba describiendo la maqueta del póster
("¡SE PERDIÓ!" con banda roja) y el chrome de los pantallazos de story, no la
mascota. Con el recorte previo ese falso positivo cayó de **0.885 a 0.461** y el
verdadero positivo se mantuvo en **0.997**.

Por eso el pipeline tiene dos etapas y por eso esta calibración se corre sobre
fotos reales de producción y no sobre un dataset limpio: las fotos de una
emergencia son pósters, pantallazos y capturas de WhatsApp.

> Sin fotos en el repo: el script las descarga del bucket público al vuelo y no
> las guarda. Aquí solo viven los números.

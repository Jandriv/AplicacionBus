## Puesta en funcionamiento
El proyecto depende de tener una api [api-auvasa](https://www.auvasa.es/datos-abiertos/) disponible a la que consultar. Durante el desarrollo se hizo con una ejecucion local en [docker](https://github.com/VallaBus/api-auvasa?tab=readme-ov-file#despliegue-en-producci%C3%B3n).

La parada y las líneas a consultar se configuran en `app_config.json`:

```json
{
	"parada_actual": "625",
	"lineas_a_probar": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C1", "C2", "H"]
}
```

`parada_actual` es el código de parada (puedes consultarlo en [el mapa oficial de auvasa](https://www.auvasa.es/mapa-de-servicios/)).

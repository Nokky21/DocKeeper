<!--
Plantilla DocKeeper · README de un PAQUETE (monorepo o repositorio con varias piezas)
Va en la carpeta del paquete (junto a su manifiesto). Para quién: quien llega a este paquete desde el
mapa de la raíz y necesita saber qué hace, cómo se usa y qué rompe si lo cambia.
Reglas:
- Cada afirmación verificable lleva su ancla: [[ruta/al/fichero.ext#Simbolo]] (preferida) o
  [[ruta/al/fichero.ext:N]]. Rutas relativas a la RAÍZ del repositorio, no del paquete.
- Lo que es común a todo el repositorio va en la raíz (README, ARQUITECTURA, DECISIONES): aquí solo
  se enlaza.
- No copies código del repositorio en bloques; lo que no sepas, «No consta».
Borra este comentario al rellenar.
-->

# nombre-del-paquete

Una frase: qué hace este paquete y quién lo usa (otro paquete, un servicio, una persona).

## Punto de entrada

Por dónde entra la ejecución o qué exporta: [[ruta/al/paquete/src/index.ext#Simbolo]]

## Qué ofrece

Funciones, rutas, comandos o componentes públicos, uno por línea, con su ancla y una frase sobre su
contrato (entrada, salida, errores):

- `nombre` — qué hace. [[ruta/al/paquete/src/modulo.ext#nombre]]

## Depende de / lo usan

- Depende de: otros paquetes del repositorio y servicios externos, según su manifiesto.
  [[ruta/al/paquete/manifiesto:N]]
- Lo usan: qué paquetes lo importan (busca su nombre en los manifiestos del resto).

## Configuración

Variables o ficheros que lee, con su valor por defecto y ancla al código que los lee. Sin secretos
reales.

## Desarrollar y probar

Comandos exactos de este paquete (desde la raíz o desde su carpeta), con ancla al script que los
define.

## Límites

Qué no hace, qué se sabe que falla. «No consta» si no se sabe.

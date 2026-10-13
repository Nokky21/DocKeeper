<!--
Plantilla DocKeeper · README
Para quién: alguien que llega al repositorio y quiere saber qué es, si le sirve y cómo arrancarlo.
Reglas:
- Cada afirmación verificable lleva su ancla: [[ruta/al/fichero.ext#Simbolo]] (preferida) o
  [[ruta/al/fichero.ext:N]]. Si el README se publica y su código es privado, nada de anclas:
  usa `dockeeper link README.md:N ruta#Simbolo`.
- No copies código del repositorio en bloques: descríbelo o escribe un ejemplo propio.
- Lo que no sepas, no lo inventes: escribe «No consta».
Borra este comentario al rellenar.
-->

# Nombre del proyecto

Una frase: qué hace y para quién.

## Qué resuelve

El problema concreto, en dos o tres frases. Sin promesas que el código no cumpla.

## Cómo funciona (en una vuelta)

Recorrido de una petición, un comando o un dato desde que entra hasta que sale, con un ancla por
paso:

1. Entra por … [[ruta/al/fichero.ext#Simbolo]]
2. Se valida en … [[ruta/al/fichero.ext#Simbolo]]
3. Se guarda / se responde en … [[ruta/al/fichero.ext#Simbolo]]

## Arrancar

Requisitos (versiones exactas, de dónde salen) y los comandos mínimos para ejecutarlo y para pasar
las pruebas. Ancla al fichero que define cada comando (scripts, Makefile, manifiesto).

## Configuración

Qué variables o ficheros de configuración existen, qué hace cada una y su valor por defecto, con
ancla al código que la lee. Nunca valores reales de secretos.

## Estado y límites

Qué funciona, qué no, y qué se sabe que falla. «No consta» si no se sabe.

## Más documentación

- Arquitectura: ARQUITECTURA.md
- Decisiones: DECISIONES.md
- Procedimientos: PROCEDIMIENTOS.md
- API: API.md
- Incorporación: INCORPORACION.md

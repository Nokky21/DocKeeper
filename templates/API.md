<!--
Plantilla DocKeeper · API
Para quién: quien llama a la API (o a la biblioteca) y necesita el contrato exacto.
Reglas:
- Un ancla por operación a su manejador y otra a su validación de entrada.
- Los ejemplos se escriben a mano: si se copian del código, `dockeeper check` los marca como
  CODIGO_COPIADO en documentos publicados.
- Si la API es pública y su código privado, clase «publico»: usa `dockeeper link` en vez de anclas.
Borra este comentario al rellenar.
-->

# API

## Convenciones

Autenticación, versionado, formato de errores, paginación y límites, con ancla a dónde se aplica
cada uno. [[ruta/al/fichero.ext#Simbolo]]

## Operaciones

### MÉTODO /ruta (o nombreDeFuncion)

Qué hace, en una frase. [[ruta/al/manejador.ext#Simbolo]]

- **Permisos:** quién puede llamarla. [[ruta/al/guardia.ext#Simbolo]]
- **Entrada:** campos, tipos, obligatorios y límites. [[ruta/al/validacion.ext#Simbolo]]
- **Salida:** forma de la respuesta.
- **Errores:** códigos y cuándo salen.
- **Efectos:** qué cambia (datos, eventos, llamadas externas) y si es idempotente.

Ejemplo (escrito a mano):

```
petición y respuesta de ejemplo
```

(Repite por operación.)

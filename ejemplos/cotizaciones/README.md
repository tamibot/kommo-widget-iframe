# Ejemplo: Cotizaciones (y su versión «Tratamientos»)

Un lead de Kommo tiene un solo valor de venta. Este widget permite **varias cotizaciones o tratamientos
por cliente**, cada uno con su estado, monto y seguimiento, sin perder las propuestas anteriores.

## Qué ve el usuario

| Dónde | Qué |
|---|---|
| *Ajustes → Integraciones → Cotizaciones* | Lista con búsqueda y filtros. Una fila = un producto o tratamiento. Estado, monto y próxima fecha se cambian desde la lista |
| Ficha del lead | Las cotizaciones de ese cliente, con el historial de cambios de cada una |
| Reportes | Volumen por mes, estado, producto y nivel de interés; importes por moneda (venta cotizada, no pagos) |
| Excel | Descarga con la base completa y una hoja por tabla |
| **Sincronizar** | Trae de Kommo lo cambiado en las últimas 24 h, por si un aviso no llegó |

## Cómo guarda los datos

- Cada cotización es un **elemento de la lista de Kommo** «Cotizaciones», enlazado al lead. En Kommo
  queda visible aunque el widget no esté.
- El servidor guarda además su propia tabla, con historial de cambios y estado de sincronización
  (`pendiente`, `ok` o `error`). Si Kommo no responde, nada se pierde: queda pendiente y se reintenta
  en lotes por el limitador.
- **Eliminar** no borra: oculta la fila, conserva el historial y la desenlaza del lead en Kommo.

## La versión «Tratamientos»: una vista a la medida de un cliente

Para una clínica, la misma base se mostró como **sus propias tablas de Excel**, en pestañas: «tal vez»,
«sí», «no», «espera de resultados», todos, pacientes y reportes. También tiene filtro por sede y una ficha
del paciente con todos sus tratamientos. Lo que funcionó:

- **Cargar todo de una vez** (unas 1.100 filas, unos 100 KB comprimidos) y filtrar en el navegador. Las
  pestañas cambian al instante.
- **Una fila = un tratamiento.** El primero sale de una pestaña de la ficha de Kommo y es de solo
  lectura (se edita en Kommo). Los siguientes se agregan desde el widget.
- **Avisos en «Por revisar»:** datos incompletos o contradictorios, y pacientes repetidos con el mismo
  nombre y teléfono. Un botón **«Quedarme con…»** une dos leads: copia los datos que faltan, pasa los
  tratamientos y archiva el otro. Lo decide una persona, nunca solo el teléfono.
- **Aviso de «posible duplicado»** al registrar un tratamiento de la misma dolencia con fecha cercana.
- **El Excel replica columna por columna el Sheet que ya usaba la clínica.** Las columnas nuevas van al
  final, para no romper sus tablas dinámicas.
- **Un portal con usuario y contraseña** para abrir la misma vista sin entrar a Kommo.

## Lecciones de este widget

- **Releer los 10.000 leads cada vez que alguien abría el widget costaba unos 6 s de CPU** y volvía
  lenta la vista para todos. La mejora: actualizar solo al paciente que cambió, desde el webhook, y
  dejar la relectura completa como respaldo.
- **Los leads borrados o fusionados en Kommo deben salir de la copia.** Si no, aparecen en tablas y
  descargas aunque en Kommo no existan.
- **Los campos que pide el cliente se definen antes de crearlos.** En Kommo un campo no cambia de tipo:
  lista o texto libre se decide una vez.
- **El Excel lleva una hoja «CÓMO USAR».** Ahí se explica de dónde sale cada dato, a qué hora se
  actualiza el Sheet y qué hacer si algo no aparece.

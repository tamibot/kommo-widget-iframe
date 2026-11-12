---
title: 10. Lecciones aprendidas
---

# 10. Lecciones aprendidas

Cosas que pasaron en producción con un widget de este tipo y cómo quedaron resueltas en el kit.

## Datos
- **Un lead fusionado seguía apareciendo.** Al fusionar dos leads, Kommo borra uno. Si no procesas
  `leads[delete]`, tu copia guarda «fantasmas» que el cliente ve en tablas y descargas, pero no
  encuentra en Kommo. → El webhook de borrado confirma con un GET y lo saca.
- **Mismo teléfono no significa misma persona.** Madre e hija, o un familiar que agenda por otro,
  comparten número. Nunca unas ni archives leads solo por teléfono. Avisa y que decida una persona.
- **Una limpieza automática apagada sigue «existiendo» en lo que dijiste.** Si apagas un proceso,
  corrige también la guía y lo que le dijiste al cliente.
- **Las fechas de Kommo vienen en segundos UTC.** Conviértelas a la zona del cliente antes de agrupar
  por día, o los leads de la noche caen al día siguiente.

## Excel y Sheets
- **«No me salen los leads de hoy»** casi nunca es el servidor: la tabla dinámica del cliente lee hasta
  una fila fija y los leads nuevos quedan al final, fuera del rango. Explícalo en la hoja de ayuda del
  Excel.
- **Las columnas nuevas, al final.** Si insertas una en el medio, se rompen las tablas dinámicas del
  cliente.
- **Años y teléfonos como texto.** Si no, Excel convierte «2026» en una fecha de 1905 y se pierden los
  ceros.
- **La cuota de Google Sheets se comparte.** Dos flujos leyendo el mismo Sheet al mismo minuto chocan.
  Separa los horarios.

## Servidor
- **Reiniciar en horario laboral pierde avisos.** Despliega de noche y nunca con una exportación en
  curso.
- **Releer todo en cada apertura vuelve lenta la vista.** Mientras corre la relectura completa, las
  demás respuestas tardan hasta 4 veces más.
- **Pon un tope de memoria al contenedor** y mide el pico real (`memory.peak`). Un Excel grande dispara
  la memoria y el kernel mata el proceso sin aviso.
- **Git dentro de iCloud o Dropbox se cuelga.** El repositorio va en una carpeta local.

## Con el cliente
- **Verifica tú, no le pidas al cliente que pruebe.** Reproduce con sus filtros y sus datos antes de
  decir «listo».
- **Mensajes cortos y sin jerga.** Qué pasó, qué se corrigió y qué tiene que hacer él, si algo.
- **Si te equivocaste en algo que le dijiste, corrígelo en el mismo canal.**

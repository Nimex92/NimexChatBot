# Historial de Cambios

## Versión Actual

### ✨ Nuevas Funcionalidades

#### 1. Módulo de Debate Diario
- **Debate Automático:** Cada día a las 00:00, el bot propondrá un nuevo tema de debate y lo anclará en el grupo para fomentar la conversación.
- **Limpieza Automática:** El debate del día anterior se desanclará automáticamente a las 23:59.
- **Comando Manual:** Se ha añadido el comando `/debate` para que los administradores puedan forzar la creación de un nuevo debate en cualquier momento.

#### 2. Sistema de Niveles: "La Senda del Riojano"
- **Progresión por Actividad:** Los usuarios ahora ganan experiencia (XP) al participar en el chat (con un cooldown para evitar spam).
- **Niveles Temáticos:** Se ha introducido un sistema de 12 niveles con temática riojana, desde "Turista en la Laurel" hasta "San Mateo".
- **Anuncios de Nivel:** El bot anunciará públicamente cuando un usuario suba de nivel, ¡dándole su merecido reconocimiento!
- **Comando de Progreso:** Los usuarios pueden usar el nuevo comando `/nivel` para consultar su rango actual y su progreso hacia el siguiente nivel en un mensaje privado.

### 🐞 Corrección de Errores
- Se ha solucionado un error en el comando `/start` que provocaba un fallo debido a caracteres no escapados en el mensaje de bienvenida (`MarkdownV2`).

/*
 * Every user-visible string in the app (1.5, constraint 23). Components hold no
 * string literals. KD-17: the backend emits machine codes only and its
 * `message` field is never displayed — the map from code to Spanish lives here.
 *
 * Copy is carried from the approved mockups. Tone: patient, not apologetic. No
 * "still working", no apology, no celebration.
 */

export const nav = {
  finanzas: 'Finanzas',
  diario: 'Diario',
  gimnasio: 'Gimnasio',
  pronto: 'pronto',
} as const

export const tabs = {
  hoy: 'Hoy',
  mes: 'Este mes',
  // A40: the user's own word for this list, used verbatim as the tab label.
  historial: 'Historial',
  analisis: 'Análisis',
  todo: 'Todo',
  porFecha: 'Por fecha',
} as const

export const capture = {
  anotarGasto: 'Anotar gasto',
  escribir: 'Escribir',
  grabarVoz: 'Grabar con la voz',
} as const

export const common = {
  ajustes: 'Ajustes',
  cancelar: 'Cancelar',
  guardar: 'Guardar',
  cerrar: 'Cerrar',
  reintentar: 'Reintentar',
  editar: 'Editar',
  volver: 'Volver',
  cargando: 'Cargando…',
} as const

export const hoy = {
  gastosContados: (n: number) =>
    n === 1 ? '1 gasto anotado hoy' : `${n} gastos anotados hoy`,
  vacioTitulo: 'Todavía no has anotado nada hoy.',
  vacioCuerpo:
    'Puedes escribirlo con el botón de abajo, o decirlo en voz alta mientras caminas.',
} as const

export const mes = {
  enQueSeFue: 'En qué se fue',
  comoSePago: 'Cómo se pagó',
  gastosContados: (n: number) => (n === 1 ? '1 gasto' : `${n} gastos`),
  mesAnterior: 'Mes anterior',
  mesSiguiente: 'Mes siguiente',
  vacioTitulo: (mesNombre: string) => `En ${mesNombre} no hay gastos anotados.`,
  vacioCuerpo:
    'Cuando anotes el primero, aquí verás en qué se fue el mes y cómo lo pagaste.',
  // 18.10 / constraint 42. The name is absent only for an id that names no
  // category the app can see — an unknown id, or an archived one with nothing
  // in the viewed month. Then the sentence says "esa categoría" rather than
  // inventing a name.
  categoriaVaciaTitulo: (mesNombre: string, categoria: string | null) =>
    categoria
      ? `En ${mesNombre} ya no queda nada en ${categoria}.`
      : `En ${mesNombre} ya no queda nada en esa categoría.`,
  categoriaVaciaCuerpo:
    'Puede que lo hayas borrado o que lo hayas pasado a otra categoría. El resto del mes sigue completo.',
} as const

/**
 * 16.6 / constraint 31: the ordering statement is one line, stating the order
 * and pre-empting the "these dates are broken" reading in the same breath. No
 * count readout — "mostrando 50 de 431" is on the visual brief's Avoid list.
 */
export const historial = {
  orden: 'En el orden en que los anotaste, no por su fecha.',
  verMas: 'Ver gastos más antiguos',
  vacioTitulo: 'Todavía no has anotado ningún gasto.',
  vacioCuerpo: 'Cuando anotes el primero, aquí van quedando todos, del último al primero.',
} as const

/**
 * The read-only detail (17.2-17.6, 17.11). The two timestamps are footnote
 * prose rather than rows in the facts list: constraint 37 forbids the dated-for
 * date and the recorded moment reading as one value or a range, and stacking
 * them as adjacent rows is the arrangement that invites exactly that.
 */
export const gastoDetalle = {
  titulo: 'Gasto',
  metodo: 'Método de pago',
  fechaGasto: 'Fecha del gasto',
  anotado: (cuando: string) => `Anotado el ${cuando}.`,
  // 17.5 / constraint 38: a fact about the record, in the same ink and the same
  // size as "Anotado el…". The timestamp is what lets a surprising mark be
  // reconciled against "oh, that was when I opened it yesterday" (R3).
  editado: (cuando: string) => `Editado el ${cuando}.`,
  noExisteTitulo: 'Este gasto ya no existe.',
  noExisteCuerpo:
    'Puede que lo hayas borrado desde otra pantalla. En la lista está todo lo que sí tienes anotado.',
} as const

export const gasto = {
  nuevo: 'Nuevo gasto',
  editar: 'Editar gasto',
  revisar: 'Revisar gasto',
  monto: 'Monto',
  categoria: 'Categoría',
  metodoPago: 'Método de pago',
  fecha: 'Fecha',
  descripcion: 'Descripción',
  opcional: '(opcional)',
  descripcionPlaceholder: 'Para acordarte después',
  guardarGasto: 'Guardar gasto',
  guardarCambios: 'Guardar cambios',
  guardando: 'Guardando…',
  seGuardaAqui: 'Se guarda en tu computador.',
  eliminarGasto: 'Eliminar gasto',
  nueva: 'Nueva',
  nuevo_: 'Nuevo',
  nuevaCategoria: 'Nombre de la categoría',
  nuevoMetodo: 'Nombre del método de pago',
  crearYElegir: 'Crear y elegir',
  seQuedaComoEsta: 'Lo que ya escribiste se queda como está.',
  hoyEs: (fecha: string) => `Hoy, ${fecha}`,
  cambiarFecha: 'Cambiar',
  // 9.2: one phrase family for "the voice pass could not determine this",
  // said in the gender of the field and the verb of its control — the amount
  // is written, the category and the method are chosen.
  faltaEscribirlo: 'Falta escribirlo',
  faltaElegirla: 'Falta elegirla',
  faltaElegirlo: 'Falta elegirlo',
  sugerido: 'sugerido',
  escuche: 'Esto fue lo que escuché',
  grabarOtraVez: 'Grabar otra vez',
  nadaSeGuarda: 'Nada se guarda hasta que toques Guardar.',
  descripcionRecortada:
    'La descripción guarda 1.000 caracteres y lo que dijiste es más largo. Se recortó al final de una palabra. Arriba está completo si quieres reescribirlo.',
  confirmarTitulo: '¿Eliminar este gasto?',
  confirmarCuerpo:
    'Deja de contar en el total de hoy y en el del mes. No se puede deshacer.',
  eliminar: 'Eliminar',
} as const

export const diario = {
  escribir: 'Escribir',
  revisarEntrada: 'Revisar entrada',
  placeholder: 'Lo que estés pensando…',
  ayuda:
    'Se guarda con la fecha y la hora de ahora. Los saltos de línea se respetan tal cual.',
  seguirLeyendo: 'Seguir leyendo',
  vacioTitulo: 'El diario está vacío.',
  vacioCuerpo:
    'Escribe lo que estés pensando. No hace falta título, ni categoría, ni ánimo del día: solo el texto.',
  fechaVaciaTitulo: (fecha: string) => `No escribiste nada el ${fecha}.`,
  fechaVaciaCuerpo:
    'Puedes moverte a otro día con las flechas, o volver a todas las entradas.',
  diaAnterior: 'Día anterior',
  diaSiguiente: 'Día siguiente',
  eliminarEntrada: 'Eliminar entrada',
  confirmarTitulo: '¿Eliminar esta entrada?',
  confirmarCuerpo: 'El texto se borra del diario. No se puede deshacer.',
  sonTusPalabras:
    'Son tus palabras, sin corregir ni resumir. Puedes editarlas antes de guardar.',
  cargarMas: 'Ver entradas más antiguas',
} as const

export const voz = {
  gastoPorVoz: 'Gasto por voz',
  entradaPorVoz: 'Entrada por voz',
  preguntaPorVoz: 'Pregunta por voz',
  escuchando: 'Te estoy escuchando',
  maximo: 'máximo 30 segundos',
  listo: 'Listo',
  pasandoATexto: 'Pasando tu voz a texto',
  transcribiendo: 'Transcribiendo en tu computador',
  preparando: 'Preparando el audio',
  enviando: 'Enviando al computador',
  local:
    'Esto ocurre en tu propio computador, no en internet. Con un mensaje corto suele tardar entre 7 y 15 segundos.',
  escribirAMano: 'Escribir a mano',
  escribirGastoAMano: 'Escribir el gasto a mano',
  segundos: 'segundos',
  falloTitulo: 'No entendí lo que dijiste.',
  falloCuerpo:
    'El audio llegó, pero salió vacío. Suele pasar cuando hay mucho ruido alrededor o el micrófono quedó tapado. No se guardó nada.',
  falloNota:
    'Si pasa siempre: la transcripción corre en tu computador y puede estar apagada. Lo ves en Ajustes → Tu servidor.',
  falloTimeout:
    'Tu computador tardó demasiado en pasarlo a texto y lo detuve. No se guardó nada.',
  falloLargo: 'La grabación es más larga de lo que puedo procesar. Prueba con algo más corto.',
  falloAudio: 'El audio no salió como esperaba. Intenta grabar otra vez, más cerca del micrófono.',
  sinPermisoTitulo: 'El navegador no me deja usar el micrófono.',
  sinPermisoCuerpo:
    'El permiso está bloqueado para esta dirección. Puedes cambiarlo en los ajustes del navegador, en Permisos del sitio.',
  sinPermisoManual: 'Mientras tanto, anotar a mano funciona igual que siempre.',
  sinMicrofonoTitulo: 'Este teléfono no me deja grabar aquí.',
  sinMicrofonoCuerpo:
    'El navegador no ofrece grabación en esta dirección. Anotar a mano funciona igual que siempre.',
} as const

export const analisis = {
  resumenDe: (periodo: string) => `Resumen de ${periodo}`,
  escritoEl: (cuando: string) => `Escrito el ${cuando}`,
  empezoALas: (cuando: string) => `Empezó a las ${cuando}`,
  ultimoIntento: (cuando: string) => `Último intento: ${cuando}`,
  sinResumenTitulo: 'Todavía no hay ningún resumen.',
  sinResumenCuerpo:
    'El primero se escribe solo cuando termine el mes. No tienes que pedirlo ni esperarlo aquí.',
  escribiendoResumen: (periodo: string) => `Escribiendo el resumen de ${periodo}`,
  escribiendoCuerpo:
    'Lo está escribiendo tu computador, sin que tengas que esperar aquí. Puedes cerrar la app: cuando vuelvas, estará listo.',
  periodoVacioTitulo: (periodo: string) =>
    `${periodo[0].toUpperCase()}${periodo.slice(1)} no tiene nada anotado.`,
  periodoVacioCuerpo:
    'Sin gastos y sin entradas de diario no hay resumen que escribir. El del mes en curso se intentará cuando termine.',
  resumenFalloTitulo: (periodo: string) => `El resumen de ${periodo} no se pudo escribir.`,
  resumenFalloCuerpo:
    'El modelo de texto de tu computador no respondió. Tus gastos y tu diario de ese mes están completos; lo único que falta es el texto del resumen.',
  resumenFalloNota: 'Puedes revisar si el modelo está encendido en Ajustes → Tu servidor.',
  hazUnaPregunta: 'Haz una pregunta',
  preguntaPlaceholder: '¿En qué gasté más en julio?',
  preguntaNoDisponible: 'No disponible ahora mismo',
  preguntaAyuda:
    'Responde solo con lo que tú has anotado. La respuesta la escribe tu computador y suele tardar cerca de un minuto.',
  preguntar: 'Preguntar',
  preguntarConVoz: 'Preguntar con la voz',
  pensando: 'Pensándolo en tu computador',
  esperaCuerpo:
    'Suele tardar alrededor de un minuto. Puedes irte de esta pantalla; cancelar no borra nada de lo que tienes guardado.',
  cancelarPregunta: 'Cancelar la pregunta',
  periodo: 'Periodo',
  entradasLeidas: 'Entradas leídas',
  tardo: 'Tardó',
  deN: (usadas: number, total: number) => `${usadas} de ${total}`,
  truncado: (usadas: number, total: number) =>
    `Leí ${usadas} de las ${total} entradas del periodo. No cupieron todas, así que esta respuesta no cubre el periodo completo.`,
  periodoAsumido: (periodo: string) =>
    `No dijiste de qué periodo, así que respondí sobre ${periodo}, el mes en curso.`,
  ocupadoTitulo: 'Ya hay una pregunta en curso.',
  ocupadoCuerpo: (pregunta: string) =>
    `Tu computador está respondiendo “${pregunta}”. Puede con una a la vez.`,
  ocupadoCuerpoSinTexto:
    'Tu computador ya está respondiendo otra pregunta. Puede con una a la vez.',
  cancelarEsa: 'Cancelar esa y hacer la mía',
  esperar: 'Esperar a que termine',
  iaNoDisponibleTitulo: 'El modelo de texto de tu computador no responde.',
  iaNoDisponibleCuerpo:
    'No se pueden hacer preguntas ni escribir resúmenes ahora mismo. Anotar gastos, escribir en el diario y ver tus totales funciona igual que siempre.',
  verEstadoServidor: 'Ver el estado del servidor',
  sinResponder: 'Sin responder todavía.',
} as const

export const ajustes = {
  titulo: 'Ajustes',
  categorias: 'Categorías',
  metodosPago: 'Métodos de pago',
  tuServidor: 'Tu servidor',
  copiaSeguridad: 'Copia de seguridad',
  transcripcion: 'Transcripción',
  modeloTexto: 'Modelo de texto',
  disponible: 'disponible',
  noDisponible: 'no disponible',
  exportarTodo: 'Exportar todo',
  exportarAyuda:
    'Descarga un archivo con todo lo que tienes guardado: gastos, diario, categorías y métodos de pago. Se lee en cualquier editor de texto.',
  nuevaCategoria: 'Nueva categoría',
  nuevoMetodo: 'Nuevo método',
  enNGastos: (n: number) => (n === 1 ? 'en 1 gasto' : `en ${n} gastos`),
  sinUsar: 'sin usar todavía',
  nombre: 'Nombre',
  quitarDeLaLista: 'Quitar de la lista',
  quitarTitulo: (nombre: string, n: number) =>
    n === 1 ? `“${nombre}” está en 1 gasto.` : `“${nombre}” está en ${n} gastos.`,
  quitarCuerpo: (nombre: string, n: number) =>
    n === 1
      ? `Ese gasto se queda como está y sigue contando en los totales, con el nombre “${nombre}”. Lo único que cambia es que ya no vas a poder elegirlo al anotar.`
      : `Esos ${n} gastos se quedan como están y siguen contando en los totales, con el nombre “${nombre}”. Lo único que cambia es que ya no vas a poder elegirlo al anotar.`,
  quitarSinUsoTitulo: (nombre: string) => `¿Quitar “${nombre}” de la lista?`,
  quitarSinUsoCuerpo: 'No está en ningún gasto. Deja de aparecer al anotar.',
  guardarNombre: 'Guardar nombre',
} as const

export const gimnasio = {
  titulo: 'Todavía no está disponible.',
  cuerpo:
    'Este espacio queda reservado para el gimnasio. Por ahora no hay nada que anotar aquí.',
} as const

export const servidor = {
  titulo: 'No puedo alcanzar tu servidor.',
  cuerpo1:
    'Tu teléfono no encuentra el computador donde vive Autonom-OS. Casi siempre es que el computador está suspendido o apagado.',
  cuerpo2: 'Lo que ya guardaste está a salvo allá. No se pierde nada por esperar.',
  abrirCasa: 'Abrir la versión de casa',
  // Offered from the LAN origin: the everyday one, which works on any network.
  abrirSiempre: 'Abrir la versión de siempre',
  casaAyuda:
    'La versión de casa funciona cuando el teléfono y el computador están en el mismo wifi, aunque no haya internet.',
  siempreAyuda:
    'La versión de siempre funciona desde cualquier red, mientras el computador esté encendido.',
  bannerTitulo: 'No alcanzo tu servidor.',
  bannerCuerpo:
    'Lo que ves puede estar desactualizado y no se puede guardar nada nuevo hasta que vuelva. Se reconecta solo.',
  verQueHacer: 'Ver qué hacer',
  guardarFalloTitulo: 'No pude guardar: no alcanzo tu servidor.',
  guardarFalloCuerpo:
    'Nada se perdió. Lo que escribiste sigue aquí tal como está; vuelve a intentarlo cuando el computador esté despierto.',
  // QA D2/D3: ONE request failing while the server itself keeps answering. This
  // is deliberately not 16.10's or 18.10's copy: those state a fact about the
  // data ("no has anotado nada", "ya no queda nada en Transporte"), and a
  // request that failed knows nothing about the data. It is not the unreachable
  // banner either — `ListFailure` renders nothing when the server is out of
  // reach, so the first sentence is true whenever this is on screen.
  listaFalloTitulo: 'No pude cargar esta lista.',
  listaFalloCuerpo:
    'Tu servidor está respondiendo, pero esta lista no llegó. Lo que anotaste sigue guardado.',
} as const

/**
 * KD-17: the closed error-code set, each mapped to Spanish. Nothing outside this
 * map can reach the screen.
 */
export const errores: Record<string, string> = {
  validation: 'Revisa los campos marcados.',
  not_found: 'Eso ya no existe. Puede que lo hayas borrado desde otra pantalla.',
  conflict: 'Ya tienes uno con ese nombre.',
  in_use: 'Está en uso en gastos que ya anotaste.',
  audio_invalid: 'El audio no llegó en el formato que esperaba. Intenta grabar otra vez.',
  audio_too_long: 'La grabación es más larga de lo que puedo procesar. Prueba con algo más corto.',
  transcription_failed: 'No entendí lo que dijiste. No se guardó nada.',
  transcription_timeout: 'La transcripción tardó demasiado y la detuve. No se guardó nada.',
  llm_unavailable: 'El modelo de texto de tu computador no responde.',
  llm_timeout:
    'Pasaron dos minutos y tu computador seguía escribiendo, así que lo detuve. Una pregunta más corta suele salir.',
  insufficient_data: 'Todavía hay muy poco anotado de ese periodo para decir algo que sirva.',
  unverifiable_figures:
    'No puedo responder eso con lo que tienes anotado. Prefiero no darte una cifra antes que darte una inventada.',
  period_unrecognised:
    'No entendí de qué periodo hablas. Prueba nombrando un mes, “este mes” o “el mes pasado”.',
  preempted:
    'La respuesta se detuvo porque empezaste a grabar y la voz va primero. Nada se perdió.',
  busy: 'Ya hay una pregunta en curso.',
  internal: 'Algo se rompió en tu servidor. Vuelve a intentarlo.',
}

/** The action offered alongside a failed question, where one makes sense. */
export const erroresAccion: Record<string, string | undefined> = {
  period_unrecognised: 'Preguntar de otra forma',
  llm_timeout: 'Preguntar otra vez',
  preempted: 'Volver a preguntar',
  unverifiable_figures: undefined,
  insufficient_data: undefined,
  llm_unavailable: undefined,
}

/** `fields[].reason` → Spanish, per field. Reasons are a closed vocabulary. */
const razones: Record<FieldKey, Partial<Record<string, string>>> = {
  amount_cop: {
    required: 'Escribe un monto mayor que cero.',
    must_be_positive: 'Escribe un monto mayor que cero.',
    not_an_integer: 'El monto va en pesos enteros, sin centavos.',
  },
  category_id: {
    required: 'Elige una categoría.',
    unknown_id: 'Esa categoría ya no está en la lista. Elige otra.',
  },
  payment_method_id: {
    required: 'Elige un método de pago.',
    unknown_id: 'Ese método de pago ya no está en la lista. Elige otro.',
  },
  spent_on: {
    future_date: 'No puedes anotar un gasto en una fecha futura.',
  },
  description: {
    too_long: 'La descripción es demasiado larga.',
  },
  text: {
    blank: 'Escribe algo antes de guardar.',
  },
  name: {
    blank: 'Escribe un nombre.',
    too_long: 'El nombre es demasiado largo: máximo 40 caracteres.',
    duplicate_name: 'Ya tienes uno con ese nombre.',
  },
}

type FieldKey =
  | 'amount_cop'
  | 'category_id'
  | 'payment_method_id'
  | 'spent_on'
  | 'description'
  | 'text'
  | 'name'

export function razonEnEspanol(field: string, reason: string): string {
  const porCampo = razones[field as FieldKey]
  return porCampo?.[reason] ?? errores.validation
}

export function errorEnEspanol(code: string): string {
  return errores[code] ?? errores.internal
}

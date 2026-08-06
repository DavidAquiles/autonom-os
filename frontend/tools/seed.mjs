/*
 * Fills the running backend with the sample record the approved mockups depict,
 * so the screenshot matrix is rendered against real API responses rather than
 * fixtures. Development tooling only — not part of the app.
 *
 *   node tools/seed.mjs [http://127.0.0.1:8001]
 */
const BASE = process.argv[2] ?? 'http://127.0.0.1:8001'

async function j(path, init) {
  const res = await fetch(BASE + path, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!res.ok && res.status !== 409) {
    throw new Error(`${init?.method ?? 'GET'} ${path} → ${res.status} ${await res.text()}`)
  }
  return res.status === 204 ? null : res.json()
}

const cats = (await j('/api/categories')).items
const pays = (await j('/api/payment-methods')).items
const cat = (n) => cats.find((c) => c.name === n).id
const pay = (n) => pays.find((p) => p.name === n).id

const health = await j('/api/health')
const today = health.server_time.slice(0, 10)
const [y, m] = today.split('-').map(Number)
const day = (d) => `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`

const existing = await j(`/api/summary/day?date=${today}`)
if (existing.expense_count === 0) {
  const hoy = [
    [6200, 'Comida', 'Nequi', 'Café y pan'],
    [12000, 'Servicios', 'Transferencia', 'Recarga de datos'],
    [23500, 'Comida', 'Efectivo', 'Almuerzo con Ana'],
    [14000, 'Transporte', 'Tarjeta de crédito', 'Uber a la casa'],
  ]
  for (const [amount, c, p, d] of hoy) {
    await j('/api/expenses', {
      method: 'POST',
      body: JSON.stringify({
        amount_cop: amount,
        category_id: cat(c),
        payment_method_id: pay(p),
        description: d,
      }),
    })
  }

  const mes = [
    [412000, 'Mercado', 'Tarjeta débito', 'Mercado del mes', 2],
    [298500, 'Comida', 'Efectivo', 'Almuerzos de la semana', 3],
    [187000, 'Transporte', 'Tarjeta de crédito', 'Uber y buses', 1],
    [154000, 'Servicios', 'Transferencia', 'Internet y luz', 2],
    [96000, 'Hogar', 'Tarjeta de crédito', 'Cosas de aseo', 4],
    [74000, 'Ocio', 'Nequi', 'Cine con Ana', 1],
    [38000, 'Salud', 'Efectivo', 'Farmacia', 3],
    [25000, 'Ropa', 'Tarjeta débito', 'Medias', 2],
  ]
  for (const [amount, c, p, d, dd] of mes) {
    await j('/api/expenses', {
      method: 'POST',
      body: JSON.stringify({
        amount_cop: amount,
        category_id: cat(c),
        payment_method_id: pay(p),
        spent_on: day(dd),
        description: d,
      }),
    })
  }
}

const journal = await j('/api/journal')
if (journal.items.length === 0) {
  const entries = [
    'Dormí mal. Volví a soñar con la mudanza, otra vez con las cajas sin marcar.',
    'Llamé a mi mamá. Está bien, el jardín le está quedando lindo y el limonero por fin dio algo. Me contó lo del vecino con el perro y me reí como no me reía hace rato.',
    'Estuve pensando en por qué me pongo tan tenso los domingos por la tarde. Creo que es la sensación de que la semana ya empezó aunque todavía no, y me la paso adelantándome a cosas que ni siquiera han pasado. Hoy intenté quedarme quieto un rato, sin teléfono, sin lista de pendientes, solo mirando por la ventana, y a los diez minutos ya estaba buscando algo que hacer. No sé si eso se entrena. Ana dice que sí, que es cuestión de aburrirse más seguido, y que el aburrimiento es un músculo que uno deja de usar. Puede ser. Lo que sí sé es que los domingos que salgo a caminar sin destino terminan mejor que los que me quedo en la casa organizando cosas que no hacía falta organizar.',
    'Hoy fue un día raro. Empecé con la sensación de que no iba a rendir nada y terminé sacando adelante todo lo que tenía pendiente. ¿Por qué me cuesta tanto confiar en las mañanas?\n\nMañana quiero levantarme sin revisar el teléfono. A ver cuánto dura.',
  ]
  for (const text of entries) {
    await j('/api/journal', { method: 'POST', body: JSON.stringify({ text }) })
  }
}

const d = await j(`/api/summary/day?date=${today}`)
const mo = await j('/api/summary/month')
const jr = await j('/api/journal')
console.log(
  `hoy: ${d.expense_count} gastos, ${d.total_cop} · mes: ${mo.expense_count} gastos, ${mo.total_cop} · diario: ${jr.items.length} entradas`,
)

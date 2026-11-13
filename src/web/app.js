/* =========================================================
   app.js — El "cerebro" de la interfaz FitZone
   Qué hace: escucha clics, habla con la API y dibuja los resultados.
   ========================================================= */

// "use strict" hace que JavaScript avise de errores comunes (variables mal escritas, etc.)
"use strict";

// ---------------------------------------------------------
// 1. CONFIGURACIÓN
// ---------------------------------------------------------

// Dirección base de la API. Como la interfaz la sirve el MISMO FastAPI,
// basta con la ruta relativa (funciona igual en tu PC y en Render).
const API = "/api/v1";

// Formato que deben tener los IDs: "FIT-" + una letra + 3 números (FIT-C001, FIT-R001).
const FORMATO_ID = /^FIT-[A-Z]\d{3}$/;

// "Memoria" de la sesión: quién está usando el sistema ahora mismo.
const sesion = {
  rol: null, // "Recepción" o "Socio" (texto exacto que espera la API)
  id: null,  // Ejemplo: "FIT-R001"
};

// ---------------------------------------------------------
// 2. ATAJOS (funciones pequeñas que usamos muchas veces)
// ---------------------------------------------------------

// $("id") es un atajo para document.getElementById("id"): busca un elemento del HTML.
const $ = (id) => document.getElementById(id);

// Evita que un texto raro (por ejemplo "<script>") se convierta en código HTML.
// Siempre que metamos datos dentro de innerHTML los pasamos por aquí. (Seguridad)
function escapar(texto) {
  const div = document.createElement("div"); // Creamos un elemento temporal
  div.textContent = String(texto ?? "");     // textContent guarda el texto "tal cual"
  return div.innerHTML;                      // Y lo devolvemos ya "escapado"
}

// Convierte "2026-11-12T10:00:00" en "10:00" (hora local de México).
function hora(fechaTexto) {
  return new Date(fechaTexto).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

// Convierte "2026-11-12T10:00:00" en "12/11/2026".
function fecha(fechaTexto) {
  return new Date(fechaTexto).toLocaleDateString("es-MX");
}

// Limpia lo que escribió el usuario: quita espacios y lo pasa a MAYÚSCULAS.
function limpiarId(texto) {
  return texto.trim().toUpperCase();
}

// ---------------------------------------------------------
// 3. NAVEGACIÓN ENTRE PANTALLAS
// ---------------------------------------------------------

// Muestra UNA pantalla y oculta las demás.
function mostrarVista(nombre) {
  // Recorre todas las <section class="vista"> y las oculta
  document.querySelectorAll(".vista").forEach((v) => (v.hidden = true));
  // Muestra solo la que pedimos (vista-inicio, vista-menu, ...)
  $("vista-" + nombre).hidden = false;
  // Regresa la página hasta arriba para no aparecer "a la mitad"
  window.scrollTo(0, 0);

  // Algunas pantallas necesitan cargar datos al abrirse:
  if (nombre === "clases") cargarClases();
  if (nombre === "socio") prepararVistaSocio();
}

// ---------------------------------------------------------
// 4. AVISOS (mensajes verdes o rojos)
// ---------------------------------------------------------

// tipo = "exito" o "error". solucion = texto opcional con qué hacer.
function avisar(mensaje, tipo = "exito", solucion = "") {
  const aviso = document.createElement("div");       // Crea la cajita del aviso
  aviso.className = "aviso " + tipo;                 // Le pone color según el tipo
  aviso.setAttribute("role", tipo === "error" ? "alert" : "status"); // Accesibilidad
  // Ícono + mensaje + (si hay) la solución en una segunda línea
  aviso.innerHTML =
    (tipo === "error" ? "⚠️ " : "✅ ") + escapar(mensaje) +
    (solucion ? `<span class="solucion">👉 ${escapar(solucion)}</span>` : "");
  $("avisos").appendChild(aviso);                    // Lo muestra en pantalla
  // Los errores duran más (8 s) para que dé tiempo de leerlos; los éxitos 4 s.
  setTimeout(() => aviso.remove(), tipo === "error" ? 8000 : 4000);
}

// ---------------------------------------------------------
// 5. HABLAR CON LA API
// ---------------------------------------------------------

// Hace una petición a la API y devuelve la respuesta ya convertida a objeto.
// Si la API responde con error, "lanza" un Error con mensaje y solución humanos.
async function llamarApi(metodo, ruta, cuerpo) {
  let respuesta;
  try {
    // fetch = "ve a esta dirección y tráeme la respuesta"
    respuesta = await fetch(API + ruta, {
      method: metodo,                                   // "GET" o "POST"
      headers: { "Content-Type": "application/json" },  // Le decimos que mandamos JSON
      body: cuerpo ? JSON.stringify(cuerpo) : undefined // Datos a enviar (solo en POST)
    });
  } catch {
    // Si ni siquiera hubo respuesta: servidor apagado o sin internet.
    throw crearError(
      "No hay conexión con el servidor.",
      "Revisa que el servidor esté encendido (uvicorn) y tu internet."
    );
  }

  // Intentamos leer el JSON de la respuesta (si no trae, usamos {}).
  const datos = await respuesta.json().catch(() => ({}));

  // respuesta.ok es true para códigos 200-299 (éxito).
  if (respuesta.ok) return datos;

  // --- Si llegamos aquí, hubo un error. Traducimos cada caso a lenguaje humano ---
  // a) Errores de negocio (400) y permisos (403): la API ya trae "mensaje" y "solucion".
  if (datos.mensaje) throw crearError(datos.mensaje, datos.solucion);
  // b) Error 422: algún dato tiene un formato que la API no acepta.
  if (respuesta.status === 422) {
    throw crearError("Algún dato no tiene el formato correcto.", "Revisa los IDs escritos.");
  }
  // c) Cualquier otro error inesperado (500, etc.).
  throw crearError("Ocurrió un error inesperado (código " + respuesta.status + ").",
                   "Intenta de nuevo o avisa al administrador.");
}

// Crea un objeto Error que además guarda la "solución".
function crearError(mensaje, solucion = "") {
  const e = new Error(mensaje);
  e.solucion = solucion;
  return e;
}

// Envuelve una acción para que el botón muestre "Procesando…" y no se pueda
// presionar dos veces mientras esperamos a la API.
async function conBotonOcupado(boton, accion) {
  const textoOriginal = boton.textContent; // Guardamos el texto ("RESERVAR")
  boton.disabled = true;                   // Desactivamos el botón
  boton.textContent = "Procesando…";       // Retroalimentación visual
  try {
    await accion();                        // Ejecutamos la acción real
  } catch (error) {
    avisar(error.message, "error", error.solucion); // Si falla, mostramos aviso rojo
  } finally {
    // "finally" se ejecuta SIEMPRE, haya error o no: restauramos el botón
    // (solo si el botón sigue en pantalla; a veces se redibuja la lista).
    if (document.body.contains(boton)) {
      boton.disabled = false;
      boton.textContent = textoOriginal;
    }
  }
}

// ---------------------------------------------------------
// 6. VENTANA DE CONFIRMACIÓN ("¿Estás seguro?")
// ---------------------------------------------------------

// Abre el <dialog> y espera a que el usuario conteste.
// Devuelve una Promesa que termina con { ok: true/false, socioId: "..." }.
function preguntar({ titulo, texto, textoSi = "Sí, confirmar", pedirSocio = false, peligro = false }) {
  return new Promise((resolver) => {
    const dialogo = $("dialogo");
    $("dialogo-titulo").textContent = titulo;      // Título de la ventana
    $("dialogo-texto").textContent = texto;        // Explicación
    $("dialogo-si").textContent = textoSi;         // Texto del botón "Sí"
    // Botón rojo si la acción es "peligrosa" (cancelar), azul si no.
    $("dialogo-si").className = "btn " + (peligro ? "btn-peligro" : "btn-principal");
    $("dialogo-campo").hidden = !pedirSocio;       // ¿Mostramos el campo del socio?
    const campo = $("dialogo-socio");
    campo.value = "";
    campo.removeAttribute("aria-invalid");

    // Cuando la ventana se cierre, revisamos qué botón se presionó.
    dialogo.addEventListener("close", function alCerrar() {
      resolver({ ok: dialogo.returnValue === "si", socioId: limpiarId(campo.value) });
    }, { once: true }); // once: este "escuchador" se usa una sola vez

    dialogo.returnValue = "";                      // Borramos la respuesta anterior (si cierran con Esc = "No")
    dialogo.showModal();                           // Abre la ventana (bloquea el fondo)
    if (pedirSocio) campo.focus();                 // Cursor directo en el campo
  });
}

// Si se presiona Enter dentro del campo del diálogo, equivale a "Sí, confirmar".
$("dialogo-socio").addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    evento.preventDefault();      // Evita el comportamiento por defecto
    $("dialogo-si").click();      // Simula clic en "Sí"
  }
});

// Antes de cerrar con "Sí", validamos el ID del socio (si se pidió).
$("dialogo-si").addEventListener("click", (evento) => {
  const campo = $("dialogo-socio");
  if (!$("dialogo-campo").hidden && !FORMATO_ID.test(limpiarId(campo.value))) {
    evento.preventDefault();                    // NO cerramos la ventana
    campo.setAttribute("aria-invalid", "true"); // Borde rojo
    avisar("Escribe un ID de socio válido.", "error", "Ejemplo: FIT-C001");
    campo.focus();
  }
});

// ---------------------------------------------------------
// 7. PANTALLA A: INICIO
// ---------------------------------------------------------

// Al tocar "Soy RECEPCIÓN" o "Soy SOCIO"...
document.querySelectorAll("[data-rol]").forEach((boton) => {
  boton.addEventListener("click", () => {
    // Desmarcamos ambos botones y marcamos solo el elegido
    document.querySelectorAll("[data-rol]").forEach((b) => b.setAttribute("aria-pressed", "false"));
    boton.setAttribute("aria-pressed", "true");
    sesion.rol = boton.dataset.rol; // dataset.rol lee el atributo data-rol del HTML
    $("campo-id").focus();          // Llevamos el cursor al campo del ID (un clic menos)
  });
});

// Al presionar ENTRAR (o Enter en el campo)...
$("form-entrar").addEventListener("submit", async (evento) => {
  evento.preventDefault(); // Evita que la página se recargue (comportamiento normal de un form)
  const campo = $("campo-id");
  const id = limpiarId(campo.value);

  // Validación 1: ¿eligió rol?
  if (!sesion.rol) {
    avisar("Primero toca si eres RECEPCIÓN o SOCIO.", "error");
    return; // "return" detiene la función aquí
  }
  // Validación 2: ¿el ID tiene buen formato?
  if (!FORMATO_ID.test(id)) {
    campo.setAttribute("aria-invalid", "true");
    avisar("Ese ID no tiene el formato correcto.", "error", "Debe verse así: FIT-C001");
    return;
  }
  campo.removeAttribute("aria-invalid");

  // Validación 3 (solo socios): preguntamos a la API si ese socio existe.
  const boton = evento.submitter || evento.target.querySelector("button");
  await conBotonOcupado(boton, async () => {
    if (sesion.rol === "Socio") {
      try {
        await llamarApi("GET", `/socios/${encodeURIComponent(id)}/membresia`);
      } catch {
        throw crearError("No encontramos un socio con ese ID.", "Revisa tu credencial o acude a recepción.");
      }
    }
    entrar(id); // Todo bien: entramos al sistema
  });
});

// Guarda la sesión y muestra el menú.
function entrar(id) {
  sesion.id = id;
  // Guardamos en el navegador para no perder la sesión si recargan la página.
  try { sessionStorage.setItem("fitzone-sesion", JSON.stringify(sesion)); } catch { /* sin almacenamiento: no pasa nada */ }
  $("usuario-actual").textContent = `${sesion.rol} · ${sesion.id}`; // Barra superior
  $("btn-salir").hidden = false;
  // Textos del menú según el rol
  const esRecepcion = sesion.rol === "Recepción";
  $("texto-boton-socio").textContent = esRecepcion ? "Buscar SOCIO" : "Mi MEMBRESÍA y reservas";
  $("ayuda-menu").textContent = esRecepcion
    ? "Para CANCELAR o marcar ASISTENCIA: entra a «Buscar SOCIO»."
    : "Para CANCELAR una reserva: entra a «Mi MEMBRESÍA y reservas».";
  mostrarVista("menu");
}

// Botón SALIR: borra la sesión y regresa al inicio.
$("btn-salir").addEventListener("click", () => {
  sesion.rol = null;
  sesion.id = null;
  try { sessionStorage.removeItem("fitzone-sesion"); } catch { /* nada */ }
  $("usuario-actual").textContent = "";
  $("btn-salir").hidden = true;
  $("campo-id").value = "";
  document.querySelectorAll("[data-rol]").forEach((b) => b.setAttribute("aria-pressed", "false"));
  mostrarVista("inicio");
});

// ---------------------------------------------------------
// 8. PANTALLA B: MENÚ (y todos los botones "Volver")
// ---------------------------------------------------------

// Cualquier botón con data-ir="algo" lleva a la pantalla "algo".
document.querySelectorAll("[data-ir]").forEach((boton) => {
  boton.addEventListener("click", () => mostrarVista(boton.dataset.ir));
});

// ---------------------------------------------------------
// 9. PANTALLA C: CLASES
// ---------------------------------------------------------

// Decide el color del semáforo según los lugares libres.
function colorSemaforo(lugares) {
  if (lugares <= 0) return "rojo";
  if (lugares <= 5) return "ambar";
  return "verde";
}

// Pide el calendario a la API y dibuja una tarjeta por clase.
async function cargarClases() {
  const contenedor = $("lista-clases");
  contenedor.innerHTML = '<p class="cargando">Cargando clases…</p>';
  try {
    const clases = await llamarApi("GET", "/calendario");
    if (clases.length === 0) {
      contenedor.innerHTML = '<p class="vacio">No hay clases programadas.</p>';
      return;
    }
    // .map convierte cada clase en un pedazo de HTML; .join("") los une.
    contenedor.innerHTML = clases.map((c) => {
      const color = colorSemaforo(c.lugares_disponibles);
      const llena = c.lugares_disponibles <= 0;
      const textoLugares = llena
        ? "🔴 LLENA"
        : `${color === "verde" ? "🟢" : "🟡"} ${c.lugares_disponibles} lugar${c.lugares_disponibles === 1 ? "" : "es"} libre${c.lugares_disponibles === 1 ? "" : "s"}`;
      return `
        <article class="clase ${color}">
          <h3>${escapar(c.nombre)}</h3>
          <span>🕗 ${hora(c.horario_inicio)} – ${hora(c.horario_fin)}</span>
          <span class="pista">Código: ${escapar(c.id)}</span>
          <span class="lugares">${textoLugares}</span>
          <button class="btn ${llena ? "btn-secundario" : "btn-principal"}"
                  data-reservar="${escapar(c.id)}" data-nombre="${escapar(c.nombre)}"
                  ${llena ? "disabled" : ""}>
            ${llena ? "Sin lugares" : "RESERVAR"}
          </button>
        </article>`;
    }).join("");
  } catch (error) {
    contenedor.innerHTML = `<p class="vacio">No se pudieron cargar las clases.</p>`;
    avisar(error.message, "error", error.solucion);
  }
}

// Un solo "escuchador" para TODOS los botones RESERVAR (aunque se redibujen).
$("lista-clases").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-reservar]"); // ¿Se tocó un botón RESERVAR?
  if (!boton) return;                                     // Si no, ignoramos el clic
  const claseId = boton.dataset.reservar;
  const esRecepcion = sesion.rol === "Recepción";

  // Paso de confirmación. Recepción además escribe el ID del socio.
  const respuesta = await preguntar({
    titulo: "Reservar " + boton.dataset.nombre,
    texto: esRecepcion
      ? "¿Para qué socio es el lugar?"
      : "¿Confirmas que quieres apartar tu lugar en esta clase?",
    textoSi: "Sí, reservar",
    pedirSocio: esRecepcion,
  });
  if (!respuesta.ok) return; // Si dijo "No", no hacemos nada

  const socioId = esRecepcion ? respuesta.socioId : sesion.id;
  await conBotonOcupado(boton, async () => {
    // Enviamos exactamente lo que pide la API (ComandoReservar)
    const r = await llamarApi("POST", "/reservas", {
      clase_id: claseId,
      socio_id: socioId,
      actor_id: sesion.id,
      actor_rol: sesion.rol,
    });
    avisar(`${r.mensaje} (${socioId} en ${claseId})`, "exito");
    await cargarClases(); // Redibujamos para ver los lugares actualizados
  });
});

// ---------------------------------------------------------
// 10. PANTALLA D: FICHA DEL SOCIO
// ---------------------------------------------------------

// Al abrir la pantalla: Recepción ve el buscador; el Socio ve directo su ficha.
function prepararVistaSocio() {
  const esRecepcion = sesion.rol === "Recepción";
  $("form-buscar").hidden = !esRecepcion;
  $("titulo-socio").textContent = esRecepcion ? "Buscar socio" : "Mi membresía y reservas";
  if (esRecepcion) {
    $("ficha-socio").hidden = true;  // Ocultamos la ficha anterior
    $("campo-buscar").focus();
  } else {
    cargarFicha(sesion.id);
  }
}

// Buscador de Recepción
$("form-buscar").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const campo = $("campo-buscar");
  const id = limpiarId(campo.value);
  if (!FORMATO_ID.test(id)) {
    campo.setAttribute("aria-invalid", "true");
    avisar("Escribe un ID de socio válido.", "error", "Ejemplo: FIT-C001");
    return;
  }
  campo.removeAttribute("aria-invalid");
  const boton = evento.submitter || evento.target.querySelector("button");
  await conBotonOcupado(boton, () => cargarFicha(id));
});

// Carga membresía + reservas de un socio y las dibuja.
async function cargarFicha(socioId) {
  // Promise.all pide las DOS cosas al mismo tiempo (más rápido).
  // Si el socio no tiene membresía, la API responde error → lo mostramos.
  const [membresia, reservas] = await Promise.all([
    llamarApi("GET", `/socios/${encodeURIComponent(socioId)}/membresia`),
    llamarApi("GET", `/socios/${encodeURIComponent(socioId)}/reservas`),
  ]).catch((error) => {
    $("ficha-socio").hidden = true;
    throw error; // Lo re-lanzamos para que conBotonOcupado muestre el aviso
  });

  dibujarMembresia(membresia);
  dibujarReservas(socioId, reservas);
  $("ficha-socio").hidden = false;
}

// Tarjeta grande verde (vigente) o roja (vencida / suspendida).
function dibujarMembresia(m) {
  const tarjeta = $("tarjeta-membresia");
  let estado, clase, consejo = "";
  if (m.vigente) {
    estado = "✅ MEMBRESÍA VIGENTE"; clase = "ok";
  } else if (m.suspendida) {
    estado = "⛔ MEMBRESÍA SUSPENDIDA"; clase = "mal";
    consejo = "No puede reservar ni entrar. Debe acudir a recepción.";
  } else {
    estado = "⛔ MEMBRESÍA VENCIDA"; clase = "mal";
    consejo = "No puede reservar ni entrar. Debe renovar en recepción.";
  }
  tarjeta.className = "membresia " + clase;
  tarjeta.innerHTML = `
    <p class="estado">${estado}</p>
    <p>Socio: <strong>${escapar(m.socio_id)}</strong> · Plan: ${escapar(m.plan_id)}</p>
    <p>Vigencia: ${fecha(m.inicio_vigencia)} al ${fecha(m.fin_vigencia)}</p>
    ${consejo ? `<p><strong>${consejo}</strong></p>` : ""}`;
}

// Nombres "humanos" para los estados de la API.
const NOMBRE_ESTADO = {
  SOLICITADA: "Solicitada",
  ACTIVA: "Activa",
  CANCELADA: "Cancelada",
  ASISTIDA: "Asistió",
  NO_SHOW: "No asistió",
};

// Lista de reservas, con botones solo donde tienen sentido.
function dibujarReservas(socioId, reservas) {
  const lista = $("lista-reservas");
  if (reservas.length === 0) {
    lista.innerHTML = '<p class="vacio">Este socio todavía no tiene reservas.</p>';
    return;
  }
  const esRecepcion = sesion.rol === "Recepción";
  lista.innerHTML = reservas.map((r) => {
    const activa = r.estado === "ACTIVA"; // Solo las activas se pueden cancelar o marcar
    const botones = activa ? `
        ${esRecepcion ? `<button class="btn btn-exito btn-chico" data-accion="asistencia"
              data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">✅ Marcar asistencia</button>` : ""}
        <button class="btn btn-peligro btn-chico" data-accion="cancelar"
              data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">❌ Cancelar</button>` : "";
    return `
      <div class="reserva">
        <div class="info">
          <strong>Clase ${escapar(r.clase_id)}</strong>
          <span class="etiqueta ${escapar(r.estado)}">${NOMBRE_ESTADO[r.estado] || escapar(r.estado)}</span>
          <div class="fecha">Creada: ${r.fecha_creacion ? fecha(r.fecha_creacion) : "—"}</div>
        </div>
        ${botones}
      </div>`;
  }).join("");
}

// Un solo escuchador para los botones Cancelar / Marcar asistencia.
$("lista-reservas").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-accion]");
  if (!boton) return;
  const { accion, clase, socio } = boton.dataset; // Lee data-accion, data-clase, data-socio
  const esCancelar = accion === "cancelar";

  const respuesta = await preguntar({
    titulo: esCancelar ? "¿Cancelar esta reserva?" : "¿Registrar asistencia?",
    texto: esCancelar
      ? `Se liberará el lugar del socio ${socio} en la clase ${clase}. Esta acción no se puede deshacer.`
      : `Confirma que el socio ${socio} llegó a la clase ${clase}.`,
    textoSi: esCancelar ? "Sí, cancelar" : "Sí, llegó",
    peligro: esCancelar,
  });
  if (!respuesta.ok) return;

  await conBotonOcupado(boton, async () => {
    // Ambas acciones mandan el mismo "paquete" de datos; solo cambia la ruta.
    const r = await llamarApi("POST", esCancelar ? "/reservas/cancelar" : "/reservas/asistencia", {
      clase_id: clase,
      socio_id: socio,
      actor_id: sesion.id,
      actor_rol: sesion.rol,
    });
    avisar(r.mensaje, "exito");
    await cargarFicha(socio); // Redibujamos para ver el nuevo estado
  });
});

// ---------------------------------------------------------
// 11. ARRANQUE: ¿ya había alguien con sesión abierta?
// ---------------------------------------------------------
(function arrancar() {
  try {
    const guardada = JSON.parse(sessionStorage.getItem("fitzone-sesion") || "null");
    if (guardada && guardada.rol && guardada.id) {
      sesion.rol = guardada.rol;
      entrar(guardada.id); // Recargó la página: lo regresamos al menú directo
      return;
    }
  } catch { /* si falla, simplemente empezamos en el inicio */ }
  mostrarVista("inicio");
})();

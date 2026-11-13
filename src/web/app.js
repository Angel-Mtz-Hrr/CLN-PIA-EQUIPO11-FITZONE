/* =========================================================
   app.js — Controlador de la interfaz FitZone
   Totalmente fiel a la lógica original del equipo,
   con estética moderna, profesional y CERO emojis.
   ========================================================= */

"use strict";

// ---------------------------------------------------------
// 1. CONFIGURACIÓN BASE
// ---------------------------------------------------------
const API = "/api/v1";
const FORMATO_ID = /^FIT-[A-Z]\d{3}$/;

const sesion = {
  rol: null, // "Recepción" o "Socio"
  id: null,  // Ejemplo: "FIT-R001" o "FIT-C001"
};

// ---------------------------------------------------------
// 2. ICONOS VECTORIALES DE LÍNEA (Sustitutos de emojis)
// ---------------------------------------------------------
const ICONOS = {
  check: `<svg class="icono-mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  alerta: `<svg class="icono-mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
  reloj: `<svg class="icono-mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`,
  cancelar: `<svg class="icono-mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
  flecha: `<svg class="icono-mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`,
};

// ---------------------------------------------------------
// 3. ATAJOS Y UTILIDADES
// ---------------------------------------------------------
const $ = (id) => document.getElementById(id);

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = String(texto ?? "");
  return div.innerHTML;
}

function hora(fechaTexto) {
  return new Date(fechaTexto).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

function fecha(fechaTexto) {
  return new Date(fechaTexto).toLocaleDateString("es-MX");
}

function limpiarId(texto) {
  return texto.trim().toUpperCase();
}

// ---------------------------------------------------------
// 4. NAVEGACIÓN ENTRE PANTALLAS
// ---------------------------------------------------------
function mostrarVista(nombre) {
  document.querySelectorAll(".vista").forEach((v) => (v.hidden = true));
  const destino = $("vista-" + nombre);
  if (destino) {
    destino.hidden = false;
    window.scrollTo(0, 0);
  }

  if (nombre === "clases") cargarClases();
  if (nombre === "socio") prepararVistaSocio();
}

// ---------------------------------------------------------
// 5. AVISOS FLOTANTES
// ---------------------------------------------------------
function avisar(mensaje, tipo = "exito", solucion = "") {
  const aviso = document.createElement("div");
  aviso.className = "aviso " + tipo;
  aviso.setAttribute("role", tipo === "error" ? "alert" : "status");

  const icono = tipo === "error" ? ICONOS.alerta : ICONOS.check;
  aviso.innerHTML = `
    <div>${icono} ${escapar(mensaje)}</div>
    ${solucion ? `<span class="solucion">${ICONOS.flecha} ${escapar(solucion)}</span>` : ""}
  `;
  $("avisos").appendChild(aviso);
  setTimeout(() => aviso.remove(), tipo === "error" ? 8000 : 4000);
}

// ---------------------------------------------------------
// 6. COMUNICACIÓN CON LA API
// ---------------------------------------------------------
async function llamarApi(metodo, ruta, cuerpo) {
  let respuesta;
  try {
    respuesta = await fetch(API + ruta, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw crearError(
      "No hay conexión con el servidor.",
      "Revisa que el servidor esté encendido (uvicorn) y tu conexión de red."
    );
  }

  const datos = await respuesta.json().catch(() => ({}));
  if (respuesta.ok) return datos;

  if (datos.mensaje) throw crearError(datos.mensaje, datos.solucion);
  if (respuesta.status === 422) {
    throw crearError("Algún dato no tiene el formato correcto.", "Revisa los IDs escritos.");
  }
  throw crearError(
    "Ocurrió un error inesperado (código " + respuesta.status + ").",
    "Intenta de nuevo o consulta al administrador."
  );
}

function crearError(mensaje, solucion = "") {
  const e = new Error(mensaje);
  e.solucion = solucion;
  return e;
}

async function conBotonOcupado(boton, accion) {
  const textoOriginal = boton.innerHTML;
  boton.disabled = true;
  boton.innerHTML = "Procesando…";
  try {
    await accion();
  } catch (error) {
    avisar(error.message, "error", error.solucion);
  } finally {
    if (document.body.contains(boton)) {
      boton.disabled = false;
      boton.innerHTML = textoOriginal;
    }
  }
}

// ---------------------------------------------------------
// 7. VENTANA DE CONFIRMACIÓN (<dialog>)
// ---------------------------------------------------------
function preguntar({ titulo, texto, textoSi = "Sí, confirmar", pedirSocio = false, peligro = false }) {
  return new Promise((resolver) => {
    const dialogo = $("dialogo");
    $("dialogo-titulo").textContent = titulo;
    $("dialogo-texto").textContent = texto;
    $("dialogo-si").textContent = textoSi;
    $("dialogo-si").className = "btn " + (peligro ? "btn-peligro" : "btn-principal");
    $("dialogo-campo").hidden = !pedirSocio;
    const campo = $("dialogo-socio");
    campo.value = "";
    campo.removeAttribute("aria-invalid");

    dialogo.addEventListener(
      "close",
      function alCerrar() {
        resolver({ ok: dialogo.returnValue === "si", socioId: limpiarId(campo.value) });
      },
      { once: true }
    );

    dialogo.returnValue = "";
    dialogo.showModal();
    if (pedirSocio) campo.focus();
  });
}

$("dialogo-socio").addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    evento.preventDefault();
    $("dialogo-si").click();
  }
});

$("dialogo-si").addEventListener("click", (evento) => {
  const campo = $("dialogo-socio");
  if (!$("dialogo-campo").hidden && !FORMATO_ID.test(limpiarId(campo.value))) {
    evento.preventDefault();
    campo.setAttribute("aria-invalid", "true");
    avisar("Escribe un ID de socio válido.", "error", "Ejemplo: FIT-C001");
    campo.focus();
    return;
  }
  $("dialogo").close("si");
});

// ---------------------------------------------------------
// 8. PANTALLA A: INICIO
// ---------------------------------------------------------
document.querySelectorAll("[data-rol]").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll("[data-rol]").forEach((b) => b.setAttribute("aria-pressed", "false"));
    boton.setAttribute("aria-pressed", "true");
    sesion.rol = boton.dataset.rol;
    $("campo-id").focus();
  });
});

$("form-entrar").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const campo = $("campo-id");
  const id = limpiarId(campo.value);

  if (!sesion.rol) {
    avisar("Primero toca si eres RECEPCIÓN o SOCIO.", "error");
    return;
  }
  if (!FORMATO_ID.test(id)) {
    campo.setAttribute("aria-invalid", "true");
    avisar("Ese ID no tiene el formato correcto.", "error", "Debe verse así: FIT-C001");
    return;
  }
  campo.removeAttribute("aria-invalid");

  const boton = evento.submitter || evento.target.querySelector("button");
  await conBotonOcupado(boton, async () => {
    if (sesion.rol === "Socio") {
      try {
        await llamarApi("GET", `/socios/${encodeURIComponent(id)}/membresia`);
      } catch {
        throw crearError("No encontramos un socio con ese ID.", "Revisa tu credencial o acude a recepción.");
      }
    }
    entrar(id);
  });
});

function entrar(id) {
  sesion.id = id;
  try {
    sessionStorage.setItem("fitzone-sesion", JSON.stringify(sesion));
  } catch {}

  $("usuario-actual").textContent = `${sesion.rol} · ${sesion.id}`;
  $("btn-salir").hidden = false;

  const esRecepcion = sesion.rol === "Recepción";
  $("texto-boton-socio").textContent = esRecepcion ? "Buscar SOCIO" : "Mi MEMBRESÍA y reservas";
  $("ayuda-menu").textContent = esRecepcion
    ? "Para CANCELAR o marcar ASISTENCIA: entra a «Buscar SOCIO»."
    : "Para CANCELAR una reserva: entra a «Mi MEMBRESÍA y reservas».";
  mostrarVista("menu");
}

$("btn-salir").addEventListener("click", () => {
  sesion.rol = null;
  sesion.id = null;
  try {
    sessionStorage.removeItem("fitzone-sesion");
  } catch {}

  $("usuario-actual").textContent = "";
  $("btn-salir").hidden = true;
  $("campo-id").value = "";
  document.querySelectorAll("[data-rol]").forEach((b) => b.setAttribute("aria-pressed", "false"));
  mostrarVista("inicio");
});

// ---------------------------------------------------------
// 9. PANTALLA B: MENÚ (y botones volver)
// ---------------------------------------------------------
document.querySelectorAll("[data-ir]").forEach((boton) => {
  boton.addEventListener("click", () => mostrarVista(boton.dataset.ir));
});

// ---------------------------------------------------------
// 10. PANTALLA C: CLASES
// ---------------------------------------------------------
function colorSemaforo(lugares) {
  if (lugares <= 0) return "rojo";
  if (lugares <= 5) return "ambar";
  return "verde";
}

async function cargarClases() {
  const contenedor = $("lista-clases");
  contenedor.innerHTML = '<p class="cargando">Cargando clases…</p>';
  try {
    const clases = await llamarApi("GET", "/calendario");
    if (!clases || clases.length === 0) {
      contenedor.innerHTML = '<p class="vacio">No hay clases programadas.</p>';
      return;
    }

    contenedor.innerHTML = clases
      .map((c) => {
        const color = colorSemaforo(c.lugares_disponibles);
        const llena = c.lugares_disponibles <= 0;
        const textoLugares = llena
          ? `<span class="punto rojo"></span> LLENA`
          : `<span class="punto ${color}"></span> ${c.lugares_disponibles} lugar${c.lugares_disponibles === 1 ? "" : "es"} libre${c.lugares_disponibles === 1 ? "" : "es"}`;

        return `
        <article class="clase ${color}">
          <h3>${escapar(c.nombre)}</h3>
          <span class="horario-linea">${ICONOS.reloj} ${hora(c.horario_inicio)} – ${hora(c.horario_fin)}</span>
          <span class="codigo-linea">Código: ${escapar(c.id)}</span>
          <span class="lugares">${textoLugares}</span>
          <button class="btn ${llena ? "btn-secundario" : "btn-principal"}"
                  data-reservar="${escapar(c.id)}" data-nombre="${escapar(c.nombre)}"
                  ${llena ? "disabled" : ""}>
            ${llena ? "Sin lugares" : "RESERVAR"}
          </button>
        </article>`;
      })
      .join("");
  } catch (error) {
    contenedor.innerHTML = '<p class="vacio">No se pudieron cargar las clases.</p>';
    avisar(error.message, "error", error.solucion);
  }
}

$("lista-clases").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-reservar]");
  if (!boton) return;

  const claseId = boton.dataset.reservar;
  const esRecepcion = sesion.rol === "Recepción";

  const respuesta = await preguntar({
    titulo: "Reservar " + boton.dataset.nombre,
    texto: esRecepcion
      ? "¿Para qué socio es el lugar?"
      : "¿Confirmas que quieres apartar tu lugar en esta clase?",
    textoSi: "Sí, reservar",
    pedirSocio: esRecepcion,
  });
  if (!respuesta.ok) return;

  const socioId = esRecepcion ? respuesta.socioId : sesion.id;
  await conBotonOcupado(boton, async () => {
    const r = await llamarApi("POST", "/reservas", {
      clase_id: claseId,
      socio_id: socioId,
      actor_id: sesion.id,
      actor_rol: sesion.rol,
    });
    avisar(`${r.mensaje} (${socioId} en ${claseId})`, "exito");
    await cargarClases();
  });
});

// ---------------------------------------------------------
// 11. PANTALLA D: FICHA DEL SOCIO
// ---------------------------------------------------------
function prepararVistaSocio() {
  const esRecepcion = sesion.rol === "Recepción";
  $("form-buscar").hidden = !esRecepcion;
  $("titulo-socio").textContent = esRecepcion ? "Buscar socio" : "Mi membresía y reservas";
  if (esRecepcion) {
    $("ficha-socio").hidden = true;
    $("campo-buscar").focus();
  } else {
    cargarFicha(sesion.id);
  }
}

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

async function cargarFicha(socioId) {
  const [membresia, reservas] = await Promise.all([
    llamarApi("GET", `/socios/${encodeURIComponent(socioId)}/membresia`),
    llamarApi("GET", `/socios/${encodeURIComponent(socioId)}/reservas`),
  ]).catch((error) => {
    $("ficha-socio").hidden = true;
    throw error;
  });

  dibujarMembresia(membresia);
  dibujarReservas(socioId, reservas);
  $("ficha-socio").hidden = false;
}

function dibujarMembresia(m) {
  const tarjeta = $("tarjeta-membresia");
  let estado, clase, consejo = "";
  if (m.vigente) {
    estado = `${ICONOS.check} MEMBRESÍA VIGENTE`;
    clase = "ok";
  } else if (m.suspendida) {
    estado = `${ICONOS.alerta} MEMBRESÍA SUSPENDIDA`;
    clase = "mal";
    consejo = "No puede reservar ni entrar. Debe acudir a recepción.";
  } else {
    estado = `${ICONOS.alerta} MEMBRESÍA VENCIDA`;
    clase = "mal";
    consejo = "No puede reservar ni entrar. Debe renovar en recepción.";
  }

  tarjeta.className = "membresia " + clase;
  tarjeta.innerHTML = `
    <p class="estado">${estado}</p>
    <p>Socio: <strong>${escapar(m.socio_id)}</strong> · Plan: ${escapar(m.plan_id)}</p>
    <p>Vigencia: ${fecha(m.inicio_vigencia)} al ${fecha(m.fin_vigencia)}</p>
    ${consejo ? `<p><strong>${consejo}</strong></p>` : ""}`;
}

const NOMBRE_ESTADO = {
  SOLICITADA: "Solicitada",
  ACTIVA: "Activa",
  CANCELADA: "Cancelada",
  ASISTIDA: "Asistió",
  NO_SHOW: "No asistió",
};

function dibujarReservas(socioId, reservas) {
  const lista = $("lista-reservas");
  if (!reservas || reservas.length === 0) {
    lista.innerHTML = '<p class="vacio">Este socio todavía no tiene reservas.</p>';
    return;
  }
  const esRecepcion = sesion.rol === "Recepción";
  lista.innerHTML = reservas
    .map((r) => {
      const activa = r.estado === "ACTIVA";
      const botones = activa
        ? `
        ${
          esRecepcion
            ? `<button class="btn btn-exito btn-chico" data-accion="asistencia"
                      data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">
                ${ICONOS.check} Marcar asistencia
               </button>`
            : ""
        }
        <button class="btn btn-peligro btn-chico" data-accion="cancelar"
                data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">
          ${ICONOS.cancelar} Cancelar
        </button>`
        : "";

      return `
      <div class="reserva">
        <div class="info">
          <strong>Clase ${escapar(r.clase_id)}</strong>
          <span class="etiqueta ${escapar(r.estado)}">${NOMBRE_ESTADO[r.estado] || escapar(r.estado)}</span>
          <div class="fecha">Creada: ${r.fecha_creacion ? fecha(r.fecha_creacion) : "—"}</div>
        </div>
        ${botones}
      </div>`;
    })
    .join("");
}

$("lista-reservas").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-accion]");
  if (!boton) return;
  const { accion, clase, socio } = boton.dataset;
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
    const r = await llamarApi("POST", esCancelar ? "/reservas/cancelar" : "/reservas/asistencia", {
      clase_id: clase,
      socio_id: socio,
      actor_id: sesion.id,
      actor_rol: sesion.rol,
    });
    avisar(r.mensaje, "exito");
    await cargarFicha(socio);
  });
});

// ---------------------------------------------------------
// 12. INICIO Y RECUPERACIÓN DE SESIÓN
// ---------------------------------------------------------
(function arrancar() {
  try {
    const guardada = JSON.parse(sessionStorage.getItem("fitzone-sesion") || "null");
    if (guardada && guardada.rol && guardada.id) {
      sesion.rol = guardada.rol;
      entrar(guardada.id);
      return;
    }
  } catch {}
  mostrarVista("inicio");
})();

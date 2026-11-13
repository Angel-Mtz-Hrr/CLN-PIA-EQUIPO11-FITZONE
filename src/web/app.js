/* =========================================================
   app.js — Controlador UI/UX FitZone 2026
   Arquitectura limpia: Event-Driven, Fetch API, SVG Icons & Glassmorphism
   ========================================================= */

"use strict";

// ---------------------------------------------------------
// 1. CONFIGURACIÓN BASE
// ---------------------------------------------------------
const API = "/api/v1";
const FORMATO_ID = /^FIT-[A-Z]\d{3}$/;

const sesion = {
  rol: null, // "Recepción" o "Socio"
  id: null,  // Ej. "FIT-R001" o "FIT-C001"
};

// ---------------------------------------------------------
// 2. ICONOS VECTORIALES PROFESIONALES (SVG Sistema Lucide)
// ---------------------------------------------------------
const ICONOS = {
  check: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  alert: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
  clock: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`,
  dumbbell: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5v14M18 5v14M2 9v6M22 9v6M6 12h12"></path></svg>`,
  shieldCheck: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>`,
  shieldAlert: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
  x: `<svg class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
};

// ---------------------------------------------------------
// 3. UTILIDADES Y SANITIZACIÓN
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
  return new Date(fechaTexto).toLocaleDateString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function limpiarId(texto) {
  return texto.trim().toUpperCase();
}

// ---------------------------------------------------------
// 4. CONTROL DE PANTALLAS (Single Page Navigation)
// ---------------------------------------------------------
function mostrarVista(nombre) {
  document.querySelectorAll(".vista").forEach((v) => (v.hidden = true));
  const destino = $("vista-" + nombre);
  if (destino) {
    destino.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (nombre === "clases") cargarClases();
  if (nombre === "socio") prepararVistaSocio();
}

// ---------------------------------------------------------
// 5. SISTEMA DE TOASTS FLOTANTES MODERNOS (Avisos)
// ---------------------------------------------------------
function avisar(mensaje, tipo = "exito", solucion = "") {
  const aviso = document.createElement("div");
  aviso.className = "aviso-toast " + tipo;
  aviso.setAttribute("role", tipo === "error" ? "alert" : "status");

  const iconoHtml = tipo === "error" ? ICONOS.alert : ICONOS.check;
  aviso.innerHTML = `
    <div class="aviso-toast-icono">${iconoHtml}</div>
    <div class="aviso-cuerpo">
      <span class="aviso-mensaje">${escapar(mensaje)}</span>
      ${solucion ? `<span class="aviso-solucion">${escapar(solucion)}</span>` : ""}
    </div>
  `;

  $("avisos").appendChild(aviso);

  setTimeout(() => {
    aviso.style.opacity = "0";
    aviso.style.transform = "translateX(40px)";
    aviso.style.transition = "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)";
    setTimeout(() => aviso.remove(), 320);
  }, tipo === "error" ? 7000 : 4000);
}

// ---------------------------------------------------------
// 6. CLIENTE HTTP REST (FastAPI Bridge)
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
      "Imposible conectar con el servidor central.",
      "Verifica que el servicio backend se encuentre activo y con conexión estable."
    );
  }

  const datos = await respuesta.json().catch(() => ({}));

  if (respuesta.ok) return datos;

  if (datos.mensaje) throw crearError(datos.mensaje, datos.solucion);
  if (respuesta.status === 422) {
    throw crearError("Estructura de datos inválida para el servidor.", "Revisa el formato del identificador.");
  }

  throw crearError(
    `Error en la operación (Código HTTP ${respuesta.status}).`,
    "Intenta nuevamente o consulta con el personal técnico de FitZone."
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
  boton.innerHTML = `<span>Procesando…</span>`;
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
// 7. MODAL DE CONFIRMACIÓN GLASSMORPHISM
// ---------------------------------------------------------
function preguntar({ titulo, texto, textoSi = "Confirmar", pedirSocio = false, peligro = false }) {
  return new Promise((resolver) => {
    const dialogo = $("dialogo");
    $("dialogo-titulo").textContent = titulo;
    $("dialogo-texto").textContent = texto;
    $("dialogo-si").textContent = textoSi;
    $("dialogo-si").className = "btn " + (peligro ? "btn-peligro" : "btn-gradiente");
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

$("dialogo-si").addEventListener("click", () => {
  const campo = $("dialogo-socio");
  if (!$("dialogo-campo").hidden && !FORMATO_ID.test(limpiarId(campo.value))) {
    campo.setAttribute("aria-invalid", "true");
    avisar("El ID del socio ingresado es inválido.", "error", "Formato requerido: FIT-C001");
    campo.focus();
    return;
  }
  $("dialogo").close("si");
});

// ---------------------------------------------------------
// 8. AUTENTICACIÓN Y SESIÓN (Vista Inicio)
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
    avisar("Por favor selecciona tu perfil (Recepción o Socio).", "error");
    return;
  }

  if (!FORMATO_ID.test(id)) {
    campo.setAttribute("aria-invalid", "true");
    avisar("El identificador proporcionado no cumple con el estándar.", "error", "Ejemplo esperado: FIT-R001 o FIT-C001");
    return;
  }
  campo.removeAttribute("aria-invalid");

  const boton = evento.submitter || evento.target.querySelector("button");
  await conBotonOcupado(boton, async () => {
    if (sesion.rol === "Socio") {
      try {
        await llamarApi("GET", `/socios/${encodeURIComponent(id)}/membresia`);
      } catch {
        throw crearError("No existe registro de membresía con ese ID de socio.", "Verifica tu credencial física o acude a recepción.");
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
  $("usuario-badge").hidden = false;
  $("btn-salir").hidden = false;

  const esRecepcion = sesion.rol === "Recepción";
  $("texto-boton-socio").textContent = esRecepcion ? "Gestión de Socios" : "Mi Membresía y Reservas";
  $("descripcion-boton-socio").textContent = esRecepcion
    ? "Verifica contratos, valida accesos en puerta o cancela lugares."
    : "Consulta tu estado de cuenta, vigencia contractual y próximas clases.";

  $("ayuda-menu").textContent = esRecepcion
    ? "Modo Operador: Puedes registrar asistencias en puerta y tramitar cancelaciones desde el panel de socios."
    : "Modo Socio: Recuerda cancelar con anticipación si no podrás asistir a tu clase programada.";

  mostrarVista("menu");
}

$("btn-salir").addEventListener("click", () => {
  sesion.rol = null;
  sesion.id = null;
  try {
    sessionStorage.removeItem("fitzone-sesion");
  } catch {}

  $("usuario-actual").textContent = "";
  $("usuario-badge").hidden = true;
  $("btn-salir").hidden = true;
  $("campo-id").value = "";
  document.querySelectorAll("[data-rol]").forEach((b) => b.setAttribute("aria-pressed", "false"));
  mostrarVista("inicio");
});

document.querySelectorAll("[data-ir]").forEach((boton) => {
  boton.addEventListener("click", () => mostrarVista(boton.dataset.ir));
});

// ---------------------------------------------------------
// 9. CARTELERA DE CLASES CON SEMÁFORO INTELIGENTE
// ---------------------------------------------------------
function colorSemaforo(lugares) {
  if (lugares <= 0) return "rojo";
  if (lugares <= 5) return "ambar";
  return "verde";
}

async function cargarClases() {
  const contenedor = $("lista-clases");
  contenedor.innerHTML = `
    <div class="cargando-estado glass-panel">
      <div class="spinner"></div>
      <p>Sincronizando disponibilidad con el servidor…</p>
    </div>`;

  try {
    const clases = await llamarApi("GET", "/calendario");
    if (!clases || clases.length === 0) {
      contenedor.innerHTML = `
        <div class="estado-vacio glass-panel">
          <p>No se encontraron clases programadas para esta fecha.</p>
        </div>`;
      return;
    }

    contenedor.innerHTML = clases
      .map((c) => {
        const color = colorSemaforo(c.lugares_disponibles);
        const llena = c.lugares_disponibles <= 0;
        let textoAforo = "";

        if (llena) {
          textoAforo = `<span class="badge-aforo rojo"><span class="indicador-dot rojo"></span> Cupo Agotado</span>`;
        } else if (color === "ambar") {
          textoAforo = `<span class="badge-aforo ambar"><span class="indicador-dot ambar"></span> Últimos ${c.lugares_disponibles} cupos</span>`;
        } else {
          textoAforo = `<span class="badge-aforo verde"><span class="indicador-dot verde"></span> ${c.lugares_disponibles} cupos disponibles</span>`;
        }

        return `
          <article class="tarjeta-clase glass-panel ${color}">
            <div class="clase-cabecera">
              <h3 class="clase-titulo">${escapar(c.nombre)}</h3>
              <span class="clase-codigo">${escapar(c.id)}</span>
            </div>

            <div class="clase-horario">
              ${ICONOS.clock}
              <span>${hora(c.horario_inicio)} – ${hora(c.horario_fin)}</span>
            </div>

            <div class="clase-pie">
              ${textoAforo}
              <button class="btn ${llena ? "btn-vidrio" : "btn-gradiente"} btn-ancho"
                      data-reservar="${escapar(c.id)}"
                      data-nombre="${escapar(c.nombre)}"
                      ${llena ? "disabled" : ""}>
                <span>${llena ? "Sin Disponibilidad" : "Apartar Lugar"}</span>
              </button>
            </div>
          </article>
        `;
      })
      .join("");
  } catch (error) {
    contenedor.innerHTML = `
      <div class="estado-vacio glass-panel">
        <p>No fue posible cargar las sesiones grupales.</p>
      </div>`;
    avisar(error.message, "error", error.solucion);
  }
}

$("lista-clases").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-reservar]");
  if (!boton) return;

  const claseId = boton.dataset.reservar;
  const esRecepcion = sesion.rol === "Recepción";

  const respuesta = await preguntar({
    titulo: `Reservar en ${boton.dataset.nombre}`,
    texto: esRecepcion
      ? "Indica el número de socio que tomará la sesión:"
      : "¿Deseas apartar tu lugar formal en esta sesión deportiva?",
    textoSi: "Confirmar Lugar",
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
    avisar(`${r.mensaje} (${socioId} asignado a ${claseId})`, "exito");
    await cargarClases();
  });
});

// ---------------------------------------------------------
// 10. FICHA DEL SOCIO Y GESTIÓN DE ACCESOS
// ---------------------------------------------------------
function prepararVistaSocio() {
  const esRecepcion = sesion.rol === "Recepción";
  $("form-buscar").hidden = !esRecepcion;
  $("titulo-socio").textContent = esRecepcion ? "Consulta de Membresía y Socios" : "Mi Estatus de Membresía";

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
    avisar("El identificador del socio no tiene el formato requerido.", "error", "Ejemplo: FIT-C001");
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
  let estadoTitulo, estadoSub, claseTipo, consejo = "";

  if (m.vigente) {
    estadoTitulo = "Membresía Activa y Vigente";
    estadoSub = "Acceso a instalaciones y reservas habilitado";
    claseTipo = "ok";
  } else if (m.suspendida) {
    estadoTitulo = "Membresía Suspendida";
    estadoSub = "Temporalmente inhabilitada para reservaciones";
    claseTipo = "mal";
    consejo = "Cuenta pausada. Acude al mostrador de recepción para reactivar tu plan.";
  } else {
    estadoTitulo = "Membresía Vencida";
    estadoSub = "Periodo de vigencia concluido";
    claseTipo = "mal";
    consejo = "Tu suscripción ha expirado. Renueva tu contrato para agendar clases.";
  }

  const iconoHeader = m.vigente ? ICONOS.shieldCheck : ICONOS.shieldAlert;

  tarjeta.className = "tarjeta-membresia-moderna glass-panel " + claseTipo;
  tarjeta.innerHTML = `
    <div class="membresia-header">
      <div class="icono-circulo-estado ${claseTipo}">
        ${iconoHeader}
      </div>
      <div>
        <h3 class="membresia-estado-texto">${estadoTitulo}</h3>
        <span class="membresia-sub-estado">${estadoSub}</span>
      </div>
    </div>

    <div class="membresia-detalles-grid">
      <div class="detalle-item">
        <span class="etiqueta">Socio Titular</span>
        <span class="valor">${escapar(m.socio_id)}</span>
      </div>
      <div class="detalle-item">
        <span class="etiqueta">Plan Asignado</span>
        <span class="valor">${escapar(m.plan_id)}</span>
      </div>
      <div class="detalle-item">
        <span class="etiqueta">Inicio de Periodo</span>
        <span class="valor">${fecha(m.inicio_vigencia)}</span>
      </div>
      <div class="detalle-item">
        <span class="etiqueta">Vencimiento</span>
        <span class="valor">${fecha(m.fin_vigencia)}</span>
      </div>
    </div>

    ${consejo ? `
      <div class="alerta-consejo">
        ${ICONOS.alert}
        <span>${escapar(consejo)}</span>
      </div>
    ` : ""}
  `;
}

const NOMBRE_ESTADO = {
  SOLICITADA: "Solicitada",
  ACTIVA: "Activa",
  CANCELADA: "Cancelada",
  ASISTIDA: "Asistencia Confirmada",
  NO_SHOW: "Falta Registrada",
};

function dibujarReservas(socioId, reservas) {
  const lista = $("lista-reservas");
  if (!reservas || reservas.length === 0) {
    lista.innerHTML = `
      <div class="estado-vacio glass-panel">
        <p>No se registran reservaciones pasadas o activas para este socio.</p>
      </div>`;
    return;
  }

  const esRecepcion = sesion.rol === "Recepción";

  lista.innerHTML = reservas
    .map((r) => {
      const activa = r.estado === "ACTIVA";
      const botones = activa
        ? `
        <div class="reserva-acciones-botones">
          ${esRecepcion ? `
            <button class="btn btn-exito btn-chico" data-accion="asistencia"
                    data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">
              ${ICONOS.check}
              <span>Validar Acceso</span>
            </button>` : ""}
          <button class="btn btn-peligro btn-chico" data-accion="cancelar"
                  data-clase="${escapar(r.clase_id)}" data-socio="${escapar(socioId)}">
            ${ICONOS.x}
            <span>Cancelar</span>
          </button>
        </div>`
        : "";

      return `
        <div class="tarjeta-reserva-fila glass-panel">
          <div class="reserva-info-principal">
            <div class="reserva-icono-caja">
              ${ICONOS.dumbbell}
            </div>
            <div>
              <div class="reserva-titulo-linea">Sesión ${escapar(r.clase_id)}</div>
              <div class="reserva-fecha-creacion">Registro: ${r.fecha_creacion ? fecha(r.fecha_creacion) : "—"}</div>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
            <span class="reserva-estado-pill ${escapar(r.estado)}">
              ${NOMBRE_ESTADO[r.estado] || escapar(r.estado)}
            </span>
            ${botones}
          </div>
        </div>
      `;
    })
    .join("");
}

$("lista-reservas").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-accion]");
  if (!boton) return;

  const { accion, clase, socio } = boton.dataset;
  const esCancelar = accion === "cancelar";

  const respuesta = await preguntar({
    titulo: esCancelar ? "¿Cancelar esta reservación?" : "¿Confirmar asistencia en puerta?",
    texto: esCancelar
      ? `Se liberará inmediatamente el cupo del socio ${socio} en la sesión ${clase}. Esta operación es definitiva.`
      : `Registra el ingreso formal del socio ${socio} a la sesión deportiva ${clase}.`,
    textoSi: esCancelar ? "Confirmar Cancelación" : "Validar Ingreso",
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
// 11. INICIALIZACIÓN
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

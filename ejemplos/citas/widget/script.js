/* Citas Kommo10K 2.0 — la cáscara.
 *
 * La agenda vive en nuestro servidor y se abre en un iframe. Este widget
 * solo la monta dentro de Kommo:
 *   · Configuración → Integraciones → Citas Kommo10K: la agenda completa
 *   · ficha del lead, panel derecho: sus citas y «Agendar cita»
 * No llama a la API de Kommo: gasta 0 solicitudes. Lo que la agenda escribe
 * en Kommo lo hace el servidor, por su torniquete. Cambiar la agenda no
 * obliga a subir otro ZIP.
 *
 * Credenciales: el token de Kommo se pega UNA vez en los ajustes y se canjea
 * por la clave de la cuenta, que solo abre la agenda. El token se borra del
 * formulario antes de guardar: Kommo guarda la clave, nunca el token. Con la
 * clave se pide un ticket de 15 minutos; el iframe solo ve el ticket, en el
 * #hash (no viaja al servidor ni en el Referer).
 */
define(['jquery'], function ($) {
  'use strict';

  var API = 'https://widget.tudominio.com';   // fija: nadie en la página puede desviar la clave
  var ORIGEN = API.replace(/^(https?:\/\/[^/]+).*$/, '$1');
  var escuchando = false;

  return function () {
    var self = this;

    function ajustes() { return self.get_settings() || {}; }
    function codigo() { return ajustes().widget_code; }
    function cuenta() { return (self.system() || {}).subdomain; }
    function usuario() { var s = self.system() || {}; return s.amouser_id || s.user_id || ''; }
    function esc(v) {
      return String(v === null || v === undefined ? '' : v).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    }
    function aviso(texto) {
      return '<div style="padding:12px 14px;border:1px solid #f0d58c;background:#fff8e1;color:#7a5200;border-radius:8px;font:13px/1.45 system-ui,sans-serif">' + esc(texto) + '</div>';
    }

    /* La clave la guarda Kommo en los ajustes (la ven todos los usuarios de
     * la cuenta). localStorage solo cubre el rato entre «Conectar» y
     * «Guardar» en el navegador del administrador. */
    function clave() {
      if (ajustes().clave) { return ajustes().clave; }
      try { return localStorage.getItem('k10k_clave_' + cuenta()) || ''; } catch (e) { return ''; }
    }
    /* Con `lead`, el ticket es de la ficha: solo abre ese lead, así copiar la
     * URL del iframe de una ficha no da la agenda entera. */
    function ticket(lead) {
      var k = clave();
      if (!k) { return $.Deferred().reject({ sinClave: true }).promise(); }
      return $.ajax({ url: API + '/v1/embed/sesion', method: 'POST', dataType: 'json', timeout: 15000,
                      contentType: 'application/json', data: JSON.stringify(lead ? { lead: +lead } : {}),
                      headers: { 'X-Kommo-Clave': k } }).then(function (r) { return r.ticket; });
    }
    function motivo(x) {
      if (x && (x.sinClave || x.status === 403)) {
        return 'La agenda todavía no está conectada. Un administrador debe abrir los ajustes de esta integración, pegar el token de Kommo y presionar «Conectar».';
      }
      return 'No pudimos abrir la agenda. Revisa tu conexión y vuelve a abrir esta página.';
    }

    /* El iframe pide otro ticket cuando el suyo vence, y avisa su alto para
     * que el panel de la ficha crezca con él. Solo se atiende a nuestro
     * servidor. */
    function escuchar() {
      if (escuchando) { return; }
      escuchando = true;
      window.addEventListener('message', function (ev) {
        if (ev.origin !== ORIGEN || !ev.data) { return; }
        if (ev.data.k10k === 'renovar') {
          ticket(ev.data.lead).then(function (t) { ev.source.postMessage({ k10kTicket: t }, ORIGEN); },
                                    function () { ev.source.postMessage({ k10kTicket: null }, ORIGEN); });
        } else if (ev.data.k10kAlto) {
          $('iframe.k10k-agenda').each(function () {
            if (this.contentWindow === ev.source) { this.style.height = Math.min(Math.max(+ev.data.k10kAlto, 140), 2400) + 'px'; }
          });
        }
      });
    }

    function iframe(consulta, t, alto) {
      return '<iframe class="k10k-agenda" title="Agenda de citas" allow="clipboard-write" src="' +
        esc(API + '/embed?u=' + encodeURIComponent(usuario()) + consulta + '#' + t) +
        '" style="display:block;width:100%;height:' + alto + ';border:0;background:#fff"></iframe>';
    }

    /* El contenedor de la página propia cambia de nombre entre versiones de
     * Kommo: se prueban los conocidos y, si no, se crea uno. */
    function caja() {
      var c = codigo(), intentos = ['#work-area-' + c, '.work-area-' + c, '#widget_' + c, '#' + c];
      for (var i = 0; i < intentos.length; i++) { var $x = $(intentos[i]); if ($x.length) { return $x.first(); } }
      var $p = $('#k10k-area');
      if (!$p.length) {
        $p = $('<div id="k10k-area"></div>');
        $('.work-area, #work-area, #page_holder, #content, body').first().append($p);
      }
      return $p;
    }

    var pintada = false;
    function pagina() {
      pintada = true;
      escuchar();
      var $c = caja();
      $c.html(aviso('Abriendo la agenda…'));
      ticket().then(function (t) { $c.html(iframe('', t, 'calc(100vh - 110px)')); },
                    function (x) { $c.html(aviso(motivo(x))); });
    }
    function pintarSiEsMiPagina() {
      if (!pintada && $('#work-area-' + codigo()).length) { pagina(); }
    }

    function tarjeta() {
      var id = (location.pathname.match(/leads\/detail\/(\d+)/) || [])[1];
      var sel = 'js-k10k-' + codigo(), $d = $('.' + sel);
      if ($d.length && $d.attr('data-lead') === String(id || '')) { return; }   // mismo lead: no recargar
      if (!$d.length) {
        self.render_template({ caption: { class_name: 'k10k-caption' },
                               body: '<div class="' + sel + '"></div>', render: '' }, { w_code: codigo() });
        $d = $('.' + sel);
      }
      $d.attr('data-lead', id || '');
      if (!id || id === '0') { $d.html(aviso('Guarda el lead para poder agendarle una cita.')); return; }
      escuchar();
      $d.html(aviso('Cargando citas…'));
      ticket(id).then(function (t) { $d.html(iframe('&lead=' + encodeURIComponent(id), t, '260px')); },
                    function (x) { $d.html(aviso(motivo(x))); });
    }

    /* Ventana de ajustes: estado de la conexión y el botón que canjea el
     * token por la clave. El token nunca queda guardado. */
    function campo($m, nombre) { return $m.find('input[name="' + nombre + '"]'); }
    function ventana($modal) {
      var $m = $modal && $modal.find ? $modal : $('.modal.' + codigo());
      var $b = $m.find('.widget_settings_block').first();
      if (!$b.length) { return; }
      campo($m, 'clave').prop('readonly', true);
      $b.find('.k10k-conexion').remove();
      var conectada = !!clave();
      $b.prepend('<div class="k10k-conexion" style="margin:0 0 14px;padding:12px 14px;border-radius:8px;font:13px/1.45 system-ui,sans-serif;' +
        (conectada ? 'background:#e6f6f0;color:#0b5e47' : 'background:#fff8e1;color:#7a5200') + '">' +
        '<b>' + (conectada ? 'Agenda conectada' : 'Falta conectar la agenda') + '</b>' +
        '<p style="margin:4px 0 8px">' + (conectada
          ? 'Para cambiar el token, pégalo abajo y presiona «Conectar».'
          : 'Pega el token de larga duración de esta integración (pestaña «Claves y alcances») en el campo Token y presiona «Conectar». Después, «Guardar».') + '</p>' +
        '<button type="button" class="button-input k10k-conectar">Conectar</button> <span class="k10k-resultado"></span></div>');
      $b.find('.k10k-conectar').on('click', function () {
        var $boton = $(this), $res = $b.find('.k10k-resultado'), token = $.trim(campo($m, 'token').val() || '');
        if (!token) { $res.text('Primero pega el token.'); return; }
        $boton.prop('disabled', true); $res.text('Conectando…');
        $.ajax({ url: API + '/v1/clave', method: 'POST', contentType: 'application/json', dataType: 'json', timeout: 30000,
                 data: JSON.stringify({ cuenta: cuenta(), token: token, widget: 'citas' }) })
          .then(function (r) {
            campo($m, 'token').val('').trigger('change');
            campo($m, 'clave').val(r.clave).trigger('input').trigger('change');
            try { localStorage.setItem('k10k_clave_' + cuenta(), r.clave); } catch (e) { /* sin almacenamiento */ }
            $res.text('Conectado. Ahora presiona «Guardar».');
          }, function (x) {
            $res.text((x && x.responseJSON && x.responseJSON.detail) || 'No se pudo validar el token.');
          })
          .always(function () { $boton.prop('disabled', false); });
      });
    }

    function seguro(nombre, fn) {
      try { return fn(); } catch (e) { try { window.console && console.error('[Citas Kommo10K] ' + nombre, e); } catch (x) { /* nada */ } return true; }
    }

    this.callbacks = {
      render: function () {
        seguro('render', function () {
          if ((self.system() || {}).area === 'lcard') { tarjeta(); }
          setTimeout(pintarSiEsMiPagina, 400);
        });
        return true;
      },
      init: function () { setTimeout(pintarSiEsMiPagina, 800); return true; },
      bind_actions: function () { return true; },
      settings: function ($modal) { seguro('settings', function () { ventana($modal); }); return true; },
      onSave: function () {
        // Un token escrito y sin «Conectar» NO se guarda en Kommo
        if ($.trim(campo($('.modal.' + codigo()), 'token').val() || '')) {
          if (window.alert) { window.alert('Presiona «Conectar» antes de guardar: el token no se guarda en Kommo.'); }
          return false;
        }
        return true;
      },
      destroy: function () { pintada = false; return true; },
      advancedSettings: function () { seguro('advancedSettings', pagina); return true; }
    };
    return this;
  };
});

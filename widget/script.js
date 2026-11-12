/* Cáscara del widget: no guarda datos ni tokens. Conecta la cuenta una vez,
 * pide tickets cortos al servidor y muestra la página del servidor en un iframe.
 * Cambia API por tu dominio antes de armar el ZIP (lo hace build.sh). */
define(['jquery'], function ($) {
  'use strict';
  var API = 'https://widget.tudominio.com';
  var ORIGEN = API.replace(/^(https?:\/\/[^/]+).*$/, '$1');
  var escuchando = false;

  return function () {
    var self = this;
    function ajustes() { return self.get_settings() || {}; }
    function codigo() { return ajustes().widget_code; }
    function cuenta() { return (self.system() || {}).subdomain; }
    function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]; }); }
    function aviso(t) {
      return '<div style="padding:12px 14px;border:1px solid #e4e6ed;background:#f7f8fb;border-radius:8px;font:13px system-ui">' + esc(t) + '</div>';
    }

    // La clave (no el token) es lo único que queda en los ajustes de Kommo.
    function ticket(lead) {
      var clave = ajustes().clave;
      if (!clave) return $.Deferred().reject().promise();
      return $.ajax({url: API + '/v1/sesion', method: 'POST', dataType: 'json', timeout: 15000,
        contentType: 'application/json', data: JSON.stringify(lead ? {lead: +lead} : {}),
        headers: {'X-Widget-Clave': clave}}).then(function (r) { return r.ticket; });
    }

    // El iframe pide un ticket nuevo cuando el suyo vence y avisa su altura.
    function escuchar() {
      if (escuchando) return;
      escuchando = true;
      window.addEventListener('message', function (ev) {
        if (ev.origin !== ORIGEN || !ev.data) return;
        if (ev.data.kw === 'renovar') {
          ticket(ev.data.lead).then(function (t) { ev.source.postMessage({kwTicket: t}, ORIGEN); },
                                    function () { ev.source.postMessage({kwTicket: null}, ORIGEN); });
        } else if (ev.data.kwAlto) {
          $('iframe.kw-iframe').each(function () {
            if (this.contentWindow === ev.source) this.style.height = Math.min(Math.max(+ev.data.kwAlto, 240), 1800) + 'px';
          });
        }
      });
    }

    // El ticket va en el #hash: el navegador no lo manda al servidor ni a sus logs.
    function iframe(t, lead, alto) {
      return '<iframe class="kw-iframe" title="Widget" src="' + esc(API + '/app' + (lead ? '?lead=' + lead : '') + '#' + t) +
        '" style="display:block;width:100%;height:' + alto + ';border:0"></iframe>';
    }

    // Pantalla completa: Ajustes → Integraciones → el widget (advanced_settings).
    function pagina() {
      escuchar();
      var $c = $('#work-area-' + codigo());
      $c.html(aviso('Abriendo…'));
      ticket().then(function (t) { $c.html(iframe(t, null, 'calc(100vh - 110px)')); },
                    function () { $c.html(aviso('Un administrador debe conectar el widget desde sus ajustes.')); });
    }

    // Columna derecha de la ficha del lead: solo los datos de ESE lead.
    function tarjeta() {
      var id = (location.pathname.match(/leads\/detail\/(\d+)/) || [])[1];
      self.render_template({caption: {class_name: 'kw-caption'}, body: '<div class="kw-ficha"></div>', render: ''});
      var $d = $('.kw-ficha');
      if (!id) { $d.html(aviso('Guarda el lead para ver sus datos.')); return; }
      escuchar();
      ticket(id).then(function (t) { $d.html(iframe(t, id, '480px')); },
                      function () { $d.html(aviso('Un administrador debe conectar el widget.')); });
    }

    // Ajustes: se pega el token una vez, el servidor lo valida y devuelve la clave.
    function ventana($modal) {
      var $b = $modal.find('.widget_settings_block').first();
      $b.find('.kw-conectar').remove();
      $b.prepend('<div class="kw-conectar" style="margin:0 0 14px;font:13px system-ui">' +
        '<button type="button" class="button-input">Conectar</button> <span class="kw-res"></span></div>');
      $b.find('.kw-conectar button').on('click', function () {
        var $t = $modal.find('input[name="token"]'), $res = $b.find('.kw-res'), token = $.trim($t.val() || '');
        if (!token) { $res.text('Primero pega el token.'); return; }
        $res.text('Conectando…');
        $.ajax({url: API + '/v1/conectar', method: 'POST', contentType: 'application/json', dataType: 'json',
          data: JSON.stringify({cuenta: cuenta(), token: token})}).then(function (r) {
            $t.val('').trigger('change');
            $modal.find('input[name="clave"]').val(r.clave).trigger('change');
            $res.text('Conectado. Ahora presiona «Guardar».');
          }, function (x) { $res.text((x.responseJSON && x.responseJSON.detail) || 'No se pudo validar el token.'); });
      });
    }

    this.callbacks = {
      render: function () { if ((self.system() || {}).area === 'lcard') tarjeta(); return true; },
      init: function () { return true; },
      bind_actions: function () { return true; },
      settings: function ($modal) { ventana($modal); return true; },
      onSave: function () {
        if ($.trim($('.modal input[name="token"]').val() || '')) {
          alert('Presiona «Conectar» antes de guardar: el token no se guarda en Kommo.');
          return false;
        }
        return true;
      },
      advancedSettings: function () { pagina(); return true; },
      destroy: function () { return true; }
    };
    return this;
  };
});

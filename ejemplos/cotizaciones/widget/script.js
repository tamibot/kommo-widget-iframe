/* Cáscara de Cotizaciones Kommo10K. Los datos viven en el servidor y el
 * ticket breve se limita al lead cuando se abre desde su ficha. */
define(['jquery'], function ($) {
  'use strict';
  var API = window.K10K_API || 'https://widget.tudominio.com';
  var ORIGEN = API.replace(/^(https?:\/\/[^/]+).*$/, '$1');
  var escuchando = false;

  return function () {
    var self = this;
    function ajustes() { return self.get_settings() || {}; }
    function codigo() { return ajustes().widget_code; }
    function cuenta() { return (self.system() || {}).subdomain; }
    function usuario() { var s = self.system() || {}; return s.amouser_id || s.user_id || ''; }
    function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    }); }
    function aviso(texto) { return '<div style="padding:12px 14px;border:1px solid #e4e6ed;background:#f7f8fb;color:#454b60;border-radius:8px;font:13px/1.45 system-ui,sans-serif">' + esc(texto) + '</div>'; }
    function clave() {
      if (ajustes().clave) return ajustes().clave;
      try { return localStorage.getItem('k10k_cotizaciones_' + cuenta()) || ''; } catch (e) { return ''; }
    }
    function ticket(lead) {
      var k = clave();
      if (!k) return $.Deferred().reject({sinClave:true}).promise();
      return $.ajax({url:API + '/v1/embed/sesion',method:'POST',dataType:'json',timeout:15000,
        contentType:'application/json',data:JSON.stringify(lead ? {lead:+lead} : {}),
        headers:{'X-Kommo-Clave':k}}).then(function(r){return r.ticket;});
    }
    function escuchar() {
      if (escuchando) return;
      escuchando = true;
      window.addEventListener('message', function(ev) {
        if (ev.origin !== ORIGEN || !ev.data) return;
        if (ev.data.k10k === 'renovar') {
          ticket(ev.data.lead).then(function(t){ev.source.postMessage({k10kTicket:t},ORIGEN);},
                                    function(){ev.source.postMessage({k10kTicket:null},ORIGEN);});
        } else if (ev.data.k10kAlto) {
          $('iframe.k10k-cotizaciones').each(function(){
            if (this.contentWindow === ev.source) this.style.height = Math.min(Math.max(+ev.data.k10kAlto,240),1800)+'px';
          });
        }
      });
    }
    function marco(t, lead, alto) {
      var q = '?u='+encodeURIComponent(usuario())+(lead?'&lead='+encodeURIComponent(lead):'');
      return '<iframe class="k10k-cotizaciones" title="Cotizaciones del cliente" allow="clipboard-write" src="'+
        esc(API + '/cotizaciones'+q+'#'+t)+'" style="display:block;width:100%;height:'+alto+';border:0;background:#f6f7fb"></iframe>';
    }
    function caja() {
      var c=codigo(), intentos=['#work-area-'+c,'.work-area-'+c,'#widget_'+c,'#'+c];
      for(var i=0;i<intentos.length;i++){var $x=$(intentos[i]);if($x.length)return $x.first();}
      var $p=$('#k10k-cotizaciones-area');
      if(!$p.length){$p=$('<div id="k10k-cotizaciones-area"></div>');$('.work-area,#work-area,#page_holder,#content,body').first().append($p);}
      return $p;
    }
    var pintada=false;
    function pagina(){pintada=true;escuchar();var $c=caja();$c.html(aviso('Abriendo cotizaciones…'));
      ticket().then(function(t){$c.html(marco(t,null,'calc(100vh - 110px)'));},function(){$c.html(aviso('Un administrador debe conectar Cotizaciones Kommo10K desde sus ajustes.'));});}
    function paginaActual(){if(!pintada&&$('#work-area-'+codigo()).length)pagina();}
    function tarjeta(){
      var id=(location.pathname.match(/leads\/detail\/(\d+)/)||[])[1],sel='js-k10k-cotizaciones-'+codigo(),$d=$('.'+sel);
      if($d.length&&$d.attr('data-lead')===String(id||''))return;
      if(!$d.length){self.render_template({caption:{class_name:'k10k-caption'},body:'<div class="'+sel+'"></div>',render:''},{w_code:codigo()});$d=$('.'+sel);}
      $d.attr('data-lead',id||'');if(!id){$d.html(aviso('Guarda el lead para registrar sus cotizaciones.'));return;}
      escuchar();$d.html(aviso('Cargando cotizaciones…'));
      ticket(id).then(function(t){$d.html(marco(t,id,'620px'));},function(){$d.html(aviso('Un administrador debe conectar Cotizaciones Kommo10K desde sus ajustes.'));});
    }
    function campo($m,n){return $m.find('input[name="'+n+'"]');}
    function ventana($modal){
      var $m=$modal&&$modal.find?$modal:$('.modal.'+codigo()),$b=$m.find('.widget_settings_block').first();if(!$b.length)return;
      campo($m,'clave').prop('readonly',true);$b.find('.k10k-conexion').remove();
      var conectada=!!clave();
      $b.prepend('<div class="k10k-conexion" style="margin:0 0 14px;padding:12px 14px;border-radius:8px;font:13px/1.45 system-ui,sans-serif;'+
        (conectada?'background:#e6f6f0;color:#0b5e47':'background:#fff8e1;color:#7a5200')+'"><b>'+(conectada?'Widget conectado':'Falta conectar el widget')+
        '</b><p style="margin:4px 0 8px">'+(conectada?'Para cambiar el token, pégalo abajo y presiona «Conectar».':'Pega el token de larga duración de esta integración y presiona «Conectar». Después, «Guardar».')+
        '</p><button type="button" class="button-input k10k-conectar">Conectar</button> <span class="k10k-resultado"></span></div>');
      $b.find('.k10k-conectar').on('click',function(){var $btn=$(this),$res=$b.find('.k10k-resultado'),token=$.trim(campo($m,'token').val()||'');
        if(!token){$res.text('Primero pega el token.');return;}$btn.prop('disabled',true);$res.text('Conectando…');
        $.ajax({url:API + '/v1/clave',method:'POST',contentType:'application/json',dataType:'json',timeout:30000,
          data:JSON.stringify({cuenta:cuenta(),token:token,widget:'cotizaciones'})}).then(function(r){
            campo($m,'token').val('').trigger('change');campo($m,'clave').val(r.clave).trigger('input').trigger('change');
            try{localStorage.setItem('k10k_cotizaciones_'+cuenta(),r.clave);}catch(e){}$res.text('Conectado. Ahora presiona «Guardar».');
          },function(x){$res.text((x&&x.responseJSON&&x.responseJSON.detail)||'No se pudo validar el token.');})
          .always(function(){$btn.prop('disabled',false);});
      });
    }
    function seguro(nombre,fn){try{return fn();}catch(e){try{window.console&&console.error('[Cotizaciones Kommo10K] '+nombre,e);}catch(x){}return true;}}
    this.callbacks={
      render:function(){seguro('render',function(){if((self.system()||{}).area==='lcard')tarjeta();setTimeout(paginaActual,400);});return true;},
      init:function(){setTimeout(paginaActual,800);return true;},bind_actions:function(){return true;},
      settings:function($modal){seguro('settings',function(){ventana($modal);});return true;},
      onSave:function(){if($.trim(campo($('.modal.'+codigo()),'token').val()||'')){if(window.alert)window.alert('Presiona «Conectar» antes de guardar: el token no se guarda en Kommo.');return false;}return true;},
      destroy:function(){pintada=false;return true;},advancedSettings:function(){seguro('advancedSettings',pagina);return true;}
    };
    return this;
  };
});

(() => {
  const money = c => '€ ' + (c / 100).toLocaleString('nl-NL', { minimumFractionDigits: c % 100 ? 2 : 0 });

  // Galerij
  document.querySelectorAll('[data-gallery]').forEach(g => {
    const slides = [...g.querySelectorAll('[data-slide]')], thumbs = [...g.querySelectorAll('[data-thumb]')];
    let i = 0;
    const go = n => { i = (n + slides.length) % slides.length; slides.forEach((s, k) => s.classList.toggle('is-active', k === i)); thumbs.forEach((t, k) => t.classList.toggle('is-active', k === i)); };
    g.querySelector('[data-prev]')?.addEventListener('click', () => go(i - 1));
    g.querySelector('[data-next]')?.addEventListener('click', () => go(i + 1));
    thumbs.forEach((t, k) => t.addEventListener('click', () => go(k)));
    g._go = go; g._slides = slides;
  });

  // Variantkeuze
  document.querySelectorAll('[data-product]').forEach(root => {
    const sid = root.dataset.section;
    const product = JSON.parse(document.getElementById('product-json-' + sid).textContent);
    const form = document.getElementById('product-form-' + sid);
    const idInput = root.querySelector('[data-variant-id]');
    const tierName = root.dataset.tierOption, colorName = root.dataset.colorOption;
    const tierIdx = product.options.indexOf(tierName), colorIdx = product.options.indexOf(colorName);
    const selected = () => product.options.map(name => (root.querySelector('input[name="' + CSS.escape(name) + '"]:checked') || {}).value);
    const find = vals => product.variants.find(v => v.options.every((o, k) => o === vals[k]));
    const base = product.variants[0];

    const update = () => {
      const vals = selected(), v = find(vals);
      // prijs per uitvoering (bij huidige kleur) en meerprijs per kleur (bij huidige uitvoering)
      root.querySelectorAll('[data-tier-price]').forEach(el => { const o = [...vals]; o[tierIdx] = el.dataset.tierPrice; const m = find(o); el.textContent = m ? money(m.price) : ''; });
      root.querySelectorAll('[data-color-extra]').forEach(el => {
        const o = [...vals]; o[colorIdx] = el.dataset.colorExtra; const m = find(o);
        const o0 = [...vals]; o0[colorIdx] = product.options_with_values?.[colorIdx]?.values?.[0] ?? base.options[colorIdx]; const b = find(o0);
        const diff = m && b ? m.price - b.price : 0; el.textContent = diff > 0 ? ' + ' + money(diff) : '';
      });
      if (!v) return;
      idInput.value = v.id;
      root.querySelectorAll('[data-price]').forEach(el => el.textContent = money(v.price));
      root.querySelectorAll('[data-summary]').forEach(el => el.textContent = product.title + ' ' + v.title.replace(' / ', ', '));
      const btn = root.querySelector('[data-add]'); if (btn) btn.disabled = !v.available;
      if (v.featured_media) { const g = root.querySelector('[data-gallery]'); const idx = product.media.filter(m => m.media_type === 'image').findIndex(m => m.id === v.featured_media.id); if (g && idx > -1) g._go(idx); }
      const url = new URL(location.href); url.searchParams.set('variant', v.id); history.replaceState(null, '', url);
    };
    root.addEventListener('change', e => { if (e.target.matches('input[type=radio]')) update(); });
    update();

    // Toevoegen aan winkelwagen zonder pagina-herlaad
    form?.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = form.querySelector('[data-add]'); btn.disabled = true;
      try {
        const res = await fetch(window.Shopify?.routes?.root + 'cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ items: [{ id: +idInput.value, quantity: 1 }] }) });
        if (!res.ok) throw new Error((await res.json()).description);
        const cart = await (await fetch(window.Shopify?.routes?.root + 'cart.js')).json();
        document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = cart.item_count; el.hidden = cart.item_count === 0; });
        const t = document.querySelector('[data-cart-toast]');
        if (t) { t.querySelector('[data-cart-toast-text]').textContent = root.querySelector('[data-summary]').textContent + ' is toegevoegd aan je winkelwagen.'; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 4000); }
      } catch (err) { form.submit(); }
      finally { btn.disabled = false; }
    });
  });

  // Mobiel menu sluiten bij klik buiten
  document.addEventListener('click', e => { document.querySelectorAll('.mobile-nav[open]').forEach(d => { if (!d.contains(e.target)) d.removeAttribute('open'); }); });
})();

// Afspraak plannen: Cal.com inline embed, pas geladen na een klik.
(() => {
  const track = (event, data = {}) => { if (Array.isArray(window.dataLayer)) window.dataLayer.push({ event, ...data }); };

  // Interesse meegeven vanaf een productpagina: "Bali Premium, White".
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href*="#afspraak"]');
    const summary = document.querySelector('[data-summary]');
    if (!link || !summary) return;
    const url = new URL(link.href, location.href);
    url.searchParams.set('interesse', summary.textContent.trim());
    link.href = url.toString();
  });

  document.querySelectorAll('[data-booking]').forEach((root) => {
    const target = root.querySelector('[data-booking-target]');
    const button = root.querySelector('[data-booking-load]');
    const origin = root.dataset.calOrigin || 'https://cal.com';
    const script = origin.replace('https://', 'https://app.') + '/embed/embed.js';

    button?.addEventListener('click', () => {
      // Officiële Cal.com-loader (namespace "spatime").
      (function (C, A, L) { const p = function (a, ar) { a.q.push(ar); }; const d = C.document; C.Cal = C.Cal || function () { const cal = C.Cal; const ar = arguments; if (!cal.loaded) { cal.ns = {}; cal.q = cal.q || []; d.head.appendChild(d.createElement('script')).src = A; cal.loaded = true; } if (ar[0] === L) { const api = function () { p(api, arguments); }; const namespace = ar[1]; api.q = api.q || []; if (typeof namespace === 'string') { cal.ns[namespace] = cal.ns[namespace] || api; p(cal.ns[namespace], ar); p(cal, ['initNamespace', namespace]); } else p(cal, ar); return; } p(cal, ar); }; })(window, script, 'init');

      const interest = new URLSearchParams(location.search).get('interesse');
      const config = { layout: 'month_view', theme: 'light' };
      if (interest) config.notes = 'Interesse: ' + interest;

      target.innerHTML = '';
      target.classList.add('is-loaded');
      const mount = document.createElement('div');
      mount.id = 'spatime-cal-' + Math.random().toString(36).slice(2);
      target.appendChild(mount);

      window.Cal('init', 'spatime', { origin });
      window.Cal.ns.spatime('inline', { elementOrSelector: '#' + mount.id, calLink: root.dataset.calLink, config });
      window.Cal.ns.spatime('ui', { theme: 'light', cssVarsPerTheme: { light: { 'cal-brand': '#946E42' } }, hideEventTypeDetails: false, layout: 'month_view' });
      window.Cal.ns.spatime('on', { action: 'bookingSuccessfulV2', callback: () => track('generate_lead', { method: 'showroom_booking', interest: interest || '' }) });
      track('booking_open');
    });
  });
})();

(() => {
  // Locale, currency and UI strings come from the theme (layout/theme.liquid → window.SpaTime).
  const cfg = window.SpaTime || {};
  const money = c => new Intl.NumberFormat(cfg.locale || 'nl-NL', { style: 'currency', currency: cfg.currency || 'EUR', minimumFractionDigits: c % 100 ? 2 : 0 }).format(c / 100);

  // Galerij
  document.querySelectorAll('[data-gallery]').forEach(g => {
    const slides = [...g.querySelectorAll('[data-slide]')], thumbs = [...g.querySelectorAll('[data-thumb]')];
    let i = Math.max(0, slides.findIndex(s => s.classList.contains('is-active')));
    const go = n => { i = (n + slides.length) % slides.length; slides.forEach((s, k) => s.classList.toggle('is-active', k === i)); thumbs.forEach((t, k) => t.classList.toggle('is-active', k === i)); };
    // door de bezoeker gekozen foto → event, zodat de variantkeuze kan meeschakelen
    const pick = n => { go(n); g.dispatchEvent(new CustomEvent('gallery:pick', { detail: i })); };
    g.querySelector('[data-prev]')?.addEventListener('click', () => pick(i - 1));
    g.querySelector('[data-next]')?.addEventListener('click', () => pick(i + 1));
    thumbs.forEach((t, k) => t.addEventListener('click', () => pick(k)));
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

    let prev = selected(), last = prev;  // vorige keuze, voor de foto → variant-koppeling hieronder
    const update = (first = false) => {
      const vals = selected(), v = find(vals);
      if (vals.join() !== last.join()) { prev = last; last = vals; }
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
      // foto van de variant tonen; variant zonder eigen foto → hoofdfoto (niet bij eerste keer laden)
      const g = root.querySelector('[data-gallery]');
      if (g && (v.featured_media || !first)) { const idx = v.featured_media ? product.media.filter(m => m.media_type === 'image').findIndex(m => m.id === v.featured_media.id) : 0; if (idx > -1) g._go(idx); }
      const url = new URL(location.href); url.searchParams.set('variant', v.id); history.replaceState(null, '', url);
    };
    root.addEventListener('change', e => { if (e.target.matches('input[type=radio]')) update(); });
    update(true);

    // Andersom: foto gekozen die bij een of meer varianten hoort → die variant selecteren. Bij meerdere
    // kandidaten (bijv. één marmerfoto voor Comfort én Premium) wint de variant die het meest op de
    // huidige keuze lijkt, bij gelijke stand die op de vorige keuze; zo verandert alleen wat bij de foto hoort.
    const images = product.media.filter(m => m.media_type === 'image');
    root.querySelector('[data-gallery]')?.addEventListener('gallery:pick', e => {
      const media = images[e.detail]; if (!media) return;
      const cur = selected();
      const best = product.variants.filter(v => v.featured_media?.id === media.id)
        .map(v => ({ v, score: v.options.filter((o, k) => o === cur[k]).length, tie: v.options.filter((o, k) => o === prev[k]).length }))
        .sort((a, b) => b.score - a.score || b.tie - a.tie)[0];
      if (!best || best.score === cur.length) return;
      best.v.options.forEach((val, k) => {
        const input = [...root.querySelectorAll('input[name="' + CSS.escape(product.options[k]) + '"]')].find(r => r.value === val);
        if (input) input.checked = true;
      });
      update();
    });

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
        if (t) { t.querySelector('[data-cart-toast-text]').textContent = root.querySelector('[data-summary]').textContent + ' ' + (cfg.strings?.added || ''); t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 4000); }
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
      if (interest) config.notes = ((window.SpaTime?.strings?.interest) || '') + ' ' + interest;

      target.innerHTML = '';
      target.classList.add('is-loaded');
      const mount = document.createElement('div');
      mount.id = 'spatime-cal-' + Math.random().toString(36).slice(2);
      target.appendChild(mount);

      window.Cal('init', 'spatime', { origin });
      // Accept "user", "user/type" or a full pasted URL (https://cal.com/user/type?x=y).
      const calLink = (root.dataset.calLink || '').trim().replace(/^https?:\/\/(app\.)?cal\.(com|eu)\//, '').replace(/[?#].*$/, '').replace(/^\/+|\/+$/g, '');
      window.Cal.ns.spatime('inline', { elementOrSelector: '#' + mount.id, calLink, config });
      window.Cal.ns.spatime('ui', { theme: 'light', cssVarsPerTheme: { light: { 'cal-brand': '#946E42' } }, hideEventTypeDetails: false, layout: 'month_view' });
      window.Cal.ns.spatime('on', { action: 'bookingSuccessfulV2', callback: () => track('generate_lead', { method: 'showroom_booking', interest: interest || '' }) });
      track('booking_open');
    });
  });
})();

// Rustige onthulling van secties bij het scrollen. Alleen voor elementen die bij het laden onder de
// vouw staan, zodat er bovenaan niets knippert. Niet in de editor en niet bij prefers-reduced-motion.
(() => {
  if (window.Shopify?.designMode || !('IntersectionObserver' in window) ||
      matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Containers waarvan de kinderen één voor één verschijnen.
  const GROUPS = ['.st-split__content .stack', '.st-hero__content .stack', '.section-head', '.features__intro',
    '.features__grid', '.grid-3', '.feature-cards__grid', '.usp-bar__grid', '.key-specs__strip', '.key-specs__panel',
    '.specs__grid', '.timeline__chapters', '.contact__grid', '.compare__table', '.statement .container', '.booking__panel', '.site-footer__grid'];
  // Beelden die langzaam uitzoomen als ze in beeld komen.
  const MEDIA = ['.st-split__media', '.st-hero__media'];

  const fold = innerHeight * 0.92;
  const below = (el) => el.getBoundingClientRect().top > fold;
  const io = new IntersectionObserver((entries) => entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('is-in');
    io.unobserve(e.target);
  }), { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

  document.querySelectorAll(GROUPS.join(',')).forEach((group) => {
    [...group.children].forEach((el, i) => {
      if (!below(el) || el.closest('.st-reveal')) return;
      el.classList.add('st-reveal');
      el.style.setProperty('--rd', `${Math.min(i, 5) * 0.11}s`);
      io.observe(el);
    });
  });
  document.querySelectorAll(MEDIA.join(',')).forEach((el) => {
    if (!below(el) || !el.querySelector('img')) return;
    el.classList.add('st-zoom');
    io.observe(el);
  });
})();

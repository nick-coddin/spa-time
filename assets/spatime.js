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

const grid = document.querySelector('#product-grid');
const count = document.querySelector('#count');
const loadMore = document.querySelector('#load-more');
const PAGE_SIZE = 8;
let currentFilter = 'all';
let visible = PAGE_SIZE;
let inventory = [];

const labels = { singles: 'Single', sealed: 'Sellado', collection: 'Nueva colección' };
const statusLabels = { available: 'Disponible', sold_out: 'Agotado', coming_soon: 'Próximamente' };

function formatPrice(product) {
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: product.currency, maximumFractionDigits: 0 }).format(product.price);
}

function productArt(product) {
  const symbols = product.category === 'singles' ? ['⚡', '✦', '🔥', '◉'] : product.category === 'sealed' ? ['▣', '◆', '⚡'] : ['★', '✦', '◈'];
  const symbol = symbols[product.id % symbols.length];
  return product.image_url
    ? `<img src="${product.image_url}" alt="${product.name}" loading="lazy">`
    : `<div class="art-placeholder ${product.category}"><span class="art-set">${product.set_name}</span><b>${symbol}</b><small>TCG / ${product.card_number}</small></div>`;
}

function render() {
  const filtered = currentFilter === 'all' ? inventory : inventory.filter(p => p.category === currentFilter);
  const shown = filtered.slice(0, visible);
  count.textContent = filtered.length;
  grid.innerHTML = shown.map((p, index) => `
    <article class="product-card ${p.is_holo ? 'is-holo' : ''}" style="--delay:${index * 45}ms">
      <div class="product-image">
        ${productArt(p)}
        <span class="status ${p.status}">${statusLabels[p.status]}</span>
        ${p.is_holo ? '<span class="rarity" title="Holográfica">★ HOLO</span>' : ''}
      </div>
      <div class="product-info">
        <div class="product-meta"><span>${labels[p.category]}</span><span>${p.set_name} · ${p.card_number}</span></div>
        <h3>${p.name}</h3>
        <p>${p.description}</p>
        <div class="product-bottom"><strong>${formatPrice(p)} <small>${p.currency}</small></strong><button aria-label="Ver ${p.name}" ${p.status === 'sold_out' ? 'disabled' : ''}>${p.status === 'coming_soon' ? 'Avisarme' : p.status === 'sold_out' ? 'Agotado' : 'Ver'} <span>↗</span></button></div>
      </div>
    </article>`).join('');
  loadMore.hidden = shown.length >= filtered.length;
}

// Fetch from Airtable via the API proxy
async function loadProducts() {
  try {
    const resp = await fetch('/api/tcg-products');
    const data = await resp.json();
    if (data.products) {
      inventory = data.products;
      // Deduplicate by name + price (keep first occurrence)
      const seen = new Set();
      inventory = inventory.filter(p => {
        const key = `${p.name}|${p.price}|${p.currency}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      render();
    }
  } catch (err) {
    console.error('Failed to load products:', err);
    grid.innerHTML = '<p style="color:#777;text-align:center;padding:60px">Error al cargar el inventario. Intenta de nuevo más tarde.</p>';
  }
}

document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
  document.querySelector('.filter.active')?.classList.remove('active');
  button.classList.add('active');
  currentFilter = button.dataset.filter;
  visible = PAGE_SIZE;
  render();
}));

document.querySelectorAll('[data-filter-link]').forEach(button => button.addEventListener('click', () => {
  currentFilter = button.dataset.filterLink;
  visible = PAGE_SIZE;
  document.querySelector('.filter.active')?.classList.remove('active');
  document.querySelector(`[data-filter="${currentFilter}"]`)?.classList.add('active');
  render();
  document.querySelector('#inventario').scrollIntoView({ behavior: 'smooth' });
}));

loadMore.addEventListener('click', () => { visible += PAGE_SIZE; render(); });

const observer = new IntersectionObserver(entries => entries.forEach(entry => {
  if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
}), { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// Start loading
loadProducts();

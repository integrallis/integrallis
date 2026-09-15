document.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('[data-menu]');
    const menuButton = document.querySelector('[data-menu-button]');

    const setMenu = (open) => {
        if (!menu || !menuButton) return;
        menu.classList.toggle('open', open);
        menuButton.setAttribute('aria-expanded', String(open));
        document.body.classList.toggle('menu-open', open);
    };

    menuButton?.addEventListener('click', () => {
        setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
    });

    menu?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') setMenu(false);
    });

    const year = document.querySelector('[data-year]');
    if (year) year.textContent = String(new Date().getFullYear());

    hydrateArticles();
});

async function hydrateArticles() {
    const container = document.querySelector('[data-articles]');
    if (!container) return;

    try {
        const response = await fetch('assets/data/articles.json', { cache: 'no-cache' });
        if (!response.ok) return;
        const articles = await response.json();
        if (!Array.isArray(articles) || articles.length === 0) return;

        const fragment = document.createDocumentFragment();
        articles.slice(0, 12).forEach((article) => fragment.append(createArticleCard(article)));
        container.replaceChildren(fragment);
    } catch (_error) {
        // Authored article cards remain visible if the feed file cannot be loaded.
    }
}

function createArticleCard(article) {
    const card = document.createElement('a');
    card.className = 'article-card';
    card.href = article.url;
    card.target = '_blank';
    card.rel = 'noopener';

    const meta = document.createElement('div');
    meta.className = 'article-meta';
    const category = document.createElement('span');
    category.textContent = article.category || 'Field notes';
    const time = document.createElement('time');
    time.dateTime = article.published;
    time.textContent = article.dateLabel;
    meta.append(category, time);

    const title = document.createElement('h3');
    title.textContent = article.title;
    const excerpt = document.createElement('p');
    excerpt.textContent = article.excerpt;
    const read = document.createElement('span');
    read.className = 'read-article';
    read.append('Read article ');
    const arrow = document.createElement('b');
    arrow.textContent = '↗';
    read.append(arrow);

    card.append(meta, title, excerpt, read);
    return card;
}

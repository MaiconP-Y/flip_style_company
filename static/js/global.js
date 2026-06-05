// ==========================================================================
// FLIP STYLE COMPANY - GLOBAL & MAESTRO JAVASCRIPT (COM ESCUTA DE RESOLUÇÃO)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initGlobalSearch();
    
    // Define a nossa regra de corte (media query) no JS
    const mediaQueryMobile = window.matchMedia("(max-width: 850px)");

    // 1. Checa logo de cara assim que a página carrega
    if (mediaQueryMobile.matches) {
        carregarScriptMobile();
    }

    // 2. BOA PRÁTICA: Fica escutando a resolução. Se diminuir no PC, ativa na hora!
    mediaQueryMobile.addEventListener('change', (e) => {
        if (e.matches) {
            carregarScriptMobile();
        }
    });
});

/**
 * Gerencia o comportamento do formulário de busca
 */
function initGlobalSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-form input');

    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', (e) => {
            if (searchInput.value.trim() === "") {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
}

/**
 * Injeta dinamicamente o arquivo mobile.js apenas quando necessário
 */
function carregarScriptMobile() {
    // Evita injetar o script de novo se ele já foi carregado antes
    if (document.getElementById('js-mobile-script')) return;

    const script = document.createElement('script');
    script.src = "/static/js/mobile.js"; // Caminho dos estáticos do Django
    script.id = "js-mobile-script";
    script.defer = true;
    
    document.body.appendChild(script);
    console.log("Performance: mobile.js carregado dinamicamente via redimensionamento.");
}
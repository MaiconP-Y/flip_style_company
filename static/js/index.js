// static/js/index.js
document.addEventListener('DOMContentLoaded', () => {
    
    /**
     * Lógica Modular e Nativa de Carrossel com Arrastar e Clicar (Pointer Events)
     * @param {HTMLElement} container - O elemento pai que encapsula o carrossel (ex: .banner-home)
     * @param {number} autoPlayInterval - Tempo em milissegundos para o autoplay (0 para desativar)
     */
    const initCarousel = (container, autoPlayInterval = 0) => {
        if (!container) return;

        const inner = container.querySelector('.carousel-inner');
        const items = container.querySelectorAll('.carousel-item');
        if (!inner || items.length === 0) return;

        let index = 0, timer;
        let isDragging = false, isMoved = false, startX = 0;

        const update = (newIndex) => {
            index = (newIndex + items.length) % items.length;
            inner.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            inner.style.transform = `translateX(-${index * 100}%)`;
            if (autoPlayInterval > 0) resetAutoPlay();
        };

        const resetAutoPlay = () => {
            clearInterval(timer);
            timer = setInterval(() => update(index + 1), autoPlayInterval);
        };

        container.querySelector('.next')?.addEventListener('click', () => update(index + 1));
        container.querySelector('.prev')?.addEventListener('click', () => update(index - 1));

        inner.addEventListener('dragstart', e => e.preventDefault());

        inner.addEventListener('pointerdown', (e) => {
            isDragging = true;
            isMoved = false;
            startX = e.clientX;
            inner.style.transition = 'none';
            if (autoPlayInterval > 0) clearInterval(timer);
            
            // Captura o ponteiro no elemento alvo exato para preservar a árvore do DOM
            e.target.setPointerCapture(e.pointerId);
        });

        inner.addEventListener('pointermove', (e) => {
            if (!isDragging) return;
            const diff = e.clientX - startX;
            if (Math.abs(diff) > 5) isMoved = true;
            
            // Aplica o deslocamento físico baseado no arrasto do usuário
            inner.style.transform = `translateX(calc(-${index * 100}% + ${diff}px))`;
        });

        const pointerEnd = (e) => {
            if (!isDragging) return;
            isDragging = false;
            
            e.target.releasePointerCapture(e.pointerId);
            
            const diff = e.clientX - startX;
            // Define se passa para o próximo, volta ou mantém a imagem atual
            update(diff > 50 ? index - 1 : diff < -50 ? index + 1 : index);
        };

        inner.addEventListener('pointerup', pointerEnd);
        inner.addEventListener('pointercancel', pointerEnd);

        inner.addEventListener('click', (e) => {
            // Se o usuário arrastou o elemento, cancela o link. Se apenas clicou, redireciona nativamente.
            if (isMoved) { 
                e.preventDefault(); 
                e.stopPropagation(); 
            }
        });

        if (autoPlayInterval > 0) resetAutoPlay();
    };

    // ==========================================================================
    // INICIALIZAÇÃO DOS COMPONENTES DA HOME
    // ==========================================================================

    // 1. Banner Principal: Passa o elemento correspondente e define Autoplay de 5 segundos (5000ms)
    initCarousel(document.querySelector('.banner-home'), 5000);

    // 2. Carrossel de Categorias: Passa o container criado e desativa o Autoplay (0)
    initCarousel(document.querySelector('.categories-carousel'), 0);

    // 3. Carrossel de Mais Vendidos (Produtos): Passa o container criado e desativa o Autoplay (0)
    initCarousel(document.querySelector('.products-carousel'), 0);
});
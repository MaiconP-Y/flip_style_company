document.addEventListener('DOMContentLoaded', () => {

    /**
     * ENGINE DE COMPORTAMENTO NATIVO
     */
    const CarouselEngine = {
        // Calcula a largura real considerando bordas e o espaçamento (gap) do CSS
        getCardWidth: (container) => {
            const item = container.firstElementChild;
            if (!item) return 0;
            const gap = parseFloat(window.getComputedStyle(container).gap) || 0;
            return item.getBoundingClientRect().width + gap;
        },

        getActiveIndex: (scrollLeft, cardWidth, dotsCount) => {
            if (cardWidth <= 0) return 0;
            const index = Math.round(scrollLeft / cardWidth);
            return Math.max(0, Math.min(index, dotsCount - 1));
        },

        createDots: (container, dotsContainer, cardWidth, onDotClick) => {
            if (!dotsContainer) return [];
            const totalItems = container.children.length;
            const visibleCards = Math.round(container.clientWidth / (cardWidth || 1)) || 1;
            const dotsCount = Math.max(1, totalItems - visibleCards + 1);

            if (dotsCount <= 1) {
                dotsContainer.innerHTML = '';
                return [];
            }

            const fragment = document.createDocumentFragment();
            const dots = Array.from({ length: dotsCount }, (_, i) => {
                const dot = document.createElement('button');
                dot.classList.add('carousel-dot');
                dot.setAttribute('aria-label', `Ir para slide ${i + 1}`);
                dot.addEventListener('click', () => onDotClick(i));
                fragment.appendChild(dot);
                return dot;
            });

            dotsContainer.innerHTML = '';
            dotsContainer.appendChild(fragment);
            return dots;
        }
    };

    /**
     * CARROSSEL INFINITO (Banners)
     */
    const initInfiniteCarousel = (wrapperId, nextBtnId, prevBtnId) => {
        const wrapper = document.getElementById(wrapperId);
        if (!wrapper) return;
        
        const container = wrapper.querySelector('.carousel-inner');
        const nextBtn = document.getElementById(nextBtnId);
        const prevBtn = document.getElementById(prevBtnId);
        if (!container || container.children.length <= 1) return;
        
        const originalItems = Array.from(container.children);
        const originalCount = originalItems.length;

        // Injeção limpa de clones via DocumentFragment (1 único Reflow)
        const startFragment = document.createDocumentFragment();
        const endFragment = document.createDocumentFragment();

        originalItems.forEach(item => endFragment.appendChild(item.cloneNode(true)).classList.add('carousel-clone'));
        [...originalItems].reverse().forEach(item => startFragment.insertBefore(item.cloneNode(true), startFragment.firstChild).classList.add('carousel-clone'));

        container.appendChild(endFragment);
        container.insertBefore(startFragment, container.firstChild);

        let timer = null;
        let isTransitioning = false;
        let cardWidth = 0;

        const move = (index, smooth = true) => {
            if (cardWidth <= 0) return;
            isTransitioning = true;
            
            // Remove o snap antes de mover programaticamente para evitar conflito com o CSS
            container.style.scrollSnapType = 'none';
            container.style.scrollBehavior = smooth ? 'smooth' : 'auto';
            container.scrollLeft = cardWidth * index;
            
            // Restaura o snap imediatamente se o movimento for instantâneo
            if (!smooth) {
                container.style.scrollSnapType = 'x mandatory';
                isTransitioning = false;
            }
        };

        const handleResetPosition = () => {
            const idx = Math.round(container.scrollLeft / cardWidth);
            if (idx < originalCount) {
                move(idx + originalCount, false);
            } else if (idx >= originalCount * 2) {
                move(idx - originalCount, false);
            }
            container.style.scrollSnapType = 'x mandatory';
            isTransitioning = false;
        };

        const startTimer = () => {
            if (timer) cancelAnimationFrame(timer);
            let lastTime = performance.now();
            
            const loop = (now) => {
                if (now - lastTime >= 5000) {
                    if (document.visibilityState === 'visible' && !isTransitioning) {
                        const currentIndex = Math.round(container.scrollLeft / cardWidth);
                        move(currentIndex + 1);
                    }
                    lastTime = now;
                }
                timer = requestAnimationFrame(loop);
            };
            timer = requestAnimationFrame(loop);
        };

        const stopTimer = () => {
            if (timer) cancelAnimationFrame(timer);
            timer = null;
        };

        // Escuta redimensionamento de tela e atualiza a matemática em tempo real
        const resizeObserver = new ResizeObserver(() => {
            const oldWidth = cardWidth;
            cardWidth = CarouselEngine.getCardWidth(container);
            if (oldWidth !== cardWidth && oldWidth > 0) {
                const currentIndex = Math.round(container.scrollLeft / oldWidth);
                move(currentIndex, false);
            }
        });
        resizeObserver.observe(container);

        // Listeners com tratamento passivo para manter a fluidez de toque
        container.addEventListener('scrollend', handleResetPosition);
        container.addEventListener('touchstart', stopTimer, { passive: true });
        container.addEventListener('touchend', startTimer, { passive: true });

        nextBtn?.addEventListener('click', () => {
            if (isTransitioning) return;
            move(Math.round(container.scrollLeft / cardWidth) + 1);
        });

        prevBtn?.addEventListener('click', () => {
            if (isTransitioning) return;
            move(Math.round(container.scrollLeft / cardWidth) - 1);
        });

        document.addEventListener('visibilitychange', () => {
            document.visibilityState === 'hidden' ? stopTimer() : startTimer();
        });

        requestAnimationFrame(() => {
            cardWidth = CarouselEngine.getCardWidth(container);
            move(originalCount, false);
            startTimer();
        });
    };

    /**
     * CARROSSEL TRADICIONAL (Produtos e Categorias)
     */
    const setupCarousel = (carouselId, nextBtnId, prevBtnId, dotsContainerId) => {
        const container = document.getElementById(carouselId);
        const nextBtn = document.getElementById(nextBtnId);
        const prevBtn = document.getElementById(prevBtnId);
        const dotsContainer = document.getElementById(dotsContainerId);
        if (!container) return;

        let cardWidth = 0;
        let dots = [];

        const update = () => {
            cardWidth = CarouselEngine.getCardWidth(container);
            dots = CarouselEngine.createDots(container, dotsContainer, cardWidth, (i) => {
                container.scrollTo({ left: i * cardWidth, behavior: 'smooth' });
            });
            syncDots();
        };

        const syncDots = () => {
            const idx = CarouselEngine.getActiveIndex(container.scrollLeft, cardWidth, dots.length);
            dots.forEach((dot, i) => dot.classList.toggle('active', i === idx));
        };

        new ResizeObserver(update).observe(container);

        nextBtn?.addEventListener('click', () => {
            const atEnd = container.scrollLeft + container.offsetWidth >= container.scrollWidth - 10;
            container.scrollTo({ left: atEnd ? 0 : container.scrollLeft + cardWidth, behavior: 'smooth' });
        });

        prevBtn?.addEventListener('click', () => {
            const atStart = container.scrollLeft <= 1;
            container.scrollTo({ left: atStart ? container.scrollWidth : container.scrollLeft - cardWidth, behavior: 'smooth' });
        });

        container.addEventListener('scroll', () => window.requestAnimationFrame(syncDots), { passive: true });
    };

    // Execução Centralizada
    initInfiniteCarousel('bannerHome', 'bannerNext', 'bannerPrev');
    initInfiniteCarousel('brandsCarouselWrapper', 'brandsNext', 'brandsPrev');
    setupCarousel('productsCarousel', 'prodNext', 'prodPrev', 'prodPagination');
    setupCarousel('categoriesCarousel', 'catNext', 'catPrev', 'catPagination');
});
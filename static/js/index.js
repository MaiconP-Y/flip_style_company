document.addEventListener('DOMContentLoaded', () => {

    const CarouselEngine = {
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

        createDots: (container, dotsContainer, onDotClick) => {
            if (!dotsContainer) return [];
            
            const totalItems = container.children.length;
            const cardWidth = container.firstElementChild?.getBoundingClientRect().width || 1;
            const visibleCards = Math.max(1, Math.floor(container.clientWidth / cardWidth));
            const dotsCount = Math.max(1, totalItems - visibleCards + 1);

            if (dotsCount <= 1) {
                dotsContainer.innerHTML = '';
                return [];
            }

            if (dotsContainer.children.length === dotsCount) {
                return Array.from(dotsContainer.children);
            }

            dotsContainer.innerHTML = '';
            const fragment = document.createDocumentFragment();
            const dots = Array.from({ length: dotsCount }, (_, i) => {
                const dot = document.createElement('button');
                dot.classList.add('carousel-dot');
                dot.setAttribute('aria-label', `Ir para slide ${i + 1}`);
                dot.addEventListener('click', () => onDotClick(i));
                fragment.appendChild(dot);
                return dot;
            });

            dotsContainer.appendChild(fragment);
            return dots;
        }
    };

    /**
     * RESTAURADO: CARROSSEL INFINITO ORIGINAL E FUNCIONAL
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
            
            container.style.scrollSnapType = 'none';
            container.style.scrollBehavior = smooth ? 'smooth' : 'auto';
            container.scrollLeft = cardWidth * index;
            
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

        const resizeObserver = new ResizeObserver(() => {
            const oldWidth = cardWidth;
            cardWidth = CarouselEngine.getCardWidth(container);
            if (oldWidth !== cardWidth && oldWidth > 0) {
                const currentIndex = Math.round(container.scrollLeft / oldWidth);
                move(currentIndex, false);
            }
        });
        resizeObserver.observe(container);

        container.addEventListener('scrollend', handleResetPosition);
        container.addEventListener('touchstart', stopTimer, { passive: true });
        container.addEventListener('touchend', startTimer, { passive: true });

        nextBtn?.addEventListener('click', () => {
            if (isTransitioning) return;
            stopTimer();
            move(Math.round(container.scrollLeft / cardWidth) + 1);
            startTimer();
        });

        prevBtn?.addEventListener('click', () => {
            if (isTransitioning) return;
            stopTimer();
            move(Math.round(container.scrollLeft / cardWidth) - 1);
            startTimer();
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
     * OTIMIZADO: CARROSSEL TRADICIONAL COM RECALCULO CIRÚRGICO APENAS EM BREAKPOINTS
     */
    const setupCarousel = (carouselId, nextBtnId, prevBtnId, dotsContainerId) => {
        const container = document.getElementById(carouselId);
        const nextBtn = document.getElementById(nextBtnId);
        const prevBtn = document.getElementById(prevBtnId);
        const dotsContainer = document.getElementById(dotsContainerId);
        if (!container) return;

        let cardWidth = CarouselEngine.getCardWidth(container);
        let dots = [];

        const rebuildDots = () => {
            dots = CarouselEngine.createDots(container, dotsContainer, (i) => {
                container.scrollTo({ left: i * cardWidth });
            });
            syncDots();
        };

        const update = () => {
            cardWidth = CarouselEngine.getCardWidth(container);
            syncDots();
        };

        let ticking = false;

        const syncDots = () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    const idx = CarouselEngine.getActiveIndex(container.scrollLeft, cardWidth, dots.length);
                    dots.forEach((dot, i) => {
                        const isActive = i === idx;
                        if (dot.classList.contains('active') !== isActive) {
                            dot.classList.toggle('active', isActive);
                        }
                    });
                    ticking = false;
                });
                ticking = true;
            }
        };

        rebuildDots();

        new ResizeObserver(update).observe(container);

        const breakpoints = [
            window.matchMedia('(max-width: 899px)'),
            window.matchMedia('(max-width: 600px)')
        ];
        breakpoints.forEach(query => {
            query.addEventListener('change', rebuildDots);
        });

        nextBtn?.addEventListener('click', () => {
            const atEnd = container.scrollLeft + container.offsetWidth >= container.scrollWidth - 10;
            container.scrollTo({ left: atEnd ? 0 : container.scrollLeft + cardWidth });
        });

        prevBtn?.addEventListener('click', () => {
            const atStart = container.scrollLeft <= 1;
            container.scrollTo({ left: atStart ? container.scrollWidth : container.scrollLeft - cardWidth });
        });

        container.addEventListener('scroll', syncDots, { passive: true });
    };

    // Execução Centralizada
    initInfiniteCarousel('bannerHome', 'bannerNext', 'bannerPrev');
    initInfiniteCarousel('brandsCarouselWrapper', 'brandsNext', 'brandsPrev');
    
    setupCarousel('productsCarousel', 'prodNext', 'prodPrev', 'prodPagination');
    setupCarousel('categoriesCarousel', 'catNext', 'catPrev', 'catPagination');
});
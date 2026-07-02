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

    const createAutoPlayer = (actionFn, interval = 5000) => {
        let timer = null;
        let lastTime = performance.now();
        let isRunning = false;

        const loop = (now) => {
            if (!isRunning) return;
            if (now - lastTime >= interval) {
                // Só executa a ação se a aba estiver em foco (poupa recursos do cliente)
                if (document.visibilityState === 'visible') {
                    actionFn();
                }
                lastTime = now;
            }
            timer = requestAnimationFrame(loop);
        };

        const start = () => {
            if (isRunning) return;
            isRunning = true;
            lastTime = performance.now();
            timer = requestAnimationFrame(loop);
        };

        const stop = () => {
            isRunning = false;
            if (timer) cancelAnimationFrame(timer);
            timer = null;
        };

        // Controle global de visibilidade
        document.addEventListener('visibilitychange', () => {
            document.visibilityState === 'hidden' ? stop() : start();
        });

        return { start, stop };
    };

    const initInfiniteCarousel = (wrapperId, nextBtnId, prevBtnId, autoPlayInterval = 5000) => {
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

        // Reutilizando o AutoPlayer na lógica infinita
        const player = createAutoPlayer(() => {
            if (!isTransitioning) {
                move(Math.round(container.scrollLeft / cardWidth) + 1);
            }
        }, autoPlayInterval);

        const safeManualMove = (direction) => {
            if (isTransitioning) return;
            player.stop();
            move(Math.round(container.scrollLeft / cardWidth) + direction);
            player.start();
        };

        nextBtn?.addEventListener('click', () => safeManualMove(1));
        prevBtn?.addEventListener('click', () => safeManualMove(-1));

        container.addEventListener('scrollend', handleResetPosition);
        container.addEventListener('touchstart', player.stop, { passive: true });
        container.addEventListener('touchend', player.start, { passive: true });

        new ResizeObserver(() => {
            const oldWidth = cardWidth;
            cardWidth = CarouselEngine.getCardWidth(container);
            if (oldWidth !== cardWidth && oldWidth > 0) {
                move(Math.round(container.scrollLeft / oldWidth), false);
            }
        }).observe(container);

        requestAnimationFrame(() => {
            cardWidth = CarouselEngine.getCardWidth(container);
            move(originalCount, false);
            player.start();
        });
    };

    const setupCarousel = ({ containerId, nextBtnId, prevBtnId, dotsContainerId, autoPlay = false, interval = 5000 }) => {
        const container = document.getElementById(containerId);
        const nextBtn = document.getElementById(nextBtnId);
        const prevBtn = document.getElementById(prevBtnId);
        const dotsContainer = document.getElementById(dotsContainerId);
        
        if (!container) return;

        let cardWidth = CarouselEngine.getCardWidth(container);
        let dots = [];
        let ticking = false;

        const syncDots = () => {
            if (!ticking && dots.length > 0) {
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

        const rebuildDots = () => {
            if (dotsContainer) {
                dots = CarouselEngine.createDots(container, dotsContainer, (i) => {
                    container.scrollTo({ left: i * cardWidth });
                });
                syncDots();
            }
        };

        const goNext = () => {
            const atEnd = container.scrollLeft + container.offsetWidth >= container.scrollWidth - 10;
            container.scrollTo({ left: atEnd ? 0 : container.scrollLeft + cardWidth });
        };

        const goPrev = () => {
            const atStart = container.scrollLeft <= 1;
            container.scrollTo({ left: atStart ? container.scrollWidth : container.scrollLeft - cardWidth });
        };

        // Integração cirúrgica com o AutoPlayer
        let player = null;
        if (autoPlay) {
            player = createAutoPlayer(goNext, interval);
            container.addEventListener('touchstart', player.stop, { passive: true });
            container.addEventListener('touchend', player.start, { passive: true });
            
            player.start();
        }

        rebuildDots();

        new ResizeObserver(() => {
            cardWidth = CarouselEngine.getCardWidth(container);
            syncDots();
        }).observe(container);

        const breakpoints = [
            window.matchMedia('(max-width: 899px)'),
            window.matchMedia('(max-width: 600px)')
        ];
        breakpoints.forEach(query => query.addEventListener('change', rebuildDots));

        nextBtn?.addEventListener('click', () => {
            if (player) player.stop();
            goNext();
            if (player) player.start();
        });

        prevBtn?.addEventListener('click', () => {
            if (player) player.stop();
            goPrev();
            if (player) player.start();
        });

        container.addEventListener('scroll', syncDots, { passive: true });
    };

    initInfiniteCarousel('brandsCarouselWrapper', 'brandsNext', 'brandsPrev', 4000);

    setupCarousel({
        containerId: 'bannerInner',
        nextBtnId: 'bannerNext',
        prevBtnId: 'bannerPrev',
        autoPlay: true,
        interval: 5000
    });

    setupCarousel({ 
        containerId: 'productsCarousel', 
        nextBtnId: 'prodNext', 
        prevBtnId: 'prodPrev', 
        dotsContainerId: 'prodPagination' 
    });

    setupCarousel({ 
        containerId: 'categoriesCarousel', 
        nextBtnId: 'catNext', 
        prevBtnId: 'catPrev', 
        dotsContainerId: 'catPagination' 
    });
});
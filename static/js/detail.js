document.addEventListener('DOMContentLoaded', () => {
    // --- 1. Galeria: troca de imagem por miniatura ---
    const mainImage = document.getElementById('mainImage');
    const thumbBtns = document.querySelectorAll('.thumb-btn');

    thumbBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const fullSrc = this.querySelector('.thumb-img')?.dataset.fullSrc;
            if (fullSrc && mainImage) {
                mainImage.src = fullSrc;
                thumbBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    thumbBtns[0]?.classList.add('active');

    // --- 2. Zoom: mouse (desktop) + touch (mobile) ---
    const zoomContainer = document.getElementById('zoomContainer');
    if (!zoomContainer || !mainImage) return;

    function applyZoom(x, y) {
        const { width, height } = zoomContainer.getBoundingClientRect();
        const px = ((x / width) * 100).toFixed(2);
        const py = ((y / height) * 100).toFixed(2);
        mainImage.style.transformOrigin = `${px}% ${py}%`;
    }

    function getRelativePos(e) {
        const rect = zoomContainer.getBoundingClientRect();
        const src = e.touches ? e.touches[0] : e;
        return { x: src.clientX - rect.left, y: src.clientY - rect.top };
    }

    // Desktop
    zoomContainer.addEventListener('mouseenter', () => {
        zoomContainer.classList.add('zoomed');
    });

    zoomContainer.addEventListener('mousemove', (e) => {
        const { x, y } = getRelativePos(e);
        applyZoom(x, y);
    });

    zoomContainer.addEventListener('mouseleave', () => {
        zoomContainer.classList.remove('zoomed');
        mainImage.style.transformOrigin = 'center center';
    });

    // Mobile
    function resetZoom() {
        zoomContainer.classList.remove('zoomed');
        mainImage.style.transformOrigin = 'center center';
    }

    function isTouchInsideContainer(touch) {
        const rect = zoomContainer.getBoundingClientRect();
        return (
            touch.clientX >= rect.left &&
            touch.clientX <= rect.right &&
            touch.clientY >= rect.top &&
            touch.clientY <= rect.bottom
        );
    }

    zoomContainer.addEventListener('touchstart', (e) => {
        zoomContainer.classList.add('zoomed');
        const { x, y } = getRelativePos(e);
        applyZoom(x, y);
    }, { passive: true });

    zoomContainer.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        if (!isTouchInsideContainer(touch)) {
            resetZoom();
            return;
        }
        const { x, y } = getRelativePos(e);
        applyZoom(x, y);
    }, { passive: false });

    zoomContainer.addEventListener('touchend', resetZoom);
    zoomContainer.addEventListener('touchcancel', resetZoom);

    // --- 3. Modal de tabela de medidas (dialog nativo) ---
    const sizeGuideModal = document.getElementById('sizeGuideModal');
    document.getElementById('openSizeGuide')?.addEventListener('click', () => {
        sizeGuideModal?.showModal();
        toggleScrollLock(true);
    });
    document.getElementById('closeSizeGuide')?.addEventListener('click', () => {
        sizeGuideModal?.close();
        toggleScrollLock(false);
    });
    sizeGuideModal?.addEventListener('click', e => {
        if (e.target === sizeGuideModal) {
            sizeGuideModal.close();
            toggleScrollLock(false);
        }
    });
    // garante reset se fechar via Escape
    sizeGuideModal?.addEventListener('close', () => toggleScrollLock(false));
});
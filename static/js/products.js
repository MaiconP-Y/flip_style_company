document.addEventListener('click', function (e) {
    const btn = e.target.closest('.dropbtn');
    const clickedDropdown = e.target.closest('.dropdown');

    document.querySelectorAll('.dropdown').forEach(d => {
        const content = d.querySelector('.dropdown-content');
        if (!content) return;

        if (d === clickedDropdown && btn) {
            const isOpen = content.style.display === 'grid';
            content.style.display = isOpen ? 'none' : 'grid';
            if (isOpen) btn.blur();
        } else {
            content.style.display = 'none';
        }
    });
});
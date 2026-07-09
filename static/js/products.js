document.addEventListener('click', function (e) {
    // Clique numa opção de filtro: deixa o link navegar normalmente.
    if (e.target.closest('.btn-filtro')) return;

    const btn = e.target.closest('.dropbtn');
    const clickedDropdown = e.target.closest('.dropdown');

    document.querySelectorAll('.dropdown').forEach(d => {
        if (d === clickedDropdown && btn) {
            d.classList.toggle('active');
            if (!d.classList.contains('active')) btn.blur();
        } else {
            d.classList.remove('active');
        }
    });
});
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.dropbtn');
    const dropdown = e.target.closest('.dropdown');

    // fecha qualquer outro dropdown que não seja o clicado
    document.querySelectorAll('.dropdown.active').forEach(d => {
        if (d !== dropdown) d.classList.remove('active');
    });

    if (btn && dropdown) {
        dropdown.classList.toggle('active');
        if (!dropdown.classList.contains('active')) btn.blur();
    }
});
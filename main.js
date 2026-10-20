const menuButton = document.querySelector('.menu-button');
const mobileNav = document.querySelector('#mobile-nav');
menuButton.addEventListener('click', () => {
  const expanded = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!expanded));
  menuButton.setAttribute('aria-label', expanded ? 'Abrir menú' : 'Cerrar menú');
  mobileNav.hidden = expanded;
  menuButton.textContent = expanded ? '☰' : '✕';
});
mobileNav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  mobileNav.hidden = true;
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', 'Abrir menú');
  menuButton.textContent = '☰';
}));
document.querySelector('#year').textContent = new Date().getFullYear();

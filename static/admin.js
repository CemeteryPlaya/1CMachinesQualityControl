/**
 * Свайп-навигация между вкладками (История, Аналитика).
 * Свайп влево — следующая вкладка, вправо — предыдущая.
 * Работает на любой странице с блоком .tabs; переход — по href вкладки.
 */
(function () {
    'use strict';

    const tabs = Array.from(document.querySelectorAll('.tabs .tab'));
    if (tabs.length < 2) return;

    const activeIdx = tabs.findIndex(t => t.classList.contains('active'));
    if (activeIdx < 0) return;

    const THRESHOLD = 60;      // минимальная длина свайпа, px
    const RATIO = 1.5;         // горизонталь должна доминировать над вертикалью

    let startX = null;
    let startY = null;

    document.addEventListener('touchstart', function (e) {
        // Не перехватываем жесты на горизонтально прокручиваемых зонах и полях ввода
        if (e.target.closest('.tabs, .admin-nav-links, select, input, textarea, a, button')) {
            startX = null;
            return;
        }
        const t = e.touches[0];
        startX = t.clientX;
        startY = t.clientY;
    }, { passive: true });

    document.addEventListener('touchend', function (e) {
        if (startX === null) return;
        const t = e.changedTouches[0];
        const dx = t.clientX - startX;
        const dy = t.clientY - startY;
        startX = null;

        if (Math.abs(dx) < THRESHOLD || Math.abs(dx) < Math.abs(dy) * RATIO) return;

        const nextIdx = dx < 0 ? activeIdx + 1 : activeIdx - 1;
        if (nextIdx >= 0 && nextIdx < tabs.length) {
            window.location.href = tabs[nextIdx].href;
        }
    }, { passive: true });
})();

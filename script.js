/* =====================================================================
   PORTFOLIO SCRIPT (vanilla JS, no dependencies)
   ---------------------------------------------------------------------
   1. Smooth in-page scroll (accounts for fixed header height)
   2. Header background/shadow once the page is scrolled
   3. Page-top button show/hide + click
   4. Scroll-reveal animation for elements with class="reveal"
   ===================================================================== */

document.addEventListener('DOMContentLoaded', function () {

  var header = document.querySelector('.header');
  var pageTop = document.getElementById('js-page-top');

  /* ---- 1. smooth in-page scroll with header offset ---- */
  document.querySelectorAll('a[href*="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = link.getAttribute('href');
      var hashIndex = href.indexOf('#');
      if (hashIndex === -1) return;

      var hash = href.slice(hashIndex);
      var isSamePage = href.slice(0, hashIndex) === '' || href.slice(0, hashIndex) === './' || href.slice(0, hashIndex) === location.pathname;
      if (!isSamePage) return; // let the browser navigate to another page first

      var target = hash === '#' ? document.body : document.querySelector(hash);
      if (!target) return;

      e.preventDefault();
      var headerH = header ? header.offsetHeight : 0;
      var top = target.getBoundingClientRect().top + window.pageYOffset - headerH + 1;
      window.scrollTo({ top: top, behavior: 'smooth' });
    });
  });

  /* ---- 2 & 3. header + page-top state on scroll ---- */
  function onScroll() {
    var scrolled = window.scrollY > 40;
    if (header) header.classList.toggle('is-scrolled', scrolled);
    if (pageTop) pageTop.classList.toggle('is-visible', window.scrollY > 400);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  if (pageTop) {
    pageTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---- 4. scroll reveal ---- */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

});

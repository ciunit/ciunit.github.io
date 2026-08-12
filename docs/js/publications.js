/* Client-side filter for the publications index.
 *
 * Progressive enhancement. The search control ships with `hidden` set in the
 * generated HTML and is revealed here, so a browser with JavaScript off never
 * shows a control that does nothing. Everything it filters is already in the
 * page; nothing is fetched.
 *
 * This is the only behavioural script on the site — no build step, no
 * dependencies, no module syntax. Keep it that way.
 */
(function () {
  'use strict';

  var form = document.querySelector('[data-pub-filter]');
  var grid = document.querySelector('.pub-grid');
  if (!form || !grid) return;

  var input = form.querySelector('input');
  var status = document.querySelector('[data-pub-status]');
  var empty = document.querySelector('[data-pub-empty]');
  var items = Array.prototype.slice.call(grid.querySelectorAll('[data-search]'));
  var total = items.length;

  // Fold diacritics, so "Sesboue" finds "Sesboüé" and "Virguez" finds "Virgüez".
  function fold(s) {
    return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  var hay = items.map(function (li) { return fold(li.getAttribute('data-search')); });

  function apply() {
    var terms = fold(input.value).split(/\s+/).filter(Boolean);
    var shown = 0;
    for (var i = 0; i < items.length; i++) {
      var match = true;
      for (var t = 0; t < terms.length; t++) {
        if (hay[i].indexOf(terms[t]) === -1) { match = false; break; }
      }
      // hidden, not display:none, so a filtered-out card leaves the tab order
      // and the accessibility tree rather than staying as an invisible link.
      items[i].hidden = !match;
      if (match) shown++;
    }
    if (empty) empty.hidden = shown !== 0;
    if (status) {
      status.textContent = terms.length
        ? shown + ' of ' + total + ' publications match'
        : '';
    }
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); });
  input.addEventListener('input', apply);
  form.removeAttribute('hidden');
  apply();   // honour a value restored by the back/forward cache or autofill
})();

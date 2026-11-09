/**
 * @file site-media.js
 * @author Aurélien Capron
 * @description Suit le chargement des images, leurs erreurs et les changements de source.
 * @created Non renseignée — date d’origine non vérifiée.
 * @since 2026-11-09 — premier ajout retrouvé dans Git.
 * @documented 2026-11-09 — nettoyage et documentation des sources.
 */
(() => {
  'use strict';
  const sources = new WeakMap();
  const listeners = new WeakSet();
  // Le cadre reste accessible si un gestionnaire d’erreur retire l’image du DOM.
  const frames = new WeakMap();
  const selector = '.image-open, .pcb-open, .media-placeholder, .race-cover';

  /**
   * Identifie le cadre visuel que l’image peut utiliser comme espace de chargement.
   * @param {HTMLImageElement} image - Image suivie.
   * @returns {Element|null}
   */
  function frameFor(image) {
    const frame = image.parentElement;
    return frame && frame.matches(selector) ? frame : null;
  }

  /**
   * Termine l’attente et restaure l’affichage de l’image ou de son état d’erreur.
   * @param {HTMLImageElement} image - Image suivie.
   * @param {boolean} success - Indique si l’image est disponible.
   * @param {boolean} animate - Active le fondu à l’apparition.
   */
  function finish(image, success, animate) {
    const frame = frames.get(image) || frameFor(image);
    image.classList.remove('site-image-loading');
    if (frame) frame.dataset.mediaState = success ? 'ready' : 'error';
    if (success && animate) {
      image.classList.add('site-image-reveal');
      image.addEventListener('animationend', () => image.classList.remove('site-image-reveal'), {
        once: true,
      });
    } else {
      image.classList.remove('site-image-reveal');
    }
  }

  /**
   * Attend le décodage et ignore sa résolution si la source a changé entre-temps.
   * @param {HTMLImageElement} image - Image dont le chargement vient de se terminer.
   */
  function loaded(image) {
    const source = sources.get(image);
    const animate = image.classList.contains('site-image-loading');
    const show = () => {
      if (sources.get(image) === source) finish(image, image.naturalWidth > 0, animate);
    };
    if (typeof image.decode === 'function')
      image
        .decode()
        .catch(() => {})
        .then(show);
    else show();
  }

  /**
   * Suit la source d’une image sans dupliquer ses écouteurs et traite le cache immédiatement.
   * @param {HTMLImageElement} image - Image à observer.
   */
  function track(image) {
    const source = (image.getAttribute('src') || '') + '|' + (image.getAttribute('srcset') || '');
    if (source === '|') {
      sources.delete(image);
      finish(image, false, false);
      return;
    }
    if (sources.get(image) === source) return;
    sources.set(image, source);
    if (!listeners.has(image)) {
      listeners.add(image);
      image.addEventListener('load', () => loaded(image));
      image.addEventListener('error', () => finish(image, false, false));
    }
    const frame = frameFor(image);
    if (frame) {
      frames.set(image, frame);
      frame.classList.add('site-media-frame');
    }
    if (image.complete) {
      finish(image, image.naturalWidth > 0, false);
      return;
    }
    image.classList.remove('site-image-reveal');
    image.classList.add('site-image-loading');
    if (frame) frame.dataset.mediaState = 'loading';
  }

  /**
   * Enregistre les images du nœud ajouté et de ses descendants.
   * @param {Node} node - Nœud à examiner.
   */
  function scan(node) {
    if (!(node instanceof Element)) return;
    if (node instanceof HTMLImageElement) track(node);
    node.querySelectorAll('img').forEach(track);
  }

  scan(document.documentElement);
  const observer = new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === 'attributes' && record.target instanceof HTMLImageElement)
        track(record.target);
      else record.addedNodes.forEach(scan);
    }
  });
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['src', 'srcset'],
  });
})();

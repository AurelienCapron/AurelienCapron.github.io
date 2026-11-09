/**
 * @file site-media.js
 * @author Aurélien Capron
 * @description Suit les médias, leur chargement et leurs erreurs avec des solutions de repli.
 * @created Non renseignée — date d’origine non vérifiée.
 * @documented 2026-11-09 — nettoyage et documentation des sources.
 * @updated 2026-11-09
 * @since 2026-11-09 — premier ajout retrouvé dans Git.
 */
(() => {
  'use strict';
  const sources = new WeakMap(),
    listeners = new WeakSet(),
    panels = new Map();
  const frames = new WeakMap(),
    pending = new WeakMap();
  const frameSelector = '.image-open, .pcb-open, .media-placeholder, .race-cover';
  const language = () => (document.documentElement.lang === 'en' ? 'en' : 'fr');
  const words = {
    fr: {
      image: 'Cette image ne peut pas être affichée.',
      video: 'Cette vidéo ne peut pas être lue pour le moment.',
      hint: 'Vous pouvez réessayer ou consulter la ressource associée lorsqu’elle est disponible.',
      retry: 'Réessayer',
      source: 'Voir la publication d’origine',
      page: 'Voir la page associée',
      file: 'Ouvrir le fichier vidéo',
    },
    en: {
      image: 'This image could not be displayed.',
      video: 'This video cannot be played at the moment.',
      hint: 'Try again or open the associated resource when available.',
      retry: 'Try again',
      source: 'View the original publication',
      page: 'View the related page',
      file: 'Open the video file',
    },
  };

  /** @param {HTMLImageElement} image Image suivie. @returns {Element|null} Cadre visuel compatible. */
  function frameFor(image) {
    const parent = image.parentElement;
    return parent?.matches(frameSelector) ? parent : null;
  }
  /** Retourne uniquement les adresses de navigation utilisables dans les liens de repli. */
  function safeUrl(value) {
    if (!value) return null;
    try {
      const url = new URL(value, location.href);
      return ['http:', 'https:', 'file:'].includes(url.protocol) ? url.href : null;
    } catch {
      return null;
    }
  }
  /** Recherche une publication explicitement associée, puis une page ou un fichier vidéo. */
  function alternative(media) {
    const explicit = media.dataset.mediaSource || media.closest('figure')?.dataset.mediaSource;
    if (safeUrl(explicit)) return { url: safeUrl(explicit), label: 'source' };
    const figure = media.closest('figure');
    const sourceLink = figure?.querySelector('figcaption a[href^="https://"]');
    if (sourceLink) return { url: sourceLink.href, label: 'source' };
    const articleLink = media
      .closest('article')
      ?.querySelector('a[href$=".html"], a[href*=".html#"]');
    if (articleLink) return { url: articleLink.href, label: 'page' };
    if (media instanceof HTMLVideoElement) {
      const file = safeUrl(
        media.getAttribute('src') || media.querySelector('source')?.getAttribute('src'),
      );
      if (file) return { url: file, label: 'file' };
    }
    return null;
  }
  /** Restaure l'image et son bouton après un changement de source ou une reprise du chargement. */
  function clearError(media) {
    const panel = panels.get(media);
    panel?.remove();
    panels.delete(media);
    media.hidden = false;
    const frame = frames.get(media);
    if (frame) {
      frame.hidden = false;
      if (frame.dataset.mediaDisabled === 'true') {
        frame.disabled = false;
        delete frame.dataset.mediaDisabled;
      }
    }
  }
  /** Recrée uniquement les libellés du panneau ; la langue suit celle du document. */
  function labelPanel(media, panel) {
    const labels = words[language()],
      isVideo = media instanceof HTMLVideoElement;
    panel.querySelector('[data-error-title]').textContent = labels[isVideo ? 'video' : 'image'];
    panel.querySelector('[data-error-hint]').textContent = labels.hint;
    panel.querySelector('button').textContent = labels.retry;
    const link = panel.querySelector('a'),
      alt = alternative(media);
    link.hidden = !alt;
    if (alt) {
      link.href = alt.url;
      link.textContent = labels[alt.label];
    }
  }
  /** Remplace un média indisponible par une explication et des commandes accessibles. */
  function showError(media) {
    if (!media.isConnected) return;
    const frame = frames.get(media) || (media instanceof HTMLImageElement ? frameFor(media) : null);
    if (frame) {
      frames.set(media, frame);
      frame.dataset.mediaState = 'error';
      frame.hidden = true;
      if (frame instanceof HTMLButtonElement && !frame.disabled) {
        frame.disabled = true;
        frame.dataset.mediaDisabled = 'true';
      }
    }
    if (media instanceof HTMLImageElement) media.hidden = true;
    if (panels.has(media)) {
      labelPanel(media, panels.get(media));
      return;
    }
    const panel = document.createElement('div');
    panel.className = 'site-media-error';
    panel.setAttribute('role', 'status');
    const title = document.createElement('p');
    title.dataset.errorTitle = '';
    const hint = document.createElement('p');
    hint.dataset.errorHint = '';
    const controls = document.createElement('div');
    const retry = document.createElement('button');
    retry.type = 'button';
    const link = document.createElement('a');
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    controls.append(retry, link);
    panel.append(title, hint, controls);
    (frame || media).insertAdjacentElement('afterend', panel);
    panels.set(media, panel);
    labelPanel(media, panel);
    retry.addEventListener('click', () => {
      clearError(media);
      if (media instanceof HTMLVideoElement) {
        media.load();
        media.focus();
      } else {
        sources.delete(media);
        const src = media.getAttribute('src');
        media.removeAttribute('src');
        if (src) media.setAttribute('src', src);
        trackImage(media);
        if (frame instanceof HTMLButtonElement) frame.focus();
      }
    });
  }
  /** Termine le chargement d'une image sans laisser de panneau périmé. */
  function finish(image, success, animate) {
    image.classList.remove('site-image-loading');
    const frame = frames.get(image) || frameFor(image);
    if (frame) frame.dataset.mediaState = success ? 'ready' : 'error';
    if (!success) {
      image.classList.remove('site-image-reveal');
      showError(image);
      return;
    }
    clearError(image);
    if (animate) {
      image.classList.add('site-image-reveal');
      image.addEventListener('animationend', () => image.classList.remove('site-image-reveal'), {
        once: true,
      });
    }
  }
  /** Attend le décodage et rejette les réponses appartenant à une ancienne source. */
  function loaded(image) {
    const source = sources.get(image),
      animate = image.classList.contains('site-image-loading');
    if (!source || source === '|') return;
    const show = () => {
      if (sources.get(image) === source && source !== '|')
        finish(image, image.naturalWidth > 0, animate);
    };
    if (typeof image.decode === 'function')
      image
        .decode()
        .catch(() => {})
        .then(show);
    else show();
  }
  /** Suit chaque source d'image une seule fois, y compris lorsqu'elle provient du cache. */
  function trackImage(image) {
    const source = (image.getAttribute('src') || '') + '|' + (image.getAttribute('srcset') || '');
    if (source === '|') {
      sources.delete(image);
      clearError(image);
      image.classList.remove('site-image-loading', 'site-image-reveal');
      return;
    }
    if (sources.get(image) === source) return;
    sources.set(image, source);
    clearError(image);
    if (!listeners.has(image)) {
      listeners.add(image);
      image.addEventListener('load', () => loaded(image));
      image.addEventListener('error', () => {
        if (sources.get(image) === source || sources.has(image)) finish(image, false, false);
      });
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
    image.classList.add('site-image-loading');
    if (frame) frame.dataset.mediaState = 'loading';
  }
  /** Attend l'échec de toutes les sources avant de remplacer un lecteur vidéo. */
  function videoError(video) {
    clearTimeout(pending.get(video));
    pending.set(
      video,
      setTimeout(() => {
        if (video.error || video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE)
          showError(video);
      }, 0),
    );
  }
  function trackVideo(video) {
    if (listeners.has(video)) return;
    listeners.add(video);
    video.addEventListener('error', () => videoError(video));
    video
      .querySelectorAll('source')
      .forEach((source) => source.addEventListener('error', () => videoError(video)));
    video.addEventListener('loadeddata', () => clearError(video));
    if (video.error) showError(video);
  }
  /** Enregistre les médias d'un sous-arbre ajouté après le chargement initial. */
  function scan(node) {
    if (!(node instanceof Element)) return;
    if (node instanceof HTMLImageElement) trackImage(node);
    if (node instanceof HTMLVideoElement) trackVideo(node);
    node.querySelectorAll('img').forEach(trackImage);
    node.querySelectorAll('video').forEach(trackVideo);
  }
  scan(document.documentElement);
  new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === 'attributes' && record.target === document.documentElement) {
        panels.forEach((panel, media) => labelPanel(media, panel));
        continue;
      }
      if (record.type === 'attributes' && record.target instanceof HTMLImageElement)
        trackImage(record.target);
      else record.addedNodes.forEach(scan);
    }
    for (const [media, panel] of panels)
      if (!media.isConnected) {
        panel.remove();
        panels.delete(media);
      }
  }).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['src', 'srcset', 'lang'],
  });
})();

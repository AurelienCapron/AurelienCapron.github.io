(() => {
  'use strict';
  const sources = new WeakMap();
  const listeners = new WeakSet();
  const frames = new WeakMap();
  const selector = '.image-open, .pcb-open, .media-placeholder, .race-cover';

  function frameFor(image) {
    const frame = image.parentElement;
    return frame && frame.matches(selector) ? frame : null;
  }

  function finish(image, success, animate) {
    const frame = frames.get(image) || frameFor(image);
    image.classList.remove('site-image-loading');
    if (frame) frame.dataset.mediaState = success ? 'ready' : 'error';
    if (success && animate) {
      image.classList.add('site-image-reveal');
      image.addEventListener('animationend', () => image.classList.remove('site-image-reveal'), { once: true });
    } else {
      image.classList.remove('site-image-reveal');
    }
  }

  function loaded(image) {
    const source = sources.get(image);
    const animate = image.classList.contains('site-image-loading');
    const show = () => {
      if (sources.get(image) === source) finish(image, image.naturalWidth > 0, animate);
    };
    if (typeof image.decode === 'function') image.decode().catch(() => {}).then(show);
    else show();
  }

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

  function scan(node) {
    if (!(node instanceof Element)) return;
    if (node instanceof HTMLImageElement) track(node);
    node.querySelectorAll('img').forEach(track);
  }

  scan(document.documentElement);
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'attributes' && record.target instanceof HTMLImageElement) track(record.target);
      else record.addedNodes.forEach(scan);
    }
  });
  observer.observe(document.documentElement, {
    childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'srcset']
  });
})();

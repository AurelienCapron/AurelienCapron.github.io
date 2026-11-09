/**
 * @file site-experience.js
 * @author Aurélien Capron
 * @description Relie les compétences aux projets, suit le sommaire et prépare le contact.
 * @created 2026-11-09
 */
(() => {
  'use strict';
  const language = () => (document.documentElement.lang === 'en' ? 'en' : 'fr');
  const projects = {
    remote: [
      'telecommande.html#carte',
      'Télécommande autonome',
      'Autonomous remote control',
      'Une carte dédiée, des capteurs et une commande infrarouge.',
      'A custom PCB, sensors and infrared control.',
    ],
    audio: [
      'amplificateur.html#fabrication',
      'Amplificateur audio',
      'Audio amplifier',
      'Schémas KiCad, cartes CMS et validation sur banc.',
      'KiCad schematics, SMD boards and bench validation.',
    ],
    vision: [
      'tipe.html#localisation',
      'TIPE · Badminton',
      'TIPE · Badminton',
      'Python, vision par ordinateur et triangulation.',
      'Python, computer vision and triangulation.',
    ],
    race: [
      'backyard.html#pointage',
      'Chronométrage Backyard Ultra',
      'Backyard Ultra timing',
      'Un serveur Python/Flask et plusieurs postes de pointage.',
      'A Python/Flask server and multiple timing desks.',
    ],
    coop: [
      'poulailler.html#electronique',
      'Porte de poulailler',
      'Chicken coop door',
      'Commande sur ATmega328P, capteur de lumière et relais.',
      'ATmega328P control, light sensor and relays.',
    ],
    tests: [
      'amplificateur.html#mesures',
      'Mesures de l’amplificateur',
      'Amplifier measurements',
      'Oscilloscope et générateur pour comparer mesures et calculs.',
      'Oscilloscope and generator for comparing measurements and calculations.',
    ],
    emc: [
      'domethic.html#contribution',
      'Essais des centrales Myha',
      'Myha controller testing',
      'Assemblage, paramétrage et essais de robustesse et de CEM.',
      'Assembly, configuration, robustness and EMC tests.',
    ],
  };
  const evidence = {
    kicad: ['audio', 'remote'],
    cpp: ['coop', 'remote'],
    python: ['vision', 'race', 'remote'],
    arduino: ['remote', 'vision', 'coop'],
    scope: ['tests', 'remote'],
    generator: ['tests'],
    emc: ['emc'],
  };
  const names = {
    kicad: 'KiCad',
    cpp: 'C/C++',
    python: 'Python / MicroPython',
    arduino: 'Arduino',
    scope: 'Oscilloscope',
    generator: 'Générateur de signaux',
    emc: 'CEM',
  };
  const panel = document.getElementById('skill-evidence');
  let activeSkill = null,
    trigger = null;

  /** Actualise les preuves sans insérer de contenu HTML provenant du visiteur. */
  function renderEvidence() {
    if (!panel || !activeSkill) return;
    const en = language() === 'en';
    panel.querySelector('[data-skill-name]').textContent =
      activeSkill === 'generator' && en
        ? 'Signal generator'
        : activeSkill === 'emc' && en
          ? 'EMC'
          : names[activeSkill];
    const links = panel.querySelector('[data-skill-links]');
    links.replaceChildren();
    for (const key of evidence[activeSkill]) {
      const item = projects[key],
        link = document.createElement('a');
      link.href = item[0];
      const title = document.createElement('strong'),
        description = document.createElement('span');
      title.textContent = item[en ? 2 : 1];
      description.textContent = item[en ? 4 : 3];
      link.append(title, description);
      links.append(link);
    }
  }
  document.querySelectorAll('[data-skill]').forEach((button) =>
    button.addEventListener('click', () => {
      if (!panel || !evidence[button.dataset.skill]) return;
      activeSkill = button.dataset.skill;
      trigger = button;
      document
        .querySelectorAll('[data-skill]')
        .forEach((item) => item.setAttribute('aria-expanded', String(item === button)));
      renderEvidence();
      panel.hidden = false;
      panel.focus({ preventScroll: true });
      panel.scrollIntoView({
        block: 'nearest',
        behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      });
    }),
  );
  panel?.querySelector('[data-close-skills]').addEventListener('click', () => {
    panel.hidden = true;
    trigger?.setAttribute('aria-expanded', 'false');
    trigger?.focus();
    activeSkill = null;
  });

  /** Prépare un courriel contextualisé ; aucun message n'est envoyé par le site. */
  function updateContact() {
    const en = language() === 'en';
    document.querySelectorAll('[data-project-contact]').forEach((link) => {
      const title = en ? link.dataset.titleEn : link.dataset.titleFr;
      const subject = en ? `About your project: ${title}` : `Échange au sujet du projet : ${title}`;
      const body = en
        ? `Hello Aurélien,\r\n\r\nI am contacting you about your project “${title}”.\r\n\r\n`
        : `Bonjour Aurélien,\r\n\r\nJe vous contacte au sujet de votre projet « ${title} ».\r\n\r\n`;
      link.href = `mailto:aurelien-capron@outlook.fr?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
  }

  const toc = document.querySelector('.page-toc');
  const tocLinks = toc ? [...toc.querySelectorAll('nav a[href^="#"]')] : [];
  const sections = tocLinks.map((link) =>
    document.getElementById(decodeURIComponent(link.hash.slice(1))),
  );
  let scheduled = false;
  /** Suit la dernière section atteinte sans déplacer le focus ni modifier l'historique. */
  function updateToc() {
    scheduled = false;
    let active = 0;
    sections.forEach((section, index) => {
      if (section && section.getBoundingClientRect().top <= 170) active = index;
    });
    tocLinks.forEach((link, index) => {
      if (index === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    const current = toc?.querySelector('.toc-current');
    if (current && tocLinks[active])
      current.textContent = tocLinks[active].querySelector('span:last-child').textContent;
  }
  function scheduleToc() {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(updateToc);
    }
  }
  tocLinks.forEach((link) =>
    link.addEventListener('click', () => {
      toc.open = false;
      scheduleToc();
    }),
  );
  if (toc) {
    window.addEventListener('scroll', scheduleToc, { passive: true });
    window.addEventListener('resize', scheduleToc);
    updateToc();
  }
  new MutationObserver(() => {
    renderEvidence();
    updateContact();
    scheduleToc();
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  updateContact();
  document
    .querySelectorAll('[data-media-back]')
    .forEach((link) => link.addEventListener('click', () => link.closest('dialog')?.close()));
})();

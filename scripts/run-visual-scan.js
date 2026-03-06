#!/usr/bin/env node
/**
 * Visual Pattern Scanner — runs all SPEC-000-A and SPEC-000-B checks
 * against a target URL using Playwright and outputs findings.json + report.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const TARGET_URL = process.argv[2] || 'https://www.fincap.org.nz/our-team/';
const OUTPUT_DIR = path.join(__dirname, '..', 'output');
const SCREENSHOTS_DIR = path.join(OUTPUT_DIR, 'screenshots');

fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

async function run() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  console.log(`Navigating to ${TARGET_URL}...`);
  await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Page loaded.');

  // Take full-page screenshot
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'our-team-full.png'), fullPage: true });

  const findings = [];

  // ========== SPEC-000-A: Heading Detection ==========
  console.log('Running heading detection...');
  const headingFindings = await page.evaluate(() => {
    const results = [];
    const bodyStyle = window.getComputedStyle(document.body);
    const bodyFontSize = parseFloat(bodyStyle.fontSize);
    const bodyFontWeight = parseInt(bodyStyle.fontWeight) || 400;

    // Class-based heading detection
    const allElements = document.querySelectorAll('*');
    for (const el of allElements) {
      const className = el.className;
      if (typeof className !== 'string') continue;
      if (/\bh[1-6]\b/i.test(className) && !/^h[1-6]$/i.test(el.tagName)) {
        const style = window.getComputedStyle(el);
        const text = el.textContent?.trim();
        if (!text) continue;
        results.push({
          url: window.location.href,
          type: 'Heading-like content',
          reason: `This appears to function as a heading but is not marked up as one. The element uses a <${el.tagName.toLowerCase()}> tag with class '${className.trim().split(/\s+/).find(c => /h[1-6]/i.test(c))}' and has visual characteristics of a heading: font size ${style.fontSize} (vs ${bodyFontSize}px body), weight ${style.fontWeight} (vs ${bodyFontWeight} body).`,
          location: {
            cssSelector: getCssSelector(el),
            xpath: getXPath(el)
          },
          visual: {
            fontSize: style.fontSize,
            fontWeight: style.fontWeight
          },
          screenshot: '',
          htmlSnippet: el.outerHTML.substring(0, 200),
          confidence: 0.95
        });
      }
    }

    // Visual heading detection (non-heading tags with large/bold text)
    const textTags = document.querySelectorAll('p, div, span, a, li, td, th, label, strong, em, b');
    for (const el of textTags) {
      if (el.closest('h1, h2, h3, h4, h5, h6')) continue;
      if (el.children.length > 3) continue;
      const style = window.getComputedStyle(el);
      const fontSize = parseFloat(style.fontSize);
      const fontWeight = parseInt(style.fontWeight) || 400;
      const text = el.textContent?.trim();
      if (!text || text.length > 100 || text.length < 2) continue;
      const isLarger = fontSize > bodyFontSize * 1.3;
      const isBolder = fontWeight >= 600;
      const isBlock = style.display === 'block' || style.display === 'flex';
      if (isLarger && isBolder && isBlock) {
        const alreadyFound = results.some(r => r.location.cssSelector === getCssSelector(el));
        if (!alreadyFound) {
          results.push({
            url: window.location.href,
            type: 'Heading-like content',
            reason: `Visually styled as a heading: font size ${style.fontSize} (${(fontSize / bodyFontSize * 100).toFixed(0)}% of body), weight ${style.fontWeight}, displayed as block. Not marked up with a heading tag.`,
            location: { cssSelector: getCssSelector(el), xpath: getXPath(el) },
            visual: { fontSize: style.fontSize, fontWeight: style.fontWeight },
            screenshot: '',
            htmlSnippet: el.outerHTML.substring(0, 200),
            confidence: 0.8
          });
        }
      }
    }

    function getCssSelector(el) {
      if (el.id) return `#${el.id}`;
      const parts = [];
      let current = el;
      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        if (current.id) { parts.unshift(`#${current.id}`); break; }
        const parent = current.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
          if (siblings.length > 1) {
            const idx = siblings.indexOf(current) + 1;
            selector += `:nth-of-type(${idx})`;
          }
        }
        parts.unshift(selector);
        current = current.parentElement;
      }
      return parts.join(' > ');
    }

    function getXPath(el) {
      const parts = [];
      let current = el;
      while (current && current.nodeType === 1) {
        let idx = 1;
        let sib = current.previousElementSibling;
        while (sib) {
          if (sib.tagName === current.tagName) idx++;
          sib = sib.previousElementSibling;
        }
        parts.unshift(`${current.tagName.toLowerCase()}[${idx}]`);
        current = current.parentElement;
      }
      return '/' + parts.join('/');
    }

    return results;
  });
  findings.push(...headingFindings);
  console.log(`  Found ${headingFindings.length} heading-like elements.`);

  // ========== SPEC-000-A: Card Detection ==========
  console.log('Running card detection...');
  const cardFindings = await page.evaluate(() => {
    const results = [];
    // Find repeated structures with image + text + link
    const articles = document.querySelectorAll('article, [class*="card"], [class*="Card"]');
    const patternGroups = {};

    for (const el of articles) {
      const hasImage = el.querySelector('img, [style*="background-image"]');
      const hasLink = el.querySelector('a[href]');
      const hasText = el.textContent?.trim().length > 10;
      if (hasImage && hasLink && hasText) {
        const classKey = el.className?.split?.(' ')?.sort()?.join(' ') || 'unknown';
        if (!patternGroups[classKey]) patternGroups[classKey] = [];
        patternGroups[classKey].push(el);
      }
    }

    for (const [cls, elements] of Object.entries(patternGroups)) {
      if (elements.length >= 2) {
        for (const el of elements) {
          const link = el.querySelector('a[href]');
          results.push({
            url: window.location.href,
            type: 'Card-like content',
            reason: `Repeated content group (${elements.length} instances with matching structure). Contains image, text, and link${link ? ' to ' + link.href : ''}. Review for keyboard focus and screen reader behaviour.`,
            location: { cssSelector: getCssSelector(el), xpath: getXPath(el) },
            visual: {},
            screenshot: '',
            htmlSnippet: el.outerHTML.substring(0, 200),
            confidence: 0.9
          });
        }
      }
    }

    function getCssSelector(el) {
      if (el.id) return `#${el.id}`;
      const parts = [];
      let current = el;
      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        if (current.id) { parts.unshift(`#${current.id}`); break; }
        const parent = current.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
          if (siblings.length > 1) {
            const idx = siblings.indexOf(current) + 1;
            selector += `:nth-of-type(${idx})`;
          }
        }
        parts.unshift(selector);
        current = current.parentElement;
      }
      return parts.join(' > ');
    }

    function getXPath(el) {
      const parts = [];
      let current = el;
      while (current && current.nodeType === 1) {
        let idx = 1;
        let sib = current.previousElementSibling;
        while (sib) {
          if (sib.tagName === current.tagName) idx++;
          sib = sib.previousElementSibling;
        }
        parts.unshift(`${current.tagName.toLowerCase()}[${idx}]`);
        current = current.parentElement;
      }
      return '/' + parts.join('/');
    }

    return results;
  });
  findings.push(...cardFindings);
  console.log(`  Found ${cardFindings.length} card-like elements.`);

  // ========== SPEC-000-B: 2.1 Government Identity ==========
  console.log('Running government identity checks...');
  const govFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;

    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      const parts = [];
      let current = el;
      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        if (current.id) { parts.unshift(`#${current.id}`); break; }
        const parent = current.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
          if (siblings.length > 1) {
            const idx = siblings.indexOf(current) + 1;
            selector += `:nth-of-type(${idx})`;
          }
        }
        parts.unshift(selector);
        current = current.parentElement;
      }
      return parts.join(' > ');
    }

    // Check for government branding/logo
    const logos = document.querySelectorAll('img[alt*="logo" i], img[alt*="crest" i], img[alt*="government" i], [class*="logo" i]');
    if (logos.length === 0) {
      results.push({ url, type: 'Government identity', reason: 'No government logo or branding element detected on the page.', location: { cssSelector: 'html', xpath: '/html' }, htmlSnippet: '', confidence: 0.7 });
    } else {
      const logo = logos[0];
      results.push({ url, type: 'Government identity', reason: `Logo/branding detected: ${logo.alt || logo.className || logo.tagName}. Verify it meets government identity requirements.`, location: { cssSelector: getCssSelector(logo), xpath: '' }, htmlSnippet: logo.outerHTML?.substring(0, 200) || '', confidence: 0.8 });
    }

    // Check for contact info
    const telLinks = document.querySelectorAll('a[href^="tel:"]');
    const mailLinks = document.querySelectorAll('a[href^="mailto:"]');
    const bodyText = document.body.textContent || '';
    const hasPhone = telLinks.length > 0 || /\b0[23789]\d[\s-]?\d{3,4}[\s-]?\d{3,4}\b/.test(bodyText) || /\+64/.test(bodyText);
    const hasEmail = mailLinks.length > 0;
    const hasAddress = /\b\d+\s+\w+\s+(street|st|road|rd|avenue|ave|drive|dr|place|pl|crescent|cres)\b/i.test(bodyText) || /P\.?O\.?\s*Box/i.test(bodyText);

    if (!hasPhone && !hasEmail && !hasAddress) {
      results.push({ url, type: 'Government identity', reason: 'No contact information detected (no phone, email, or physical address found).', location: { cssSelector: 'body', xpath: '/html/body' }, htmlSnippet: '', confidence: 0.7 });
    }

    // Check for copyright
    const hasCopyright = /copyright|©|\(c\)|crown copyright/i.test(bodyText);
    if (!hasCopyright) {
      results.push({ url, type: 'Government identity', reason: 'No copyright notice detected on the page.', location: { cssSelector: 'body', xpath: '/html/body' }, htmlSnippet: '', confidence: 0.6 });
    }

    // Check for privacy link
    const privacyLinks = document.querySelectorAll('a[href*="privacy" i]');
    const privacyText = Array.from(document.querySelectorAll('a')).filter(a => /privacy/i.test(a.textContent));
    if (privacyLinks.length === 0 && privacyText.length === 0) {
      results.push({ url, type: 'Government identity', reason: 'No privacy policy link detected on the page.', location: { cssSelector: 'body', xpath: '/html/body' }, htmlSnippet: '', confidence: 0.7 });
    }

    return results;
  });
  findings.push(...govFindings);
  console.log(`  Found ${govFindings.length} government identity findings.`);

  // ========== SPEC-000-B: 2.2 CAPTCHA Detection ==========
  console.log('Running CAPTCHA detection...');
  const captchaFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    const captchaSelectors = [
      'iframe[src*="recaptcha"]', 'iframe[src*="hcaptcha"]',
      '.g-recaptcha', '.h-captcha',
      'script[src*="recaptcha"]', 'script[src*="hcaptcha"]',
      '[id*="captcha" i]', '[class*="captcha" i]'
    ];
    let found = false;
    for (const sel of captchaSelectors) {
      const els = document.querySelectorAll(sel);
      if (els.length > 0) {
        found = true;
        results.push({ url, type: 'CAPTCHA detected', reason: `CAPTCHA element found matching "${sel}". CAPTCHAs can be a barrier for users with disabilities — ensure accessible alternatives are provided.`, location: { cssSelector: sel, xpath: '' }, htmlSnippet: els[0].outerHTML?.substring(0, 200) || '', confidence: 0.95 });
      }
    }
    if (!found) {
      // Check for "verify you are human" text
      const bodyText = document.body.textContent || '';
      if (/verify\s+(you\s+are|that\s+you('re|\s+are))\s+(human|not\s+a\s+robot)/i.test(bodyText)) {
        results.push({ url, type: 'CAPTCHA detected', reason: 'Text suggesting a CAPTCHA challenge detected ("verify you are human"). Review for accessibility.', location: { cssSelector: 'body', xpath: '/html/body' }, htmlSnippet: '', confidence: 0.7 });
      }
    }
    return results;
  });
  findings.push(...captchaFindings);
  console.log(`  Found ${captchaFindings.length} CAPTCHA findings.`);

  // ========== SPEC-000-B: 2.3 Carousel Detection ==========
  console.log('Running carousel detection...');
  const carouselFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      return el.tagName.toLowerCase() + (el.className ? '.' + el.className.trim().split(/\s+/).join('.') : '');
    }
    const selectors = [
      '[class*="carousel" i]', '[id*="carousel" i]',
      '[class*="slider" i]', '[id*="slider" i]',
      '[class*="swiper" i]', '[class*="slick" i]',
      '[class*="slideshow" i]'
    ];
    const seen = new Set();
    for (const sel of selectors) {
      const els = document.querySelectorAll(sel);
      for (const el of els) {
        const key = getCssSelector(el);
        if (seen.has(key)) continue;
        seen.add(key);
        // Check for pause controls
        const pauseBtn = el.querySelector('[aria-label*="pause" i], [aria-label*="stop" i], button:has([class*="pause" i])');
        const autoplay = el.hasAttribute('data-autoplay') || el.hasAttribute('data-auto-play') || el.getAttribute('data-ride') === 'carousel';
        let reason = `Carousel/slider component detected (${sel}).`;
        if (autoplay && !pauseBtn) {
          reason += ' Auto-play indicators found but no pause/stop control detected — may not meet WCAG 2.2.2 (Pause, Stop, Hide).';
        } else if (autoplay && pauseBtn) {
          reason += ' Auto-play and pause control detected.';
        }
        results.push({ url, type: 'Carousel detected', reason, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.85 });
      }
    }
    return results;
  });
  findings.push(...carouselFindings);
  console.log(`  Found ${carouselFindings.length} carousel findings.`);

  // ========== SPEC-000-B: 2.4 Disclosure/Accordion Detection ==========
  console.log('Running disclosure/accordion detection...');
  const disclosureFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      return el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : '');
    }
    // Native details/summary
    const details = document.querySelectorAll('details');
    for (const el of details) {
      const summary = el.querySelector('summary');
      results.push({ url, type: 'Disclosure widget detected', reason: `Native <details>/<summary> disclosure widget found. Summary text: "${summary?.textContent?.trim()?.substring(0, 50) || 'none'}".`, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.95 });
    }
    // ARIA-based
    const expanded = document.querySelectorAll('[aria-expanded]');
    for (const el of expanded) {
      if (el.closest('details')) continue;
      const controls = el.getAttribute('aria-controls');
      const target = controls ? document.getElementById(controls) : null;
      let reason = `Element with aria-expanded="${el.getAttribute('aria-expanded')}" detected.`;
      if (controls && target) {
        reason += ` Controls target #${controls} (found).`;
      } else if (controls && !target) {
        reason += ` aria-controls points to #${controls} but target element not found on page.`;
      } else {
        reason += ' No aria-controls attribute — target element is unclear.';
      }
      results.push({ url, type: 'Disclosure widget detected', reason, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.85 });
    }
    // Accordion class patterns
    const accordions = document.querySelectorAll('[class*="accordion" i], [id*="accordion" i]');
    for (const el of accordions) {
      if (results.some(r => r.htmlSnippet && el.outerHTML?.startsWith(r.htmlSnippet?.substring(0, 50)))) continue;
      results.push({ url, type: 'Disclosure widget detected', reason: `Accordion pattern detected (class/id contains "accordion").`, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.8 });
    }
    return results;
  });
  findings.push(...disclosureFindings);
  console.log(`  Found ${disclosureFindings.length} disclosure/accordion findings.`);

  // ========== SPEC-000-B: 2.5 Heading Text Quality ==========
  console.log('Running heading text quality checks...');
  const headingQualityFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      const parts = [];
      let current = el;
      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        if (current.id) { parts.unshift(`#${current.id}`); break; }
        const parent = current.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
          if (siblings.length > 1) {
            const idx = siblings.indexOf(current) + 1;
            selector += `:nth-of-type(${idx})`;
          }
        }
        parts.unshift(selector);
        current = current.parentElement;
      }
      return parts.join(' > ');
    }

    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const vaguePatterns = /^(click here|read more|learn more|more information|details|link|untitled|more|info)$/i;

    // Track heading texts for duplicate detection
    const headingTexts = {};
    const headingLevels = [];

    for (const h of headings) {
      const text = h.textContent?.trim() || '';
      const level = parseInt(h.tagName[1]);
      headingLevels.push({ level, el: h, text });

      // Vague text
      if (vaguePatterns.test(text)) {
        results.push({ url, type: 'Heading text quality', reason: `Heading <${h.tagName.toLowerCase()}> has vague text "${text}". Heading text should describe the content that follows.`, location: { cssSelector: getCssSelector(h), xpath: '' }, htmlSnippet: h.outerHTML?.substring(0, 200) || '', confidence: 0.9 });
      }

      // Empty headings
      if (!text || text.length === 0) {
        results.push({ url, type: 'Heading text quality', reason: `Empty <${h.tagName.toLowerCase()}> heading detected. Headings must have text content.`, location: { cssSelector: getCssSelector(h), xpath: '' }, htmlSnippet: h.outerHTML?.substring(0, 200) || '', confidence: 0.95 });
      }

      // Excessively long
      if (text.length > 80) {
        results.push({ url, type: 'Heading text quality', reason: `Heading <${h.tagName.toLowerCase()}> has ${text.length} characters ("${text.substring(0, 50)}..."). Headings should be concise and scannable (under ~80 characters).`, location: { cssSelector: getCssSelector(h), xpath: '' }, htmlSnippet: h.outerHTML?.substring(0, 200) || '', confidence: 0.7 });
      }

      // Track duplicates
      const key = `${level}:${text.toLowerCase()}`;
      if (!headingTexts[key]) headingTexts[key] = [];
      headingTexts[key].push(h);
    }

    // Duplicate headings
    for (const [key, els] of Object.entries(headingTexts)) {
      if (els.length > 1) {
        const text = els[0].textContent?.trim();
        const level = els[0].tagName;
        results.push({ url, type: 'Heading text quality', reason: `${els.length} duplicate <${level.toLowerCase()}> headings with text "${text}". Consider differentiating heading text to help users navigate.`, location: { cssSelector: getCssSelector(els[0]), xpath: '' }, htmlSnippet: els[0].outerHTML?.substring(0, 200) || '', confidence: 0.8 });
      }
    }

    // Heading hierarchy skips
    for (let i = 1; i < headingLevels.length; i++) {
      const prev = headingLevels[i - 1].level;
      const curr = headingLevels[i].level;
      if (curr > prev + 1) {
        results.push({ url, type: 'Heading text quality', reason: `Heading hierarchy skip: <h${prev}> followed by <h${curr}> (skipped h${prev + 1}). Heading levels should not skip (e.g., h1 to h3 without h2).`, location: { cssSelector: getCssSelector(headingLevels[i].el), xpath: '' }, htmlSnippet: headingLevels[i].el.outerHTML?.substring(0, 200) || '', confidence: 0.85 });
      }
    }

    return results;
  });
  findings.push(...headingQualityFindings);
  console.log(`  Found ${headingQualityFindings.length} heading text quality findings.`);

  // ========== SPEC-000-B: 2.6 Link Quality ==========
  console.log('Running link quality checks...');
  const linkFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      const parts = [];
      let current = el;
      while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        if (current.id) { parts.unshift(`#${current.id}`); break; }
        const parent = current.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
          if (siblings.length > 1) {
            const idx = siblings.indexOf(current) + 1;
            selector += `:nth-of-type(${idx})`;
          }
        }
        parts.unshift(selector);
        current = current.parentElement;
      }
      return parts.join(' > ');
    }

    const links = document.querySelectorAll('a[href]');
    const nonDescriptive = /^(click here|here|read more|more|link|download|this|page|website|this link)$/i;

    for (const link of links) {
      const text = link.textContent?.trim() || '';
      const ariaLabel = link.getAttribute('aria-label') || '';
      const accessibleName = ariaLabel || text;

      // Non-descriptive link text
      if (nonDescriptive.test(text) && !ariaLabel) {
        results.push({ url, type: 'Link quality', reason: `Link with non-descriptive text "${text}". Link text should describe the destination or purpose of the link.`, location: { cssSelector: getCssSelector(link), xpath: '' }, htmlSnippet: link.outerHTML?.substring(0, 200) || '', confidence: 0.9 });
      }

      // Empty links
      if (!accessibleName && !link.querySelector('img[alt]')) {
        results.push({ url, type: 'Link quality', reason: 'Empty link with no visible text, aria-label, or image with alt text. Links must have an accessible name.', location: { cssSelector: getCssSelector(link), xpath: '' }, htmlSnippet: link.outerHTML?.substring(0, 200) || '', confidence: 0.95 });
      }

      // Opens in new window without warning
      if (link.target === '_blank') {
        const hasWarning = /new (window|tab)/i.test(text + ariaLabel) ||
          link.querySelector('[class*="external" i], [class*="new-window" i], [aria-label*="new" i]');
        if (!hasWarning) {
          results.push({ url, type: 'Link quality', reason: `Link "${text.substring(0, 40)}" opens in a new window (target="_blank") without indicating this to users. Add "(opens in new tab)" or equivalent to the link text or aria-label.`, location: { cssSelector: getCssSelector(link), xpath: '' }, htmlSnippet: link.outerHTML?.substring(0, 200) || '', confidence: 0.8 });
        }
      }

      // aria-label doesn't include visible text
      if (ariaLabel && text && !ariaLabel.toLowerCase().includes(text.toLowerCase()) && text.length > 1) {
        results.push({ url, type: 'Link quality', reason: `Link aria-label "${ariaLabel}" does not contain the visible text "${text}". Per WCAG 2.5.3 (Label in Name), aria-label should include the visible text.`, location: { cssSelector: getCssSelector(link), xpath: '' }, htmlSnippet: link.outerHTML?.substring(0, 200) || '', confidence: 0.85 });
      }
    }

    // Adjacent duplicate links
    const linkList = Array.from(links);
    for (let i = 0; i < linkList.length - 1; i++) {
      const a = linkList[i], b = linkList[i + 1];
      if (a.href === b.href && a.parentElement === b.parentElement) {
        results.push({ url, type: 'Link quality', reason: `Adjacent duplicate links pointing to "${a.href.substring(0, 60)}". Consider combining into a single link element.`, location: { cssSelector: getCssSelector(a), xpath: '' }, htmlSnippet: a.outerHTML?.substring(0, 200) || '', confidence: 0.75 });
      }
    }

    return results;
  });
  findings.push(...linkFindings);
  console.log(`  Found ${linkFindings.length} link quality findings.`);

  // ========== SPEC-000-B: 2.7 Skip Link Detection ==========
  console.log('Running skip link detection...');
  const skipLinkFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      return el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : '');
    }

    const allLinks = document.querySelectorAll('a[href^="#"]');
    const skipLinks = Array.from(allLinks).filter(a => /skip/i.test(a.textContent || '') || /skip/i.test(a.getAttribute('aria-label') || ''));

    if (skipLinks.length === 0) {
      results.push({ url, type: 'Skip link', reason: 'No skip navigation link detected. Pages should include a "Skip to content" link as the first focusable element for keyboard users (WCAG 2.4.1).', location: { cssSelector: 'body', xpath: '/html/body' }, htmlSnippet: '', confidence: 0.8 });
    } else {
      for (const skip of skipLinks) {
        const targetId = skip.getAttribute('href')?.substring(1);
        const target = targetId ? document.getElementById(targetId) : null;
        let reason = `Skip link found: "${skip.textContent?.trim()}" pointing to #${targetId}.`;
        if (target) {
          reason += ` Target element found (<${target.tagName.toLowerCase()}>).`;
        } else {
          reason += ' Target element not found on the page.';
        }

        // Check position
        const focusable = document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        const position = Array.from(focusable).indexOf(skip) + 1;
        if (position > 3) {
          reason += ` Skip link is at position ${position} in tab order (should be among the first).`;
        }

        results.push({ url, type: 'Skip link', reason, location: { cssSelector: getCssSelector(skip), xpath: '' }, htmlSnippet: skip.outerHTML?.substring(0, 200) || '', confidence: 0.9 });
      }
    }
    return results;
  });
  findings.push(...skipLinkFindings);
  console.log(`  Found ${skipLinkFindings.length} skip link findings.`);

  // ========== SPEC-000-B: 2.8 Modal Detection ==========
  console.log('Running modal detection...');
  const modalFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    function getCssSelector(el) {
      if (!el) return '';
      if (el.id) return `#${el.id}`;
      return el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/).join('.') : '');
    }

    // Native dialog elements
    const dialogs = document.querySelectorAll('dialog');
    for (const el of dialogs) {
      const hasLabel = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      results.push({ url, type: 'Modal dialog detected', reason: `Native <dialog> element found.${hasLabel ? ' Has accessible name.' : ' Missing aria-label or aria-labelledby.'}`, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.95 });
    }

    // ARIA dialogs
    const ariaDialogs = document.querySelectorAll('[role="dialog"], [role="alertdialog"]');
    for (const el of ariaDialogs) {
      const hasModal = el.getAttribute('aria-modal') === 'true';
      const hasLabel = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      const hasClose = el.querySelector('button[aria-label*="close" i], button[class*="close" i], [class*="dismiss" i]');
      let reason = `ARIA ${el.getAttribute('role')} detected.`;
      reason += hasModal ? ' aria-modal="true" present.' : ' aria-modal not set.';
      reason += hasLabel ? ' Has accessible name.' : ' Missing accessible name (aria-label/aria-labelledby).';
      reason += hasClose ? ' Close mechanism found.' : ' No obvious close button detected.';
      results.push({ url, type: 'Modal dialog detected', reason, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.9 });
    }

    // Class-based modal patterns
    const modalClasses = document.querySelectorAll('[class*="modal" i]:not([role="dialog"]):not([role="alertdialog"]):not(dialog), [id*="modal" i]:not([role="dialog"]):not([role="alertdialog"]):not(dialog)');
    for (const el of modalClasses) {
      if (el.closest('dialog, [role="dialog"], [role="alertdialog"]')) continue;
      results.push({ url, type: 'Modal dialog detected', reason: `Element with modal class/id pattern detected but without proper dialog role. Consider using <dialog> or role="dialog" with aria-modal="true".`, location: { cssSelector: getCssSelector(el), xpath: '' }, htmlSnippet: el.outerHTML?.substring(0, 200) || '', confidence: 0.7 });
    }

    return results;
  });
  findings.push(...modalFindings);
  console.log(`  Found ${modalFindings.length} modal findings.`);

  // ========== SPEC-000-B: 2.9 Page Title ==========
  console.log('Running page title check...');
  const titleFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;
    const title = document.title?.trim() || '';
    const generic = /^(untitled|home|page|welcome|document)$/i;

    if (!title) {
      results.push({ url, type: 'Page title', reason: 'No page title found or title is empty. Pages must have a descriptive <title> element (WCAG 2.4.2).', location: { cssSelector: 'head > title', xpath: '/html/head/title' }, htmlSnippet: '<title></title>', confidence: 0.95 });
    } else if (generic.test(title)) {
      results.push({ url, type: 'Page title', reason: `Page title "${title}" is generic. Page titles should uniquely describe the page content.`, location: { cssSelector: 'head > title', xpath: '/html/head/title' }, htmlSnippet: `<title>${title}</title>`, confidence: 0.85 });
    } else {
      results.push({ url, type: 'Page title', reason: `Page title found: "${title}" (${title.length} characters). Review for accuracy and descriptiveness.`, location: { cssSelector: 'head > title', xpath: '/html/head/title' }, htmlSnippet: `<title>${title}</title>`, confidence: 0.5 });
    }

    return results;
  });
  findings.push(...titleFindings);
  console.log(`  Found ${titleFindings.length} page title findings.`);

  // ========== SPEC-000-B: 2.10 Print Stylesheet ==========
  console.log('Running print stylesheet check...');
  const printFindings = await page.evaluate(() => {
    const results = [];
    const url = window.location.href;

    // Check for print stylesheets
    const printLinks = document.querySelectorAll('link[media="print"], link[media*="print"]');
    const styleSheets = document.querySelectorAll('style');
    let hasPrintInline = false;
    for (const s of styleSheets) {
      if (s.textContent?.includes('@media print')) {
        hasPrintInline = true;
        break;
      }
    }

    if (printLinks.length > 0 || hasPrintInline) {
      results.push({ url, type: 'Print stylesheet reminder', reason: `Print styles detected (${printLinks.length} print stylesheet link(s)${hasPrintInline ? ', inline @media print rules' : ''}). Verify print output is usable — check that important content is visible and navigation/decorative elements are hidden.`, location: { cssSelector: 'head', xpath: '/html/head' }, htmlSnippet: '', confidence: 0.6 });
    } else {
      results.push({ url, type: 'Print stylesheet reminder', reason: 'No print stylesheet detected. Manual print check recommended — pages should be usable when printed.', location: { cssSelector: 'head', xpath: '/html/head' }, htmlSnippet: '', confidence: 0.5 });
    }

    return results;
  });
  findings.push(...printFindings);
  console.log(`  Found ${printFindings.length} print stylesheet findings.`);

  // ========== Take highlighted screenshot ==========
  console.log('Taking highlighted screenshot...');
  // Highlight all found elements with red overlays
  await page.evaluate(() => {
    const headingLike = document.querySelectorAll('*');
    for (const el of headingLike) {
      const cn = el.className;
      if (typeof cn === 'string' && /\bh[1-6]\b/i.test(cn) && !/^h[1-6]$/i.test(el.tagName)) {
        el.style.outline = '3px solid red';
        el.style.outlineOffset = '2px';
      }
    }
  });
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'our-team-highlighted.png'), fullPage: true });

  // ========== Write output ==========
  const outputPath = path.join(OUTPUT_DIR, 'findings.json');
  fs.writeFileSync(outputPath, JSON.stringify(findings, null, 2));
  console.log(`\nTotal findings: ${findings.length}`);
  console.log(`Output written to: ${outputPath}`);

  // Summary by type
  const typeCounts = {};
  for (const f of findings) {
    typeCounts[f.type] = (typeCounts[f.type] || 0) + 1;
  }
  console.log('\nFindings by type:');
  for (const [type, count] of Object.entries(typeCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${type}: ${count}`);
  }

  // ========== Generate Markdown report ==========
  const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
  let report = `# Visual Pattern Scan Report\n\n`;
  report += `**URL:** ${TARGET_URL}\n`;
  report += `**Date:** ${now}\n`;
  report += `**Total Findings:** ${findings.length}\n\n`;
  report += `## Summary by Type\n\n`;
  report += `| Type | Count |\n|------|-------|\n`;
  for (const [type, count] of Object.entries(typeCounts).sort((a, b) => b[1] - a[1])) {
    report += `| ${type} | ${count} |\n`;
  }
  report += `\n---\n\n`;
  report += `## Findings\n\n`;
  for (let i = 0; i < findings.length; i++) {
    const f = findings[i];
    report += `### Finding ${i + 1}: ${f.type}\n\n`;
    report += `- **Reason:** ${f.reason}\n`;
    if (f.location?.cssSelector) report += `- **CSS Selector:** \`${f.location.cssSelector}\`\n`;
    if (f.visual?.fontSize) report += `- **Font Size:** ${f.visual.fontSize}\n`;
    if (f.visual?.fontWeight) report += `- **Font Weight:** ${f.visual.fontWeight}\n`;
    if (f.htmlSnippet) report += `- **HTML:** \`${f.htmlSnippet.replace(/`/g, "'")}\`\n`;
    if (f.confidence !== undefined) report += `- **Confidence:** ${f.confidence}\n`;
    report += `\n`;
  }
  report += `---\n\n*Generated: ${now}*\n`;

  const reportPath = path.join(OUTPUT_DIR, 'accessibility-scan-report.md');
  fs.writeFileSync(reportPath, report);
  console.log(`Report written to: ${reportPath}`);

  await browser.close();
  console.log('Done.');
}

run().catch(err => {
  console.error('Scan failed:', err);
  process.exit(1);
});

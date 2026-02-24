**Check my website** 

**About the tool** 

**Scope** 

This is a tool that scans webpages and looks at elements to check them against certain patterns to find components, for example cards or headings.  

It is designed to assist accessibility testing by scanning whole webpages and highlighting issues that need to be manually checked. 

The intent is to complement CWAC scans. The CWAC scans look for patterns that fails the WCAG criteria, which can be programmatically tested.  

This tool will look for patterns, with AI helping to: 

* Detect “heading-like” visual patterns   
* Detect “card-like” content structures   
* Explain findings in plain language. 

**Headings** 

Finds text that has a class with H1, H2, H3, H4, H5 or H6 in the name 

Finds text that is formatted like a heading, e.g., larger or darker than the other text and on a line by itself  

**Cards** 

Finds groups of content that contain an image, a heading or text that looks like a heading, and some text. Where these elements are wrapped in a link to another page.  

**Output** 

List of what was found with the URL, and where on the webpage it was found.  

Give me a screen shot of the item with the area highlighted and tell me the target in the code. 

Each finding should always include: 

* URL   
* Type (Heading-like, Card-like)   
* DOM location (CSS selector \+ XPath)   
* Screenshot with highlighted region   
* Code target (HTML snippet \+ attributes)   
* Reason *why* it was flagged 

**Future scope** 

* Interactive content on the right side of the page   
* Sticky content 

 

**High-level architecture** 

**Layers** 

* Crawler   
* DOM Analyzer   
* Visual Analyzer   
* AI Reasoning   
* Reporter 

**DOM & rules-based analysis (non-AI)** 

This layer does the **deterministic work**. 

A. Heading detection (code-based) 

Detect: 

* Elements with class names containing: h1, h2, h3, h4, h5, h6   
* Case-insensitive, partial matches 

Also record: 

* Tag name   
* ARIA roles   
* Font size, weight, color   
* Position in DOM 

This gives you a **known baseline** before AI interpretation. 

B. Card candidate detection (structure-based) 

Find groups where: 

* A link (\<a\>) wraps:   
* An image (\<img\> or background-image)   
* AND a heading   
* AND text   
* OR multiple elements in a group that share the same link destination 

Heuristics: 

* Bounding boxes overlap or align vertically   
* Same parent container   
* Repeated patterns across the page 

Output these as **“card candidates”**, not violations. 

**Visual analysis layer (semi-AI)** 

This is where you detect *things that look like headings*. 

C. Heading-like visual patterns 

Flag text where: 

* Font size is larger than body text   
* Font weight is heavier   
* Text is isolated on its own line   
* Has margin above/below   
* Appears before a block of content 

**AI reasoning layer (LLM)** 

Feed the model: 

* HTML snippet   
* Computed styles   
* Screenshot crop   
* Context (surrounding DOM) 

Ask it to: 

* Classify:   
* “Is this functioning as a heading?”   
* “Is this functioning as a card?”   
* Explain *why* in human language   
* Suggest what *might* be wrong (not auto-fail) 

**Screenshot & highlighting system** 

**How to do this** 

For each flagged item: 

1. Get bounding box from Playwright   
2. Take a full-page screenshot   
3. Draw a rectangle overlay around the element   
4. Save:   
* Full screenshot   
* Cropped screenshot 

**What to store** 

* Screenshot path   
* Element selector   
* Pixel coordinates 

This is critical for: 

* QA review   
* Stakeholder buy-in   
* Audit evidence 

**Output format** 

Outputs a structured JSON then renders it. 

Example: 

{ 

  "url": "https://example.com/page", 

  "type": "Heading-like content", 

  "reason": "Text is visually styled as a heading but not marked up as one", 

  "location": { 

	"cssSelector": ".card-title", 

	"xpath": "//\*\[@class='card-title'\]" 

  }, 

  "visual": { 

	"fontSize": "28px", 

	"fontWeight": "700" 

  }, 

  "screenshot": "screenshots/page1-item3.png", 

  "htmlSnippet": "\<div class='card-title'\>Services\</div\>" 

} 

Future versions: 

* Export to CSV   
* Feed into reports 

**Build phases (as recommended by AI)** 

Phase 1 – Proof of concept  

* Crawl a single page   
* [Our Team | FinCap](https://www.fincap.org.nz/our-team/) (cards and pseudo headings)   
* [E Tū Whānau stories \- Te mana kaha o te whānau\!](https://etuwhanau.org.nz/stories-of-positive-change/) (cards)   
* Detect:   
* Class-based headings   
* Visually large text   
* Screenshot \+ highlight   
* JSON output only 

Phase 2 – Card detection 

* Detect linked content groups   
* Identify repeated patterns   
* Screenshot each card 

Phase 3 – AI explanations 

* Add LLM classification \+ explanations   
* Focus on *confidence scoring*, not pass/fail 

Phase 4 – UI / integration 

* Simple web UI or report viewer   
* Link findings back to CWAC scan IDs 

 

**6\. Key design principles (important)** 

* **Never auto-fail WCAG**   
  This tool *flags patterns*, not violations.   
* **Explain, don’t judge**   
  “This appears to function as a heading but is not marked up as one.”   
* **Deterministic first, AI second**   
  AI should interpret, not discover from scratch.   
* **Auditor trust \> AI cleverness** 

![Shape][image1] 

**7\. What you should do next (concrete steps)** 

1. **Choose Playwright** as your page engine   
2. Build a script that:   
* Loads a page   
* Extracts all text nodes \+ computed styles   
3. Define your **visual heading thresholds**   
4. Output JSON \+ screenshots   
5. Only then introduce AI classification 

If you want, next I can: 

* Sketch the **data model**   
* Draft **Playwright pseudocode**   
* Help you write the **AI prompt**   
* Or map this directly to **WCAG advisory language** 

 

 

*Playwrite mcp server – runs code for you* 

*Claude has a browser extension to drive the browser* 

 

 

 

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4XmNgAAIAAAUAAQYUdaMAAAAASUVORK5CYII=>
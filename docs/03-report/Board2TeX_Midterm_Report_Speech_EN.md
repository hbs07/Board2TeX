# Board2TeX Midterm Report — Presentation Script (EN)

> Companion to "Board2TeX Midterm Report"
> Format: **four presenters, relay style** · Target length: **about 3.6 minutes** (including handovers) · 7 slides
> Blocks: **each speaker presents one continuous segment** — Guo Jiaxin (Slides 1–2, opening), Hu Bingshan (Slides 3–4), Tao Puzhou (Slides 5–6), Li Ruochen (Slide 7, closing)
> **Bold** = slow down and stress. `[pause]` = one-second pause.
> Text in parentheses is a cue; do not read it aloud.
> Anything already shown on the slide (comparison, division table, timeline, metrics) is **not read aloud** — point to the screen instead.
> Hand over naturally: the next speaker steps up and bridges with one sentence before starting.

---

## Slide 1 · Title (15 sec) · Guo Jiaxin

Hello everyone. I'm Guo Jiaxin from Group __. Our project is **Board2TeX: it turns a photo of a blackboard into a compilable LaTeX document**. The four of us will present it in relay.

---

## Slide 2 · Problem and Goal (40 sec) · Guo Jiaxin

Here is why. Taking a photo is easy, but typing every formula into LaTeX by hand is **slow and error-prone**. Existing tools like Mathpix charge per use, and only recognize a **single formula** — not a full board, not mixed text and formulas. So we are building a **free, end-to-end tool for whole boards**. The detailed comparison is on the slide.

(Handover) Next, Hu Bingshan will present the system design.

---

## Slide 3 · System Design (35 sec) · Hu Bingshan

Thank you, Jiaxin. The pipeline has five stages — please follow the diagram. Preprocessing separates the writing from the background. Layout analysis **splits the board into lines** and labels each as text or formula. Recognition sends text lines to PaddleOCR and formula lines to pix2tex. Composition builds a compilable LaTeX file. And the desktop app handles **proofreading, PDF export, and the error notebook**.

(Continue) Now, the key technical problems.

---

## Slide 4 · Key Technical Problems (40 sec) · Hu Bingshan

Four points — the details are on the slide, so I'll take one sentence each. **Illumination enhancement**: CLAHE plus automatic thresholding — simple and stable. **Line segmentation**: counting foreground pixels per row to find the gaps between lines. **Text versus formula**: a geometric first guess, with manual correction in the UI. **Compilable LaTeX**: uniform escaping, verified by actually compiling with xelatex.

(Handover) Now Tao Puzhou will explain the team division and the schedule.

---

## Slide 5 · Team Division (25 sec) · Tao Puzhou

Thanks, Bingshan. One sentence on our principle: **the proposal was decided together; each of us owns one module, and pairs up to review another** — the full table is on the slide. All code goes to GitHub, and **the commit history is the record of each person's contribution**.

(Continue) Next, the schedule.

---

## Slide 6 · Schedule (15 sec) · Tao Puzhou

The schedule is on the timeline: this midterm report is Week 5; then core modules, interface work and evaluation, the report, and the final presentation.

(Handover) Finally, Li Ruochen will present the expected outcomes.

---

## Slide 7 · Expected Outcomes (30 sec) · Li Ruochen

Thanks, Puzhou. We will deliver a **Windows desktop program** that runs the full pipeline from photo to PDF, with an error notebook. The targets — **above 90% line-segmentation accuracy and above 70% end-to-end usability** — are on the slide. Recognition uses open-source models, which we will state in the report; the rest of the code is written by the four of us.

That is our report. Thank you.

> [pause] Now I am happy to take questions.

---

## Backup · Likely Questions

**Q: Isn't this just calling existing models?**
> Recognition does use existing models, but the illumination enhancement, line segmentation, and mixed composition are written by us. Single-formula recognition exists, but the full path from a whole board to a compilable document — plus English text mixed with formulas and the error notebook — is something existing tools do not offer.

**Q: What if recognition is wrong?**
> That is exactly why we build the proofreading interface. Low-confidence regions are highlighted, and the user can fix them and re-export. We are not aiming for full automation — we aim to remove most of the manual work.

**Q: Will you make it in time?**
> The biggest risk was whether the environment and models can run, and we have already verified that up front. Interfaces and module boundaries freeze in Week 6, and each of us owns one module while covering another, so we are fairly confident.

**Q: Why no perspective correction?**
> Perspective correction requires tuning contour detection and coordinate transforms, which is a poor return on effort for first-year students. Shooting the board straight is enough for the first version; automatic correction is planned as future work.

**Q: Why not handle double columns?**
> Double-column segmentation is error-prone and has a low return on effort. The first version focuses on making single columns solid; double columns come later.

---

## Backup · On-site Demo Notes

- Launch the program and load the models beforehand — do not run it for the first time on stage;
- Prepare 3–5 carefully chosen sample photos, shot as straight as possible;
- Before exporting a PDF, confirm the demo machine has xelatex installed; otherwise only demo the `.tex` export;
- Also keep a recorded demo video as a backup in case of lag.

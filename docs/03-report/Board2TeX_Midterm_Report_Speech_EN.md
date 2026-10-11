# Board2TeX Midterm Report — Presentation Script (EN)

> Companion to "Board2TeX Midterm Report"
> Format: **four presenters, relay style** · Target length: **about 5 minutes** (including handovers) · 7 slides
> Blocks: **each speaker presents one continuous segment** — Guo Jiaxin (Slides 1–2, opening), Hu Bingshan (Slides 3–4), Tao Puzhou (Slides 5–6), Li Ruochen (Slide 7, closing)
> **Bold** = slow down and stress. `[pause]` = one-second pause.
> Text in parentheses is a cue; do not read it aloud.
> Hand over naturally: the next speaker steps up and bridges with one sentence before starting.

---

## Slide 1 · Title (15 sec) · Guo Jiaxin

Hello everyone. I'm Guo Jiaxin from Group __. Our project is called Board2TeX. In short, it turns a photo of a blackboard into a compilable LaTeX document. All four of us built this project together, and today each of us will present one continuous part of it. Let me first explain the problem and our goal.

---

## Slide 2 · Problem and Goal (45 sec) · Guo Jiaxin

Let me start with why we are doing this.

Taking photos of the board with a phone is easy, but when we review, we have to type every formula into LaTeX by hand — slow, and easy to get wrong. Existing tools like Mathpix charge per use, and they only recognize a screenshot of a **single formula**. They cannot handle a full board, and they do not support English text mixed with formulas.

So we want to build a **free** tool that works on a whole board. Our target users are students who want to archive board notes, and teaching assistants and instructors who need to turn derivations into handouts.

What sets our project apart is the complete end-to-end flow — from a full board all the way to a compilable document — with **English text mixed with formulas**, and an **error notebook** for archiving. Existing tools offer none of these.

(Handover) Next, Hu Bingshan will walk you through the system design.

---

## Slide 3 · System Design (50 sec) · Hu Bingshan

Thank you, Jiaxin. Our pipeline has five stages.

First, preprocessing: we resize the photo, then convert to grayscale, normalize the lighting, and binarize, so the writing stands out clearly from the background. Second, layout analysis: we split the board into lines, and judge whether each line is text or a formula. Third, recognition: text lines go to PaddleOCR, formula lines go to pix2tex. Fourth, composition: everything is assembled into a compilable LaTeX file in reading order. Fifth, the application: in a desktop program, the user proofreads, exports a PDF, and saves the result to an error notebook.

Our stack is Python, OpenCV, PaddleOCR, pix2tex, PyQt5, and SQLite.

(Continue) Now let me zoom into the key technical problems.

---

## Slide 4 · Key Technical Problems (60 sec) · Hu Bingshan

First, **illumination enhancement**. Phone photos of a board are often half bright, half dark. We equalize the lighting with CLAHE, then binarize with Otsu's automatic threshold — both are ready-made OpenCV functions, and the combination is simple and stable.

Second, **line segmentation**. We count foreground pixels per row and treat the blank rows as the boundaries between lines. It is simple and stable, and the first version handles single columns only.

Third, **telling text and formulas apart**. They need different engines, so we first judge by geometric features, and let the user correct uncertain cases in the interface.

Fourth, **producing compilable LaTeX**. Characters like percent, ampersand, and underscore break compilation if not escaped, so we escape them uniformly and verify by compiling with xelatex.

(Handover) Now Tao Puzhou will explain how we divide the work and stay on schedule.

---

## Slide 5 · Team Division (45 sec) · Tao Puzhou

Thanks, Bingshan. Our division of work is built on full participation by all four of us: the proposal, the design, and the schedule were all decided together. During development, each of us owns one core module and also pairs up to join another module for development and code review, so every one of us understands the whole pipeline.

Specifically, Hu Bingshan owns the image entry, main integration, and the UI framework; Guo Jiaxin owns image enhancement and line segmentation; I own recognition integration and LaTeX composition; Li Ruochen owns the interface, export, and the error notebook. After the interfaces freeze in Week 6, each of us first runs a minimal example of our own module using the shared skeletons, test images, and verification commands. All code goes to GitHub, and the commit history is the record of each person's contribution.

(Continue) Next, the schedule.

---

## Slide 6 · Schedule (30 sec) · Tao Puzhou

In terms of timing, we formed the team in Week 4, and this midterm report is in Week 5. Weeks 6 to 10 will finish the core modules, Weeks 11 to 15 the interface, integration, and evaluation, Week 16 the report, and Week 17 the final presentation.

(Handover) Finally, Li Ruochen will present the expected outcomes.

---

## Slide 7 · Expected Outcomes (30 sec) · Li Ruochen

Thanks, Puzhou. We plan to deliver a Windows desktop program that runs the whole pipeline, from photo to PDF, and can save to the error notebook. On metrics, we are aiming for line-segmentation accuracy above 90%, and an end-to-end usability rate above 70%.

Recognition uses open-source models, which we will state clearly in the report; the rest of the code is written by the four of us ourselves.

That is our report. Thank you — from all four of us.

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

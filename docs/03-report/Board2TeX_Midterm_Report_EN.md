# Board2TeX Midterm Report

**Board-to-LaTeX One-Click Archiving Tool**

ICSP (Track A) Midterm Report · Fall 2026

> Team Members: Hu Bingshan (Team Leader), Guo Jiaxin, Tao Puzhou, Li Ruochen
> Repository: https://github.com/hbs07/Board2TeX

---

## 1. Background and Objectives

Our project is called Board2TeX. It aims to solve one concrete problem: automatically converting a photo of a blackboard or whiteboard into a directly compilable LaTeX document.

Taking photos of a blackboard with a phone is quick and convenient, but at the review stage, transcribing every formula from the photo into LaTeX or Word is time-consuming and error-prone. Existing tools of this kind, such as Mathpix, have two shortcomings: first, they charge per use; second, they only recognize a screenshot of a single formula, and cannot handle a full board, nor English text mixed with formulas. We therefore plan to develop a free tool capable of processing an entire board. Its target users are of two kinds: students who want to archive board notes for review, and teaching assistants and instructors who need to turn in-class derivations into handouts. Compared with existing tools, the innovation of this project lies in providing a complete end-to-end pipeline from a full board to a compilable document, supporting English text mixed with formulas, and offering error-notebook archiving—none of which existing tools provide.

---

## 2. System Design

The processing pipeline consists of five stages:

```
Input photo
  ↳ (1) Image preprocessing: resizing → grayscale → illumination normalization → binarization → cropping
  ↳ (2) Layout analysis: split the board into lines, and classify each line as text or formula
  ↳ (3) Recognition: text lines to PaddleOCR, formula lines to pix2tex
  ↳ (4) Composition: assemble into a compilable .tex in reading order
  ↳ (5) Application: proofread, export PDF, and save to the error notebook in a desktop program
```

The technology stack is Python, OpenCV, PaddleOCR, pix2tex, PyQt5, and SQLite. For recognition we use open-source pretrained models, which run on CPU without a dedicated GPU.

---

## 3. Key Technical Problems

We focus on the following four problems.

First, illumination and binarization enhancement. Photos of a blackboard usually have uneven lighting. We apply CLAHE for illumination normalization, then Otsu's automatic threshold for binarization, so that the writing separates cleanly from the background; both steps combine ready-made OpenCV functions.

Second, layout segmentation. A blackboard is written line by line. By counting the number of foreground pixels in each row, the blank regions serve as the boundaries between lines. This method is simple and stable. The first version handles only single-column layouts.

Third, distinguishing text from formulas. Since the two kinds of content require different recognition engines, we first make a preliminary judgment based on geometric features such as aspect ratio and connected components; for uncertain results, the user is allowed to correct them in the interface.

Fourth, generating compilable LaTeX. Characters such as the percent sign, the ampersand, and the underscore will cause compilation failure if not escaped, so escaping is applied uniformly, and the result is verified by actually compiling with xelatex.

In addition, to ensure on-time delivery, the first version does not support perspective correction, double-column layouts, in-line block splitting, glare removal, or live preview (shooting the board straight is enough); these are left to later versions. Among the above problems, illumination enhancement, layout segmentation, and mixed-layout composition are all implemented by this project itself and account for the bulk of the project workload; recognition uses open-source pretrained models, and our work lies in the integration, wrapping, and post-processing.

---

## 4. Team Division

The project follows a model of shared participation, module ownership, and cross-coverage: requirements analysis, system design, and scheduling are decided jointly by all four members; during development, each member owns one core module while also pairing up to join another module for development and code review, so that every member gains an end-to-end understanding of the pipeline.

Module ownership is as follows: the team leader, Hu Bingshan, owns image preprocessing, main program integration, the UI framework, and PDF compilation; Guo Jiaxin owns image enhancement and line segmentation; Tao Puzhou owns recognition engine integration and LaTeX composition; Li Ruochen owns the interface, export, and the error notebook.

To keep collaboration smooth, after the interfaces are frozen in Week 6, each member first runs a minimal example of their own module against the shared function skeletons, test images, and verification commands; during integration, all members take part in locating and fixing problems. Code is committed to GitHub uniformly, with commit records serving as evidence of each member's participation. This midterm report is likewise delivered jointly by all four members, each presenting the part that corresponds to their own work.

---

## 5. Schedule

Week 4: team formation. Week 5: this midterm report. After that, Weeks 6–10 will complete the core modules, Weeks 11–15 the interface, integration, and evaluation, Week 16 the project report, and Week 17 the final presentation.

| Week | Main work |
|---|---|
| Week 6 | Freeze interfaces, distribute skeletons, run a minimal example each |
| Week 7–8 | Image enhancement, layout analysis, recognition wrappers |
| Week 9–10 | Recognition and composition, integrated with the layout module |
| Week 11–12 | Export, error notebook, and UI controls |
| Week 13–14 | Assemble the interface, complete the full pipeline |
| Week 15 | Evaluation, integration and packaging, demo preparation |
| Week 16 | Write the project report |
| Week 17 | Final presentation |

To make the plan actionable, the deliverables and owners of each module are defined: image preprocessing outputs the enhanced binary image (Hu Bingshan and Guo Jiaxin); layout analysis outputs the region list with reading order (Guo Jiaxin); recognition and composition outputs the compilable .tex (Tao Puzhou); application and evaluation outputs the desktop program, error notebook, and evaluation report (Li Ruochen). The data structures between modules will be frozen in Week 6; any later change must first update the interface agreement.

---

## 6. Expected Outcomes

We plan to deliver a Windows desktop program that realizes the full pipeline from photo input to PDF output, and supports saving results to the error notebook. In terms of metrics, the target for the line-segmentation accuracy is above 90% (on neat board notes), and the end-to-end usability rate (usable with only minor manual edits) above 70%. Deliverables include the GitHub repository, a one-click environment verification script, a demo video, and the project report.

---

## 7. AI Usage Statement

For recognition, we use the open-source pretrained models PaddleOCR and pix2tex, which will be clearly stated in the report. The code for preprocessing, layout, composition, interface, and the error notebook is written by the team members themselves, and the report will explain each member's contribution module by module. If AI assistance is used during debugging, it will also be noted in code comments and in the report.

---

*Detailed plans are available in the proposal outline and the four role-specific documents.*

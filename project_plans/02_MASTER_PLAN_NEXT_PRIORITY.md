# Tennis Technique Desktop App — Master Plan: Next Priority

Version: 1.0  
Date: 2026-11-14  
Status: Phase 2 implementation specification; features and accuracy are not yet implemented or verified.  
Audience: A future implementation agent or developer with no access to the originating chat.  
Prerequisite: [Highest-priority master plan](01_MASTER_PLAN_HIGHEST_PRIORITY.md).

## 1. Purpose and inherited decisions

Build a personal desktop application for a beginner improving tennis stroke technique from horizontal phone video. The user wants to see a body skeleton over their movement, compare with good demonstrations or earlier attempts, and understand whether practice changes a specific skill.

The highest-priority plan supplies precise playback, a confidence-aware skeleton overlay, synchronized comparison, editable stroke moments, evidence-linked feedback, and skill-focused history. This document extends that workflow with repeated-attempt analysis, focused measurements, practice exercises, ball/racket tracking, and recording guidance.

The learning loop remains:

**Observe a specific skill → understand evidence → practice a change → repeat a comparable check.**

Automatic video cutting and match-strategy analysis are outside both plans. A manually selected attempt is a saved source-video range, not a cut-file feature.

### Technical foundation retained

- Local Python desktop application; primary target is the user's Mac, with actual hardware/OS qualification required.
- PySide6 for UI, OpenCV for image operations, PyAV/FFmpeg for timestamp-aware media handling, a replaceable MediaPipe-based body-pose adapter, NumPy for calculations, and SQLite for records.
- Packaged macOS application; users must not need a terminal, a separately installed Python environment, or a server.
- Core review and analysis work offline after model installation. Preserve local storage and privacy behavior.
- CPU operation is required; acceleration is optional and benchmarked.
- Keep source media, source timestamps, confidence/validity, transformations, manual corrections, and analysis versions.
- Use background jobs with cancellation, bounded memory, and cache reuse.
- Phase 1's complete time/coordinate/data contracts remain authoritative; this document adds to them.

The starting automated coaching scope is forehand. Backhand and serve can use the shared review tools, but automated criteria and drills require stroke-specific definitions and validation.

## 2. Phase 2 entry gate

Before implementing aggregate judgments, verify that Phase 1 can:

1. Decode and review representative phone videos with correct timestamps and orientation.
2. Maintain the intended player's identity or explicitly stop on ambiguity.
3. Display missing tracking honestly.
4. Save and correct event markers and evidence-linked observations.
5. Compare two attempts without silent timing drift.
6. Reopen a skill focus, reference, and follow-up recording after restart.
7. Keep human annotations distinct from model output.

Do not build trend charts on top of unvalidated measurements. An aggregate of unreliable labels is still unreliable.

## 3. P1-01 — Compare several repetitions

### Beginner-facing purpose

Help the user tell whether a movement pattern is recurring, occasional, or improving. One selected stroke cannot establish consistency.

### User experience

- Select several attempts from one practice set and link them to the same skill focus.
- Review a compact sequence or contact sheet of the same event across attempts.
- Filter by assessable attempts, confirmed observations, and footage needing review.
- Compare similar practice sets from different dates.
- Keep representative difficult attempts, not only favorite examples.
- Let the user revise attempt membership and mark an attempt unassessable, with a reason.

### Analysis rules

- Initial grouping is manual; detecting strokes across a whole recording is not a prerequisite.
- Compare the same stroke type, review criterion/version, relevant camera view, and similar feed/movement conditions.
- Count assessable attempts separately from all selected attempts.
- Show numerator and denominator, not a bare percentage.
- Treat unassessable footage as missing evidence, never as a successful or failed attempt.
- Use a default minimum of 10 assessable comparable attempts across a set before summarizing frequency; this is a product guardrail, not proof of statistical reliability. Below it, show individual evidence and a small-sample notice.
- Describe observed differences without asserting that a practice cue caused them.
- Preserve comparisons across easy and harder conditions as separate groups. For example, stationary self-feeds and moving partner feeds should not merge into one trend.

Example, explicitly illustrative: “Crowded contact was marked in 7/10 assessable attempts in the baseline set and 3/10 in this set. Both used stationary feeds from the same view. Two additional attempts today were unassessable.”

### Records added

- PracticeSet: session, stroke, drill/feed context, movement condition, view, selected attempts.
- AttemptAssessment: criterion/version, result, evidence, author/source, assessability and exclusion reason.
- AggregateSnapshot: source assessment IDs, denominator rules, calculations, creation time, analysis version.

### Acceptance criteria

- Every count opens its contributing attempts; exclusions are inspectable.
- Changing a label recomputes the active summary and preserves superseded snapshots.
- Different criteria/model versions are not silently combined. Reanalyze comparable historical footage under one version or mark a break.
- An empty or wholly unassessable set displays no numerical progress claim.
- Tests cover denominator errors, deleted/moved attempts, changed labels, and mixed practice conditions.

## 4. P1-02 — Focused movement traces and measurements

### Beginner-facing purpose

Use a measurement when it clarifies a practice question. The main output remains video evidence and an explanation, not a screen full of numbers.

### Initial supported measurement candidates

1. Wrist trajectory during the selected swing, explicitly labeled as wrist movement.
2. Time between manually confirmed or validated events, such as forward-swing onset and contact.
3. Selected projected elbow or knee angles when landmarks and camera view are suitable.
4. Contact-position annotations across repetitions, initially manually marked and view-specific.
5. Serve-toss position variation from a fixed camera, only after ball tracking or manual marking supports it.

These are candidates requiring separate qualification. An angle or duration does not automatically define good technique.

### Technical requirements

- Implement a versioned measurement registry: name, definition, units, input requirements, supported view, calculation, missing-data policy, and validation status.
- Compute image angles in an aspect-correct coordinate system; do not calculate geometry directly from differently scaled normalized x/y coordinates.
- A projected angle is a 2D image-plane estimate, not a true 3D anatomical angle.
- Use source timestamps for temporal calculations; withhold real-world durations when slow-motion mapping is unknown.
- Keep raw and filtered signals, confidence masks, filter settings, and algorithm version.
- Do not bridge substantial missing spans or smooth away genuine movement changes. Any interpolated values must remain identifiable and cannot establish exact contact.
- Use fixed-view or carefully documented body-relative normalization for comparisons. State units such as pixels or body-length ratios; do not invent centimeters without calibration.
- Camera movement, perspective, and normalization can change paths. Detect/flag or require manual confirmation before a trace is used for comparison.
- Keep numerical work in Python/NumPy; use OpenCV for transforms. Add SciPy only if a specific validated filtering method requires it.
- Render traces over video using the same transform pipeline as the body skeleton.

Sports2D is a useful evaluation reference for 2D trajectories and angles, but its own documentation cautions about motion plane and pose accuracy. Evaluate it as an optional alternative or benchmark; it is not a required second production pipeline. [Sports2D](https://github.com/davidpagnon/Sports2D)

### Records added

- MeasurementDefinition and MeasurementRun.
- Numeric artifacts with timestamps, units, validity masks, coordinate conventions, and filter metadata.
- Source marker/landmark dependencies and uncertainty reasons.

### Acceptance criteria

- Synthetic coordinate tests verify angles, transforms, mirror behavior, and units.
- Real footage is compared against manually annotated events/landmarks where practical.
- Report error and usable-coverage separately for each measurement and view.
- Replacing a source marker invalidates dependent measurements.
- No trajectory of the wrist is labeled as a racket trajectory.
- No metric is promoted into a coaching threshold solely because it can be computed.

## 5. P1-03 — Practice exercises connected to observations

### Beginner-facing purpose

Turn a review into a manageable practice action and a concrete recheck. Phase 1 stores a cue; Phase 2 adds a small, structured exercise library and follow-up workflow.

### User experience

- For an applicable confirmed or clearly provisional observation, suggest one suitable exercise.
- Explain setup, task, one cue, and what to record afterward.
- Let the user record completion and a short reflection.
- Link the next attempt set directly to the original practice focus.
- If no exercise is validated for the observation/context, allow a manual practice note rather than generating an unrelated prescription.

### Exercise data

Each exercise includes:

- ID, version, title, intended stroke and skill.
- Applicable observation criteria and prerequisites.
- Beginner-friendly setup and instructions.
- One main cue and coach-reviewed practice dose where appropriate.
- A demonstration or source reference.
- A measurable or visually assessable recheck.
- Reviewer/source, review date, and publication status.

### Technical implementation

- Store curated exercise definitions as versioned JSON or database content validated against a schema.
- Use deterministic matching of observation/context to eligible exercises first.
- Keep exercise selection editable and preserve the version actually practiced.
- No external language model is required. If added in future implementation, it must not invent observations, exercises, or results; changing cloud/privacy requirements is a separate product decision.
- Store attempt-linked user outcomes such as clean contact, ball reaching a target area, or serve in/out, with manual origin labeled. These are practice outcomes, not match-strategy statistics.

### Acceptance criteria

- Every recommendation has an applicable criterion, source/reviewer, and recheck.
- Unsupported criteria do not produce confident drill prescriptions.
- Users can see which cue they actually practiced before reviewing follow-up footage.
- A changed exercise version does not silently change historical practice records.
- Treat “felt easier” as user reflection, not automatic evidence that technique improved.

Teaching material may inform the library; it does not validate the app's detection logic. Relevant starting sources include [USTA contact spacing](https://www.usta.com/en/home/improve/tips-and-instruction/national/find-your-optimal-contact-point.html) and [LTA beginner serve guidance](https://www.lta.org.uk/play/tennis-tips-and-techniques/how-to-hit-a-serve-for-beginners/).

## 6. P1-04 — Racket and ball tracking

### Beginner-facing purpose

Improve contact review and explain how the racket moves relative to the body and ball. Body pose alone cannot reliably supply these objects.

### Progressive delivery

1. Manual marking: mark ball center and racket head on selected frames or a contact interval. This is the useful baseline.
2. Assisted tracking: propagate marks over short local spans, with visible gaps and easy correction.
3. Detector-assisted tracking: evaluate an appropriate object detector plus temporal association against the manual baseline.
4. Contact suggestions: propose a contact interval only when independent evidence supports it, with user correction available.

Do not commit to a particular new detector before measuring small-object performance on representative phone footage. Model runtime, dependency footprint, supported hardware, and model/code licenses must be evaluated before adoption.

### Technical requirements

- Use original-resolution frames or documented high-resolution regions around the selected player. A body-pose resize can make the ball disappear.
- OpenCV may support local optical flow, region tracking, and geometric checks. Color thresholds alone are not a reliable general tennis-ball detector.
- Combine detections with temporal association and a bounded motion model. Record detection versus propagated/interpolated origin.
- Reject or flag nearby-court balls, racket-shaped background objects, motion blur, occlusion, and implausible track jumps.
- Do not bridge contact occlusion with a fabricated exact impact frame.
- Store racket-head observations separately from wrist landmarks. If only a bounding box is known, do not infer racket-face orientation from it.
- Estimate contact as an interval/candidate supported by ball-racket proximity and available trajectory evidence. Optional audio is supplementary and may belong to another court.
- Preserve an explicit null/unassessable state.
- Run tracking jobs locally and only for selected attempt ranges by default.

### Records added

- ObjectTrack: object type, source timestamps, coordinates/bounds, confidence, origin, model version, corrections.
- ContactCandidate: supporting tracks/frames, estimated interval, uncertainty, and user confirmation.
- Coordinate/transform links to the same source space used by body pose.

### Acceptance criteria

- Evaluate on held-out people and recording sessions, including different ball sizes in the frame, light, backgrounds, and blur.
- Report tracking coverage, location error against annotations, false associations, and contact timing error separately.
- Set metric-specific release thresholds before final evaluation with the intended use in mind.
- Manual marking remains usable when tracking fails.
- Unreliable tracking disables dependent contact conclusions while preserving body/video review.
- Failure on a distant whole-court recording must not become a confident spacing diagnosis.

## 7. P1-05 — Recording guidance and suitability checks

### Beginner-facing purpose

Help the user obtain footage that can answer the skill question. Existing recordings remain usable for whatever review they support.

### User experience

- Before the next recording, select the skill being reviewed and show a simple camera-placement guide.
- Recommend a fixed landscape view, clear full-body/racket coverage, suitable lighting, and enough player detail for the selected analysis.
- Explain the tradeoff between a wider view for movement and a closer view for contact detail.
- Offer side and rear/diagonal examples with explanations of what each view can reveal; do not claim one angle measures every movement.
- Higher frame rate is helpful for contact review when available, but accept ordinary footage and adjust the available analysis.
- After import, provide capability-specific results: suitable for body review, suitable for this measurement, contact unclear, or needs manual inspection.
- A recording-quality limitation must never lower a player's skill assessment.

### Technical implementation

- Extract resolution, orientation, frame timing, duration, and encoding metadata.
- Evaluate image sharpness, exposure, player size, body/racket truncation where detectable, landmark coverage, and camera movement over sampled intervals.
- OpenCV blur/exposure/motion heuristics are provisional signals; tune them on actual footage and explain specific issues rather than displaying an unexplained universal quality score.
- Separate automatic checks from manual input, such as camera-view confirmation or verification that the racket is visible.
- Store the suitability result per intended capability and interval, with algorithm version and reasons.
- Calibration/view mismatch can disable a measurement without preventing basic playback and annotation.

### Acceptance criteria

- Known blur, occlusion, framing, and camera-motion examples trigger appropriate capability limitations.
- Clear supported footage is not rejected by an arbitrary universal threshold.
- The user can override a recording suggestion for visual review; overriding does not convert unsupported measurements into reliable ones.
- The same suitability definition is applied to reference footage and personal footage.

## 8. Shared analysis and data integrity requirements

### Separate evidence from judgments

Maintain distinct layers:

1. Source video and metadata.
2. Raw body/object observations and validity.
3. Derived markers and measurements.
4. Tennis-specific interpretations using versioned criteria.
5. Practice actions and follow-up records.

User corrections must be attributed and auditable. Reanalysis must not overwrite confirmed manual data. Store the dependency chain so changing a marker, model, or calibration invalidates the relevant derived result.

### Comparable progress

- Always show what was compared, under which practice conditions, and how many attempts were usable.
- Preserve reference clip, camera view, handedness, and criterion versions.
- Prefer a small number of meaningful measures tied to a focus.
- Exclude missing evidence without hiding the exclusion count.
- Do not compare different camera projections as equivalent anatomical quantities.
- When a model upgrade changes outputs, recompute a comparable historical set under the same version or mark the discontinuity.

### Storage and migrations

Extend the Phase 1 SQLite schema through tested migrations. Save numeric arrays separately with hashes and schema metadata. Preserve the same portable library structure, backups, non-executable serialization, immutable originals, and local-only defaults.

Build user-facing explanations from saved evidence, not from unsupported language-model guesses. Raw model confidence is not necessarily a calibrated probability that a coaching conclusion is correct.

## 9. Recommended implementation order

This order reflects dependencies, not a change to the user-agreed feature priorities:

1. Add practice sets and manual repeated-attempt review using existing observations.
2. Add recording guidance and capability checks so later measures have suitable input.
3. Add one or two focused measurements, beginning with confirmed-event timing and a clearly labeled wrist trace.
4. Add a small curated exercise library and follow-up links for supported criteria.
5. Add manual ball/racket marks, then assisted tracking, then validated detector-based tracking.
6. Enable aggregate automatic claims only for criteria that pass their validation gates.
7. Extend validated skill modules to backhand and serve after the forehand workflow works end to end.

Do not require automated ball tracking before releasing useful manual contact comparison. Do not require a large exercise catalog before validating that one exercise-to-recheck loop helps the user.

## 10. Verification and completion criteria

Use pytest for computation, timestamps, aggregate denominators, migrations, and invalidation rules. Use pytest-qt and manual packaged-app checks for interaction workflows. Do not rely only on visual demos with ideal footage.

Required evidence before calling Phase 2 complete:

- Practice sets produce inspectable, correct counts with explicit exclusions.
- Each released measurement has a definition, units, supported views, and recorded evaluation results.
- Exercises have reviewed sources, applicability, and a usable recheck.
- Ball/racket tracking has been benchmarked; unsupported cases degrade to manual review.
- Suitability checks distinguish video limitations from technique observations.
- Reanalysis, corrections, model changes, backup, and restore preserve history accurately.
- A beginner can complete a baseline → practice → comparable follow-up workflow and explain the evidence for the reported difference.
- The packaged desktop app retains local operation and responsive background processing.

If a capability has not met its validation gate, document it as incomplete or experimental. A polished UI, skeleton overlay, or generated report is not evidence that the underlying coaching is accurate.

## 11. Current handoff state and source context

At document creation, no app implementation, user-footage evaluation, coach review, or benchmark has been completed. Actual video quality and device capability remain unknown. Build on the highest-priority document and verify the implementation state before starting work.

Relevant researched tool patterns:

- [Kinovea](https://kinovea.org/features.html): movement observation, annotation, and synchronized comparison; useful workspace precedent.
- [Onform analysis tools](https://support.onform.com/article/116-analysis-tools): visual comparison and feedback interaction ideas. This is not an endorsement of all automated conclusions.
- [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker): initial body-observation component.
- [Sports2D](https://github.com/davidpagnon/Sports2D): optional reference for 2D measurements and their limitations.

Treat product documentation as evidence of documented features, not independently tested coaching accuracy. Verify current APIs and dependency compatibility when implementing. Keep the two master documents synchronized when requirements materially change.

# Tennis Technique Desktop App — Master Plan: Highest Priority

Version: 1.0  
Date: 2026-11-14  
Status: Implementation specification; no app, analyzed user footage, or validated accuracy is claimed by this document.  
Audience: A future implementation agent or developer with no access to the originating chat.  
Companion: [Next-priority master plan](02_MASTER_PLAN_NEXT_PRIORITY.md).

## 1. Read this first

Build a personal desktop application that helps a beginner understand and improve tennis stroke technique from phone video. The user particularly wants a body skeleton overlay, comparison against a good example, and a record of improvement over time.

The central experience is:

**Watch my movement → understand a specific observation → compare with a demonstration → practice one change → revisit comparable footage.**

This document defines Phase 1, the highest-priority release. The companion defines Phase 2. Complete the Phase 1 learning workflow before expanding into Phase 2. Both are master specifications, not evidence that features already exist.

### Confirmed user intent

- The user is a beginner who recently started tennis.
- Input is existing horizontal phone video.
- The focus is physical skills and stroke mechanics, not match strategy.
- The user wants to compare against professional players or other good demonstrations.
- The user wants records that help explain improvement across sessions.
- A visible stick-figure body overlay is a central feature.
- Automatic video cutting, removing idle time, and highlight generation are a separate feature and are outside these plans.
- Deliver an actual desktop application using Python and OpenCV; specify the other necessary components.

### Product decisions made by this plan

- Use Python with a PySide6 desktop interface, OpenCV image operations, and a replaceable pose-estimation adapter initially implemented with MediaPipe Tasks.
- Process and store video locally. No account, cloud server, API key, or network connection is required for the main workflow after installation/model setup.
- Target the user's Mac first. The exact processor and macOS version have not been verified. Qualify the stack on the actual machine before committing to binary dependencies; Apple Silicon is the initial packaging target, not a verified fact about the user's hardware.
- Build one complete forehand workflow first. The data model and comparison workspace must also accept backhand and serve footage; do not claim automated coaching for those strokes until their criteria are implemented and validated.
- Use manually selected stroke ranges initially. A range is a bookmark into the original recording, not an exported cut file.
- Keep manual correction available wherever automation is uncertain.

## 2. Success means learning, not merely displaying tracking

A beginner must be able to open an attempt, see a relevant movement, understand the evidence for a specific observation, save a practice focus, and return later to compare a new attempt.

The first release must make these questions easy to answer:

1. What happened during my stroke?
2. At which moment did it happen?
3. What does a suitable demonstration show?
4. What one thing am I practicing?
5. What changed in later footage under similar conditions?

Do not equate a convincing skeleton animation with correct tennis coaching. Pose detection, event timing, and coaching judgments are separate capabilities with separate evaluation.

## 3. Supported workflow and screen layout

### Skill library

Organize entry points around Forehand, Backhand, and Serve. Each skill opens its current practice focus, related recordings, reference demonstrations, and prior reviews. A date-based session list can support this, but must not replace the skill-oriented organization.

### Review workspace

- Center: the user's video; optional second pane for a reference or previous attempt.
- Below: timeline, frame controls, loop range, and stroke-event markers.
- Beside the video: observation, evidence links, explanation, and one practice cue.
- Collapsible history: baseline, practice changes, and follow-up attempts for this focus.
- Skeleton and annotations are layers over the actual video, never a replacement for it.

### First-use sequence

1. Choose a local library folder and import a recording.
2. Choose stroke type, handedness, backhand style if relevant, and broad camera view.
3. Mark a short range containing an attempt and select the player to analyze.
4. Review slow motion with the skeleton overlay.
5. Confirm or edit key-event markers.
6. Open a local reference clip or earlier personal attempt and align the comparison.
7. Save an evidence-linked observation and practice focus.
8. On a later visit, attach a follow-up attempt to the same focus.

## 4. Phase 1 feature requirements

### P0-01 — Precise video review

Required behavior:

- Import common MP4/MOV phone videos; qualify H.264 and HEVC using real fixtures.
- Provide normal playback, 0.5× and 0.25× playback, pause, frame-step forward/backward, zoom, pan, and looping of a selected range.
- Preserve aspect ratio and correctly apply orientation metadata.
- Keep the original file unchanged.
- Store each selected attempt as start/end timestamps into a source asset.
- Long recordings must be readable without loading the whole recording into memory. Analyze only selected ranges.
- If a codec or unusual file cannot be decoded, show a specific explanation and retain any existing work. Do not crash or silently misread time.
- Audio playback is optional in Phase 1; the app must clearly communicate if playback is silent.

Acceptance:

- Frame stepping selects actual neighboring decoded frames, including variable-frame-rate input.
- A saved range opens at the same source positions after restarting the app.
- Zooming and resizing do not displace annotations relative to the video.
- Opening a long recording has bounded memory use; duration does not cause linear growth in decoded-frame RAM.

### P0-02 — Body skeleton overlay

Required behavior:

- Estimate and connect visible body landmarks for the selected player.
- Toggle the overlay and emphasize relevant groups such as shoulders/arms or hips/legs.
- Use landmark validity/visibility to hide or fade uncertain segments.
- Select the target person manually. If identity becomes ambiguous, stop that analysis span and request reselection rather than silently switching players.
- Cache inference results and keep them separate from the original media.
- Provide a way to flag an incorrect tracking span and exclude it from analysis. Detailed manual joint editing is not required in Phase 1.

Technical constraints:

- Start with the MediaPipe Tasks Pose Landmarker VIDEO interface, not an assumed legacy API.
- Use source timestamps for sequential inference. Reinitialize tracking when processing disjoint ranges or seeking backward.
- Store coordinates in a canonical, orientation-corrected source-image space. Track the complete crop/resize/display transformation.
- Keep raw outputs and a separately versioned display-smoothed result. Do not smooth across missing spans or introduce unrecorded phase shifts into event measurements.
- Body landmarks are estimates. They do not establish the ball, racket head, exact grip, muscle force, weight distribution, or true depth.
- Default to a 2D overlay. Estimated depth must not become calibrated biomechanical truth.

Acceptance:

- Overlay registration is visually correct after rotation, zoom, resize, and optional display mirroring.
- Missing or obscured joints do not appear as confident invented observations.
- A second player entering the image does not silently take over the selected identity.
- A cached analysis loads without rerunning inference.

MediaPipe documents video body-landmark estimation; its output is the starting input to this feature, not a tennis-quality assessment. [Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker)

### P0-03 — Synchronized comparison

Required behavior:

- Compare two local recordings: user versus reference, or user versus earlier self.
- Let each pane seek independently before synchronization.
- Set a shared anchor, normally confirmed contact, and play both panes from one comparison clock.
- Support synchronized frame navigation and independent zoom/pan.
- Support optional mirroring to aid opposite-handed comparison, visibly labeled; preserve anatomical left/right labels in stored data.
- Save alignment, view settings, selected ranges, reference identity, and the concept being studied.
- Ask for or record stroke type, handedness, and camera view for references.
- Show view/context mismatch information. Visual review can continue, but unsupported numerical comparison must be withheld.

Timing rule:

For a comparison-relative time t, map each video to its own anchor timestamp plus t, adjusted only for a verified source slow-motion time mapping. Do not let two independent players drift. Select frames according to presentation timestamps, not a shared frame number.

Phase navigation may jump to each video's matching event. Label that mode clearly; it is not proof that the two movements took the same time. Do not silently time-warp a stroke to make it resemble a reference.

Acceptance:

- Different-frame-rate videos remain anchored during repeated play/pause/seek operations.
- The selected frame in each pane is within one local source-frame interval of the requested comparison time when in range.
- End-of-range behavior is explicit; do not loop one pane while the other continues unnoticed.
- Saved comparison state survives restart.

Kinovea's event-based synchronization is a useful interaction reference. [Comparison documentation](https://www.kinovea.org/help/en/observation/comparison.html)

### P0-04 — Key stroke moments

Required event vocabulary for the first forehand workflow:

- Preparation onset.
- Forward-swing onset.
- Contact, or a contact interval if the exact frame is unresolved.
- Finish/recovery checkpoint, defined by the selected review criterion.

Support manual placement first. Add automatic suggestions only where validated. Each marker records source timestamp, origin (manual/model), confidence or uncertainty, and user confirmation status. Definitions must be visible to reviewers; different interpretations of preparation onset must not be silently mixed.

If the ball/racket cannot be resolved, mark contact as approximate or unknown. Never substitute a wrist-velocity peak and present it as confirmed ball impact.

Acceptance:

- Markers are editable, ordered consistently, and linked to source frames.
- Changing a marker invalidates or recomputes dependent observations without erasing earlier review history.
- Unknown contact still permits visual comparison using a manually chosen alternative anchor, clearly labeled.

### P0-05 — Evidence-linked feedback

Display no more than two primary observations per review and allow one active practice focus. Distinguish:

1. Observation: what is visible and where.
2. Interpretation: what it may imply, with uncertainty.
3. Practice cue: a concise action connected to that observation.
4. Recheck: what to look for in a future comparable attempt.

Initial forehand analysis scope:

- Preparation sequence: describe visible body/racket preparation and forward-swing order. Do not call preparation late relative to the ball without relevant ball-event evidence.
- Contact spacing: assess only when person, racket, ball, and a usable contact interval are visible or manually marked. A body skeleton alone is insufficient.
- Visible movement control can be annotated manually. Avoid inferring physical balance or weight transfer from a single apparent position.

Every automated criterion must have a versioned definition specifying applicable stroke, camera view, required evidence, calculation or label rubric, abstention conditions, explanation template, cue source, and validation status.

Release policy:

- Implement manual/user/coach observations with the same evidence structure from the start.
- An automatic criterion becomes a coaching feature only after a qualified tennis coach reviews its rubric and an independent labeled evaluation supports it.
- Until then, expose descriptive movement annotations or explicitly provisional suggestions. Do not label them validated coaching.
- Public instructional material can inform a cue, but is not proof that an algorithm reliably detects the problem.
- No external language-model service is required. Prefer curated explanation templates for the first release.

Acceptance:

- Clicking an observation opens its supporting source frame or interval.
- Every observation shows who/what created it and whether it is confirmed, provisional, rejected, or unassessable.
- Users can correct or reject an observation without corrupting source data.
- A cue does not appear as a diagnosis when the required evidence is unavailable.

Example teaching source: USTA describes crowding at contact as a beginner issue. The detection rubric still requires separate validation. [Contact-spacing guidance](https://www.usta.com/en/home/improve/tips-and-instruction/national/find-your-optimal-contact-point.html)

### P0-06 — Skill-focused learning history

The central record is a practice focus such as “Forehand: leave enough room at contact.” Store:

- Baseline attempt(s), including representative difficulties.
- Evidence-linked observation and its author/source.
- Chosen reference demonstration and comparison configuration.
- Practice cue and user notes about what was tried.
- Practice conditions: self-feed, partner/coach feed, machine feed, or rally; stationary/moving; broad camera view.
- Later attempts attached to the same focus.
- A qualitative review of what changed and what remains uncertain.
- Status: active, reviewing, or archived. Archiving must not imply mastery.

Phase 1 supports visual before/after review and human notes. Automated repetition counts, aggregate metrics, and trend claims belong to Phase 2.

Acceptance:

- A user can resume an existing focus and compare its baseline with a new attempt.
- Video evidence, notes, markers, and comparisons survive restart and backup/restore.
- Reviews distinguish changed practice conditions from comparable attempts.
- Reanalysis creates a new version and does not overwrite human confirmation or old evidence.

## 5. Runtime and implementation requirements

### Desktop delivery

- Native desktop window, file picker, keyboard playback controls, and local filesystem access.
- Primary delivery is a macOS .app that launches without a terminal or a separately installed Python interpreter.
- Use Python 3.12 as the initial development target; qualify compatible wheels for the actual CPU/OS and pin the tested environment. A documented compatibility change is acceptable if required by the selected model runtime.
- Use PySide6/Qt Widgets with a custom video canvas for deterministic frame/overlay composition.
- Prototype packaging early with pyside6-deploy; a documented packaging alternative is acceptable if actual compatibility testing requires it.
- Record the tested macOS version, CPU, RAM, and supported media profiles. Windows/Linux are architectural portability goals, not Phase 1 release promises.
- Development needs a compiler/toolchain where packaging requires it; end users must not need those tools.

Qt's deployment tool supports packaged desktop applications, including macOS app bundles. Packaging the complete selected dependency set still needs testing. [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)

### Selected components and responsibilities

- Python: application orchestration, analysis, persistence, and worker jobs.
- PySide6: desktop UI, controls, annotations, and rendering.
- OpenCV: color conversion, geometric transforms, crops, image-quality operations, and later tracking primitives. It is not the source of truth for playback time.
- PyAV with FFmpeg libraries: timestamp-aware decoding and precise access to frames. If an FFmpeg/ffprobe executable is separately needed, bundle or explicitly provision it; do not assume it exists on PATH.
- MediaPipe Tasks: initial body-pose adapter.
- NumPy: typed numeric arrays and geometric calculations.
- SQLite: metadata, skill history, observations, links, and migration state.
- JSON plus compressed numeric artifacts: versioned configuration and pose arrays. Use non-executable serialization; do not load untrusted pickle files.
- pytest and pytest-qt: meaningful processing and desktop interaction tests.

Prefer opencv-python-headless because PySide6 owns the GUI. Inspect dependency constraints first: install exactly one OpenCV wheel variant providing cv2, including transitive requirements. If the pinned model package requires a different variant, resolve the dependency set explicitly and smoke-test Qt rather than installing conflicting variants. [OpenCV package guidance](https://pypi.org/project/opencv-python-headless/)

### Time, decoding, and transforms

- Store original presentation timestamp and time base; derive seconds without assuming constant frame rate.
- Keep a decoded-frame index with source timestamps. Seeking means seek to a suitable keyframe, decode forward, and select the required frame; reverse stepping may require bounded caching/redecode.
- Normalize inference timestamps while preserving a reversible mapping to the original source time. Handle missing/duplicate timestamps explicitly and mark uncertain timing.
- Phone slow-motion exports may have retiming. Unless a capture-to-playback mapping is verified, permit visual review but withhold claims in real-world seconds.
- Preserve transform metadata for source rotation, crop, analysis resize, display scale, and optional mirroring.
- If using preview proxies, preserve a source-time mapping and use source-detail frames for paused contact review. Never measure the proxy as though it were the original.

PyAV distinguishes timestamp values and time bases; this plan uses those concepts to prevent variable-frame-rate synchronization errors. [PyAV time documentation](https://pyav.org/docs/stable/api/time.html)

### Background work and responsiveness

- Never decode large ranges or run inference on the GUI thread.
- Use bounded decode queues and an isolated analysis worker process; use spawn-safe startup for macOS and frozen bundles.
- Let users cancel analysis, see progress, and continue reviewing cached content.
- CPU execution must work. Acceleration is optional and must have a tested fallback.
- Process one selected attempt at a time by default. Do not require inference over an entire long recording.
- Cache by media hash, range, selected player, model hash, and preprocessing/configuration version.
- No real-time inference target is required. Benchmark actual processing speed and report it honestly.

## 6. Data contract and storage

Use stable IDs and schema migrations. At minimum define these entities:

- PlayerProfile: handedness, backhand style, optional user label.
- SkillFocus: stroke type, learning question, cue, status, linked baseline/follow-up attempts.
- PracticeSession: date/time, practice conditions, notes.
- MediaAsset: content hash, library-relative path, media metadata, source type (personal/reference), orientation, timing characteristics, reference attribution.
- Attempt: asset ID, source range, stroke type, selected player/region, camera view, session ID.
- AnalysisRun: input hashes, attempt ID, model/runtime/configuration versions, job status, artifact locations.
- PoseArtifact: source timestamps, landmarks, validity fields, coordinate definition, transform and smoothing versions.
- EventMarker: attempt ID, event definition/version, source time or interval, origin, uncertainty, confirmation state.
- Observation: criterion/version, observation text, separate interpretation, evidence links, author/source, review state, superseded-by relationship.
- Comparison: two attempt IDs, anchors, mirroring/display settings, context compatibility notes.
- PracticeEntry: focus ID, session/attempt links, cue tried, user reflection, follow-up review.

Store files in a user-selected library directory with a SQLite database and separate media, analysis, and thumbnail areas. Copy imported media into the managed library by default, preserving bytes and checking disk space. Reference clips are local files with optional source URL/credit metadata, not automatically downloaded URLs.

Use atomic artifact writes and database transactions. Keep library-relative paths so a library can move between folders. Treat thumbnails and derived pose data as regenerable; original media, annotations, and learning history are not disposable caches.

Provide backup/restore of database plus required media and annotations. Use a consistent SQLite backup or checkpointed snapshot rather than blindly copying an active database. Restoring must validate schema compatibility and media hashes. Deleting an app record must not delete the original file outside the library.

Persist analysis/model versions so future changes do not silently rewrite the user's progress. No default telemetry or uploading of frames.

## 7. Evaluation and release gates

All numerical goals here are proposed engineering acceptance targets, not achieved results.

### Functional fixtures

Test: 30/60 fps, variable frame rate, orientation metadata, HEVC/MOV, H.264/MP4, source slow-motion with known and unknown retiming, two-person footage, occlusion, mirrored display, unsupported/corrupt input, and reopening a relocated library.

Include left- and right-handed attempts and varied body proportions/clothing when evaluating pose and coaching. Development fixtures may be synthetic for timing/transforms; coaching validation requires real annotated tennis footage.

### Technical gates

- Frame selection and synchronization: requested position resolves within one local source-frame interval on valid timestamp fixtures.
- Cached frame-step target: p95 under 150 ms on a documented benchmark computer; qualify after measuring. Cold seeks are measured separately.
- Cancel feedback appears promptly; the worker reaches a safe cancellation point without corrupting saved state.
- No full-video decoded-frame accumulation; record peak memory on both short and long recordings.
- Full workflow works offline after setup.
- Packaged app launches and completes import → overlay → comparison → save → reopen on the target Mac.
- Backup/restore reproduces source links, confirmed markers, comparisons, and learning history.

### Coaching gates

- Maintain a coach-reviewed labeling guide for each proposed automated criterion.
- Separate data by player and recording session between development and evaluation; do not test on adjacent frames from the same training clip.
- Measure false flags, missed observations, disagreement, and abstention/coverage by camera view. Always report denominators.
- Set per-criterion release thresholds with the reviewer before final evaluation. No blanket accuracy claim for all technique feedback.
- If a criterion fails, retain manual review and mark automation experimental; the validated coaching release remains incomplete for that criterion.

### Beginner usability gate

Using the interface, a beginner should be able to identify the evidence behind an observation, describe the selected practice cue, and reopen the same focus with later footage. Log confusing wording and unsupported certainty, not just software failures.

## 8. Build sequence for the next agent

1. Inspect the actual machine and repository; do not assume an implementation exists. Qualify Python/PySide6/OpenCV/PyAV/MediaPipe together and package a minimal Mac app early.
2. Implement media import, immutable library storage, timestamps, and precise single-video playback.
3. Implement manual attempt ranges, markers, and SQLite persistence.
4. Add pose inference through an adapter, overlay rendering, invalid-span handling, caching, and cancellation.
5. Add synchronized comparison and saved reference metadata.
6. Add skill-focus history, evidence-linked manual observations, practice notes, backup, and restore.
7. Add narrowly scoped event suggestions and coaching criteria only after their required evidence and validation path exist.
8. Run timing/transform tests, representative-media checks, beginner workflow review, and packaged-app acceptance. Record what passed and what remains experimental.

Suggested module boundaries: ui, media, pose, events, feedback, comparison, storage, jobs, and tests. Keep inference and criteria independent of UI widgets so they can be evaluated without launching the interface.

Future agents should preserve these boundaries and the user's learning goal. Routine implementation choices may be made autonomously. Ask only when missing user footage, actual hardware constraints, or a material product decision prevents progress. Do not add automatic video editing or match-strategy analysis to fill gaps.

## 9. Handoff state and unresolved inputs

- Current deliverables are two planning documents only.
- No user video has been inspected in this task.
- Actual video resolution, frame rate, camera view, and body/ball/racket visibility are unknown.
- Actual hardware and dependency compatibility must be tested.
- No qualified coach has yet approved detection rubrics or feedback.
- No model accuracy, processing speed, minimum hardware specification, or distribution signing/notarization has been verified.
- Choose and document exact dependency/model versions during implementation, not by assuming untested latest releases.
- Before distribution beyond development, verify bundled software/model licenses and the required platform signing process.

The first useful milestone is a working desktop review loop with visible body tracking, reliable comparison, and saved learning evidence. Completion of that milestone does not itself establish the accuracy of automatic coaching.

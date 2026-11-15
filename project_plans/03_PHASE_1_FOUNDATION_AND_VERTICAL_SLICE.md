# Tennis Technique Desktop App — Foundation and First Vertical Slice

Version: 1.0  
Date: 2026-11-15  
Status: Small implementation plan  
Parent plan: [Highest-priority master plan](01_MASTER_PLAN_HIGHEST_PRIORITY.md)

## 1. Goal

Build the smallest useful version of the application:

**Open one local tennis video → select one forehand attempt → review it slowly → show a body skeleton → mark key moments → save and reopen the review.**

This is a foundation milestone, not the complete Phase 1 release. Prefer a simple working path over broad feature coverage. Add complexity only after this workflow is reliable.

## 2. What the first slice includes

- A Python desktop application using PySide6.
- A user-selected local library folder.
- Import of one MP4 or MOV video into the library without changing its bytes.
- Video display with play, pause, seek, 0.5× speed, and forward/backward frame stepping.
- Manual selection of one start/end range containing a forehand attempt.
- MediaPipe body-pose processing for that selected range only.
- A skeleton overlay that can be toggled on and off.
- Manual markers for preparation, forward swing, approximate contact, and finish.
- A short user note and one practice cue.
- Save, close, reopen, and recover the same attempt, markers, note, and pose cache.

The initial interface may be plain. Correct video timing, overlay placement, and saved data matter more than visual polish.

## 3. Explicit non-goals

Do not include these in the first slice:

- Automatic coaching or technique scoring.
- Automatic contact, stroke, ball, or racket detection.
- Professional-player downloads or an online reference catalog.
- Side-by-side synchronized comparison.
- Backhand or serve analysis.
- Multi-attempt trends, charts, or progress percentages.
- Exercise recommendations.
- Accounts, cloud storage, telemetry, or external AI services.
- Automatic video cutting or highlight creation.
- Full backup/restore or production distribution signing.

These remain valid later features. They must not block the first working review loop.

## 4. First technical check

Before building the full interface, confirm that the selected versions of Python, PySide6, PyAV, OpenCV, MediaPipe, and NumPy can run together.

Create a minimal application that:

1. Opens a window.
2. Decodes a representative phone-video frame.
3. Runs pose estimation on that frame.
4. Displays the frame and skeleton.
5. Can be packaged and launched on the target Mac without a terminal.

Record the tested Mac processor, macOS version, Python version, dependency versions, and any unsupported video format. If packaging is not immediately available in the development environment, keep the app runnable from source and retain packaging as the end-of-slice target.

## 5. Simple architecture

Use these boundaries without creating unnecessary abstraction:

- `app`: startup and application configuration.
- `ui`: main window, video canvas, timeline, and review controls.
- `media`: import, metadata, timestamps, and frame decoding.
- `pose`: pose adapter, MediaPipe implementation, and cached results.
- `storage`: SQLite setup and save/load operations.
- `models`: small application data objects.
- `tests`: timestamp, persistence, transform, and workflow tests.

Keep video decoding, pose processing, and storage independent from UI widgets where practical. Begin with one implementation per interface; do not build a plugin framework.

## 6. Minimal stored data

Use SQLite for records and a separate file for cached pose arrays. The first schema needs only:

- `media_asset`: ID, library-relative path, content hash, basic metadata, orientation, and import time.
- `attempt`: ID, media ID, start timestamp, end timestamp, stroke type, and created time.
- `event_marker`: ID, attempt ID, event name, source timestamp, and whether it is approximate.
- `review_note`: attempt ID, user note, practice cue, and updated time.
- `pose_run`: attempt ID, model/configuration version, status, and artifact path.

Use source presentation timestamps rather than assumed frame numbers. Store paths relative to the library. Add a basic migration mechanism from the beginning, even if it initially contains only migration `001`.

## 7. Implementation order

### Milestone A — App and media

- Create the project structure, dependency lock, and test setup.
- Let the user choose or create a library folder.
- Import one video and store an unchanged managed copy.
- Read duration, orientation, dimensions, and source timestamps.
- Implement playback, seeking, speed selection, and frame stepping.

Done when the same imported video can be reopened and reviewed at stable source positions.

### Milestone B — Attempt and markers

- Let the user set the start and end of one forehand attempt.
- Add the four manual event markers.
- Save a note and one practice cue.
- Persist everything in SQLite.

Done when restarting the application restores the range, markers, note, and cue at the correct video positions.

### Milestone C — Pose overlay

- Run pose estimation only over the selected attempt.
- Keep inference off the UI thread and show simple progress and cancellation.
- Cache timestamps, landmarks, and validity values.
- Draw the skeleton in the same orientation and coordinate space as the video.
- Hide or fade invalid landmarks and allow the overlay to be toggled.

Done when cached pose results reopen without rerunning inference and remain aligned while the window is resized.

### Milestone D — First usable build

- Handle missing files, unsupported videos, and failed pose processing without losing saved work.
- Test the complete workflow from a clean library.
- Package and launch the app on the target Mac.
- Record limitations and known failures.

Done when a user can complete the full goal in Section 1 without developer assistance.

## 8. Small work packets for coding models

Give a coding model one packet at a time:

1. Scaffold the package, dependency configuration, and test runner.
2. Add SQLite migration `001` and storage tests.
3. Implement library creation and byte-preserving video import.
4. Implement media metadata and timestamp-aware frame decoding.
5. Build the video canvas and basic playback controls.
6. Add attempt-range selection and persistence.
7. Add manual event markers, note, and practice cue.
8. Define the small pose adapter and MediaPipe implementation.
9. Add background pose processing, cancellation, and caching.
10. Render the skeleton with transform tests.
11. Add the save/reopen workflow test and basic error handling.
12. Package and smoke-test the first Mac build.

Each packet should state the files it may change, the expected behavior, tests to add, verification command, and features that are out of scope. A packet is complete only when its tests pass and its saved data remains compatible with earlier packets.

## 9. Minimum test material

Start with a very small fixture set:

- One ordinary landscape MP4.
- One phone video that requires orientation metadata.
- One variable-frame-rate video, if available.
- One unsupported or intentionally damaged file for error handling.

Real tennis footage is needed to check pose visibility and overlay alignment. It is not needed to claim coaching accuracy because this slice makes no automatic coaching claims.

## 10. Completion checklist

The first vertical slice is complete when:

- The app launches on the target Mac.
- An MP4 or MOV can be imported without changing the source content.
- Playback and frame stepping use source timestamps and remain stable after reopening.
- One forehand range and four manual markers can be saved.
- Pose processing is limited to the selected range and can be cancelled.
- The skeleton is visibly aligned and uncertain segments are not shown as confident.
- The note and practice cue survive restart.
- Cached pose data survives restart without reprocessing.
- A bad or missing video produces a useful message instead of a crash.
- Automated coaching, comparison, trends, and other non-goals have not slipped into the build.

## 11. What comes next

After this slice works reliably, expand one capability at a time:

1. Add synchronized comparison with a local reference or earlier attempt.
2. Add skill-focus history linking baseline and follow-up attempts.
3. Add evidence-linked manual observations.
4. Add backup and restore.
5. Evaluate narrowly scoped automatic event suggestions.
6. Begin automatic coaching only after its evidence and validation process exist.

The companion Phase 2 plan remains deferred until the Phase 1 learning workflow is working end to end.

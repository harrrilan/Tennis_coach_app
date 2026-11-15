const state = {
  videos: [],
  selectedId: null,
};

const elements = {
  uploadButton: document.querySelector("#upload-button"),
  emptyUploadButton: document.querySelector("#empty-upload-button"),
  newReviewButton: document.querySelector("#new-review-button"),
  videoInput: document.querySelector("#video-input"),
  uploadZone: document.querySelector("#upload-zone"),
  uploadProgress: document.querySelector("#upload-progress"),
  videoList: document.querySelector("#video-list"),
  videoCount: document.querySelector("#video-count"),
  libraryLocation: document.querySelector("#library-location"),
  emptyState: document.querySelector("#empty-state"),
  reviewLayout: document.querySelector("#review-layout"),
  workspaceTitle: document.querySelector("#workspace-title"),
  videoPlayer: document.querySelector("#video-player"),
  videoBadge: document.querySelector("#video-badge"),
  centerPlay: document.querySelector("#center-play"),
  playButton: document.querySelector("#play-button"),
  playLabel: document.querySelector("#play-label"),
  previousFrame: document.querySelector("#previous-frame"),
  nextFrame: document.querySelector("#next-frame"),
  timeline: document.querySelector("#timeline"),
  currentTime: document.querySelector("#current-time"),
  durationTime: document.querySelector("#duration-time"),
  clipMeta: document.querySelector("#clip-meta"),
  toast: document.querySelector("#toast"),
};

function chooseFile() {
  elements.videoInput.click();
}

elements.uploadButton.addEventListener("click", chooseFile);
elements.emptyUploadButton.addEventListener("click", chooseFile);
elements.newReviewButton.addEventListener("click", chooseFile);

elements.videoInput.addEventListener("change", () => {
  const [file] = elements.videoInput.files;
  if (file) uploadVideo(file);
  elements.videoInput.value = "";
});

["dragenter", "dragover"].forEach((eventName) => {
  elements.uploadZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.uploadZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  elements.uploadZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.uploadZone.classList.remove("dragging");
  });
});

elements.uploadZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (file) uploadVideo(file);
});

async function loadVideos() {
  try {
    const response = await fetch("/api/videos");
    if (!response.ok) throw new Error("Could not open the local video library.");
    state.videos = await response.json();
    renderVideoList();
    if (state.videos.length) selectVideo(state.videos[state.videos.length - 1].id);
  } catch (error) {
    showToast(error.message);
  }
}

async function loadLibraryInfo() {
  try {
    const response = await fetch("/api/library");
    if (!response.ok) return;
    const library = await response.json();
    elements.libraryLocation.textContent = "Saved in .data/library";
    elements.libraryLocation.title = library.path;
  } catch (_error) {
    // The library remains usable even if this optional label cannot be refreshed.
  }
}

async function uploadVideo(file) {
  const extension = file.name.split(".").pop().toLowerCase();
  if (!["mp4", "mov"].includes(extension)) {
    showToast("Choose an MP4 or MOV video.");
    return;
  }

  const formData = new FormData();
  formData.append("video", file);
  elements.uploadProgress.hidden = false;
  elements.uploadButton.disabled = true;

  try {
    const response = await fetch("/api/videos", { method: "POST", body: formData });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Could not import this video.");

    const existingIndex = state.videos.findIndex((video) => video.id === result.id);
    if (existingIndex >= 0) state.videos[existingIndex] = result;
    else state.videos.push(result);
    renderVideoList();
    selectVideo(result.id);
    showToast(`${result.name} is ready to review.`);
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.uploadProgress.hidden = true;
    elements.uploadButton.disabled = false;
  }
}

function renderVideoList() {
  elements.videoList.replaceChildren();
  elements.videoCount.textContent = state.videos.length;

  if (!state.videos.length) {
    const empty = document.createElement("p");
    empty.className = "video-list-empty";
    empty.textContent = "Your imported recordings will appear here.";
    elements.videoList.append(empty);
    return;
  }

  state.videos.forEach((video) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "video-list-item";
    if (video.id === state.selectedId) button.classList.add("active");
    button.addEventListener("click", () => selectVideo(video.id));

    const thumb = document.createElement("span");
    thumb.className = "video-thumb";
    thumb.textContent = "▶";

    const copy = document.createElement("span");
    const name = document.createElement("span");
    name.className = "video-name";
    name.textContent = video.name;
    const detail = document.createElement("span");
    detail.className = "video-detail";
    detail.textContent = `${formatDuration(video.duration_seconds)} · ${video.width}×${video.height}`;
    copy.append(name, detail);
    button.append(thumb, copy);
    elements.videoList.append(button);
  });
}

function selectVideo(id) {
  const video = state.videos.find((item) => item.id === id);
  if (!video) return;
  state.selectedId = id;
  renderVideoList();

  elements.emptyState.hidden = true;
  elements.reviewLayout.hidden = false;
  elements.workspaceTitle.textContent = video.name;
  elements.videoPlayer.src = video.stream_url;
  elements.videoPlayer.load();
  elements.videoBadge.textContent = `${video.width} × ${video.height}`;
  elements.durationTime.textContent = formatDuration(video.duration_seconds);
  elements.currentTime.textContent = formatDuration(0);
  elements.timeline.value = 0;
  elements.clipMeta.replaceChildren(
    metaItem(formatBytes(video.size_bytes)),
    metaItem(`${video.width} × ${video.height}`),
    metaItem(formatDuration(video.duration_seconds)),
    metaItem("Original preserved"),
  );
}

function metaItem(text) {
  const span = document.createElement("span");
  span.textContent = text;
  return span;
}

function togglePlayback() {
  if (elements.videoPlayer.paused) elements.videoPlayer.play();
  else elements.videoPlayer.pause();
}

elements.playButton.addEventListener("click", togglePlayback);
elements.centerPlay.addEventListener("click", togglePlayback);
elements.videoPlayer.addEventListener("click", togglePlayback);

elements.videoPlayer.addEventListener("play", () => setPlaying(true));
elements.videoPlayer.addEventListener("pause", () => setPlaying(false));
elements.videoPlayer.addEventListener("ended", () => setPlaying(false));

function setPlaying(playing) {
  elements.playButton.classList.toggle("playing", playing);
  elements.centerPlay.classList.toggle("playing", playing);
  elements.playLabel.textContent = playing ? "Pause" : "Play";
}

elements.videoPlayer.addEventListener("timeupdate", updateTimeline);
elements.videoPlayer.addEventListener("loadedmetadata", () => {
  elements.durationTime.textContent = formatDuration(elements.videoPlayer.duration);
  updateTimeline();
});

function updateTimeline() {
  const duration = elements.videoPlayer.duration || 0;
  const current = elements.videoPlayer.currentTime || 0;
  elements.timeline.value = duration ? Math.round((current / duration) * 1000) : 0;
  elements.currentTime.textContent = formatDuration(current);
}

elements.timeline.addEventListener("input", () => {
  const duration = elements.videoPlayer.duration || 0;
  elements.videoPlayer.currentTime = (Number(elements.timeline.value) / 1000) * duration;
});

elements.previousFrame.addEventListener("click", () => stepFrame(-1));
elements.nextFrame.addEventListener("click", () => stepFrame(1));

function stepFrame(direction) {
  elements.videoPlayer.pause();
  const step = 1 / 30;
  const duration = elements.videoPlayer.duration || 0;
  elements.videoPlayer.currentTime = Math.min(
    duration,
    Math.max(0, elements.videoPlayer.currentTime + direction * step),
  );
}

document.querySelectorAll("[data-speed]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-speed]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    elements.videoPlayer.playbackRate = Number(button.dataset.speed);
  });
});

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "0:00.000";
  const totalMilliseconds = Math.max(0, Math.round(seconds * 1000));
  const minutes = Math.floor(totalMilliseconds / 60000);
  const remaining = totalMilliseconds % 60000;
  const wholeSeconds = Math.floor(remaining / 1000);
  const milliseconds = remaining % 1000;
  return `${minutes}:${String(wholeSeconds).padStart(2, "0")}.${String(milliseconds).padStart(3, "0")}`;
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

let toastTimer;
function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  toastTimer = setTimeout(() => {
    elements.toast.hidden = true;
  }, 4200);
}

loadVideos();
loadLibraryInfo();

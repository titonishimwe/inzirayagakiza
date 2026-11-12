(function () {
  document.querySelectorAll('.qa-video-player[data-embed-url]').forEach(function (wrap) {
    var btn = wrap.querySelector('[data-qa-video-play]');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var src = (wrap.getAttribute('data-embed-url') || '').trim();
      if (!src) return;
      var watchUrl = (wrap.getAttribute('data-watch-url') || '').trim();
      var box = document.createElement('div');
      box.className = 'ratio ratio-16x9 rounded-3 overflow-hidden shadow-sm';
      var iframe = document.createElement('iframe');
      iframe.src = src;
      iframe.title = 'Video answer';
      iframe.setAttribute(
        'allow',
        'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share'
      );
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      box.appendChild(iframe);
      wrap.replaceChildren(box);
      if (watchUrl) {
        var note = document.createElement('p');
        note.className = 'small text-secondary mt-2 mb-0';
        note.innerHTML =
          'Video not playing? <a href="' +
          watchUrl +
          '" class="fw-semibold">Open on YouTube</a>';
        wrap.appendChild(note);
      }
    });
  });
})();

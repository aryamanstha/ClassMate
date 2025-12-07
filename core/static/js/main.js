// main.js for basic UI behaviors: dark-mode, DESC link, small animation
(function () {
  // DARK MODE: toggle and persist in localStorage
  const toggleBtn = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');

  function setDarkMode(on) {
    if (on) {
      document.documentElement.classList.add('cm-dark');
      document.body.classList.add('cm-dark');
      themeIcon.className = 'bi bi-sun-fill';
      localStorage.setItem('cm-theme', 'dark');
    } else {
      document.documentElement.classList.remove('cm-dark');
      document.body.classList.remove('cm-dark');
      themeIcon.className = 'bi bi-moon-fill';
      localStorage.setItem('cm-theme', 'light');
    }
  }

  // initialize theme from storage or prefer dark if user prefers
  const stored = localStorage.getItem('cm-theme');
  if (stored === 'dark') {
    setDarkMode(true);
  } else if (stored === 'light') {
    setDarkMode(false);
  } else {
    // use media query fallback
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(prefersDark);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      const isDark = document.body.classList.contains('cm-dark');
      setDarkMode(!isDark);
    });
  }

  // DESC link: open the uploaded PDF in a new tab if present
  const descLink = document.getElementById('descLink');
  try {
    if (descLink && typeof DESC_FILE_URL !== 'undefined') {
      // If your server exposes the file under /media/ or /static/, update DESC_FILE_URL accordingly.
      descLink.href = DESC_FILE_URL;
    }
  } catch (e) {
    // ignore
  }

  // Small fade-in for page content
  document.addEventListener('DOMContentLoaded', function () {
    const container = document.querySelector('.page-container');
    if (container) {
      container.style.opacity = 0;
      container.style.transform = 'translateY(6px)';
      setTimeout(() => {
        container.style.transition = 'opacity 350ms ease, transform 350ms ease';
        container.style.opacity = 1;
        container.style.transform = 'translateY(0)';
      }, 60);
    }
  });
})();
// AUTOCOMPLETE LIVE SEARCH
(function(){
  const input = document.getElementById("topSearch");
  const box = document.getElementById("searchSuggestions");

  if (!input || !box) return;

  let timer = null;

  input.addEventListener("input", function() {
    const q = this.value.trim();

    if (q.length < 2) {
      box.style.display = "none";
      return;
    }

    clearTimeout(timer);
    timer = setTimeout(() => {
      fetch(`/search/suggest/?q=${encodeURIComponent(q)}`)
        .then(res => res.json())
        .then(data => {
          if (!data.results || data.results.length === 0) {
            box.style.display = "none";
            return;
          }

          let html = "";
          data.results.forEach(item => {
            html += `
              <div class="suggestion-item" onclick="selectSuggestion('${item.text}')">
                  <strong>${item.text}</strong><br>
                  <span class="suggestion-type">${item.type}</span>
              </div>`;
          });

          box.innerHTML = html;
          box.style.display = "block";
        });
    }, 200); // debounce 200ms
  });

  // hide box on click outside
  document.addEventListener("click", function(e){
    if (!box.contains(e.target) && e.target !== input) {
      box.style.display = "none";
    }
  });

})();

// When user clicks a suggestion
function selectSuggestion(text) {
  const input = document.getElementById("topSearch");
  input.value = text;
  document.querySelector("form[role='search']").submit();
}



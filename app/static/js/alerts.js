(function(){
  function wireCloseHandler(btn){
    if (!btn.__wired) { // avoid double-binding
      btn.addEventListener('click', function(ev){
        const container = btn.closest('.alert');
        if (container) container.remove();
      });
      btn.__wired = true;
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    // Normalize and enhance all alerts: ensure close buttons exist and are functional
    document.querySelectorAll('.alert').forEach(function(alert){
      // If the template didn't include a close button, add one
      if(!alert.querySelector('.alert-close')){
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'alert-close';
        btn.setAttribute('aria-label', 'Close alert');
        btn.innerHTML = '\u2715'; // simple "×"
        alert.appendChild(btn);
      }

      // Wire up any existing or newly added close buttons
      alert.querySelectorAll('.alert-close').forEach(wireCloseHandler);

      // Map common category aliases to our CSS classes if needed
      // e.g. Flask may use "warning" or "warn", "error" or "danger"
      const classes = alert.classList;
      if(classes.contains('alert-warn') && !classes.contains('alert-warning')){
        classes.add('alert-warning');
      }
      if(classes.contains('alert-error') && !classes.contains('alert-danger')){
        classes.add('alert-danger');
      }
    });
  });
})();

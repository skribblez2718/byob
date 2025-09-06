(function(){
  const formEl = document.getElementById('projects-form');
  if(!formEl) return;

  function nextIndex(listEl){
    return listEl.querySelectorAll(':scope > .item').length;
  }

  function createEl(html){
    const t=document.createElement('template');
    t.innerHTML=html.trim();
    return t.content.firstElementChild;
  }

  function addProject(){
    const list = document.getElementById('projects-list');
    const idx = nextIndex(list);
    const html = `
      <div class="item" data-role="project">
        <div class="form-group">
          <label class="form-label" for="projects-${idx}-project_image">Project Image (PNG/JPEG/WEBP)</label>
          <input type="file" id="projects-${idx}-project_image" name="projects-${idx}-project_image" />
          <div class="form-group">
            <input type="checkbox" id="projects-${idx}-remove_image" name="projects-${idx}-remove_image" />
            <label for="projects-${idx}-remove_image" class="form-label checkbox-label">Remove Image</label>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" for="projects-${idx}-project_title">Project Title</label>
          <input class="form-input" id="projects-${idx}-project_title" name="projects-${idx}-project_title" type="text" value="" required>
        </div>
        <div class="form-group">
          <label class="form-label" for="projects-${idx}-project_description">Project Description</label>
          <textarea class="form-textarea" rows="3" id="projects-${idx}-project_description" name="projects-${idx}-project_description"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label" for="projects-${idx}-project_url">Project URL</label>
          <input class="form-input" id="projects-${idx}-project_url" name="projects-${idx}-project_url" type="url" value="">
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" id="projects-${idx}-delete" name="projects-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Project</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }

  // Event handler for add button
  document.getElementById('add-project')?.addEventListener('click', addProject);

  // Mark delete + hide for any item with a delete checkbox within it
  document.body.addEventListener('click', function(e){
    const delBtn = e.target.closest('.mark-delete');
    if(delBtn){
      const item = delBtn.closest('.item');
      if(item){
        const checkbox = item.querySelector('input[type="checkbox"][name$="-delete"]');
        if(checkbox){ checkbox.checked = true; }
        item.classList.add('is-hidden');
      }
    }
  });
})();

(function(){
  const formEl = document.getElementById('resume-form');
  if(!formEl) return;

  function nextIndex(listEl){
    return listEl.querySelectorAll(':scope > .item').length;
  }

  function addEducation(){
    const list = document.getElementById('education-list');
    const idx = nextIndex(list);
    const html = `
      <div class="item" data-role="education">
        <div class="form-group">
          <label class="form-label" for="education-${idx}-image">Education Image (PNG/JPEG/WEBP)</label>
          <input type="file" id="education-${idx}-image" name="education-${idx}-image" />
        </div>
        <div class="form-group">
          <label class="form-label" for="education-${idx}-title">Title</label>
          <input class="form-input" id="education-${idx}-title" name="education-${idx}-title" type="text" value="">
        </div>
        <div class="form-group">
          <label class="form-label" for="education-${idx}-description">Description</label>
          <textarea class="form-textarea" rows="2" id="education-${idx}-description" name="education-${idx}-description"></textarea>
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" id="education-${idx}-delete" name="education-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Education</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }
  function createEl(html){
    const t=document.createElement('template');
    t.innerHTML=html.trim();
    return t.content.firstElementChild;
  }

  function addSkill(){
    const list=document.getElementById('skills-list');
    const idx=nextIndex(list);
    const html=`
      <div class="item" data-role="skill">
        <div class="form-group">
          <label class="form-label" for="skills-${idx}-skill_title">Skill Title</label>
          <input class="form-input" id="skills-${idx}-skill_title" name="skills-${idx}-skill_title" type="text" value="">
        </div>
        <div class="form-group">
          <label class="form-label" for="skills-${idx}-skill_description">Skill Description</label>
          <textarea class="form-textarea" rows="3" id="skills-${idx}-skill_description" name="skills-${idx}-skill_description"></textarea>
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" name="skills-${idx}-delete" id="skills-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Skill</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }

  function addWorkItem(){
    const list=document.getElementById('work-list');
    const idx=nextIndex(list);
    const html=`
      <div class="item" data-role="work">
        <div class="form-group">
          <label class="form-label" for="work_history-${idx}-work_history_image">Company/Image (PNG/JPEG/WEBP)</label>
          <input type="file" id="work_history-${idx}-work_history_image" name="work_history-${idx}-work_history_image" />
        </div>
        <div class="form-group">
          <label class="form-label" for="work_history-${idx}-work_history_company_name">Company Name</label>
          <input class="form-input" id="work_history-${idx}-work_history_company_name" name="work_history-${idx}-work_history_company_name" type="text" value="">
        </div>
        <div class="form-group form-row">
          <div class="flex-1">
            <label class="form-label" for="work_history-${idx}-work_history_dates">Dates</label>
            <input class="form-input" id="work_history-${idx}-work_history_dates" name="work_history-${idx}-work_history_dates" type="text" value="">
          </div>
          <div class="flex-1">
            <label class="form-label" for="work_history-${idx}-work_history_role">Role/Title</label>
            <input class="form-input" id="work_history-${idx}-work_history_role" name="work_history-${idx}-work_history_role" type="text" value="">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label" for="work_history-${idx}-work_history_role_description">Role Description</label>
          <textarea class="form-textarea" rows="3" id="work_history-${idx}-work_history_role_description" name="work_history-${idx}-work_history_role_description"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Accomplishments</label>
          <div class="accomplishments"></div>
          <div class="section-actions">
            <button type="button" class="btn btn-secondary btn-small add-accomplishment" data-work-index="${idx}">+ Add Accomplishment</button>
          </div>
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" name="work_history-${idx}-delete" id="work_history-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Work Item</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }

  function addAccomplishment(workIdx){
    const list=document.getElementById('work-list');
    const workItem=list.querySelectorAll(':scope > .item')[workIdx];
    if(!workItem) return;
    const accList=workItem.querySelector('.accomplishments');
    const next=accList.querySelectorAll(':scope > .acc-item').length;
    const html=`
      <div class="acc-item">
        <input class="form-input" type="text" id="work_history-${workIdx}-accomplishments-${next}-accomplishment_text" name="work_history-${workIdx}-accomplishments-${next}-accomplishment_text" value="">
        <input type="checkbox" id="work_history-${workIdx}-accomplishments-${next}-delete" name="work_history-${workIdx}-accomplishments-${next}-delete" />
        <button type="button" class="btn btn-outline-danger btn-small mark-delete-accomplishment">Remove Accomplishment</button>
      </div>`;
    accList.appendChild(createEl(html));
  }

  function addCert(){
    const list=document.getElementById('certs-list');
    const idx=nextIndex(list);
    const html=`
      <div class="item" data-role="cert">
        <div class="form-group"><label class="form-label" for="certifications-${idx}-image">Image (PNG/JPEG/WEBP)</label> <input type="file" id="certifications-${idx}-image" name="certifications-${idx}-image"></div>
        <div class="form-group">
          <label class="form-label" for="certifications-${idx}-title">Title</label>
          <input class="form-input" id="certifications-${idx}-title" name="certifications-${idx}-title" type="text" value="">
        </div>
        <div class="form-group">
          <label class="form-label" for="certifications-${idx}-description">Description</label>
          <textarea class="form-textarea" rows="2" id="certifications-${idx}-description" name="certifications-${idx}-description"></textarea>
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" id="certifications-${idx}-delete" name="certifications-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Certification</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }

  function addPD(){
    const list=document.getElementById('pd-list');
    const idx=nextIndex(list);
    const html=`
      <div class="item" data-role="pd">
        <div class="form-group"><label class="form-label" for="professional_development-${idx}-image">Image (PNG/JPEG/WEBP)</label> <input type="file" id="professional_development-${idx}-image" name="professional_development-${idx}-image"></div>
        <div class="form-group">
          <label class="form-label" for="professional_development-${idx}-title">Title</label>
          <input class="form-input" id="professional_development-${idx}-title" name="professional_development-${idx}-title" type="text" value="">
        </div>
        <div class="form-group">
          <label class="form-label" for="professional_development-${idx}-description">Description</label>
          <textarea class="form-textarea" rows="2" id="professional_development-${idx}-description" name="professional_development-${idx}-description"></textarea>
        </div>
        <div class="form-group center-actions">
          <input type="checkbox" id="professional_development-${idx}-delete" name="professional_development-${idx}-delete" />
          <button type="button" class="btn btn-outline-danger btn-small mark-delete">Remove Professional Development</button>
        </div>
      </div>`;
    list.appendChild(createEl(html));
  }

  // Event handlers for add buttons
  document.getElementById('add-skill')?.addEventListener('click', addSkill);
  document.getElementById('add-work-item')?.addEventListener('click', addWorkItem);
  document.getElementById('add-cert')?.addEventListener('click', addCert);
  document.getElementById('add-pd')?.addEventListener('click', addPD);
  document.getElementById('add-education')?.addEventListener('click', addEducation);

  // Delegate add-accomplishment clicks
  document.getElementById('work-list')?.addEventListener('click', function(e){
    const btn = e.target.closest('.add-accomplishment');
    if(!btn) return;
    const idx = parseInt(btn.getAttribute('data-work-index'), 10);
    if(Number.isFinite(idx)) addAccomplishment(idx);
  });

  // Cleanup: if there are any previously hidden items from older behavior, remove them and ensure delete markers
  function cleanupHiddenDeletions(){
    // Hidden full items
    document.querySelectorAll('.item.is-hidden').forEach((item)=>{
      let deleteName = '';
      const delInput = item.querySelector('input[name$="-delete"]');
      if(delInput){ deleteName = delInput.name; }
      if(!deleteName){
        const anyField = item.querySelector('input[name], textarea[name]');
        if(anyField && anyField.name){
          deleteName = anyField.name.replace(/-[a-z_]+$/, '-delete');
        }
      }
      ensureFormDeleteInput(deleteName);
      item.remove();
    });
    // Hidden accomplishments
    document.querySelectorAll('.acc-item.is-hidden').forEach((acc)=>{
      let deleteName = '';
      const delInput = acc.querySelector('input[name$="-delete"]');
      if(delInput){ deleteName = delInput.name; }
      if(!deleteName){
        const textInput = acc.querySelector('input.form-input');
        if(textInput && textInput.name){
          deleteName = textInput.name.replace(/accomplishment_text$/, 'delete');
        }
      }
      ensureFormDeleteInput(deleteName);
      acc.remove();
    });
  }

  // Run cleanup on load
  cleanupHiddenDeletions();

  // Utility: ensure a hidden delete input with given name exists on the form
  function ensureFormDeleteInput(deleteName){
    if(!deleteName) return;
    // Check if a top-level input already exists on the form
    let existing = formEl.querySelector(`input[name="${CSS.escape(deleteName)}"]`);
    if(existing){
      if(existing.type === 'checkbox') existing.checked = true;
      else existing.value = 'y';
      return existing;
    }
    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = deleteName;
    hidden.value = 'y';
    formEl.appendChild(hidden);
    return hidden;
  }

  // Mark delete and remove from DOM for any item; also handle accomplishments separately
  document.body.addEventListener('click', function(e){
    const delBtn = e.target.closest('.mark-delete');
    if(delBtn){
      const item = delBtn.closest('.item');
      if(item){
        // Determine delete field name
        let deleteName = '';
        let delInput = item.querySelector('input[name$="-delete"]');
        if(delInput){ deleteName = delInput.name; }
        if(!deleteName){
          const anyField = item.querySelector('input[name], textarea[name]');
          if(anyField && anyField.name){
            deleteName = anyField.name.replace(/-[a-z_]+$/, '-delete');
          }
        }
        // Ensure a persistent hidden delete marker on the form
        ensureFormDeleteInput(deleteName);
        // Remove from DOM to avoid hidden required fields causing validation errors
        item.remove();
      }
    }
    const delAccBtn = e.target.closest('.mark-delete-accomplishment');
    if(delAccBtn){
      const acc = delAccBtn.closest('.acc-item');
      if(acc){
        // Compute delete field name for accomplishments
        let deleteName = '';
        let delInput = acc.querySelector('input[name$="-delete"]');
        if(delInput){ deleteName = delInput.name; }
        if(!deleteName){
          const textInput = acc.querySelector('input.form-input');
          if(textInput && textInput.name){
            deleteName = textInput.name.replace(/accomplishment_text$/, 'delete');
          }
        }
        // Ensure a persistent hidden delete marker on the form
        ensureFormDeleteInput(deleteName);
        // Remove from DOM for immediate feedback
        acc.remove();
      }
    }
  });
})();

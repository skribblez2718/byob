(function(){
  const formEl = document.getElementById('projects-form');
  if(formEl) {
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
  }

  // Drag and drop functionality for projects table
  const projectsTable = document.getElementById('projects-table');
  const projectsTBody = document.getElementById('projects-tbody');
  
  if (projectsTable && projectsTBody) {
    let draggedRow = null;
    let draggedIndex = null;
    let targetIndex = null;

    // Add drag event listeners to all draggable rows
    function initializeDragAndDrop() {
      const rows = projectsTBody.querySelectorAll('.draggable-row');
      
      rows.forEach((row, index) => {
        row.draggable = true;
        row.dataset.originalIndex = index;
        
        row.addEventListener('dragstart', handleDragStart);
        row.addEventListener('dragover', handleDragOver);
        row.addEventListener('drop', handleDrop);
        row.addEventListener('dragend', handleDragEnd);
        row.addEventListener('dragenter', handleDragEnter);
        row.addEventListener('dragleave', handleDragLeave);
      });
    }

    function handleDragStart(e) {
      draggedRow = this;
      draggedIndex = Array.from(projectsTBody.children).indexOf(this);
      this.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', this.outerHTML);
    }

    function handleDragOver(e) {
      if (e.preventDefault) {
        e.preventDefault();
      }
      e.dataTransfer.dropEffect = 'move';
      return false;
    }

    function handleDragEnter(e) {
      if (this !== draggedRow) {
        this.classList.add('drag-over');
      }
    }

    function handleDragLeave(e) {
      this.classList.remove('drag-over');
    }

    function handleDrop(e) {
      if (e.stopPropagation) {
        e.stopPropagation();
      }

      if (draggedRow !== this) {
        targetIndex = Array.from(projectsTBody.children).indexOf(this);
        
        // Determine if we're inserting before or after the target
        const rect = this.getBoundingClientRect();
        const midpoint = rect.top + rect.height / 2;
        const insertAfter = e.clientY > midpoint;
        
        if (insertAfter) {
          this.parentNode.insertBefore(draggedRow, this.nextSibling);
        } else {
          this.parentNode.insertBefore(draggedRow, this);
        }
        
        // Send reorder request to server
        updateProjectOrder();
      }

      return false;
    }

    function handleDragEnd(e) {
      // Clean up
      const rows = projectsTBody.querySelectorAll('.draggable-row');
      rows.forEach(row => {
        row.classList.remove('dragging', 'drag-over');
      });
      
      draggedRow = null;
      draggedIndex = null;
      targetIndex = null;
    }

    function updateProjectOrder() {
      const rows = projectsTBody.querySelectorAll('.draggable-row');
      const projectHexIds = Array.from(rows).map(row => row.dataset.projectHexId);
      
      // Send AJAX request to update order
      fetch('/api/admin/projects/reorder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({
          project_hex_ids: projectHexIds
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.error('Error reordering projects:', data.error);
          // Optionally show user feedback
          showNotification('Error reordering projects: ' + data.error, 'error');
        } else {
          console.log('Projects reordered successfully');
          showNotification('Projects reordered successfully', 'success');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showNotification('Error reordering projects', 'error');
      });
    }

    function showNotification(message, type = 'info') {
      // Create a simple notification
      const notification = document.createElement('div');
      notification.className = `alert alert-${type} notification`;
      notification.textContent = message;
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        padding: 10px 15px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      `;
      
      document.body.appendChild(notification);
      
      // Auto-remove after 3 seconds
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }

    // Initialize drag and drop
    initializeDragAndDrop();
  }
})();
